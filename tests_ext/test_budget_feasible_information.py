import copy
from dataclasses import replace

import pytest
from gosc.config import Config
from extensions.budget_feasible_information import BudgetInformationSimulation,versioned_diagnostic
from extensions.paid_receiver_service import ServiceConfig
from extensions.causal_paid_service import CausalPolicy
from scripts.repro_information_identifiability import cases
from scripts.audit_budget_feasible_selector import audit_indexed,audit_submissions
from scripts.audit_information_identifiability import decision_audit,resource_audit

PLAN=dict(arms=['public-fixed','native-age','native-price','paid-ignore','paid-native-age','paid-age',
    'paid-price','paid-pose','paid-pose-native-age','paid-pose-age'],
    simple_references=['bits','aoi','periodic_k8_eps0'],fixed_diagnostic_price=1e-4,
    service=dict(ul_capacity=100,dl_capacity=2000,slot_seconds=1.,encode_seconds=.001,
                 decode_seconds=.001,ul_rate=1.,dl_rate=2.,delay=0,ttl=20,refresh=5))


@pytest.mark.parametrize('case',cases(PLAN),ids=lambda c:c['id'])
def test_all_cases_new_backend_observer_equivalence_and_independent_audit(case):
    sims=[];results=[]
    for observe in (False,True):
        cfg=Config(max_steps=12,energy_price=case['price'],filter_eps=case['eps'],sem_interval=case['k'])
        sim=BudgetInformationSimulation(cfg,27000000,ServiceConfig(**PLAN['service']),case['mode'],case['arm'],CausalPolicy(),.05,observe)
        sims.append(sim);results.append(sim.run())
    omit={'selection_process_seconds'}
    assert {k:v for k,v in results[0].items() if k not in omit}=={k:v for k,v in results[1].items() if k not in omit}
    a,b=sims
    assert a.service.events==b.service.events and a.event_field_hashes==b.event_field_hashes
    for name in ('sense_rng','plan_rng','dl_rng'):
        assert getattr(a,name).bit_generator.state==getattr(b,name).bit_generator.state
    assert a.channel.rng.bit_generator.state==b.channel.rng.bit_generator.state
    assert (a.chan_rng.t,a.chan_rng.k)==(b.chan_rng.t,b.chan_rng.k)
    events=b.observation();resource_audit(events,results[1],PLAN);decision_audit(events,results[1])
    audit_submissions(events)
    for d in b.decisions:
        audit_indexed(d)
        diagnostic=versioned_diagnostic(d)
        if diagnostic is not None:assert diagnostic['replay_matches_actual']
    assert a.observation()==[]


def sample_decision():
    o=dict(rate=1.,bits=20,symbols=20,n_records=0,value=1.,value_hex=(1.).hex())
    return dict(selector_version='BF-selector-v1',budget=100,
        groups_before_age=[dict(kind='CONF',cell=1,options=[o,dict(o,rate=2.,symbols=10)])],
        selected=[dict(kind='CONF',cell=1,**{k:o[k] for k in ('rate','bits','symbols','n_records')})],
        selected_indices=[dict(group_index=0,option_index=0)],
        selector_trace=dict(selector_version='BF-selector-v1',path='legacy_feasible',legacy_used=20,
                            final_used=20,upper_checks=[]))


def test_independent_audit_rejects_same_group_two_different_members_under_budget():
    d=sample_decision();audit_indexed(d)
    d['selected'].append(dict(d['selected'][0],rate=2.,symbols=10))
    d['selected_indices'].append(dict(group_index=0,option_index=1))
    with pytest.raises(ValueError,match='Repeated selected group'):audit_indexed(d)


@pytest.mark.parametrize('change',['version','index','symbols','trace'])
def test_independent_index_audit_rejects_tampering(change):
    d=sample_decision()
    if change=='version':d['selector_version']='unknown'
    if change=='index':d['selected_indices'][0]['option_index']=7
    if change=='symbols':d['selected'][0]['symbols']=19
    if change=='trace':d['selector_trace']['final_used']=0
    with pytest.raises(ValueError):audit_indexed(d)


def test_legacy_diagnostic_dispatch_and_unknown_version_rejection():
    assert versioned_diagnostic(dict(groups_before_age=None)) is None
    with pytest.raises(ValueError):versioned_diagnostic(dict(selector_version='future'))


def test_actual_submitted_payload_tampering_is_rejected():
    sim=BudgetInformationSimulation(Config(max_steps=12),27000000,ServiceConfig(**PLAN['service']),observe=True)
    sim.run();events=copy.deepcopy(sim.observation())
    submit=next(e for e in events if e['event']=='task_submit')
    submit['payload_hex']=submit['payload_hex'][:-2]+'ff'
    with pytest.raises(ValueError):audit_submissions(events)
