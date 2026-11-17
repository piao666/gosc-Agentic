"""HPC artifact inspection only: download/hash/list; never run a new compiler."""
from pathlib import Path
import base64
import hashlib
import json
import http.client
import os
import signal
import tarfile
import time
import urllib.request
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc,write_json

ZIG_URL='https://ziglang.org/download/0.17.1/zig-x86_64-linux-0.17.1.tar.xz'
ZIG_SIZE=57411036
ZIG_SHA='3581863e3cbcfd0fce0efc682ce7e9e93da96668a977791d356a26d2a7e9b17a'
LIMIT=80*1024*1024
downloaded=0
download_lock=threading.Lock()
START=time.monotonic()
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))

def account_download(count):
    global downloaded
    with download_lock:
        downloaded+=count
        if downloaded>LIMIT:raise RuntimeError('preparation download cap')

def range_archive(partial,url):
    if partial.is_symlink():raise RuntimeError('partial symlink')
    def segment(bounds):
        start,end=bounds
        req=urllib.request.Request(url,headers={
            'User-Agent':'GOSC-archive-inspection','Range':f'bytes={start}-{end}'})
        chunks=[];count=0
        local=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with local.open(req,timeout=12) as response:
            if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{ZIG_SIZE}':
                raise RuntimeError('range response mismatch')
            while count<=end-start:
                if time.monotonic()-START>560:raise RuntimeError('range deadline')
                b=response.read(min(65536,end-start+1-count))
                if not b:raise RuntimeError('short range')
                account_download(len(b));chunks.append(b);count+=len(b)
        return b''.join(chunks)
    with ThreadPoolExecutor(max_workers=2) as pool:
        while not partial.exists() or partial.stat().st_size<ZIG_SIZE:
            offset=partial.stat().st_size if partial.exists() else 0
            bounds=[(s,min(s+512*1024-1,ZIG_SIZE-1))
                    for s in range(offset,min(offset+1024*1024,ZIG_SIZE),512*1024)]
            pieces=list(pool.map(segment,bounds))
            with partial.open('ab') as f:
                for b in pieces:f.write(b)
    if partial.stat().st_size!=ZIG_SIZE:raise RuntimeError('range size')

def get(url,stream,maximum,raw_blob=False):
    global downloaded
    headers={'User-Agent':'GOSC-fixed-source-audit'}
    if raw_blob:headers['Accept']='application/vnd.github.raw+json'
    req=urllib.request.Request(url,headers=headers)
    count=0
    with op.open(req,timeout=12) as response:
        while True:
            chunk=response.read(min(65536,maximum-count+1))
            if not chunk:break
            count+=len(chunk);downloaded+=len(chunk)
            if count>maximum or downloaded>LIMIT:raise RuntimeError('preparation download cap')
            stream.write(chunk)
    return count

