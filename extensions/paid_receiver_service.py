"""Finite byte-level UL/DL/CPU service, not a native GOSC task-wire adapter.

Call tick once per slot after submitting locally available inputs. Explicit
channel outcomes are supplied by the caller. Every frame has a CRC16; DL service
is a segmented codeword accounting model, not an implemented fragmentation PHY.
"""
from collections import defaultdict, deque
from dataclasses import dataclass
import binascii
import heapq
import math

from .receiver_pose_interface import PoseKnowledge
from .receiver_rtt_contract import RTTLane
from .receiver_summary_audit import encode, decode, unframe
from .receiver_transport_replay import batch, feedback, read_feedback


def envelope(kind, payload):
    body = bytes([kind]) + len(payload).to_bytes(2,'big') + payload
    return body + binascii.crc_hqx(body,0xffff).to_bytes(2,'big')


def open_envelope(wire):
    if len(wire)<5 or binascii.crc_hqx(wire[:-2],0xffff)!=int.from_bytes(wire[-2:],'big'):
        raise ValueError('CRC/length')
    if len(wire)!=5+int.from_bytes(wire[1:3],'big'):
        raise ValueError('Envelope size')
    return wire[0], wire[3:-2]


@dataclass(frozen=True)
class ServiceConfig:
    ul_capacity: int
    dl_capacity: int
    slot_seconds: float
    encode_seconds: float
    decode_seconds: float
    ul_rate: float = 1.
    dl_rate: float = 2.
    delay: int = 0
    ttl: int = 20
    refresh: int = 5

    def __post_init__(self):
        for name in ('ul_capacity','dl_capacity','delay','ttl','refresh'):
            v=getattr(self,name)
            if type(v) is not int or v<0:raise ValueError(name)
        if self.refresh<1 or self.ttl>511:raise ValueError('refresh/TTL')
        for name in ('slot_seconds','encode_seconds','decode_seconds','ul_rate','dl_rate'):
            v=getattr(self,name)
            if not math.isfinite(v) or v<0:raise ValueError(name)
        if min(self.slot_seconds,self.ul_rate,self.dl_rate)<=0:raise ValueError('time/rate')


