"""Preserve the specific failed formal T1 lease and recover only an idle service."""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from experiments_ext.masbench_t1_runner_evidence_audit import read_chain, require, sha_bytes, verify_artifacts
from extensions.masbench_reasoning.live_driver import Runtime, file_sha, proc_stamp, runner_identities, runtime_files
from experiments_ext.masbench_t1b_live import HELPER, own_listener

RUNS = ROOT/'research/sync/runs'
FAILED = RUNS/'hpc-masbench-t1b-formal-20261119'
AUDIT = RUNS/'hpc-masbench-t1b-formal-audit-detail-20261119'
LEASE = ROOT/'.local/t1-service.lock'
ARCHIVE_PARENT = Path('/hdd/u202520081000097/gosc-archive')
ARCHIVE = ARCHIVE_PARENT/'2026-11-19-t1-formal-failed-lease'
MARKER_SHA = 'b5b58650e78e392a8b58700e0e438414f4d0cf2d2440abf9c87da156dca4a52b'
SERVICE = Runtime(str(ROOT), HELPER, 37483, '4897373256',
                  'e014750cd656db3a77f3bf6b45903f646c76075e58b835cc9787fb5fc8a8a600')


def now():
    return datetime.now(timezone.utc).isoformat()


def preserve(path, body):
    with path.open('xb') as file:
        file.write(body)
        file.flush()
        os.fsync(file.fileno())
    require(file_sha(path)==sha_bytes(body),'HDD readback mismatch')


def fsync_dir(path):
    descriptor = os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def idle(identities):
    runtime_files(SERVICE)
    own_listener(SERVICE)
    require(not runner_identities(SERVICE),'project runner still present')
    observed = [dict(row,observed_stamp=proc_stamp(row['pid'])) for row in identities]
    require(all(row['stamp']!=row['observed_stamp'] for row in observed),'recorded runner still present')
    gpu = subprocess.check_output(['nvidia-smi','--query-gpu=memory.used',
                                   '--format=csv,noheader,nounits'],timeout=5,text=True).strip()
    require(gpu=='0','GPU currently occupied')
    require(all(json.loads(path.read_bytes())['status'] not in {'running','planned'}
                for path in RUNS.glob('*/status.json')),'active job prevents lease recovery')
    return {'utc':now(),'service_pid':SERVICE.service_pid,'service_stamp':SERVICE.service_stamp,
            'runner_exit_observations':observed,'own_listener_idle':True,'gpu_used_mib':0}


def main():
    require(sys.argv[1:] in ([],['--apply']),'unexpected argument')
    require(os.getuid()==8301880 and os.uname().nodename=='n1' and ROOT.resolve()==ROOT,'wrong HPC identity')
    require(LEASE.resolve()==LEASE and ARCHIVE_PARENT.resolve()==ARCHIVE_PARENT
            and ARCHIVE_PARENT.is_dir() and os.path.ismount(ARCHIVE_PARENT.parent.parent),'HDD archive mount missing')
    apply = sys.argv[1:]==['--apply']
    flags = os.O_NOFOLLOW | (os.O_RDWR if apply else os.O_RDONLY)
    with os.fdopen(os.open(LEASE,flags),'r+b' if apply else 'rb',buffering=0) as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        marker = lock.read(4097)
        require(len(marker)==210 and sha_bytes(marker)==MARKER_SHA,'unexpected active marker')
        owner = json.loads(marker)
        driver = FAILED/'outputs/driver'
        require(owner['campaign']==str(driver),'wrong marker campaign')
        state = json.loads((FAILED/'status.json').read_bytes())
        require(state['status']=='failed' and state['exit_code']==1 and proc_stamp(state['pid']) is None,
                'prior campaign still active or identity changed')
        verify_artifacts(FAILED)
        verify_artifacts(AUDIT)
        ledger = read_chain(driver/'campaign/ledger.jsonl')
        control = read_chain(driver/'control.jsonl')
        require(ledger[0]['event']['binding']==owner['ledger_binding']==control[0]['event']['identity'],
                'marker not bound to the prior evidence')
        finishes = [row['event'] for row in ledger if row['event']['kind']=='finish']
        require(len(finishes)==4 and [(r['id'],r['status']) for r in finishes if r['usage'] is None]==
                [('synthetic/1','timeout'),('synthetic/2','interrupted')], 'prior usage evidence changed')
        audit = json.loads((AUDIT/'outputs/audit.json').read_bytes())
        failure = audit['final_cleanup_failure']
        start, stop = failure['start'], failure['stop']
        require(audit['acceptance_passed'] is False and control[start['seq']]==start and control[stop['seq']]==stop,
                'original audit no longer matches the live evidence')
        observation = stop['event']['observation']
        require(observation['ps']=={'models':[]} and observation['remaining_runners']==[]
                and observation['response']['done_reason']=='unload','prior unload evidence changed')
        identities = start['event']['old_runners']+failure['unbound_runner_identities']
        require(identities==[{'pid':54817,'stamp':'4915893959'},{'pid':54844,'stamp':'4915894302'}],
                'prior runner identities changed')
        before = idle(identities)
        record = {'marker_sha256':MARKER_SHA,'original_run':FAILED.name,'previous_finishes':finishes,
                  'original_ledger_sha256':file_sha(driver/'campaign/ledger.jsonl'),'idle_check':before,
                  'archive':str(ARCHIVE),'administrative_recovery':True,'model_calls':0,'http_requests':0}
        if apply:
            ARCHIVE.mkdir(mode=0o700)
            evidence = {'t1-service.lock':marker,
                        'control.jsonl':(driver/'control.jsonl').read_bytes(),
                        'ledger.jsonl':(driver/'campaign/ledger.jsonl').read_bytes(),
                        'status.json':(FAILED/'status.json').read_bytes(),
                        'summary.json':(FAILED/'outputs/summary.json').read_bytes(),
                        'audit.json':(AUDIT/'outputs/audit.json').read_bytes()}
            for name,body in evidence.items():
                preserve(ARCHIVE/name,body)
            record['files'] = {name:sha_bytes(body) for name,body in evidence.items()}
            record['pre_clear_check'] = idle(identities)
            preserve(ARCHIVE/'pre-clear.json',json.dumps(record,indent=2).encode()+b'\n')
            fsync_dir(ARCHIVE)
            fsync_dir(ARCHIVE_PARENT)
            lock.seek(0)
            require(lock.read(4097)==marker,'marker identity changed after archive')
            lock.truncate(0)
            os.fsync(lock.fileno())
            require(os.fstat(lock.fileno()).st_size==0,'active marker did not clear')
            record['cleared_at'] = now()
            preserve(ARCHIVE/'completion.json',json.dumps(record,indent=2).encode()+b'\n')
            fsync_dir(ARCHIVE)
        print(json.dumps(record))


if __name__=='__main__':
    main()
