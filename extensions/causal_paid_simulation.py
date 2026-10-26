"""Separately named GP-v2 Planner arms; delivered local information only."""
from dataclasses import replace
from types import SimpleNamespace
import time

from gosc.schemes import lagrangian_select
from .causal_paid_service import CausalPaidService,CausalPolicy
from .paired_paid_simulation import PairedPaidSimulation,event_rng
from .wire_periodic import WirePeriodic


class CausalPaidSimulation(PairedPaidSimulation):
    def __init__(self,cfg,seed,service_config,mode='tom',arm='public',policy=None,dl_loss=.05):
        if arm not in ('public','pose','ignore','age','shuffle'):raise ValueError('Unknown arm')
        if arm!='public' and mode!='tom':raise ValueError('Paid arms require ToM')
        self.arm=arm;self.causal_policy=CausalPolicy() if policy is None else policy
        self.selection_process_seconds=0.;self.selection_calls=0
        super().__init__(cfg,seed,service_config,mode,use_pose=arm!='public',dl_loss=dl_loss)

    def make_service(self, starts, grid, config, task_window):
        return CausalPaidService(starts,grid,config,task_window,self.causal_policy)

    def _eligible(self, view, sender, t):
        k=self.service.knowledge
        return {peer:item for peer,item in k.cache[sender].items()
                if peer!=sender and peer in view.team_pos and peer in k.native[sender]
                and k.native[sender][peer].pos==tuple(view.team_pos[peer])
                and item.received<=t<=item.valid_until
                and item.created>k.native[sender][peer].created}

    def valuation_view(self, view, sender, t):
        if self.arm in ('public','ignore','age'):return view
        projected=self.service.knowledge.value_view(view,sender,t)
        if self.arm=='shuffle':
            peers=sorted(self._eligible(view,sender,t))
            poses=[projected.team_pos[k] for k in peers]
            order=event_rng(self.event_seed,206,t,sender,'local-pose-shuffle').permutation(len(peers))
            for k,j in zip(peers,order):projected.team_pos[k]=poses[int(j)]
        return projected

    def select(self, agent, known, view):
        # Charge every admission decision (also periodic / empty selections),
        # ahead of that decision's encoding jobs on the same shared CPU queue.
        self.service.valuation_work(agent.idx,view.t)
        start=time.process_time();self.selection_calls+=1
        try:
            if isinstance(self.scheme,WirePeriodic):return self.scheme.select(agent,known,view)
            groups=self.scheme.build_groups(agent,known,view)
            if self.arm=='age':
                eligible=self._eligible(view,agent.idx,view.t);ages=[]
                for peer,native in self.service.knowledge.native[agent.idx].items():
                    if peer!=agent.idx:
                        created=eligible[peer].created if peer in eligible else native.created
                        ages.append(max(0,view.t-created))
                factor=1/(1+sum(ages)/len(ages)) if ages else 1.
                groups=[replace(g,options=[replace(o,value=o.value*factor) for o in g.options]) for g in groups]
            return lagrangian_select(groups,self.cfg.symbols_per_slot,self.scheme.price)
        finally:self.selection_process_seconds+=time.process_time()-start

    def result(self):
        out=super().result()
        out.update(scheme='GP-v2_'+self.scheme.voi_mode+'_'+self.arm,
                   selection_calls=self.selection_calls,selection_process_seconds=self.selection_process_seconds,
                   compute_scope='Selection process_time measured; fixed valuation_seconds per admission reserves shared logical CPU. Projection/planning/interpreter overhead is in mission process/wall, not a measured hardware service model.',
                   scope='Prospective GP-v2 Planner calibration; not author-wire reproduction, live LLM, or confirmatory evidence')
        return out
