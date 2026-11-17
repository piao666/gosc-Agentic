"""Read-only public metadata reachability, not module installation or build."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import remote_script
src=r'''
import json,urllib.request,time
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
urls=[
 'https://proxy.golang.org/github.com/ollama/ollama/@v/v0.11.11.info',
 'https://goproxy.cn/github.com/ollama/ollama/@v/v0.11.11.info',
 'https://goproxy.cn/sumdb/sum.golang.org/lookup/github.com/ollama/ollama@v0.11.11',
 'https://sum.golang.org/lookup/github.com/ollama/ollama@v0.11.11']
rows=[]
for url in urls:
 t=time.monotonic()
 try:
  with op.open(url,timeout=5) as r: raw=r.read(65537);status=r.status
  if len(raw)>65536:raise ValueError('metadata cap')
  rows.append({'url':url,'status':status,'body':raw.decode(),'elapsed':time.monotonic()-t})
 except Exception as e:
  rows.append({'url':url,'error':type(e).__name__,'detail':str(e)[:400],'elapsed':time.monotonic()-t})
print(json.dumps({'scope':'public metadata only; no source execution','rows':rows},ensure_ascii=False,indent=2))
'''
p=remote_script(src)
(HERE/'module_transport_probe.json').write_bytes(p.stdout)
(HERE/'module_transport_probe_stderr.txt').write_bytes(p.stderr)
print(p.stdout.decode(errors='replace'))
raise SystemExit(p.returncode)
