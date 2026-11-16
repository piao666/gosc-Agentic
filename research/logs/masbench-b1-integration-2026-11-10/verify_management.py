"""Local file/hash/receipt management only; never runs project tests or models."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
LOG=Path(__file__).resolve().parent


def sha(p,normalized=False):
    data=p.read_bytes()
    return hashlib.sha256(data.replace(b'\r\n',b'\n') if normalized else data).hexdigest()


def main():
    frozen=json.loads((ROOT/'research/artifacts/native-masbench-20261104/native_frozen.json').read_bytes())
    mismatches=[p for p,h in frozen['source_sha256'].items() if sha(ROOT/p,True)!=h]
    ids=['hpc-masbench-b1-integration'+s+'-20261110' for s in ['', '-v2','-v3','-v4']]
    records=[]
    for rid in ids:
        p=ROOT/'research/sync/runs'/rid
        m=json.loads((p/'manifest.json').read_bytes());s=json.loads((p/'status.json').read_bytes())
        entries=json.loads((p/'artifacts.json').read_bytes())['files']
        for e in entries:
            if sha(p/e['path'])!=e['sha256']:mismatches.append(rid+'/'+e['path'])
        result=json.loads((p/'outputs/integration_contract.json').read_bytes())
        records.append({'run_id':rid,'host':m['execution_host'],'head':m['git_commit'],
                        'source_sync_id':m['source_sync_id'],'source_manifest_sha256':m['source_manifest_sha256'],
                        'command':m['command'],'resources':m['resource_limits'],
                        'status':s['status'],'exit_code':s['exit_code'],'elapsed_seconds':s['elapsed_seconds'],
                        'resource_usage':s['resource_usage'],'result':result,'artifacts':entries})
    snapshot=json.loads((ROOT/'research/sync/runs'/ids[-1]/'source_snapshot.json').read_bytes())
    rows={e['path']:e for e in snapshot['files']}
    protected=['extensions/masbench_reasoning/'+n+'.py' for n in ['client','application','wire','registry','execution_safety']]
    protected += ['research/benchmarks/masbench_context_tokenizer_preflight_review.md',
                  'research/benchmarks/masbench_data_split_and_power_feasibility_review.md',
                  'research/protocols/masbench_b1_execution_safety_spec_v1.md',
                  'research/reports/masbench_b1_preflight_acceptance.md']
    new_sources=['extensions/masbench_reasoning/fixture_driver.py',
                 'experiments_ext/masbench_b1_integration_contract.py','tests_ext/test_masbench_fixture_driver.py']
    for rel in protected+new_sources:
        if sha(ROOT/rel,True)!=rows[rel]['remote_sha256']:mismatches.append(rel)
    registry=ROOT/'research/sync/runs/hpc-masbench-registry-v2-20261103/outputs/development_registry_v1.json'
    if sha(registry)!='6d14229ae0dd85a5b3c88b9309fcf86e54fab2523a3701914a7f7ebc06500a86':
        mismatches.append('registry')
    receipt_names=['20261110T033305Z-7b64a5','20261110T033649Z-485991',
                   '20261110T034016Z-ef567d','20261110T034339Z-eaef8e','20261110T034520Z-f62d10']
    receipts=[]
    for n in receipt_names:
        r=json.loads((ROOT/'research/sync/receipts'/(n+'.json')).read_bytes())
        receipts.append({'id':n,'all_outputs_mirrored':r['all_outputs_mirrored'],
                         'bytes_downloaded':r['bytes_downloaded'],
                         'HPC_receipt_upload':'failed_quota' if n.endswith('eaef8e') else 'completed'})
    changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode().splitlines()
    result={'scope':'lightweight local file/hash management only','frozen_source_count':len(frozen['source_sha256']),
            'protected_previous_files':protected,'new_sources_vs_final_test_snapshot':new_sources,
            'mismatches':mismatches,'tracked_paths_changed':changed,
            'receipts':receipts,'final_full_suite_tests':records[-1]['result']['tests_run'],
            'final_result_execution_completed':records[-1]['status']=='completed',
            'final_launch_management_quota_failure_preserved':True}
    (LOG/'experiment_manifest.json').write_text(json.dumps({'archive_head':records[-1]['head'],
        'scientific_baseline':'014b85dfc472c45d8ea5f15e83e0c1ed8e938daf',
        'third_party':'c0301a650db95958924bb080192c09fef39389a5','runs':records,
        'real_generations':0,'real_reasoning_episodes':0,'installations':0,'service_changes':0,
        'git_commit_or_push':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (LOG/'management_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'mismatches':mismatches,'frozen_source_count':len(frozen['source_sha256']),
                      'final_tests':records[-1]['result']['tests_run'],'latest_mirror':receipts[-1]},ensure_ascii=False))
    if mismatches or not receipts[-1]['all_outputs_mirrored']:raise SystemExit(1)


if __name__=='__main__':main()
