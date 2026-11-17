"""Bounded transport probe of mirrors listed by official Zig website; no code execution."""
import json,time,urllib.request
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
rows=[]
for base in ['https://fs.liujiacai.net/zigbuilds','https://ziglang.freetls.fastly.net','https://pkg.hexops.org/zig']:
    url=base+'/zig-x86_64-linux-0.17.1.tar.xz'
    start=time.monotonic()
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'GOSC-archive-inspection','Range':'bytes=0-65535'})
        with op.open(req,timeout=6) as r:
            b=r.read(65536)
            rows.append({'url':url,'status':r.status,'content_range':r.headers.get('Content-Range'),
                         'sample_bytes':len(b),'seconds':time.monotonic()-start})
    except Exception as e:rows.append({'url':url,'error':repr(e),'seconds':time.monotonic()-start})
print(json.dumps({'official_list':'https://ziglang.org/download/community-mirrors.txt','probes':rows}))
