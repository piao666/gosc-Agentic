"""One HPC campaign for frozen T1-B synthetic cases."""
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from hpc_runs import require_hpc, resource_limits, write_json
from extensions.masbench_reasoning import live_driver as live
from extensions.masbench_reasoning.application import LocalAgent, PrivateView
from extensions.masbench_reasoning.client import ClientFailure
from extensions.masbench_reasoning.execution_safety import Limits, SafetyError

AUTH = ROOT / live.FORMAL_AUTH
PLAN = ROOT / live.FORMAL_PLAN
HELPER = '/tmp/gosc-hpc-masbench-context-build-v3-20261116/context-counter'


def command(*args, timeout=1):
    return subprocess.check_output(args, text=True, timeout=timeout).strip()


def own_listener(runtime):
    lines = command('ss', '-Hlnpt', 'sport = :11434').splitlines()
    if (len(lines) != 1 or '127.0.0.1:11434' not in lines[0]
            or f'pid={runtime.service_pid},' not in lines[0]):
        raise SafetyError('loopback listener identity changed')
    if command('ss', '-Hnt', 'sport = :11434 or dport = :11434'):
        # TIME-WAIT belongs to closed sockets and does not represent activity.
        established = command('ss', '-Hnt', 'state', 'established',
                              'sport = :11434 or dport = :11434')
        if established:
            raise SafetyError('active connection on project service')


def process_rss(driver_pid, service_pid, rows=None):
    if rows is None:
        rows = process_rows()

    def descendants(root_pid):
        found = {root_pid}
        while True:
            expanded = found | {pid for pid, (parent, _) in rows.items() if parent in found}
            if expanded == found:
                return found
            found = expanded

    page = os.sysconf('SC_PAGE_SIZE')
    service = descendants(service_pid)
    driver = descendants(driver_pid) - service
    return (sum(rows[pid][1] for pid in driver if pid in rows) * page,
            sum(rows[pid][1] for pid in service if pid in rows) * page)


def process_rows():
    rows = {}
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            fields = (proc / 'stat').read_text().rsplit(') ', 1)[1].split()
            rows[int(proc.name)] = (int(fields[1]), max(0, int(fields[21])))
        except (OSError, ValueError, IndexError):
            continue
    return rows


class Monitor:
    def __init__(self, runtime, caps, control):
        self.runtime = runtime
        self.caps = caps
        self.control = control
        self.last = 0.0
        self.samples = 0
        self.peaks = dict(driver_rss=0, service_rss=0, gpu_bytes=0)
        self.failure = None

    def __call__(self, cleanup=False, force=False):
        if self.failure and not cleanup:
            raise SafetyError(self.failure)
        if not force and time.monotonic() - self.last < .5:
            return
        self.last = time.monotonic()
        try:
            if live.proc_stamp(self.runtime.service_pid) != self.runtime.service_stamp:
                raise SafetyError('service PID drift')
            gpu = command('nvidia-smi', '--query-gpu=memory.used',
                          '--format=csv,noheader,nounits', timeout=.45)
            driver_rss,service_rss = process_rss(os.getpid(),self.runtime.service_pid)
            values = {
                'driver_rss': driver_rss,
                'service_rss': service_rss,
                'gpu_bytes': sum(int(line) for line in gpu.splitlines()) * 1024**2,
            }
            self.samples += 1
            for key, value in values.items():
                self.peaks[key] = max(self.peaks[key], value)
            if any(values[key] > self.caps[key] for key in values):
                raise SafetyError('resource cap exceeded')
            return values
        except (OSError, ValueError, subprocess.SubprocessError, SafetyError) as exc:
            if not self.failure:
                self.failure = str(exc)[:160]
                self.control.append({'kind': 'resource-stop', 'reason': self.failure})
            if not cleanup:
                raise SafetyError(self.failure) from exc


def events_since(driver, start):
    return [row['event'] for row in driver.control.rows[start:]]


