"""Read-only source transport and isolated Git index management probe."""
from pathlib import Path
import hashlib,json,os,subprocess,urllib.request
root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
report={'range_probes':[],'real_index_unchanged':True}
for name,url in [('vendor','https://api.github.com/repos/ollama/ollama/git/blobs/c74bebeb3c725c898e4e3502e917a017799b0dca?gosc_media=raw'),
                 ('compiler','https://ziglang.org/download/0.17.1/zig-x86_64-linux-0.17.1.tar.xz')]:
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'GOSC-fixed-source-audit','Accept':'application/vnd.github.raw+json','Range':'bytes=65536-81919'})
        with op.open(req,timeout=10) as r:
            b=r.read(16384)
            report['range_probes'].append({'name':name,'status':r.status,'headers':dict(r.headers),'sample_size':len(b)})
    except Exception as e:report['range_probes'].append({'name':name,'error':repr(e)})
index=Path('/tmp/gosc-snapshot-index-916289b-20261116')
real=root/'.git/index'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(real)
env=dict(os.environ,GIT_INDEX_FILE=str(index))
if not index.exists():subprocess.run(['git','-C',str(root),'read-tree','HEAD'],env=env,check=True)
report['isolated_index']=str(index)
report['isolated_diff_stat']=subprocess.check_output(['git','-C',str(root),'diff','--shortstat','HEAD'],env=env,text=True).strip()
report['real_index_sha256']=before
report['real_index_unchanged']=before==sha(real)
print(json.dumps(report))
