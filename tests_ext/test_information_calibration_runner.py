"""Prospective calibration runner contracts; execute only in registered HPC tests."""
import copy
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from scripts import repro_information_calibration as runner
from scripts.repro_information_identifiability import cases as original_cases


ROOT = Path(__file__).resolve().parents[1]


def plan():
    old = runner.read(ROOT / 'research/protocols/information_identifiability_v1.json')
    old.update(calibration_seeds=list(range(28000000, 28000012)),
               budget_seeds=[28100000, 28100001], budget_steps=96,
               calibration_steps=400, per_mission_timeout_seconds=60,
               calibration_timeout_seconds=1200, calibration_projection_gate_seconds=1080,
               compressed_output_cap_bytes=268435456, minimum_free_bytes=671088640,
               workers=1, numeric_threads=1, user_authorized=True,
               formal_test_authorized=False, training=False)
    return old


def test_gzip_recording_roundtrip_preserves_every_field_order_and_hash(tmp_path):
    events = [{'event':'decision', 't':1, 'all':{'tiny':1e-200, 'hex':(.3).hex()},
               'catalog':[{'value':.3, 'unused':None}], 'unicode':'位置'},
              {'event':'service_end', 'pending':[1, 2]}]
    path = tmp_path / 'events.jsonl.gz'
    meta = runner.write_gzip_jsonl(path, iter(events))
    raw = gzip.decompress(path.read_bytes())
    assert [json.loads(line) for line in raw.splitlines()] == events
    assert list(json.loads(raw.splitlines()[0])) == list(events[0])
    assert meta == dict(path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        uncompressed_sha256=hashlib.sha256(raw).hexdigest(), rows=2,
        compressed_bytes=path.stat().st_size, uncompressed_bytes=len(raw))
    with pytest.raises(FileExistsError):
        runner.write_gzip_jsonl(path, events)


def test_calibration_matrix_exactly_reuses_original_cases_and_no_formal_mode():
    p = plan()
    assert runner.cases(p) == original_cases(p)
    assert len(runner.cases(p)) == 13
    runner.validate_plan(p)
    for field, value in [('user_authorized', False), ('formal_test_authorized', True),
                         ('training', True), ('workers', 2), ('fixed_diagnostic_price', .1),
                         ('calibration_seeds', list(range(28000000, 28000011))),
                         ('arms', list(reversed(p['arms'])))]:
        invalid = copy.deepcopy(p); invalid[field] = value
        with pytest.raises((RuntimeError, ValueError)):
            runner.validate_plan(invalid)
    assert runner.build_parser()._option_string_actions['--mode'].choices == ['prepare', 'budget', 'calibrate']


@pytest.mark.parametrize('seed', [0, 99, 1001, 1079, 3001, 3099, 4001,
                                  4099, 20000001, 20000199, 24000001, 24000199])
def test_calibration_registry_protects_reserved_range_interiors(seed):
    with pytest.raises(RuntimeError, match='[Rr]eserved|[Pp]rotected'):
        runner.validate_seed_candidates([seed], set())


def test_registry_detects_historical_seed_and_world_no_substitution(tmp_path):
    with pytest.raises(RuntimeError, match='collision'):
        runner.validate_seed_candidates([28000000], {28000000})
    with pytest.raises(RuntimeError, match='[Dd]uplicate|collision'):
        runner.validate_seed_candidates([28000000, 28000000], set())
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps({'seeds':[28000002], 'nested':{'world':'a'*64}}))
    integers, hashes = runner.registry_values([path])
    assert 28000002 in integers and 'a'*64 in hashes


