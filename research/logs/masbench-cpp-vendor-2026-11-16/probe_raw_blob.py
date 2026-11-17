import json,urllib.request
url='https://api.github.com/repos/ollama/ollama/git/blobs/9429171390a41654a73b1fd63d6048712a4893a2?gosc_media=raw'
req=urllib.request.Request(url,headers={'User-Agent':'GOSC-fixed-source-audit','Accept':'application/vnd.github.raw+json'})
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
 with op.open(req,timeout=8) as r:
  b=r.read(7000)
  result={'status':r.status,'content_type':r.headers.get('Content-Type'),'content_length':r.headers.get('Content-Length'),
          'read_bytes':len(b),'raw_header_prefix':b[:120].decode(errors='replace')}
except Exception as e:result={'error':type(e).__name__,'detail':str(e)[:300]}
print(json.dumps(result))
