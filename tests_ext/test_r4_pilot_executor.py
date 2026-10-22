"""Executor fault tests, run on HPC; synthetic workers never simulate GOSC."""
from pathlib import Path
import copy
import json
import os
import sys
import subprocess
import time

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from r4_pilot import PLAN, expand_plan, run_jobs, validate_payload


def jobs(*names):
    return [{'job_id':name} for name in names]


def fake_command(job,spec,dest):
    kind=job['job_id']
    if kind=='bad':return [sys.executable,'-c',"import sys;print('expected fixture failure',file=sys.stderr);raise SystemExit(3)"]
    if kind=='invalid':return [sys.executable,'-c',"from pathlib import Path;import sys;Path(sys.argv[1]).write_text('invalid-json')",str(dest)]
    delay=5 if kind in ['slow','never'] else 0.03
    code="from pathlib import Path;import json,sys,time;time.sleep(float(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps({'job_id':sys.argv[3]}))"
    return [sys.executable,'-c',code,str(delay),str(dest),kind]


def check(job,payload):
    if payload['job_id']!=job['job_id']:raise ValueError('Wrong fixture identity')


def verify_reaped(out):
    events=[json.loads(s) for s in (out/'events.jsonl').read_text().splitlines()]
    for event in events:
        if event['event']=='start':
            with pytest.raises(ProcessLookupError):os.kill(event['pid'],0)


def test_predeclared_scope_expands_to_unique_paired_jobs():
    result=expand_plan(json.loads(PLAN.read_text()))
    assert len(result)==60 and len({r['job_id'] for r in result})==60
    assert {r['seed'] for r in result}==set(range(9000,9010))
    for setting in ['search-W100','rescue-W100']:
        for seed in range(9000,9010):assert len([r for r in result if r['setting']==setting and r['seed']==seed])==3
    rescue=next(r for r in result if r['setting']=='rescue-W100' and r['scheme']=='sem_ras')
    assert rescue['config']['deadline_min']==60 and rescue['config']['deadline_max']==180
    assert rescue['config']['filter_eps']==1.0 and rescue['config']['sem_interval']==2


@pytest.mark.parametrize('change',['seeds','resources','llm_or_new_arm'])
def test_rejects_expanded_or_changed_scope(change):
    plan=copy.deepcopy(json.loads(PLAN.read_text()))
    if change=='seeds':plan['pilot']['seeds'][0]=1000
    elif change=='resources':plan['pilot']['workers_max']=3
    else:plan['pilot']['settings'][0]['arms'][0]['overrides']['llm_agents']=[0]
    with pytest.raises(ValueError):expand_plan(plan)


def test_timeout_failure_and_corrupt_output_are_kept(tmp_path):
    out=tmp_path/'faults'
    result=run_jobs(jobs('good','bad','invalid','slow'),out,tmp_path/'workers',fake_command,check,2,0.4,4,stop_on_failure=False)
    assert {r['job_id']:r['execution_status'] for r in result['records']}=={'good':'completed','bad':'failed','invalid':'failed','slow':'timeout'}
    assert result['max_active_workers']==2
    assert len((out/'episodes.jsonl').read_text().splitlines())==4
    assert 'expected fixture failure' in (out/'worker_logs.jsonl').read_text()
    assert next(r for r in result['records'] if r['job_id']=='invalid')['invalid_or_partial_worker_output']=='invalid-json'
    verify_reaped(out)


def test_campaign_budget_accounts_for_unstarted_jobs(tmp_path):
    out=tmp_path/'budget'
    result=run_jobs(jobs('slow','never'),out,tmp_path/'workers',fake_command,check,1,5,0.2)
    assert len(result['records'])==2 and all(r['execution_status']=='timeout' for r in result['records'])
    assert not next(r for r in result['records'] if r['job_id']=='never')['attempt_started']
    assert result['stop_reason']=='campaign_budget'
    verify_reaped(out)


def test_cancellation_and_fail_fast_reap_children(tmp_path):
    out=tmp_path/'cancel';start=time.monotonic()
    result=run_jobs(jobs('slow','never','pending'),out,tmp_path/'cancel-workers',fake_command,check,2,5,5,cancel=lambda:time.monotonic()-start>0.2)
    assert len(result['records'])==3 and all(r['execution_status']=='interrupted' for r in result['records'])
    verify_reaped(out)
    out=tmp_path/'fail-fast'
    result=run_jobs(jobs('bad','slow','never'),out,tmp_path/'failure-workers',fake_command,check,2,5,5)
    assert len(result['records'])==3 and sum(r['execution_status']=='failed' for r in result['records'])==1
    assert sum(r['execution_status']=='interrupted' for r in result['records'])==2
    verify_reaped(out)


def test_rejects_duplicate_jobs_and_cross_job_results(tmp_path):
    with pytest.raises(ValueError):run_jobs(jobs('same','same'),tmp_path/'out',tmp_path/'workers',fake_command,check,2,1,2)
    with pytest.raises(ValueError):validate_payload({'job_id':'expected','config_sha256':'a','config':{}},
                                                  {'job_id':'another','config_sha256':'a','config':{}})


def test_absolute_cli_entry_without_pythonpath(tmp_path):
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    script=Path(__file__).resolve().parents[1]/'scripts/r4_pilot.py'
    run=subprocess.run([sys.executable,str(script),'validate'],cwd=tmp_path,env=env,capture_output=True,timeout=30)
    assert run.returncode==0,run.stderr.decode()
    assert json.loads(run.stdout)=={'planned_missions':60,'scientific_missions_started':0}
