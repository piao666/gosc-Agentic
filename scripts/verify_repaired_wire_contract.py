"""Derived control-only queue contracts. Not closed-loop historical replay."""
import argparse
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gosc.config import Config
from gosc.schemes import Group,Option,lagrangian_select
from extensions.budget_feasible_information import BudgetInformationSimulation
from extensions.information_identifiability import selection_signature
from extensions.paid_receiver_service import ServiceConfig
from extensions.causal_paid_service import CausalPolicy
from scripts.repro_information_calibration import write_gzip_jsonl
from scripts.audit_budget_feasible_selector import audit_indexed,audit_submissions
from scripts.audit_information_identifiability import resource_audit,decision_audit


def require(test,message):
    if not test:raise ValueError(message)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--frozen',type=Path,required=True);a=p.parse_args()
    require(os.name=='posix' and os.getuid()==8301880 and str(ROOT)=='/home/u202520081000097/jupyterlab/Paper/gosc'
            and os.environ.get('GOSC_OUTPUT_DIR'),'Registered HPC only')
    f=json.loads(a.frozen.read_text());out=Path(os.environ['GOSC_OUTPUT_DIR'])
    for name,sha in f['source_sha256'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,'Frozen source changed')
    path=a.frozen.parent/f['samples']['path']
    require(hashlib.sha256(path.read_bytes()).hexdigest()==f['samples_sha256'],'Sample hash')
    with gzip.open(path,'rt') as stream:samples=[json.loads(line) for line in stream]
    rows=[]
    for sample in samples:
        if sample['kind']!='violation':continue
        d=sample['decision'];old=f['legacy_plan']
        # Restrict to control groups to isolate the repaired-admission/wire
        # contract without injecting historical evidence into current belief.
        groups=[Group(g['kind'],[Option(o['rate'],o['bits'],o['symbols'],float.fromhex(o['value_hex']),o['n_records'])
                    for o in g['options']],cell=g['cell']) for g in d['groups_before_age'] if g['kind'] in ('CONF','INTENT')]
        require(d['base_price']==0. and d['factor']==1.,'Control-only contract domain')
        require(selection_signature(lagrangian_select(groups,d['budget'],0.))==d['selected'],'Derived pre-repair control selection changed')
        sim=BudgetInformationSimulation(Config(max_steps=4,energy_price=0.,filter_eps=.02),27000000,
            ServiceConfig(**old['service']),mode=d['mode'],policy=CausalPolicy(**old['policy']),observe=True)
        sim._start()  # The service harness deliberately bypasses run()/planning.
        # Native communicate advances every agent after service, so a harness
        # bypassing planning must provide valid stationary targets explicitly.
        for agent in sim.agents:agent.target=agent.pos[0]*sim.cfg.grid+agent.pos[1]
        target=d['candidate_context']['intent_target']
        if target is not None:sim.agents[0].target=target
        # A deterministic injected catalog, only at sender0/slot0. It is a
        # contract harness, explicitly excluded from all task-effect datasets.
        sim.scheme.build_groups=lambda agent,known,view:groups if agent.idx==0 and view.t==0 else []
        for t in range(3):
            sim.t=t
            for view in sim.local:view.t=t
            sim.phase_communicate(t)
        result=sim.result();events=sim.observation()
        first=next(e for e in events if e['event']=='decision' and e['sender']==0 and e['t']==0)
        require(first['selector_trace']['path']=='budget_repair' and first['selected'],'Repair branch not exercised')
        for decision in sim.decisions:audit_indexed(decision)
        decision_audit(events,result);ledger=resource_audit(events,result,old)
        submissions=audit_submissions(events)
        require(submissions==len(first['selected']),'Actual repaired admission')
        require(any(e['event']=='ul_attempt' and e['message_kind']=='task' for e in events),'No actual task UL')
        observation=write_gzip_jsonl(out/('derived-'+str(len(rows))+'.jsonl.gz'),events)
        rows.append(dict(source_locator=sample['locator'],status='passed',derived_control_catalog=True,
            source_sender_remapped_to=0,source_time_remapped_to=0,selected=first['selected'],trace=first['selector_trace'],
            submissions=submissions,ledger=ledger,observation=observation))
    require(len(rows)==7,'Derived contract count')
    report=dict(status='passed',scope='Seven synthetic control-only queue contracts derived from original violations; not original missions, task quality or efficacy samples',
        rows=rows,frozen_sha256=hashlib.sha256(a.frozen.read_bytes()).hexdigest(),efficacy_N=0,new_mission_runs=0)
    with (out/'wire_contracts.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(status='passed',derived_contracts=len(rows),efficacy_N=0)))


if __name__=='__main__':main()
