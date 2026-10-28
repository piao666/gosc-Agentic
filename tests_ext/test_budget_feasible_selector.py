import copy
import math
import sys

import pytest
from gosc.schemes import Group, Option, lagrangian_select
from extensions import budget_feasible_selector as bf


def catalog(value=1.):
    return [Group('CONF',[Option(2.,152,76,value)],cell=k) for k in (1,2)]


def test_valid_legacy_return_preserves_identity_order_and_inputs():
    groups=catalog(); before=copy.deepcopy(groups)
    old=lagrangian_select(groups,200,0.)
    got,trace=bf.select_feasible(groups,200,0.)
    assert all(g is h and o is p for (g,o),(h,p) in zip(old,got)) and len(got)==len(old)
    assert groups==before and trace['path']=='legacy_feasible'
    assert bf.selection_indices(groups,got)==[dict(group_index=i,option_index=0) for i in range(2)]


@pytest.mark.parametrize('budget',[0,1,75,76,100,151,152,200])
@pytest.mark.parametrize('value',[0.,-1.,1.,.37740635744655543*76,1e6,1e-300])
def test_finite_ties_budget_and_nonpositive_values(budget,value):
    groups=catalog(value); got,trace=bf.select_feasible(groups,budget,0.)
    assert sum(o.symbols for _,o in got)<=budget
    assert len({id(g) for g,_ in got})==len(got)
    bf.validate_selection(groups,got,budget)


@pytest.mark.parametrize('budget,price,symbols,value',[
    (True,0.,1,1.),(-1,0.,1,1.),(1.5,0.,1,1.),(1,float('nan'),1,1.),
    (1,float('inf'),1,1.),(1,-1.,1,1.),(1,True,1,1.),
    (1,0.,0,1.),(1,0.,-1,1.),(1,0.,1.5,1.),(1,0.,True,1.),
    (1,0.,1,float('nan')),(1,0.,1,float('inf'))])
def test_invalid_inputs_fail_closed(budget,price,symbols,value):
    with pytest.raises((ValueError,TypeError)):
        bf.select_feasible([Group('EVID',[Option(1.,1,symbols,value)])],budget,price)


def test_empty_groups_oversized_and_shared_option_identity():
    assert bf.select_feasible([],0,0.)[0]==[]
    assert bf.select_feasible([Group('EVID',[])],10,0.)[0]==[]
    o=Option(1.,1,1,1.)
    groups=[Group('CONF',[o],cell=i) for i in (1,2)]
    assert len(bf.select_feasible(groups,2,0.)[0])==2
    with pytest.raises(ValueError):bf.select_feasible([groups[0],groups[0]],2,0.)
    with pytest.raises(TypeError):bf.select_feasible(iter(groups),2,0.)


def test_postcondition_rejects_same_group_two_options_and_cloned_member():
    a,b=Option(1.,1,1,1.),Option(2.,1,1,2.)
    g=Group('EVID',[a,b])
    with pytest.raises(ValueError):bf.validate_selection([g],[(g,a),(g,b)],10)
    with pytest.raises(ValueError):bf.validate_selection([g],[(g,copy.copy(a))],10)


def test_bounded_repair_and_exhaustion_are_explicit(monkeypatch):
    groups=catalog()
    monkeypatch.setattr(bf,'legacy_select',lambda gs,*args:[(g,g.options[0]) for g in gs])
    got,trace=bf.select_feasible(groups,100,0.)
    assert trace['path']=='budget_repair' and sum(o.symbols for _,o in got)<=100
    monkeypatch.setattr(bf,'_pick',lambda gs,lam: ([(g,g.options[0]) for g in gs],152))
    with pytest.raises(bf.SelectorFailure,match='exhaust'):
        bf.select_feasible(groups,100,0.)


def test_overflow_and_stagnant_expansion_fail_not_empty_success(monkeypatch):
    groups=catalog(sys.float_info.max)
    monkeypatch.setattr(bf,'legacy_select',lambda gs,*args:[(g,g.options[0]) for g in gs])
    with pytest.raises(bf.SelectorFailure):bf.select_feasible(groups,100,sys.float_info.max)
    monkeypatch.setattr(bf,'_pick',lambda gs,lam: ([(g,g.options[0]) for g in gs],152))
    monkeypatch.setattr(bf,'_expand',lambda hi:hi)
    with pytest.raises(bf.SelectorFailure,match='progress'):
        bf.select_feasible(catalog(),100,0.)


def test_extreme_finite_value_and_price_are_accepted_when_safe():
    groups=[Group('EVID',[Option(1.,1,1,sys.float_info.max)])]
    assert bf.select_feasible(groups,1,0.)[0]
    assert bf.select_feasible(groups,0,sys.float_info.max)[0]==[]


def test_finite_operands_with_overflow_cannot_masquerade_as_empty_legacy_success():
    groups=catalog(sys.float_info.max)
    assert lagrangian_select(groups,100,sys.float_info.max)==[]
    with pytest.raises(bf.SelectorFailure,match='arithmetic'):
        bf.select_feasible(groups,100,sys.float_info.max)
    with pytest.raises(bf.SelectorFailure,match='arithmetic'):
        bf.select_feasible([Group('EVID',[Option(1.,1,1,-sys.float_info.max)])],100,sys.float_info.max)
