"""Lightweight local file/hash archival management; no scientific computation."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[3]
LOG=Path(__file__).resolve().parent
ART=ROOT/'research/artifacts/masbench-b1-20261116'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    chosen=[
        ('hpc-masbench-b1-preflight-20261110','preflight.json','deployment_data_preflight.json'),
        ('hpc-masbench-b1-safety-20261110','safety_contract.json','safety_17_contract.json'),
        ('hpc-masbench-b1-integration-20261110','integration_contract.json','integration_20_contract.json'),
        ('hpc-masbench-b1-integration-v2-20261110','integration_contract.json','integration_22_contract.json'),
        ('hpc-masbench-b1-integration-v3-20261110','integration_contract.json','integration_23_contract.json'),
        ('hpc-masbench-b1-integration-v4-20261110','integration_contract.json','integration_24_contract.json')]
    provenance=[];omitted=[]
    for rid,filename,target_name in chosen:
        directory=ROOT/'research/sync/runs'/rid
        src=directory/'outputs'/filename
        entry=next(x for x in json.loads((directory/'artifacts.json').read_bytes())['files'] if x['path']=='outputs/'+filename)
        assert src.stat().st_size==entry['size'] and sha(src)==entry['sha256']
        dst=ART/target_name;dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists():assert sha(dst)==entry['sha256']
        else:shutil.copyfile(src,dst)
        provenance.append({'archive_path':dst.relative_to(ROOT).as_posix(),
                           'source_path':src.relative_to(ROOT).as_posix(),
                           'run_id':rid,'bytes':entry['size'],'sha256':entry['sha256'],
                           'policy':'byte_identical_no_recomputation'})
        for name in ['source_changes.patch','source_untracked.tar.gz']:
            p=directory/name
            if p.exists():omitted.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,
                                         'sha256':sha(p),'disposition':'retained_local_and_HPC_not_newly_published'})
    (ART/'provenance.json').write_text(json.dumps({'date':'2026-11-16 Asia/Shanghai',
        'scope':'six explicit immutable small outputs; no task dataset, model or new result computation',
        'files':provenance},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (LOG/'omitted_snapshot_inventory.json').write_text(json.dumps({'files':omitted,
        'bytes':sum(x['bytes'] for x in omitted),'older_tracked_history_preserved':True},indent=2)+'\n',encoding='utf-8')
    receipts=[]
    for src in sorted((ROOT/'research/sync/receipts').glob('20261110T*.json')):
        r=json.loads(src.read_bytes())
        relevant=[x for x in r['files'] if any(x['path'].startswith('research/sync/runs/'+rid+'/') for rid,_,_ in chosen)]
        receipts.append({'source_path':src.relative_to(ROOT).as_posix(),'bytes':src.stat().st_size,
                         'sha256':sha(src),'sync_id':r['sync_id'],'all_outputs_mirrored':r['all_outputs_mirrored'],
                         'bytes_downloaded':r['bytes_downloaded'],'total_inventory_files':len(r['files']),
                         'new_B1_files':relevant,
                         'upload_status':'failed_quota_then_recovered_by_034520Z-f62d10' if src.stem=='20261110T034339Z-eaef8e' else 'completed',
                         'original_retained_local_HPC':True})
    (ART/'receipt_index.json').write_text(json.dumps({'scope':'compact index; full transfer inventory originals not newly published',
        'receipts':receipts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'whitelist_files':len(provenance),'whitelist_bytes':sum(x['bytes'] for x in provenance),
                      'omitted_source_snapshot_files':len(omitted),'omitted_source_snapshot_bytes':sum(x['bytes'] for x in omitted),
                      'full_receipts_retained_not_published':len(receipts),'receipt_bytes':sum(x['bytes'] for x in receipts)}))


if __name__=='__main__':main()
