"""Safety semantics of the long original-entry-point reproduction adapter; HPC only."""
import dataclasses
import json
import os
from pathlib import Path
import sys
import time

import pytest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from repro_legacy import CappedPool,serial
from repro_selection import freeze,job
from repro_ordered import audit_events,equal,STAGES


def fixture(value):
    if value=='slow':time.sleep(3)
    if value=='bad':raise ValueError('intentional fixture failure')
    return value


def test_pool_order_reuse_unique_indexes_and_concurrency(tmp_path,monkeypatch):
    monkeypatch.setenv('GOSC_OUTPUT_DIR',str(tmp_path));monkeypatch.setenv('GOSC_POOL_COUNTER','0')
    with CappedPool(64) as pool:
        assert pool.map(fixture,[3,1,2])==[3,1,2]
        assert pool.map(fixture,[4,5])==[4,5]
    audit_events(tmp_path)
    audit=json.loads((tmp_path/'stage_audit.json').read_text())
    assert audit['worker_starts']==audit['worker_terminals']==5 and audit['max_concurrency']<=2
    rows=[json.loads(line) for line in (tmp_path/'pool-001-jobs.jsonl').read_text().splitlines()]
    assert {r['index'] for r in rows}==set(range(5))


@pytest.mark.parametrize('value',['bad','slow'])
def test_failure_and_alarm_are_preserved_and_workers_reaped(value,tmp_path,monkeypatch):
    monkeypatch.setenv('GOSC_OUTPUT_DIR',str(tmp_path));monkeypatch.setenv('GOSC_POOL_COUNTER','0');monkeypatch.setenv('REPRO_JOB_TIMEOUT_SECONDS','1')
    with pytest.raises(RuntimeError):
        with CappedPool(2) as pool:list(pool.imap_unordered(fixture,[value]))
    rows=[json.loads(line) for line in (tmp_path/'pool-001-jobs.jsonl').read_text().splitlines()]
    assert rows[0]['status']=='failed'
    assert all(not worker.is_alive() for worker in pool.pool._pool)


def test_worker_matches_original_and_records_common_world():
    from gosc import Config,run_episode
    cfg=dataclasses.asdict(Config());cfg=json.loads(json.dumps(cfg))
    case={'case':0,'setting':'fixture','family':'gosc','point':'fixture','scheme':'gosc','config':cfg}
    value=job((case,9022));original=run_episode(Config(),'gosc',9022);original.pop('curve')
    assert all(equal(value[k],v) for k,v in original.items())
    periodic=job(({**case,'case':1,'scheme':'sem'},9022))
    assert value['world_start_sha256']==periodic['world_start_sha256']


def test_freeze_uses_target_then_cost_and_rejects_fresh_reference():
    cases=[{'case':i,'setting':'search-X','family':family,'point':str(i),'scheme':str(i),'metric':'completion_time','config':{}}
           for i,family in enumerate(['genie_reference','gosc','gosc','periodic'])]
    rows=[{'case':i,'seed':s,'completion_time':outcome,'symbols':symbols}
          for i,outcome,symbols in [(0,10,0),(1,13,1),(2,12,20),(3,11,25)] for s in range(100)]
    selected,_=freeze(cases,rows)
    assert selected['search-X']['target']==12.5 and selected['search-X']['gosc']['point']=='2'
    bad=[{**r,'seed':r['seed']+3000} if r['case']==0 else r for r in rows]
    with pytest.raises(AssertionError):freeze(cases,bad)


def test_nonfinite_diagnostic_evidence_is_explicit():
    assert serial(float('nan'))=={'nonfinite_float':'nan'}
    assert equal(float('nan'),float('nan'))
    assert not equal(1,2)


def test_queue_order_and_scientific_scope():
    names=[s[0] for s in STAGES]
    assert names.index('selection')<names.index('c-analysis')<names.index('radio-noise')<names.index('cached-llm')<names.index('live-llm')
    assert names.index('sensitivity')>names.index('live-llm')
    assert all(s[3] in [120,1800] for s in STAGES)


@pytest.mark.parametrize('table', [False, True])
def test_original_belief_cli_without_main_preserves_parser_and_pool(monkeypatch, table):
    from experiments import run_belief_divergence as original
    from repro_legacy import invoke_entry
    seen=[]
    monkeypatch.setattr(original, 'Pool', CappedPool)
    monkeypatch.setattr(original, 'simulate', lambda seeds, workers: seen.append((seeds, workers, original.Pool)))
    monkeypatch.setattr(original, 'fill_table', lambda: seen.append('table'))
    monkeypatch.setattr(sys, 'argv', ['experiments.run_belief_divergence', '--seeds', '2', '--workers', '2'] + (['--table'] if table else []))
    assert not hasattr(original, 'main')
    invoke_entry(original)
    assert seen == (['table'] if table else [(2, 2, CappedPool)])


def test_legacy_regular_main_is_called_once(monkeypatch):
    from experiments import run_revision as original
    from repro_legacy import invoke_entry
    seen=[]
    monkeypatch.setattr(original, 'main', lambda: seen.append(tuple(sys.argv)))
    monkeypatch.setattr(sys, 'argv', ['experiments.run_revision', '--only', 'frontier'])
    invoke_entry(original)
    assert seen == [('experiments.run_revision', '--only', 'frontier')]
