"""Task-only profile. Probe authority is neither edited nor accepted here.

Agent/parser/client/wire/persistent journal and bounded I/O are reused. Only
task plan, authorization, fresh epoch and request accounting are specialized.
No dataset loader or gold object is admitted to the online domain.
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
from . import fair_final_v2_live as probe
from . import live_driver as primitives
from .application import PrivateView
from .client import ClientConfig, ClientFailure, ContextBinding, ControlledClient, LivePermit
from .execution_safety import Ledger, Limits, SafetyError, canonical, digest
from .fair_final_v2 import REGISTRY_SHA, TEMPLATE_SHA
from .fair_final_v2_guard import FairLedger, FixtureDriver, PacketBudget
from .wire import ContractTransport

ROOT=Path(__file__).resolve().parents[2]
AUTH=ROOT/'research/protocols/masbench_t3rv2t_authorization_2026-11-26.json'
PLAN=ROOT/'research/protocols/masbench_t3rv2t_plan_2026-11-26.json'
SCOPE='T3-R-v2-T original four exposed development families only'
CAPS=dict(generation=48,render=48,get=152,cleanup_get=56,unload=8,lifecycle_get=128)
MODEL=probe.MODEL;HELPER=probe.HELPER
BINARY_SHA=probe.BINARY_SHA
file_sha=probe.file_sha
HDD=Path('/hdd/u202520081000097/gosc-t3rv2t-runs')
MATERIAL_FILES=(
    'extensions/masbench_reasoning/fair_final_v2_task.py',
    'extensions/masbench_reasoning/fair_final_v2_task_campaign.py',
    'extensions/masbench_reasoning/fair_final_v2_runtime.py',
    'extensions/masbench_reasoning/fair_final_v2.py',
    'extensions/masbench_reasoning/fair_final_v2_prompt.txt',
    'extensions/masbench_reasoning/fair_final_v2_live.py',
    'extensions/masbench_reasoning/fair_final_v2_guard.py',
    'extensions/masbench_reasoning/application.py',
    'extensions/masbench_reasoning/client.py',
    'extensions/masbench_reasoning/execution_safety.py',
    'extensions/masbench_reasoning/live_driver.py',
    'extensions/masbench_reasoning/wire.py',
    'experiments_ext/masbench_t3rv2_live_probe.py',
    'experiments_ext/masbench_t3rv2t_task.py',
    'research/protocols/masbench_t3rv2t_plan_2026-11-26.json')


def validate_plan(plan):
    if len(plan)!=8 or len({r['id'] for r in plan})!=8:raise SafetyError('eight_unique_episodes')
    families=[]
    for i in range(4):
        pair=plan[2*i:2*i+2]
        if pair[0]['family']!=pair[1]['family'] or pair[0]['family'] in families:raise SafetyError('four_unique_families')
        families.append(pair[0]['family'])
        order=['Full','No-A2A'] if i%2==0 else ['No-A2A','Full']
        if [r['condition'] for r in pair]!=order:raise SafetyError('predeclared_condition_order')
        for row in pair:
            if set(row)!={'id','family','condition','partition','private_view_sha256'} or row['partition']!='task':
                raise SafetyError('task_plan_schema')
    return plan


def validate_task_approval(a,run_id,plan):
    validate_plan(plan)
    if (a.get('schema')!='t3rv2t-task-approval-v1' or a.get('approved') is not True
        or a.get('scope')!=SCOPE or a.get('run_id')!=run_id or a.get('generation_cap')!=48
        or a.get('synthetic_cap')!=0 or a.get('http_caps')!=CAPS or a.get('wall_seconds')!=18360
        or a.get('monitoring_approved') is not True or a.get('plan_sha256')!=digest(plan)
        or a.get('baseline_pid') is None or not a.get('baseline_stamp')):
        raise SafetyError('task_specific_approval_required')
    if a.get('previous_probe_generations')!=2 or a.get('old_2000s_deadline_reopened') is not False:
        raise SafetyError('history_cannot_refund_or_reopen')
    return a


def require_approval():
    run=Path(os.environ.get('GOSC_RUN_DIR','/'))
    if run.parent!=ROOT/'research/sync/runs':raise SafetyError('registered_task_run_required')
    plan=json.loads(PLAN.read_bytes())['episodes']
    a=validate_task_approval(json.loads(primitives.reject_links(AUTH).read_bytes()),run.name,plan)
    required=set(MATERIAL_FILES)
    if not required<=set(a.get('bound_files',{})):raise SafetyError('task_source_bindings_missing')
    for name,h in a['bound_files'].items():
        p=primitives.reject_links(ROOT/name)
        if ROOT not in p.parents or probe.file_sha(p)!=h:raise SafetyError('task_source_drift')
    receipt=ROOT/a['contract_receipt']
    receipt=primitives.reject_links(receipt)
    tested=json.loads(receipt.read_bytes())
    if ROOT not in receipt.parents or probe.file_sha(receipt)!=a['contract_sha256'] or not tested['passed']:
        raise SafetyError('task_contract_required')
    if any(tested.get('source_files',{}).get(name)!=a['bound_files'][name] for name in required):
        raise SafetyError('approved_source_must_equal_tested_source')
    parent=json.loads(PLAN.read_bytes())['parent_probe']
    if a.get('parent_probe_ledger_sha256')!=parent['ledger_sha256']:raise SafetyError('historical_parent_binding')
    return a


def load_private_bundle(path,expected_sha,plan):
    """Only an offline-exported four-view bundle; never a native dataset.

    Strict schema rejects gold/supporting_facts/full records. Future offline
    exporter must bind each pair to the original T3 private-view digest.
    """
    validate_plan(plan);p=primitives.reject_links(path)
    if p.stat().st_size>1024**2 or probe.file_sha(p)!=expected_sha:raise SafetyError('view_bundle_SHA_or_size')
    obj=json.loads(p.read_bytes())
    if set(obj)!={'schema','families'} or obj['schema']!='four-local-views-v1':raise SafetyError('no_gold_online_schema')
    families=[r['family'] for r in plan[::2]]
    if len(obj['families'])!=4 or [r.get('family') for r in obj['families']]!=families:raise SafetyError('bundle_family_order')
    result={}
    for row,meta in zip(obj['families'],plan[::2]):
        if set(row)!={'family','views'} or len(row['views'])!=2:raise SafetyError('view_pair_schema')
        for v in row['views']:
            if set(v)!={'name','partner','question','information'}:raise SafetyError('no_record_or_gold_in_view')
        views=[PrivateView(**v) for v in row['views']]
        if [v.name for v in views]!=['Alice','Bob'] or views[0].question!=views[1].question:
            raise SafetyError('private_pair_identity')
        if digest([asdict(v) for v in views])!=meta['private_view_sha256']:raise SafetyError('original_views_changed')
        result[row['family']]=views
    return result


class TaskLedger(FairLedger):
    def __init__(self,root,plan,*,fixture,identity=None,wall=18360,artifact_bytes=64*1024**2):
        validate_plan(plan)
        self.fixture=bool(fixture)
        basic=[{k:r[k] for k in ('id','family','condition','partition')} for r in plan]
        # Existing FairLedger implements monotonic slots, 24/condition, 48/task,
        # hash chain, artifact reservation and no-replay. No new budget engine.
        super().__init__(root,basic,limits=Limits(requests=48,metadata=440,input_tokens=761856,
            output_tokens=24576,wall_seconds=wall,operation_seconds=180,artifact_bytes=artifact_bytes),caps=CAPS)
        self.task_plan=plan
        binding=digest(dict(plan=plan,fixture=fixture,identity=identity))
        if 'task_binding' not in self.state:self._append(dict(kind='task-init',binding=binding,fixture=fixture))
        elif self.state['task_binding']!=binding:self.close();raise SafetyError('task_identity_or_mode_changed')
    def _apply(self,e):
        if e['kind']=='task-init':
            self.state.update(task_binding=e['binding'],task_fixture=e['fixture'],operations=dict(counter=0,precount=0,start=0,stop=0));return
        if e['kind']=='task-operation':self.state['operations'][e['name']]+=1;return
        if e['kind']=='task-control':return
        if e['kind']=='cleanup':self.state['cleanup'][e['episode']]=e['status'];return
        super()._apply(e)
    def control(self,label,**data):self._append(dict(kind='task-control',label=label,mono=time.monotonic(),**data))
    def operation(self,name):
        cap=48 if name=='counter' else 8 if name=='precount' else 2
        if name not in self.state['operations'] or self.state['operations'][name]>=cap:raise SafetyError('task_operation_cap')
        if name in ('counter','precount'):self._admit()
        self._append(dict(kind='task-operation',name=name))
    def cleanup_once(self,episode):self.start_cleanup(episode)
    def charge(self,category,path,body=None):
        probe.validate_http(category,path,body)
        if category not in ('cleanup_get','unload','lifecycle_get'):self._admit()
        if self.state['http'][category]>=CAPS[category] or sum(self.state['http'].values())>=440:raise SafetyError('task_HTTP_cap')
        rid=None
        if category=='generation':
            inflight=[k for k,r in self.state['requests'].items() if r['status']=='inflight']
            if len(inflight)!=1 or inflight[0] in self.state['http_generated_ids']:raise SafetyError('one_reserved_send')
            rid=inflight[0]
        self._append(dict(kind='v2-http',category=category,method='GET' if body is None else 'POST',path=path,
                          request_id=rid,body_sha256=digest(body),fake_operation=False))
    def reserve_request(self,rid,episode,p,out):
        existing=list(self.state['requests'].values())
        if sum(r['episode']==episode for r in existing)>=6:raise SafetyError('six_slots_per_episode')
        condition=self.plan[episode]['condition']
        if sum(self.plan[r['episode']]['condition']==condition for r in existing)>=24:raise SafetyError('24_each_condition')
        super().reserve_request(rid,episode,p,out)
    def begin_in_order(self,episode):
        first=next((r['id'] for r in self.task_plan if self.state['episodes'][r['id']]=='unstarted'),None)
        if episode!=first or any(v=='started' for v in self.state['episodes'].values()):raise SafetyError('episode_order_or_overlap')


class TaskFixtureDriver(FixtureDriver):
    accounting_scope='task_fixture: synthetic counter units; not qwen or real task usage'
    def __init__(self,ledger,outputs,**kwargs):
        if not ledger.fixture:raise SafetyError('fixture_cannot_use_live_ledger')
        super().__init__(ledger,outputs,**kwargs)
    def begin(self,episode):
        self.ledger.begin_in_order(episode)
        self.service.identity=(episode,'fixture');self.service.bound_identity=self.service.identity
        self.service.next_runner=1+list(self.ledger.plan).index(episode)
        super().begin(episode)


def engineering_complete(plan,results,ledger,*,require_real):
    errors=[]
    if len(results)!=8 or [r['id'] for r in results]!=[r['id'] for r in plan]:errors.append('full_plan_not_completed')
    if require_real and ledger.fixture:errors.append('fixture_not_real_task')
    if ledger.state['fenced']:errors.append('persistent_infrastructure_fence')
    for row in results:
        if not row.get('completed') or row.get('error') or row.get('cleanup_error') or len(row.get('slots',[]))!=6:errors.append('incomplete_episode')
        expected=next((p for p in plan if p['id']==row['id']),{})
        if row.get('condition')!=expected.get('condition') or ledger.state['episodes'].get(row['id'])!='completed':errors.append('episode_identity_or_state')
        if [(s.get('turn'),s.get('speaker'),s.get('stage')) for s in row.get('slots',[])]!=[(i,'Alice' if i%2==0 else 'Bob','exchange' if i<4 else 'local_final') for i in range(6)]:errors.append('slot_identity')
        if any(s.get('status')!='returned' for s in row.get('slots',[])):errors.append('incomplete_slot')
        if not row.get('accounting',{}).get('scope','').startswith('task_'):errors.append('wrong_usage_label')
        if require_real and not row.get('accounting',{}).get('scope','').startswith('task_real:'):errors.append('fixture_usage_not_real')
        if ledger.state['cleanup'].get(row['id']) not in ('verified','verified-fixture-only'):errors.append('cleanup_unverified')
    if len(ledger.state['requests'])!=48 or any(r['status']!='completed' or r.get('observed_usage') is None for r in ledger.state['requests'].values()):
        errors.append('48_known_requests_required')
    return dict(passed=not errors,errors=sorted(set(errors)))


def scientific_gate(plan,results,ledger,paired,l2_verified_families,*,infrastructure=None):
    engineering=engineering_complete(plan,results,ledger,require_real=True)
    positive=[p for p in paired.get('pairs',[]) if p.get('delta') is not None and p['delta']>0 and p['valid_both_conditions']]
    full=paired.get('conditions',{}).get('Full',{})
    delivered={r['id'] for r in results if any(m.get('delivered') for m in r.get('messages',[]))}
    reviewed=set(l2_verified_families)
    required=('runtime_bound','resource_monitor_passed','rollback_verified','independent_audit_passed','all_outputs_mirrored','deadline_met')
    infra_pass=all((infrastructure or {}).get(k) is True for k in required)
    eligible=(engineering['passed'] and infra_pass and paired.get('complete_pairs') is True and paired.get('N_families')==4
              and full.get('both_correct_families',0)>=2 and (paired.get('Delta_F1') or 0)>=.10
              and len(positive)>=2 and bool(reviewed) and reviewed<={r['family'] for r in plan}
              and bool(delivered))
    return dict(passed=bool(eligible),engineering=engineering,
                infrastructure_passed=infra_pass,
                L2='external independent evidence review required; E self-report is insufficient',
                independent_confirmation=False)

# Bounded RPC/worker is an authorization-specialized copy of the already tested
# probe I/O, retaining its process/size/timeout implementation unchanged. Its
# global approval function and module entry are this independent task profile.
verify_count=probe.verify_count
validate_http=probe.validate_http
class RPC:
    def __init__(self, ledger, artifact, monitor):
        self.ledger,self.artifact,self.monitor=ledger,artifact,monitor
        self.sequence=0

    def call(self, spec, timeout):
        require_approval()
        if len(canonical(spec))>1024**2:raise SafetyError('RPC_input_cap')
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



class TaskDriver(probe.LiveDriver):
    accounting_scope='task_real: exact deployed qwen usage and actual task HTTP'
    def __init__(self,root,runtime,budget,approval,lease,owner,monitor):
        if budget.fixture or approval['scope']!=SCOPE or Path(root)!=HDD/approval['run_id']:
            raise SafetyError('task_real_scope_or_root')
        self.root,self.runtime,self.ledger=Path(root),runtime,budget
        self.approval,self.lease,self.owner,self.monitor=approval,lease,owner,monitor
        self.rpc=RPC(budget,self.artifact,monitor);self.storage_check=None
        self.touched=False;self.old=[];self.active=None;self.audits=[]
        self.transport=ContractTransport();self.packets=PacketBudget()
    def begin(self,episode):
        self.ledger.begin_in_order(episode)
        if self.touched or self.old:raise SafetyError('previous_epoch_not_clean')
        self.transport=ContractTransport(episode_id=list(self.ledger.plan).index(episode)+1)
        self.packets=PacketBudget();self.next_turn=0;self.audits=[]
        super().begin(episode)
    def generate(self, messages, episode, turn):
        l=self.ledger
        if self.active!=episode or turn!=self.next_turn or turn not in range(6):
            raise SafetyError('task_slot_order')
        l.slot(episode,turn,'preparing')
        self.next_turn+=1
        l._admit()
        if l.remaining()<150+180+40+1000:raise SafetyError('cleanup_rollback_tail_reserve')
        self.packets.packet(messages)
        prep_end=time.monotonic()+150
        if not self.touched and self.http('get','/api/ps',deadline=prep_end).get('models')!=[]:
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
        self.artifact(f'{episode}/t{turn}/count.json',canonical(dict(messages=messages,reply=value)))
        previous=list(self.old)
        self.touched=True
        debug=self.http('render','/api/chat',dict(model=MODEL,messages=messages,stream=False,_debug_render_only=True),
                        deadline=min(prep_end,time.monotonic()+120))
        ps=self.http('get','/api/ps',deadline=prep_end)
        version=self.http('get','/api/version',deadline=prep_end)
        self.old=primitives.runner_identities(self.runtime)
        if previous and self.old!=previous:raise SafetyError('runner_changed_within_episode')
        active=[m for m in ps.get('models',[]) if m.get('name')==MODEL]
        if (len(active)!=1 or active[0].get('digest')!=primitives.MANIFEST
                or active[0].get('context_length')!=16384 or len(self.old)!=1
                or version.get('version')!='0.11.11'
                or debug.get('_debug_info',{}).get('rendered_template')!=counted['rendered']):
            raise SafetyError('actual_render_context_runner_binding')
        evidence=dict(ps=ps,version=version,debug=debug,runner=self.old[0],
                      runtime=self.runtime.identity(),messages_sha256=digest(messages))
        self.artifact(f'{episode}/t{turn}/binding.json',canonical(evidence))
        if time.monotonic()>=prep_end:raise TimeoutError('prepare_150s')
        driver=self;rid=episode+f'/t{turn}';gen_end=time.monotonic()+180
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
                l.reserve_dispatch(rid,episode,counted['token_count'])
                return driver.http('generation','/v1/chat/completions',payload,deadline=gen_end)
        binding=ContextBinding(primitives.MANIFEST,16384,'ollama01111-vocabonly-full-render',digest(evidence),True)
        def counter(frozen):
            if frozen!=messages:raise SafetyError('frozen_request_drift')
            return counted['token_count']
        client=ControlledClient(ClientConfig(MODEL,primitives.MANIFEST,16384,timeout_seconds=180,
            max_calls=1,wall_seconds=max(.001,l.remaining()-600),max_request_bytes=65536,max_response_bytes=512*1024),
            Backend(),counter,binding,permit=LivePermit(self.approval['protocol_sha256'],REGISTRY_SHA),
            audit_sink=lambda e:self.artifact(f'{episode}/t{turn}/client-{e["phase"]}.json',canonical(e)))
        try:
            client.generate(messages);row=client.audit[-1]
            if row['usage_missing']:raise ClientFailure('unknown_usage')
            u=row['usage'];l.finish_request(rid,'completed',dict(prompt_tokens=u['prompt_tokens'],completion_tokens=u['completion_tokens']))
            raw=row['response']['choices'][0]['message']['content']
            self.packets.packet(raw);self.audits.append(row)
            l.slot(episode,turn,'returned')
            return raw,row
        except BaseException:
            if rid in l.state['requests'] and l.state['requests'][rid]['status']=='inflight':
                l.finish_request(rid,'failed',None,True)
            l.fence('generation_or_usage_failed')
            raise


if __name__=='__main__':
    if len(sys.argv)!=4 or sys.argv[1]!='--worker':raise SystemExit('task worker only')
    worker(int(sys.argv[2]),float(sys.argv[3]))
