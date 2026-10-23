"""Read-only observation wrappers for existing paid calibration replay.

Shadow selection does not advance another world. No production policy, clock,
channel result or service rule is modified. Require original result equality.
"""
from collections import Counter,defaultdict
import hashlib
import math
from types import MethodType
from gosc.schemes import lagrangian_select
from .paired_paid_simulation import PairedPaidSimulation
from .paid_receiver_service import open_envelope
from .receiver_summary_audit import unframe
from .receiver_transport_replay import read_feedback


def signature(chosen,payload_only=False):
    return sorted((g.kind,-1 if g.cell is None else g.cell,o.n_records) if payload_only else
                  (g.kind,-1 if g.cell is None else g.cell,o.rate,o.bits,o.n_records)
                  for g,o in chosen)


def options(groups):
    return {(g.kind,-1 if g.cell is None else g.cell,o.rate,o.bits,o.n_records):o.value
            for g in groups for o in g.options}


class ServiceTrace:
    def __init__(self,service):
        self.s=service;self.frames={};self.ul=[];self.cpu=defaultdict(Counter)
        self.receipts=Counter();self.attempts=Counter();self.data_enqueued=set();self.received=set()
        self.first_good={};self.ack_first=set();self.feedback_delays=[]
        self.summary_unobserved=set()
        enqueue=service._enqueue_dl;cpu=service._cpu;receive=service._receive;tick=service.tick
        trace=self

        def enqueue_wrapper(this,priority,kind,wire):
            label=kind
            if kind=='task':
                _,body=open_envelope(wire);key=(body[0],int.from_bytes(body[1:5],'big'))
                label='task_replay' if key in trace.data_enqueued else 'task_initial'
                trace.data_enqueued.add(key)
            enqueue(priority,kind,wire)
            trace.frames[this.seq]={'id':this.seq,'kind':label,'enqueued':this.next_t,
                'bytes':len(wire),'need':math.ceil(len(wire)*8/this.c.dl_rate),'served':0,
                'first_service':None,'last_service':None,'completed':None}

        def cpu_wrapper(this,observer,t,seconds,action,data):
            label=action
            if action=='received':label='decode_'+data[0]
            start=max(t*this.c.slot_seconds,this.cpu_free[observer]);end=start+seconds
            ready=math.ceil(end/this.c.slot_seconds-1e-12)
            row=trace.cpu[label];row['jobs']+=1;row['work_seconds']+=seconds
            row['queue_wait_seconds']+=start-t*this.c.slot_seconds
            row['ready_minus_submit_slots']+=ready-t
            row['rounding_slack_seconds']+=ready*this.c.slot_seconds-end
            cpu(observer,t,seconds,action,data)

        def receive_wrapper(this,kind,receiver,wire,t):
            trace.receipts[kind]+=1
            if kind in ('task','task_ack'):
                _,body=open_envelope(wire);source=body[0];ident=int.from_bytes(body[1:5],'big')
                if kind=='task':
                    key=(receiver,source,ident)
                    trace.receipts['task_duplicate' if key in trace.received else 'task_unique']+=1
                    trace.received.add(key)
                else:
                    trace.receipts['task_ack_self' if receiver==source else 'task_ack_other']+=1
                    key=('task',source,ident)
                    if receiver==source and key not in trace.ack_first:
                        trace.ack_first.add(key)
                        trace.feedback_delays.append({'kind':'task','source':source,'received':t,
                            'first_success':trace.first_good[key],'delay':t-trace.first_good[key]})
            elif kind=='summary_ack':
                for source,tx_slot,good in read_feedback(wire):
                    if source==receiver:
                        trace.summary_unobserved.discard((source,tx_slot))
                        trace.feedback_delays.append({'kind':'summary','source':source,
                            'received':t,'tx_slot':tx_slot,'good':good,'delay':t-tx_slot,
                            'configured_RTO':1+this.c.delay})
            previous=dict(this.knowledge.cache[receiver]) if kind=='summary_snapshot' else None
            receive(kind,receiver,wire,t)
            if previous is not None:
                for peer,item in this.knowledge.cache[receiver].items():
                    old=previous.get(peer)
                    # _accept creates a new immutable ReceivedPose only when
                    # this frame was accepted. Unchanged same-slot entries may
                    # belong to another snapshot and must not be counted again.
                    if item is old:continue
                    if old is None or item.created>old.created:trace.receipts['summary_new_generation']+=1
                    elif item.received==t and item.created==old.created:trace.receipts['summary_same_generation']+=1

        def tick_wrapper(this,t,ul_ok=lambda *args:True,dl_ok=lambda *args:True):
            before=len(this.events)
            def ul_wrapper(sender,kind,wire):
                rate=this.c.ul_rate
                if kind=='task':
                    _,body=open_envelope(wire);ident=int.from_bytes(body[1:5],'big')
                    rate=next(x[2] for x in this.tasks[sender] if x[0]==ident)
                    key=(kind,sender,ident);already_edge=(sender,ident) in this.seen
                else:
                    ident=unframe(wire,t,max_age=this.c.ttl)['created']
                    key=(kind,sender,ident);already_edge=sender in this.edge and this.edge[sender][0]>=ident
                attempt=trace.attempts[key];trace.attempts[key]+=1
                label=kind+'_first' if attempt==0 else kind+('_retry_after_edge' if already_edge else '_retry_before_edge')
                good=bool(ul_ok(sender,kind,wire))
                if good and key not in trace.first_good:trace.first_good[key]=t
                prior=sum(source==sender for source,slot in trace.summary_unobserved) if kind=='summary' else 0
                if kind=='summary':trace.summary_unobserved.add((sender,t))
                trace.ul.append({'t':t,'sender':sender,'kind':kind,'generation':ident,'attempt':attempt+1,
                                 'category':label,'edge_had_before':already_edge,'good':good,
                                 'unobserved_summary_feedback_before':prior,
                                 'bytes':len(wire),'uses':math.ceil(len(wire)*8/rate)})
                return good
            tick(t,ul_wrapper,dl_ok)
            for event in this.events[before:]:
                if event['kind']!='dl':continue
                row=trace.frames[event['frame_id']];row['served']+=event['uses']
                if row['first_service'] is None:row['first_service']=t
                row['last_service']=t
                if row['served']==row['need']:row['completed']=t
                assert row['served']<=row['need']

        service._enqueue_dl=MethodType(enqueue_wrapper,service)
        service._cpu=MethodType(cpu_wrapper,service)
        service._receive=MethodType(receive_wrapper,service)
        service.tick=MethodType(tick_wrapper,service)

    def result(self):
        s=self.s
        assert sum(x['uses'] for x in self.ul)==s.cost['ul_uses']
        assert sum(x['bytes'] for x in self.ul if x['kind']=='task')==s.cost['ul_task_bytes']
        assert sum(x['bytes'] for x in self.ul if x['kind']=='summary')==s.cost['ul_summary_bytes']
        assert sum(x['served'] for x in self.frames.values())==s.cost['dl_uses']
        assert sum(x['bytes'] for x in self.frames.values())==s.cost['dl_offered_bytes']
        assert sum(x['bytes'] for x in self.frames.values() if x['completed'] is not None)==s.cost['dl_completed_bytes']
        assert math.isclose(sum(x['work_seconds'] for x in self.cpu.values()),s.cost['cpu_seconds'],abs_tol=1e-8)
        assert math.isclose(sum(x['queue_wait_seconds'] for x in self.cpu.values()),s.cost['cpu_queue_wait_seconds'],abs_tol=1e-8)
        return {'ul_attempts':self.ul,'dl_frames':list(self.frames.values()),
                'cpu':dict(self.cpu),'receipts':dict(self.receipts),'feedback_delays':self.feedback_delays,
                'ledger_identities':'passed'}


