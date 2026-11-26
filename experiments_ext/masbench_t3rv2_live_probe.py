"""Registered two-probe deployment and bounded reversible service lifecycle."""
import json
import os
from pathlib import Path
import resource
import selectors
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from scripts.hpc_runs import require_hpc,write_json
from extensions.masbench_reasoning import fair_final_v2_live as v2
from extensions.masbench_reasoning import live_driver as old
from extensions.masbench_reasoning.fair_final_v2 import parse_output
from extensions.masbench_reasoning.execution_safety import SafetyError,canonical,digest
from experiments_ext.masbench_t1b_live import own_listener,process_rss

STATE=ROOT/'.local/ollama/service.json'
PROFILE=ROOT/'.local/ollama/context_profile.json'
LEASE=ROOT/'.local/t1-service.lock'


def sync_dir(p):
    fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def quota():
    p=ROOT/'research/logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota.py'
    return json.loads(subprocess.check_output([sys.executable,str(p)],timeout=10))


def storage_gate(q):
    for name,minimum in [('ssd',64*1024**2),('hdd',256*1024**2)]:
        value=q['volumes'][name].get('remaining_to_hard_limit_bytes')
        if type(value) is not int or value<minimum:raise SafetyError('personal_'+name+'_quota')


class Monitor:
    def __init__(self,budget):
        self.budget=budget;self.runtime=None;self.last=0;self.last_end=0
        self.peaks=dict(driver_rss=0,service_rss=0,gpu_bytes=0)
        self.samples=0;self.max_start_gap=0;self.enforce=True
        self.service_tree_root=None

    def __call__(self,force=False):
        now=time.monotonic()
        if not force and now-self.last<.1:return
        if self.enforce and self.last and now-self.last>.5:
            self.budget.control('resource-sampling-gap',seconds=now-self.last)
            raise SafetyError('resource_monitor_gap_over_0.5s')
        if self.enforce and self.last:self.max_start_gap=max(self.max_start_gap,now-self.last)
        self.last=now
        pid=self.runtime.service_pid if self.runtime else -1
        if self.runtime and old.proc_stamp(pid)!=self.runtime.service_stamp:
            raise SafetyError('monitored_service_identity_drift')
        driver,service=process_rss(os.getpid(),self.service_tree_root or pid)
        raw=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],
                                    timeout=.3,text=True)
        values=dict(driver_rss=driver,service_rss=service,gpu_bytes=sum(int(x) for x in raw.splitlines())*1024**2)
        self.samples+=1
        for k,n in values.items():self.peaks[k]=max(self.peaks[k],n)
        self.budget.control('resources',values=values,sample_start=now,
                            sample_end=time.monotonic(),enforced_active=self.enforce,
                            scope='observation-stop-not-hard-isolation')
        if driver>2*1024**3 or service>16*1024**3 or values['gpu_bytes']>16*1024**3:
            raise SafetyError('resource_observation_stop')
        self.last_end=time.monotonic()
        return values

    def bind(self,runtime,enforce=True):
        self.runtime=runtime;self.last=0;self.enforce=enforce
        self.budget.control('monitor-bind',runtime=runtime.identity() if runtime else None,enforced_active=enforce)


