"""Bound live adapter. No data loader, cloud fallback or helper rebuild.

The fixture sandbox is deliberately not used for HTTP or vocabulary loading.
The guardian owns the service lease; all owned RPC groups are registered before
stdin is released. Unknown usage remains charged after a verified unload.
"""
from dataclasses import asdict,dataclass
import ctypes,hashlib,json,os,re,selectors,signal,subprocess,sys,time
from pathlib import Path
from .client import ClientConfig,ClientFailure,ContextBinding,ControlledClient,LivePermit,run_controlled
from .execution_safety import Limits,SafetyError,canonical,digest
from .fixture_driver import CampaignLedger,_sandbox,_jsonable
from .wire import ContractTransport

HELPER_SHA='e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5'
MANIFEST='845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'
TEMPLATE='eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175'
SYSTEM='66b9ea09bd5b7099cbb4fc820f31b575c0366fa439b08245566692c6784e281e'
MODEL_BLOB='sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730'
FIXTURE_MODEL = 't1-fixture'
FIXTURE_MANIFEST = '0' * 64
RECHECK_AUTH = 'research/protocols/masbench_t1b_post_storage_authorization.json'
RECHECK_PLAN = 'research/protocols/masbench_t1b_post_storage_plan.json'
RECHECK_BUDGET = 'research/protocols/masbench_t1b_post_storage_budget_2026-11-19.md'
FORMAL_AUTH = 'research/protocols/masbench_t1b_formal_runner_retest_authorization.json'
FORMAL_PLAN = 'research/protocols/masbench_t1b_formal_runner_retest_plan.json'
FORMAL_BUDGET = 'research/protocols/masbench_t1b_formal_runner_retest_budget_2026-11-19.md'
T2_AUTH = 'research/protocols/masbench_t2_live_v3_authorization.json'
T2_PLAN = 'research/protocols/masbench_t2_live_v3_plan.json'
T2_BUDGET = 'research/protocols/masbench_t2_live_v3_budget_2026-11-25.md'
T3_AUTH = 'research/protocols/masbench_t3_execution_authorization_2026-11-25.json'
T3_PLAN = 'research/protocols/masbench_t3_candidate_plan_2026-11-25.json'
T3_BUDGET = 'research/protocols/masbench_t3_budget_proposal_2026-11-25.md'
T3_SCOPE = 'T3 frozen four development families'
T3_CONTROL = {'debug':98,'get':312,'cleanup_get':108,'unload':18}
T3_CONTROL_BYTES = 8 * 1024**2
T3_HDD_BYTES = 1024**3
T3_SERVICE_LOG_BYTES = 16 * 1024**2
T3_DRIVER_BYTES = T3_HDD_BYTES - T3_CONTROL_BYTES - T3_SERVICE_LOG_BYTES - 1024**2
T3_EVIDENCE_ROOT = Path('/hdd/u202520081000097/gosc-t3-runs')
T3_SSD_BYTES = 32 * 1024**2
T3_WALL_SECONDS = 34800
T3_OPERATION_SECONDS = 180
T2_WINDOWS = (1024, 2048, 4096, 8192, 16384, 32768)
MAX_RPC_SECONDS = 60
APPLICATION_FRAME_BYTES = 64 * 1024
APPLICATION_REQUEST_BYTES = 512 * 1024
APPLICATION_RESULT_BYTES = 8 * 1024**2


