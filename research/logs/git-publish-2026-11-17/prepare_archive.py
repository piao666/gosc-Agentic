"""Local file/hash archival management only; no project tests or data analysis."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[3];LOG=Path(__file__).resolve().parent
ART=ROOT/'research/artifacts/context-deployment-20261117';ART.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
runs=sorted(p for p in (ROOT/'research/sync/runs').iterdir() if p.name.startswith((
    'hpc-masbench-context-build','hpc-masbench-context-offline-contract',
    'hpc-masbench-cpp-vendor-prepare','hpc-masbench-cpp17-helper-build',
    'hpc-masbench-real-deployment')))
selected={'build.json','preparation.json','contract.json','client-boundaries.json','acceptance.json',
          'loaded-model.json','normal-response.json','synthetic-effective-inputs.json','synthetic-counts.json'}
provenance=[];run_index=[];omitted=[]
for d in runs:
    state=json.loads((d/'status.json').read_bytes());manifest=json.loads((d/'manifest.json').read_bytes())
    artifacts=json.loads((d/'artifacts.json').read_bytes())['files']
    outputs=[]
    for entry in artifacts:
        p=d/entry['path']
        if p.name not in selected:continue
        assert p.stat().st_size==entry['size'] and sha(p)==entry['sha256']
        dst=ART/(d.name+'__'+p.name)
        if dst.exists():assert sha(dst)==sha(p)
        else:shutil.copyfile(p,dst)
        item={'archive_path':dst.relative_to(ROOT).as_posix(),'source_path':p.relative_to(ROOT).as_posix(),
              'run_id':d.name,'bytes':p.stat().st_size,'sha256':sha(p),'policy':'byte_identical_no_recomputation'}
        provenance.append(item);outputs.append(item['archive_path'])
    run_index.append({'run_id':d.name,'status':state,'command':manifest['command'],
        'git_commit':manifest['git_commit'],'source_sync_id':manifest.get('source_sync_id'),
        'manifest_sha256':sha(d/'manifest.json'),'archived_outputs':outputs})
    for name in ['source_changes.patch','source_changes.patch.gz','source_untracked.tar.gz']:
        p=d/name
        if p.exists():omitted.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
write(ART/'provenance.json',{'files':provenance,'scope':'explicit small immutable engineering outputs, synthetic inputs only'})
write(ART/'run_index.json',{'scope':'15 registered runs since base916289b; unknown finish/exit retained', 'runs':run_index})
receipts=[]
for p in sorted((ROOT/'research/sync/receipts').glob('2026111[67]T*.json')):
    r=json.loads(p.read_bytes())
    receipts.append({'source_path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),
        'sync_id':r['sync_id'],'all_outputs_mirrored':r['all_outputs_mirrored'],
        'bytes_downloaded':r['bytes_downloaded'],'total_inventory_files':len(r['files']),
        'selected_run_files':[x for x in r['files'] if any(x['path'].startswith('research/sync/runs/'+d.name+'/') for d in runs)],
        'original_retained_local_HPC':True})
write(ART/'receipt_index.json',{'scope':'full receipt originals retained; compact SHA-bound relevant entries', 'receipts':receipts})
write(LOG/'omitted_snapshot_inventory.json',{'files':omitted,'policy':'retained local/HPC; not published; compressed copies are separately identified'})
print(json.dumps({'runs':len(runs),'outputs':len(provenance),'output_bytes':sum(x['bytes'] for x in provenance),
                  'receipts':len(receipts),'receipt_original_bytes':sum(x['bytes'] for x in receipts)}))
for r in run_index:print(r['run_id'],r['status']['status'],r['status'].get('elapsed_seconds'),r['status'].get('exit_code'))