def test_frozen_source_gate_rejects_modified_source(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    source = tmp_path / 'source.py'; source.write_text('first\n')
    frozen = {'source_sha256':{'source.py':runner.digest(source)}}
    runner.check_sources(frozen)
    source.write_text('second\n')
    with pytest.raises(RuntimeError, match='Source changed'):
        runner.check_sources(frozen)


def test_source_snapshot_covers_all_scientific_and_new_audit_sources():
    paths = set(runner.source_files(ROOT / 'research/protocols/information_calibration_v1.json'))
    assert set((ROOT / 'gosc').glob('*.py')) <= paths
    assert set((ROOT / 'extensions').glob('*.py')) <= paths
    assert {ROOT / 'scripts/repro_information_calibration.py',
            ROOT / 'scripts/analyze_information_calibration.py',
            ROOT / 'scripts/audit_information_calibration.py',
            ROOT / 'tests_ext/test_information_calibration_runner.py',
            ROOT / 'tests_ext/test_information_calibration_analysis.py',
            ROOT / 'tests_ext/test_information_calibration_audit.py'} <= paths


def test_calibration_contract_gate_rejects_skips_and_source_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    config = tmp_path / 'config.json'; config.write_text('{}')
    monkeypatch.setattr(runner, 'source_files', lambda c: [config])
    contracts = tmp_path / 'research/sync/runs/contracts'
    (contracts / 'outputs').mkdir(parents=True)
    (contracts / 'status.json').write_text(json.dumps({'status':'completed', 'exit_code':0}))
    (contracts / 'manifest.json').write_text(json.dumps({'kind':'test'}))
    (contracts / 'source_snapshot.json').write_text(json.dumps({'files':[
        {'path':'config.json', 'remote_sha256':runner.digest(config)}]}))
    xml = '<testsuite>'+''.join('<testcase name="'+name+'"/>' for name in runner.REQUIRED_CONTRACTS)+'</testsuite>'
    (contracts / 'outputs/pytest.xml').write_text(xml)
    runner.validate_contracts(config, contracts)
    (contracts / 'outputs/pytest.xml').write_text(xml.replace('/>', '><skipped/></testcase>', 1))
    with pytest.raises(RuntimeError, match='JUnit'):
        runner.validate_contracts(config, contracts)
    (contracts / 'outputs/pytest.xml').write_text(xml)
    config.write_text('{"changed":true}')
    with pytest.raises(RuntimeError, match='snapshot|sources'):
        runner.validate_contracts(config, contracts)


def test_end_to_end_recording_includes_serialization_selector_and_compression(tmp_path, monkeypatch):
    p = plan(); c = runner.cases(p)[0]
    clock = [0.]
    monkeypatch.setattr(runner.time, 'monotonic', lambda: clock[0])
    class Simulation:
        input_world_sha256 = 'a'*64
        decisions = [{'groups_before_age':[], 'extra':'complete'}]
        def run(self):
            clock[0] += 2
            return {'steps':4, 'full_result':[1, 2]}
        def observation(self):
            return [{'event':'decision', 'full_catalog':[1, 2]}]
    monkeypatch.setattr(runner, 'make', lambda *args: Simulation())
    def diagnostic(decision):
        clock[0] += 3
        return dict(replay_matches_actual=True, scale_price_same=False, complete=decision)
    monkeypatch.setattr(runner, 'catalog_diagnostic', diagnostic)
    original = runner.write_gzip_jsonl
    def record(*args):
        clock[0] += 5
        return original(*args)
    monkeypatch.setattr(runner, 'write_gzip_jsonl', record)
    row = runner.run_case(p, c, 28000000, 4, 'budget', tmp_path,
                          {'worlds':{'28000000':'a'*64}})
    assert row['mission_wall_seconds'] == 2
    assert row['end_to_end_wall_seconds'] >= 15
    assert row['selector']['diagnostics'] == 1
    assert row['selector']['replay_mismatches'] == 0
    assert row['selector']['cross_form_mismatches'] == 1
    assert row['observation']['rows'] == 1 and row['status'] == 'completed'


def test_short_real_mission_keeps_full_observation_and_selectors(tmp_path):
    p = plan(); c = runner.cases(p)[0]; seed = 28200000
    sim = runner.make(p, c, seed, 3)
    row = runner.run_case(p, c, seed, 3, 'contract', tmp_path,
                          {'worlds':{str(seed):sim.input_world_sha256}})
    observation = [json.loads(x) for x in gzip.decompress((tmp_path / row['observation']['path']).read_bytes()).splitlines()]
    assert observation and observation[-1]['event'] == 'service_end'
    assert all('groups_before_age' in x for x in observation if x['event'] == 'decision')
    assert row['selector']['replay_mismatches'] == 0


def test_output_cap_stops_without_deleting_retained_files(tmp_path):
    artifact = tmp_path / 'existing.jsonl.gz'; artifact.write_bytes(b'x'*20)
    row = tmp_path / 'existing.json'; row.write_bytes(b'y'*20)
    with pytest.raises(RuntimeError, match='cap'):
        runner.check_output_cap(tmp_path, 39)
    assert artifact.read_bytes() == b'x'*20 and row.exists()


def test_projection_uses_per_case_worst_world_and_double_safety():
    p = plan()
    rows = [dict(case_id=c['id'], end_to_end_wall_seconds=float(k),
                 artifact_bytes=100*k) for c in runner.cases(p) for k in [1, 2]]
    projection = runner.project_budget(rows, p)
    factor = 2 * 12 * 400 / 96
    assert projection['projected_seconds'] == pytest.approx(factor * 13 * 2)
    assert projection['projected_bytes'] == pytest.approx(factor * 13 * 200 + 131072)


def test_calibration_budget_audit_is_bound_to_exact_inputs(tmp_path):
    budget = tmp_path / 'budget.json'; budget.write_text('{}')
    results = tmp_path / 'results.json'; results.write_text('{}')
    frozen = tmp_path / 'frozen.json'; frozen.write_text('{}')
    audit = dict(status='passed', budget_sha256=runner.digest(budget),
                 results_sha256=runner.digest(results), frozen_sha256=runner.digest(frozen))
    runner.check_budget_audit(audit, budget, results, frozen)
    audit['results_sha256'] = '0'*64
    with pytest.raises(RuntimeError, match='audit|hash'):
        runner.check_budget_audit(audit, budget, results, frozen)


def test_prepare_freezes_fourteen_worlds_without_running_any_mission(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    config = tmp_path / 'config.json'; config.write_text('{}')
    contracts = tmp_path / 'contracts'; (contracts / 'outputs').mkdir(parents=True)
    (contracts / 'status.json').write_text('{}')
    (contracts / 'outputs/pytest.xml').write_text('<testsuite/>')
    monkeypatch.setattr(runner, 'validate_contracts', lambda *args: ({'config.json':runner.digest(config)}, 20))
    monkeypatch.setattr(runner, 'registry_paths', lambda *args: [])
    def prospective(p, case, seed, steps):
        class NeverRun:
            input_world_sha256 = hashlib.sha256(str(seed).encode()).hexdigest()
            def run(self):
                raise AssertionError('Preparation ran a task outcome')
        return NeverRun()
    monkeypatch.setattr(runner, 'make', prospective)
    frozen = runner.prepare(plan(), tmp_path, config, contracts)
    assert len(frozen['worlds']) == 14 and len(set(frozen['worlds'].values())) == 14
    assert frozen['user_authorized'] and not frozen['formal_test_authorized']
    assert frozen['source_sha256'] == {'config.json':runner.digest(config)}
    assert runner.read(tmp_path / 'frozen.json') == frozen


def test_failed_case_keeps_failure_and_preexisting_artifacts(tmp_path, monkeypatch):
    p = plan(); case = runner.cases(p)[0]
    class Failed:
        input_world_sha256 = 'a'*64
        def run(self):
            raise TimeoutError('bounded fixture failure')
    monkeypatch.setattr(runner, 'make', lambda *args: Failed())
    kept = tmp_path / 'old.jsonl.gz'; kept.write_bytes(b'old')
    with pytest.raises(TimeoutError):
        runner.run_case(p, case, 28000000, 4, 'budget', tmp_path,
                        {'worlds':{'28000000':'a'*64}})
    failure = runner.read(tmp_path / '28000000-public-fixed-failure.json')
    assert failure['status'] == 'failed' and failure['seed'] == 28000000
    assert failure['case_id'] == case['id'] and kept.read_bytes() == b'old'
