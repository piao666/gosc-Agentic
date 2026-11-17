"""New explicitly approved C++/vendor phase; old failed build gate stays closed."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'experiments_ext'))
from hpc_runs import require_hpc,write_json
from masbench_context_build import digest,group_rss,tree_bytes,stop

START=time.monotonic()
OUT=None
EVENT={}
SPACE=Path('/tmp/gosc-hpc-masbench-context-build-v3-20261116')
ARTIFACTS=Path('/tmp/gosc-cpp-vendor-artifacts-20261116')
GIB=1024**3
ARCHIVE_PREVIEW=Path('/tmp/gosc-snapshot-archive-preview-20261116')
SNAPSHOT_INDEX=Path('/tmp/gosc-snapshot-index-916289b-20261116')

def footprint():
    return (tree_bytes(SPACE)+tree_bytes(ARTIFACTS)+tree_bytes(ARCHIVE_PREVIEW)+
            (SNAPSHOT_INDEX.stat().st_size if SNAPSHOT_INDEX.is_file() else 0))

def check_budget(proc=None):
    used=footprint()
    rss=group_rss(proc.pid) if proc else 0
    own=int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
    EVENT['sampled_peak_directory_bytes']=max(EVENT.get('sampled_peak_directory_bytes',0),used)
    EVENT['sampled_peak_process_group_rss_bytes']=max(EVENT.get('sampled_peak_process_group_rss_bytes',0),rss)
    EVENT['sampled_peak_combined_bytes']=max(EVENT.get('sampled_peak_combined_bytes',0),used+rss+own)
    if used>2*GIB or rss>2*GIB or used+rss+own>4*GIB:raise RuntimeError('conservative scratch/process/combined cap')
    if time.monotonic()-START>1170:raise RuntimeError('1200s stage cap including cleanup')

def command(args,env,cwd,name):
    log=OUT/(name+'.log')
    with log.open('xb') as stream:
        proc=subprocess.Popen(args,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            while proc.poll() is None:
                check_budget(proc)
                if log.stat().st_size>4*1024**2:raise RuntimeError('log cap')
                time.sleep(.5)
            if proc.returncode:raise RuntimeError(name+' failed exit '+str(proc.returncode))
        except BaseException:stop(proc);raise
    check_budget()
    return log

def wrapper(path,zig,mode):
    # Keep every C++ object on one bundled libc++ ABI. cgo normally injects
    # -lstdc++; for this explicitly selected toolchain map it to libc++.
    body='''#!/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python
import os,sys
zig=ZIG
args=['-lc++' if x=='-lstdc++' else x for x in sys.argv[1:]]
os.execv(zig,[zig,MODE,'-target','x86_64-linux-gnu.2.27','-mcpu=baseline',*args])
'''.replace('ZIG',repr(str(zig))).replace('MODE',repr(mode))
    if path.exists():raise RuntimeError('wrapper target already exists')
    path.write_text(body);path.chmod(0o700)

def main():
    global OUT,EVENT
    require_hpc()
    OUT=Path(os.environ['GOSC_OUTPUT_DIR'])
    approval=ROOT/'research/protocols/masbench_cpp_vendor_build_authorization_2026-11-16.json'
    if not approval.is_file() or json.loads(approval.read_text()).get('authorized') is not True:
        raise RuntimeError('new C++ compiler installation/execution approval absent')
    permission=json.loads(approval.read_text())
    EVENT={'status':'running','approval_sha256':digest(approval),'model_calls':0,'gpu_used':False,
           'old_build_gate_modified':False,'binding_verified':False,'baseline_archive':'916289ba20fd9808a3673af0aebf175bfc830ccc',
           'compiler':'Zig0.17.1 bundled C/C++/libc++; glibc target2.27',
           'compiler_abi_change':'Every -lstdc++ passed to the isolated wrappers maps to -lc++; no system library modified'}
    try:
        cgroup=Path('/sys/fs/cgroup')
        limits={name:(cgroup/path).read_text().strip() for name,path in {
            'cpu_quota':'cpu/cpu.cfs_quota_us','cpu_period':'cpu/cpu.cfs_period_us',
            'cpuset':'cpuset/cpuset.cpus','memory':'memory/memory.limit_in_bytes'}.items()}
        EVENT['observed_cgroup_limits']=limits
        if int(limits['cpu_quota'])/int(limits['cpu_period'])<2 or limits['cpuset']!='0-1':
            raise RuntimeError('CPU quota/affinity drift; review required')
        for p in [SPACE,ARTIFACTS]:
            if p.resolve()!=p or p.is_symlink() or not p.is_dir() or p.stat().st_uid!=os.getuid():
                raise RuntimeError('scratch ownership/identity')
        if permission.get('preparation_run')!='hpc-masbench-cpp-vendor-prepare-v5-20261116':
            raise RuntimeError('explicit preparation identity required')
        prep_dir=ROOT/'research/sync/runs'/permission['preparation_run']
        prep=json.loads((prep_dir/'outputs/preparation.json').read_text())
        state=json.loads((prep_dir/'status.json').read_text())
        if state['status']!='completed' or prep['status']!='sources_and_compiler_archive_verified_not_installed':
            raise RuntimeError('preparation acceptance missing')
        archive=ARTIFACTS/'zig-x86_64-linux-0.17.1.tar.xz'
        if digest(archive)!='3581863e3cbcfd0fce0efc682ce7e9e93da96668a977791d356a26d2a7e9b17a':
            raise RuntimeError('compiler archive drift')
        check_budget()
        install=SPACE/'cpp17-toolchain'
        install.mkdir(mode=0o700,exist_ok=False)
        with tarfile.open(archive,'r:xz') as tf:
            members=tf.getmembers()
            if footprint()+sum(m.size for m in members if m.isfile())>2*GIB:
                raise RuntimeError('expanded toolchain would exceed directory cap')
            for m in members:
                p=Path(m.name)
                if p.is_absolute() or '..' in p.parts or m.issym() or m.islnk():
                    raise RuntimeError('unapproved archive member')
            tf.extractall(install,filter='data')
        zig=install/'zig-x86_64-linux-0.17.1/zig'
        if not zig.is_file():raise RuntimeError('compiler layout mismatch')
        env=os.environ.copy()
        env.update(CUDA_VISIBLE_DEVICES='',GOMAXPROCS='2',GOTOOLCHAIN='local',GOPROXY='off',
            GOSUMDB='sum.golang.org',GOPATH=str(SPACE/'gopath'),GOMODCACHE=str(SPACE/'modcache'),
            GOCACHE=str(SPACE/'cache'),GOTMPDIR=str(SPACE/'tmp'),TMPDIR=str(SPACE/'tmp'),
            ZIG_GLOBAL_CACHE_DIR=str(SPACE/'zig-cache'),ZIG_LOCAL_CACHE_DIR=str(SPACE/'zig-local-cache'),
            OLLAMA_LIBRARY_PATH=str(SPACE/'no-backend-libraries'),OMP_NUM_THREADS='2',CGO_ENABLED='1')
        env['CGO_CXXFLAGS']='-O2 -g -std=c++17'
        bins=SPACE/'cpp17-wrappers';bins.mkdir(mode=0o700,exist_ok=False)
        wrapper(bins/'cc',zig,'cc');wrapper(bins/'c++',zig,'c++')
        env.update(CC=str(bins/'cc'),CXX=str(bins/'c++'))
        command([str(zig),'version'],env,SPACE,'compiler-version')
        probe=SPACE/'cpp17-abi-probe';probe.mkdir(mode=0o700,exist_ok=False)
        (probe/'go.mod').write_text('module gosc.local/cpp17probe\n\ngo 1.24.0\n')
        (probe/'main.go').write_text('package main\n/*\nint cpp17_probe(void);\n*/\nimport "C"\nimport "fmt"\nfunc main(){if C.cpp17_probe()!=1{panic("ABI/standard-library mismatch")};fmt.Println("cpp17_cgo_probe_ok")}\n')
        (probe/'probe.cpp').write_text('#include <filesystem>\n#include <string>\nextern "C" int cpp17_probe(void) { std::filesystem::path p("/tmp/gosc-probe");std::string s=p.filename().string();return s=="gosc-probe"; }\n')
        go=SPACE/'go/bin/go'
        command([str(go),'build','-p','1','-mod=readonly','-o',str(probe/'probe'),'.'],env,probe,'abi-build')
        command([str(probe/'probe')],env,probe,'abi-run')
        if (OUT/'abi-run.log').read_text().strip()!='cpp17_cgo_probe_ok':raise RuntimeError('ABI marker')
        EVENT['cpp17_cgo_probe_passed']=True
        src=SPACE/'source'
        reference=ROOT/'research/logs/masbench-context-deployment-2026-11-16/source_reference'
        for p in reference.glob('*.txt'):
            if digest(src/p.name[:-4].replace('__','/'))!=digest(p):raise RuntimeError('fixed source drift')
        routes=ROOT/'research/logs/masbench-cpp-vendor-2026-11-16/source_reference_server_routes.go.txt'
        if digest(routes)!='12d2889140fc0c84162bf7fe9fd84848670aed34caf1c1200631349cfbab3c8c' or digest(src/'server/routes.go')!=digest(routes):
            raise RuntimeError('fixed default-system source drift')
        lock=json.loads((ROOT/'research/protocols/masbench_vendor_source_lock_2026-11-16.json').read_text())
        parent=src/'llama/llama.cpp';parent.chmod(0o755)
        vendor=parent/'vendor';vendor.mkdir(mode=0o755,exist_ok=False)
        for f in lock['files']:
            raw=(ARTIFACTS/'vendor'/f['path']).read_bytes()
            if len(raw)!=f['size'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=f['git_blob_sha1']:
                raise RuntimeError('fixed vendor drift')
            dest=vendor/f['path'];dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as output:output.write(raw)
        helper=ROOT/'experiments_ext/masbench_context_counter/main.go'
        if digest(src/'cmd/gosc-context-counter/main.go')!=digest(helper):raise RuntimeError('helper source drift')
        binary=SPACE/'context-counter'
        if binary.exists():raise RuntimeError('binary target exists')
        command([str(go),'build','-p','1','-mod=readonly','-o',str(binary),'./cmd/gosc-context-counter'],env,src,'helper-build')
        command([str(go),'version','-m',str(binary)],env,SPACE,'helper-build-info')
        command([str(go),'version','-m',str(ROOT/'.local/ollama/runtime/0.11.11/bin/ollama')],env,SPACE,'deployed-build-info')
        EVENT.update(status='built_offline_candidate_not_deployment_verified',binary=str(binary),
                     binary_sha256=digest(binary),helper_source_sha256=digest(helper),
                     source_commit=lock['source_commit'],vendor_files=len(lock['files']))
    except BaseException as e:
        EVENT.update(status='failed',error=type(e).__name__+': '+str(e));raise
    finally:
        EVENT.update(elapsed_seconds=time.monotonic()-START,final_directory_bytes=footprint())
        write_json(OUT/'build.json',EVENT)

if __name__=='__main__':main()
