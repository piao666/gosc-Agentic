"""HPC management preview: copy/compress seven own snapshots, never remove originals."""
from pathlib import Path
import gzip, hashlib, json, os, subprocess, time

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
scratch=Path('/tmp/gosc-snapshot-archive-preview-20261116')
scratch.mkdir(mode=0o700,exist_ok=True)
if scratch.is_symlink() or scratch.stat().st_uid!=os.getuid():raise RuntimeError('scratch identity')
run_ids=['hpc-masbench-context-build-20261116']+[
    'hpc-masbench-context-build-v%d-20261116'%i for i in range(2,6)]+[
    'hpc-masbench-cpp-vendor-prepare-20261116',
    'hpc-masbench-cpp-vendor-prepare-v2-20261116']
report={'scope':'management preview only; originals retained', 'files':[],
        'observed_at_unix':time.time(),'scratch':str(scratch)}
for run_id in run_ids:
    source=root/'research/sync/runs'/run_id/'source_changes.patch'
    if source.is_symlink() or not source.is_file():raise RuntimeError('source identity')
    target=scratch/(run_id+'.patch.gz')
    rawhash=hashlib.sha256()
    if not target.exists():
        with source.open('rb') as src,target.open('xb') as dst:
            with gzip.GzipFile(filename='',mode='wb',compresslevel=1,fileobj=dst,mtime=0) as z:
                while True:
                    b=src.read(1024*1024)
                    if not b:break
                    z.write(b)
    with source.open('rb') as src:
        for b in iter(lambda:src.read(1024*1024),b''):rawhash.update(b)
    restored=hashlib.sha256();n=0
    with gzip.open(target,'rb') as src:
        for b in iter(lambda:src.read(1024*1024),b''):restored.update(b);n+=len(b)
    if restored.digest()!=rawhash.digest() or n!=source.stat().st_size:raise RuntimeError('restore mismatch')
    report['files'].append({'run_id':run_id,'source':str(source),'size':n,
        'sha256':rawhash.hexdigest(),'compressed_copy':str(target),
        'compressed_size':target.stat().st_size,'restore_verified':True})
report['raw_total']=sum(f['size'] for f in report['files'])
report['compressed_total']=sum(f['compressed_size'] for f in report['files'])
report['potential_released_bytes']=report['raw_total']-report['compressed_total']
report['child_pid_50168_exists']=Path('/proc/50168').exists()
report['git_diff_names_sample']=subprocess.check_output(
    ['git','-C',str(root),'diff','--name-status','HEAD'],text=True).splitlines()[:15]
print(json.dumps(report,ensure_ascii=False))
