"""Read-only inventory of HPC quotas, service lease and registered large files."""
from collections import Counter
from pathlib import Path
import ctypes
import json
import os
import shutil
import stat
import subprocess

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
HDD = Path('/hdd/u202520081000097')
RUNS = ROOT/'research/sync/runs'
UID = 8301880
assert os.getuid()==UID and os.stat(HDD).st_uid==UID and not HDD.is_symlink()


def query(args):
    done = subprocess.run(args, capture_output=True, text=True, timeout=8, check=False)
    return {'exit':done.returncode,'stdout':done.stdout.strip(),'stderr':done.stderr.strip()}


class Dqblk(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in
                ('bhardlimit', 'bsoftlimit', 'curspace', 'ihardlimit', 'isoftlimit', 'curinodes', 'btime', 'itime')]
    _fields_ += [('valid', ctypes.c_uint32)]


def vfs_quota(mount):
    libc = ctypes.CDLL(None, use_errno=True)
    answer = Dqblk()
    code = 0x800007 << 8  # Linux QCMD(Q_GETQUOTA, USRQUOTA).
    rc = libc.quotactl(ctypes.c_int(code), os.fsencode(mount), ctypes.c_int(UID), ctypes.byref(answer))
    if rc:
        error = ctypes.get_errno()
        return {'errno':error,'error':os.strerror(error)}
    return {field: getattr(answer,field) for field, _ in answer._fields_}


counts = Counter()
running, candidates, unmanaged, failures = [], [], [], []
cutoff = 32*1024**2
for status_file in sorted(RUNS.glob('*/status.json')):
    run = status_file.parent
    state = json.loads(status_file.read_bytes())
    counts[state['status']] += 1
    if state['status'] in ('planned', 'running'):
        running.append({name:state.get(name) for name in ('run_id','status','pid','started_at')})
    if state['status']!='completed' or state.get('exit_code')!=0:
        continue
    index = run/'artifacts.json'
    if not index.is_file():
        failures.append(run.name)
        continue
    entries = json.loads(index.read_bytes())['files']
    for row in entries:
        if row['size']<cutoff or not row['path'].startswith('outputs/'):
            continue
        path = run/row['path']
        if not path.exists():
            unmanaged.append({'path':str(path),'reason':'missing from SSD','indexed_bytes':row['size']})
            continue
        st = path.lstat()
        if (not stat.S_ISREG(st.st_mode) or path.resolve()!=path or st.st_uid!=UID
                or st.st_size!=row['size'] or st.st_nlink!=1):
            unmanaged.append({'path':str(path),'reason':'metadata or link mismatch','indexed_bytes':row['size']})
            continue
        candidates.append({'run_id':run.name,'path':path.relative_to(ROOT).as_posix(),
                           'relative':row['path'],'bytes':st.st_size,'allocated_bytes':st.st_blocks*512,
                           'inode':st.st_ino,'links':st.st_nlink,'registration_sha256':row['sha256']})
candidates.sort(key=lambda row:(-row['allocated_bytes'],row['path']))
lease = (ROOT/'.local/t1-service.lock').read_bytes()
state = json.loads((ROOT/'.local/ollama/service.json').read_bytes())
pid = int(state['pid'])
proc = Path('/proc')/str(pid)
alive = proc.is_dir()
mounts = ['/home/u202520081000097','/hdd']
print(json.dumps({
    'host':os.uname().nodename,'uid':UID,'root':str(ROOT),'hdd':str(HDD),
    'filesystem_space':query(['df','-B1','-T',str(ROOT),str(HDD)]),
    'vfs_user_quota':{mount:vfs_quota(mount) for mount in mounts},
    'quota_commands':{name:shutil.which(name) for name in ('lfs','quota','findmnt','lctl')},
    'service_pid':pid,'service_stamp':(proc/'stat').read_text().rsplit(') ',1)[1].split()[19] if alive else None,
    'service_children':query(['ps','--ppid',str(pid),'-o','pid=,stat=,comm=']),
    'listener':query(['ss','-Hlnpt','sport = :11434']),
    'established':query(['ss','-Hnt','state','established','sport = :11434 or dport = :11434']),
    'gpu':query(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader']),
    'lease_size':len(lease),'lease':json.loads(lease) if lease else None,
    'status_counts':dict(counts),'pending_or_running':running,
    'missing_artifact_index':failures, 'rejected_candidates':unmanaged,
    'large_files':candidates, 'large_files_bytes':sum(row['bytes'] for row in candidates),
    'large_files_allocated_bytes':sum(row['allocated_bytes'] for row in candidates),
}))
