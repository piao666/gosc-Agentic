"""Local lightweight file/hash/receipt verification only; no research computation."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
LOG = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    old = json.loads((ROOT/'research/artifacts/native-masbench-20261104/native_frozen.json').read_bytes())
    mismatches = [p for p,h in old['source_sha256'].items()
                  if sha((ROOT/p).read_bytes().replace(b'\r\n', b'\n')) != h]
    evidence = []
    manifest = {'archive_head': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
                'scientific_baseline': '014b85dfc472c45d8ea5f15e83e0c1ed8e938daf',
                'third_party_commit': 'c0301a650db95958924bb080192c09fef39389a5',
                'new_real_model_calls': 0, 'new_real_reasoning_episodes': 0,
                'runs': []}
    current_sources = ['experiments_ext/masbench_b1_preflight.py',
                       'experiments_ext/masbench_b1_safety_contract.py',
                       'extensions/masbench_reasoning/execution_safety.py',
                       'tests_ext/test_masbench_b1_safety.py']
    source_mismatch = []
    for rid in ['hpc-masbench-b1-preflight-20261110','hpc-masbench-b1-safety-20261110']:
        base=ROOT/'research/sync/runs'/rid
        m=json.loads((base/'manifest.json').read_bytes())
        status=json.loads((base/'status.json').read_bytes())
        artifacts=json.loads((base/'artifacts.json').read_bytes())
        entries=artifacts['files']
        # Runner artifact paths are relative to the run directory.
        for entry in entries:
            p=base/entry['path']
            if sha(p.read_bytes()) != entry['sha256']:
                mismatches.append(str(p.relative_to(ROOT)))
        snapshot=json.loads((base/'source_snapshot.json').read_bytes())
        if rid.endswith('safety-20261110'):
            rows={e['path']:e for e in snapshot['files']}
            for rel in current_sources:
                if sha((ROOT/rel).read_bytes().replace(b'\r\n',b'\n')) != rows[rel]['remote_sha256']:
                    source_mismatch.append(rel)
        manifest['runs'].append({
            'run_id':rid,'execution_host':m['execution_host'],'git_commit':m['git_commit'],
            'working_tree_status_preserved_in_original_manifest':True,
            'source_sync_id':m['source_sync_id'],'source_manifest_sha256':m['source_manifest_sha256'],
            'command':m['command'],'resource_limits':m['resource_limits'],
            'elapsed_seconds':status['elapsed_seconds'],'exit_code':status['exit_code'],
            'status':status['status'],'resources':status['resource_usage'],
            'outputs':[{'path':str((base/e['path']).relative_to(ROOT)).replace('\\','/'),
                        'sha256':e['sha256'],'size':e.get('size')} for e in entries]})
        evidence.append({'run':rid,'status':status['status'],'artifacts_hashed':len(entries)})
    receipts=[]
    for name in ['20261110T030625Z-0a4021.json','20261110T030748Z-00d31d.json']:
        r=json.loads((ROOT/'research/sync/receipts'/name).read_bytes())
        receipts.append({'name':name,'all_outputs_mirrored':r['all_outputs_mirrored'],
                         'bytes_downloaded':r['bytes_downloaded']})
    result={'scope':'lightweight local file/hash management, no tests/data analysis/model',
            'frozen_sources_checked':len(old['source_sha256']), 'frozen_or_artifact_mismatches':mismatches,
            'current_new_sources_vs_final_HPC_test_snapshot_mismatches':source_mismatch,
            'runs':evidence,'receipts':receipts}
    (LOG/'experiment_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (LOG/'management_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    if mismatches or source_mismatch or not all(r['all_outputs_mirrored'] for r in receipts):
        raise SystemExit(1)


if __name__=='__main__':
    main()
