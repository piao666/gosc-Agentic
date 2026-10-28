"""Explicit GP-ID-BF-v1 entry point. Legacy GP-ID is untouched."""
from dataclasses import replace
import hashlib
import math
import time

from gosc.schemes import Group,Option
from .budget_feasible_selector import VERSION,select_feasible,validate_selection,selection_indices
from .information_identifiability import (InformationSimulation,ObservedCausalService,
    local_age,local_summary_trace,export_groups,selection_signature,catalog_diagnostic)
from .paid_receiver_service import envelope
from .wire_periodic import WirePeriodic

PERIODIC_VERSION='WirePeriodic-contract-v1'


def select_rule_feasible(groups,budget,price,factor,form):
    if (form not in ('scale','price') or not math.isfinite(factor) or factor<=0
            or not math.isfinite(price) or price<0):
        raise ValueError('Invalid selector parameters')
    active=groups if factor==1. or form=='price' else [
        replace(g,options=[replace(o,value=o.value*factor) for o in g.options]) for g in groups]
    effective=price/factor if form=='price' else price
    chosen,trace=select_feasible(active,budget,effective)
    return chosen,trace,selection_indices(active,chosen)


def versioned_diagnostic(d):
    version=d.get('selector_version','legacy')
    if version=='legacy':return catalog_diagnostic(d)
    if version==PERIODIC_VERSION:
        if d['groups_before_age'] is not None:raise ValueError('Periodic catalog')
        return None
    if version!=VERSION:raise ValueError('Unknown selector version')
    groups=[Group(g['kind'],[Option(o['rate'],o['bits'],o['symbols'],
        float.fromhex(o['value_hex']),o['n_records']) for o in g['options']],cell=g['cell'])
        for g in d['groups_before_age']]
    forms={};indices={}
    for form in ('scale','price'):
        selected,trace,index=select_rule_feasible(groups,d['budget'],d['base_price'],d['factor'],form)
        forms[form]=selection_signature(selected);indices[form]=index
    return dict(t=d['t'],sender=d['sender'],original_form=d['form'],selector_version=VERSION,
        selected=forms,selected_indices=indices,
        replay_matches_actual=(forms[d['form']]==d['selected'] and indices[d['form']]==d['selected_indices']),
        scale_price_same=forms['scale']==forms['price'])


class BudgetObservedService(ObservedCausalService):
    def submit_task(self,sender,payload,t,rate=None):
        ident=super().submit_task(sender,payload,t,rate)
        if self.observe:
            wire=envelope(192,bytes([sender])+ident.to_bytes(4,'big')+payload)
            self.observations.append(dict(event='task_submit',t=t,sender=sender,ident=ident,
                rate=self.c.ul_rate if rate is None else rate,payload_hex=payload.hex(),
                wire_bytes=len(wire),wire_sha256=hashlib.sha256(wire).hexdigest()))
        return ident


class BudgetInformationSimulation(InformationSimulation):
    def __init__(self,*args,**kwargs):
        self.budget_repairs=0
        super().__init__(*args,**kwargs)

    def make_service(self,starts,grid,config,task_window):
        return BudgetObservedService(starts,grid,config,task_window,self.causal_policy,observe=self.observe)

    def select(self,agent,known,view):
        self.service.valuation_work(agent.idx,view.t)
        start=time.process_time();self.selection_calls+=1
        try:
            public=self.view(agent)
            factor,stamps=local_age(self.service.knowledge,public,agent.idx,view.t,self.rule.age_source,self.observe)
            periodic=isinstance(self.scheme,WirePeriodic)
            if periodic:
                chosen=self.scheme.select(agent,known,view)
                admitted=[g for g,_ in chosen]
                used=validate_selection(admitted,chosen,self.cfg.symbols_per_slot)
                index=selection_indices(admitted,chosen)
                groups=None;version=PERIODIC_VERSION
                trace=dict(selector_version=version,path='periodic_independent',legacy_used=used,
                    final_used=used,upper_checks=[],expansions=0,bisection_steps=0)
            else:
                groups=self.scheme.build_groups(agent,known,view)
                chosen,trace,index=select_rule_feasible(groups,self.cfg.symbols_per_slot,
                    self.scheme.price,factor,self.rule.form)
                version=VERSION
            self.budget_repairs+=trace['path']=='budget_repair'
            if self.observe:
                self.decisions.append(dict(event='decision',t=view.t,sender=agent.idx,
                    arm=self.information_arm,mode=self.scheme.voi_mode,age_source=self.rule.age_source,
                    form=self.rule.form,timestamps=stamps,factor=factor,base_price=self.scheme.price,
                    summary_cache=local_summary_trace(self.service.knowledge,public,agent.idx,view.t) if self.use_pose else [],
                    effective_price=self.scheme.price/factor,budget=self.cfg.symbols_per_slot,
                    native_positions={str(k):list(v) for k,v in public.team_pos.items()},
                    valuation_positions={str(k):list(v) for k,v in view.team_pos.items()},
                    candidate_context=dict(intent_target=agent.target,
                        pending_records=[dict(created=int(r.t),pos=list(r.pos),detections=list(map(int,r.det)))
                                         for r in agent.pending_records]),
                    groups_before_age=None if groups is None else export_groups(groups),
                    periodic_admitted_groups=export_groups(admitted) if periodic else None,
                    selected=selection_signature(chosen),selected_indices=index,
                    selector_version=version,selector_trace=trace))
            return chosen
        finally:
            self.selection_process_seconds+=time.process_time()-start

    def result(self):
        out=super().result()
        out.update(scheme='GP-ID-BF-v1_'+self.scheme.voi_mode+'_'+self.information_arm,
            selector_version=PERIODIC_VERSION if isinstance(self.scheme,WirePeriodic) else VERSION,
            budget_repairs=self.budget_repairs,
            scope='Budget-selector engineering fixture only; efficacy N0; old calibration No-Go retained',
            compute_scope='Selection process_time includes legacy call, validation and repair. Logical CPU remains an explicit fixed model, not measured hardware cost.')
        return out