class Deployment:
    def __init__(self,driver,monitor,log,spawner=None):
        self.driver,self.monitor,self.log=driver,monitor,Path(log)
        self.original=None;self.env=None;self.changed=False;self.start_count=0
        self.spawner=spawner

    def runtime(self,context):
        pid=json.loads(STATE.read_bytes())['pid'];stamp=old.proc_stamp(pid)
        if not stamp:raise SafetyError('owned_service_not_running')
        r=old.Runtime(str(ROOT),v2.HELPER,pid,stamp,v2.BINARY_SHA,context)
        old.runtime_files(r);return r

    def idle(self,runtime):
        old.runtime_files(runtime);own_listener(runtime)
        if self.driver.http('lifecycle_get','/api/ps').get('models')!=[] or old.runner_identities(runtime):
            raise SafetyError('service_not_idle')
        values=self.monitor(force=True)
        if values['gpu_bytes']!=0:raise SafetyError('GPU_not_idle')

    def stop(self,runtime):
        self.idle(runtime);self.driver.ledger.operation('stop')
        self.driver.ledger.control('service-stop',runtime=runtime.identity())
        os.kill(runtime.service_pid,signal.SIGTERM)
        end=time.monotonic()+12;self.monitor.bind(None,enforce=False)
        while time.monotonic()<end:
            try:os.waitpid(runtime.service_pid,os.WNOHANG)
            except ChildProcessError:pass
            if old.proc_stamp(runtime.service_pid)!=runtime.service_stamp:
                break
            try:
                if old.proc_fields(Path('/proc')/str(runtime.service_pid))[0]=='Z':break
            except FileNotFoundError:break
            self.monitor();time.sleep(.03)
        else:raise SafetyError('service_exit_deadline')
        if subprocess.check_output(['ss','-Hlnpt','sport = :11434']):
            raise SafetyError('listener_remains_after_stop')
        self.driver.ledger.control('service-exit',pid=runtime.service_pid,stamp=runtime.service_stamp)

    def start(self,context):
        self.driver.ledger.operation('start');self.start_count+=1
        if subprocess.check_output(['ss','-Hlnpt','sport = :11434']):raise SafetyError('listener_before_start')
        exe=ROOT/'.local/ollama/runtime/0.11.11/bin/ollama'
        if v2.file_sha(exe)!=v2.BINARY_SHA:raise SafetyError('binary_drift_before_start')
        env=dict(self.env,OLLAMA_CONTEXT_LENGTH=str(context))
        log=self.log/('service-'+str(context)+'.log')
        if self.spawner is None:raise SafetyError('separate_service_spawner_required')
        spawned=self.spawner.request(dict(context=context,env=env,log=str(log)))
        pid=spawned['pid'];stamp=old.proc_stamp(pid)
        if not stamp:raise SafetyError('service_start_process_missing')
        if stamp!=spawned['stamp']:raise SafetyError('service_spawn_stamp_drift')
        r=old.Runtime(str(ROOT),v2.HELPER,pid,stamp,v2.BINARY_SHA,context)
        self.driver.ledger.control('service-spawn-limits',pid=pid,stamp=stamp,
                                   service_AS=spawned['service_AS'],spawner_pid=self.spawner.process.pid)
        write_json(STATE,dict(pid=pid,binary=str(exe),bind='127.0.0.1:11434',
            models=str(ROOT.parents[1]/'models/ollama-gosc'),version='0.11.11',
            started_at_unix=time.time(),log=str(log),auto_restart_after_container_reboot=False))
        self.driver.runtime=r;self.monitor.bind(r,enforce=False)
        end=time.monotonic()+60
        for _ in range(61):
            if old.proc_stamp(r.service_pid)!=r.service_stamp:raise SafetyError('service_exited_while_starting')
            if subprocess.check_output(['ss','-Hlnpt','sport = :11434']):
                if self.driver.http('lifecycle_get','/api/version',deadline=end).get('version')=='0.11.11':
                    self.idle(r);self.driver.ledger.control('service-start',runtime=r.identity())
                    self.monitor.bind(r,enforce=True);return r
            else:
                # Even a readiness attempt made before a listener exists is
                # permanently accounted, without an unmetered ping.
                self.driver.ledger.charge('lifecycle_get','/api/version')
            if time.monotonic()>=end:break
            self.monitor();time.sleep(.05)
        raise SafetyError('service_readiness_deadline_or_cap')

    def enter(self):
        d=self.driver
        self.original=self.runtime(1024)
        if (self.original.service_pid!=d.approval.get('baseline_pid')
                or self.original.service_stamp!=d.approval.get('baseline_stamp')):
            raise SafetyError('approved_baseline_PID_stamp_drift')
        d.runtime=self.original;self.monitor.bind(self.original,enforce=False)
        if PROFILE.exists() or d.lease.owner()!=d.owner:raise SafetyError('profile_or_lease_not_owned')
        self.idle(self.original)
        raw=Path('/proc',str(self.original.service_pid),'environ').read_bytes()
        self.env=dict(x.split('=',1) for x in raw.decode().split('\0') if '=' in x)
        expected=b'{"context_tokens":16384}\n'
        with PROFILE.open('xb') as f:f.write(expected);f.flush();os.fsync(f.fileno())
        sync_dir(PROFILE.parent);self.changed=True
        self.stop(self.original)
        return self.start(16384)

    def rollback(self):
        d=self.driver
        if not self.changed:
            self.monitor.enforce=False
            if self.original:
                d.runtime=self.original;self.monitor.bind(self.original,enforce=False)
                self.idle(self.original);d.lease.clear(d.owner)
                d.ledger.control('rollback-unchanged-baseline',runtime=self.original.identity())
                return self.original.identity()
            return None
        if d.touched or d.lease.owner()!=d.owner:
            raise SafetyError('rollback_fenced_by_unverified_model_or_lease')
        if PROFILE.read_bytes()!=b'{"context_tokens":16384}\n':raise SafetyError('foreign_context_profile')
        self.monitor.enforce=False
        r=self.runtime(16384);d.runtime=r;self.monitor.bind(r,enforce=False)
        self.stop(r)
        PROFILE.unlink();sync_dir(PROFILE.parent)
        restored=self.start(1024);d.runtime=restored;self.monitor.bind(restored,enforce=False)
        self.idle(restored)
        d.lease.clear(d.owner)
        d.ledger.control('rollback-verified',runtime=restored.identity(),profile_exists=False,lease_bytes=0)
        self.changed=False
        return restored.identity()


