"""Task lifecycle wiring; not executable without new approved task authority."""
import json,os,sys,subprocess,resource,selectors,signal,time,hashlib
from datetime import datetime
from experiments_ext.masbench_t3rv2t_admission_paths import LIVE_ID
from experiments_ext.masbench_t3rv2t_admission import site
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from scripts.hpc_runs import require_hpc,write_json
from extensions.masbench_reasoning import fair_final_v2_task as v2
from extensions.masbench_reasoning import live_driver as old
from extensions.masbench_reasoning.execution_safety import SafetyError,canonical,digest
from extensions.masbench_reasoning.fixture_driver import _jsonable
from extensions.masbench_reasoning.fair_final_v2_task_campaign import run_campaign,preflight_initial_inputs
from experiments_ext.masbench_t3rv2_live_probe import Monitor,Deployment,ServiceSpawner,quota,storage_gate

class TaskSpawner(ServiceSpawner):
    def __init__(self):
        self.process=subprocess.Popen([sys.executable,'-m','experiments_ext.masbench_t3rv2t_task','--task-spawner',str(os.getpid())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
        self.stamp=old.proc_stamp(self.process.pid);self.calls=0
        self.selector=selectors.DefaultSelector();self.selector.register(self.process.stdout,selectors.EVENT_READ)
def task_service_spawner(parent,fixture=False):
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
    approval=v2.require_approval() # approved:false template stops BEFORE data or service access
    run=Path(os.environ['GOSC_RUN_DIR']);out=Path(os.environ['GOSC_OUTPUT_DIR'])
    manifest=json.loads((run/'manifest.json').read_bytes())
    if run.name != LIVE_ID or manifest['git_commit'] != approval['git_commit']:
        raise SafetyError('frozen_live_run_identity')
    offline=old.reject_links(ROOT/approval['site_receipt'])
    if ROOT not in offline.parents or v2.file_sha(offline)!=approval['site_receipt_sha256']:
        raise SafetyError('site_receipt_identity')
    admission=json.loads(offline.read_bytes())
    if (not admission['passed'] or admission['model_calls']!=0 or admission['helper_calls']!=8
            or any(admission[k]!=approval[k] for k in ('plan_sha256','view_bundle_path','view_bundle_sha256','baseline_pid','baseline_stamp'))):
        raise SafetyError('site_receipt_binding')
    runtime, _, _, _ = site()
    if (runtime.service_pid,runtime.service_stamp)!=(approval['baseline_pid'],approval['baseline_stamp']):
        raise SafetyError('approved_baseline_PID_stamp_drift')
    registered=datetime.fromisoformat(json.loads((run/'status.json').read_bytes())['started_at']).timestamp()
    seconds=int(17360-(time.time()-registered))
    if not 0<seconds<=17360:raise SafetyError('registered_start_clock')
    plan=json.loads(v2.PLAN.read_bytes())['episodes']
    views=v2.load_private_bundle(approval['view_bundle_path'],approval['view_bundle_sha256'],plan)
    history=Path('/hdd/u202520081000097/gosc-t3rv2-live/hpc-t3rv2i-live-probe-20261126/budget/ledger.jsonl')
    if v2.probe.file_sha(history)!=approval['parent_probe_ledger_sha256']:raise SafetyError('historical_probe_changed')
    root=old.reject_links(v2.HDD/run.name);root.mkdir(parents=True,mode=0o700,exist_ok=False)
    authorization=v2.AUTH.read_bytes()
    if json.loads(authorization)!=approval:raise SafetyError('authorization_changed_before_launch')
    (root/'authorization.json').write_bytes(authorization)
    ledger=v2.TaskLedger(root/'budget',plan,fixture=False,identity=approval,artifact_bytes=999*1024**2)
    lease=old.ServiceLease(ROOT/'.local/t1-service.lock')
    owner=canonical(dict(task_run=run.name,binding=ledger.binding))
    if lease.owner():raise SafetyError('service_recovery_marker_exists')
    lease.mark(owner)
    monitor=Monitor(ledger);spawner=TaskSpawner();monitor.service_tree_root=spawner.process.pid
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    driver=v2.TaskDriver(root,runtime,ledger,approval,lease,owner,monitor)
    def space():
        current=quota()
        if current['volumes']['ssd']['remaining_to_hard_limit_bytes']<32*1024**2 or current['volumes']['hdd']['remaining_to_hard_limit_bytes']<1024**3:raise SafetyError('storage_reserve_stop')
    driver.storage_check=space
    deployment=Deployment(driver,monitor,root,spawner)
    results=[];error=None;restored=None
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(TimeoutError('17360s execution cap; 1000s closeout tail reserved')))
    signal.alarm(seconds)
    try:
        weight=ROOT.parents[1]/'models/ollama-gosc/blobs'/old.MODEL_BLOB
        start=time.monotonic();h=hashlib.sha256()
        with weight.open('rb') as f:
            while True:
                b=f.read(4*1024**2)
                if not b:break
                h.update(b)
                if time.monotonic()-start>120:raise SafetyError('weight_SHA120')
        if h.hexdigest()!=old.MODEL_BLOB.removeprefix('sha256-'):raise SafetyError('weight_SHA')
        deployment.enter()
        offline_counts={row['request_sha256']: row['tokens'] for row in admission['counts']}
        def counter(messages):
            ledger.operation('precount')
            models=old.runtime_files(driver.runtime)
            data=dict(model_path=str(models/'blobs'/old.MODEL_BLOB),template_path=str(models/'blobs'/('sha256-'+old.TEMPLATE)),template_sha256=old.TEMPLATE,requests=[dict(messages=messages)],texts=[])
            reply=driver.rpc.call(dict(kind='counter',runtime=driver.runtime.identity(),input=data),20)
            if reply.get('input_sha256')!=hashlib.sha256(canonical(data)).hexdigest():raise SafetyError('precount_input_SHA')
            row=v2.verify_count(messages,reply)
            request_sha=digest(messages)
            if offline_counts.get(request_sha)!=row['token_count']:raise SafetyError('offline_initial_count_drift')
            return dict(request_sha256=request_sha,tokens=row['token_count'])
        preflight_initial_inputs(plan,views,counter,lambda row:driver.artifact('initial/'+row['family']+'/'+row['role']+'.json',canonical(row)))
        def artifact(key,result):driver.artifact('episodes/'+key+'.json',canonical(_jsonable(result)))
        results=run_campaign(plan,views,lambda row:driver,artifact)
    except BaseException as exc:
        error=type(exc).__name__+':'+str(exc);ledger.fence(error)
    finally:
        monitor.enforce=False
        try:restored=deployment.rollback()
        except BaseException as exc:error=(error or '')+' rollback:'+str(exc)
        complete=v2.engineering_complete(plan,results,ledger,require_real=True)
        report=dict(completed=complete,execution_and_rollback_passed=complete['passed'] and not error and bool(restored),episode_ids=[r['id'] for r in results],error=error,restored=restored,http=ledger.state['http'],operations=ledger.state['operations'],history_link=approval['parent_probe_ledger_sha256'],task_count=len(ledger.state['requests']),synthetic_generations=0,monitor=dict(peaks=monitor.peaks,samples=monitor.samples,max_active_gap=monitor.max_start_gap))
        write_json(out/'task_summary.json',report)
        spawner.close();lease.close();ledger.close();signal.alarm(0)
        files=[]
        for p in sorted(root.rglob('*')):
            if p.is_symlink():raise SafetyError('HDD_evidence_symlink')
            if p.is_file():files.append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=v2.file_sha(p)))
        if sum(r['bytes'] for r in files)>1024**3:raise SafetyError('HDD_one_GiB_total')
        write_json(out/'hdd_inventory.json',dict(root=str(root),files=files,requires_full_return=True))
    if error or not report['completed']['passed']:raise SystemExit(1)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--task-spawner':task_service_spawner(int(sys.argv[2]))
    else:main()
