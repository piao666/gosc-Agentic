"""Local Git/file archival management only: immutable small evidence copies."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[3]
LOG=Path(__file__).resolve().parent
ART=ROOT/"research/artifacts/native-masbench-20261104"


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    files=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT).split(b'\0')
    runs=sorted({p.decode().split('/')[3] for p in files if p.startswith(b'research/sync/runs/')})
    attrs=ROOT/'.gitattributes';text=attrs.read_text()
    additions=['# Preserve only new Oct30/Nov02/Nov03 archive evidence; older tracked bytes unchanged.']
    additions += ['/research/sync/runs/'+name+'/** -text' for name in runs]
    additions += ['/research/sync/receipts/20261030T*.json -text',
                  '/research/sync/receipts/20261102T*.json -text',
                  '/research/sync/receipts/20261103T*.json -text',
                  '/research/artifacts/native-masbench-20261104/** -text']
    if additions[0] not in text:
        attrs.write_text(text.rstrip()+'\n'+'\n'.join(additions)+'\n',encoding='utf-8',newline='\n')
    selected=[
      ('hpc-native-information-freeze-20261030','frozen.json','native_frozen.json'),
      ('hpc-native-information-shadow-20261030','summary.json','native_shadow_summary.json'),
      ('hpc-native-information-shadow-20261030','audit.json','native_shadow_audit.json'),
      ('hpc-native-information-shadow-report-20261030','report.json','native_shadow_report.json'),
      ('hpc-native-information-regression-v2-20261030','pytest.xml','native_contract_pytest.xml'),
      ('hpc-masbench-data-audit-v2-20261103','data_audit.json','masbench_data_audit.json'),
      ('hpc-masbench-data-followup-20261103','data_followup.json','masbench_data_followup.json'),
      ('hpc-masbench-registry-v2-20261103','development_registry_v1.json','masbench_development_registry.json'),
      ('hpc-masbench-registry-v2-20261103','preparation_summary.json','masbench_registry_summary.json'),
      ('hpc-masbench-client-contract-v3-20261103','client_contract_acceptance.json','masbench_client_contract.json'),
      ('hpc-masbench-client-contract-v3-20261103','contracts.xml','masbench_client_pytest.xml'),
      ('hpc-masbench-httpx-mock-v2-20261103','httpx_mock_contract.json','masbench_httpx_mock.json'),
      ('hpc-masbench-context-budget-20261103','context_budget_preflight.json','masbench_context_budget.json'),
      ('hpc-masbench-environment-metadata-20261102','environment_ready.json','masbench_environment_metadata.json'),
      ('hpc-masbench-model-restore-after-storage-retry1-20261102','models_ready.json','masbench_models_ready.json'),
      ('hpc-masbench-model-license-audit-20261102','license_layer_index.json','model_licenses/license_layer_index.json')]
    licenses=ROOT/'research/sync/runs/hpc-masbench-model-license-audit-20261102/outputs'
    for item in json.loads((licenses/'license_layer_index.json').read_text())['license_layers']:
        selected.append(('hpc-masbench-model-license-audit-20261102',item['path'],'model_licenses/'+item['path']))
    provenance=[]
    for run,name,dest in selected:
        directory=ROOT/'research/sync/runs'/run
        source=directory/'outputs'/name
        entry=next(a for a in json.loads((directory/'artifacts.json').read_text())['files'] if a['path']=='outputs/'+name)
        assert source.stat().st_size==entry['size'] and sha(source)==entry['sha256']
        target=ART/dest;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert sha(target)==entry['sha256']
        else:shutil.copyfile(source,target)
        provenance.append({'archive_path':target.relative_to(ROOT).as_posix(),
                           'source_path':source.relative_to(ROOT).as_posix(),
                           'run_id':run,'bytes':entry['size'],'sha256':entry['sha256'],
                           'copy_policy':'byte_identical_no_recomputation'})
    (ART/'provenance.json').write_text(json.dumps({'date':'2026-11-04','scope':'small immutable artifact whitelist, not complete raw dataset/trace/model release',
        'files':provenance},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    omitted=[]
    for directory in [ROOT/'research/sync/runs'/name for name in runs]:
        for filename in ['source_changes.patch','source_untracked.tar.gz']:
            p=directory/filename
            if p.is_file():omitted.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'disposition':'retained_local_HPC_not_in_new_Git_archive'})
    (LOG/'omitted_snapshot_inventory.json').write_text(json.dumps({'files':omitted,'total_bytes':sum(x['bytes'] for x in omitted),
        'existing_tracked_snapshots_not_removed':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'whitelist_files':len(provenance),'whitelist_bytes':sum(x['bytes'] for x in provenance),
                      'new_run_dirs':len(runs),'retained_omitted_snapshots':len(omitted),
                      'omitted_bytes':sum(x['bytes'] for x in omitted)}))


if __name__=='__main__':main()
