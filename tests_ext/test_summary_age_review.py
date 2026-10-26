import math
from itertools import product
import pytest
from gosc.schemes import Group,Option,lagrangian_select
from scripts.review_summary_age import ack_consumed_lower,scale_groups,signature

def test_ack_lower_bound_accounts_for_shared_header_and_censoring():
    assert ack_consumed_lower(0,6,0)==0
    assert ack_consumed_lower(6,6,0)==64
    assert ack_consumed_lower(7,6,0)==88
    assert ack_consumed_lower(7,6,20)==68
    assert ack_consumed_lower(7,6,1000)==0
    # All partitions of 7 attempts into legal nonempty feedback batches.
    for parts in product(range(1,7),repeat=3):
        if sum(parts)==7:
            offered=sum(16+8*m for m in parts)
            assert ack_consumed_lower(7,6,0)<=offered

@pytest.mark.parametrize('factor',[1.,.5,.1,.01])
@pytest.mark.parametrize('price',[0.,1e-5,1e-4])
def test_positive_scaling_preserves_ideal_objective_order(factor,price):
    # Exhaustive feasible choices, independent of the numerical selector.
    options=[(0.,0),(.013,17),(.021,43),(.032,64)]
    choices=[(a,b) for a,b in product(options,repeat=2) if a[1]+b[1]<=100]
    left=[factor*(a[0]+b[0])-price*(a[1]+b[1]) for a,b in choices]
    right=[a[0]+b[0]-(price/factor)*(a[1]+b[1]) for a,b in choices]
    assert all(math.isclose(x/factor,y,abs_tol=1e-15) for x,y in zip(left,right))
    assert left.index(max(left))==right.index(max(right))

def test_selector_nonboundary_example_and_no_input_mutation():
    groups=[Group('EVID',[Option(1.,40,40,.03),Option(2.,80,80,.04)])]
    scaled=scale_groups(groups,.5)
    assert signature(scaled,lagrangian_select(scaled,100,.0001))==signature(groups,lagrangian_select(groups,100,.0002))
    assert groups[0].options[0].value==.03 and scaled[0].options[0].value==.015

@pytest.mark.parametrize('factor',[0.,-1.,float('nan'),float('inf')])
def test_invalid_scale_rejected(factor):
    with pytest.raises(ValueError):scale_groups([],factor)