class ServiceSpawner:
    """Fixed-command lifecycle owner created before driver AS is narrowed.

    It belongs to the monitored service tree. It cannot generate or run arbitrary
    binaries, and retains the original service AS inheritance for both starts.
    """
    def __init__(self,fixture=False):
        self.process=subprocess.Popen([sys.executable,'-m','experiments_ext.masbench_t3rv2_live_probe',
            '--fixture-spawner' if fixture else '--service-spawner',str(os.getpid())],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            start_new_session=True)
        self.stamp=old.proc_stamp(self.process.pid);self.calls=0
        self.selector=selectors.DefaultSelector();self.selector.register(self.process.stdout,selectors.EVENT_READ)

    def request(self,value):
        if self.calls>=2:raise SafetyError('service_spawn_count')
        self.calls+=1
        body=canonical(value)+b'\n'
        if len(body)>65536:raise SafetyError('service_spawn_IPC_cap')
        self.process.stdin.write(body);self.process.stdin.flush()
        if not self.selector.select(5):raise SafetyError('service_spawn_reply_timeout')
        line=self.process.stdout.readline(65537)
        if not line.endswith(b'\n'):raise SafetyError('service_spawn_reply_cap')
        result=json.loads(line)
        if result.get('error'):raise SafetyError('service_spawn_'+result['error'])
        return result

    def close(self):
        self.process.stdin.close()
        try:self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid,signal.SIGKILL);self.process.wait(timeout=2)
        self.selector.close();self.process.stdout.close()


