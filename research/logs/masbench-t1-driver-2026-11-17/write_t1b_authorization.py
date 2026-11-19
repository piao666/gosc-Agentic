"""Freeze user-confirmed T1-B authority. This script never starts the campaign."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUTH = ROOT/'research/protocols/masbench_t1b_execution_authorization.json'
FIELDS = {
    'protocol_sha256':'research/protocols/masbench_t1b_synthetic_budget_proposal_2026-11-18.md',
    'registry_sha256':'research/artifacts/native-masbench-20261104/masbench_development_registry.json',
    'plan_sha256':'research/protocols/masbench_t1b_synthetic_execution_plan.json',
    'source_sha256':'extensions/masbench_reasoning/live_driver.py',
    'runner_sha256':'experiments_ext/masbench_t1b_live.py',
}


def main():
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        raise SystemExit('Supply the user confirmation that the service is exclusive during the campaign.')
    preflight = json.loads((HERE/'t1b_preflight.json').read_bytes())
    if (preflight['host']!='n1' or preflight['service_uid']!=preflight['uid']
            or preflight['loopback_listener_count']!=1 or not preflight['loopback_own_listener']
            or preflight['established_connections'] or preflight['registered_running']
            or preflight['lease_marker'] not in (0,None)):
        raise RuntimeError('observed service is not ready for exclusive use')
    data = {
        'approved':True, 'scope':'T1-B synthetic only', 'exclusive_service':True,
        'authorization':'用户：批准按提案开展 T1-B',
        'service_exclusivity_confirmation':sys.argv[1].strip(),
        'run_id':'hpc-masbench-t1b-live-20261118',
    }
    for field in ['service_pid','service_stamp','service_binary_sha256']:
        data[field] = preflight[field]
    for field, name in FIELDS.items():
        source = (ROOT/name).read_bytes().replace(b'\r\n',b'\n')
        data[field] = hashlib.sha256(source).hexdigest()
    with AUTH.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
