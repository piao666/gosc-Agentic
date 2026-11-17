"""Management-only two-connection probes of four official-listed mirrors."""
from concurrent.futures import ThreadPoolExecutor
import json,time,urllib.request
def probe(base):
    start=time.monotonic();url=base+'/zig-x86_64-linux-0.17.1.tar.xz'
    try:
        op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with op.open(urllib.request.Request(url,headers={'Range':'bytes=0-262143','User-Agent':'GOSC-archive-inspection'}),timeout=5) as r:
            b=r.read(262144)
            return {'url':url,'status':r.status,'bytes':len(b),'seconds':time.monotonic()-start,
                    'content_range':r.headers.get('Content-Range')}
    except Exception as e:return {'url':url,'error':repr(e),'seconds':time.monotonic()-start}
with ThreadPoolExecutor(max_workers=2) as pool:
    rows=list(pool.map(probe,['https://zigmirror.com','https://zig.squirl.dev','https://zig.tilok.dev','https://pkg.earth/zig']))
print(json.dumps({'official_list':'https://ziglang.org/download/community-mirrors.txt','probes':rows}))