def service_spawner(parent,fixture=False):
    old.stop_with_parent(parent)
    inherited=resource.getrlimit(resource.RLIMIT_AS)
    count=0
    for line in sys.stdin.buffer:
        try:
            if len(line)>65536 or count>=2:raise SafetyError('fixed_spawn_budget_or_IPC')
            value=json.loads(line);count+=1
            if fixture:
                if value!={'fixture':'report-inherited-limit'}:raise SafetyError('fixture_command')
                child=subprocess.check_output([sys.executable,'-c',
                    'import resource,json;print(json.dumps(list(resource.getrlimit(resource.RLIMIT_AS))))'])
                result=dict(service_AS=json.loads(child),fixture=True)
            else:
                a=v2.require_approval()
                context=value['context'];log=old.reject_links(value['log'])
                expected=v2.HDD/a['run_id']/('service-'+str(context)+'.log')
                if (context!=(16384 if count==1 else 1024) or log!=expected
                        or set(value)!={'context','env','log'}):raise SafetyError('fixed_service_spawn_spec')
                env=value['env']
                required={'OLLAMA_CONTEXT_LENGTH':str(context),'OLLAMA_HOST':'127.0.0.1:11434',
                          'OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1',
                          'OLLAMA_MODELS':str(ROOT.parents[1]/'models/ollama-gosc')}
                if any(env.get(k)!=v for k,v in required.items()):raise SafetyError('fixed_service_environment')
                exe=ROOT/'.local/ollama/runtime/0.11.11/bin/ollama'
                if v2.file_sha(exe)!=v2.BINARY_SHA:raise SafetyError('service_binary_drift')
                def file_limit():resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024**2,8*1024**2))
                with log.open('xb') as stream:
                    p=subprocess.Popen([str(exe),'serve'],env=env,stdin=subprocess.DEVNULL,
                        stdout=stream,stderr=stream,start_new_session=True,preexec_fn=file_limit)
                result=dict(pid=p.pid,stamp=old.proc_stamp(p.pid),service_AS=list(inherited))
            print(json.dumps(result),flush=True)
        except BaseException as exc:
            print(json.dumps({'error':type(exc).__name__}),flush=True);return


