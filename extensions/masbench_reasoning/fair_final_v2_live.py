"""Independent v2 synthetic-live admission, ledger and bounded RPC entry.

No legacy approval is accepted. This release authorizes two immutable artificial
requests only, not datasets or task diagnosis. The old fixture entry is unchanged.
"""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

from . import live_driver as primitives
from .client import ClientConfig, ClientFailure, ContextBinding, ControlledClient, LivePermit
from .execution_safety import Ledger, Limits, SafetyError, canonical, digest
from .fair_final_v2 import SYSTEM_SHA, TEMPLATE_SHA, REGISTRY_SHA

ROOT = Path(__file__).resolve().parents[2]
AUTH = ROOT/'research/protocols/masbench_t3rv2_live_authorization_2026-11-26.json'
PLAN = ROOT/'research/protocols/masbench_t3rv2_live_plan_2026-11-26.json'
SCOPE = 'T3-R-v2 two immutable artificial service probes only'
MODEL = 'qwen2.5:7b'
CAPS = dict(generation=2, render=2, get=8, cleanup_get=14, unload=2, lifecycle_get=128)
HELPER = '/tmp/gosc-hpc-masbench-context-build-v3-20261116/context-counter'
BINARY_SHA = 'e014750cd656db3a77f3bf6b45903f646c76075e58b835cc9787fb5fc8a8a600'
HDD = Path('/hdd/u202520081000097/gosc-t3rv2-live')
MATERIALS = {
    'extensions/masbench_reasoning/fair_final_v2_live.py',
    'extensions/masbench_reasoning/fair_final_v2_runtime.py',
    'experiments_ext/masbench_t3rv2_live_probe.py',
    'experiments_ext/masbench_t3rv2_live_contract.py',
    'tests_ext/test_masbench_t3rv2_live.py',
    'extensions/masbench_reasoning/client.py',
    'extensions/masbench_reasoning/execution_safety.py',
    'extensions/masbench_reasoning/application.py',
    'extensions/masbench_reasoning/wire.py',
    'extensions/masbench_reasoning/fixture_driver.py',
    'extensions/masbench_reasoning/live_driver.py',
    'extensions/masbench_reasoning/fair_final_v2.py',
    'extensions/masbench_reasoning/fair_final_v2_guard.py',
    'extensions/masbench_reasoning/fair_final_v2_prompt.txt',
    'research/protocols/masbench_t3rv2_live_plan_2026-11-26.json',
    'research/protocols/masbench_t3rv2_live_budget_2026-11-26.md',
    'research/logs/masbench-t3rv2-deployment-2026-11-26/probe_inputs.json',
    'scripts/hpc_ollama.py',
    'experiments_ext/masbench_t3rv2i_register.py',
}


def file_sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def validate_approval(a, run_id):
    if (a.get('schema') != 't3rv2-synthetic-live-approval-v1' or a.get('approved') is not True
            or a.get('scope') != SCOPE or a.get('run_id') != run_id
            or a.get('generation_cap') != 2 or a.get('task_generation_cap') != 0
            or a.get('monitoring_approved') is not True or a.get('context') != 16384
            or a.get('http_caps') != CAPS or a.get('wall_seconds') != 2000
            or a.get('max_output') != 512 or a.get('helper_attempts') != 2):
        raise SafetyError('new_v2_approval_required')
    return a


