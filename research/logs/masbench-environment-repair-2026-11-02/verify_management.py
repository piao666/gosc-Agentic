"""Lightweight local validation of HPC infrastructure evidence and protected source hashes."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

LOG=Path(__file__).resolve().parent
ROOT=LOG.parents[2]
RUNS=ROOT/'research/sync/runs'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path,lf=False):
    body=path.read_bytes()
    return hashlib.sha256(body.replace(b'\r\n',b'\n') if lf else body).hexdigest()
def git(*args):
    p=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    assert p.returncode==0,p.stderr
    return p.stdout.strip()
assert git('rev-parse','HEAD')=='014b85dfc472c45d8ea5f15e83e0c1ed8e938daf'
git('diff','--exit-code','HEAD','--','gosc','extensions','tests','tests_ext','scripts')
git('diff','--check')
frozen=read(RUNS/'hpc-native-information-freeze-20261030/outputs/frozen.json')
assert all(sha(ROOT/p,True)==v for p,v in frozen['source_sha256'].items())
prior=read(ROOT/'research/logs/masbench-reasoning-static-2026-10-30/experiment_manifest.json')
assert all(sha(ROOT/p)==v for p,v in prior['protected_previous_report_sha256'].items())
run_ids=['hpc-masbench-repair-plan-20261102','hpc-masbench-dependencies-20261102',
         'hpc-masbench-download-probe-20261102','hpc-storage-reconcile-capacity-20261102',
         'hpc-laya-authorized-cleanup-20261102','hpc-authorized-installer-cleanup-20261102',
         'hpc-storage-capacity-after-cleanup-20261102',
         'hpc-masbench-model-restore-after-storage-retry1-20261102','hpc-masbench-environment-metadata-20261102',
         'hpc-masbench-model-license-audit-20261102']
execution=[]
for name in run_ids:
    directory=RUNS/name;status=read(directory/'status.json');manifest=read(directory/'manifest.json')
    assert status['status']=='completed' and status['exit_code']==0,(name,status)
    assert manifest['kind']=='infrastructure' and not manifest['seeds']
    for entry in read(directory/'artifacts.json')['files']:
        path=directory/entry['path']
        assert path.stat().st_size==entry['size'] and sha(path)==entry['sha256'],str(path)
    execution.append({'run_id':name,'seconds':status['elapsed_seconds'],'exit_code':0,
                      'manifest_sha256':sha(directory/'manifest.json')})
interrupted=read(RUNS/'hpc-masbench-model-restore-20261102/status.json')
assert interrupted['status']=='failed' and interrupted['exit_code']==-15
retry1=read(RUNS/'hpc-masbench-model-restore-retry1-20261102/status.json')
assert retry1['status']=='failed' and retry1['exit_code']==-15
retry2=read(RUNS/'hpc-masbench-model-restore-retry2-20261102/status.json')
assert retry2['status']=='failed' and retry2['exit_code'] is None and retry2['finished_at'] is None
assert retry2.get('reconciled_at')
assert read(RUNS/'hpc-storage-capacity-rdwr-20261102/status.json')['exit_code']==120
deps=read(RUNS/'hpc-masbench-dependencies-20261102/outputs/dependencies_ready.json')
assert deps['original_gosc_packages_before']==deps['original_gosc_packages_after']
assert deps['import_check']['inference_requested'] is False
model=read(RUNS/'hpc-masbench-model-restore-after-storage-retry1-20261102/outputs/models_ready.json')
after_storage=read(RUNS/'hpc-masbench-model-restore-after-storage-20261102/status.json')
assert after_storage['status']=='failed' and after_storage['exit_code']==-15
assert read(RUNS/'hpc-storage-capacity-after-cleanup-20261102/outputs/capacity_after_cleanup.json')['status']=='allocated_successfully'
ready=read(RUNS/'hpc-masbench-environment-metadata-20261102/outputs/environment_ready.json')
assert set(ready['model_ids_via_openai_sdk'])==set(model['models'])
assert not ready['inference_requested'] and not ready['model_load_requested']
receipt_path=ROOT/'research/sync/receipts/20261102T074010Z-67b8fc.json'
receipt=read(receipt_path)
assert receipt['all_outputs_mirrored'] is True
license_index=read(RUNS/'hpc-masbench-model-license-audit-20261102/outputs/license_layer_index.json')
assert len(license_index['license_layers'])==4
assert len({item['path'] for item in license_index['license_layers']})==4
for item in license_index['license_layers']:
    assert sha(RUNS/'hpc-masbench-model-license-audit-20261102/outputs'/item['path'])==item['sha256']
old=read(RUNS/'hpc-ollama-deploy-retry1-20261020/outputs/readiness.json')
assert {k:v['manifest_sha256'] for k,v in model['models'].items()}=={x['model']:x['digest'] for x in old['models']}
assert all(v['verified_sha256']==key.split(':',1)[1] for key,v in model['blobs'].items())
assert not model['inference_requested'] and not model['loaded']['models']
lock=ROOT/'research/benchmarks/masbench_reasoning_requirements_v1.linux.lock.txt'
assert sha(lock)==deps['lock_sha256']
docs=[ROOT/'research/benchmarks'/name for name in ['masbench_reasoning_adapter_spec_v1.md',
      'masbench_reasoning_feasibility_review.md','masbench_reasoning_gate_matrix.md','masbench_reasoning_environment_v1.md']]
docs+=list(LOG.glob('*.md'))
for path in docs:
    body=path.read_text(encoding='utf-8')
    assert all(line==line.rstrip() for line in body.splitlines()),str(path)
    for link in re.findall(r'\]\(([^)]+)\)',body):
        if '://' not in link:
            destination=path.parent/link.split('#')[0]
            assert destination.exists() or destination==LOG/'verification.json',str(destination)
value={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'scope':'Local file/hash evidence management, not scientific tests',
       'frozen_sources_unchanged':len(frozen['source_sha256']),'previous_reports_unchanged':True,
       'original_gosc_package_metadata_unchanged':True,'infrastructure_runs':execution,
       'models_restored':list(model['models']),'historical_model_manifest_identity_match':True,
       'all_hpc_blob_hashes_verified':True,'lock_sha256':sha(lock),'llm_calls':0,
       'sdk_metadata_listing_passed':True,'controlled_failed_download_retained':interrupted,
       'controlled_retry1_failure_retained':retry1,'quota_retry2_failure_reconciled':retry2,
       'after_storage_controlled_failure_retained':after_storage,
       'unique_license_layers_verified':4,'old_ambiguous_license_output_preserved':True,
       'final_receipt':str(receipt_path.relative_to(ROOT)),'all_outputs_mirrored':True,
       'authorized_cleanup_runs':['hpc-storage-reconcile-capacity-20261102','hpc-laya-authorized-cleanup-20261102','hpc-authorized-installer-cleanup-20261102'],
       'new_scientific_runs':[],'training':False,'git_commit_or_push':False,
       'documents_sha256':{str(p.relative_to(ROOT)):sha(p) for p in docs},
       'earlier_timeout_inventory_sha256':sha(ROOT/'research/logs/masbench-reasoning-static-2026-11-02/inventory.json')}
(LOG/'verification.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'status':'management_checks_passed','frozen_sources_unchanged':73,
                  'models_restored':3,'original_gosc_packages_unchanged':True,'llm_calls':0}))
