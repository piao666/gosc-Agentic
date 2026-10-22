"""A1 scope, seed-overlap policy and paired-statistics safeguards; run on HPC."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from r4_a1 import PLAN,BASE_HEAD,expand_plan,check_ledger,paired_statistics


def test_exact_1200_scope_and_paired_seed_sets():
    jobs=expand_plan(json.loads(PLAN.read_text()))
    assert len(jobs)==len({j['job_id'] for j in jobs})==1200
    groups={(j['setting'],j['scheme']) for j in jobs};assert len(groups)==12
    for setting,scheme in groups:
        assert {j['seed'] for j in jobs if j['setting']==setting and j['scheme']==scheme}==set(range(3000,3100))
    assert all(j['config']['max_steps']==400 and not j['config']['llm_agents'] and not j['config']['tom_oracle'] for j in jobs)


@pytest.mark.parametrize('field,value',[('seeds',list(range(4000,4100))),('workers_max',3),
    ('campaign_budget_seconds',1861),('planned_missions',1800),('bootstrap_resamples',1000)])
def test_scope_cannot_expand_or_change(field,value):
    plan=json.loads(PLAN.read_text());plan[field]=value
    with pytest.raises(ValueError):expand_plan(plan)


def test_frozen_settings_cannot_be_tuned():
    plan=json.loads(PLAN.read_text());plan['settings'][0]['arms'][0]['overrides']['energy_price']=1e-4
    with pytest.raises(ValueError):expand_plan(plan)


def test_pairing_and_ratio_of_means_not_mean_of_ratios():
    result=paired_statistics([1,2,3],[2,3,4],[1,9,10],[2,18,40])
    assert result['outcome_difference_gosc_minus_periodic']==[-1,-1,-1]
    assert result['uplink_ratio_periodic_over_gosc'][0]==3
    assert result['ratio_valid_resamples']==4000 and result['ratio_invalid_resamples']==0
    with pytest.raises(ValueError):paired_statistics([1,2],[3],[1,1],[1,1])


def test_zero_uplink_ratio_is_explicit_not_nan():
    result=paired_statistics([1,2],[3,4],[0,0],[1,2])
    assert result['uplink_ratio_periodic_over_gosc'] is None
    assert result['ratio_valid_resamples']==0 and result['ratio_invalid_resamples']==4000


def test_only_disclosed_completed_r3_overlap_is_allowed(tmp_path):
    plan=json.loads(PLAN.read_text());prior=tmp_path/'hpc-r3-20261019';prior.mkdir()
    manifest={'kind':'simulation','stage':'R3','seeds':[3000],'git_commit':BASE_HEAD,'command':['python','scripts/hpc_reproduce.py','r3','--seed','3000']}
    (prior/'manifest.json').write_text(json.dumps(manifest));(prior/'status.json').write_text(json.dumps({'status':'completed'}))
    assert check_ledger(tmp_path,'current',plan)[0]['seeds']==[3000]
    other=tmp_path/'previous-a1';other.mkdir();(other/'manifest.json').write_text(json.dumps({**manifest,'stage':'R4-A1','seeds':[3000,3001]}))
    (other/'status.json').write_text(json.dumps({'status':'failed'}))
    with pytest.raises(ValueError):check_ledger(tmp_path,'current',plan)


def test_absolute_cli_validation_starts_no_missions(tmp_path):
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    run=subprocess.run([sys.executable,str(ROOT/'scripts/r4_a1.py'),'validate'],cwd=tmp_path,env=env,capture_output=True,timeout=30)
    assert run.returncode==0,run.stderr.decode()
    assert json.loads(run.stdout)=={'planned_missions':1200,'scientific_missions_started':0}
