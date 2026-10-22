"""HPC-only execution records and Windows-side verified result retrieval.

Local: hpc_runs.py launch --kind test --stage R1 --purpose '...' -- {python} ...
Local: hpc_runs.py pull [--max-bytes 104857600]
HPC:   hpc_runs.py run --kind simulation --stage R3 --purpose '...' -- ...
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / 'research/sync'
KINDS = ['test','train','simulation','analysis','infrastructure']


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    temp.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    os.replace(temp, path)


def config():
    return json.loads((SYNC / 'config.json').read_text(encoding='utf-8'))


def require_hpc():
    c = config()
    if os.name != 'posix' or ROOT.resolve() != Path(c['remote_project_root']).resolve():
        raise RuntimeError('Project computation is HPC-only; use launch from local Windows.')
    if os.getuid() != c['remote_uid']:
        raise RuntimeError('Unexpected remote account')
    return c


def require_local():
    c = config()
    if ROOT.resolve() != Path(c['local_project_root']).resolve() or os.name != 'nt':
        raise RuntimeError('launch/pull must run from the configured local Windows checkout')
    return c


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args]).decode('utf-8',errors='replace').strip()


def refresh_dashboard():
    require_hpc()
    (SYNC / 'runs').mkdir(exist_ok=True)
    (SYNC / 'receipts').mkdir(exist_ok=True)
    records = []
    for p in sorted((SYNC/'runs').glob('*/status.json')):
        s = json.loads(p.read_text(encoding='utf-8'))
        m = json.loads((p.parent/'manifest.json').read_text(encoding='utf-8'))
        records.append({**s,'kind':m['kind'],'stage':m['stage'],'purpose':m['purpose']})
    value = {'generated_at':now(),'authority':'hpc','runs':records,
             'research_runs':sum(x['kind']!='infrastructure' for x in records),
             'note':'Execution status only. Local transfer completeness is recorded in receipts/.'}
    write_json(SYNC/'dashboard.json',value)
    text = '# HPC execution status\n\nGenerated: '+value['generated_at']+'\n\n'
    text += '| Run | Kind | Stage | Status | Exit |\n|---|---|---|---|---|\n'
    for r in records:
        text += '| {run_id} | {kind} | {stage} | {status} | {exit_code} |\n'.format(**r)
    if not records:
        text += '| No runs recorded | | | not_run | |\n'
    (SYNC/'STATUS.md').write_text(text,encoding='utf-8')
    return value


def resource_limits():
    values = {}
    for name, path in {
        'cpu_quota':'/sys/fs/cgroup/cpu/cpu.cfs_quota_us',
        'cpu_period':'/sys/fs/cgroup/cpu/cpu.cfs_period_us',
        'cpuset':'/sys/fs/cgroup/cpuset/cpuset.cpus',
        'memory_bytes':'/sys/fs/cgroup/memory/memory.limit_in_bytes',
    }.items():
        p = Path(path)
        values[name] = p.read_text().strip() if p.is_file() else None
    values['gpu_settings'] = {k:os.environ.get(k) for k in ['CUDA_DEVICE_MEMORY_LIMIT','CUDA_DEVICE_SM_LIMIT']}
    return values


def run(args):
    c = require_hpc()
    run_id = args.run_id or (args.kind+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6])
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',run_id) or '..' in run_id:
        raise RuntimeError('Invalid run ID')
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise RuntimeError('A command is required')
    snapshot = ROOT / '.local/hpc-sync/latest_manifest.json'
    if not snapshot.is_file():
        raise RuntimeError('A verified source sync is required before execution')
    source = json.loads(snapshot.read_text(encoding='utf-8'))
    if source['head'] != git('rev-parse','HEAD'):
        raise RuntimeError('Source snapshot HEAD does not match checkout')
    run_dir = SYNC / 'runs' / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    outputs = run_dir/'outputs'
    outputs.mkdir()
    runtime = Path(c['runtime_python'])
    if not runtime.is_file():
        raise RuntimeError('Configured HPC Python is unavailable')
    command = [x.replace('{python}',str(runtime)).replace('{run_dir}',str(run_dir)).replace('{output_dir}',str(outputs)) for x in command]
    cwd = ROOT if args.cwd is None else Path(args.cwd).resolve()
    if cwd != ROOT and ROOT not in cwd.parents:
        raise RuntimeError('Run cwd must stay in this HPC project')
    m = {'schema_version':1,'run_id':run_id,'kind':args.kind,'stage':args.stage,'purpose':args.purpose,
         'created_at':now(),'execution_host':socket.gethostname(),'ssh_alias':c['ssh_alias'],
         'project_root':str(ROOT),'cwd':str(cwd),'command':command,'seeds':args.seed,
         'models':args.model,'cache_mode':args.cache_mode,'config_file':args.config,
         'git_commit':git('rev-parse','HEAD'),'working_tree_status':git('-c','core.quotepath=false','status','--short'),
         'source_sync_id':source['sync_id'],'source_manifest_sha256':digest(snapshot),
         'python_executable':str(runtime),'runner_python_version':sys.version,
         'resource_limits':resource_limits(),'metrics_not_measured':['peak_gpu_memory','tokens','channel_uses']}
    if args.config:
        p = (ROOT/args.config).resolve()
        if ROOT not in p.parents or not p.is_file():
            raise RuntimeError('Config must be an existing project file')
        m['config_sha256'] = digest(p)
    write_json(run_dir/'manifest.json',m)
    shutil.copyfile(snapshot,run_dir/'source_snapshot.json')
    (run_dir/'source_changes.patch').write_bytes(subprocess.check_output(['git','-C',str(ROOT),'diff','--binary','HEAD']))
    untracked = set(x.decode('utf-8') for x in subprocess.check_output(['git','-C',str(ROOT),'ls-files','--others','--exclude-standard','-z']).split(b'\0') if x)
    with tarfile.open(run_dir/'source_untracked.tar.gz','w:gz') as archive:
        for entry in source['files']:
            if entry['path'] in untracked:
                p = ROOT/entry['path']
                if digest(p) != entry['remote_sha256']:
                    raise RuntimeError('Source changed since last verified sync: '+entry['path'])
                archive.add(p,arcname=entry['path'],recursive=False)
    state = {'run_id':run_id,'status':'planned','started_at':None,'finished_at':None,'exit_code':None,'pid':None}
    write_json(run_dir/'status.json',state)
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',MPLBACKEND='Agg',GOSC_RUN_DIR=str(run_dir),GOSC_OUTPUT_DIR=str(outputs))
    for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        env[k] = str(c['default_cpu_workers'])
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Signal '+str(signum))
    for sig in [signal.SIGTERM,signal.SIGHUP]:
        signal.signal(sig,interrupted)
    child = None
    start = time.monotonic()
    state.update(status='running',started_at=now())
    write_json(run_dir/'status.json',state)
    try:
        with (run_dir/'stdout.log').open('wb') as out, (run_dir/'stderr.log').open('wb') as err:
            child = subprocess.Popen(command,cwd=str(cwd),env=env,stdout=out,stderr=err,start_new_session=True)
            state['pid'] = child.pid
            write_json(run_dir/'status.json',state)
            refresh_dashboard()
            code = child.wait()
        state.update(status='completed' if code==0 else 'failed',exit_code=code)
    except KeyboardInterrupt as e:
        if child and child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL);child.wait()
        state.update(status='interrupted',exit_code=130,error=str(e))
    except Exception as e:
        state.update(status='failed',exit_code=127,error=repr(e))
    finally:
        state.update(finished_at=now(),elapsed_seconds=round(time.monotonic()-start,6))
        import resource
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        state['resource_usage'] = {'child_max_rss_kib':usage.ru_maxrss,'child_cpu_user_seconds':usage.ru_utime,'child_cpu_system_seconds':usage.ru_stime,'peak_gpu_memory':None}
        state['resource_usage_scope'] = 'All runner child processes, including Git metadata; not exclusive model/job performance.'
        artifacts = []
        for p in sorted(outputs.rglob('*')):
            if p.is_symlink():
                state.update(status='failed',exit_code=127,error='Symlink artifact is not supported');continue
            if p.is_file():
                artifacts.append({'path':p.relative_to(run_dir).as_posix(),'size':p.stat().st_size,'sha256':digest(p)})
        write_json(run_dir/'artifacts.json',{'run_id':run_id,'files':artifacts})
        write_json(run_dir/'status.json',state)
        refresh_dashboard()
    print(json.dumps(state,ensure_ascii=False))
    return state['exit_code']


def inventory():
    dashboard = refresh_dashboard()
    files = []
    candidates = [SYNC/'dashboard.json',SYNC/'STATUS.md'] + sorted((SYNC/'runs').rglob('*'))
    for p in candidates:
        if (SYNC/'runs') in p.parents:
            parts = p.relative_to(SYNC/'runs').parts
            if len(parts) > 1 and parts[1] == 'pytest-tmp':
                continue  # Disposable pytest workspace may contain its own symlinks.
        if p.is_symlink():
            raise RuntimeError('Symlink in run store')
        if p.is_file() and '.tmp-' not in p.name:
            files.append({'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':digest(p)})
    return {'generated_at':now(),'dashboard':dashboard,'files':files}


def remote_script(source, capture=True):
    c = config()
    r = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',c['ssh_alias'],'python3','-'],input=source.encode('utf-8'),capture_output=capture)
    if capture and r.stderr:
        print(r.stderr.decode('utf-8',errors='replace'),file=sys.stderr,end='')
    return r


def remote_command(argv):
    c = config()
    cmd = [c['runtime_python'],c['remote_project_root']+'/scripts/hpc_runs.py',*argv]
    return remote_script('import subprocess\nraise SystemExit(subprocess.call('+repr(cmd)+'))\n')


def pull(max_bytes=None):
    c = require_local()
    r = remote_command(['inventory'])
    if r.returncode:
        raise RuntimeError('Unable to retrieve HPC run inventory')
    remote = json.loads(r.stdout.decode('utf-8'))
    cap = c['default_pull_max_bytes'] if max_bytes is None else max_bytes
    if cap < 0:
        raise RuntimeError('max-bytes must be non-negative')
    transferred = 0
    rows = []
    sync_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]
    # Small manifests and statuses are fetched before large payloads/logs.
    files = sorted(remote['files'],key=lambda e:('/outputs/' in e['path'],e['size'],e['path']))
    for entry in files:
        rel = Path(entry['path'])
        if rel.is_absolute() or '..' in rel.parts or '\\' in entry['path'] or ':' in entry['path'] or not (entry['path'].startswith('research/sync/runs/') or entry['path'] in ['research/sync/dashboard.json','research/sync/STATUS.md']):
            raise RuntimeError('Unsafe remote inventory path')
        dst = ROOT / rel
        if ROOT.resolve() not in dst.resolve().parents or dst.is_symlink():
            raise RuntimeError('Destination escapes local project')
        row = dict(entry)
        if dst.is_file() and digest(dst)==entry['sha256']:
            row['transfer_status']='unchanged';rows.append(row);continue
        if transferred+entry['size'] > cap:
            row['transfer_status']='skipped_size_limit';rows.append(row);continue
        dst.parent.mkdir(parents=True,exist_ok=True)
        temp = dst.with_name(dst.name+'.partial-'+uuid.uuid4().hex)
        subprocess.run(['scp','-q','-o','BatchMode=yes',c['ssh_alias']+':'+c['remote_project_root']+'/'+entry['path'],str(temp)],check=True)
        if digest(temp)!=entry['sha256']:
            raise RuntimeError('File changed during pull or hash mismatch; retry: '+entry['path'])
        if dst.exists():
            backup = ROOT/'.local/hpc-runs/pull-backups'/sync_id/rel
            backup.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(dst,backup)
        os.replace(temp,dst)
        transferred += entry['size']
        row['transfer_status']='copied';rows.append(row)
    receipt = {'sync_id':sync_id,'created_at':now(),'direction':'hpc_to_local','source_host':c['ssh_alias'],
               'files':rows,'bytes_downloaded':transferred,'all_outputs_mirrored':all(x['transfer_status']!='skipped_size_limit' for x in rows),
               'execution_runs':remote['dashboard']['runs'],'note':'Execution completion and file-mirror completion are independent.'}
    path = SYNC/'receipts'/(sync_id+'.json')
    write_json(path,receipt)
    # A receipt is mirrored back to HPC so both sides know the transfer outcome.
    source='from pathlib import Path\nimport hashlib\np=Path('+repr(c['remote_project_root']+'/research/sync/receipts/'+path.name)+')\np.parent.mkdir(parents=True,exist_ok=True)\np.write_bytes('+repr(path.read_bytes())+')\nassert hashlib.sha256(p.read_bytes()).hexdigest()=='+repr(digest(path))+'\n'
    r = remote_script(source)
    if r.returncode:
        raise RuntimeError('Local pull finished but receipt upload failed; local receipt preserved')
    print(json.dumps({'receipt':str(path),'files':len(rows),'bytes_downloaded':transferred,'all_outputs_mirrored':receipt['all_outputs_mirrored']},ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action',required=True)
    for name in ['run','launch']:
        q = sub.add_parser(name)
        q.add_argument('--run-id')
        q.add_argument('--kind',choices=KINDS,required=True)
        q.add_argument('--stage',required=True)
        q.add_argument('--purpose',required=True)
        q.add_argument('--seed',type=int,action='append',default=[])
        q.add_argument('--model',action='append',default=[])
        q.add_argument('--cache-mode',default='not_applicable')
        q.add_argument('--config')
        q.add_argument('--cwd')
        q.add_argument('command',nargs=argparse.REMAINDER)
    q=sub.add_parser('pull');q.add_argument('--max-bytes',type=int)
    sub.add_parser('status');sub.add_parser('inventory')
    a = p.parse_args()
    if a.action=='run':return run(a)
    if a.action=='pull':return pull(a.max_bytes)
    if a.action=='status':print(json.dumps(refresh_dashboard(),ensure_ascii=False));return 0
    if a.action=='inventory':print(json.dumps(inventory(),ensure_ascii=False));return 0
    if a.action=='launch':
        require_local()
        subprocess.run([sys.executable,str(ROOT/'scripts/sync_hpc.py')],check=True)
        r=remote_command(['run',*sys.argv[2:]])
        if r.stdout:print(r.stdout.decode('utf-8',errors='replace'),end='')
        pull()
        return r.returncode


if __name__=='__main__':
    raise SystemExit(main())