def main():
    require_hpc()
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    approval=v2.require_approval();run=Path(os.environ['GOSC_RUN_DIR']);out=Path(os.environ['GOSC_OUTPUT_DIR'])
    for p in run.parent.glob('*/status.json'):
        if p.parent!=run and json.loads(p.read_bytes())['status'] in ('running','planned'):
            raise SafetyError('another_registered_run_active')
    q=quota();storage_gate(q)
    parent=old.reject_links(v2.HDD)
    parent.mkdir(mode=0o700,exist_ok=True)
    if parent.stat().st_uid!=os.getuid() or parent.stat().st_dev==run.stat().st_dev:
        raise SafetyError('HDD_identity_or_filesystem')
    evidence=parent/run.name;evidence.mkdir(mode=0o700,exist_ok=False)
    plan=json.loads(v2.PLAN.read_bytes());cases=json.loads((ROOT/plan['input_assets']).read_bytes())['cases']
    identity=dict(schema='T3-R-v2-independent-live-v1',approval_sha256=v2.file_sha(v2.AUTH),
                  plan_sha256=v2.file_sha(v2.PLAN),system_template_sha256=v2.TEMPLATE_SHA)
    budget=v2.LiveBudget(evidence/'budget',identity,[r['id'] for r in cases])
    lease=old.ServiceLease(LEASE);owner=canonical(dict(v2_run=run.name,binding=budget.binding))
    if lease.owner():raise SafetyError('preexisting_recovery_marker')
    lease.mark(owner)
    monitor=Monitor(budget)
    # Service tree needs its original AS inheritance; never let it inherit the
    # 2GiB driver/helper limit. The owner is itself monitored with that tree.
    spawner=ServiceSpawner()
    monitor.service_tree_root=spawner.process.pid
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    original_pid=json.loads(STATE.read_bytes())['pid']
    runtime=old.Runtime(str(ROOT),v2.HELPER,original_pid,old.proc_stamp(original_pid),v2.BINARY_SHA,1024)
    driver=v2.LiveDriver(evidence,runtime,budget,approval,lease,owner,monitor)
    def protect_space():
        qnow=quota()
        for volume,minimum in [('ssd',32*1024**2),('hdd',128*1024**2)]:
            value=qnow['volumes'][volume].get('remaining_to_hard_limit_bytes')
            if type(value) is not int or value<minimum:raise SafetyError('write_protection_'+volume)
    driver.storage_check=protect_space
    deployment=Deployment(driver,monitor,evidence,spawner)
    results=[];error=None;restored=None
    def timeout(*unused):raise TimeoutError('1460s execution phase; 540s tail remains')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(1460)
    try:
        # Full immutable weight hash is bounded and occurs before service change.
        monitor.bind(runtime,enforce=False)
        weight=ROOT.parents[1]/'models/ollama-gosc/blobs'/old.MODEL_BLOB
        started=time.monotonic();h=__import__('hashlib').sha256()
        with weight.open('rb') as f:
            while True:
                b=f.read(4*1024**2)
                if not b:break
                h.update(b);monitor()
                if time.monotonic()-started>120:raise SafetyError('weight_SHA_deadline')
        if h.hexdigest()!=old.MODEL_BLOB.removeprefix('sha256-'):raise SafetyError('full_weight_SHA_mismatch')
        budget.control('weight-SHA-verified',sha256=h.hexdigest(),bytes=weight.stat().st_size)
        deployment.enter()
        for case in cases:
            driver.begin(case['id'])
            try:
                raw,audit=driver.generate(case['messages'],case['id'],0)
                results.append(dict(id=case['id'],raw=raw,parsed=parse_output(raw,'Alice','exchange'),
                                    usage=audit['usage'],request_sha256=audit['request_sha256']))
                driver.end(case['id'])
            except BaseException as exc:
                monitor.enforce=False
                try:driver.abort(case['id'],type(exc).__name__+':'+str(exc))
                finally:raise
    except BaseException as exc:
        error=type(exc).__name__+':'+str(exc)
        budget.fence(error)
    finally:
        monitor.enforce=False
        try:restored=deployment.rollback()
        except BaseException as exc:
            error=(error+'; ' if error else '')+'rollback:'+type(exc).__name__+':'+str(exc)
            budget.control('rollback-failed',error=error)
        summary=dict(passed=error is None and len(results)==2 and restored is not None,
            run_id=run.name,scope=v2.SCOPE,error=error,results=results,restored=restored,
            http=budget.state['http'],operations=budget.state['operations'],
            requests=budget.state['requests'],episodes=budget.state['episodes'],
            cleanup=budget.state['cleanup'],monitor=dict(samples=monitor.samples,peaks=monitor.peaks,
                max_active_sample_start_gap_seconds=monitor.max_start_gap,hard_isolation=False),
            quota_before=q,elapsed_seconds=time.monotonic()-budget.state['started_mono'],
            identity=identity,evidence_root=str(evidence),task_generations=0)
        write_json(evidence/'summary.json',summary)
        files=[]
        for p in sorted(evidence.rglob('*')):
            if p.is_symlink():raise SafetyError('evidence_symlink')
            if p.is_file():files.append(dict(path=p.relative_to(evidence).as_posix(),bytes=p.stat().st_size,sha256=v2.file_sha(p)))
        if sum(r['bytes'] for r in files)>128*1024**2:raise SafetyError('HDD_total_cap')
        write_json(out/'hdd_inventory.json',dict(root=str(evidence),files=files,bytes=sum(r['bytes'] for r in files)))
        write_json(out/'summary.json',summary)
        spawner.close();lease.close();budget.close()
        signal.alarm(0)
    print(json.dumps(dict(passed=summary['passed'],generations=len(summary['requests']),error=error)))
    if not summary['passed']:raise SystemExit(1)


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1] in ('--service-spawner','--fixture-spawner'):
        service_spawner(int(sys.argv[2]),sys.argv[1]=='--fixture-spawner')
    else:main()