def validate_case(driver, case, start, response, error):
    rows = events_since(driver, start)
    kinds = {event['kind'] for event in rows}
    request = driver.ledger.state['requests'].get(driver.pending)
    if request is None:
        raise SafetyError(f'case did not reach generation: {case["id"]}')
    if case['fault'] == 'none':
        if error or not isinstance(response, str) or response.strip() != 'OK':
            raise SafetyError('normal response/usage check failed')
        if request['status'] != 'completed' or request['observed_usage'] is None:
            raise SafetyError('normal request did not settle with usage')
    else:
        expected = 'timeout' if case['fault'] == 'timeout' else 'interrupted'
        marker = 'rpc-timeout' if expected == 'timeout' else 'controller-exit'
        for kind in ['fault-trigger-armed', marker, 'unload-complete', 'dispatch-permit-evaluated']:
            if kind not in kinds:
                raise SafetyError('fault path lacked evidence: '+kind)
        if not error or request['status'] != expected or request['observed_usage'] is not None:
            raise SafetyError('fault condition did not trigger before completion')
        if 'generation-result-observed' in kinds:
            raise SafetyError('terminal response observed before cancellation completed')
        proof = next(event['observation'] for event in rows if event['kind']=='unload-complete')
        if not proof['process_observations'] or driver.service_touched:
            raise SafetyError('no owned runner observed through unload')
        permits = [row for row in rows if row['kind']=='dispatch-permit-evaluated']
        if not permits[-1]['permitted']:
            raise SafetyError('continued dispatch forbidden after recovery')
    return {'id':case['id'], 'request_id':driver.pending, 'status':request['status'],
            'reserved_input':request['input'], 'reserved_output':request['output'],
            'usage':request['observed_usage']}


def run_case(driver, case):
    start = len(driver.control.rows)
    driver.pending = None
    driver.control.append({'kind':'case-start','id':case['id'],'max_output':case['max_output']})
    driver.armed_case = case
    response = error = None
    try:
        if case['fault'] == 'interrupt':
            agents = [
                LocalAgent(PrivateView('Alice','Bob','Fictitious check',''), case['messages'][0]['content']),
                LocalAgent(PrivateView('Bob','Alice','Fictitious check',''), 'Unused fictitious turn.'),
            ]
            driver._guard_application(agents, {'id':'synthetic','style':'base','condition':'No-A2A'}, 1, None)
        else:
            response = driver.generate(case['messages'])
    except (SafetyError, ClientFailure, OSError) as exc:
        error = str(exc)[:160]
        driver.control.append({'kind':'case-error','id':case['id'],'message':error})
    result = validate_case(driver, case, start, response, error)
    driver.control.append(dict(result, kind='case-end'))
    return result


