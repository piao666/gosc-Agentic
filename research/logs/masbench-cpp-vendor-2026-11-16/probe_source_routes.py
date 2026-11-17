"""Read-only small public-source route probe; no installations/execution."""
import base64,json,urllib.request
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
urls=[
 'https://api.github.com/repos/ollama/ollama/git/blobs/9429171390a41654a73b1fd63d6048712a4893a2',
 'https://ziglang.org/download/0.17.1/zig-x86_64-linux-0.17.1.tar.xz']
rows=[]
for url in urls:
 try:
  req=urllib.request.Request(url,method='HEAD' if 'ziglang.org' in url else 'GET',headers={'User-Agent':'GOSC-source-audit'})
  with op.open(req,timeout=5) as response:
   raw=response.read(20000) if req.method=='GET' else b''
   row={'url':url,'status':response.status,'content_length':response.headers.get('Content-Length')}
   if raw:
    value=json.loads(raw);row['git_blob_sha1']=value.get('sha');row['size']=value.get('size');row['encoding']=value.get('encoding')
   rows.append(row)
 except Exception as e:rows.append({'url':url,'error':type(e).__name__,'detail':str(e)[:300]})
print(json.dumps(rows,indent=2))