class PaidReceiverService:
    def __init__(self, starts, grid, config, task_window=1, replay_tasks=False):
        if set(starts)!=set(range(len(starts))) or not 1<=len(starts)<=31:
            raise ValueError('Contiguous 1..31 agents required')
        if type(task_window) is not int or task_window<1:raise ValueError('task_window')
        self.task_window=task_window;self.task_acks=[]
        self.replay_tasks=replay_tasks;self.task_history={}
        self.c=config;self.n=len(starts);self.knowledge=PoseKnowledge(starts,grid,config.ttl)
        self.lanes=[RTTLane(k,config.delay,config.ttl,config.ul_rate) for k in starts]
        self.next_t=0;self.seq=0;self.jobs=[];self.arrivals=[];self.dl=[]
        self.cpu_free=[0.]*self.n;self.tasks=[deque() for _ in starts]
        self.task_id=[0]*self.n;self.seen=set();self.edge={};self.last_pose={}
        self.events=[];self.task_received=[];self.cost=defaultdict(float)
        for key in ('ul_uses','ul_task_bytes','ul_summary_bytes','dl_uses',
                    'dl_offered_bytes','dl_completed_bytes','dl_recipient_erasures',
                    'cpu_seconds','cpu_queue_wait_seconds','cpu_expired_summaries'):
            self.cost[key]=0

    def _cpu(self, observer, t, seconds, action, data):
        start=max(t*self.c.slot_seconds,self.cpu_free[observer])
        end=start+seconds;self.cpu_free[observer]=end
        ready=math.ceil(end/self.c.slot_seconds-1e-12)
        self.cost['cpu_seconds']+=seconds
        self.cost['cpu_queue_wait_seconds']+=start-t*self.c.slot_seconds
        self.seq+=1;heapq.heappush(self.jobs,(ready,self.seq,action,observer,data))

    def submit_task(self, sender, payload, t, rate=None):
        if t!=self.next_t or sender not in range(self.n) or not isinstance(payload,bytes):
            raise ValueError('Local task input/time')
        ident=self.task_id[sender];self.task_id[sender]+=1
        wire=envelope(192,bytes([sender])+ident.to_bytes(4,'big')+payload)
        rate=self.c.ul_rate if rate is None else rate
        if not math.isfinite(rate) or rate<=0:raise ValueError('Task rate')
        self._cpu(sender,t,self.c.encode_seconds,'task_ready',(ident,wire,rate))
        return ident

    def submit_pose(self, sender, pose, t, change_only=False):
        if t!=self.next_t or sender not in range(self.n):raise ValueError('Local pose/time')
        # Validate even when change_only could suppress the frame.
        app=encode(sender,t,0,pose)
        if pose>=self.knowledge.grid**2:raise ValueError('Pose outside grid')
        if change_only and self.last_pose.get(sender)==pose:return False
        self.last_pose[sender]=pose
        self._cpu(sender,t,self.c.encode_seconds,'pose_ready',app)
        return True

    def _enqueue_dl(self, priority, kind, wire):
        self.seq+=1
        self.cost['dl_offered_bytes']+=len(wire)
        need=math.ceil(len(wire)*8/self.c.dl_rate)
        heapq.heappush(self.dl,[priority,self.seq,kind,wire,need])

    def _receive(self, kind, receiver, wire, t):
        if kind=='summary_ack':
            for source,slot,good in read_feedback(wire):
                if source==receiver:self.lanes[source].feedback(slot,good,t)
        elif kind=='summary_snapshot':
            self.knowledge.receive_snapshot(receiver,wire,t)
        else:
            tag,payload=open_envelope(wire)
            source=payload[0];ident=int.from_bytes(payload[1:5],'big')
            if kind=='task_ack':
                assert tag==193
                if source==receiver:
                    self.tasks[source]=deque(x for x in self.tasks[source] if x[0]!=ident)
                    self.task_acks.append((receiver,ident))
            else:
                assert tag==192
                self.task_received.append((t,receiver,source,ident,payload[5:]))

    def tick(self, t, ul_ok=lambda source,kind,wire:True,
             dl_ok=lambda receiver,kind,wire:True):
        if type(t) is not int or t!=self.next_t or not 0<=t<512:
            raise ValueError('Sequential finite mission slots required')
        while self.arrivals and self.arrivals[0][0]<=t:
            _,_,kind,wire=heapq.heappop(self.arrivals)
            for receiver in range(self.n):
                if dl_ok(receiver,kind,wire):
                    self._cpu(receiver,t,self.c.decode_seconds,'received',(kind,wire))
                else:self.cost['dl_recipient_erasures']+=1
        while self.jobs and self.jobs[0][0]<=t:
            _,_,action,observer,data=heapq.heappop(self.jobs)
            if action=='task_ready':self.tasks[observer].append(data)
            elif action=='pose_ready':
                # Computation delay must not regenerate/refresh the timestamp.
                if t-decode(data,t,max_age=511)['created']<=self.c.ttl:
                    self.lanes[observer].offer_ready(data,t)
                else:self.cost['cpu_expired_summaries']+=1
            else:self._receive(data[0],observer,data[1],t)
        acks=[];changed=False
        for sender in range(self.n):
            used=0
            for ident,wire,rate in list(self.tasks[sender])[:self.task_window]:
                need=math.ceil(len(wire)*8/rate)
                if need<=self.c.ul_capacity-used:
                    used+=need;good=bool(ul_ok(sender,'task',wire))
                    self.cost['ul_task_bytes']+=len(wire)
                    if good:
                        self._enqueue_dl(0,'task_ack',envelope(193,bytes([sender])+ident.to_bytes(4,'big')))
                    if good and (sender,ident) not in self.seen:
                        self.seen.add((sender,ident));self._enqueue_dl(2,'task',wire)
                        self.task_history[sender,ident]=wire
            tx=self.lanes[sender].attempt(t,self.c.ul_capacity,used)
            if tx:
                good=bool(ul_ok(sender,'summary',tx.frame));used+=tx.ul_uses
                self.cost['ul_summary_bytes']+=len(tx.frame);acks.append((sender,t,good))
                if good:
                    item=unframe(tx.frame,t,max_age=self.c.ttl)
                    previous=self.edge.get(sender)
                    if previous is None or item['created']>previous[0]:
                        self.edge[sender]=(item['created'],tx.frame[:-2]);changed=True
            assert used<=self.c.ul_capacity
            self.cost['ul_uses']+=used
            self.events.append({'kind':'ul','t':t,'sender':sender,'ul_uses':used})
        if acks:self._enqueue_dl(1,'summary_ack',feedback(acks))
        if self.replay_tasks and t>0 and t%self.c.refresh==0:
            for wire in self.task_history.values():self._enqueue_dl(2,'task',wire)
        if changed or (t%self.c.refresh==0 and self.edge):
            apps=[v[1] for _,v in sorted(self.edge.items()) if t-v[0]<=self.c.ttl]
            if apps:self._enqueue_dl(3,'summary_snapshot',batch(apps))
        remaining=self.c.dl_capacity
        while self.dl and remaining:
            frame=heapq.heappop(self.dl);take=min(remaining,frame[4])
            remaining-=take;frame[4]-=take;self.cost['dl_uses']+=take
            self.events.append({'kind':'dl','t':t,'frame_id':frame[1],'uses':take})
            if frame[4]:heapq.heappush(self.dl,frame);break
            _,_,kind,wire,_=frame
            self.cost['dl_completed_bytes']+=len(wire)
            self.seq+=1
            heapq.heappush(self.arrivals,(t+1+self.c.delay,self.seq,kind,wire))
        self.next_t+=1

    def finish(self):
        """Censor at caller's mission end; never invent post-mission service."""
        return {'slots':self.next_t,'cost':dict(self.cost),
                'pending_tasks':sum(map(len,self.tasks)),
                'pending_dl_frames':len(self.dl),'inflight_dl_frames':len(self.arrivals),
                'pending_cpu_jobs':len(self.jobs),
                'pending_summary_generations':sum(x.pending is not None for x in self.lanes),
                'scope':'Byte-level service contracts; native task-wire/Planner adapter not integrated'}
