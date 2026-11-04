"""Read-only service/package/resource inventory; never generates, loads or starts a model."""
import datetime
import json
from pathlib import Path
import subprocess
import urllib.request

LOG = Path(__file__).resolve().parent
REMOTE = r'''
import datetime, importlib.metadata as md, json, os, platform, subprocess, sys, urllib.request
from pathlib import Path
root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
def command(args):
    p=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=10)
    return dict(exit_code=p.returncode,stdout=p.stdout.strip(),stderr=p.stderr.strip())
def get(path):
    try:
        with urllib.request.urlopen('http://127.0.0.1:11434'+path,timeout=4) as f:
            return dict(status='available',response=json.load(f))
    except Exception as e:return dict(status='unavailable',error=type(e).__name__+': '+str(e))
def package(name):
    try:return md.version(name)
    except md.PackageNotFoundError:return None
limits={}
for name,path in [('quota','/sys/fs/cgroup/cpu/cpu.cfs_quota_us'),('period','/sys/fs/cgroup/cpu/cpu.cfs_period_us'),('cpuset','/sys/fs/cgroup/cpuset/cpuset.cpus'),('memory','/sys/fs/cgroup/memory/memory.limit_in_bytes')]:
    p=Path(path);limits[name]=p.read_text().strip() if p.exists() else 'unavailable'
space=os.statvfs(root)
data=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),uid=os.getuid(),host=platform.node(),
    project_root=str(root),python_executable=sys.executable,python_version=platform.python_version(),
    git_head=command(['git','rev-parse','HEAD']),origin=command(['git','remote','get-url','origin']),
    resource_limits=limits,filesystem_free_bytes=space.f_bavail*space.f_frsize,
    packages={n:package(n) for n in ['openai','httpx','requests','python-dotenv','numpy','pandas','tiktoken','pytest']},
    gpu=command(['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.used','--format=csv,noheader']),
    ollama={p:get(p) for p in ['/api/version','/api/tags','/api/ps','/v1/models']},
    inference_requested=False,service_started=False,dependencies_installed=False)
print(json.dumps(data,ensure_ascii=False))
'''
cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','hpc',
     '/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -']
try:
    result=subprocess.run(cmd,input=REMOTE.encode('utf-8'),capture_output=True,timeout=70)
    (LOG/'hpc_inventory_stdout.json').write_bytes(result.stdout)
    (LOG/'hpc_inventory_stderr.txt').write_bytes(result.stderr)
    hpc=dict(exit_code=result.returncode)
    if result.returncode==0:hpc['inventory']=json.loads(result.stdout)
except subprocess.TimeoutExpired:
    hpc=dict(status='ssh_timeout',inference_requested=False)
local={}
for path in ['/api/version','/api/tags']:
    try:
        with urllib.request.urlopen('http://127.0.0.1:11434'+path,timeout=2) as stream:
            local[path]=dict(status='available',response=json.load(stream))
    except Exception as e:local[path]=dict(status='unavailable',error=type(e).__name__)
record=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Read-only inventory, no project test/inference/task',
    command=cmd,local_loopback_ollama=local,hpc=hpc)
(LOG/'environment_inventory.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(record,ensure_ascii=False))