def application_frames(packet, result_limit):
    raw = canonical(_jsonable(packet))
    if len(raw) + 1 <= APPLICATION_FRAME_BYTES:
        return (raw + b'\n',)
    if packet['kind'] != 'result' or len(raw) > result_limit:
        raise SafetyError('application IPC cap')
    header = {'kind':'large-result','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    return (canonical(header)+b'\n',raw)


def rpc_seconds(spec, formal, generation_seconds=MAX_RPC_SECONDS):
    body=spec.get('body')
    if (formal and spec.get('kind')=='http' and spec.get('method')=='POST' and spec.get('path')=='/api/chat'
            and isinstance(body,dict) and body.get('_debug_render_only') is True):
        return 120
    if formal and spec.get('kind')=='http' and spec.get('method')=='POST' and spec.get('path')=='/v1/chat/completions':
        return generation_seconds
    return MAX_RPC_SECONDS


def reject_links(path):
    p=Path(path).absolute()
    if any(x.is_symlink() for x in [p,*p.parents]):raise SafetyError('symlink in path')
    return p
def require_authorization(path):
    root=Path(__file__).resolve().parents[2]
    if path is None:raise SafetyError('real execution not authorized')
    expected=reject_links(path)
    profiles={
        root/FORMAL_AUTH:(FORMAL_PLAN,FORMAL_BUDGET,'T1-B synthetic only',
                          'research/logs/masbench-t1-driver-2026-11-17/t1_formal_marker_recovery_applied_20261119.json'),
        root/T2_AUTH:(T2_PLAN,T2_BUDGET,'T2 synthetic only',None),
        root/T3_AUTH:(T3_PLAN,T3_BUDGET,T3_SCOPE,None),
    }
    if expected not in profiles or not expected.is_file():raise SafetyError('real execution not authorized')
    plan_path,budget_path,scope,recovery = profiles[expected]
    data=json.loads(expected.read_bytes())
    if data.get('approved') is not True or data.get('scope')!=scope or data.get('exclusive_service') is not True:
        raise SafetyError('approval/exclusive-service absent')
    for k in ['protocol_sha256','registry_sha256','plan_sha256','source_sha256']:
        if not re.fullmatch('[0-9a-f]{64}',str(data.get(k,''))):raise SafetyError('incomplete execution identity')
    if data['source_sha256']!=file_sha(__file__):raise SafetyError('authorized source drift')
    bindings = [('protocol_sha256',budget_path),
                            ('registry_sha256','research/artifacts/native-masbench-20261104/masbench_development_registry.json'),
                            ('plan_sha256',plan_path),('runner_sha256','experiments_ext/masbench_t1b_live.py')]
    if recovery:
        bindings.append(('previous_recovery_receipt_sha256',recovery))
    if scope=='T2 synthetic only':
        bindings.append(('launcher_sha256','experiments_ext/masbench_t2_live.py'))
        bindings.append(('service_source_sha256','scripts/hpc_ollama.py'))
        bindings.append(('recovery_sha256','research/logs/masbench-t2-2026-11-25/zero_dispatch_rollback.json'))
    if scope==T3_SCOPE:
        bindings.extend([
            ('launcher_sha256','experiments_ext/masbench_t3_live.py'),
            ('service_source_sha256','scripts/hpc_ollama.py'),
            ('lifecycle_sha256','experiments_ext/masbench_t2_live.py'),
            ('campaign_ledger_sha256','extensions/masbench_reasoning/fixture_driver.py'),
            ('client_sha256','extensions/masbench_reasoning/client.py'),
        ])
    for field, relative in bindings:
        if data.get(field)!=file_sha(reject_links(root/relative)):raise SafetyError('authorized material drift: '+field)
    run = Path(os.environ.get('GOSC_RUN_DIR','/'))
    if run.parent != root/'research/sync/runs' or run.name != data.get('run_id'):
        raise SafetyError('authorization is bound to one registered run')
    plan=json.loads((root/plan_path).read_bytes())
    context=plan['runtime']['context']
    if scope=='T2 synthetic only' and (context not in T2_WINDOWS or data.get('context')!=context):
        raise SafetyError('T2 context is not bound to the authorized plan')
    if scope=='T1-B synthetic only' and context!=1024:
        raise SafetyError('fixed T1 context changed')
    seconds=plan['caps']['operation'] if scope=='T2 synthetic only' else MAX_RPC_SECONDS
    if scope==T3_SCOPE:
        if context!=16384 or data.get('context')!=context:
            raise SafetyError('fixed T3 context changed')
        seconds=T3_OPERATION_SECONDS
    if type(seconds) is not int or not 1<=seconds<=180:
        raise SafetyError('invalid authorized generation deadline')
    return dict(data,plan_path=plan_path,context=context,generation_seconds=seconds)


def t3_cases():
    instruction = {'role':'system','content':'This is a synthetic service check. Reply only with OK.'}
    return [
        {'id':'synthetic-short','messages':[instruction, {'role':'user','content':'Confirm this sample.'}],
         'max_output':512,'fault':'none'},
        {'id':'synthetic-long','messages':[instruction, {'role':'user',
          'content':'The sample ledger contains a blue parcel.\n'*900+'Confirm this sample.'}],
         'max_output':512,'fault':'none'},
    ]


def t3_plan(candidate):
    return [
        {'id':case['id'],'partition':'synthetic','family':case['id'],'style':'base','condition':'No-A2A'}
        for case in t3_cases()
    ] + [dict(row,partition='task',family=row['family_sha256']) for row in candidate['episodes']]

class ServiceLease:
    def __init__(self,path):
        import fcntl
        self.path=reject_links(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.stream=self.path.open('a+b')
        try:fcntl.flock(self.stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:self.stream.close();raise SafetyError('service lease busy')
    def close(self):self.stream.close()

    def owner(self):
        self.stream.seek(0)
        return self.stream.read(4097)

    def mark(self, owner):
        previous = self.owner()
        if previous not in (b'', owner):
            raise SafetyError('another campaign requires service recovery')
        if not previous:
            self.stream.write(owner)
            self.stream.flush()
            os.fsync(self.stream.fileno())

    def clear(self, owner):
        if self.owner() != owner:
            raise SafetyError('campaign does not own the recovery marker')
        self.stream.truncate(0)
        self.stream.flush()
        os.fsync(self.stream.fileno())
def file_sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def proc_stamp(pid):
    try:return proc_fields(Path('/proc',str(pid)))[19]
    except (FileNotFoundError, ProcessLookupError):return None


def proc_fields(path):
    return (path/'stat').read_text().rsplit(') ',1)[1].split()


def service_identity(runtime):
    return {'pid':runtime.service_pid, 'stamp':runtime.service_stamp}


def runner_epoch(rows, service):
    """Select observations made under the current service lease."""
    claims = [i for i,row in enumerate(rows) if row['event']['kind']=='service-claimed']
    if not claims or rows[claims[-1]]['event']['service'] != service:
        raise SafetyError('service claim missing or changed')
    epoch = [row['event'] for row in rows[claims[-1]+1:]]
    witnesses = set()
    for event in epoch:
        if event['kind'] != 'runner-observed':
            continue
        runner = event['runner']
        if (event['service'] != service or type(runner['pid']) is not int
                or runner['pid'] <= 0 or not re.fullmatch(r'[0-9]+',runner['stamp'])):
            raise SafetyError('invalid runner identity witness')
        witnesses.add((runner['pid'],runner['stamp']))
    return epoch, [{'pid':pid,'stamp':stamp} for pid,stamp in sorted(witnesses)]

def stop_with_parent(parent_pid):
    """Fail closed if the owned process loses its controller during setup."""
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, int(signal.SIGKILL), 0, 0, 0) or os.getppid() != parent_pid:
        os._exit(74)

class ControlJournal:
    """Independent fsync cleanup reserve, outside the main artifact allowance."""
    def __init__(self,path,identity,caps=None,reserve_bytes=128*1024):
        self.path=Path(path);self.caps=caps or {'debug':4,'get':24,'cleanup_get':16,'unload':4}
        if type(reserve_bytes) is not int or not 128*1024<=reserve_bytes<=8*1024**2:
            raise SafetyError('invalid control reserve')
        self.reserve_bytes=reserve_bytes
        init={'kind':'init','identity':identity,'caps':self.caps}
        if reserve_bytes!=128*1024:init['reserve_bytes']=reserve_bytes
        self.rows=[];self.previous='0'*64;self.used={k:0 for k in self.caps}
        reject_links(self.path)
        self.lease=ServiceLease(self.path.with_suffix('.lock'))
        exists=self.path.exists()
        if exists:
            if self.path.stat().st_size>reserve_bytes:raise SafetyError('control reserve exceeded')
            prefix=self.path.read_bytes().rstrip(b'\0')
            for line in prefix.splitlines(keepends=True):
                if not line.endswith(b'\n'):raise SafetyError('partial control record')
                r=json.loads(line);h=r.pop('hash')
                if r['seq']!=len(self.rows) or r['previous']!=self.previous or digest(r)!=h:raise SafetyError('control chain')
                self.rows.append(r);self.previous=h
                if r['event']['kind']=='charge':self.used[r['event']['category']]+=1
            if not self.rows or self.rows[0]['event']!=init:raise SafetyError('control identity changed')
            if any(self.used[k]>self.caps[k] for k in self.caps):raise SafetyError('persisted control over budget')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.stream=self.path.open('r+b' if exists else 'x+b',buffering=0)
        if not exists:
            os.posix_fallocate(self.stream.fileno(),0,reserve_bytes)
            self.stream.truncate(reserve_bytes);os.fsync(self.stream.fileno())
        self.offset=len(prefix) if exists else 0
        self.stream.seek(self.offset)
        if not self.rows:self.append(init)
        self.identity=identity
    def append(self,event):
        r={'seq':len(self.rows),'previous':self.previous,'mono':time.monotonic(),'event':event};h=digest(r)
        b=canonical(dict(r,hash=h))+b'\n'
        if self.offset+len(b)>self.reserve_bytes:raise SafetyError('control reserve exhausted')
        if self.stream.write(b)!=len(b):raise SafetyError('short control write')
        os.fsync(self.stream.fileno());self.offset+=len(b);self.rows.append(r);self.previous=h
    def charge(self,category):
        if category not in self.caps or self.used[category]>=self.caps[category]:raise SafetyError('control budget '+category)
        self.append({'kind':'charge','category':category});self.used[category]+=1
    def close(self):
        if getattr(self,'stream',None):self.stream.close()
        if getattr(self,'lease',None):self.lease.close()
    def __del__(self):
        try:self.close()
        except Exception:pass

class LiveLedger(CampaignLedger):
    """Versioned recovery gate; never erases historical fenced/unknown state."""
    def __init__(self,root,identity,limits,plan=None,t3=False):
        self.last_fault=-1;self.last_barrier=-1;self.recovery_required=False;self.permanent_fence=False
        self.service={'pid':identity['runtime']['service_pid'], 'stamp':identity['runtime']['service_stamp']}
        super().__init__(root,{'schema':'t1-live-v1','binding':identity},
            plan or [{'id':'synthetic','partition':'synthetic'}],limits,
            task_cap=96 if t3 else 0,synthetic_cap=2 if t3 else limits.requests)
        self.recovery_required=any(v=='started' for v in self.state['episodes'].values())
        self.partitions={row['id']:row['partition'] for row in (plan or [{'id':'synthetic','partition':'synthetic'}])}
        self.t3=t3
    def episode(self,episode_id,status):
        if not (self.t3 and status=='completed' and self.state['fenced']):
            return super().episode(episode_id,status)
        self._admit()
        if self.state['episodes'].get(episode_id)!='started' or any(
                r['episode']==episode_id and r['status']!='completed' for r in self.state['requests'].values()):
            raise SafetyError('invalid episode completion after recovery')
        self._append({'kind':'episode','id':episode_id,'status':status})
    def reserve_partition(self,request_id,episode_id,exact_input,max_output,partition):
        if self.partitions.get(episode_id)!=partition:
            raise SafetyError('episode partition mismatch')
        if self.t3:
            cap=6 if partition=='task' else 1
            used=sum(r['episode']==episode_id for r in self.state['requests'].values())
            if used>=cap or max_output!=512 or exact_input+max_output>16384:
                raise SafetyError('T3 per-episode or token cap exceeded')
        super().reserve_partition(request_id,episode_id,exact_input,max_output,partition)
    def _apply(self,event):
        if event['kind']=='barrier':
            self.last_barrier=self.seq
            return
        super()._apply(event)
        if event['kind']=='fence':self.permanent_fence=True
        if event['kind']=='finish' and event.get('uncertain'):self.last_fault=self.seq
    def _admit(self):
        if self.remaining()<=30 or self.permanent_fence:raise SafetyError('dispatch deadline/permanent fence')
        if self.recovery_required or any(r['status']=='inflight' for r in self.state['requests'].values()):raise SafetyError('recovery required')
        if self.state['fenced'] and self.last_barrier<=self.last_fault:raise SafetyError('unresolved service fence')
    def can_reserve(self, exact_input, max_output):
        self._admit()
        if (len(self.state['requests']) >= self.limits.requests or
                self.state['inputs'] + exact_input > self.limits.input_tokens or
                self.state['outputs'] + max_output > self.limits.output_tokens):
            raise SafetyError('request/token budget exhausted')
    def barrier(self,receipt):
        # A bare boolean dictionary is not an observation or recovery proof.
        path=self.root.parent/'control.jsonl'
        reject_links(path);rows=[];previous='0'*64
        for line in path.read_bytes().rstrip(b'\0').splitlines(keepends=True):
            if not line.endswith(b'\n'):raise SafetyError('partial control proof')
            r=json.loads(line);h=r.pop('hash')
            if r['seq']!=len(rows) or r['previous']!=previous or digest(r)!=h:raise SafetyError('control proof chain')
            rows.append(r);previous=h
        if not rows or rows[0]['event'].get('identity')!=self.binding:raise SafetyError('control campaign mismatch')
        index=receipt.get('control_event_seq',-1)
        if type(index) is not int or not 0<=index<len(rows):raise SafetyError('missing control proof')
        r=rows[index];event=r['event']
        if digest(r)!=receipt.get('control_event_hash') or event.get('kind')!='unload-complete':raise SafetyError('control proof mismatch')
        obs=event['observation']
        if obs.get('ledger_tip')!=self.previous or obs.get('ledger_seq')!=self.seq:
            raise SafetyError('stale recovery proof')
        if obs['response'].get('done_reason')!='unload' or obs['response'].get('done') is not True or obs['ps'].get('models')!=[]:
            raise SafetyError('unload proof incomplete')
        epoch, expected = runner_epoch(rows[:index],self.service)
        starts = [e for e in epoch if e['kind']=='unload-start']
        observations = obs['process_observations']
        if (not expected or any(e['kind']=='runner-response-drift' for e in epoch)
                or len(starts)!=1 or starts[0]['old_runners']!=expected
                or any(r not in expected for r in starts[0]['present_before_unload'])
                or obs.get('service')!=self.service or obs.get('remaining_runners')!=[]
                or [{'pid':x['pid'],'stamp':x['stamp']} for x in observations]!=expected):
            raise SafetyError('missing or mismatched pre-cleanup runner evidence')
        if any(x['observed_stamp']==x['stamp'] for x in observations):raise SafetyError('old runner remains')
        self._append({'kind':'barrier','receipt':receipt});self.recovery_required=False

@dataclass(frozen=True)
class Runtime:
    root: str
    helper: str
    service_pid: int
    service_stamp: str
    binary_sha: str
    context: int=1024
    model: str='qwen2.5:7b'
    def identity(self):return asdict(self)

def runtime_files(runtime):
    root=Path(runtime.root);models=root.parents[1]/'models/ollama-gosc'
    if proc_stamp(runtime.service_pid)!=runtime.service_stamp:raise SafetyError('service PID identity drift')
    env=dict(x.split('=',1) for x in Path('/proc',str(runtime.service_pid),'environ').read_bytes().decode().split('\0') if '=' in x)
    if (env.get('OLLAMA_CONTEXT_LENGTH')!=str(runtime.context) or env.get('OLLAMA_NUM_PARALLEL')!='1'
            or env.get('OLLAMA_MODELS')!=str(models) or env.get('OLLAMA_HOST')!='127.0.0.1:11434'):
        raise SafetyError('configured context/parallel/models/endpoint drift')
    exe=Path('/proc',str(runtime.service_pid),'exe').resolve()
    if exe!=root/'.local/ollama/runtime/0.11.11/bin/ollama' or file_sha(exe)!=runtime.binary_sha:raise SafetyError('service binary drift')
    for path,expected in [(runtime.helper,HELPER_SHA),(models/'manifests/registry.ollama.ai/library/qwen2.5/7b',MANIFEST),
                          (models/'blobs'/('sha256-'+TEMPLATE),TEMPLATE),(models/'blobs'/('sha256-'+SYSTEM),SYSTEM)]:
        if file_sha(path)!=expected:raise SafetyError('helper/model/template/system identity drift')
    return models

def stop_owned(pid,stamp,control):
    error=None
    for sig in [signal.SIGTERM,signal.SIGKILL]:
        alive=stamp is not None and proc_stamp(pid)==stamp
        sent=False
        if alive:
            try:os.killpg(pid,sig);sent=True
            except ProcessLookupError:pass
        try:control.append({'kind':'signal','pid':pid,'stamp':stamp,'signal':int(sig),'sent':sent})
        except BaseException as e:error=e
        if sig==signal.SIGTERM:time.sleep(.03)
    if error:raise error

class RPC:
    is_live=True
    def __init__(self,control,deadline,trace_sink,authorization=None):
        self.control,self.deadline,self.trace_sink=control,deadline,trace_sink
        self.authorization=authorization
        self.abort_check=None
        self.on_generation_sent = None
        self.monitor = None
    def call(self,spec,timeout,crash=False):
        if crash:raise SafetyError('broker crash injection forbidden')
        spec=dict(spec)
        seconds=MAX_RPC_SECONDS
        if spec.get('kind')!='fixture':
            seconds=require_authorization(self.authorization)['generation_seconds']
            spec['authorization']=str(self.authorization)
        payload=canonical(spec)
        if len(payload)>1024*1024:raise SafetyError('RPC input size cap')
        deadline=min(self.deadline,time.monotonic()+min(timeout,rpc_seconds(spec,self.authorization is not None,seconds)))
        if deadline<=time.monotonic():raise TimeoutError()
        p=subprocess.Popen([sys.executable,'-m','extensions.masbench_reasoning.live_driver','--rpc',
                            str(os.getpid()),str(deadline)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
        stamp=proc_stamp(p.pid)
        chunks=bytearray();raw=bytearray();result=None;sent=False
        sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
        try:
            self.control.append({'kind':'rpc-spawn','pid':p.pid,'stamp':stamp,'request_sha256':digest(spec),
                                 'deadline_monotonic':deadline})
            os.set_blocking(p.stdin.fileno(),False);sel.register(p.stdin,selectors.EVENT_WRITE);offset=0
            while True:
                if self.monitor:
                    self.monitor()
                if self.abort_check and self.abort_check():raise ClientFailure('application controller exited')
                if time.monotonic()>=deadline:
                    self.control.append({'kind':'rpc-timeout','pid':p.pid,'stamp':stamp,'sent_observed':sent})
                    raise TimeoutError()
                from experiments_ext.masbench_context_build import group_rss
                if group_rss(p.pid)>2*1024**3:raise SafetyError('RPC RSS cap')
                for key,_ in sel.select(min(.02,deadline-time.monotonic())):
                    if key.fileobj is p.stdin:
                        try:offset+=os.write(p.stdin.fileno(),payload[offset:offset+4096])
                        except BlockingIOError:continue
                        if offset==len(payload):sel.unregister(p.stdin);p.stdin.close()
                        continue
                    b=os.read(key.fileobj.fileno(),65536)
                    if not b:
                        if result is None:raise ClientFailure('RPC EOF without complete result')
                        return result
                    chunks.extend(b);raw.extend(b)
                    if len(raw)>1024*1024:raise ClientFailure('RPC size cap')
                    # A bounded child process tree; all RPCs are sequential.
                    from experiments_ext.masbench_context_build import group_rss
                    if group_rss(p.pid)>2*1024**3:raise SafetyError('RPC RSS cap')
                    while b'\n' in chunks:
                        line,_,rest=chunks.partition(b'\n');chunks=bytearray(rest);r=json.loads(line)
                        if r.get('phase')=='sent':
                            sent=True
                            send_time=r.get('mono',time.monotonic())
                            self.control.append({'kind':'fixture-send-marker' if spec['kind']=='fixture' else 'http-sent',
                                'pid':p.pid,'request_sha256':digest(spec),'worker_sent_mono':send_time})
                            if spec.get('path')=='/v1/chat/completions' and self.on_generation_sent:
                                deadline=min(deadline,self.on_generation_sent(send_time))
                        elif r.get('phase')=='result':
                            result=r['value']
                            if spec.get('path')=='/v1/chat/completions':
                                self.control.append({'kind':'generation-result-observed','pid':p.pid})
                        elif r.get('phase')=='error':raise ClientFailure('RPC '+r.get('error','unknown'))
                try:zombie=Path('/proc',str(p.pid),'stat').read_text().split(') ')[1].startswith('Z')
                except FileNotFoundError:zombie=True
                if zombie and not sel.select(0):
                    if result is not None:return result
                    raise ClientFailure('RPC exited without result')
        finally:
            try:stop_owned(p.pid,stamp,self.control)
            finally:
                p.wait(timeout=2);sel.close();p.stdout.close()
                if not p.stdin.closed:p.stdin.close()
            self.trace_sink('rpc',bytes(raw));self.control.append({'kind':'rpc-end','pid':p.pid,'sent':sent,'exit':p.returncode})

def rpc_worker(parent_pid, deadline):
    """Owned worker: fixed local endpoint only, no credentials/cloud/retries."""
    stop_with_parent(parent_pid)
    import http.client
    spec=json.loads(sys.stdin.buffer.read(1024*1024+1))
    def emit(x):print(json.dumps(x),flush=True)
    try:
        if spec.get('kind')=='fixture':
            mode=spec.get('mode','ok')
            if mode=='hang':
                signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)
            elif mode=='hang-sent':
                signal.signal(signal.SIGTERM,signal.SIG_IGN)
                emit({'phase':'sent','fixture':True})
                time.sleep(30)
            elif mode=='oversize':emit({'phase':'result','value':'x'*(1024*1024+1)})
            elif mode=='exit':os._exit(19)
            else:emit({'phase':'result','value':{'fixture':True}})
            return
        approval=require_authorization(spec.get('authorization'))
        if spec['kind']=='counter':
            helper=spec['helper']
            if file_sha(helper)!=HELPER_SHA:raise SafetyError('helper SHA')
            p=subprocess.run([helper],input=canonical(spec['input']),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=20)
            if p.returncode or len(p.stdout)>512*1024:raise SafetyError('helper error/size')
            emit({'phase':'result','value':json.loads(p.stdout)});return
        method,path=spec['method'],spec['path'];body=spec.get('body')
        if method=='GET':
            if path not in ['/api/version','/api/tags','/api/ps']:raise SafetyError('GET path')
        elif method=='POST':
            if path=='/api/chat':
                if not (body.get('_debug_render_only') is True or body.get('messages')==[] and body.get('keep_alive')==0):raise SafetyError('native POST type')
            elif path!='/v1/chat/completions':raise SafetyError('POST path')
        else:raise SafetyError('method')
        # Cold render can load the runner. Follow the guardian's operation cap
        # while its separate after-send watchdog can stop generation earlier.
        cap = rpc_seconds(spec,True,approval['generation_seconds'])
        remaining = min(deadline-time.monotonic(),cap)
        if not 0 < remaining <= cap:
            raise TimeoutError('HTTP dispatch deadline expired')
        c=http.client.HTTPConnection('127.0.0.1',11434,timeout=remaining)
        try:
            c.request(method,path,None if body is None else canonical(body),{'Content-Type':'application/json'})
            emit({'phase':'sent','mono':time.monotonic()})
            r=c.getresponse();raw=r.read(512*1024+1)
            if r.status!=200 or len(raw)>512*1024:raise SafetyError('HTTP status/size')
            emit({'phase':'result','value':json.loads(raw)})
        finally:c.close()
    except BaseException as e:emit({'phase':'error','error':type(e).__name__});raise SystemExit(1)

def runner_identities(runtime, proc=Path('/proc')):
    """Observe the fixed Ollama service's direct children for its pinned model."""
    service = proc/str(runtime.service_pid)
    if proc_fields(service)[19]!=runtime.service_stamp:
        raise SafetyError('service PID identity drift during runner observation')
    exe = (service/'exe').readlink()
    model = str(Path(runtime.root).parents[1]/'models/ollama-gosc/blobs'/MODEL_BLOB).encode()
    runners = []
    for child in proc.iterdir():
        if not child.name.isdigit():
            continue
        try:
            first = proc_fields(child)
            if int(first[1])!=runtime.service_pid or first[0]=='Z':
                continue
            args = (child/'cmdline').read_bytes().split(b'\0')
            child_exe = (child/'exe').readlink()
            last = proc_fields(child)
        except (FileNotFoundError, ProcessLookupError):
            continue
        if last[0]=='Z' or first[1]!=last[1] or first[19]!=last[19]:
            continue
        if child_exe!=exe or args[1:2]!=[b'runner']:
            raise SafetyError('unexpected live process under the project service')
        indices = [i for i,arg in enumerate(args) if arg==b'--model']
        if len(indices)!=1 or args[indices[0]+1:indices[0]+2]!=[model]:
            raise SafetyError('runner model blob does not match the pinned model')
        runners.append({'pid':int(child.name),'stamp':last[19]})
    if proc_fields(service)[19]!=runtime.service_stamp:
        raise SafetyError('service PID changed during runner observation')
    return sorted(runners,key=lambda r:(r['pid'],r['stamp']))

class LiveDriver:
    def __init__(self,root,runtime,limits,transport=None,validator=None,authorization=None,plan=None):
        if transport is not None and getattr(transport,'is_live',True):raise SafetyError('injected transport must be explicitly no-network')
        if transport is not None and runtime.model != FIXTURE_MODEL:
            raise SafetyError('fixture transport requires separate model identity')
        approval=require_authorization(authorization) if transport is None else None
        self.t3=bool(approval and approval['scope']==T3_SCOPE)
        if self.t3:
            candidate=json.loads((Path(runtime.root)/T3_PLAN).read_bytes())
            if plan!=t3_plan(candidate) or len(plan)!=18:
                raise SafetyError('frozen T3 episode order mismatch')
            if (limits.requests,limits.metadata,limits.input_tokens,limits.output_tokens,limits.per_output,
                limits.operation_seconds)!=(98,420,1555456,50176,512,T3_OPERATION_SECONDS):
                raise SafetyError('T3 budget mismatch')
            expected_root=T3_EVIDENCE_ROOT/approval['run_id']/'live'
            if (reject_links(root)!=expected_root or limits.artifact_bytes!=T3_DRIVER_BYTES
                    or not 0<limits.wall_seconds<=T3_WALL_SECONDS):
                raise SafetyError('T3 storage or wall limit mismatch')
        elif plan is not None and any(e.get('partition')!='synthetic' or e.get('style') not in {'base','protocol'} or e.get('condition') not in {'Full','No-A2A'} for e in plan):
            raise SafetyError('unapproved plan must be synthetic only')
        if approval and (validator is not None or runtime.model!='qwen2.5:7b' or runtime.context!=approval['context']):
            raise SafetyError('live runtime profile may not be overridden')
        self.root=reject_links(root);self.root.mkdir(parents=True,exist_ok=True);self.runtime=runtime
        self.model_manifest = MANIFEST if approval else FIXTURE_MANIFEST
        self.service_lease=ServiceLease(Path(runtime.root)/'.local/t1-service.lock')
        self.validate=validator or runtime_files
        identity={'runtime':runtime.identity(),'source_sha256':file_sha(__file__),
                  'authorization_sha256':file_sha(authorization) if approval else 'fixture-only',
                  'scope':approval['scope'] if approval else 'T1-A no-network fixture',
                  'model_manifest': self.model_manifest}
        self.ledger=LiveLedger(self.root/'campaign',identity,limits,plan,t3=self.t3)
        self.lease_owner = canonical({'campaign': str(self.root), 'ledger_binding': self.ledger.binding})
        previous_owner = self.service_lease.owner()
        if previous_owner not in (b'', self.lease_owner):
            raise SafetyError('specific previous campaign must recover before dispatch')
        if previous_owner:
            self.ledger.recovery_required = True
        self.plan=plan;self.current_episode='synthetic'
        self.control=ControlJournal(self.root/'control.jsonl',self.ledger.binding,
            caps=T3_CONTROL if self.t3 else None,reserve_bytes=T3_CONTROL_BYTES if self.t3 else 128*1024)
        self.operation_deadline=0;self.pending=None;self.counted=None;self.rpc_seq=0
        self.authorization=authorization;self.approval=approval
        self.rpc=transport or RPC(self.control,time.monotonic()+max(0,self.ledger.remaining()),self.trace,authorization)
        if transport is not None:
            self.rpc.control=self.control;self.rpc.trace_sink=self.trace
        self.audit=[]
        from types import SimpleNamespace
        self.backend=SimpleNamespace(is_live=getattr(self.rpc,'is_live',True))
        self.service_touched = bool(previous_owner)
        self.application_deadline = float('inf')
        self.dispatch_deadline = float('inf')
        self.prepare_seconds = 150 if approval else None
        self.cleanup_deadline = float('inf')
        self.active_controller = None
        self.resource_monitor = None
        self.armed_case = None
        self.attested_runner = None
        self.task_packet = None
        if not plan and self.ledger.state['episodes']['synthetic']=='unstarted':self.ledger.episode('synthetic','started')
    def trace(self,kind,data):
        self.check_storage()
        self.rpc_seq+=1
        ext='jsonl' if kind.startswith('rpc') else 'json'
        self.ledger.put_artifact(f'{self.ledger.seq:06d}-{self.rpc_seq}-{kind}.{ext}',data)
    def emit(self,kind,value):self.trace(kind,canonical(value))
    def check_storage(self):
        self.ledger.check_storage()
        allowed={'control.jsonl','control.lock'}
        size=0
        for p in self.root.rglob('*'):
            if p.is_symlink():raise SafetyError('symlink artifact')
            if p.is_file():
                rel=p.relative_to(self.root).as_posix()
                if not rel.startswith('campaign/') and rel not in allowed:raise SafetyError('unregistered outer artifact')
                size+=p.stat().st_size
        if size>self.ledger.public_limits.artifact_bytes+self.control.reserve_bytes:raise SafetyError('physical campaign+control cap')
    def http(self,path,body=None,category='get',cleanup=False):
        if not cleanup:
            self.ledger._admit()
            self.check_storage()
            if time.monotonic() >= self.dispatch_deadline:raise SafetyError('new dispatch deadline')
        if category == 'debug':
            if not self.service_touched:
                self.validate(self.runtime)
                initial = self.http('/api/ps')
                if initial.get('models') != []:
                    raise SafetyError('service must be empty before campaign model load')
                self.service_lease.mark(self.lease_owner)
                self.service_touched = True
                self.control.append({'kind':'service-claimed','service':service_identity(self.runtime)})
        self.control.charge(category)
        timeout=(min(30,self.ledger.remaining(),self.cleanup_deadline-time.monotonic())
                 if cleanup else self.operation_deadline-time.monotonic())
        if timeout<=0:raise TimeoutError()
        rpc=self.rpc
        if cleanup and getattr(self.rpc,'is_live',True):
            rpc=RPC(self.control,time.monotonic()+timeout,lambda k,b:self.control.append({'kind':'cleanup-rpc','data':json.loads(b.splitlines()[-1]) if b else None}),self.authorization)
            if self.resource_monitor:
                rpc.monitor=lambda:self.resource_monitor(cleanup=True)
        return rpc.call({'kind':'http','method':'GET' if body is None else 'POST','path':path,'body':body},timeout)
    def recover(self):
        self.cleanup_deadline = time.monotonic()+40 if self.prepare_seconds else float('inf')
        self.validate(self.runtime)  # Never unload a drifted or unrelated service.
        if self.service_lease.stream.closed or self.service_lease.owner()!=self.lease_owner:
            raise SafetyError('campaign does not own the service recovery lease')
        self.ledger.recovery_required = True
        service = service_identity(self.runtime)
        epoch, old = runner_epoch(self.control.rows,service)
        if any(e['kind']=='unload-start' for e in epoch):
            raise SafetyError('cleanup already attempted for this service lease')
        # Surviving RPC groups must die before calling the external unload API.
        for r in self.control.rows[:]:
            e=r['event']
            if e['kind'] in {'rpc-spawn','application-spawn'} and e['stamp'] is not None and proc_stamp(e['pid'])==e['stamp']:
                stop_owned(e['pid'],e['stamp'],self.control)
                if e['kind']=='application-spawn':
                    try:os.waitpid(e['pid'],os.WNOHANG)
                    except ChildProcessError:pass
                if proc_stamp(e['pid'])==e['stamp']:
                    raise SafetyError('owned worker exit not verified')
        initial=self.http('/api/ps',category='cleanup_get',cleanup=True)
        if not isinstance(initial.get('models'),list) or any(
            x.get('name')!=self.runtime.model or x.get('digest')!=self.model_manifest for x in initial['models']):
            raise SafetyError('foreign or unknown resident model; do not unload')
        for rid,r in self.ledger.state['requests'].items():
            if r['status']=='inflight':self.ledger.finish_request(rid,'interrupted',None,True)
        current = runner_identities(self.runtime)
        unbound = [runner for runner in current if runner not in old]
        drift = [event for event in epoch if event['kind']=='runner-response-drift']
        for event in drift:
            for runner in event['present_after_response']:
                if runner not in old and runner not in unbound:
                    unbound.append(runner)
        self.control.append({'kind':'unload-start','old_runners':old,'present_before_unload':current})
        value=self.http('/api/chat',{'model':self.runtime.model,'messages':[],'keep_alive':0,'stream':False},'unload',True)
        if value.get('done_reason')!='unload' or value.get('done') is not True:raise SafetyError('unload response')
        for _ in range(6):
            ps=self.http('/api/ps',category='cleanup_get',cleanup=True)
            remaining = runner_identities(self.runtime)
            for runner in remaining:
                if runner not in old and runner not in unbound:
                    unbound.append(runner)
            observations = [dict(x,observed_stamp=proc_stamp(x['pid'])) for x in old+unbound]
            if ps.get('models') == [] and not remaining and all(x['observed_stamp']!=x['stamp'] for x in observations):
                self.validate(self.runtime)
                observation={'response':value,'ps':ps,'process_observations':observations,
                             'ledger_tip':self.ledger.previous,'ledger_seq':self.ledger.seq,
                             'service':service,'remaining_runners':remaining}
                if not old or unbound or drift:
                    self.control.append({'kind':'unload-unverified','observation':observation})
                    raise SafetyError('old runner identity missing or changed; keep fenced')
                if self.resource_monitor:
                    try:
                        observation['resources_after_unload']=self.resource_monitor(force=True)
                    except SafetyError as exc:
                        self.control.append({'kind':'unload-unverified','observation':observation,
                                             'resource_error':str(exc)})
                        raise
                self.control.append({'kind':'unload-complete','observation':observation})
                receipt={'control_event_seq':len(self.control.rows)-1,'control_event_hash':self.control.previous}
                self.ledger.barrier(receipt)
                if self.service_lease.owner():
                    self.service_lease.clear(self.lease_owner)
                self.service_touched = False
                try:self.ledger.can_reserve(0,1);permitted=time.monotonic()<self.dispatch_deadline
                except SafetyError:permitted=False
                self.control.append({'kind':'dispatch-permit-evaluated','permitted':permitted,'remaining_seconds':self.ledger.remaining(),
                    'charged_requests':len(self.ledger.state['requests']),'charged_outputs':self.ledger.state['outputs']})
                return receipt
            time.sleep(.1)
        raise SafetyError('unload/exit not verified; keep fenced')
    def attest(self,messages,max_output):
        models=self.validate(self.runtime)
        if self.ledger.recovery_required:self.recover()
        self.ledger._admit()
        data={'model_path':str(models/'blobs'/MODEL_BLOB),
              'template_path':str(models/'blobs'/('sha256-'+TEMPLATE)),'template_sha256':TEMPLATE,
              'requests':[{'messages':messages}],'texts':[]}
        value=self.rpc.call({'kind':'counter','helper':self.runtime.helper,'input':data},self.operation_deadline-time.monotonic())
        row=value['requests'][0];self.emit('full-input-count',{'messages':messages,'row':row})
        if type(row['token_count']) is not int or row['token_count'] < 0:
            raise SafetyError('invalid helper token count')
        if row['token_count']+max_output>self.runtime.context:raise ClientFailure('context_overflow_no_truncation')
        self.ledger.can_reserve(row['token_count'],max_output)
        # Native rendering and the OpenAI adapter must use the same runner defaults.
        debug=self.http('/api/chat',{'model':self.runtime.model,'messages':messages,'stream':False,
            '_debug_render_only':True},'debug')
        ps=self.http('/api/ps');version=self.http('/api/version')
        active=[m for m in ps['models'] if m['name']==self.runtime.model]
        ok=(debug.get('_debug_info',{}).get('rendered_template')==row['rendered'] and len(active)==1 and
            active[0].get('digest')==self.model_manifest and active[0].get('context_length')==self.runtime.context and version.get('version')=='0.11.11')
        evidence={'debug':debug,'ps':ps,'version':version,'input_sha':digest(messages),'runtime':self.runtime.identity(),
                  'scope':'live-per-request' if getattr(self.rpc,'is_live',True) else 'fixture-only-not-qwen'}
        self.emit('binding-evidence',evidence)
        if len(active)==1 and active[0].get('digest')==self.model_manifest:
            runners = runner_identities(self.runtime)
            if len(runners)!=1:
                raise SafetyError('one bound runner is required before generation')
            self.attested_runner = runners[0]
            self.control.append({'kind':'runner-observed','service':service_identity(self.runtime),
                                 'runner':self.attested_runner,'context_evidence_sha256':digest(evidence)})
        if not ok:raise SafetyError('runtime binding/complete rendering not verified')
        self.counted=(messages,row['token_count'])
        tokenizer = 'ollama01111-vocabonly-full-render' if self.backend.is_live else 't1-fixture-counter'
        return ContextBinding(self.model_manifest,self.runtime.context,tokenizer,digest(evidence),ok)
    def generate(self,messages,max_output=None,network_timeout=None,crash=False):
        case = self.armed_case if self.approval else None
        partition = self.ledger.partitions.get(self.current_episode)
        if self.approval:
            if self.t3 and partition=='task':
                if (case is not None or self.active_controller is None or self.task_packet is not messages
                        or self.ledger.state['episodes'][self.current_episode]!='started'):
                    raise SafetyError('task request is outside the guarded application')
                self.ledger._admit()
                self.task_packet=None
                cap=512
            else:
                path=Path(__file__).resolve().parents[2]/self.approval['plan_path']
                frozen_cases=t3_cases() if self.t3 else json.loads(path.read_bytes())['cases']
                started=[r['event']['id'] for r in self.control.rows if r['event']['kind']=='case-start']
                if (case not in frozen_cases or case['messages']!=messages or not started or started[-1]!=case['id']
                        or started!=[x['id'] for x in frozen_cases[:len(started)]]
                        or self.t3 and self.current_episode!=case['id']):
                    raise SafetyError('generation is outside the frozen synthetic case')
                cap=case['max_output']
            if max_output is not None and max_output!=cap:raise SafetyError('output cap drift')
            max_output=cap
            authorized_timeout=self.approval['generation_seconds']
            self.armed_case=None
        else:
            authorized_timeout=MAX_RPC_SECONDS
            if max_output is None:max_output=min(32,self.ledger.limits.per_output)
        network_timeout=authorized_timeout if network_timeout is None else min(network_timeout,authorized_timeout)
        if (not isinstance(messages,list) or not messages or any(not isinstance(m,dict) or set(m)!={'role','content'} or
            m['role'] not in ({'system'} if i==0 else {'user','assistant'}) or not isinstance(m['content'],str) for i,m in enumerate(messages))):
            raise ClientFailure('request_schema')
        if type(max_output) is not int or max_output<=0 or max_output>self.ledger.limits.per_output:raise SafetyError('output cap')
        phase_start=time.monotonic()
        reserve=40 if self.prepare_seconds else 30
        self.operation_deadline=min(self.application_deadline,self.dispatch_deadline,
            phase_start+min(self.prepare_seconds or self.ledger.limits.operation_seconds,self.ledger.remaining()-reserve))
        if self.prepare_seconds:
            self.control.append({'kind':'phase-clock','phase':'prepare','start_mono':phase_start,
                                 'deadline_mono':self.operation_deadline})
        self.pending=None
        self.attested_runner=None
        driver=self
        class Backend:
            is_live=getattr(driver.rpc,'is_live',True)
            def identity(self,timeout):
                driver.validate(driver.runtime)
                ps=driver.http('/api/ps');active=[m for m in ps['models'] if m['name']==driver.runtime.model]
                if len(active)!=1 or active[0].get('context_length')!=driver.runtime.context:raise SafetyError('runtime changed before dispatch')
                return {'model':driver.runtime.model,'manifest_sha256':active[0]['digest']}
            def create(self,payload,timeout):
                if time.monotonic() >= driver.dispatch_deadline:
                    raise SafetyError('new dispatch deadline')
                if not driver.attested_runner or runner_identities(driver.runtime)!=[driver.attested_runner]:
                    raise SafetyError('observed runner changed before dispatch')
                request_id=partition+'/'+str(len(driver.ledger.state['requests']))
                driver.control.append({'kind':'runner-dispatch-bound','request_id':request_id,
                                       'runner':driver.attested_runner,'service':service_identity(driver.runtime),
                                       'payload_sha256':digest(payload)})
                driver.ledger.reserve_partition(request_id,driver.current_episode,driver.counted[1],max_output,partition)
                driver.pending=request_id
                proof={'request_id':request_id,'payload':payload}
                if driver.t3:proof['episode_id']=driver.current_episode
                driver.emit('provider-request',proof)
                response = driver.rpc.call({'kind':'http','method':'POST','path':'/v1/chat/completions','body':payload},
                    min(timeout,network_timeout,driver.operation_deadline-time.monotonic()),crash)
                try:
                    after_response = runner_identities(driver.runtime)
                except (OSError, SafetyError) as exc:
                    driver.control.append({'kind':'runner-response-drift','request_id':request_id,
                                           'runner':driver.attested_runner,'present_after_response':[],
                                           'service':service_identity(driver.runtime),'observation_error':str(exc)})
                    raise
                matched = after_response == [driver.attested_runner]
                driver.control.append({'kind':'runner-response-bound' if matched else 'runner-response-drift',
                                       'request_id':request_id,'runner':driver.attested_runner,
                                       'present_after_response':after_response,'service':service_identity(driver.runtime)})
                if not matched:
                    raise SafetyError('runner changed or vanished during generation')
                return response
        success=False;inner=None;failure=None
        if case and case['fault']!='none':
            def after_send(sent):
                if case['fault']=='timeout':
                    watchdog=sent+case['watchdog_after_send_seconds']
                    driver.control.append({'kind':'fault-trigger-armed','id':case['id'],'fault':case['fault'],
                                           'sent_mono':sent,'watchdog_deadline_mono':watchdog})
                    return watchdog
                if case['fault']=='interrupt':
                    driver.control.append({'kind':'fault-trigger-armed','id':case['id'],'fault':case['fault'],'sent_mono':sent})
                    pid,stamp=driver.active_controller or (None,None)
                    if stamp is None or proc_stamp(pid)!=stamp:raise SafetyError('controller identity missing at fault trigger')
                    os.kill(pid,signal.SIGKILL)
                    driver.control.append({'kind':'controller-signal','pid':pid,'stamp':stamp,'signal':int(signal.SIGKILL)})
                    end=time.monotonic()+.25
                    while time.monotonic()<end:
                        waited,status=os.waitpid(pid,os.WNOHANG)
                        if waited:
                            driver.control.append({'kind':'controller-exit','pid':pid,'status':status})
                            return float('inf')
                        time.sleep(.005)
                    return float('inf')
                raise SafetyError('unknown frozen fault')
            self.rpc.on_generation_sent=after_send
        try:
            binding=self.attest(messages,max_output)
            if self.prepare_seconds:
                phase_start=time.monotonic()
                if phase_start>=self.operation_deadline:
                    raise TimeoutError('preparation deadline')
                self.operation_deadline=min(self.application_deadline,
                    phase_start+min(self.ledger.limits.operation_seconds,self.ledger.remaining()-reserve))
                self.control.append({'kind':'phase-clock','phase':'generate','start_mono':phase_start,
                                     'deadline_mono':self.operation_deadline})
            def counter(request):
                if request!=self.counted[0]:raise SafetyError('messages changed after exact count')
                return self.counted[1]
            permit=(LivePermit(self.approval['protocol_sha256'],self.approval['registry_sha256'])
                    if self.approval else None)
            inner=ControlledClient(ClientConfig(self.runtime.model,self.model_manifest,self.runtime.context,max_output_tokens=max_output,
                timeout_seconds=max(.001,self.operation_deadline-time.monotonic()),wall_seconds=max(.001,self.ledger.remaining()-30)),
                Backend(),counter,binding,permit=permit,audit_sink=lambda r:self.emit('client',r))
            result=inner.generate(messages)
            if inner.audit[-1].get('usage') is None:
                self.control.append({'kind':'driver-validation-failure','reason':'usage_missing'})
                raise ClientFailure('usage_missing')
            success=True;return result
        except BaseException as exc:
            failure=exc.reason if isinstance(exc,ClientFailure) else type(exc).__name__
            raise
        finally:
            if case:self.rpc.on_generation_sent=None
            if inner is not None:self.audit.extend(inner.audit)
            try:
                if self.pending:
                    row=inner.audit[-1];u=row.get('usage')
                    usage={k:u[k] for k in ['prompt_tokens','completion_tokens']} if success and u else None
                    if self.t3 and not success and isinstance(row.get('response'),dict):
                        reported=row['response'].get('usage')
                        if isinstance(reported,dict):
                            p,c,total=(reported.get(k) for k in ('prompt_tokens','completion_tokens','total_tokens'))
                            if (type(p) is int and type(c) is int and type(total) is int
                                    and p==self.counted[1] and 0<=c<=max_output and total==p+c):
                                usage={'prompt_tokens':p,'completion_tokens':c}
                    outcome = 'completed' if success else {'timeout':'timeout','application controller exited':'interrupted'}.get(failure,'failed')
                    self.ledger.finish_request(self.pending,outcome,usage,not success)
                if not success:
                    self.control.append({'kind':'client-failure','request_id':self.pending,'error':failure})
            finally:
                # The task controller must receive its terminal failure and emit
                # its partial wire/result record before the episode-level unload.
                if (not success and self.service_touched
                        and not (self.t3 and partition=='task' and self.active_controller is not None)):
                    self.recover()
    def run_episode(self,episode_id,agents,max_turns=2,fixture_fault=None):
        if not self.plan:raise SafetyError('application plan required')
        row=next((e for e in self.plan if e['id']==episode_id),None)
        if row is None or type(max_turns) is not int or not 1<=max_turns<=6:raise SafetyError('unplanned episode/turns')
        if any(a.memory or a.facts or a.received for a in agents):raise SafetyError('fresh agent state required')
        if fixture_fault and self.backend.is_live:raise SafetyError('fixture fault injection not a live execution mode')
        proof={'id':episode_id,'family':row['family'],'style':row['style'],
               'views':digest([asdict(a.view) for a in agents]),'initial_requests':digest([a.request() for a in agents])}
        if self.t3:
            from .registry import digest as registry_digest
            expected=next((key for key,value in self.ledger.state['episodes'].items() if value=='unstarted'),None)
            if (row['partition']!='task' or expected!=episode_id or max_turns!=6
                    or proof['views']!=row['private_view_sha256']
                    or [registry_digest(a.request()) for a in agents]!=row['initial_request_sha256']):
                raise SafetyError('T3 episode/view/initial prompt is outside the frozen plan')
        for record in self.ledger.artifacts.values():
            if record['path'].endswith('-pair-binding.json'):
                old=json.loads((self.ledger.root/'artifacts'/record['path']).read_bytes())
                if old['family']==proof['family'] and old['style']==proof['style'] and any(old[k]!=proof[k] for k in ['views','initial_requests']):
                    raise SafetyError('paired private views/prompt changed')
        self.ledger.episode(episode_id,'started');self.current_episode=episode_id
        self.emit('pair-binding',proof)
        try:
            result=self._guard_application(agents,row,max_turns,fixture_fault)
            self.emit('application-result',dict(result,id=episode_id) if self.t3 else result)
            self.ledger.episode(episode_id,'failed' if result['error_flags'] else 'completed')
            return result
        except BaseException:
            if self.ledger.state['episodes'][episode_id]=='started':self.ledger.episode(episode_id,'failed')
            raise
    def _guard_application(self,agents,row,max_turns,fixture_fault):
        # Only the application child gets seccomp. Real HTTP/helper workers do not.
        requests_r,requests_w=os.pipe();answers_r,answers_w=os.pipe()
        reserve=40 if self.prepare_seconds else 30
        case_seconds=(self.ledger.limits.operation_seconds+(self.prepare_seconds or 0))*max_turns
        deadline=time.monotonic()+min(self.ledger.remaining()-reserve,case_seconds)
        parent_pid=os.getpid()
        result_limit=min(APPLICATION_RESULT_BYTES,self.ledger.public_limits.artifact_bytes)
        pid=os.fork()
        if pid==0:
            stop_with_parent(parent_pid)
            os.setsid()
            for p in Path('/proc/self/fd').iterdir():
                try:
                    fd=int(p.name)
                    if fd not in {requests_w,answers_r}:os.close(fd)
                except OSError:pass
            def send(value):
                for block in application_frames(value,result_limit):
                    pending=memoryview(block)
                    while pending:pending=pending[os.write(requests_w,pending):]
            try:
                _sandbox(requests_w)
                if fixture_fault=='exit':os._exit(73)
                if fixture_fault=='hang':
                    signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)
                class Proxy:
                    backend=self.backend
                    audit=[]
                    def generate(proxy,messages):
                        send({'kind':'generate','messages':messages})
                        data=bytearray()
                        while not data.endswith(b'\n'):
                            b=os.read(answers_r,4096)
                            if not b or len(data)+len(b)>65536:raise SafetyError('broker response unavailable/oversize')
                            data.extend(b)
                        answer=json.loads(data)
                        if answer.get('error'):raise ClientFailure(answer['error'])
                        proxy.audit.append(answer['audit']);return answer['text']
                transport=ContractTransport(episode_id=list(self.ledger.state['episodes']).index(row['id'])+1)
                result=run_controlled(agents,Proxy(),transport,row['style'],max_turns=max_turns,
                    admit=lambda sender,body,turn:row['condition']=='Full',allow_live=self.backend.is_live)
                send({'kind':'result','value':result,'wire':{'events':transport.events,'cpu':transport.cpu,'offers':transport.offers}})
            except BaseException as e:
                try:send({'kind':'failure','reason':type(e).__name__})
                except BaseException:pass
            os._exit(0)
        os.close(requests_w);os.close(answers_r)
        stamp=proc_stamp(pid)
        sel=selectors.DefaultSelector();sel.register(requests_r,selectors.EVENT_READ);buffer=bytearray();received=0
        large_result=None
        def exited():
            try:return Path('/proc',str(pid),'stat').read_text().split(') ')[1].startswith('Z')
            except FileNotFoundError:return True
        self.rpc.abort_check=exited
        self.active_controller=(pid,stamp)
        self.application_deadline=deadline
        ok=False
        try:
            self.control.append({'kind':'application-spawn','pid':pid,'stamp':stamp,'deadline':deadline})
            os.set_blocking(answers_w,False)
            while True:
                if time.monotonic()>=deadline:raise TimeoutError('application deadline')
                for key,_ in sel.select(.02):
                    b=os.read(requests_r,4096)
                    if not b:raise SafetyError('application exited before result')
                    buffer.extend(b)
                    while True:
                        if large_result is not None:
                            size,checksum=large_result
                            if len(buffer)>size:raise SafetyError('trailing large application result')
                            if len(buffer)<size:break
                            if hashlib.sha256(buffer).hexdigest()!=checksum:
                                raise SafetyError('large application result identity changed')
                            packet=json.loads(buffer)
                            if packet.get('kind')!='result':raise SafetyError('invalid large application result')
                            self.emit('wire-events',packet['wire']);ok=True;return packet['value']
                        line,sep,rest=buffer.partition(b'\n')
                        if len(line)+len(sep)>APPLICATION_FRAME_BYTES or received+len(line)+len(sep)>APPLICATION_REQUEST_BYTES:
                            raise SafetyError('application IPC cap')
                        if not sep:break
                        received+=len(line)+1
                        buffer=bytearray(rest);packet=json.loads(line)
                        if packet['kind']=='generate':
                            self.check_storage()
                            if self.t3:
                                if row['partition']!='task':
                                    raise SafetyError('invalid application generation partition')
                                self.task_packet=packet['messages']
                            try:
                                text=self.generate(packet['messages'])
                                reply={'text':text,'audit':self.audit[-1]}
                            except ClientFailure as e:reply={'error':e.reason}
                            finally:self.task_packet=None
                            data=canonical(reply)+b'\n'
                            if len(data)>65536:raise SafetyError('broker reply cap')
                            while data:
                                if exited() or time.monotonic()>=deadline:
                                    raise TimeoutError('application reply deadline')
                                try:data=data[os.write(answers_w,data[:4096]):]
                                except BlockingIOError:time.sleep(.01)
                        elif packet['kind']=='result':
                            self.emit('wire-events',packet['wire']);ok=True;return packet['value']
                        elif packet['kind']=='large-result':
                            size,checksum=packet['bytes'],packet['sha256']
                            if (type(size) is not int or not APPLICATION_FRAME_BYTES<=size<=result_limit
                                    or not isinstance(checksum,str) or not re.fullmatch(r'[0-9a-f]{64}',checksum)):
                                raise SafetyError('invalid large application result header')
                            large_result=(size,checksum)
                        else:raise SafetyError('application failure '+str(packet))
        finally:
            self.rpc.abort_check=None
            self.active_controller=None
            self.application_deadline=float('inf')
            try:
                # The child may fail before setsid; safely stop the owned child
                # itself before reaping if the new group did not start.
                if proc_stamp(pid)==stamp and os.getpgid(pid)!=pid:os.kill(pid,signal.SIGKILL)
                stop_owned(pid,stamp,self.control)
            finally:
                try:os.waitpid(pid,0)
                except ChildProcessError:pass
                os.close(requests_r);os.close(answers_w);sel.close()
            self.control.append({'kind':'application-ended','pid':pid,'completed':ok})
            if not ok and self.service_touched:self.recover()
    def close(self):
        if getattr(self,'ledger',None):self.ledger.close()
        if getattr(self,'control',None):self.control.close()
        if getattr(self,'service_lease',None):self.service_lease.close()
    def __del__(self):
        try:self.close()
        except Exception:pass

if __name__=='__main__':
    if len(sys.argv)!=4 or sys.argv[1]!='--rpc' or not sys.argv[2].isdigit():
        raise SystemExit('only owned RPC entry')
    rpc_worker(int(sys.argv[2]),float(sys.argv[3]))
