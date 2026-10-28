import json
from pathlib import Path

import pytest
from scripts import repro_budget_feasible_selector as runner


ROOT=Path(__file__).resolve().parents[1]


def test_acceptance_scope_is_only_existing_catalogs_and_short_fixtures():
    p=json.loads((ROOT/'research/protocols/budget_selector_acceptance_v1.json').read_text())
    assert p['user_authorized'] and p['efficacy_N']==0 and not p['formal_test'] and not p['training']
    assert p['fixture_seeds']==[27000000,27000001] and p['fixture_steps']==24
    assert p['historical_failure_count']==7 and p['expected_feasible_catalogs']==192
    assert p['workers']==p['numeric_threads']==1


def test_frozen_source_mismatch_prevents_execution(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    p=tmp_path/'source.py';p.write_text('original\n')
    frozen=dict(source_sha256={'source.py':runner.digest(p)})
    runner.check_sources(frozen)
    p.write_text('changed\n')
    with pytest.raises(RuntimeError,match='Source changed'):runner.check_sources(frozen)


def test_output_cap_preserves_failure_evidence(tmp_path):
    p=tmp_path/'evidence';p.write_bytes(b'original')
    with pytest.raises(RuntimeError,match='cap'):runner.cap(tmp_path,{'output_cap_bytes':1})
    assert p.read_bytes()==b'original'
