"""Policy-independent exogenous potential fields for the GP-v1 paid model.

Random fields are only consumed by the physical sensing/channel/planner layer;
estimators receive no seed/field accessor. Coupling is not author-history replay.
"""
import hashlib
import json
import math
from types import MethodType
import numpy as np
from gosc.channel import fbl_error
from .native_paid_adapter import NativePaidSimulation
from .wire_periodic import WirePeriodic


def world_fingerprint(sim):
    world={'victims':sorted(map(int,sim.world.victims)),
           'starts':[[int(v) for v in a.pos] for a in sim.agents],
           'deadlines':{str(k):int(v) for k,v in sim.world.deadline.items()}}
    return hashlib.sha256(json.dumps(world,sort_keys=True).encode()).hexdigest()


def event_rng(seed,domain,t,agent,kind='',wire=b''):
    key=hashlib.sha256(kind.encode()+b'\0'+wire).digest()
    words=[int.from_bytes(key[i:i+4],'little') for i in range(0,32,4)]
    return np.random.default_rng([seed,domain,t,agent,*words])


class FadingField:
    def __init__(self,sim,seed):self.sim=sim;self.seed=seed;self.t=None;self.k=0
    def exponential(self):
        if self.t!=self.sim.t:self.t=self.sim.t;self.k=0
        k=self.k;self.k+=1
        if k>=self.sim.cfg.n_agents:raise RuntimeError('Unexpected fading consumption')
        return float(event_rng(self.seed,202,self.t,k).exponential())


class PairedPaidSimulation(NativePaidSimulation):
    def __init__(self,cfg,seed,service_config,mode='tom',use_pose=False,dl_loss=.05,record_traj=False):
        if not 0<=dl_loss<=1:raise ValueError('DL probability')
        super().__init__(cfg,seed,service_config,'bits' if mode=='periodic' else mode,use_pose,record_traj)
        if mode=='periodic':
            if use_pose:raise ValueError('Periodic does not use pose valuation')
            self.scheme=WirePeriodic(cfg,self.channel)
        self.event_seed=seed;self.event_dl_loss=dl_loss
        self.input_world_sha256=world_fingerprint(self);self.event_field_hashes={}
        self.chan_rng=FadingField(self,seed);self._sense_t=None;self._sense_k=0

        def sense(pos,sensor,unused_rng):
            if self._sense_t!=self.t:self._sense_t=self.t;self._sense_k=0
            k=self._sense_k;self._sense_k+=1
            if k>=cfg.n_agents:raise RuntimeError('Unexpected sensor consumption')
            field=event_rng(seed,201,self.t,k).random((cfg.grid,cfg.grid))
            if self.t==0:self.event_field_hashes[str(k)]=hashlib.sha256(field.tobytes()).hexdigest()
            sx,sy=sensor.window(pos)
            prob=np.where(self.world.mask[sx,sy],self.world.p_detect,self.world.p_false_alarm)
            xs,ys=np.nonzero(field[sx,sy]<prob)
            return tuple(int((x+sx.start)*cfg.grid+y+sy.start) for x,y in zip(xs,ys))
        self.world.sense=sense
        for a in self.agents:
            old=a.plan;idx=a.idx
            def plan(this,p,others,unused_rng,original=old,k=idx):
                return original(p,others,event_rng(seed,203,self.t,k))
            a.plan=MethodType(plan,a)

    def select(self,agent,known,view):
        if isinstance(self.scheme,WirePeriodic):return self.scheme.select(agent,known,view)
        return super().select(agent,known,view)

    def decode_ul(self,sender,kind,wire,rate,snr):
        if not self.channel.fbl:return math.log2(1.+snr)>=rate
        u=event_rng(self.event_seed,204,self.t,sender,kind,wire).random()
        return bool(u>=float(fbl_error(math.ceil(len(wire)*8/rate),rate,snr*self.channel.gap)))

    def decode_dl(self,receiver,kind,wire):
        return bool(event_rng(self.event_seed,205,self.t,receiver,kind,wire).random()>=self.event_dl_loss)

    def result(self):
        out=super().result()
        out.update(world_sha256=self.input_world_sha256,event_field_hashes=self.event_field_hashes,
                   event_coupling='GP-v1 CRN-v1: sensor201/fade202/plan203/FBL204/DL205',
                   scope='Prospective common-wire Planner calibration; not historical replay or confirmatory task-effect evidence')
        return out
