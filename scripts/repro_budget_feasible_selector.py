"""Registered HPC-only prepare/replay/short-fixture acceptance, efficacy N0."""
import argparse
from collections import defaultdict,deque
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gosc.config import Config
from gosc.schemes import Group,Option,lagrangian_select
from extensions.budget_feasible_selector import VERSION,select_feasible,selection_indices
from extensions.budget_feasible_information import BudgetInformationSimulation,select_rule_feasible,versioned_diagnostic
from extensions.information_identifiability import selection_signature
from extensions.causal_paid_service import CausalPolicy
from extensions.paid_receiver_service import ServiceConfig
from scripts.repro_information_calibration import write_gzip_jsonl
from scripts.repro_information_identifiability import cases


def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(test,message):
    if not test:raise RuntimeError(message)
def save(path,data):
    with Path(path).open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')


def sources(config):
    return sorted({*ROOT.joinpath('gosc').glob('*.py'),*ROOT.joinpath('extensions').glob('*.py'),
        ROOT/'scripts/repro_budget_feasible_selector.py',ROOT/'scripts/audit_budget_feasible_selector.py',
        ROOT/'scripts/repro_information_calibration.py',ROOT/'scripts/repro_information_identifiability.py',
        ROOT/'scripts/audit_information_identifiability.py',
        ROOT/'tests_ext/test_budget_feasible_selector.py',ROOT/'tests_ext/test_budget_feasible_information.py',
        ROOT/'tests_ext/test_budget_selector_runner.py',config})


def check_sources(frozen):
    for name,sha in frozen['source_sha256'].items():require(digest(ROOT/name)==sha,'Source changed: '+name)


def cap(out,plan):
    size=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    require(size<=plan['output_cap_bytes'],'Output cap; artifacts retained')
    return size


def make(frozen,case,seed,observe):
    p=frozen['legacy_plan'];steps=frozen['plan']['fixture_steps']
    cfg=Config(max_steps=steps,energy_price=case['price'],filter_eps=case['eps'],sem_interval=case['k'])
    return BudgetInformationSimulation(cfg,seed,ServiceConfig(**p['service']),case['mode'],case['arm'],
                                       CausalPolicy(**p['policy']),p['dl_loss'],observe)


