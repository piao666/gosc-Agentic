"""Read only the registered T1-B quota failure and current guarded service."""
from pathlib import Path
from collections import deque
import hashlib
import json
import re
import subprocess

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
run=root/'research/sync/runs/hpc-masbench-t1b-runner-recheck-20261118'
outputs=run/'outputs'
def chain(path):
    rows = []
    prior = '0'*64
    for line in path.read_bytes().rstrip(b'\0').splitlines(keepends=True):
        row = json.loads(line)
        actual = row.pop('hash')
        assert line.endswith(b'\n') and row['seq']==len(rows) and row['previous']==prior
        assert canonical_sha(row)==actual
        rows.append(dict(row, hash=actual))
        prior = actual
    return rows

def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

control=chain(outputs/'driver/control.jsonl')
ledger=chain(outputs/'driver/campaign/ledger.jsonl')
assert ledger[0]['event']['binding']==control[0]['event']['identity']
auth = root/'research/protocols/masbench_t1b_runner_recheck_authorization.json'
plan = json.loads((root/'research/protocols/masbench_t1b_runner_recheck_plan.json').read_bytes())
specifications = {
    'initial_ps':{'kind':'http','method':'GET','path':'/api/ps','body':None},
    'debug_render':{'kind':'http','method':'POST','path':'/api/chat','body':{
        'model':plan['runtime']['model'],'messages':plan['cases'][0]['messages'],'stream':False,
        '_debug_render_only':True,'options':{'num_thread':2}}},
}
send_hashes = {canonical_sha(dict(spec,authorization=str(auth))):name for name,spec in specifications.items()}
sends = [send_hashes[row['event']['request_sha256']] for row in control if row['event']['kind']=='http-sent']
assert sends==['initial_ps','debug_render']
assert all(row['event']['kind'] not in ('request','finish','barrier') for row in ledger)
assert not any(row['event']['kind'] in ('runner-observed','runner-dispatch-bound','unload-start',
               'unload-complete','generation-result-observed','dispatch-permit-evaluated') for row in control)
registered = json.loads((run/'artifacts.json').read_bytes())['files']
for item in registered:
    data = (run/item['path']).read_bytes()
    assert len(data)==item['size'] and hashlib.sha256(data).hexdigest()==item['sha256']
for row in ledger:
    event = row['event']
    if event['kind']=='bytes':
        data = (outputs/'driver/campaign/artifacts'/event['path']).read_bytes()
        assert len(data)==event['count'] and hashlib.sha256(data).hexdigest()==event['sha256']
route = re.compile(r'\[GIN\] (2026/11/18 - (?:07|15):4[34]:\d\d) \|\s*(\d+)\s*\|[^\n]*?\b(GET|POST)\s+"(/[^"]+)"$')
service = root/'.local/ollama/service.log'
with service.open(encoding='utf-8',errors='replace') as stream:
    lines = deque(stream, maxlen=2000)
routes = [{'time':m[1],'response':int(m[2]),'method':m[3],'path':m[4]} for line in lines
          if (m:=route.search(line.rstrip())) and m[4] in ('/api/ps','/api/chat','/v1/chat/completions')]
kinds={'runner-observed','runner-dispatch-bound','http-sent','case-start','case-end','case-error',
       'generation-result-observed','client-failure','unload-start','unload-unverified','unload-complete',
       'dispatch-permit-evaluated','rpc-timeout','resource-stop','controller-signal','controller-exit'}
lease=(root/'.local/t1-service.lock').read_bytes()
print(json.dumps({
    'status':json.loads((run/'status.json').read_bytes()),
    'control_events':len(control),'ledger_events':len(ledger),
    'control_tip':control[-1]['hash'],'ledger_tip':ledger[-1]['hash'],
    'artifacts_verified':len(registered),'wire_hashes_matched':sends,'generation_requests':0,
    'server_routes':routes,
    'key_control_events':[r for r in control if r['event']['kind'] in kinds],
    'ledger_reservations':[r for r in ledger if r['event']['kind'] in ('request','finish','barrier')],
    'last_control':control[-1]['event'],'last_ledger':ledger[-1]['event'],
    'lease_bytes':len(lease),'lease_sha256':hashlib.sha256(lease).hexdigest(),
    'lease_binding':json.loads(lease) if lease else None,
    'summary_exists':(outputs/'summary.json').exists(),
    'stderr_bytes':(run/'stderr.log').stat().st_size,
    'live_test_process_exists':Path('/proc/56831').exists(),
    'service_direct_children':subprocess.run(
        ['ps','--ppid','37483','-o','pid=,stat=,comm='],capture_output=True,text=True,check=False).stdout.splitlines(),
    'gpu_memory':subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader'],
                                          text=True).strip(),
    'root_log_end_file_bytes':(root/'.local/ollama/service.log').stat().st_size,
}))