class ReviewSimulation(PairedPaidSimulation):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.trace=ServiceTrace(self.service);self.decisions=[]

    def select(self,agent,known,view):
        # Called at the actual valuation boundary, after the original projection.
        public=self.local[agent.idx]
        actual_groups=self.scheme.build_groups(agent,known,view)
        actual=lagrangian_select(actual_groups,self.cfg.symbols_per_slot,self.scheme.price)
        if not self.use_pose:return actual
        shadow_groups=self.scheme.build_groups(agent,known,public)
        shadow=lagrangian_select(shadow_groups,self.cfg.symbols_per_slot,self.scheme.price)
        a,b=options(actual_groups),options(shadow_groups)
        if set(a)!=set(b):raise RuntimeError('Pose changed candidate identities')
        peers=[]
        for peer,pos in public.team_pos.items():
            if peer==agent.idx:continue
            item=self.service.knowledge.cache[agent.idx].get(peer)
            native=self.service.knowledge.native[agent.idx].get(peer)
            reason='absent'
            if item is not None:
                if native is None or native.pos!=tuple(pos):reason='ledger_mismatch'
                elif not item.received<=self.t<=item.valid_until:reason='expired_or_not_arrived'
                elif item.created<=native.created:reason='not_newer'
                elif item.pos==tuple(pos):reason='newer_same_position'
                else:reason='newer_changed_position'
            changed=tuple(view.team_pos[peer])!=tuple(pos)
            assert changed==(reason=='newer_changed_position')
            peers.append({'peer':peer,'reason':reason,'changed':changed,
                          'age':None if item is None else self.t-item.created,
                          'native_age':None if native is None else self.t-native.created})
        values=[{'key':list(k),'actual':a[k],'public':b[k]} for k in sorted(a)]
        self.decisions.append({'t':self.t,'sender':agent.idx,'peers':peers,'values':values,
            'exact_value_changed':any(x['actual']!=x['public'] for x in values),
            'material_value_changed':any(abs(x['actual']-x['public'])>1e-12+1e-9*max(abs(x['actual']),abs(x['public'])) for x in values),
            'actual_selection':signature(actual),'public_shadow_selection':signature(shadow),
            'selection_changed':signature(actual)!=signature(shadow),
            'payload_choice_changed':signature(actual,True)!=signature(shadow,True)})
        return actual
