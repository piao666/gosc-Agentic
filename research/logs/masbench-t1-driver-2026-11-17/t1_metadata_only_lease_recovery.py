"""Retire the exact stale lease from the failed, metadata-only T1 campaign."""
from datetime import datetime, timezone
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
RUNS = ROOT/'research/sync/runs'
RUN = RUNS/'hpc-masbench-t1b-runner-recheck-20261118'
ARCHIVE = Path('/hdd/u202520081000097/gosc-archive/2026-11-18-ssd-relief-v1')
LEASE = ROOT/'.local/t1-service.lock'
OUTPUTS = RUN/'outputs/driver'
SERVICE = {'pid':37483,'stamp':'4897373256'}
MARKER_SHA = '2e6b8f8af8eade765e04f77dd0ff1a16c97b226cfa442c7e1302ccd9ef032eb7'
SERVICE_SHA = 'e014750cd656db3a77f3bf6b45903f646c76075e58b835cc9787fb5fc8a8a600'
JOURNAL_TIPS = {
    'control':'0cf2af91fb7c9bb3c10b1c4c18e38e0fd2f1ec4a3722f4b479ee9f10412577f6',
    'ledger':'bffa52a71e65455c53d1986a4812957296180da92ffd77b968c925151e31d5c0',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',', ':')).encode()


def utc():
    return datetime.now(timezone.utc).isoformat()


def proc_stamp(pid):
    try:
        return (Path('/proc')/str(pid)/'stat').read_text().rsplit(') ',1)[1].split()[19]
    except (FileNotFoundError, ProcessLookupError):
        return None


def command(*args):
    return subprocess.check_output(args,text=True,timeout=4).strip()


def read_chain(path, expected_tip):
    rows = []
    prior = '0'*64
    for raw in path.read_bytes().rstrip(b'\0').splitlines(keepends=True):
        row = json.loads(raw)
        actual = row.pop('hash')
        assert raw.endswith(b'\n') and row['seq']==len(rows) and row['previous']==prior and sha(canonical(row))==actual
        prior = actual
        rows.append(row['event'])
    assert prior==expected_tip
    return rows


def snapshot():
    current = json.loads((ROOT/'.local/ollama/service.json').read_bytes())['pid']
    assert current==SERVICE['pid'] and proc_stamp(current)==SERVICE['stamp']
    listen = command('ss','-Hlnpt','sport = :11434')
    assert len(listen.splitlines())==1 and '127.0.0.1:11434' in listen and f'pid={current},' in listen
    assert not command('ss','-Hnt','state','established','sport = :11434 or dport = :11434')
    children = subprocess.run(['ps','--ppid',str(current),'-o','pid='],capture_output=True,text=True,timeout=4)
    assert children.returncode==1 and not children.stdout.strip() and not children.stderr.strip()
    gpu = command('nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits')
    assert gpu=='0'
    for p in RUNS.glob('*/status.json'):
        assert json.loads(p.read_bytes())['status'] not in ('running','planned')
    return {'utc':utc(),'service':SERVICE,'children':[],'established':0,'gpu_used_mib':0}


def metadata(path):
    assert path in ('/api/ps','/api/version')
    conn = http.client.HTTPConnection('127.0.0.1',11434,timeout=3)
    try:
        conn.request('GET',path)
        response = conn.getresponse()
        body = response.read(64*1024+1)
        assert response.status==200 and len(body)<=64*1024
        value=json.loads(body)
    finally:
        conn.close()
    return value


