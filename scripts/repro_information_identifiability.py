"""HPC-only GP-ID-v1 prepare/probe. No calibration, formal test or training mode."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
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


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')


def source_files(config):
    return sorted({*ROOT.joinpath('gosc').glob('*.py'),
                   *ROOT.joinpath('extensions').glob('*.py'), Path(__file__),
                   ROOT / 'scripts/audit_information_identifiability.py',
                   ROOT / 'tests_ext/test_information_identifiability.py', config})


def check_sources(frozen):
    for name, sha in frozen['source_sha256'].items():
        if digest(ROOT / name) != sha:
            raise RuntimeError('Source changed since preparation: ' + name)


def cases(plan):
    rows = [dict(id=arm, arm=arm, mode='tom', price=plan['fixed_diagnostic_price'], eps=.02, k=1)
            for arm in plan['arms']]
    rows.extend(dict(id=mode, arm='public-fixed', mode=mode, price=0., eps=.02, k=1)
                for mode in ('bits', 'aoi'))
    rows.append(dict(id='periodic_k8_eps0', arm='public-fixed', mode='periodic', price=0., eps=0., k=8))
    if [r['id'] for r in rows[len(plan['arms']):]] != plan['simple_references']:
        raise RuntimeError('Simple reference list mismatch')
    return rows


def make(plan, case, seed, observe):
    cfg = Config(max_steps=plan['probe_steps'], energy_price=case['price'],
                 filter_eps=case['eps'], sem_interval=case['k'])
    return InformationSimulation(cfg, seed, ServiceConfig(**plan['service']), case['mode'],
        case['arm'], CausalPolicy(**plan['policy']), plan['dl_loss'], observe)


def is_reserved_seed(seed):
    # Inclusive interiors, not just endpoints collected from JSON catalogs.
    ranges = ((0, 99), (1000, 1079), (3000, 3099), (4000, 4099),
              (20000000, 20000199), (24000000, 24000199))
    return any(lower <= seed <= upper for lower, upper in ranges)


def prepare(plan, output, config, contracts):
    """Requires successful JUnit and a matching verified source snapshot."""
    contracts = contracts.resolve()
    if contracts.parent != ROOT / 'research/sync/runs':
        raise RuntimeError('Contracts must be an immediate registered HPC run')
    state, manifest = read(contracts / 'status.json'), read(contracts / 'manifest.json')
    if state['status'] != 'completed' or state['exit_code'] != 0 or manifest['kind'] != 'test':
        raise RuntimeError('HPC contract run has not passed')
    junit = ET.parse(contracts / 'outputs/pytest.xml').getroot()
    tests = list(junit.iter('testcase'))
    if not tests or any(list(t.iter('failure')) or list(t.iter('error')) or list(t.iter('skipped')) for t in tests):
        raise RuntimeError('JUnit missing tests or includes failures/errors/skips')
    names = {t.attrib.get('name', '').split('[')[0] for t in tests}
    required = {'test_observation_switch_preserves_scientific_results_and_noise_state',
                'test_existing_arms_preserve_legacy_gpv2_fixture',
                'test_native_age_never_reads_paid_cache',
                'test_purchase_status_and_complete_resource_accounting',
                'test_protocol_has_no_calibration_test_or_training_permission'}
    if not required <= names:
        raise RuntimeError('Required information-identifiability contracts missing')
    snapshot = read(contracts / 'source_snapshot.json')
    tested = {entry['path']:entry['remote_sha256'] for entry in snapshot['files']}
    sources = {x.relative_to(ROOT).as_posix():digest(x) for x in source_files(config)}
    if any(tested.get(name) != sha for name, sha in sources.items()):
        raise RuntimeError('Current sources differ from the passed contract snapshot')

    integers, hashes, catalog = set(), set(), []
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
    paths = set(ROOT.joinpath('research/protocols').glob('*.json'))
    paths.update(ROOT.joinpath('research/sync/runs').glob('*/manifest.json'))
    for name in ('frozen.json', 'results.json', 'pool-plans.jsonl', 'selection_episodes.jsonl',
                 'protocol.json', 'calibration.jsonl', 'validation.jsonl', 'results.jsonl'):
        paths.update(ROOT.joinpath('research/sync/runs').glob('*/outputs/' + name))
    for path in sorted(paths):
        if path.resolve() == config:
            continue
        if path.suffix == '.jsonl':
            with path.open(encoding='utf-8') as stream:
                for line in stream:
                    if line.strip():
                        walk(json.loads(line))
        else:
            walk(read(path))
        catalog.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=digest(path)))
    seeds = plan['probe_seed_candidates']
    if len(set(seeds)) != len(seeds) or set(seeds) & integers or set(seeds) & set(plan['fixture_seeds']):
        raise RuntimeError('Probe candidate seed collision; no automatic substitution')
    # Explicitly seal old calibration/evaluation/test ranges as well as catalogs.
    if any(is_reserved_seed(s) for s in seeds):
        raise RuntimeError('Protected seed range')
    worlds = {}
    for seed in seeds:
        fp = make(plan, cases(plan)[0], seed, False).input_world_sha256
        if fp in hashes or fp in worlds.values():
            raise RuntimeError('Registered world collision')
        worlds[str(seed)] = fp
    frozen = dict(status='cost_probe_only_prepared_before_outcomes', plan=plan, cases=cases(plan),
        worlds=worlds, source_sha256=sources, registry=catalog,
        contracts_run=contracts.name, contract_tests=len(tests),
        contracts_status_sha256=digest(contracts / 'status.json'),
        junit_sha256=digest(contracts / 'outputs/pytest.xml'),
        registry_scope='Discoverable named catalogs only; no guarantee about unregistered history',
        formal_test_missions=0, efficacy_N=0)
    save(output / 'frozen.json', frozen)
    print(json.dumps(dict(status=frozen['status'], cases=len(frozen['cases']), worlds=len(worlds))))


def scientific_result(result):
    return {k:v for k, v in result.items()
            if k not in ('selection_process_seconds', 'scheme', 'scope', 'compute_scope')}


def probe(frozen, output):
    check_sources(frozen)
    plan, rows, pairs = frozen['plan'], [], []
    expected = len(frozen['cases']) * len(plan['probe_seed_candidates']) * 2
    if expected != plan['probe_max_missions'] or plan['probe_observation_states'] != [False, True]:
        raise RuntimeError('Bounded observation-pair matrix changed')
    for seed in plan['probe_seed_candidates']:
        for case in frozen['cases']:
            pair = []
            for observe in plan['probe_observation_states']:
                name = f'{seed}-{case["id"]}-obs{int(observe)}'
                def expired(*_):
                    raise TimeoutError('Per-fixture timeout')
                signal.signal(signal.SIGALRM, expired)
                signal.setitimer(signal.ITIMER_REAL, plan['per_mission_timeout_seconds'])
                try:
                    wall, cpu = time.monotonic(), time.process_time()
                    sim = make(plan, case, seed, observe)
                    if sim.input_world_sha256 != frozen['worlds'][str(seed)]:
                        raise RuntimeError('World differs from preparation')
                    result = sim.run()
                    row = dict(id=name, seed=seed, case=case, observe=observe, status='completed',
                        result=result, wall_seconds=time.monotonic() - wall,
                        process_seconds=time.process_time() - cpu)
                    # Serialization is excluded from mission wall/process, but
                    # included in runner elapsed/resources; do not conflate.
                    save(output / (name + '.json'), row)
                    if observe:
                        postprocess = time.monotonic()
                        with (output / (name + '-observations.jsonl')).open('x', encoding='utf-8') as stream:
                            for event in sim.observation():
                                stream.write(json.dumps(event, allow_nan=False) + '\n')
                        diagnostics = [catalog_diagnostic(d) for d in sim.decisions]
                        diagnostics = [d for d in diagnostics if d is not None]
                        save(output / (name + '-selector.json'), dict(
                            decisions=diagnostics,
                            same_catalog_mismatches=sum(not d['scale_price_same'] for d in diagnostics),
                            replay_mismatches=sum(not d['replay_matches_actual'] for d in diagnostics),
                            postprocess_wall_seconds=time.monotonic() - postprocess,
                            scope='Numerical mechanism replay, no additional mission or efficacy N'))
                        if any(not d['replay_matches_actual'] for d in diagnostics):
                            raise RuntimeError('Logged catalog does not replay actual selection')
                    rows.append(row); pair.append(row)
                    print(json.dumps(dict(id=name, wall_seconds=row['wall_seconds'])), flush=True)
                except Exception as exc:
                    save(output / (name + '-failure.json'), dict(status='failed', id=name, error=repr(exc)))
                    raise
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
            if scientific_result(pair[0]['result']) != scientific_result(pair[1]['result']):
                raise RuntimeError('Observer changed scientific result: ' + case['id'])
            pairs.append(dict(seed=seed, case_id=case['id'], scientific_equal=True,
                process_off=pair[0]['process_seconds'], process_on=pair[1]['process_seconds'],
                wall_off=pair[0]['wall_seconds'], wall_on=pair[1]['wall_seconds']))
    save(output / 'results.json', dict(status='probe_completed_requires_independent_audit', rows=rows,
        observation_pairs=pairs, frozen=frozen, frozen_worlds=len(frozen['worlds']),
        efficacy_N=0, calibration_run=False, formal_test_run=False, training=False,
        timing_scope='Mission including instrumentation, excluding output serialization; fixed order off then on, no randomized benchmark or deployment estimate',
        task_outcome_scope='Truncated cost fixtures, not efficacy estimates or a basis for selecting arms'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['prepare', 'probe'], required=True)
    parser.add_argument('--config', type=Path, default=ROOT / 'research/protocols/information_identifiability_v1.json')
    parser.add_argument('--contracts-run', type=Path)
    parser.add_argument('--frozen', type=Path)
    args = parser.parse_args()
    if os.name != 'posix' or os.getuid() != 8301880 or str(ROOT) != '/home/u202520081000097/jupyterlab/Paper/gosc':
        raise RuntimeError('HPC-only: use scripts/hpc_runs.py launch')
    if not os.environ.get('GOSC_RUN_DIR') or not os.environ.get('GOSC_OUTPUT_DIR'):
        raise RuntimeError('Registered runner required')
    output = Path(os.environ['GOSC_OUTPUT_DIR'])
    if args.mode == 'prepare':
        if args.contracts_run is None:
            parser.error('--contracts-run is required for prepare')
        prepare(read(args.config), output, args.config.resolve(), args.contracts_run)
    else:
        if args.frozen is None:
            parser.error('--frozen is required for probe')
        frozen = read(args.frozen)
        if frozen['status'] != 'cost_probe_only_prepared_before_outcomes':
            raise RuntimeError('Not a prepared cost-probe protocol')
        probe(frozen, output)


if __name__ == '__main__':
    main()
