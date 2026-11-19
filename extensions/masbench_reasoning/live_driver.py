"""T1 synthetic live adapter. No data loader, cloud fallback or helper rebuild.

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
MAX_RPC_SECONDS = 60


def rpc_seconds(spec, formal):
    body=spec.get('body')
    if (formal and spec.get('kind')=='http' and spec.get('method')=='POST' and spec.get('path')=='/api/chat'
            and isinstance(body,dict) and body.get('_debug_render_only') is True):
        return 120
    return MAX_RPC_SECONDS


def reject_links(path):
    p=Path(path).absolute()
    if any(x.is_symlink() for x in [p,*p.parents]):raise SafetyError('symlink in path')
    return p
def require_authorization(path):
    root=Path(__file__).resolve().parents[2]
    expected=root/FORMAL_AUTH
    if path is None or reject_links(path)!=expected or not expected.is_file():raise SafetyError('T1-B real execution not authorized')
    data=json.loads(expected.read_bytes())
    if data.get('approved') is not True or data.get('scope')!='T1-B synthetic only' or data.get('exclusive_service') is not True:
        raise SafetyError('T1-B approval/exclusive-service absent')
    for k in ['protocol_sha256','registry_sha256','plan_sha256','source_sha256']:
        if not re.fullmatch('[0-9a-f]{64}',str(data.get(k,''))):raise SafetyError('incomplete execution identity')
    if data['source_sha256']!=file_sha(__file__):raise SafetyError('authorized source drift')
    for field, relative in [('protocol_sha256',FORMAL_BUDGET),
                            ('registry_sha256','research/artifacts/native-masbench-20261104/masbench_development_registry.json'),
                            ('plan_sha256',FORMAL_PLAN),
                            ('previous_recovery_receipt_sha256','research/logs/masbench-t1-driver-2026-11-17/'
                             't1_formal_marker_recovery_applied_20261119.json'),
                            ('runner_sha256','experiments_ext/masbench_t1b_live.py')]:
        if data.get(field)!=file_sha(reject_links(root/relative)):raise SafetyError('authorized material drift: '+field)
    run = Path(os.environ.get('GOSC_RUN_DIR','/'))
    if run.parent != root/'research/sync/runs' or run.name != data.get('run_id'):
        raise SafetyError('authorization is bound to one registered run')
    return data

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
    def __init__(self,path,identity,caps=None):
        self.path=Path(path);self.caps=caps or {'debug':4,'get':24,'cleanup_get':16,'unload':4}
        self.rows=[];self.previous='0'*64;self.used={k:0 for k in self.caps}
        reject_links(self.path)
        self.lease=ServiceLease(self.path.with_suffix('.lock'))
        exists=self.path.exists()
        if exists:
            if self.path.stat().st_size>128*1024:raise SafetyError('control reserve exceeded')
            prefix=self.path.read_bytes().rstrip(b'\0')
            for line in prefix.splitlines(keepends=True):
                if not line.endswith(b'\n'):raise SafetyError('partial control record')
                r=json.loads(line);h=r.pop('hash')
                if r['seq']!=len(self.rows) or r['previous']!=self.previous or digest(r)!=h:raise SafetyError('control chain')
                self.rows.append(r);self.previous=h
                if r['event']['kind']=='charge':self.used[r['event']['category']]+=1
            if not self.rows or self.rows[0]['event']!={'kind':'init','identity':identity,'caps':self.caps}:raise SafetyError('control identity changed')
            if any(self.used[k]>self.caps[k] for k in self.caps):raise SafetyError('persisted control over budget')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.stream=self.path.open('r+b' if exists else 'x+b',buffering=0)
        if not exists:
            os.posix_fallocate(self.stream.fileno(),0,128*1024)
            self.stream.truncate(128*1024);os.fsync(self.stream.fileno())
        self.offset=len(prefix) if exists else 0
        self.stream.seek(self.offset)
        if not self.rows:self.append({'kind':'init','identity':identity,'caps':self.caps})
        self.identity=identity
    def append(self,event):
        r={'seq':len(self.rows),'previous':self.previous,'mono':time.monotonic(),'event':event};h=digest(r)
        b=canonical(dict(r,hash=h))+b'\n'
        if self.offset+len(b)>128*1024:raise SafetyError('control reserve exhausted')
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
    def __init__(self,root,identity,limits,plan=None):
        self.last_fault=-1;self.last_barrier=-1;self.recovery_required=False;self.permanent_fence=False
        self.service={'pid':identity['runtime']['service_pid'], 'stamp':identity['runtime']['service_stamp']}
        super().__init__(root,{'schema':'t1-live-v1','binding':identity},
            plan or [{'id':'synthetic','partition':'synthetic'}],limits,task_cap=0,synthetic_cap=limits.requests)
        self.recovery_required=any(v=='started' for v in self.state['episodes'].values())
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
        if spec.get('kind')!='fixture':
            require_authorization(self.authorization)
            spec['authorization']=str(self.authorization)
        payload=canonical(spec)
        if len(payload)>1024*1024:raise SafetyError('RPC input size cap')
        deadline=min(self.deadline,time.monotonic()+min(timeout,rpc_seconds(spec,self.authorization is not None)))
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
        require_authorization(spec.get('authorization'))
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
        cap = rpc_seconds(spec,spec.get('authorization') is not None)
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
        if plan is not None and any(e.get('partition')!='synthetic' or e.get('style') not in {'base','protocol'} or e.get('condition') not in {'Full','No-A2A'} for e in plan):
            raise SafetyError('T1 plan is synthetic only')
        if transport is not None and getattr(transport,'is_live',True):raise SafetyError('injected transport must be explicitly no-network')
        if transport is not None and runtime.model != FIXTURE_MODEL:
            raise SafetyError('fixture transport requires separate model identity')
        approval=require_authorization(authorization) if transport is None else None
        if approval and (validator is not None or runtime.model!='qwen2.5:7b' or runtime.context!=1024):
            raise SafetyError('live runtime profile may not be overridden')
        self.root=reject_links(root);self.root.mkdir(parents=True,exist_ok=True);self.runtime=runtime
        self.model_manifest = MANIFEST if approval else FIXTURE_MANIFEST
        self.service_lease=ServiceLease(Path(runtime.root)/'.local/t1-service.lock')
        self.validate=validator or runtime_files
        identity={'runtime':runtime.identity(),'source_sha256':file_sha(__file__),
                  'authorization_sha256':file_sha(authorization) if approval else 'fixture-only',
                  'scope':'T1-B synthetic only' if approval else 'T1-A no-network fixture',
                  'model_manifest': self.model_manifest}
        self.ledger=LiveLedger(self.root/'campaign',identity,limits,plan)
        self.lease_owner = canonical({'campaign': str(self.root), 'ledger_binding': self.ledger.binding})
        previous_owner = self.service_lease.owner()
        if previous_owner not in (b'', self.lease_owner):
            raise SafetyError('specific previous campaign must recover before dispatch')
        if previous_owner:
            self.ledger.recovery_required = True
        self.plan=plan;self.current_episode='synthetic'
        self.control=ControlJournal(self.root/'control.jsonl',self.ledger.binding)
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
        if size>self.ledger.public_limits.artifact_bytes+128*1024:raise SafetyError('physical campaign+control cap')
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
    def generate(self,messages,max_output=None,network_timeout=60,crash=False):
        case = self.armed_case if self.approval else None
        if self.approval:
            path=Path(__file__).resolve().parents[2]/FORMAL_PLAN
            frozen_cases=json.loads(path.read_bytes())['cases']
            started=[r['event']['id'] for r in self.control.rows if r['event']['kind']=='case-start']
            if (case not in frozen_cases or case['messages']!=messages or not started or started[-1]!=case['id']
                    or started!=[x['id'] for x in frozen_cases[:len(started)]]):
                raise SafetyError('generation is outside the frozen synthetic case')
            if max_output is not None and max_output!=case['max_output']:raise SafetyError('case output cap drift')
            max_output=case['max_output']
            self.armed_case=None
        elif max_output is None:max_output=min(32,self.ledger.limits.per_output)
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
                request_id='synthetic/'+str(len(driver.ledger.state['requests']))
                driver.control.append({'kind':'runner-dispatch-bound','request_id':request_id,
                                       'runner':driver.attested_runner,'service':service_identity(driver.runtime),
                                       'payload_sha256':digest(payload)})
                driver.ledger.reserve_partition(request_id,driver.current_episode,driver.counted[1],max_output,'synthetic')
                driver.pending=request_id
                driver.emit('provider-request',{'request_id':driver.pending,'payload':payload})
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
                    outcome = 'completed' if success else {'timeout':'timeout','application controller exited':'interrupted'}.get(failure,'failed')
                    self.ledger.finish_request(self.pending,outcome,usage,not success)
                if not success:
                    self.control.append({'kind':'client-failure','request_id':self.pending,'error':failure})
            finally:
                if not success and self.service_touched:
                    self.recover()
    def run_episode(self,episode_id,agents,max_turns=2,fixture_fault=None):
        if not self.plan:raise SafetyError('application plan required')
        row=next((e for e in self.plan if e['id']==episode_id),None)
        if row is None or type(max_turns) is not int or not 1<=max_turns<=6:raise SafetyError('unplanned episode/turns')
        if any(a.memory or a.facts or a.received for a in agents):raise SafetyError('fresh agent state required')
        if fixture_fault and self.backend.is_live:raise SafetyError('fixture fault injection not a live execution mode')
        proof={'id':episode_id,'family':row['family'],'style':row['style'],
               'views':digest([asdict(a.view) for a in agents]),'initial_requests':digest([a.request() for a in agents])}
        for record in self.ledger.artifacts.values():
            if record['path'].endswith('-pair-binding.json'):
                old=json.loads((self.ledger.root/'artifacts'/record['path']).read_bytes())
                if old['family']==proof['family'] and old['style']==proof['style'] and any(old[k]!=proof[k] for k in ['views','initial_requests']):
                    raise SafetyError('paired private views/prompt changed')
        self.ledger.episode(episode_id,'started');self.current_episode=episode_id
        self.emit('pair-binding',proof)
        try:
            result=self._guard_application(agents,row,max_turns,fixture_fault)
            self.emit('application-result',result)
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
                b=canonical(_jsonable(value))+b'\n'
                if len(b)>65536:raise SafetyError('application IPC cap')
                while b:b=b[os.write(requests_w,b):]
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
                    buffer.extend(b);received+=len(b)
                    if received>512*1024 or len(buffer)>65536:raise SafetyError('application IPC cap')
                    while b'\n' in buffer:
                        line,_,rest=buffer.partition(b'\n');buffer=bytearray(rest);packet=json.loads(line)
                        if packet['kind']=='generate':
                            self.check_storage()
                            try:
                                text=self.generate(packet['messages'])
                                reply={'text':text,'audit':self.audit[-1]}
                            except ClientFailure as e:reply={'error':e.reason}
                            data=canonical(reply)+b'\n'
                            if len(data)>65536:raise SafetyError('broker reply cap')
                            while data:
                                if exited() or time.monotonic()>=deadline:
                                    raise TimeoutError('application reply deadline')
                                try:data=data[os.write(answers_w,data[:4096]):]
                                except BlockingIOError:time.sleep(.01)
                        elif packet['kind']=='result':
                            self.emit('wire-events',packet['wire']);ok=True;return packet['value']
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