def require_approval():
    run = Path(os.environ.get('GOSC_RUN_DIR', '/'))
    if run.parent != ROOT/'research/sync/runs':
        raise SafetyError('registered_v2_run_required')
    a = validate_approval(json.loads(primitives.reject_links(AUTH).read_bytes()), run.name)
    if set(a.get('bound_files',{})) != MATERIALS:
        raise SafetyError('incomplete_execution_source_bindings')
    for relative, expected in a['bound_files'].items():
        p = primitives.reject_links(ROOT/relative)
        if ROOT not in p.parents or file_sha(p) != expected:
            raise SafetyError('approved_source_or_plan_drift:'+relative)
    if not a['bound_files'] or str(Path(__file__).relative_to(ROOT)).replace('\\','/') not in a['bound_files']:
        raise SafetyError('live_source_binding_missing')
    report = ROOT/a['contract_receipt']
    if file_sha(report) != a['contract_sha256']:
        raise SafetyError('new_contract_receipt_required')
    contract=json.loads(report.read_bytes())
    if (contract.get('passed') is not True or contract.get('model_calls')!=0
            or not all(contract.get('labels',{}).get(f'D{i:02d}',0)>0 for i in range(1,13))
            or any(relative not in a['bound_files'] or a['bound_files'][relative]!=expected
                   for relative,expected in contract.get('source_files',{}).items())
            or not contract.get('source_files')):
        raise SafetyError('new_contract_source_or_labels_mismatch')
    return a


class LiveBudget(Ledger):
    """One immutable journal; reopen keeps deadline/counters, never refunds."""
    def __init__(self, root, identity, episodes, *, wall=2000, artifact_bytes=99*1024**2):
        limits = Limits(requests=2, metadata=156, output_tokens=1024, input_tokens=31744,
                        per_output=512, wall_seconds=wall, operation_seconds=180,
                        artifact_bytes=artifact_bytes)
        self.artifact_records = {}
        super().__init__(root, identity, episodes, limits)
        for relative, row in self.artifact_records.items():
            p = self.root/'artifacts'/relative
            if p.is_symlink() or not p.is_file() or file_sha(p) != row['sha256']:
                self.close(); raise SafetyError('reserved_artifact_missing_or_changed')

    def _apply(self, event):
        k=event['kind']
        if k == 'http':
            self.state['http'][event['category']] += 1
            if event['category']=='generation': self.state['sent'].append(event['request_id'])
            return
        if k == 'operation':
            self.state['operations'][event['name']] += 1; return
        if k == 'fence':
            self.state['fenced']=True; return
        if k == 'cleanup':
            self.state['cleanup'][event['episode']]=event['status']; return
        if k == 'control': return
        super()._apply(event)
        if k == 'init':
            self.state.update(http=dict.fromkeys(CAPS,0),sent=[],operations=dict(counter=0,start=0,stop=0),cleanup={})
        if k == 'bytes': self.artifact_records[event['path']]=event

    def control(self, label, **data):
        self._append(dict(kind='control',label=label,mono=time.monotonic(),**data))

    def fence(self, reason):
        self._append(dict(kind='fence',reason=str(reason)))

    def operation(self, name):
        if name not in self.state['operations'] or self.state['operations'][name]>=2:
            raise SafetyError('lifecycle_or_counter_cap')
        if name=='counter': self._admit()
        self._append(dict(kind='operation',name=name))

    def charge(self, category, path, body=None):
        validate_http(category,path,body)
        if category not in ('cleanup_get','unload','lifecycle_get'): self._admit()
        if self.state['http'][category]>=CAPS[category] or sum(self.state['http'].values())>=156:
            raise SafetyError('all_HTTP_attempt_cap')
        rid=None
        if category=='generation':
            inflight=[k for k,r in self.state['requests'].items() if r['status']=='inflight']
            if len(inflight)!=1 or inflight[0] in self.state['sent']:
                raise SafetyError('unique_permanent_reservation_required')
            rid=inflight[0]
        self._append(dict(kind='http',category=category,path=path,body_sha256=digest(body),
                          request_id=rid,live_operation=True))

    def cleanup_once(self, episode):
        if episode in self.state['cleanup']: raise SafetyError('cleanup_already_attempted')
        self._append(dict(kind='cleanup',episode=episode,status='attempted'))


