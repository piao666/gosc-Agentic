"""Rebind the unchanged T1-B workload after a verified zero-call startup failure."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOCOLS = ROOT / 'research/protocols'
OLD_ID = 'hpc-masbench-t1b-live-v2-20261118'
NEW_ID = 'hpc-masbench-t1b-live-v3-20261118'
PLAN = PROTOCOLS / 'masbench_t1b_synthetic_execution_plan.json'
AUTH = PROTOCOLS / 'masbench_t1b_execution_authorization.json'


def sha(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def archive(name, data):
    with (HERE / name).open('xb') as output:
        output.write(data)


if sys.argv[1:] != ['--after-v2']:
    raise SystemExit('Specify the reconciled second startup failure.')
run = ROOT / 'research/sync/runs' / OLD_ID
summary = (HERE / 't1b_v2_reconcile.json').read_bytes()
result = json.loads(summary)
assert result['status']['status'] == 'failed'
assert result['source_archive']['http_requests'] == result['source_archive']['generation_requests'] == 0
assert hashlib.sha256((run / 'stderr.log').read_bytes()).hexdigest() == result['source_archive']['stderr_sha256']
assert not (run / 'outputs/driver/control.jsonl').exists()
assert (run / 'outputs/driver/campaign/ledger.jsonl').stat().st_size == 0
previous_plan = PLAN.read_bytes()
previous_auth = AUTH.read_bytes()
authority = json.loads(previous_auth)
assert authority['run_id'] == json.loads(previous_plan)['run_id'] == OLD_ID
assert authority['plan_sha256'] == sha(previous_plan)
assert previous_plan.count(OLD_ID.encode()) == 1
replacement = previous_plan.replace(OLD_ID.encode(), NEW_ID.encode())
archive('t1b_v2_authorization.json', previous_auth)
archive('t1b_v2_execution_plan.json', previous_plan)
authority.update(
    run_id=NEW_ID, plan_sha256=sha(replacement),
    prior_zero_call_run=OLD_ID,
    prior_authorization_sha256=sha(previous_auth),
    prior_failure_summary_sha256=hashlib.sha256(summary).hexdigest(),
    rebind_reason='EDQUOT before the first HTTP operation, token reservation, or frozen case',
)
PLAN.write_bytes(replacement)
AUTH.write_bytes((json.dumps(authority, ensure_ascii=False, indent=2) + '\n').encode())
print(json.dumps({'new_run_id': NEW_ID, 'change': 'run identity only', 'plan_sha256': sha(replacement)}))
