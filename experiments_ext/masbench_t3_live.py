"""One authorized four-development-family campaign, with raw evidence on HPC HDD."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from hpc_runs import require_hpc, write_json
from experiments_ext import masbench_t2_live as lifecycle, masbench_t2_window_demand as data
from experiments_ext import masbench_t1b_live as t1
from extensions.masbench_reasoning import live_driver as live
from extensions.masbench_reasoning.application import LocalAgent, private_view
from extensions.masbench_reasoning.execution_safety import Limits, SafetyError

HDD = Path('/hdd/u202520081000097')
QUOTA = ROOT/'research/logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota.py'
CONTRACT_ID = 'hpc-masbench-t3-integrated-contract-v2-20261125'
CAPS = {'driver_rss':2*1024**3,'service_rss':16*1024**3,'gpu_bytes':16*1024**3}


def quota_snapshot():
    raw = subprocess.check_output([sys.executable, QUOTA], timeout=10)
    value = json.loads(raw)
    for volume, cap in [('ssd', live.T3_SSD_BYTES), ('hdd', live.T3_HDD_BYTES)]:
        available = value['volumes'][volume].get('remaining_to_hard_limit_bytes')
        if not isinstance(available, int) or available < cap:
            raise SafetyError(f'insufficient personal {volume} quota')
    return value


def open_hdd(run, campaign):
    live.reject_links(HDD)
    if (os.getuid()!=8301880 or not os.path.ismount(HDD.parent) or HDD.stat().st_uid!=os.getuid()
            or run.stat().st_dev==HDD.stat().st_dev):
        raise SafetyError('unexpected HDD ownership, mount or filesystem')
    parent = live.reject_links(HDD/campaign)
    parent.mkdir(mode=0o700,exist_ok=True)
    if parent.stat().st_uid!=os.getuid() or parent.stat().st_dev!=HDD.stat().st_dev:
        raise SafetyError('unexpected HDD parent ownership or filesystem')
    root = live.reject_links(parent/run.name)
    root.mkdir(mode=0o700,exist_ok=False)
    lifecycle.sync_dir(parent)
    return root


def inventory(root):
    entries = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or path.stat().st_dev!=root.stat().st_dev:
            raise SafetyError('unexpected link or mount in evidence')
        if path.is_file():
            entries.append({'path':path.relative_to(root).as_posix(),
                            'size':path.stat().st_size,'sha256':live.file_sha(path)})
    if sum(row['size'] for row in entries)>live.T3_HDD_BYTES:
        raise SafetyError('HDD evidence cap exceeded')
    for row in entries:
        path = root/row['path']
        if path.stat().st_size!=row['size'] or live.file_sha(path)!=row['sha256']:
            raise SafetyError('HDD readback changed after indexing')
    for directory in [p for p in root.rglob('*') if p.is_dir()] + [root]:
        lifecycle.sync_dir(directory)
    return {'hdd_root':str(root),'bytes':sum(row['size'] for row in entries),
            'files':entries,'readback_verified':True,'raw_mirrored':False}


def assert_idle(runtime):
    lifecycle.assert_idle(runtime)
    if t1.command('ss','-Hnt','state','established','sport = :11434 or dport = :11434'):
        raise SafetyError('established connections block exclusive service change')


@contextmanager
def profile(root, approval):
    journal = root/'service_transitions.jsonl'
    binary_sha = approval['service_binary_sha256']
    original = lifecycle.service(1024,binary_sha)
    if not original or any(lifecycle.identity(original)[key]!=approval[key]
                           for key in ('service_pid','service_stamp')):
        raise SafetyError('approved baseline service identity has changed')
    raw = Path('/proc',str(original.service_pid),'environ').read_bytes()
    env = dict(item.split('=',1) for item in raw.decode().split('\0') if '=' in item)
    profile_path = live.reject_links(lifecycle.PROFILE)
    expected = b'{"context_tokens":16384}\n'
    changed = False
    try:
        lease = live.ServiceLease(lifecycle.LEASE)
        try:
            if lease.owner() or profile_path.exists():
                raise SafetyError('pre-existing marker or profile blocks T3')
            assert_idle(original)
            lifecycle.record(journal,'baseline',service=lifecycle.identity(original))
            with profile_path.open('xb') as stream:
                changed = True
                stream.write(expected)
                stream.flush()
                os.fsync(stream.fileno())
            lifecycle.sync_dir(profile_path.parent)
            lifecycle.record(journal,'profile-written',sha256=live.file_sha(profile_path))
            lifecycle.stop_idle(original,journal)
            runtime = lifecycle.start_checked(16384,env,binary_sha,journal,'candidate-start',
                log_path=root/'service.log',log_file_limit=live.T3_SERVICE_LOG_BYTES)
            assert_idle(runtime)
        finally:
            lease.close()
        yield runtime
    finally:
        if changed:
            lease = live.ServiceLease(lifecycle.LEASE)
            try:
                if lease.owner():
                    lifecycle.record(journal,'rollback-fenced',reason='owned recovery marker remains')
                    raise SafetyError('rollback awaits verified runner exit')
                if profile_path.read_bytes()!=expected:
                    raise SafetyError('T3 context profile changed externally')
                pid = json.loads(lifecycle.STATE.read_bytes())['pid']
                if pid==original.service_pid and lifecycle.service(1024,binary_sha)==original:
                    assert_idle(original)
                    restored = original
                else:
                    active = lifecycle.service(16384,binary_sha)
                    if active:
                        assert_idle(active)
                        lifecycle.stop_idle(active,journal)
                    restored = None
                profile_path.unlink()
                lifecycle.sync_dir(profile_path.parent)
                if restored is None:
                    restored = lifecycle.start_checked(1024,env,binary_sha,journal,'baseline-restart')
                assert_idle(restored)
                if lifecycle.hpc_ollama.settings()[0]['num_ctx']!=1024:
                    raise SafetyError('persistent 1024 setting not restored')
                lifecycle.record(journal,'rollback-verified',service=lifecycle.identity(restored),
                                 runner_count=0,gpu_mib=0,lease_clear=True)
            finally:
                lease.close()


def limits(remaining):
    return Limits(requests=98,metadata=420,input_tokens=1555456,output_tokens=50176,
                  per_output=512,wall_seconds=remaining,operation_seconds=live.T3_OPERATION_SECONDS,
                  artifact_bytes=live.T3_DRIVER_BYTES)


def run_synthetic(driver, case):
    key = case['id']
    driver.ledger.episode(key,'started')
    driver.current_episode = key
    driver.control.append({'kind':'case-start','id':key,'max_output':512})
    driver.armed_case = case
    try:
        response = driver.generate(case['messages'])
        if response.strip()!='OK' or case['id']=='synthetic-long' and driver.counted[1]<=1024:
            raise SafetyError('synthetic result or long-window precondition failed')
        driver.recover()
        driver.ledger.episode(key,'completed')
    except BaseException:
        if driver.ledger.state['episodes'][key]=='started':
            driver.ledger.episode(key,'failed')
        raise


def validate_contract(approval):
    contract = ROOT/'research/sync/runs'/CONTRACT_ID
    receipt = contract/'outputs/integration.json'
    if (json.loads((contract/'status.json').read_bytes())['status']!='completed'
            or approval['contract_receipt_sha256']!=live.file_sha(receipt)):
        raise SafetyError('T3 requires completed and bound HDD/ledger integration contract')
    report = json.loads(receipt.read_bytes())
    if (report['live_source_sha256']!=live.file_sha(live.__file__)
            or report['launcher_sha256']!=live.file_sha(__file__)
            or report['task_reservations']!=96 or report['synthetic_reservations']!=2
            or report['model_requests']!=0 or not report['hdd_readback_verified']):
        raise SafetyError('offline integration findings or source identity mismatch')


def main():
    begin = time.monotonic()
    require_hpc()
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.umask(0o077)
    authorization = ROOT/live.T3_AUTH
    approval = live.require_authorization(authorization)
    validate_contract(approval)
    run = Path(os.environ['GOSC_RUN_DIR'])
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    if any(p.parent!=run and json.loads(p.read_bytes())['status'] in {'running','planned'}
           for p in run.parent.glob('*/status.json')):
        raise SafetyError('another registered project run is active')
    pre_quota = quota_snapshot()
    write_json(out/'quota_before.json',pre_quota)
    if len(os.sched_getaffinity(0))>2:
        raise SafetyError('T3 project CPU affinity exceeds 2')
    data.check_pins()
    candidate = json.loads((ROOT/live.T3_PLAN).read_bytes())
    plan = live.t3_plan(candidate)
    task_plan = plan[2:]
    selected, items, templates = data.development_inputs()
    views = []
    for entry in selected:
        views.append([private_view(items[entry['row']],name) for name in data.NAMES])
    del items
    if [row['family_sha256'] for row in task_plan[::4]]!=[row['family_sha256'] for row in selected]:
        raise SafetyError('development registry and approved plan disagree')
    root = open_hdd(run,live.T3_EVIDENCE_ROOT.name)
    write_json(out/'raw_location.json',{'hdd_root':str(root),'run_id':run.name,'raw_mirrored':False})
    driver = monitor = None
    status = 'failed'
    error = {'stage':'profile-start'}
    def interrupted(signum, frame):
        raise InterruptedError(f'T3 lifecycle signal {signum}')
    for sig in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):
        signal.signal(sig,interrupted)
    try:
        with profile(root,approval) as runtime:
            error['stage']='driver'
            driver = live.LiveDriver(root/'live',runtime,limits(live.T3_WALL_SECONDS-90-(time.monotonic()-begin)),
                                     authorization=authorization,plan=plan)
            monitor = t1.Monitor(runtime,CAPS,driver.control)
            driver.resource_monitor = monitor

            def check_resources():
                monitor()
                if time.monotonic()-begin>live.T3_WALL_SECONDS-120:
                    raise SafetyError('cleanup and rollback time reserve')
                ssd_used = sum(p.stat().st_size for p in run.rglob('*') if p.is_file())
                if ssd_used>live.T3_SSD_BYTES-4*1024**2:
                    raise SafetyError('SSD evidence reserve reached')
            driver.rpc.monitor = check_resources
            driver.dispatch_deadline = begin+live.T3_WALL_SECONDS-180
            try:
                for case in live.t3_cases():
                    error.update(stage='synthetic',episode=case['id'])
                    run_synthetic(driver,case)
                    print(json.dumps({'episode':case['id'],'status':'completed'}),flush=True)
                for row in task_plan:
                    error.update(stage='task',episode=row['id'])
                    check_resources()
                    agents = [LocalAgent(view,templates[row['style']]) for view in views[row['case']-1]]
                    driver.run_episode(row['id'],agents,max_turns=6)
                    if driver.service_touched:
                        driver.recover()
                    print(json.dumps({'episode':row['id'],'status':driver.ledger.state['episodes'][row['id']],
                                      'reserved_requests':len(driver.ledger.state['requests'])}),flush=True)
            finally:
                try:
                    if driver.service_touched and not any(e['kind']=='unload-start' for e in
                            live.runner_epoch(driver.control.rows,live.service_identity(runtime))[0]):
                        driver.recover()
                finally:
                    driver.close()
            error = {'stage':'rollback'}
        status, error = 'completed', None
    except BaseException as exc:
        error['type'] = type(exc).__name__
        lifecycle.record(root/'failure.jsonl','campaign-failure',**error)
    finally:
        summary = {'status':status,'failure':error,'elapsed_seconds':time.monotonic()-begin,
                   'authorization_sha256':live.file_sha(authorization),'raw_mirrored':False}
        if driver:
            summary.update(episodes=driver.ledger.state['episodes'],requests=driver.ledger.state['requests'],
                           inputs_reserved=driver.ledger.state['inputs'],outputs_reserved=driver.ledger.state['outputs'],
                           control_counts=driver.control.used,control_tip=driver.control.previous,
                           ledger_tip=driver.ledger.previous,resource_peaks=monitor.peaks if monitor else None)
        write_json(out/'live_summary.json',summary)
        write_json(out/'hdd_manifest.json',inventory(root))
    return 0 if status=='completed' else 1


if __name__=='__main__':
    raise SystemExit(main())