def prepare(config,contracts,out):
    p=read(config)
    require(p['user_authorized'] and p['protocol_id']=='BF-acceptance-v1' and p['efficacy_N']==0
        and not p['formal_test'] and not p['training'],'Scope')
    require((p['feasible_per_edge_per_case'],p['historical_failure_count'],p['expected_feasible_catalogs'],
        p['fixture_seeds'],p['fixture_steps'],p['fixture_rows'],p['workers'],p['numeric_threads'])==
        (8,7,192,[27000000,27000001],24,52,1,1),'Frozen coverage')
    require(p['output_cap_bytes']==67108864 and p['minimum_free_bytes']==268435456,'Resource plan')
    require(shutil.disk_usage(out).free>=p['minimum_free_bytes'],'Free disk gate')
    st=read(contracts/'status.json');require(st['status']=='completed' and st['exit_code']==0,'Contracts not passed')
    require(read(contracts/'manifest.json')['kind']=='test','Not a contract run')
    junit=ET.parse(contracts/'outputs/pytest.xml').getroot()
    require(list(junit.iter('testcase')) and not any(list(junit.iter(k)) for k in ('failure','error','skipped')),'JUnit incomplete')
    names={t.attrib.get('name','').split('[')[0] for t in junit.iter('testcase')}
    require({'test_valid_legacy_return_preserves_identity_order_and_inputs',
        'test_all_cases_new_backend_observer_equivalence_and_independent_audit',
        'test_independent_audit_rejects_same_group_two_different_members_under_budget',
        'test_bounded_repair_and_exhaustion_are_explicit'}<=names,'Missing required contracts')
    snapshot={x['path']:x['remote_sha256'] for x in read(contracts/'source_snapshot.json')['files']}
    shas={x.relative_to(ROOT).as_posix():digest(x) for x in sources(config)}
    require(all(snapshot.get(k)==v for k,v in shas.items()),'Contract source identity')
    result_path=ROOT/p['input_results'];diagnosis_path=ROOT/p['historical_diagnosis']
    require(digest(result_path)==p['input_results_sha256'] and digest(diagnosis_path)==p['historical_diagnosis_sha256'],'Historical inputs')
    data=read(result_path);oldplan=data['frozen']['plan']
    first=defaultdict(list);last=defaultdict(lambda:deque(maxlen=8));bad=[];inputs={}
    expected={(e['seed'],e['case_id'],e['t'],e['sender']) for e in read(diagnosis_path)['examples']}
    for row in data['rows']:
        file=result_path.parent/row['observation']['path']
        require(digest(file)==row['observation']['sha256'],'Historical observation SHA')
        inputs[file.relative_to(ROOT).as_posix()]=row['observation']['sha256']
        with gzip.open(file,'rt') as stream:
            for lineno,line in enumerate(stream,1):
                d=json.loads(line)
                if d['event']!='decision' or d['groups_before_age'] is None:continue
                locator=dict(seed=row['seed'],case_id=row['case_id'],t=d['t'],sender=d['sender'],
                    observation=file.relative_to(ROOT).as_posix(),line=lineno)
                item=dict(locator=locator,decision=d)
                if sum(x['symbols'] for x in d['selected'])>d['budget']:
                    item['kind']='violation';bad.append(item)
                else:
                    item['kind']='feasible'
                    if len(first[row['case_id']])<8:first[row['case_id']].append(item)
                    last[row['case_id']].append(item)
    found={(s['locator']['seed'],s['locator']['case_id'],s['locator']['t'],s['locator']['sender']) for s in bad}
    require(found==expected and len(bad)==7,'Historical violation coverage')
    feasible=[]
    for c in cases(oldplan):
        if c['mode']=='periodic':continue
        combined=first[c['id']]+list(last[c['id']])
        require(len(combined)==16 and len({(x['locator']['observation'],x['locator']['line']) for x in combined})==16,'Feasible coverage')
        feasible.extend(combined)
    samples=write_gzip_jsonl(out/'catalogs.jsonl.gz',[*bad,*feasible])
    integrity=read(ROOT/'research/logs/information-calibration-2026-10-27/source_integrity_checks.json')
    protected={e['path']:e['current_normalized_lf_sha256'] for e in integrity['files']}
    for name,sha in protected.items():require(digest(ROOT/name)==sha,'Legacy source protection')
    frozen=dict(plan=p,legacy_plan=oldplan,cases=cases(oldplan),samples=samples,samples_sha256=samples['sha256'],
        source_sha256=shas,protected_sha256=protected,historical_observation_sha256=inputs,
        contracts_run=contracts.name,junit_sha256=digest(contracts/'outputs/pytest.xml'),
        config_sha256=digest(config),fixture_worlds={})
    for seed in p['fixture_seeds']:frozen['fixture_worlds'][str(seed)]=make(frozen,frozen['cases'][0],seed,False).input_world_sha256
    save(out/'frozen.json',frozen);cap(out,p)
    print(json.dumps(dict(samples=len(bad)+len(feasible),violations=len(bad),feasible=len(feasible),scope='Engineering only, N0')))


