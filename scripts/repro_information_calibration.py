"""Registered HPC-only GP-ID exploration: prepare, budget, calibrate. No test/train mode."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gosc.config import Config
from extensions.causal_paid_service import CausalPolicy
from extensions.information_identifiability import InformationSimulation, catalog_diagnostic
from extensions.paid_receiver_service import ServiceConfig
from scripts.repro_information_identifiability import cases, is_reserved_seed


REQUIRED_CONTRACTS = {
    'test_gzip_recording_roundtrip_preserves_every_field_order_and_hash',
    'test_calibration_matrix_exactly_reuses_original_cases_and_no_formal_mode',
    'test_calibration_registry_protects_reserved_range_interiors',
    'test_frozen_source_gate_rejects_modified_source',
    'test_calibration_contract_gate_rejects_skips_and_source_mismatch',
    'test_end_to_end_recording_includes_serialization_selector_and_compression',
    'test_short_real_mission_keeps_full_observation_and_selectors',
    'test_output_cap_stops_without_deleting_retained_files',
    'test_projection_uses_per_case_worst_world_and_double_safety',
    'test_calibration_budget_audit_is_bound_to_exact_inputs',
}
PREPARED = 'calibration_prepared_before_outcomes_requires_budget'
CAMPAIGN_HEADER_RESERVE_BYTES = 131072
ARMS = ['public-fixed', 'native-age', 'native-price', 'paid-ignore', 'paid-native-age',
        'paid-age', 'paid-price', 'paid-pose', 'paid-pose-native-age', 'paid-pose-age']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
    return sha.hexdigest()


def encoded(data):
    return (json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n').encode('utf-8')


def save(path, data):
    with Path(path).open('xb') as stream:
        stream.write(encoded(data))


def source_files(config):
    required = {
        ROOT / 'scripts/repro_information_calibration.py',
        ROOT / 'scripts/repro_information_identifiability.py',
        ROOT / 'scripts/audit_information_identifiability.py',
        ROOT / 'scripts/analyze_information_calibration.py',
        ROOT / 'scripts/audit_information_calibration.py',
        ROOT / 'tests_ext/test_information_identifiability.py',
        ROOT / 'tests_ext/test_information_calibration_runner.py',
        ROOT / 'tests_ext/test_information_calibration_analysis.py',
        ROOT / 'tests_ext/test_information_calibration_audit.py', Path(config),
    }
    return sorted(required | set(ROOT.joinpath('gosc').glob('*.py'))
                  | set(ROOT.joinpath('extensions').glob('*.py')))


def check_sources(frozen):
    for name, sha in frozen['source_sha256'].items():
        path = ROOT / name
        if not path.is_file() or digest(path) != sha:
            raise RuntimeError('Source changed since preparation: ' + name)


def validate_plan(plan):
    exact = dict(arms=ARMS, simple_references=['bits', 'aoi', 'periodic_k8_eps0'],
        fixed_diagnostic_price=1e-4, calibration_seeds=list(range(28000000, 28000012)),
        budget_seeds=[28100000, 28100001], budget_steps=96, calibration_steps=400,
        per_mission_timeout_seconds=60, calibration_timeout_seconds=1200,
        calibration_projection_gate_seconds=1080, compressed_output_cap_bytes=268435456,
        minimum_free_bytes=671088640, workers=1, numeric_threads=1,
        user_authorized=True, formal_test_authorized=False, training=False,
        service=dict(ul_capacity=100, dl_capacity=2000, slot_seconds=1.,
            encode_seconds=.001, decode_seconds=.001, ul_rate=1., dl_rate=2.,
            delay=0, ttl=20, refresh=5),
        policy=dict(replay_age=20, replay_limit=2, replay_frames_per_refresh=6,
                    valuation_seconds=.001), dl_loss=.05)
    for key, expected in exact.items():
        if plan.get(key) != expected:
            raise RuntimeError('Frozen design/authorization mismatch: ' + key)
    if len(cases(plan)) != 13 or plan.get('gpu', False) or plan.get('new_llm_calls', 0):
        raise RuntimeError('Unsupported scientific configuration')


def make(plan, case, seed, steps):
    cfg = Config(max_steps=steps, energy_price=case['price'],
                 filter_eps=case['eps'], sem_interval=case['k'])
    return InformationSimulation(cfg, seed, ServiceConfig(**plan['service']), case['mode'],
        case['arm'], CausalPolicy(**plan['policy']), plan['dl_loss'], observe=True)


def validate_contracts(config, contracts):
    contracts = Path(contracts).resolve()
    if contracts.parent != ROOT / 'research/sync/runs':
        raise RuntimeError('Contracts must be an immediate registered HPC run')
    state, manifest = read(contracts / 'status.json'), read(contracts / 'manifest.json')
    if state.get('status') != 'completed' or state.get('exit_code') != 0 or manifest.get('kind') != 'test':
        raise RuntimeError('HPC contract run has not passed')
    junit = ET.parse(contracts / 'outputs/pytest.xml').getroot()
    tests = list(junit.iter('testcase'))
    if not tests or any(list(junit.iter(tag)) for tag in ('failure', 'error', 'skipped')):
        raise RuntimeError('JUnit missing tests or includes failures/errors/skips')
    names = {t.attrib.get('name', '').split('[')[0] for t in tests}
    if not REQUIRED_CONTRACTS <= names:
        raise RuntimeError('Required calibration contracts missing')
    snapshot = read(contracts / 'source_snapshot.json')
    tested = {entry['path']:entry['remote_sha256'] for entry in snapshot['files']}
    sources = {x.relative_to(ROOT).as_posix():digest(x) for x in source_files(config)}
    if any(tested.get(name) != sha for name, sha in sources.items()):
        raise RuntimeError('Current sources differ from the passed contract snapshot')
    return sources, len(tests)


def registry_values(paths):
    integers, hashes = set(), set()
    def walk(value):
        if isinstance(value, bool):
            return
        if isinstance(value, int):
            integers.add(value)
        elif isinstance(value, str):
            if len(value) == 64:
                hashes.add(value)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
    for path in paths:
        if path.suffix == '.jsonl':
            with path.open(encoding='utf-8') as stream:
                for line in stream:
                    if line.strip():
                        walk(json.loads(line))
        else:
            walk(read(path))
    return integers, hashes


def validate_seed_candidates(seeds, historical):
    if any(is_reserved_seed(s) for s in seeds):
        raise RuntimeError('Protected reserved seed range')
    if len(set(seeds)) != len(seeds) or set(seeds) & historical:
        raise RuntimeError('Candidate seed collision; no automatic substitution')


def registry_paths(config):
    paths = set(ROOT.joinpath('research/protocols').rglob('*.json'))
    paths.update(ROOT.joinpath('research/sync/runs').glob('*/manifest.json'))
    for name in ('frozen.json', 'results.json', 'pool-plans.jsonl', 'selection_episodes.jsonl',
                 'protocol.json', 'calibration.jsonl', 'validation.jsonl', 'results.jsonl'):
        paths.update(ROOT.joinpath('research/sync/runs').glob('*/outputs/**/' + name))
    return sorted(path for path in paths if path.resolve() != Path(config).resolve())


def prepare(plan, output, config, contracts):
    validate_plan(plan)
    sources, ntests = validate_contracts(config, contracts)
    paths = registry_paths(config)
    integers, hashes = registry_values(paths)
    seeds = plan['calibration_seeds'] + plan['budget_seeds']
    validate_seed_candidates(seeds, integers)
    worlds = {}
    for seed in seeds:
        fp = make(plan, cases(plan)[0], seed, plan['calibration_steps']).input_world_sha256
        if fp in hashes or fp in worlds.values():
            raise RuntimeError('Registered world collision; no automatic substitution')
        worlds[str(seed)] = fp
    frozen = dict(status=PREPARED, plan=plan, cases=cases(plan), worlds=worlds,
        source_sha256=sources, user_authorized=True, formal_test_authorized=False,
        training=False, config_path=Path(config).relative_to(ROOT).as_posix(),
        config_sha256=digest(config), contracts_run=Path(contracts).name,
        contract_tests=ntests, contracts_status_sha256=digest(Path(contracts) / 'status.json'),
        junit_sha256=digest(Path(contracts) / 'outputs/pytest.xml'),
        registry=[dict(path=p.relative_to(ROOT).as_posix(), sha256=digest(p)) for p in paths],
        registry_scope='All discoverable JSON protocols/manifests and named historical catalogs; unregistered history cannot be guaranteed',
        reserved_inclusive_ranges=[[0,99], [1000,1079], [3000,3099], [4000,4099],
                                   [20000000,20000199], [24000000,24000199]],
        formal_test_missions=0)
    check_sources(frozen)
    save(output / 'frozen.json', frozen)
    check_sources(frozen)
    return frozen


def write_gzip_jsonl(path, events):
    """Write every supplied row/field in original order, with deterministic gzip."""
    path = Path(path)
    raw_sha, count, size = hashlib.sha256(), 0, 0
    with path.open('xb') as target:
        with gzip.GzipFile(filename='', mode='wb', compresslevel=1, mtime=0, fileobj=target) as zipped:
            for event in events:
                raw = encoded(event)
                zipped.write(raw)
                raw_sha.update(raw); count += 1; size += len(raw)
    return dict(path=path.name, sha256=digest(path), uncompressed_sha256=raw_sha.hexdigest(),
                rows=count, compressed_bytes=path.stat().st_size, uncompressed_bytes=size)


def check_output_cap(output, cap):
    size = sum(p.stat().st_size for p in Path(output).rglob('*') if p.is_file())
    if size > cap:
        raise RuntimeError('Campaign output cap exceeded; retained all artifacts')
    return size


def run_case(plan, case, seed, steps, phase, output, frozen, timeout_seconds=None):
    name = f'{seed}-{case["id"]}'
    def expired(*_):
        raise TimeoutError('Per-mission end-to-end timeout')
    old_handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, min(plan['per_mission_timeout_seconds'],
                                          timeout_seconds or plan['per_mission_timeout_seconds']))
    start, cpu = time.monotonic(), time.process_time()
    try:
        sim = make(plan, case, seed, steps)
        if sim.input_world_sha256 != frozen['worlds'][str(seed)]:
            raise RuntimeError('World differs from preparation')
        result = sim.run()
        mission_wall = time.monotonic() - start
        observation = write_gzip_jsonl(output / (name + '-observations.jsonl.gz'), sim.observation())
        counters = dict(diagnostics=0, replay_mismatches=0, cross_form_mismatches=0)
        def diagnostics():
            for decision in sim.decisions:
                item = catalog_diagnostic(decision)
                if item is not None:
                    counters['diagnostics'] += 1
                    counters['replay_mismatches'] += int(not item['replay_matches_actual'])
                    counters['cross_form_mismatches'] += int(not item['scale_price_same'])
                    yield item
        selector = write_gzip_jsonl(output / (name + '-selector.jsonl.gz'), diagnostics())
        selector.update(counters)
        row = dict(seed=seed, case_id=case['id'], case=case, phase=phase, status='completed',
            result=result, mission_wall_seconds=mission_wall,
            end_to_end_wall_seconds=time.monotonic() - start,
            process_seconds=time.process_time() - cpu, observation=observation, selector=selector,
            timing_note='Final results.json timings include this case row serialization/write; standalone row timing precedes its own write',
            artifact_bytes_scope='gzip + standalone row bytes + conservative embedded-results row bytes + 1024 metadata margin')
        save(output / (name + '.json'), row)
        row['end_to_end_wall_seconds'] = time.monotonic() - start
        row['process_seconds'] = time.process_time() - cpu
        row['artifact_bytes'] = (observation['compressed_bytes'] + selector['compressed_bytes']
            + (output / (name + '.json')).stat().st_size + len(encoded(row)) + 1024)
        if selector['replay_mismatches']:
            raise RuntimeError('Logged catalog does not replay actual selection')
        check_output_cap(output, plan['compressed_output_cap_bytes'])
        row['end_to_end_wall_seconds'] = time.monotonic() - start
        row['process_seconds'] = time.process_time() - cpu
        return row
    except Exception as exc:
        failure = dict(status='failed', seed=seed, case_id=case['id'], case=case, phase=phase,
            error=repr(exc), elapsed_wall_seconds=time.monotonic()-start,
            retained_artifacts=sorted(p.name for p in output.glob(name+'*')),
            policy='Abort campaign; retain partial artifacts; no replacement or dropped failed row')
        save(output / (name + '-failure.json'), failure)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def project_budget(rows, plan):
    maxima = []
    for case in cases(plan):
        group = [r for r in rows if r['case_id'] == case['id']]
        if len(group) != len(plan['budget_seeds']):
            raise RuntimeError('Budget matrix incomplete')
        maxima.append(dict(case_id=case['id'], max_end_to_end_wall_seconds=max(r['end_to_end_wall_seconds'] for r in group),
                           max_artifact_bytes=max(r['artifact_bytes'] for r in group)))
    multiplier = 2 * len(plan['calibration_seeds']) * plan['calibration_steps'] / plan['budget_steps']
    return dict(projected_seconds=multiplier*sum(r['max_end_to_end_wall_seconds'] for r in maxima),
                projected_bytes=multiplier*sum(r['max_artifact_bytes'] for r in maxima)+CAMPAIGN_HEADER_RESERVE_BYTES,
                campaign_header_reserve_bytes=CAMPAIGN_HEADER_RESERVE_BYTES,
                projection_multiplier=multiplier, per_case_world_maxima=maxima)


def validate_frozen(frozen):
    validate_plan(frozen['plan'])
    if frozen.get('status') != PREPARED or frozen.get('user_authorized') is not True:
        raise RuntimeError('Not a prepared user-authorized calibration protocol')
    if frozen.get('formal_test_authorized') is not False or frozen.get('training') is not False:
        raise RuntimeError('Frozen formal-test/training prohibition changed')
    if frozen['cases'] != cases(frozen['plan']):
        raise RuntimeError('Frozen case matrix changed')
    seeds = frozen['plan']['calibration_seeds'] + frozen['plan']['budget_seeds']
    if set(frozen['worlds']) != {str(s) for s in seeds} or len(set(frozen['worlds'].values())) != 14:
        raise RuntimeError('Frozen fourteen-world registry changed')
    check_sources(frozen)


def run_matrix(frozen, output, phase, frozen_path):
    plan = frozen['plan']; rows = []
    seeds = plan['budget_seeds'] if phase == 'budget' else plan['calibration_seeds']
    steps = plan['budget_steps'] if phase == 'budget' else plan['calibration_steps']
    start = time.monotonic()
    campaign_limit = plan.get('budget_timeout_seconds', 180) if phase == 'budget' else plan['calibration_timeout_seconds']
    try:
        for seed in seeds:
            for case in frozen['cases']:
                remaining = campaign_limit - (time.monotonic() - start)
                if remaining <= 0:
                    raise TimeoutError('Campaign hard time limit exceeded')
                row = run_case(plan, case, seed, steps, phase, output, frozen, remaining)
                rows.append(row)
                print(json.dumps(dict(seed=seed, case_id=case['id'], phase=phase,
                                     end_to_end_wall_seconds=row['end_to_end_wall_seconds'])), flush=True)
        check_sources(frozen)
        if time.monotonic() - start >= campaign_limit:
            raise TimeoutError('Campaign hard time limit exceeded')
        results = dict(status=phase+'_completed_requires_independent_audit', phase=phase,
            frozen=frozen, frozen_sha256=digest(frozen_path), rows=rows,
            calibration_run=phase=='calibration', formal_test_run=False, training=False,
            timing_scope='End-to-end mission construction/run, full observation JSON/gzip, complete catalog replay/gzip and per-case row JSON serialization/write; final campaign summary IO is separate',
            censoring_policy='Valid horizon-censored missions retained as capped outcomes; exceptions abort')
        save(output / 'results.json', results)
        check_output_cap(output, plan['compressed_output_cap_bytes'])
        check_sources(frozen)
        return results
    except Exception as exc:
        failures = [read(p) for p in output.glob('*-failure.json')]
        save(output / 'campaign-failure.json', dict(status='failed', phase=phase, error=repr(exc),
            frozen=frozen, frozen_sha256=digest(frozen_path), completed_rows=rows, failures=failures,
            formal_test_run=False, training=False))
        raise


def budget(frozen, output, frozen_path):
    validate_frozen(frozen)
    free = shutil.disk_usage(output).free
    if free < frozen['plan']['minimum_free_bytes']:
        raise RuntimeError('Insufficient filesystem free bytes before budget')
    results = run_matrix(frozen, output, 'budget', frozen_path)
    projection = project_budget(results['rows'], frozen['plan'])
    free = shutil.disk_usage(output).free
    plan = frozen['plan']
    passed = (projection['projected_seconds'] <= plan['calibration_projection_gate_seconds']
        and projection['projected_bytes'] <= plan['compressed_output_cap_bytes']
        and free >= plan['minimum_free_bytes'])
    report = dict(status='budget_gate_passed_requires_independent_audit' if passed else 'budget_gate_failed',
        gate_passed=passed, **projection, free_bytes=free,
        results_path=str((output / 'results.json').resolve()), results_sha256=digest(output / 'results.json'),
        frozen_path=str(Path(frozen_path).resolve()), frozen_sha256=digest(frozen_path),
        source_sha256=frozen['source_sha256'], config_sha256=frozen['config_sha256'],
        cap_bytes=plan['compressed_output_cap_bytes'], minimum_free_bytes=plan['minimum_free_bytes'],
        projection_gate_seconds=plan['calibration_projection_gate_seconds'],
        caveats=['Filesystem free bytes are not a quota measurement',
                 'Two-world per-case maximum and linear horizon scaling with 2x safety are approximate projections',
                 'Budget task outcomes do not select arms, price, N or hypotheses',
                 'Artifact projection includes standalone and embedded row estimates plus 1024 bytes per mission margin and 128KiB campaign header reserve; actual total output cap is also checked'])
    save(output / 'budget.json', report)
    check_output_cap(output, plan['compressed_output_cap_bytes'])
    check_sources(frozen)
    if not passed:
        raise RuntimeError('Budget gate failed; no calibration, no automatic redesign')
    return report


def check_budget_audit(audit, budget_path, results_path, frozen_path):
    expected = dict(status='passed', budget_sha256=digest(budget_path),
                    results_sha256=digest(results_path), frozen_sha256=digest(frozen_path))
    if any(audit.get(k) != v for k, v in expected.items()):
        raise RuntimeError('Independent budget audit/hash binding failed')


def calibrate(frozen, output, frozen_path, budget_path, audit_path):
    validate_frozen(frozen)
    report = read(budget_path)
    results_path = Path(budget_path).parent / 'results.json'
    check_budget_audit(read(audit_path), budget_path, results_path, frozen_path)
    if (not report.get('gate_passed') or report.get('frozen_sha256') != digest(frozen_path)
            or report.get('results_sha256') != digest(results_path)
            or report.get('source_sha256') != frozen['source_sha256']):
        raise RuntimeError('Budget input/source binding failed')
    rows = read(results_path)
    if rows.get('phase') != 'budget' or rows.get('frozen') != frozen:
        raise RuntimeError('Budget frozen protocol changed')
    projected = project_budget(rows['rows'], frozen['plan'])
    if (projected['projected_seconds'] > frozen['plan']['calibration_projection_gate_seconds']
            or projected['projected_bytes'] > frozen['plan']['compressed_output_cap_bytes']
            or shutil.disk_usage(output).free < frozen['plan']['minimum_free_bytes']):
        raise RuntimeError('Calibration budget/resource gate failed')
    save(output / 'budget-authorization.json', dict(budget_path=str(Path(budget_path).resolve()),
        budget_sha256=digest(budget_path), audit_path=str(Path(audit_path).resolve()),
        audit_sha256=digest(audit_path), results_sha256=digest(results_path),
        frozen_sha256=digest(frozen_path), formal_test_authorized=False, training=False))
    return run_matrix(frozen, output, 'calibration', frozen_path)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['prepare', 'budget', 'calibrate'], required=True)
    parser.add_argument('--config', type=Path, default=ROOT / 'research/protocols/information_calibration_v1.json')
    parser.add_argument('--contracts-run', type=Path)
    parser.add_argument('--frozen', type=Path)
    parser.add_argument('--budget', type=Path)
    parser.add_argument('--budget-audit', type=Path)
    return parser


def registered_output():
    if os.name != 'posix' or os.getuid() != 8301880 or str(ROOT) != '/home/u202520081000097/jupyterlab/Paper/gosc':
        raise RuntimeError('HPC-only: use scripts/hpc_runs.py launch')
    if not os.environ.get('GOSC_RUN_DIR') or not os.environ.get('GOSC_OUTPUT_DIR'):
        raise RuntimeError('Registered runner required')
    run = Path(os.environ['GOSC_RUN_DIR']).resolve()
    output = Path(os.environ['GOSC_OUTPUT_DIR']).resolve()
    if run.parent != ROOT / 'research/sync/runs' or output != run / 'outputs' or not output.is_dir():
        raise RuntimeError('Registered run/output directory mismatch')
    return output


def main():
    parser = build_parser(); args = parser.parse_args(); output = registered_output()
    if args.mode == 'prepare':
        if args.contracts_run is None:
            parser.error('--contracts-run is required for prepare')
        prepare(read(args.config), output, args.config.resolve(), args.contracts_run)
    else:
        if args.frozen is None:
            parser.error('--frozen is required')
        frozen = read(args.frozen)
        if args.mode == 'budget':
            budget(frozen, output, args.frozen)
        else:
            if args.budget is None or args.budget_audit is None:
                parser.error('--budget and --budget-audit are required for calibrate')
            calibrate(frozen, output, args.frozen, args.budget, args.budget_audit)


if __name__ == '__main__':
    main()