def validate_http(category, path, body):
    if category in ('get','cleanup_get','lifecycle_get'):
        allowed={'get':{'/api/ps','/api/version'},'cleanup_get':{'/api/ps'},
                 'lifecycle_get':{'/api/ps','/api/version','/api/tags'}}[category]
        if path not in allowed or body is not None: raise SafetyError('GET_schema')
    elif category=='unload':
        if path!='/api/chat' or body!=dict(model=MODEL,messages=[],keep_alive=0,stream=False):
            raise SafetyError('unload_schema')
    elif category=='render':
        if (path!='/api/chat' or not isinstance(body,dict)
                or set(body)!={'model','messages','stream','_debug_render_only'}
                or body['model']!=MODEL or body['stream'] is not False or body['_debug_render_only'] is not True):
            raise SafetyError('render_schema')
    elif category=='generation':
        if (path!='/v1/chat/completions' or not isinstance(body,dict)
                or set(body)!={'model','messages','temperature','max_tokens','stream'}
                or body['model']!=MODEL or body['temperature']!=0
                or body['max_tokens']!=512 or body['stream'] is not False):
            raise SafetyError('generation_schema')
    else: raise SafetyError('HTTP_category')


def verify_count(messages, value):
    if (value.get('vocab_only') is not True or value.get('tensor_context_created') is not False
            or value.get('template_sha256')!=primitives.TEMPLATE
            or value.get('add_special') is not False or value.get('parse_special') is not True
            or len(value.get('requests',[]))!=1):
        raise SafetyError('counter_identity_or_shape')
    row=value['requests'][0]
    if (type(row.get('token_count')) is not int or row['token_count']<0
            or len(row.get('token_ids',[]))!=row['token_count']
            or hashlib.sha256(canonical(row['token_ids'])).hexdigest()!=row['token_ids_json_sha256']
            or hashlib.sha256(row['rendered'].encode()).hexdigest()!=row['rendered_sha256']
            or len(row['rendered'].encode())!=row['utf8_bytes']):
        raise SafetyError('counter_content_binding')
    if row['token_count']+512>16384: raise SafetyError('context_overflow_no_truncation')
    if len(canonical(messages))>65536: raise SafetyError('application_IPC_packet_cap')
    return row


def verify_complete_download(expected, downloaded):
    if not isinstance(expected,dict) or not isinstance(downloaded,dict) or set(expected)!=set(downloaded):
        raise SafetyError('complete_transfer_file_set')
    if any(not isinstance(b,bytes) or hashlib.sha256(b).hexdigest()!=expected[p]
           for p,b in downloaded.items()):
        raise SafetyError('complete_transfer_SHA')
    return True


class RPC:
    def __init__(self, ledger, artifact, monitor):
        self.ledger,self.artifact,self.monitor=ledger,artifact,monitor
        self.sequence=0

    def call(self, spec, timeout):
        require_approval()
        timeout=min(timeout,self.ledger.remaining())
        if timeout<=0: raise TimeoutError('phase_deadline')
        self.sequence+=1
        deadline=time.monotonic()+timeout
        p=subprocess.Popen([sys.executable,'-m',__name__,'--worker',str(os.getpid()),str(deadline)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
        stamp=primitives.proc_stamp(p.pid)
        payload=canonical(spec); chunks=bytearray(); raw=bytearray(); result=None
        sel=selectors.DefaultSelector(); sel.register(p.stdout,selectors.EVENT_READ)
        os.set_blocking(p.stdin.fileno(),False);sel.register(p.stdin,selectors.EVENT_WRITE);offset=0
        self.ledger.control('rpc-spawn',pid=p.pid,stamp=stamp,request_sha256=digest(spec),deadline=deadline)
        try:
            while True:
                self.monitor()
                if time.monotonic()>=deadline: raise TimeoutError('owned_RPC_deadline')
                for key,_ in sel.select(min(.02,max(0,deadline-time.monotonic()))):
                    if key.fileobj is p.stdin:
                        try: offset+=os.write(p.stdin.fileno(),payload[offset:offset+4096])
                        except BlockingIOError: continue
                        if offset==len(payload):sel.unregister(p.stdin);p.stdin.close()
                        continue
                    b=os.read(p.stdout.fileno(),65536)
                    if not b:
                        if result is None: raise SafetyError('RPC_EOF_without_result')
                        return result
                    raw.extend(b);chunks.extend(b)
                    if len(raw)>1024**2: raise SafetyError('RPC_response_cap')
                    while b'\n' in chunks:
                        line,_,rest=chunks.partition(b'\n');chunks=bytearray(rest);r=json.loads(line)
                        if r['phase']=='sent':self.ledger.control('http-sent',pid=p.pid,spec_sha256=digest(spec))
                        elif r['phase']=='result':result=r['value']
                        elif r['phase']=='error':raise SafetyError('RPC_worker_'+r['error'])
        finally:
            try:
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGTERM)
                    try:p.wait(timeout=.15)
                    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL)
                p.wait(timeout=2)
                if primitives.proc_stamp(p.pid)==stamp:raise SafetyError('RPC_exit_unverified')
            finally:
                sel.close();p.stdout.close()
                if not p.stdin.closed:p.stdin.close()
                self.artifact(f'rpc/{self.sequence:03d}.jsonl',bytes(raw))
                self.ledger.control('rpc-end',pid=p.pid,stamp=stamp,exit_code=p.returncode)


