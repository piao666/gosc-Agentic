"""GP-v2 service: causal retry floor, paid valuation work, bounded blind replay.

The floor assumes no queue, not an RTT upper bound. Replay uses edge history only,
never unpriced receiver delivery knowledge. GP-v1 remains the default elsewhere.
"""
from dataclasses import dataclass
import math

from .paid_receiver_service import PaidReceiverService
from .receiver_rtt_contract import RTTLane


@dataclass(frozen=True)
class CausalPolicy:
    replay_age: int = 20
    replay_limit: int = 2
    replay_frames_per_refresh: int = 6
    valuation_seconds: float = .001

    def __post_init__(self):
        for key in ('replay_age','replay_limit','replay_frames_per_refresh'):
            v=getattr(self,key)
            if type(v) is not int or v<0:raise ValueError(key)
        if not math.isfinite(self.valuation_seconds) or self.valuation_seconds<0:
            raise ValueError('valuation_seconds')


def feedback_floor(config):
    return 1+config.delay+math.ceil(config.decode_seconds/config.slot_seconds-1e-12)


class CausalLane(RTTLane):
    def __init__(self, sender, config):
        super().__init__(sender,config.delay,config.ttl,config.ul_rate)
        self.retry_slots=feedback_floor(config)

    def attempt(self, now, capacity, original_used=0):
        tx=super().attempt(now,capacity,original_used)
        if tx:self.next_retry=now+self.retry_slots
        return tx

    def feedback(self, tx_slot, success, now):
        if now<tx_slot+self.retry_slots:raise ValueError('Feedback before decode completion floor')
        return super().feedback(tx_slot,success,now)


class CausalPaidService(PaidReceiverService):
    def __init__(self, starts, grid, config, task_window=1, policy=None):
        super().__init__(starts,grid,config,task_window,replay_tasks=True)
        self.policy=CausalPolicy() if policy is None else policy
        self.retry_slots=feedback_floor(config)
        self.lanes=[CausalLane(k,config) for k in starts]
        self.task_next={};self.accepted_at={};self.replays={};self.last_replayed={}
        self.replay_log=[];self.attempt_log=[];self.cpu_log=[]
        self.cost['valuation_cpu_seconds']=0.

    def _cpu(self, observer, t, seconds, action, data):
        super()._cpu(observer,t,seconds,action,data)
        ready=math.ceil(self.cpu_free[observer]/self.c.slot_seconds-1e-12)
        self.cpu_log.append(dict(t=t,observer=observer,action=action,seconds=seconds,ready=ready))

    def valuation_work(self, sender, t):
        if t!=self.next_t:raise ValueError('Valuation clock')
        self._cpu(sender,t,self.policy.valuation_seconds,'valuation',None)
        self.cost['valuation_cpu_seconds']+=self.policy.valuation_seconds

    def _job(self, action, observer, data, t):
        if action!='valuation':super()._job(action,observer,data,t)

    def _task_allowed(self, sender, ident, t):
        return t>=self.task_next.get((sender,ident),0)

    def _task_attempted(self, sender, ident, t):
        self.task_next[sender,ident]=t+self.retry_slots
        self.attempt_log.append(dict(t=t,sender=sender,ident=ident))

    def _task_accepted(self, sender, ident, t):
        self.accepted_at[sender,ident]=t

    def _replay(self, t):
        p=self.policy
        if not t or t%self.c.refresh:return
        # Least recently offered first, ties acceptance time / identity. Age is
        # edge acceptance age, NOT source creation age and not refreshed by replay.
        keys=[k for k in self.task_history if t-self.accepted_at[k]<=p.replay_age
              and self.replays.get(k,0)<p.replay_limit]
        keys.sort(key=lambda k:(self.last_replayed.get(k,-1),self.accepted_at[k],k))
        # Do not enqueue another copy of an already queued/partially served wire.
        queued={frame[3] for frame in self.dl if frame[2]=='task'}
        offered=0
        for k in keys:
            wire=self.task_history[k]
            if wire in queued:continue
            if offered>=p.replay_frames_per_refresh:break
            self._enqueue_dl(2,'task',wire);queued.add(wire);offered+=1
            self.replays[k]=self.replays.get(k,0)+1;self.last_replayed[k]=t
            self.replay_log.append(dict(t=t,sender=k[0],ident=k[1],number=self.replays[k],bytes=len(wire)))

    def finish(self):
        out=super().finish()
        out.update(protocol='GP-v2-causal-bounded',retry_floor_slots=self.retry_slots,
                   replay_offers=len(self.replay_log),
                   replay_exhausted_items=sum(self.replays.get(k,0)>=self.policy.replay_limit for k in self.task_history),
                   replay_aged_out_items=sum(self.next_t-1-self.accepted_at[k]>self.policy.replay_age for k in self.task_history),
                   scope='Finite shared CPU/UL/DL model with blind bounded catchup; no delivery guarantee')
        return out
