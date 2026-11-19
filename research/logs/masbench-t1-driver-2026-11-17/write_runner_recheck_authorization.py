"""Bind a separately approved runner recheck to a fresh preflight and source."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOCOLS = ROOT/'research/protocols'
modes = {'--formal': 'formal', '--formal-runner-retest': 'formal_runner_retest'}
name = modes.get(sys.argv[1] if len(sys.argv)>1 else '', 'post_storage')
arguments = sys.argv[2:] if name!='post_storage' else sys.argv[1:]
PLAN = PROTOCOLS/f'masbench_t1b_{name}_plan.json'
AUTH = PROTOCOLS/f'masbench_t1b_{name}_authorization.json'
FILES = {
    'protocol_sha256':PROTOCOLS/f'masbench_t1b_{name}_budget_2026-11-19.md',
    'plan_sha256':PLAN,
    'source_sha256':ROOT/'extensions/masbench_reasoning/live_driver.py',
    'runner_sha256':ROOT/'experiments_ext/masbench_t1b_live.py',
    'registry_sha256':ROOT/'research/artifacts/native-masbench-20261104/masbench_development_registry.json',
}


if len(arguments)!=1 or not arguments[0].strip():
    raise SystemExit('Supply the separate user approval for this run and exclusive use.')
preflight_name = {'formal':'t1_formal_preflight_20261119.json',
                  'formal_runner_retest':'t1_formal_runner_retest_preflight_20261119.json',
                  'post_storage':'t1_post_storage_preflight.json'}[name]
preflight = json.loads((HERE/preflight_name).read_bytes())
assert preflight['host']=='n1' and preflight['uid']==preflight['service_uid']==8301880
assert preflight['loopback_listener_count']==1 and preflight['loopback_own_listener']
assert preflight['established_connections']==0 and preflight['registered_running']==[]
assert preflight['lease_marker']==0 and preflight['gpu'].split(',')[0].strip()=='0 MiB'
assert preflight['service_env']['OLLAMA_HOST']=='127.0.0.1:11434'
assert preflight['service_env']['OLLAMA_CONTEXT_LENGTH']=='1024'
assert preflight['service_env']['OLLAMA_NUM_PARALLEL']==preflight['service_env']['OLLAMA_MAX_LOADED_MODELS']=='1'
assert preflight['helper_sha256']=='e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5'
data = {
    'approved':True, 'scope':'T1-B synthetic only', 'exclusive_service':True,
    'service_exclusivity_confirmation':arguments[0].strip(),
    'run_id':json.loads(PLAN.read_bytes())['run_id'],
    'previous_t1b_run': {'formal':'hpc-masbench-t1b-post-storage-20261119',
                         'formal_runner_retest':'hpc-masbench-t1b-formal-20261119',
                         'post_storage':'hpc-masbench-t1b-runner-recheck-20261118'}[name],
}
if name=='formal_runner_retest':
    path = HERE/'t1_formal_marker_recovery_applied_20261119.json'
    recovery = json.loads(path.read_bytes())
    assert recovery['original_run']==data['previous_t1b_run'] and recovery['cleared_at']
    FILES['previous_recovery_receipt_sha256'] = path
for field in ('service_pid','service_stamp','service_binary_sha256'):
    data[field] = preflight[field]
for field,path in FILES.items():
    data[field] = hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
with AUTH.open('x',encoding='utf-8',newline='\n') as output:
    json.dump(data,output,ensure_ascii=False,indent=2)
    output.write('\n')