def worker(parent, deadline):
    primitives.stop_with_parent(parent)
    import resource
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    spec=json.loads(sys.stdin.buffer.read(1024**2+1))
    def emit(v):print(json.dumps(v),flush=True)
    try:
        require_approval()
        runtime=primitives.Runtime(**spec['runtime'])
        models=primitives.runtime_files(runtime)
        if runtime.context not in (1024,16384) or runtime.model!=MODEL:
            raise SafetyError('runtime_scope')
        left=deadline-time.monotonic()
        if left<=0:raise TimeoutError()
        if spec['kind']=='counter':
            if runtime.context!=16384: raise SafetyError('counter_context')
            data=spec['input']
            if (set(data)!={'model_path','template_path','template_sha256','requests','texts'}
                    or data['model_path']!=str(models/'blobs'/primitives.MODEL_BLOB)
                    or data['template_path']!=str(models/'blobs'/('sha256-'+primitives.TEMPLATE))
                    or data['template_sha256']!=primitives.TEMPLATE or data['texts']!=[]
                    or len(data['requests'])!=1): raise SafetyError('counter_input_schema')
            p=subprocess.run([HELPER],input=canonical(data),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                timeout=min(20,left),env=dict(os.environ,GOMAXPROCS='2'))
            if p.returncode or len(p.stdout)>768*1024: raise SafetyError('helper_exit_or_size')
            emit({'phase':'result','value':json.loads(p.stdout)});return
        category,path,body=spec['category'],spec['path'],spec['body']
        validate_http(category,path,body)
        import http.client
        c=http.client.HTTPConnection('127.0.0.1',11434,timeout=min(left,180))
        try:
            c.request('GET' if body is None else 'POST',path,None if body is None else canonical(body),
                      {'Content-Type':'application/json'})
            emit({'phase':'sent'})
            response=c.getresponse();raw=response.read(512*1024+1)
            if response.status!=200 or len(raw)>512*1024:raise SafetyError('HTTP_status_or_size')
            emit({'phase':'result','value':json.loads(raw)})
        finally:c.close()
    except BaseException as exc:
        emit({'phase':'error','error':type(exc).__name__});raise SystemExit(1)


