"""Explicit privileged diagnostic masks and event-indexed CRN; not a deployed estimator."""
import hashlib
import json
from types import MethodType, SimpleNamespace
import numpy as np
from gosc.simulator import Simulation
from gosc.schemes import GOSC, SCHEMES
from gosc.voi import TeamModel as NativeTeamModel
import gosc.schemes as schemes

def project_view(sim, private=False, positions=False):
    agents=[]
    for j,a in enumerate(sim.agents):
        agents.append(SimpleNamespace(pos=a.pos if positions else sim.team_pos[j],
            pending_llr=a.pending_llr if private else np.zeros_like(sim.Lc),
            confirmed_pending=a.confirmed_pending if private else set()))
    return SimpleNamespace(cfg=sim.cfg,sensor=sim.sensor,t=sim.t,Lc=sim.Lc,
        declared=sim.declared,team_pos=sim.team_pos,team_intent=sim.team_intent,agents=agents)

class MaskedGOSC(GOSC):
    def __init__(self,cfg,channel,private,positions,name):
        super().__init__(cfg,channel,name=name)
        self.allow_private=private;self.allow_positions=positions
    def build_groups(self,agent,snr_mean,sim):
        native=schemes.TeamModel
        def factory(view,sender,temperature):
            return NativeTeamModel(project_view(view,self.allow_private,self.allow_positions),sender,temperature)
        schemes.TeamModel=factory
        try:return super().build_groups(agent,snr_mean,sim)
        finally:schemes.TeamModel=native

def register():
    masks={'diag_receiver_private':(True,False),'diag_receiver_positions':(False,True),
           'diag_receiver_both':(True,True),'diag_receiver_public_projection':(False,False)}
    for name,(private,positions) in masks.items():
        if name in SCHEMES:continue
        SCHEMES[name]=lambda cfg,channel,p=private,x=positions,n=name:MaskedGOSC(cfg,channel,p,x,n)
register()

def world_fingerprint(sim):
    world={'victims':sorted(map(int,sim.world.victims)),
           'starts':[[int(v) for v in a.pos] for a in sim.agents],
           'deadlines':{str(k):int(v) for k,v in sim.world.deadline.items()}}
    return hashlib.sha256(json.dumps(world,sort_keys=True).encode()).hexdigest()

class EventChannel:
    def __init__(self,sim,seed):self.sim=sim;self.seed=seed;self.t=None;self.k=0
    def exponential(self,scale=1.0,size=None):
        assert size is None
        t=self.sim.t
        if t!=self.t:self.t=t;self.k=0
        k=self.k;self.k+=1
        assert k<self.sim.cfg.n_agents
        return float(np.random.default_rng([self.seed,202,t,k]).exponential(scale))

class EventSimulation(Simulation):
    def __init__(self,cfg,scheme,seed):
        assert not cfg.llm_agents
        assert cfg.dl_loss==0 and cfg.dl_delay==0
        super().__init__(cfg,scheme,seed)
        self.input_world_sha256=world_fingerprint(self);self.event_field_hashes={}
        self._sense_t=None;self._sense_k=0
        def sense(pos,sensor,unused_rng):
            t=self.t
            if self._sense_t!=t:self._sense_t=t;self._sense_k=0
            k=self._sense_k;self._sense_k+=1
            assert k<self.cfg.n_agents
            field=np.random.default_rng([seed,201,t,k]).random((self.cfg.grid,self.cfg.grid))
            if t==0:self.event_field_hashes[str(k)]=hashlib.sha256(field.tobytes()).hexdigest()
            sx,sy=sensor.window(pos)
            prob=np.where(self.world.mask[sx,sy],self.world.p_detect,self.world.p_false_alarm)
            xs,ys=np.nonzero(field[sx,sy]<prob)
            return tuple(int((x+sx.start)*self.cfg.grid+y+sy.start) for x,y in zip(xs,ys))
        self.world.sense=sense
        self.chan_rng=EventChannel(self,seed)
        for a in self.agents:
            original=a.plan;idx=a.idx
            def plan(this,p,others,unused_rng,old=original,k=idx):
                return old(p,others,np.random.default_rng([seed,203,self.t,k]))
            a.plan=MethodType(plan,a)
