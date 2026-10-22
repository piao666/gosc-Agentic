"""Scope, freeze provenance and unequal-sample cost-budget safeguards; HPC only."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from r4_cost_probe import PLAN, FULL_GROUPS, expand_plan, check_frozen, budget_projection


def test_exact_probe_scope_and_disjoint_seed_roles():
    plan=json.loads(PLAN.read_text());jobs=expand_plan(plan)
    assert len(jobs)==24 and len({j['job_id'] for j in jobs})==24
    assert {j['seed'] for j in jobs}=={9010,9011,9012}
    assert all(not j['config']['llm_agents'] and not j['config']['tom_oracle'] for j in jobs)
    assert {j['setting'] for j in jobs}=={'search-K10','search-clustered','rescue-W50','rescue-snr-5'}
    assert all(j['config']['max_steps']==400 for j in jobs)


@pytest.mark.parametrize('field,value',[('seeds',[3000,3001,3002]),('workers_max',3),('campaign_budget_seconds',601),('planned_missions',1200)])
def test_rejects_scope_changes(field,value):
    plan=json.loads(PLAN.read_text());plan[field]=value
    with pytest.raises(ValueError):expand_plan(plan)


def test_frozen_points_checked_against_original_record():
    plan=json.loads(PLAN.read_text());frozen=json.loads((ROOT/'results/rev_validation.json').read_text())
    check_frozen(plan,frozen)
    bad=copy.deepcopy(frozen);bad['search-K10']['gosc']['point']='K10/eta1e-05'
    with pytest.raises(ValueError):check_frozen(plan,bad)


def test_budget_weights_settings_equally_despite_unequal_sample_sizes():
    groups=[{'setting':s,'scheme':a,'n':3 if 'W100' not in s else 10,
             'mean_worker_wall_seconds':2 if 'W100' not in s else 1,
             'max_worker_wall_seconds':4,'mean_worker_cpu_seconds':1,'max_single_worker_rss_kib':60000,
             'mean_raw_record_bytes':1000} for s,a in FULL_GROUPS]
    value=budget_projection(groups,1)
    assert value['estimated_campaign_wall_seconds']==1000
    assert value['estimated_worker_cpu_seconds']==1200
    assert value['estimated_raw_episodes_bytes']==1200000
    assert value['recommended_campaign_cap_seconds']==3120
    assert value['full_campaign_status']=='not_started'
    with pytest.raises(ValueError):budget_projection(groups[:-1],1)
    with pytest.raises(ValueError):budget_projection(groups,0.9)


def test_absolute_cli_entry_validates_frozen_scope_without_missions(tmp_path):
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    run=subprocess.run([sys.executable,str(ROOT/'scripts/r4_cost_probe.py'),'validate'],
                       cwd=tmp_path,env=env,capture_output=True,timeout=30)
    assert run.returncode==0,run.stderr.decode()
    assert json.loads(run.stdout)=={'planned_missions':24,'scientific_missions_started':0}
