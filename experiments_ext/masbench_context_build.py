"""HPC registered isolated build with counted official downloads and stop caps."""
from pathlib import Path
import hashlib
import http.server
import json
import os
import shutil
import signal
import subprocess
import sys
import tarfile
import threading
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from hpc_runs import require_hpc, write_json

PLAN = ROOT/'research/protocols/masbench_context_build_approved_2026-11-16.json'
START = time.monotonic()
DOWNLOADED = 0
LOCK = threading.RLock()

def digest(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def tree_bytes(p):
    total = 0
    for root, ds, fs in os.walk(p):
        for name in fs:
            try: total += (Path(root)/name).stat().st_size
            except FileNotFoundError: pass
    return total

def group_rss(pgid):
    rss = 0
    for p in Path('/proc').iterdir():
        if not p.name.isdigit(): continue
        try:
            fields = (p/'stat').read_text().split(') ',1)[1].split()
            if int(fields[2]) == pgid: rss += int(fields[21])*os.sysconf('SC_PAGE_SIZE')
        except (OSError, ValueError, IndexError): pass
    return rss

class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlsplit(newurl)
        if u.scheme!='https' or u.hostname not in {'go.dev','dl.google.com','proxy.golang.org','storage.googleapis.com','sum.golang.org','goproxy.cn'}:
            raise RuntimeError('Unapproved download redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}),OfficialRedirect())

def fetch(url, sink, cap):
    global DOWNLOADED
    with LOCK, OPENER.open(url, timeout=25) as response:
        length = response.headers.get('Content-Length')
        if length and DOWNLOADED+int(length)>cap: raise RuntimeError('download cap before body')
        while True:
            remaining = cap-DOWNLOADED
            if remaining<=0: raise RuntimeError('download cap')
            chunk = response.read(min(65536,remaining))
            if not chunk: break
            DOWNLOADED += len(chunk)
            sink.write(chunk)
            if time.monotonic()-START>1750: raise RuntimeError('download wall cap')

def stop(proc):
    try: os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError: pass
    try: proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try: os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        proc.wait(timeout=5)

def execute(args, env, cwd, log, space, cfg):
    peak = 0
    with log.open('xb') as stream:
        p = subprocess.Popen(args,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            while p.poll() is None:
                peak=max(peak,group_rss(p.pid))
                if peak>cfg['process_tree_rss_bytes']: raise RuntimeError('process-group RSS cap')
                used=tree_bytes(space)
                if used>cfg['additional_peak_disk_bytes']: raise RuntimeError('isolated directory byte cap')
                if cfg.get('tmpfs_combined_memory_bytes'):
                    own=int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
                    if used+peak+own>cfg['tmpfs_combined_memory_bytes']:
                        raise RuntimeError('tmpfs plus process RSS combined cap')
                if log.stat().st_size>4*1024*1024: raise RuntimeError('command log cap')
                if time.monotonic()-START>cfg['build_wall_seconds']-8: raise RuntimeError('build wall cap')
                time.sleep(0.5)
            if p.returncode: raise RuntimeError('command failed exit '+str(p.returncode)+': '+str(log))
        except BaseException:
            stop(p); raise
    return peak

def main():
    require_hpc()
    gate=ROOT/'research/protocols/masbench_context_build_status_2026-11-16.json'
    if gate.exists() and json.loads(gate.read_text()).get('current_build_allowed') is not True:
        raise RuntimeError('Build stopped: review C++17/full-vendor prerequisites and new approval before any retry')
    cfg=json.loads(PLAN.read_text())
    assert cfg['authorized'] is True and cfg['model_generation_authorized'] is False
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    # Home-account quota is insufficient. Use the HPC job tmpfs, within
    # stricter derived limits so its storage is not hidden memory overhead.
    cfg['process_tree_rss_bytes']=min(cfg['process_tree_rss_bytes'],2*1024**3)
    cfg['additional_peak_disk_bytes']=min(cfg['additional_peak_disk_bytes'],2*1024**3)
    cfg['tmpfs_combined_memory_bytes']=4*1024**3
    scratch=Path('/tmp')
    if scratch.resolve()!=scratch or os.statvfs(scratch).f_bavail*os.statvfs(scratch).f_frsize<5*1024**3:
        raise RuntimeError('HPC temporary filesystem identity/space gate')
    # Reuse only the verified toolchain from the failed transport attempt.
    # The old run/logs remain immutable; all command logs belong to this run.
    prior_dir=ROOT/'research/sync/runs/hpc-masbench-context-build-v3-20261116'
    previous=json.loads((prior_dir/'outputs/build.json').read_text())
    previous_status=json.loads((prior_dir/'status.json').read_text())
    if previous_status['status']!='failed' or previous['official_download_payload_bytes']!=66999944:
        raise RuntimeError('unexpected toolchain resume provenance')
    space=Path(previous['isolated_root'])
    if space!=Path('/tmp/gosc-hpc-masbench-context-build-v3-20261116') or space.resolve()!=space or space.is_symlink():
        raise RuntimeError('unsafe scratch resume')
    if not space.is_dir() or space.stat().st_uid!=os.getuid(): raise RuntimeError('scratch owner')
    space.chmod(0o700)
    event={'status':'started','authorization_sha256':digest(PLAN),'isolated_root':str(space),
           'official_download_payload_bytes':0,'server_or_python_environment_modified':False,
           'model_generations':0,'gpu_used':False,'source_commit':cfg['ollama_source_commit'],
           'scratch_scope':'HPC /tmp tmpfs; ephemeral, not home quota',
           'derived_rss_cap':cfg['process_tree_rss_bytes'],
           'derived_disk_cap':cfg['additional_peak_disk_bytes'],
           'tmpfs_combined_memory_cap':cfg['tmpfs_combined_memory_bytes'],
           'prior_toolchain_run':'hpc-masbench-context-build-v3-20261116',
           'module_transport':'https://goproxy.cn',
           'checksum_authority':'sum.golang.org default signed public key; verification not disabled'}
    write_json(out/'build.json',event)
    proxy=None
    try:
        # One exact, own failed preallocation; keep its zero-length inode and
        # original run evidence. No result/source/cache cleanup is performed.
        old=ROOT/'.local/masbench-exact-context/20261116/quota-reservation'
        if old.exists():
            prior=ROOT/'research/sync/runs/hpc-masbench-context-build-20261116'
            status=json.loads((prior/'status.json').read_text())
            observed=json.loads((prior/'outputs/build.json').read_text())
            if (status['status']!='failed' or observed['official_download_payload_bytes']!=0
                    or observed.get('error')!='OSError: [Errno 9] Bad file descriptor'
                    or old.is_symlink() or old.resolve()!=old
                    or old.stat().st_uid!=os.getuid()
                    or old.stat().st_size not in (0,cfg['additional_peak_disk_bytes'])):
                raise RuntimeError('unexpected old reservation; preserve')
            event['failed_probe_space_reclaimed_bytes']=old.stat().st_size
            with old.open('r+b') as f: f.truncate(0);os.fsync(f.fileno())
        # Only a small write probe on tmpfs. Directory and combined memory
        # monitors enforce the derived budget during commands; no full RAM
        # preallocation and no assertion about home-account quota.
        reserve=space/'quota-reservation'
        with reserve.open('x+b') as f:
            os.posix_fallocate(f.fileno(),0,1024*1024)
            os.fsync(f.fileno())
        event['quota_allocation_probe_bytes']=reserve.stat().st_size
        reserve.unlink()  # Only this run's just-created reservation; no old data.
        tool_archive=space/'go.tar.gz'
        if tool_archive.stat().st_size!=cfg['go_archive_bytes'] or digest(tool_archive)!=cfg['go_archive_sha256']:
            raise RuntimeError('official Go archive mismatch')
        with tarfile.open(tool_archive,'r:gz') as tf:
            for name in ['go/bin/go','go/bin/gofmt']:
                if hashlib.sha256(tf.extractfile(name).read()).hexdigest()!=digest(space/name):
                    raise RuntimeError('installed toolchain binary drift')
        # Count the earlier archive against the same total approved download
        # budget instead of resetting the accounting at this new run ID.
        global DOWNLOADED
        transport_run=ROOT/'research/sync/runs/hpc-masbench-context-build-v4-20261116'
        transport=json.loads((transport_run/'outputs/build.json').read_text())
        if transport.get('module_identity',{}).get('Sum')!='h1:mErMiUGclp47rCDbSUmBiY2L76EpT0uIYRZVBO6qg/k=':
            raise RuntimeError('resume module identity absent')
        DOWNLOADED=transport['official_download_payload_bytes']
        class Proxy(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if '..' in self.path or not self.path.startswith('/'):
                    self.send_error(400);return
                try:
                    # Buffer disk response before headers; all bytes, including
                    # repeated module requests, pass through the common counter.
                    import tempfile
                    with tempfile.TemporaryFile(dir=space) as f:
                        fetch('https://goproxy.cn'+self.path,f,cfg['new_download_bytes'])
                        size=f.tell();f.seek(0)
                        self.send_response(200);self.send_header('Content-Length',str(size));self.end_headers()
                        shutil.copyfileobj(f,self.wfile)
                except urllib.error.HTTPError as exc:
                    self.send_error(exc.code)
                except Exception as exc:
                    self.send_error(502,type(exc).__name__)
            def log_message(self,*a): pass
        proxy=http.server.ThreadingHTTPServer(('127.0.0.1',0),Proxy)
        threading.Thread(target=proxy.serve_forever,daemon=True).start()
        env=os.environ.copy()
        env.update(GOTOOLCHAIN='local',GOPROXY='http://127.0.0.1:'+str(proxy.server_port),
                   GOSUMDB='sum.golang.org',GOPRIVATE='',GONOPROXY='',GONOSUMDB='',
                   GOPATH=str(space/'gopath'),GOMODCACHE=str(space/'modcache'),GOCACHE=str(space/'cache'),
                   GOTMPDIR=str(space/'tmp'),TMPDIR=str(space/'tmp'),GOMAXPROCS='2',GOAMD64='v1',
                   CUDA_VISIBLE_DEVICES='',OLLAMA_LIBRARY_PATH=str(space/'no-backend-libraries'),
                   OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',CGO_ENABLED='1')
        (space/'tmp').mkdir(exist_ok=True)
        go=str(space/'go/bin/go')
        event['download_peak_rss_bytes']=execute([go,'mod','download','-json','github.com/ollama/ollama@v0.11.11'],
                                               env,space,out/'source-module.log',space,cfg)
        module=json.loads((out/'source-module.log').read_text())
        if module.get('Error'): raise RuntimeError('source module download rejected')
        origin=module.get('Origin',{})
        if module.get('Sum')!='h1:mErMiUGclp47rCDbSUmBiY2L76EpT0uIYRZVBO6qg/k=' or module.get('GoModSum')!='h1:9+1//yWPsDE2u+l1a5mpaKrYw4VdnSsRU3ioq5BvMms=':
            raise RuntimeError('fixed module or go.mod checksum mismatch')
        if origin.get('Hash') and origin['Hash']!=cfg['ollama_source_commit']:
            raise RuntimeError('module Origin differs from fixed commit')
        event['module_identity']={k:module.get(k) for k in ['Path','Version','Sum','GoModSum','Origin']}
        src=space/'source'
        if not src.exists(): shutil.copytree(module['Dir'],src)
        src.chmod(0o755)
        reference=ROOT/'research/logs/masbench-context-deployment-2026-11-16/source_reference'
        checks={}
        for p in reference.glob('*.txt'):
            rel=p.name[:-4].replace('__','/')
            checks[rel]=digest(src/rel)==digest(p)
        if not checks or not all(checks.values()): raise RuntimeError('fixed-commit source reference mismatch')
        event['source_reference_matches']=checks
        target=src/'cmd/gosc-context-counter'
        # A Go module cache is read-only by design. Only this isolated copy's
        # insertion directory is made writable; original module files stay put.
        (src/'cmd').chmod(0o755)
        target.mkdir(parents=True,exist_ok=True)
        source_helper=ROOT/'experiments_ext/masbench_context_counter/main.go'
        if (target/'main.go').exists() and digest(target/'main.go')!=digest(source_helper):
            raise RuntimeError('existing helper source drift')
        if not (target/'main.go').exists(): shutil.copy2(source_helper,target/'main.go')
        binary=space/'context-counter'
        event['compile_peak_rss_bytes']=execute([go,'build','-p','1','-mod=readonly','-o',str(binary),
                                               './cmd/gosc-context-counter'],env,src,out/'compile.log',space,cfg)
        event.update(status='built_offline_candidate_not_deployment_verified',binary=str(binary),
                     binary_sha256=digest(binary),helper_source_sha256=digest(target/'main.go'))
        execute([go,'version','-m',str(binary)],env,space,out/'helper-build-info.log',space,cfg)
        execute([go,'version','-m',str(ROOT/'.local/ollama/runtime/0.11.11/bin/ollama')],
                env,space,out/'deployed-build-info.log',space,cfg)
        event['deployed_build_info_observed']=True
    except BaseException as exc:
        event.update(status='failed',error=type(exc).__name__+': '+str(exc))
        raise
    finally:
        if proxy: proxy.shutdown();proxy.server_close()
        event.update(official_download_payload_bytes=DOWNLOADED,elapsed_seconds=time.monotonic()-START,
                     final_directory_bytes=tree_bytes(space),binding_verified=False)
        write_json(out/'build.json',event)

if __name__=='__main__': main()