def file_sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    require_hpc();signal.alarm(570)
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    space=Path('/tmp/gosc-cpp-vendor-artifacts-20261116')
    if space.resolve()!=space or space.is_symlink():raise RuntimeError('scratch identity')
    space.mkdir(mode=0o700,exist_ok=True)
    if space.stat().st_uid!=os.getuid():raise RuntimeError('scratch owner')
    lock=json.loads((ROOT/'research/protocols/masbench_vendor_source_lock_2026-11-16.json').read_text())
    report={'scope':'archive/source inspection only, no compiler executed or installed',
            'scratch':str(space),'model_calls':0,'third_party_code_executed':False,
            'source_commit':lock['source_commit'],'files':[]}
    try:
        import io
        for entry in lock['files']:
            target=space/'vendor'/entry['path']
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                if target.is_symlink():raise RuntimeError('source symlink')
                raw=target.read_bytes()
            else:
                buf=io.BytesIO()
                get('https://api.github.com/repos/ollama/ollama/git/blobs/'+entry['git_blob_sha1']+'?gosc_media=raw',
                    buf,entry['size'],raw_blob=True)
                raw=buf.getvalue()
                with target.open('xb') as f:f.write(raw)
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if blob!=entry['git_blob_sha1'] or len(raw)!=entry['size']:raise RuntimeError('source identity')
            report['files'].append({'path':entry['path'],'size':len(raw),
                'git_blob_sha1':blob,'sha256':hashlib.sha256(raw).hexdigest()})
            # License text is part of each fixed public header. Preserve small
            # attribution-bearing excerpts, not a substitute for bundled text.
            text=raw.decode(errors='replace')
            lines=text.splitlines()
            anchors=[i for i,line in enumerate(lines) if any(k in line.lower() for k in
                     ['permission is hereby granted','license -','licensing','license:'])]
            excerpts=['\n'.join(lines[:32]),'\n'.join(lines[-90:])]
            for i in anchors[:4]:excerpts.append('\n'.join(lines[max(0,i-3):i+25]))
            (out/(entry['path'].replace('/','__')+'.license.txt')).write_text('\n\n'.join(excerpts),encoding='utf-8')
        trees=[]
        for subtree in lock['subtrees']:
            payload=b''
            files=[x for x in report['files'] if x['path'].startswith(subtree['name']+'/')]
            for f in sorted(files,key=lambda x:x['path'].split('/',1)[1]):
                payload+=b'100644 '+f['path'].split('/',1)[1].encode()+b'\0'+bytes.fromhex(f['git_blob_sha1'])
            tree=hashlib.sha1(b'tree '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
            if tree!=subtree['git_tree_sha']:raise RuntimeError('vendor tree identity')
            trees.append({'name':subtree['name'],'sha1':tree,'verified':True})
        report['vendor_trees']=trees
        archive=space/'zig-x86_64-linux-0.17.1.tar.xz'
        transport=os.environ.get('GOSC_CPP_ARCHIVE_TRANSPORT_URL',ZIG_URL)
        allowed=[ZIG_URL,'https://pkg.hexops.org/zig/zig-x86_64-linux-0.17.1.tar.xz',
                 'https://fs.liujiacai.net/zigbuilds/zig-x86_64-linux-0.17.1.tar.xz',
                 'https://zigmirror.com/zig-x86_64-linux-0.17.1.tar.xz']
        if transport not in allowed:raise RuntimeError('unlisted archive transport')
        report['compiler_archive_transport']=transport
        report['compiler_primary_metadata']='https://ziglang.org/download/index.json'
        report['mirror_list']='https://ziglang.org/download/community-mirrors.txt'
        if not archive.exists() and transport.startswith('https://zigmirror.com/'):
            partial=space/'zig-x86_64-linux-0.17.1.tar.xz.part'
            range_archive(partial,transport)
            if file_sha(partial)!=ZIG_SHA:raise RuntimeError('range archive SHA')
            partial.rename(archive)
        elif not archive.exists() and transport!=ZIG_URL:
            partial=space/'zig-x86_64-linux-0.17.1.mirror.tar.xz.part'
            with partial.open('xb') as f:get(transport,f,ZIG_SIZE)
            if partial.stat().st_size!=ZIG_SIZE or file_sha(partial)!=ZIG_SHA:
                raise RuntimeError('mirror archive size/SHA')
            partial.rename(archive)
        elif not archive.exists():
            partial=space/'zig-x86_64-linux-0.17.1.tar.xz.part'
            if partial.is_symlink():raise RuntimeError('archive partial symlink')
            failures=0
            while not partial.exists() or partial.stat().st_size<ZIG_SIZE:
                offset=partial.stat().st_size if partial.exists() else 0
                end=min(ZIG_SIZE-1,offset+1024*1024-1)
                req=urllib.request.Request(ZIG_URL,headers={
                    'User-Agent':'GOSC-fixed-source-audit','Range':f'bytes={offset}-{end}'})
                before=offset
                try:
                    with op.open(req,timeout=12) as response,partial.open('ab') as f:
                        expected=f'bytes {offset}-{end}/{ZIG_SIZE}'
                        if response.status!=206 or response.headers.get('Content-Range')!=expected:
                            raise RuntimeError('range response mismatch')
                        while offset<=end:
                            try:b=response.read(min(65536,end-offset+1))
                            except http.client.IncompleteRead as e:b=e.partial
                            if not b:break
                            downloaded_local=len(b)
                            # Counter kept in the same download accounting path.
                            account_download(downloaded_local)
                            f.write(b);offset+=len(b)
                except (OSError,http.client.HTTPException):
                    failures+=1
                    if failures>8:raise
                if offset==before:
                    failures+=1
                    if failures>8:raise RuntimeError('range made no progress')
                if offset>ZIG_SIZE:raise RuntimeError('archive size cap')
            partial.rename(archive)
        if archive.is_symlink() or archive.stat().st_size!=ZIG_SIZE or file_sha(archive)!=ZIG_SHA:
            raise RuntimeError('official compiler archive size/SHA')
        with tarfile.open(archive,'r:xz') as tf:
            members=tf.getmembers()
            for m in members:
                p=Path(m.name)
                if p.is_absolute() or '..' in p.parts:raise RuntimeError('unsafe archive path')
            licenses=[]
            for m in members:
                if m.isfile() and m.size<=65536 and Path(m.name).name in {'LICENSE','LICENSE.txt','LICENSE.TXT','COPYING'}:
                    b=tf.extractfile(m).read();name=Path(m.name).as_posix().replace('/','__')
                    (out/name).write_bytes(b);licenses.append({'path':m.name,'size':m.size,'sha256':hashlib.sha256(b).hexdigest()})
            report['compiler']={'version':'0.17.1','url':ZIG_URL,'archive_size':archive.stat().st_size,
                'archive_sha256':file_sha(archive),'expanded_regular_file_bytes':sum(m.size for m in members if m.isfile()),
                'archive_members':len(members),'symlink_members':sum(m.issym() or m.islnk() for m in members),
                'filesystem_header_paths':[m.name for m in members if m.isfile() and m.name.endswith('/include/filesystem')],
                'license_files':licenses,'archive_only':True,'extracted_or_executed':False}
        report['status']='sources_and_compiler_archive_verified_not_installed'
    except BaseException as e:
        report.update(status='failed',error=type(e).__name__+': '+str(e));raise
    finally:
        report['download_body_bytes']=downloaded
        write_json(out/'preparation.json',report)

if __name__=='__main__':main()
