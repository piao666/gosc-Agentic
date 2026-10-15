import numpy as np
import pytest
from experiments_ext.statistical_agreement import (align_rows,bootstrap_means,classify_interval,simultaneous_agreement)


def metric(name,a,b,cohort='eval',scale=1,margin=.05):
    return dict(id=name,fresh=a,reference=b,cohort=cohort,scale=scale,margin=margin)


def test_non_significance_is_not_equivalence():
    assert classify_interval([-.2,.2],.05)=='inconclusive'
    assert classify_interval([.06,.08],.05)=='incompatible'
    assert classify_interval([-.05,.05],.05)=='equivalent'


def test_large_common_mission_effect_cancels():
    b=np.array([0,100,10000,-1000.])
    r=simultaneous_agreement([metric('fixed',b+3,b,scale=100)],resamples=200)
    assert r['results'][0]['simultaneous_interval']==pytest.approx([.03,.03])
    assert r['all_equivalent']


def test_constant_decimal_difference_has_no_spurious_bootstrap_variance():
    a=np.full(100,.03);b=np.zeros(100)
    r=simultaneous_agreement([metric('constant',a,b),metric('variable',np.sin(np.arange(100)),b)],resamples=1000)
    assert r['results'][0]['simultaneous_interval'][0]==r['results'][0]['simultaneous_interval'][1]
    assert r['critical_value']<5


def test_family_adjustment_includes_unadjusted_standardized_intervals():
    rng=np.random.default_rng(5);b=np.arange(50.)
    a=b+rng.normal(size=50)
    one=simultaneous_agreement([metric('a',a,b)],resamples=1000)
    both=simultaneous_agreement([metric('a',a,b),metric('b',b+np.cos(b),b)],resamples=1000)
    assert both['family_size']==2 and both['critical_value']>=one['critical_value']
    assert one['results'][0]['n']==50


def test_bootstrap_reuses_mission_indices_across_metrics():
    a=np.array([[10,20,100],[110,120,200]])
    idx=np.array([[0,0,2],[2,1,1]])
    out=bootstrap_means(a,idx)
    assert out[:,0]==pytest.approx([40,140/3])
    assert out[:,1]-out[:,0]==pytest.approx([100,100])


def test_seed_and_nonfinite_inputs_fail_closed():
    with pytest.raises(ValueError):align_rows([{'seed':0},{'seed':0}],[0,1])
    with pytest.raises(ValueError):align_rows([{'seed':0}],[0,1])
    assert [r['seed'] for r in align_rows([{'seed':1},{'seed':0}],[0,1])]==[0,1]
    with pytest.raises(ValueError):simultaneous_agreement([metric('bad',[1,np.nan],[1,2])],resamples=200)
    with pytest.raises(ValueError):simultaneous_agreement([metric('bad',[1,2],[1])],resamples=200)


def test_vectorized_frontier_matches_original_interpolation_and_range():
    from experiments.plot_revision import _interp_T
    from experiments_ext.analyze_statistical_reproduction import interp_frontier
    points=[('a',[{'symbols':v,'completion_time':t} for v,t in zip([8,10,12],[90,100,110])]),
            ('b',[{'symbols':v,'completion_time':t} for v,t in zip([25,30,35],[70,80,90])]),
            ('c',[{'symbols':v,'completion_time':t} for v,t in zip([70,80,90],[80,90,100])])]
    draws=np.array([[0,1,2],[0,0,2],[2,2,1]])
    x=np.array([[np.mean([r['symbols'] for r in rs]) for _,rs in points]])
    y=np.array([[np.mean([r['completion_time'] for r in rs]) for _,rs in points]])
    for B in (5,20,50,100):
        expected=_interp_T(points,B,np.arange(3));actual=interp_frontier(x,y,B)[0]
        if expected is None:assert np.isnan(actual)
        else:assert actual==pytest.approx(expected)
    bx=np.array([[np.mean([rs[i]['symbols'] for i in draw]) for _,rs in points] for draw in draws])
    by=np.array([[np.mean([rs[i]['completion_time'] for i in draw]) for _,rs in points] for draw in draws])
    assert interp_frontier(bx,by,20)==pytest.approx([_interp_T(points,20,draw) for draw in draws])
