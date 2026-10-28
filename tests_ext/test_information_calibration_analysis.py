"""Paired estimands and predeclared exploratory screens; HPC execution only."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from scripts import analyze_information_calibration as analysis

ROOT = Path(__file__).resolve().parents[1]


def plan():
    return json.loads((ROOT / 'research/protocols/information_calibration_v1.json').read_text())


def test_paired_gain_and_ratio_of_means_not_mean_of_ratios():
    p = plan()
    t = {'time':np.array([7.,14.]), 'comm':np.array([1.,3.]), 'cpu':np.array([2.,3.])}
    c = {'time':np.array([10.,20.]), 'comm':np.array([1.,2.]), 'cpu':np.array([2.,2.])}
    idx = np.array([[0,0], [1,1], [0,1], [1,0]])
    out = analysis.compare_pair(t, c, idx, p)
    assert out['gain']['estimate'] == 4.5
    assert out['comm_ratio']['estimate'] == pytest.approx(4/3)
    assert out['comm_ratio']['estimate'] != pytest.approx(1.25)
    assert out['gain']['ci95'] == pytest.approx([3.1125, 5.8875])
    assert out['gain']['ci_family'] == pytest.approx([3.0075, 5.9925])


def test_degenerate_and_zero_denominator_never_support_positive_screen():
    p = plan(); idx = np.tile(np.arange(3), (20,1))
    t = {'time':np.array([1.,1.,1.]), 'comm':np.array([0.,0.,0.]), 'cpu':np.ones(3)}
    c = {'time':np.array([10.,10.,10.]), 'comm':np.array([0.,0.,0.]), 'cpu':np.ones(3)}
    out = analysis.compare_pair(t,c,idx,p)
    assert out['gain']['status'] == 'degenerate'
    assert out['comm_ratio']['status'] == 'undefined'
    assert out['comm_ratio']['estimate'] is None
    assert out['comm_ratio']['ci95'] is None
    assert not out['noninferiority_screen'] and not out['matched_screen']


def test_more_efficient_point_is_reported_but_not_called_matched():
    p = plan(); idx = np.array([[0,0],[1,1],[0,1],[1,0]])
    t = {'time':np.array([1.,2.]), 'comm':np.array([1.,2.]), 'cpu':np.array([1.,2.])}
    c = {'time':np.array([10.,20.]), 'comm':np.array([2.,5.]), 'cpu':np.array([2.,5.])}
    out = analysis.compare_pair(t,c,idx,p)
    assert out['noninferiority_screen']
    assert not out['mean_joint_cost_support'] and not out['matched_screen']


def synthetic_data():
    p = plan(); p['bootstrap_resamples'] = 200
    ids = p['arms'] + p['simple_references']
    rows = []
    for seed_i,seed in enumerate(p['calibration_seeds']):
        for case_i,case in enumerate(ids):
            rows.append(dict(seed=seed,case_id=case,status='completed',
                mission_wall_seconds=.1,end_to_end_wall_seconds=.2,process_seconds=.2,
                result=dict(completion_time=200+seed_i+case_i,completed=True,found=8,
                    false_declarations=0,service={'cost':{'ul_uses':100+seed_i+case_i,
                        'dl_uses':10+case_i,'cpu_seconds':1+.1*seed_i+.01*case_i}})))
    return dict(phase='calibration',calibration_run=True,formal_test_run=False,training=False,
                rows=rows,frozen={'plan':p,'cases':[{'id':x} for x in ids]})


def test_full_matrix_keeps_censoring_and_frozen_primary_method():
    data = synthetic_data()
    row = data['rows'][0]
    row['result'].update(completion_time=400,completed=False,found=7)
    out = analysis.analyze(data)
    assert out['N'] == 12 and out['missions'] == 156
    assert out['primary_method'] == 'paid-pose'
    assert out['formal_test_N'] is None and not out['formal_test_run']
    summary = next(x for x in out['cases'] if x['id'] == row['case_id'])
    assert summary['not_completed'] == 1
    assert summary['time_quantiles']['max'] == 400
    assert [x['id'] for x in out['primary']] == [x['id'] for x in plan()['primary_comparisons']]


def test_missing_software_failed_or_duplicate_world_row_is_not_dropped():
    base = synthetic_data()
    missing = copy.deepcopy(base); missing['rows'].pop()
    failed = copy.deepcopy(base); failed['rows'][0]['status']='failed'
    duplicated = copy.deepcopy(base); duplicated['rows'][-1]=copy.deepcopy(duplicated['rows'][0])
    for data in (missing, failed, duplicated):
        with pytest.raises(ValueError):
            analysis.analyze(data)


def test_bootstrap_world_index_is_shared_and_reproducible():
    data = synthetic_data()
    first, second = analysis.analyze(data), analysis.analyze(data)
    assert first['bootstrap_index_sha256'] == second['bootstrap_index_sha256']
    assert first['primary'] == second['primary']