def replay(frozen,path,out):
    check_sources(frozen);sample_path=path.parent/frozen['samples']['path']
    require(digest(sample_path)==frozen['samples_sha256'],'Sample SHA')
    rows=[]
    with gzip.open(sample_path,'rt') as stream:
        for line in stream:
            sample=json.loads(line);d=sample['decision']
            groups=[Group(g['kind'],[Option(o['rate'],o['bits'],o['symbols'],float.fromhex(o['value_hex']),o['n_records'])
                for o in g['options']],cell=g['cell']) for g in d['groups_before_age']]
            factor=d['factor'];form=d['form'];price=d['base_price']
            # This preprocessing is exactly the old scale/price interface.
            from dataclasses import replace
            active=groups if factor==1. or form=='price' else [replace(g,options=[replace(o,value=o.value*factor) for o in g.options]) for g in groups]
            effective=price/factor if form=='price' else price
            old=lagrangian_select(active,d['budget'],effective)
            require(selection_signature(old)==d['selected'],'Original logged selector replay')
            start=time.process_time();wall=time.monotonic()
            chosen,trace=select_feasible(active,d['budget'],effective)
            elapsed=time.process_time()-start;duration=time.monotonic()-wall
            repeated,trace2=select_feasible(active,d['budget'],effective)
            same=selection_signature(chosen)==selection_signature(repeated) and trace==trace2
            identity=len(chosen)==len(old) and all(g is h and o is q for (g,o),(h,q) in zip(chosen,old))
            if sample['kind']=='feasible':require(identity,'Changed feasible identity/order')
            else:require(trace['path']=='budget_repair','Historical failure not repaired')
            new=copy.deepcopy(d);new.update(selected=selection_signature(chosen),selected_indices=selection_indices(active,chosen),
                selector_version=VERSION,selector_trace=trace,periodic_admitted_groups=None)
            require(versioned_diagnostic(new)['replay_matches_actual'],'Versioned replay')
            rows.append(dict(locator=sample['locator'],kind=sample['kind'],decision=new,repeat_identical=same,
                identity_preserved=identity,process_seconds=elapsed,wall_seconds=duration))
            cap(out,frozen['plan'])
    save(out/'replay.json',dict(frozen_sha256=digest(path),input_sha256=frozen['samples_sha256'],rows=rows,efficacy_N=0))
    cap(out,frozen['plan']);print(json.dumps(dict(rows=len(rows),efficacy_N=0)))


def noise(sim):
    return dict(rng={k:getattr(sim,k).bit_generator.state for k in ('sense_rng','plan_rng','dl_rng')},
        channel=sim.channel.rng.bit_generator.state,fading=[sim.chan_rng.t,sim.chan_rng.k],fields=sim.event_field_hashes)


def fixtures(frozen,path,out):
    check_sources(frozen);rows=[]
    for seed in frozen['plan']['fixture_seeds']:
        for case in frozen['cases']:
            for observe in (False,True):
                start=time.monotonic();cpu=time.process_time()
                sim=make(frozen,case,seed,observe);result=sim.run()
                row=dict(seed=seed,case=case,observe=observe,result=result,noise_state=noise(sim))
                if observe:
                    name=str(seed)+'-'+case['id']
                    row['observation']=write_gzip_jsonl(out/(name+'.jsonl.gz'),sim.observation())
                    row['diagnostics']=[x for d in sim.decisions if (x:=versioned_diagnostic(d)) is not None]
                row.update(process_seconds=time.process_time()-cpu,end_to_end_wall_seconds=time.monotonic()-start)
                save(out/(str(seed)+'-'+case['id']+'-'+str(int(observe))+'.json'),row)
                rows.append(row);cap(out,frozen['plan'])
    save(out/'fixtures.json',dict(frozen_sha256=digest(path),rows=rows,efficacy_N=0,formal_test=False,training=False))
    cap(out,frozen['plan']);print(json.dumps(dict(rows=len(rows),efficacy_N=0)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['prepare','replay','fixtures'],required=True)
    p.add_argument('--config',type=Path,default=ROOT/'research/protocols/budget_selector_acceptance_v1.json')
    p.add_argument('--contracts-run',type=Path);p.add_argument('--frozen',type=Path);a=p.parse_args()
    require(os.name=='posix' and os.getuid()==8301880 and str(ROOT)=='/home/u202520081000097/jupyterlab/Paper/gosc'
        and os.environ.get('GOSC_OUTPUT_DIR'),'Registered HPC only')
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    if a.mode=='prepare':
        require(a.contracts_run is not None,'Contracts required');prepare(a.config,a.contracts_run,out)
    else:
        require(a.frozen is not None,'Frozen required');f=read(a.frozen)
        (replay if a.mode=='replay' else fixtures)(f,a.frozen,out)


if __name__=='__main__':main()
