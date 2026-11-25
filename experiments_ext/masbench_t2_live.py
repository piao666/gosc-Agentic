"""Reversible T2 deployment acceptance using the existing synthetic LiveDriver."""
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
import hpc_ollama
from hpc_runs import require_hpc
from experiments_ext import masbench_t1b_live as campaign
from extensions.masbench_reasoning import live_driver as live
from extensions.masbench_reasoning.execution_safety import SafetyError

FIXTURE = 'hpc-masbench-t2-contract-v3-20261125'
DEMAND = 'hpc-masbench-t2-window-demand-20261125'
STATE = hpc_ollama.STATE / 'service.json'
PROFILE = hpc_ollama.CONTEXT_PROFILE
LEASE = ROOT / '.local/t1-service.lock'


def record(path, stage, **fields):
    with path.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(stage=stage,mono=time.monotonic(),**fields),sort_keys=True)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def sync_dir(path):
    fd = os.open(path,os.O_DIRECTORY | os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def service(context, binary_sha):
    pid = json.loads(STATE.read_bytes())['pid']
    try:
        fields = live.proc_fields(Path('/proc',str(pid)))
    except (FileNotFoundError, ProcessLookupError):
        return None
    if fields[0] == 'Z':
        return None
    runtime = live.Runtime(str(ROOT),campaign.HELPER,pid,fields[19],binary_sha,context)
    live.runtime_files(runtime)
    return runtime


def identity(runtime):
    return {'service_pid':runtime.service_pid, 'service_stamp':runtime.service_stamp,
            'service_binary_sha256':runtime.binary_sha,'context':runtime.context}


def assert_idle(runtime, require_listener=True):
    listeners = campaign.command('ss','-Hlnpt','sport = :11434')
    if listeners or require_listener:
        campaign.own_listener(runtime)
    if live.runner_identities(runtime):
        raise SafetyError('active model runner blocks service switch')
    gpu = campaign.command('nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits',timeout=3)
    if gpu != '0':
        raise SafetyError('non-idle GPU blocks service switch')


def stop_idle(runtime, journal):
    assert_idle(runtime,require_listener=False)
    if live.proc_stamp(runtime.service_pid) != runtime.service_stamp:
        raise SafetyError('refusing to stop changed service identity')
    record(journal,'service-term',service=identity(runtime),signal=int(signal.SIGTERM))
    os.kill(runtime.service_pid,signal.SIGTERM)
    deadline = time.monotonic()+12
    while time.monotonic() < deadline:
        if live.proc_stamp(runtime.service_pid) != runtime.service_stamp:
            if campaign.command('ss','-Hlnpt','sport = :11434'):
                raise SafetyError('listener remained after project service exit')
            record(journal,'service-exited',service=identity(runtime))
            return
        # Popen children can be zombies until this parent reaps them.
        try:
            os.waitpid(runtime.service_pid,os.WNOHANG)
        except ChildProcessError:
            try:
                if live.proc_fields(Path('/proc',str(runtime.service_pid)))[0] == 'Z':
                    if campaign.command('ss','-Hlnpt','sport = :11434'):
                        raise SafetyError('listener remained after project service exit')
                    record(journal,'service-exited',service=identity(runtime),zombie=True)
                    return
            except FileNotFoundError:
                continue
        time.sleep(.1)
    raise SafetyError('old service exit deadline')


def start_checked(context, env, binary_sha, journal, stage, **start_options):
    if campaign.command('ss','-Hlnpt','sport = :11434'):
        raise SafetyError('existing listener blocks startup')
    status = hpc_ollama.start(base_env=env,**start_options)
    runtime = service(context,binary_sha)
    if not runtime or status.get('reused') or status.get('pid') != runtime.service_pid:
        raise SafetyError('new service identity not verified')
    assert_idle(runtime)
    record(journal,stage,service=identity(runtime),profile_exists=PROFILE.exists())
    return runtime


def main():
    require_hpc()
    authorization = ROOT/live.T2_AUTH
    approval = live.require_authorization(authorization)
    plan = json.loads((ROOT/live.T2_PLAN).read_bytes())
    count_dir = ROOT/'research/sync/runs'/DEMAND
    fixture_dir = ROOT/'research/sync/runs'/FIXTURE
    if any(json.loads((p/'status.json').read_bytes())['status']!='completed' for p in (count_dir,fixture_dir)):
        raise SafetyError('T2 offline and fixture runs must pass before service changes')
    demand_path = count_dir/'outputs/window_demand.json'
    context = approval['context']
    demand = json.loads(demand_path.read_bytes())
    if live.file_sha(demand_path) != plan['demand_sha256'] or demand['smallest_test_candidate'] != context or context <= 1024:
        raise SafetyError('measured T2 window does not match the frozen plan')
    previous = ROOT/'research/sync/runs/hpc-masbench-t2-live-v2-20261125/outputs/summary.json'
    audit = ROOT/'research/sync/runs/hpc-masbench-t2-audit-v2-20261125/outputs/audit.json'
    prior = json.loads(previous.read_bytes())['reservations']
    if (live.file_sha(previous)!=plan['previous_summary_sha256'] or live.file_sha(audit)!=plan['previous_audit_sha256']
            or len(prior['requests'])+plan['caps']['requests']>4
            or prior['inputs']+plan['caps']['inputs']>65536 or prior['outputs']+plan['caps']['outputs']>1088):
        raise SafetyError('cumulative T2 budget mismatch')
    run = Path(os.environ['GOSC_RUN_DIR'])
    if any(p.parent != run and json.loads(p.read_bytes())['status'] in {'running','planned'}
           for p in run.parent.glob('*/status.json')):
        raise SafetyError('another project run is active')
    if PROFILE.exists() or PROFILE.is_symlink():
        raise SafetyError('pre-existing context profile must be preserved')
    journal = Path(os.environ['GOSC_OUTPUT_DIR'])/'service_transitions.jsonl'
    binary_sha = approval['service_binary_sha256']
    original = service(1024,binary_sha)
    if not original or any(identity(original)[key] != approval[key] for key in ('service_pid','service_stamp','service_binary_sha256')):
        raise SafetyError('baseline service identity drift')
    raw = Path('/proc', str(original.service_pid),'environ').read_bytes()
    env = dict(item.split('=',1) for item in raw.decode().split('\0') if '=' in item)
    profile_bytes = (json.dumps({'context_tokens':context})+'\n').encode()
    changed = False

    def interrupted(signum, frame):
        raise InterruptedError(f'T2 lifecycle signal {signum}')

    signal.signal(signal.SIGTERM,interrupted)
    signal.signal(signal.SIGHUP,interrupted)
    try:
        lease = live.ServiceLease(LEASE)
        try:
            if lease.owner():
                raise SafetyError('existing recovery marker blocks T2')
            assert_idle(original)
            record(journal,'baseline',service=identity(original),profile_exists=False)
            # Arm rollback before changing the startup profile or service.
            changed = True
            with PROFILE.open('xb') as stream:
                stream.write(profile_bytes)
                stream.flush()
                os.fsync(stream.fileno())
            sync_dir(PROFILE.parent)
            record(journal,'candidate-profile-written',profile_sha256=live.file_sha(PROFILE),context=context)
            stop_idle(original,journal)
            first = start_checked(context,env,binary_sha,journal,'candidate-first-start')
            stop_idle(first,journal)
            restarted = start_checked(context,env,binary_sha,journal,'candidate-restart')
        finally:
            lease.close()
        campaign.main(authorization,FIXTURE,identity(restarted))
    finally:
        if changed:
            lease = live.ServiceLease(LEASE)
            try:
                if lease.owner():
                    record(journal,'rollback-fenced',reason='live recovery marker remains')
                    raise SafetyError('rollback awaits owned runner recovery evidence')
                if PROFILE.exists() and PROFILE.read_bytes()!=profile_bytes:
                    raise SafetyError('context profile changed during T2')
                current_pid = json.loads(STATE.read_bytes())['pid']
                if current_pid == original.service_pid and service(1024,binary_sha) == original:
                    assert_idle(original)
                    restored = original
                    PROFILE.unlink(missing_ok=True)
                    sync_dir(PROFILE.parent)
                else:
                    current = service(context,binary_sha)
                    if current:
                        stop_idle(current,journal)
                    PROFILE.unlink(missing_ok=True)
                    sync_dir(PROFILE.parent)
                    restored = start_checked(1024,env,binary_sha,journal,'baseline-restart')
                if hpc_ollama.settings()[0]['num_ctx'] != 1024:
                    raise SafetyError('persistent 1024 startup setting not restored')
                record(journal,'rollback-verified',service=identity(restored),profile_exists=False,
                       empty_runner=True,gpu_mib=0)
            finally:
                lease.close()


if __name__ == '__main__':
    main()