class LiveDriver:
    is_live=True
    def __init__(self, root, runtime, budget, approval, lease, owner, monitor):
        if (Path(root)!=HDD/approval['run_id'] or budget.root!=Path(root)/'budget'
                or approval['scope']!=SCOPE):
            raise SafetyError('unique_authorized_HDD_root')
        self.root,self.runtime,self.ledger=Path(root),runtime,budget
        self.approval,self.lease,self.owner=approval,lease,owner
        self.monitor=monitor
        self.rpc=RPC(budget,self.artifact,monitor)
        self.touched=False;self.old=[];self.active=None;self.audits=[]
        self.storage_check=None
        from .wire import ContractTransport
        from .fair_final_v2_guard import PacketBudget
        self.transport=ContractTransport();self.packets=PacketBudget()

    def artifact(self, name, data):
        if self.storage_check:self.storage_check()
        self.ledger.put_artifact(name,data)

    def http(self, category, path, body=None, deadline=None):
        primitives.runtime_files(self.runtime)
        self.ledger.charge(category,path,body)
        return self.rpc.call(dict(kind='http',runtime=self.runtime.identity(),category=category,path=path,body=body),
                             min(180,(deadline or (time.monotonic()+30))-time.monotonic()))

    def begin(self, episode):
        self.ledger.episode(episode,'started');self.active=episode
        self.epoch_http=dict(self.ledger.state['http'])

    def generate(self, messages, episode, turn):
        l=self.ledger
        plan=json.loads(PLAN.read_bytes())
        inputs=json.loads((ROOT/plan['input_assets']).read_bytes())['cases']
        frozen=next((r for r in inputs if r['id']==episode),None)
        if self.active!=episode or turn!=0 or not frozen or frozen['messages']!=messages:
            raise SafetyError('outside_two_immutable_probe_requests')
        l._admit()
        if l.remaining()<150+180+40+600:raise SafetyError('cleanup_rollback_tail_reserve')
        self.packets.packet(messages)
        prep_end=time.monotonic()+150
        if self.http('get','/api/ps',deadline=prep_end).get('models')!=[]:
            raise SafetyError('nonempty_new_epoch')
        models=primitives.runtime_files(self.runtime)
        data=dict(model_path=str(models/'blobs'/primitives.MODEL_BLOB),
                  template_path=str(models/'blobs'/('sha256-'+primitives.TEMPLATE)),
                  template_sha256=primitives.TEMPLATE,requests=[dict(messages=messages)],texts=[])
        l.operation('counter')
        value=self.rpc.call(dict(kind='counter',runtime=self.runtime.identity(),input=data),min(20,prep_end-time.monotonic()))
        if value.get('input_sha256')!=hashlib.sha256(canonical(data)).hexdigest():
            raise SafetyError('counter_exact_input_SHA')
        counted=verify_count(messages,value)
        if episode=='deploy-long' and counted['token_count']<=1024:
            raise SafetyError('long_window_probe_not_long')
        self.artifact(f'{episode}/count.json',canonical(dict(messages=messages,reply=value)))
        self.touched=True;self.old=[]
        debug=self.http('render','/api/chat',dict(model=MODEL,messages=messages,stream=False,_debug_render_only=True),
                        deadline=min(prep_end,time.monotonic()+120))
        ps=self.http('get','/api/ps',deadline=prep_end)
        version=self.http('get','/api/version',deadline=prep_end)
        self.old=primitives.runner_identities(self.runtime)
        active=[m for m in ps.get('models',[]) if m.get('name')==MODEL]
        if (len(active)!=1 or active[0].get('digest')!=primitives.MANIFEST
                or active[0].get('context_length')!=16384 or len(self.old)!=1
                or version.get('version')!='0.11.11'
                or debug.get('_debug_info',{}).get('rendered_template')!=counted['rendered']):
            raise SafetyError('actual_render_context_runner_binding')
        evidence=dict(ps=ps,version=version,debug=debug,runner=self.old[0],
                      runtime=self.runtime.identity(),messages_sha256=digest(messages))
        self.artifact(f'{episode}/binding.json',canonical(evidence))
        if time.monotonic()>=prep_end:raise TimeoutError('prepare_150s')
        driver=self;rid=episode+'/t0';gen_end=time.monotonic()+180
        class Backend:
            is_live=True
            def identity(self, timeout):
                ps=driver.http('get','/api/ps',deadline=gen_end)
                active=[m for m in ps.get('models',[]) if m.get('name')==MODEL]
                if (len(active)!=1 or active[0].get('context_length')!=16384
                        or primitives.runner_identities(driver.runtime)!=driver.old):
                    raise SafetyError('identity_changed_before_send')
                return dict(model=MODEL,manifest_sha256=active[0]['digest'])
            def create(self,payload,timeout):
                if primitives.runner_identities(driver.runtime)!=driver.old:raise SafetyError('runner_dispatch_drift')
                l.reserve_request(rid,episode,counted['token_count'],512)
                return driver.http('generation','/v1/chat/completions',payload,deadline=gen_end)
        binding=ContextBinding(primitives.MANIFEST,16384,'ollama01111-vocabonly-full-render',digest(evidence),True)
        def counter(frozen):
            if frozen!=messages:raise SafetyError('frozen_request_drift')
            return counted['token_count']
        client=ControlledClient(ClientConfig(MODEL,primitives.MANIFEST,16384,timeout_seconds=180,
            max_calls=1,wall_seconds=max(.001,l.remaining()-600),max_request_bytes=65536,max_response_bytes=512*1024),
            Backend(),counter,binding,permit=LivePermit(self.approval['protocol_sha256'],REGISTRY_SHA),
            audit_sink=lambda e:self.artifact(f'{episode}/client-{e["phase"]}.json',canonical(e)))
        try:
            client.generate(messages);row=client.audit[-1]
            if row['usage_missing']:raise ClientFailure('unknown_usage')
            u=row['usage'];l.finish_request(rid,'completed',dict(prompt_tokens=u['prompt_tokens'],completion_tokens=u['completion_tokens']))
            raw=row['response']['choices'][0]['message']['content']
            self.packets.packet(raw);self.audits.append(row)
            return raw,row
        except BaseException:
            if rid in l.state['requests'] and l.state['requests'][rid]['status']=='inflight':
                l.finish_request(rid,'failed',None,True)
            l.fence('generation_or_usage_failed')
            raise

    def cleanup(self, episode):
        l=self.ledger;l.cleanup_once(episode)
        if not self.touched:
            l._append(dict(kind='cleanup',episode=episode,status='untouched-no-unload'));return
        if self.lease.owner()!=self.owner:raise SafetyError('cleanup_lease_identity')
        end=time.monotonic()+40
        ps=self.http('cleanup_get','/api/ps',deadline=end)
        current=primitives.runner_identities(self.runtime)
        if (any(m.get('name')!=MODEL or m.get('digest')!=primitives.MANIFEST for m in ps.get('models',[]))
                or not self.old or any(r not in self.old for r in current)):
            raise SafetyError('cleanup_unknown_or_unbound_runner_keep_fenced')
        response=self.http('unload','/api/chat',dict(model=MODEL,messages=[],keep_alive=0,stream=False),deadline=end)
        if response.get('done_reason')!='unload' or response.get('done') is not True:
            raise SafetyError('unload_response')
        for _ in range(6):
            ps=self.http('cleanup_get','/api/ps',deadline=end)
            remaining=primitives.runner_identities(self.runtime)
            stamps=[dict(r,observed_stamp=primitives.proc_stamp(r['pid'])) for r in self.old]
            if ps.get('models')==[] and not remaining and all(r['stamp']!=r['observed_stamp'] for r in stamps):
                values=self.monitor(force=True)
                if values['gpu_bytes']!=0:raise SafetyError('GPU_not_zero_after_unload')
                l.control('exit-barrier',episode=episode,old=self.old,process_observations=stamps,ps=ps,remaining=remaining)
                l._append(dict(kind='cleanup',episode=episode,status='verified'))
                self.touched=False;self.old=[];return
            if any(r not in self.old for r in remaining):raise SafetyError('new_runner_during_cleanup')
            time.sleep(.05)
        raise SafetyError('runner_exit_not_verified')

    def end(self, episode):
        self.cleanup(episode);self.ledger.episode(episode,'completed')

    def abort(self, episode, reason):
        self.ledger.fence(reason)
        if episode not in self.ledger.state['cleanup']:
            self.cleanup(episode)
        if self.ledger.state['episodes'][episode]=='started':self.ledger.episode(episode,'failed')


if __name__=='__main__':
    if len(sys.argv)!=4 or sys.argv[1]!='--worker':raise SystemExit('worker only; use registered launcher')
    worker(int(sys.argv[2]),float(sys.argv[3]))
