"""HPC-only file/ledger audit; never imports a simulator or candidate policy."""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if os.getuid() != 8301880 or str(ROOT) != '/home/u202520081000097/jupyterlab/Paper/gosc':
        raise RuntimeError('Run this evidence audit only on the configured HPC')
    run = ROOT/'research/sync/runs/hpc-pose-contract-tests-20261023'
    status = json.loads((run/'status.json').read_text())
    assert status['status'] == 'completed' and status['exit_code'] == 0
    cases = ET.parse(run/'outputs/pytest.xml').getroot().findall('.//testcase')
    assert len(cases) == 129
    assert not any(c.find('failure') is not None or c.find('error') is not None
                   or c.find('skipped') is not None for c in cases)
    counts = Counter(c.attrib['classname'] for c in cases)
    snapshot = json.loads((run/'source_snapshot.json').read_text())
    entries = {x['path']: x for x in snapshot['files']}
    implementations = [
        'extensions/receiver_pose_interface.py','extensions/receiver_rtt_contract.py',
        'tests_ext/test_receiver_pose_interface.py','tests_ext/test_receiver_rtt_contract.py',
        'research/protocols/receiver_pose_contract_tests_v1.json',
    ]
    guards = [p for p in entries if p.startswith(('gosc/','experiments/','tests/','results/'))
              or p == 'LICENSE']
    checked = implementations + guards
    assert all(sha(ROOT/p) == entries[p]['remote_sha256'] for p in checked)
    protected_diff = subprocess.check_output([
        'git','-C',str(ROOT),'diff','--name-only','HEAD','--',
        'gosc','experiments','tests','results','LICENSE']).decode().strip()
    assert not protected_diff
    package = ROOT/'research/artifacts/r2-r3-20261019'
    manifest = json.loads((package/'manifest.json').read_text())
    assert manifest['file_count'] == len(manifest['files']) == 47
    assert len({e['path'] for e in manifest['files']}) == 47
    for entry in manifest['files']:
        rel = Path(entry['path'])
        assert not rel.is_absolute() and '..' not in rel.parts
        file = package/rel
        assert sha(file) == entry['sha256'] == sha(ROOT/entry['source'])
        assert file.stat().st_size == entry['bytes']
        reference = json.loads((ROOT/'research/sync/runs'/entry['run_id']/'artifacts.json').read_text())
        registered = {e['path']:e for e in reference['files']}
        source_relative = Path(entry['source']).relative_to('research/sync/runs/'+entry['run_id']).as_posix()
        assert registered[source_relative]['sha256'] == entry['sha256']
    result = {
        'status':'passed', 'audit_scope':'Separate stdlib audit of files/JUnit/registered hashes; no new simulation or statistical effect test',
        'test_run':run.name,'test_counts_by_module':dict(counts),'tests':len(cases),
        'new_contract_tests':sum(n for name,n in counts.items() if name in (
            'tests_ext.test_receiver_pose_interface','tests_ext.test_receiver_rtt_contract')),
        'source_sync_id':snapshot['sync_id'],
        'guarded_files':len(guards),'implementation_test_protocol_files':len(implementations),
        'protected_git_changes':protected_diff,'delivery_files':47,
        'delivery_bytes':sum(e['bytes'] for e in manifest['files']),
        'delivery_manifest_sha256':sha(package/'manifest.json'),
        'paid_task_effect_tested':False,'training':False,'new_llm_calls':0,
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'pose_delivery_integrity_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
