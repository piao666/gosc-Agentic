"""HPC source-management download/hash only. Never execute downloaded source."""
from pathlib import Path
import hashlib
import json
import os
import urllib.request

assert os.getuid()==8301880
root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
lock=SOURCE_LOCK
dest=Path('/tmp/gosc-masbench-vendor-20261116')
assert dest.resolve()==dest and not dest.is_symlink()
dest.mkdir(mode=0o700,exist_ok=True)
assert dest.stat().st_uid==os.getuid()
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
rows=[]
for f in lock['files']:
    p=dest/f['path']
    p.parent.mkdir(mode=0o700,exist_ok=True)
    try:
        if p.exists():
            if p.is_symlink():raise ValueError('symlink')
            raw=p.read_bytes()
        else:
            with op.open(f['url'],timeout=8) as response:raw=response.read(f['size']+1)
            if len(raw)!=f['size']:raise ValueError('source byte count')
            with p.open('xb') as out:out.write(raw)
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if len(raw)!=f['size'] or blob!=f['git_blob_sha1']:raise ValueError('Git blob mismatch')
        rows.append({'path':f['path'],'size':len(raw),'git_blob_sha1':blob,
                     'sha256':hashlib.sha256(raw).hexdigest(),'verified':True,
                     'license_header_excerpt':raw[:1200].decode(errors='replace')})
    except Exception as e:
        rows.append({'path':f['path'],'verified':False,'error':type(e).__name__,'detail':str(e)[:350]})
trees=[]
for sub in lock['subtrees']:
    fs=[x for x in rows if x['path'].startswith(sub['name']+'/')]
    if not fs or not all(x['verified'] for x in fs):continue
    payload=b''
    for f in sorted(fs,key=lambda x:x['path'].split('/',1)[1]):
        name=f['path'].split('/',1)[1]
        payload+=b'100644 '+name.encode()+b'\0'+bytes.fromhex(f['git_blob_sha1'])
    actual=hashlib.sha1(b'tree '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
    trees.append({'name':sub['name'],'actual':actual,'expected':sub['git_tree_sha'],'verified':actual==sub['git_tree_sha']})
print(json.dumps({'scope':'fixed source management; no third-party execution',
 'source_commit':lock['source_commit'],'root':str(dest),'files':rows,'trees':trees,
 'complete':len(rows)==len(lock['files']) and all(x['verified'] for x in rows) and len(trees)==3 and all(x['verified'] for x in trees),
 'code_executed':False,'model_calls':0},ensure_ascii=False,indent=2))
