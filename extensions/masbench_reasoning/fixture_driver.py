"""B1 integration contracts only. No live backend, data loader or model entry.

The existing client/application/wire run unchanged. Synthetic RPC workers have
no network/file-open/exec/fork syscalls after a Linux x86_64 seccomp allowlist.
This sandbox is NOT suitable for a real tokenizer or model runtime.
"""
from dataclasses import asdict
import ctypes
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import select
import signal
import socket
import subprocess
import time

from .client import ClientConfig, ClientFailure, ContextBinding, ControlledClient, run_controlled
from .execution_safety import Ledger, Limits, SafetyError, canonical, digest
from .wire import ContractTransport

FIXTURE_MODEL = 'fixture-only-not-qwen'
FIXTURE_MANIFEST = '0' * 64
CONTROL_RESERVE = 4096
MAX_RPC_BYTES = 1024 * 1024


def _sandbox(ipc_fd):
    """Default-deny filter; permit writes only to the single IPC pipe."""
    if platform.machine() != 'x86_64':
        raise SafetyError('fixture seccomp requires Linux x86_64')
    class Filter(ctypes.Structure):
        _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
                    ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint)]
    class Program(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ushort), ('filters', ctypes.POINTER(Filter))]
    # seccomp_data: syscall nr at 0, architecture at 4, args at 16.
    rules = [(0x20,0,0,4), (0x15,1,0,0xc000003e), (0x06,0,0,0x80000000),
             (0x20,0,0,0)]
    allowed = [0,3,9,10,11,12,13,14,15,24,25,28,35,39,60,96,
               102,104,107,108,186,202,218,228,230,231,273,318]
    for number in allowed:
        rules.extend([(0x15,0,1,number),(0x06,0,0,0x7fff0000)])
    rules.extend([(0x15,0,4,1), (0x20,0,0,16), (0x15,0,1,ipc_fd),
                  (0x06,0,0,0x7fff0000), (0x06,0,0,0x50000|errno.EPERM),
                  (0x06,0,0,0x50000|errno.EPERM)])
    arr = (Filter*len(rules))(*(Filter(*row) for row in rules))
    prog = Program(len(rules), arr)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38,1,0,0,0) or libc.prctl(22,2,ctypes.byref(prog),0,0):
        raise OSError(ctypes.get_errno(), 'fixture sandbox unavailable')


def _fixture_value(spec, phase, payload):
    mode = spec.get(phase + '_mode', 'ok')
    if mode == 'hang':
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        time.sleep(30)
    if mode == 'error':
        raise RuntimeError('synthetic failure')
    if mode == 'probe':
        denied = {}
        for name, operation in {
            'file_open': lambda: open(spec['probe_path'], 'wb'),
            'socket': lambda: socket.socket(),
            'fork': os.fork,
            'exec': lambda: os.execve('/bin/true', ['/bin/true'], {}),
            'stdout_write': lambda: os.write(1,b'unaccounted'),
        }.items():
            try:
                operation()
            except PermissionError:
                denied[name] = True
            else:
                denied[name] = False
        return denied
    if phase == 'identity':
        return {'model': FIXTURE_MODEL, 'manifest_sha256': spec.get('manifest', FIXTURE_MANIFEST)}
    if mode == 'oversize':
        return {'oversize': 'x' * (MAX_RPC_BYTES+1)}
    response = {'model': FIXTURE_MODEL, 'choices': [{'finish_reason': spec.get('finish_reason','stop'),
                'message': {'content': spec.get('text','Alice: fixture')}}]}
    if spec.get('usage', True):
        n = 4 + spec.get('prompt_usage_offset', 0)
        response['usage'] = {'prompt_tokens': n, 'completion_tokens': 1, 'total_tokens': n+1}
    return response