def main(authorization=AUTH, fixture_id='hpc-masbench-t1b-formal-runner-retest-contract-20261119',
         expected_service=None):
    begin = time.monotonic()
    require_hpc()
    approval = live.require_authorization(authorization)
    plan = json.loads((ROOT/approval['plan_path']).read_bytes())
    caps = plan['caps']
    if approval['run_id'] != plan['run_id']:
        raise SafetyError('wrong frozen run identity')
    fixture = ROOT/'research/sync/runs'/fixture_id
    if json.loads((fixture/'status.json').read_bytes())['status']!='completed':
        raise SafetyError('formal no-network fixture did not pass')
    if approval.get('service_exclusivity_confirmation', '') == '':
        raise SafetyError('campaign exclusivity confirmation missing')
    cgroup = resource_limits()
    if int(cgroup['cpu_quota']) != 2 * int(cgroup['cpu_period']):
        raise SafetyError('CPU quota drift')
    state = json.loads((ROOT/'.local/ollama/service.json').read_bytes())
    pid = state['pid']
    binary = ROOT/'.local/ollama/runtime/0.11.11/bin/ollama'
    runtime = live.Runtime(str(ROOT), HELPER, pid, live.proc_stamp(pid), live.file_sha(binary), approval['context'])
    service = approval if expected_service is None else expected_service
    if (pid != service.get('service_pid') or runtime.service_stamp != service.get('service_stamp')
            or runtime.binary_sha != service.get('service_binary_sha256')):
        raise SafetyError('frozen service identity changed')
    live.runtime_files(runtime)
    own_listener(runtime)
    if live.runner_identities(runtime):
        raise SafetyError('model runner present before campaign')
    run_dir = Path(os.environ['GOSC_RUN_DIR'])
    other_running = []
    for p in run_dir.parent.glob('*/status.json'):
        if p.parent != run_dir and json.loads(p.read_bytes()).get('status') == 'running':
            other_running.append(p.parent.name)
    if other_running:
        raise SafetyError('another project run is active')
    limits = Limits(requests=caps['requests'], metadata=caps['get']+caps['cleanup_get'],
        input_tokens=caps['inputs'], output_tokens=caps['outputs'], per_output=512,
        wall_seconds=caps['wall']-(time.monotonic()-begin), operation_seconds=caps['operation'],
        artifact_bytes=caps['artifact_bytes']-128*1024-16*1024)
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    campaign = out/'driver'
    if campaign.exists():
        raise SafetyError('frozen campaign cannot be replayed')
    driver = live.LiveDriver(campaign, runtime, limits, authorization=authorization)
    monitor = Monitor(runtime, caps, driver.control)
    driver.resource_monitor = monitor
    driver.rpc.monitor = monitor
    driver.dispatch_deadline = begin + caps['dispatch_cutoff']
    report = {'runtime':runtime.identity(), 'caps':caps, 'cases':[], 'status':'failed',
              'actual_task_inputs':0, 'native_immediate_idle_verified':False}

    def interrupted(signum, frame):
        raise InterruptedError(f'campaign received OS signal {signum}')

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    try:
        monitor()
        driver.operation_deadline = time.monotonic()+caps['operation']
        first = plan['overflow']
        negative = [{'role':'system','content':first['system']*first['repetitions']}]
        before = dict(driver.control.used)
        try:
            driver.attest(negative, first['max_output'])
        except ClientFailure as exc:
            if exc.reason != 'context_overflow_no_truncation' or before != driver.control.used:
                raise
            driver.control.append({'kind':'overflow-blocked-before-http'})
        else:
            raise SafetyError('overflow case was not blocked')
        for case in plan['cases']:
            own_listener(runtime)
            report['cases'].append(run_case(driver, case))
        driver.recover()
        own_listener(runtime)
        monitor(cleanup=True)
        if monitor.failure or live.runner_identities(runtime) or driver.service_lease.owner():
            raise SafetyError('final lease/runner/resource state unverified')
        report['status'] = 'synthetic_driver_contract_passed'
    except BaseException as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'[:240]
        # A cleanup attempt made by the Driver owns its existing reservation.
        # Do not retry a failed unload or interfere with another client.
        last = [r['event']['kind'] for r in driver.control.rows
                if r['event']['kind'] in {'unload-start','unload-complete'}]
        if driver.service_touched and (not last or last[-1] == 'unload-complete'):
            try:
                own_listener(runtime)
                driver.recover()
            except BaseException as cleanup:
                report['cleanup_error'] = f'{type(cleanup).__name__}: {cleanup}'[:240]
        raise
    finally:
        report.update(
            elapsed_seconds=time.monotonic()-begin,
            control_counts=driver.control.used,
            reservations={key:driver.ledger.state[key] for key in ['requests','inputs','outputs']},
            resource_samples=monitor.samples, sampled_peaks=monitor.peaks,
            service_marker_retained=bool(driver.service_lease.owner()),
        )
        driver.close()
        write_json(out/'summary.json', report)


if __name__ == '__main__':
    main()