def preserve(path,data):
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    assert path.read_bytes()==data
    fd = os.open(path.parent,os.O_DIRECTORY|os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


assert os.getuid()==8301880 and os.uname().nodename=='n1' and ROOT.resolve()==ROOT and ARCHIVE.resolve()==ARCHIVE
with os.fdopen(os.open(LEASE,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC),'r+b',buffering=0) as lock:
    fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    owner = lock.read(4096)
    assert len(owner)==218 and sha(owner)==MARKER_SHA
    arm = json.loads(owner)
    assert arm['campaign']==str(OUTPUTS)
    state_body = (RUN/'status.json').read_bytes()
    state = json.loads(state_body)
    assert state['status']=='failed' and state['exit_code']==120 and proc_stamp(state['pid']) is None
    versions = ARCHIVE/'t1_failed_run_control_versions_2026-11-19'
    version_record = json.loads((versions/'comparison.json').read_bytes())
    local_registered_mirror = versions/'registered_mirror.control.jsonl'
    current = (OUTPUTS/'control.jsonl').read_bytes()
    mirror = local_registered_mirror.read_bytes()
    assert current==(versions/'current_ssd.control.jsonl').read_bytes()
    assert sha(current)==version_record['current_ssd_sha256'] and sha(mirror)==version_record['registered_mirror_sha256']
    recorded = next(e for e in json.loads((RUN/'artifacts.json').read_bytes())['files']
                    if e['path']=='outputs/driver/control.jsonl')
    assert sha(mirror)==recorded['sha256']
    assert mirror.rstrip(b'\0').startswith(current.rstrip(b'\0'))
    control = read_chain(local_registered_mirror,JOURNAL_TIPS['control'])
    assert len(control)==22 and control[-1]=={'kind':'charge','category':'cleanup_get'}
    ledger = read_chain(OUTPUTS/'campaign/ledger.jsonl',JOURNAL_TIPS['ledger'])
    assert control[0]['identity']==ledger[0]['binding']==arm['ledger_binding']
    assert all(event['kind'] not in ('request','finish','barrier') for event in ledger)
    assert not any(event['kind'] in ('runner-dispatch-bound','unload-complete','dispatch-permit-evaluated') for event in control)
    for event in control:
        if event['kind'] in ('rpc-spawn','application-spawn'):
            assert event['stamp'] is not None and proc_stamp(event['pid'])!=event['stamp']
    reviewed = json.loads((ARCHIVE/'t1_499_review_2026-11-19.json').read_bytes())
    assert reviewed['failed_run_status_sha256']==sha(state_body)
    sends = [e['request_sha256'] for e in control if e['kind']=='http-sent']
    assert sends==['b239988bff80251674e464c5d38fe009e65420df77284bd84542d8a2248b9233',
                   '18f0ad7022b91ae2523c248dab4ef1056328404e1e57cda12e2424953ac415a6']
    for artifact in json.loads((RUN/'artifacts.json').read_bytes())['files']:
        saved = mirror if artifact['path']==recorded['path'] else (RUN/artifact['path']).read_bytes()
        assert len(saved)==artifact['size'] and sha(saved)==artifact['sha256']
    service_exe = Path('/proc')/str(SERVICE['pid'])/'exe'
    with service_exe.open('rb') as binary:
        assert hashlib.file_digest(binary,'sha256').hexdigest()==SERVICE_SHA
    observations = [snapshot()]
    version = metadata('/api/version')
    ps_before = metadata('/api/ps')
    assert version=={'version':'0.11.11'} and ps_before=={'models':[]}
    time.sleep(2)
    observations.append(snapshot())
    ps_after = metadata('/api/ps')
    assert ps_after=={'models':[]}
    observations.append(snapshot())
    assert os.path.samestat(os.fstat(lock.fileno()),LEASE.stat())
    marker = ARCHIVE/'t1_stale_lease_original_2026-11-19.json'
    intent = ARCHIVE/'t1_stale_lease_release_intent_2026-11-19.json'
    receipt = ARCHIVE/'t1_stale_lease_release_2026-11-19.json'
    data = {'authorization':'按用户指示在 SSD 恢复写入后处理 T1 恢复锁',
            'old_run':RUN.name,'old_run_status':'failed','old_run_proven_generation_count':0,
            'old_run_sha256':sha(state_body),'journal_tips':JOURNAL_TIPS,
            'control_version_record':str(versions/'comparison.json'),
            'marker_sha256':MARKER_SHA,'marker_bytes':len(owner),'marker_backup':str(marker),
            'observations':observations,'api_version':version,'api_ps':[ps_before,ps_after],
            'metadata_get_count':3,'generation_calls':0,'model_unload_calls':0,
            'historic_runner_exit_verified':False,'live_t1_acceptance_passed':False}
    preserve(marker,owner)
    preserve(intent,canonical(dict(data,status='verified_ready_for_administrative_release',utc=utc()))+b'\n')
    try:
        snapshot()
        lock.seek(0)
        assert lock.read(4096)==owner
        lock.truncate(0)
        os.fsync(lock.fileno())
        assert LEASE.stat().st_size==0
        completion = dict(data,status='stale_metadata_only_lease_retired',finished_utc=utc(),lease_bytes_after=0)
        preserve(receipt,canonical(completion)+b'\n')
    except BaseException:
        lock.seek(0)
        lock.write(owner)
        lock.truncate(len(owner))
        os.fsync(lock.fileno())
        raise
print(json.dumps(dict(completion,hdd_receipt=str(receipt))))