def fixture_rpc(spec, phase, payload, timeout, trace=None):
    """Hard-stop a single sandboxed owned child; no arbitrary callbacks."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise TimeoutError()
    read_fd, write_fd = os.pipe()
    start = time.monotonic()
    pid = os.fork()
    if pid == 0:
        try:
            # Close inherited ledger/lock/files; only IPC write remains usable.
            fds = [int(p.name) for p in Path('/proc/self/fd').iterdir()]
            for fd in fds:
                if fd != write_fd:
                    try: os.close(fd)
                    except OSError: pass
            resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
            resource.setrlimit(resource.RLIMIT_CPU,(max(1,math.ceil(timeout)),max(1,math.ceil(timeout))))
            _sandbox(write_fd)
            packet = {'ok': True, 'value': _fixture_value(spec,phase,payload)}
        except BaseException as exc:
            packet = {'ok': False, 'exception': type(exc).__name__}
        try:
            data=canonical(packet)
            while data:
                n=os.write(write_fd,data)
                data=data[n:]
        except BaseException:
            pass
        os._exit(0)
    os.close(write_fd)
    data = bytearray()
    reason = None
    usage = None
    try:
        while True:
            remaining = timeout-(time.monotonic()-start)
            if remaining <= 0:
                reason = 'timeout'
                raise TimeoutError()
            if not select.select([read_fd],[],[],remaining)[0]:
                reason = 'timeout'
                raise TimeoutError()
            chunk=os.read(read_fd,65536)
            if not chunk:
                break
            data.extend(chunk)
            if len(data)>MAX_RPC_BYTES:
                reason='response_size_cap'
                raise ClientFailure(reason)
        packet=json.loads(data)
        if not packet.get('ok'):
            raise ClientFailure('fixture_worker_'+str(packet.get('exception')))
        return packet['value']
    finally:
        try: os.kill(pid, signal.SIGKILL)
        except ProcessLookupError: pass
        _, status, usage = os.wait4(pid,0)
        os.close(read_fd)
        if trace is not None:
            trace.update(phase=phase,pid=pid,elapsed_seconds=time.monotonic()-start,
                         cpu_user_seconds=usage.ru_utime,cpu_system_seconds=usage.ru_stime,
                         max_rss_kib=usage.ru_maxrss,exit_status=status,
                         model_inference=False,gpu_peak_bytes=None)


def _jsonable(value):
    if isinstance(value,bytes):
        return {'utf8_or_wire_hex':value.hex()}
    if isinstance(value,dict):
        return {k:_jsonable(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        return [_jsonable(v) for v in value]
    return value


class CampaignLedger(Ledger):
    """Separate identity/schema namespace; never resumes B1-pre v1 journals."""
    def __init__(self,root,identity,plan,limits,task_cap=96,synthetic_cap=2):
        if limits.artifact_bytes <= CONTROL_RESERVE+4096:
            raise SafetyError('insufficient control reserve')
        self.public_limits=limits
        self.artifacts={}
        self.task_cap,self.synthetic_cap=task_cap,synthetic_cap
        if any(type(n) is not int or n<0 for n in [task_cap,synthetic_cap]):
            raise SafetyError('invalid partition cap')
        if task_cap+synthetic_cap>limits.requests:
            raise SafetyError('partition cap exceeds generation cap')
        bound={'schema':'fixture-campaign-v1','identity':identity,'plan':plan,
               'task_cap':task_cap,'synthetic_cap':synthetic_cap,'control_reserve':CONTROL_RESERVE}
        ids=[row['id'] for row in plan]
        from dataclasses import replace
        super().__init__(root,bound,ids,replace(limits,artifact_bytes=limits.artifact_bytes-CONTROL_RESERVE))
        try:
            if any(v=='started' for v in self.state['episodes'].values()):
                self.state['fenced']=True  # Crash between turns still cannot replay episode.
            for name, record in self.artifacts.items():
                p=self.root/'artifacts'/name
                if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:
                    raise SafetyError('artifact missing or changed on resume')
            self.check_storage()
        except BaseException:
            self.close()
            raise

    def _apply(self,event):
        if event['kind']=='fence':
            self.state['fenced']=True
            return
        super()._apply(event)
        if event['kind']=='bytes':
            if event['path'] in self.artifacts:
                raise SafetyError('duplicate artifact reservation')
            self.artifacts[event['path']]=event

    def check_storage(self):
        total=0
        for p in self.root.rglob('*'):
            if p.is_symlink(): raise SafetyError('unexpected symlink')
            if p.is_file():
                rel=p.relative_to(self.root).as_posix()
                if rel not in {'ledger.lock','ledger.jsonl','guard.jsonl'} and not (rel.startswith('artifacts/') and rel[10:] in self.artifacts):
                    raise SafetyError('unregistered artifact')
                total+=p.stat().st_size
        guard=self.root/'guard.jsonl'
        if guard.exists() and guard.stat().st_size>CONTROL_RESERVE:
            raise SafetyError('control reserve exceeded')
        if total>self.public_limits.artifact_bytes:
            raise SafetyError('physical artifact cap')

    def reserve_partition(self,request_id,episode_id,exact_input,max_output,partition):
        if partition not in {'task','synthetic'} or not request_id.startswith(partition+'/'):
            raise SafetyError('invalid partition identity')
        cap=self.task_cap if partition=='task' else self.synthetic_cap
        used=sum(k.startswith(partition+'/') for k in self.state['requests'])
        if used>=cap: raise SafetyError('partition cap exhausted')
        self.check_storage()
        self.reserve_request(request_id,episode_id,exact_input,max_output)

    def emit(self,kind,value):
        self.check_storage()
        self.put_artifact(f'{self.seq:08d}-{kind}.jsonl',canonical(_jsonable(value))+b'\n')

    def fence(self,reason):
        self._append({'kind':'fence','reason':reason})


class _Backend:
    is_live=False
    def __init__(self,driver,episode):
        self.driver,self.episode=driver,episode
        self.pending=None
        self.uncertain=False

    def identity(self,timeout):
        l=self.driver.ledger
        l.check_storage()
        l.metadata()
        return self._call('identity',None,timeout)

    def _call(self,phase,payload,timeout):
        l=self.driver.ledger
        remaining=min(timeout,self.driver.operation_deadline-time.monotonic(),l.remaining()-.1)
        trace={}
        try:
            return fixture_rpc(self.driver.current_spec,phase,payload,remaining,trace)
        except TimeoutError:
            self.uncertain=True
            raise
        finally:
            if trace: l.emit('fixture-worker-cost',trace)

    def create(self,payload,timeout):
        l=self.driver.ledger
        kind=self.episode['partition']
        rid=f'{kind}/{self.episode["id"]}/{len(l.state["requests"])}'
        l.reserve_partition(rid,self.episode['id'],4,payload['max_tokens'],kind)
        self.pending=rid
        try:
            return self._call('create',payload,timeout)
        except TimeoutError:
            self.uncertain=True
            raise


class _Client:
    """Preserve original client audit/failure semantics and settle after validation."""
    def __init__(self,driver,episode):
        self.driver=driver
        self.backend=_Backend(driver,episode)
        l=driver.ledger
        cfg=ClientConfig(FIXTURE_MODEL,FIXTURE_MANIFEST,1024,
                         max_output_tokens=l.limits.per_output,
                         timeout_seconds=l.limits.operation_seconds,
                         max_calls=l.limits.requests,wall_seconds=max(.001,l.remaining()-.1))
        # Deliberately synthetic. Never creates a qwen ContextBinding.
        binding=ContextBinding(FIXTURE_MANIFEST,1024,'fixture-fixed-four',digest('fixture-only'),True)
        self.inner=ControlledClient(cfg,self.backend,lambda request:4,binding,
                                    audit_sink=lambda e:l.emit('client',e))
        self.audit=self.inner.audit

    def generate(self,messages):
        d=self.driver
        self.backend.pending=None
        self.backend.uncertain=False
        if d.position>=len(d.specs):
            raise ClientFailure('fixture_responses_exhausted')
        d.current_spec=d.specs[d.position]
        d.position+=1
        d.operation_deadline=time.monotonic()+d.ledger.limits.operation_seconds
        successful=False
        try:
            result=self.inner.generate(messages)
            successful=True
            return result
        finally:
            if self.backend.pending:
                row=self.audit[-1]
                status='completed' if successful and row['error'] is None else ('timeout' if row['error']=='timeout' else 'failed')
                u=row['usage'] if status=='completed' else None
                usage={k:u[k] for k in ('prompt_tokens','completion_tokens')} if u is not None else None
                d.ledger.finish_request(self.backend.pending,status,usage,self.backend.uncertain)
            elif self.backend.uncertain:
                d.ledger.fence('metadata_or_predispatch_timeout')


class _Transport(ContractTransport):
    def __init__(self,ledger,**kwargs):
        super().__init__(**kwargs)
        self.ledger=ledger
        self.event_offset=self.cpu_offset=self.offer_offset=0

    def flush(self):
        for name,offset in [('events','event_offset'),('cpu','cpu_offset'),('offers','offer_offset')]:
            rows=getattr(self,name)
            for row in rows[getattr(self,offset):]:
                self.ledger.emit('wire-'+name,row)
            setattr(self,offset,len(rows))

    def application_cpu(self,stage):
        value=super().application_cpu(stage)
        self.flush()
        return value

    def transfer(self,*args,**kwargs):
        try: return super().transfer(*args,**kwargs)
        finally: self.flush()


class FixtureCampaign:
    """No real endpoint selection, data loading, gold or live-mode switch."""
    def __init__(self,root,identity,plan,limits=Limits(),task_cap=96,synthetic_cap=2):
        for e in plan:
            if set(e)!={'id','family','style','condition','partition'} or not e['id'] or not e['family']:
                raise SafetyError('explicit fixture plan required')
            if e['style'] not in {'base','protocol'} or e['condition'] not in {'Full','No-A2A'} or e['partition'] not in {'task','synthetic'}:
                raise SafetyError('invalid fixture episode')
        self.plan=json.loads(json.dumps(plan))
        self.ledger=CampaignLedger(root,identity,self.plan,limits,task_cap,synthetic_cap)
        self.specs=[]
        self.position=0
        self.current_spec={}
        self.operation_deadline=0

    def run_episode(self,episode_id,agents,specs,max_turns=6):
        if type(max_turns) is not int or not 1<=max_turns<=6:
            raise SafetyError('six total speaking turns maximum')
        e=next((e for e in self.plan if e['id']==episode_id),None)
        if e is None: raise SafetyError('unplanned episode')
        if any(a.memory or a.facts or a.received for a in agents):
            raise SafetyError('fresh private agent state required')
        # Bind private observations across conditions without storing peer state
        # in a model input. Offline plan identity, not online value estimation.
        view=digest([asdict(a.view) for a in agents])
        initial_request=digest([a.request() for a in agents])
        for other in self.plan:
            if other['family']==e['family'] and other['style']==e['style'] and other['id']!=e['id']:
                for a in self.ledger.artifacts.values():
                    if a['path'].endswith('-episode-input.jsonl'):
                        x=json.loads((self.ledger.root/'artifacts'/a['path']).read_bytes())
                        if x['id']==other['id'] and (x['view_sha256']!=view or x['initial_request_sha256']!=initial_request):
                            raise SafetyError('paired private observations or prompt differ')
        self.ledger.episode(episode_id,'started')
        self.specs=json.loads(json.dumps(specs))
        self.position=0
        try:
            self.ledger.emit('episode-input',{'id':episode_id,'view_sha256':view,
                                            'initial_request_sha256':initial_request,'fixture_only':True})
            client=_Client(self,e)
            transport=_Transport(self.ledger,episode_id=self.plan.index(e)+1)
            result=run_controlled(agents,client,transport,e['style'],max_turns=max_turns,
                                  admit=lambda sender,body,turn:e['condition']=='Full')
            result.update(id=episode_id,fixture_only=True,wire_totals=transport.totals(),
                          real_model_inference_wall_seconds=None,gpu_peak_bytes=None)
            self.ledger.emit('episode-result',result)
            state='failed' if result['end_reason'] in {'timeout','model_error','deadline'} else 'completed'
            self.ledger.episode(episode_id,state)
            return result
        except BaseException:
            # If terminal storage is exhausted, durable started remains visible.
            if self.ledger.state['episodes'][episode_id]=='started':
                try: self.ledger.episode(episode_id,'failed')
                except BaseException: pass
            raise

    def close(self): self.ledger.close()
    def __enter__(self): return self
    def __exit__(self,*args): self.close()


def guard_fixture_process(argv,root,wall_seconds):
    """Independent outer supervisor; append-only bounded control reserve.

    A new session contains controller and inherited RPC children. KILL group
    after timeout OR controller exit (including crash). No service PID involved.
    The sole guard log is capped across resumes and included in public storage.
    """
    if not math.isfinite(wall_seconds) or wall_seconds<=0:
        raise SafetyError('invalid outer deadline')
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    guard=root/'guard.jsonl'
    if guard.is_symlink():raise SafetyError('guard log symlink')
    if guard.exists() and guard.stat().st_size>CONTROL_RESERVE-1024:
        raise SafetyError('guard reserve exhausted')
    start=time.monotonic()
    deadline=start+wall_seconds
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    header={'kind':'guard-init','started_mono':start,'boot':boot,
            'wall_seconds':wall_seconds,'argv_sha256':digest(argv)}
    new_guard=not guard.exists()
    if not new_guard:
        with guard.open('rb') as f: first=f.readline()
        if not first.endswith(b'\n'):raise SafetyError('partial guard header')
        previous=json.loads(first)
        h=previous.pop('hash')
        if (digest(previous)!=h or previous['kind']!='guard-init' or previous['boot']!=boot
                or previous['wall_seconds']!=wall_seconds or previous['argv_sha256']!=digest(argv)):
            raise SafetyError('outer guard identity/budget changed')
        deadline=min(deadline,previous['started_mono']+wall_seconds)
    journal=root/'ledger.jsonl'
    if journal.exists():
        with journal.open('rb') as f: row=json.loads(f.readline())
        h=row.pop('hash')
        event=row['event']
        if digest(row)!=h or event['kind']!='init' or event['boot']!=Path('/proc/sys/kernel/random/boot_id').read_text().strip():
            raise SafetyError('resume deadline identity invalid')
        deadline=min(deadline,event['started_mono']+wall_seconds)
    if deadline<=time.monotonic(): raise SafetyError('original wall expired')
    if new_guard:
        with guard.open('xb') as f:
            f.write(canonical({**header,'hash':digest(header)})+b'\n')
            f.flush();os.fsync(f.fileno())
    p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,start_new_session=True)
    reason='exited'
    try:
        p.wait(timeout=max(.001,deadline-time.monotonic()-.1))
    except subprocess.TimeoutExpired:
        reason='timeout'
    finally:
        try: os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        p.wait(timeout=2)
    result={'kind':'guard-stop','reason':reason,'returncode':p.returncode,'group':p.pid,
            'elapsed_seconds':time.monotonic()-start,'server_cancel_verified':False}
    data=canonical(result)+b'\n'
    if guard.is_symlink() or (guard.stat().st_size if guard.exists() else 0)+len(data)>CONTROL_RESERVE:
        raise SafetyError('guard log unsafe/exhausted')
    with guard.open('ab') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    return result
