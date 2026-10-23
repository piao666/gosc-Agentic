"""Native Planner/semantic task bridge with a separately named paid wire model.

Not author-byte-exact reproduction. No training or cost-matched effect claim.
At each slot, native planning precedes service completion; new receptions first
affect planning at the next slot. Old EVID/CONF replay is idempotent per receiver.
"""
import math
from types import SimpleNamespace
import numpy as np

from gosc.simulator import Simulation,teammate_points
from gosc.schemes import lagrangian_select
from .paid_receiver_service import PaidReceiverService,open_envelope
from .receiver_pose_interface import NativePose
from .native_task_wire import WireGOSC,encode_packet,decode_packet


class NativePaidSimulation(Simulation):
    def __init__(self,cfg,seed,service_config,mode='tom',use_pose=False,record_traj=False):
        super().__init__(cfg,'gosc',seed,record_traj=record_traj)
        if cfg.max_steps>512 or cfg.grid>32 or cfg.dl_delay or cfg.dl_loss:
            raise ValueError('Use service delay/loss callbacks, finite grid/mission only')
        if service_config.ul_capacity!=cfg.symbols_per_slot:
            raise ValueError('Native and service UL budgets must agree')
        self.scheme=WireGOSC(cfg,self.channel,mode)
        self.service=PaidReceiverService(self.team_pos,cfg.grid,service_config,
                                        task_window=cfg.grid**2+2,replay_tasks=True)
        self.use_pose=use_pose;self._tx={};self._outstanding=set();self._local_seen=set()
        self._ack_index=0;self._received_index=0;self._edge_seen=set()
        self.local=[]
        for k in range(cfg.n_agents):
            state=SimpleNamespace(cfg=cfg,sensor=self.sensor,t=0,Lc=self.Lc.copy(),
                                  declared=self.declared.copy(),team_pos=dict(self.team_pos),
                                  team_intent={})
            state.teammates=lambda idx,s=state:teammate_points(cfg,s.team_pos,s.team_intent,idx)
            self.local.append(state)

    def view(self,agent):
        return self.local[agent.idx]

    def declare(self,cell,t):
        # Objective bookkeeping at edge only; never clear recipients' private state.
        if not self.declared[cell]:
            self.declared[cell]=True
            if cell in self.world.victims:self.located_time[cell]=t
            else:self.false_declarations+=1

    def phase_decide(self,t):
        for state in self.local:state.t=t
        super().phase_decide(t)

    def _edge_packet(self,pkt,t):
        for rec in pkt.records:self.sensor.apply(self.Lc,rec)
        if pkt.records:self.team_pos[pkt.sender]=pkt.records[-1].pos
        if pkt.intent is not None:self.team_intent[pkt.sender]=pkt.intent
        if pkt.confirm is not None:self.declare(pkt.confirm,t)
        for cell in np.flatnonzero((self.Lc.reshape(-1)>=self.thr)&~self.declared):
            self.declare(int(cell),t)

    def _local_packet(self,receiver,source,ident,payload):
        key=(receiver,source,ident)
        if key in self._local_seen:return
        pkt=decode_packet(payload,self.cfg)
        if pkt.sender!=source:raise ValueError('Transport/payload sender mismatch')
        self._local_seen.add(key);state=self.local[receiver];agent=self.agents[receiver]
        for rec in pkt.records:
            self.sensor.apply(state.Lc,rec)
            if receiver==source:self.sensor.apply(agent.pending_llr,rec,sign=-1.)
        if pkt.records:
            rec=pkt.records[-1];state.team_pos[source]=rec.pos
            stamps=dict(self.service.knowledge.native[receiver])
            stamps[source]=NativePose(rec.t,rec.pos)
            self.service.knowledge.receive_native(receiver,stamps)
        if pkt.intent is not None:
            state.team_intent[source]=pkt.intent
            if receiver==source:agent.shared_intent=pkt.intent
        if pkt.confirm is not None:state.declared[pkt.confirm]=True
        state.declared|=state.Lc.reshape(-1)>=self.thr
        agent.confirmed_pending-=set(np.flatnonzero(state.declared).tolist())

    def select(self,agent,known,view):
        groups=self.scheme.build_groups(agent,known,view)
        return lagrangian_select(groups,self.cfg.symbols_per_slot,self.scheme.price)

    def decode_ul(self,sender,kind,wire,rate,snr):
        return self.channel.decodes(rate,snr,n=math.ceil(len(wire)*8/rate))

    def decode_dl(self,receiver,kind,wire):
        return True

    def phase_communicate(self,t):
        snrs={}
        for a in self.agents:
            mean=self.channel.mean_snr(a.pos)
            snrs[a.idx]=mean*self.chan_rng.exponential()
            # Stop-and-wait batch prevents duplicate queue admission before ACK.
            if not any(k==a.idx for k,_ in self._outstanding):
                view=self.view(a)
                if self.use_pose:view=self.service.knowledge.value_view(view,a.idx,t)
                chosen=self.select(a,snrs[a.idx] if self.cfg.csit else mean,view)
                for g,o in chosen:
                    pkt=self.scheme.packet(a,g,o,t);payload=encode_packet(pkt,self.cfg)
                    ident=self.service.submit_task(a.idx,payload,t,rate=o.rate)
                    key=(a.idx,ident);self._tx[key]=pkt;self._outstanding.add(key)
            if self.use_pose:
                self.service.submit_pose(a.idx,a.pos[0]*self.cfg.grid+a.pos[1],t,change_only=True)
        def uplink(sender,kind,wire):
            rate=self.service.c.ul_rate
            if kind=='task':
                _,body=open_envelope(wire);ident=int.from_bytes(body[1:5],'big')
                rate=next(x[2] for x in self.service.tasks[sender] if x[0]==ident)
            return self.decode_ul(sender,kind,wire,rate,snrs[sender])
        self.service.tick(t,ul_ok=uplink,dl_ok=self.decode_dl)
        for key in sorted(self.service.seen-self._edge_seen):
            _,body=open_envelope(self.service.task_history[key])
            self._edge_packet(decode_packet(body[5:],self.cfg),t)
        self._edge_seen=set(self.service.seen)
        for source,ident in self.service.task_acks[self._ack_index:]:
            key=(source,ident)
            if key not in self._outstanding:continue
            a=self.agents[source];pkt=self._tx[key]
            if pkt.confirm is not None:
                a.acked_confirms=getattr(a,'acked_confirms',set())|{pkt.confirm}
            if pkt.intent is not None:a.acked_intent=pkt.intent
            for rec in pkt.records:
                a.pending_records.remove(rec);self.sensor.apply(a.queued_llr,rec,sign=-1.)
            self._outstanding.remove(key)
        self._ack_index=len(self.service.task_acks)
        for _,receiver,source,ident,payload in self.service.task_received[self._received_index:]:
            self._local_packet(receiver,source,ident,payload)
        self._received_index=len(self.service.task_received)
        self.curve[t]=len(self.located_time)
        if len(self.located_time)==self.cfg.n_victims:
            self.done_at=t+1;return True
        for a in self.agents:a.step()
        return False

    def result(self):
        out=super().result()
        # Do not report inherited zero/abstract counters as paid resources.
        for key in ('bits','symbols','delivered_bits','dl_symbols'):out.pop(key,None)
        out.update(scheme='native_paid_'+self.scheme.voi_mode+('_pose' if self.use_pose else '_public'),
                   service=self.service.finish(),wire_model='GP-v1 explicit semantic records + service envelope/CRC16',
                   scope='Adapter/short contract run; not original historical wire or task-effect evidence')
        return out
