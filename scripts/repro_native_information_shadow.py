"""Registered HPC-only, authorization-gated native-information shadow runner.

No local computation is allowed. No execution authorization file is generated.
prepare freezes passed contract/source identities; run requires separate human
authorization binding that frozen file and the unchanged implementation plan.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CONFIG = ROOT/'research/protocols/native_information_shadow_v1.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def registered_output():
    require(os.name == 'posix' and os.getuid() == 8301880 and
        str(ROOT) == '/home/u202520081000097/jupyterlab/Paper/gosc', 'Registered HPC only')
    require(os.environ.get('GOSC_RUN_DIR') and os.environ.get('GOSC_OUTPUT_DIR'), 'hpc_runs required')
    run, out = Path(os.environ['GOSC_RUN_DIR']).resolve(), Path(os.environ['GOSC_OUTPUT_DIR']).resolve()
    require(run.parent == ROOT/'research/sync/runs' and out == run/'outputs' and out.is_dir(), 'Run/output identity')
    return out


def validate_plan(plan):
    require(plan == read(CONFIG), 'Plan changed from checked file')
    require(plan['protocol_id'] == 'Native-Information-Shadow-v1' and
        plan['diagnostic_execution_authorized'] is False and plan['training'] is False and
        plan['formal_test'] is False and plan['efficacy_N'] == 0, 'Scope')
    require((plan['worlds'], plan['steps'], plan['per_sender_cap'], plan['max_snapshots'],
        plan['workers'], plan['numeric_threads'], plan['hard_timeout_seconds'], plan['output_cap_bytes']) ==
        ([27000000, 27000001], 24, 8, 96, 1, 1, 120, 33554432), 'Fixed bounded coverage')
    require(plan['config'] == dict(max_steps=24, energy_price=1e-4, filter_eps=.02, sem_interval=1)
        and plan['p_ref'] == 1e-4 and plan['price_multipliers'] == [0, .25, .5, 1, 2, 4], 'Fixed working point')
    require(plan['service'] == dict(ul_capacity=100, dl_capacity=2000, slot_seconds=1.,
        encode_seconds=.001, decode_seconds=.001, ul_rate=1., dl_rate=2., delay=0, ttl=20, refresh=5)
        and plan['policy'] == dict(replay_age=20, replay_limit=2, replay_frames_per_refresh=6, valuation_seconds=.001)
        and plan['dl_loss'] == .05 and plan['minimum_free_bytes'] == 134217728, 'Unchanged service contract')
    require(sha(ROOT/'research/protocols/native_information_value_spec_v1.md') ==
            plan['specification_sha256'], 'Accepted specification changed')


def source_paths():
    return sorted({*ROOT.joinpath('gosc').glob('*.py'), *ROOT.joinpath('extensions').glob('*.py'),
        *ROOT.joinpath('tests').glob('*.py'), *ROOT.joinpath('tests_ext').glob('*.py'),
        ROOT/'scripts/repro_native_information_shadow.py', ROOT/'scripts/audit_native_information_shadow.py',
        ROOT/'research/protocols/native_information_value_spec_v1.md', CONFIG})


def source_hashes():
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths()}


def save_new(out, name, data, limit=33554432):
    path = out/name
    body = (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
    size = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    require(size+len(body) <= limit-65536, 'Output cap; prior artifacts retained')
    with path.open('xb') as stream:
        stream.write(body)


def prepare(contracts, out):
    contracts = contracts.resolve()
    plan = read(CONFIG)
    validate_plan(plan)
    require(contracts.resolve().parent == ROOT/'research/sync/runs', 'Registered contract run path')
    status, manifest = read(contracts/'status.json'), read(contracts/'manifest.json')
    require(status['status'] == 'completed' and status['exit_code'] == 0 and manifest['kind'] == 'test', 'Passed test run required')
    junit = ET.parse(contracts/'outputs/pytest.xml').getroot()
    cases = list(junit.iter('testcase'))
    require(len(cases) >= 485 and not any(list(junit.iter(k)) for k in ('failure', 'error', 'skipped')), 'Full contracts required')
    names = {c.attrib['name'].split('[')[0] for c in cases}
    require({'test_native_g0_matches_original_tv_without_private_double_counting',
             'test_native_shadow_host_preserves_scientific_result',
             'test_native_shadow_audit_rejects_tampered_score',
             'test_native_shadow_execution_requires_explicit_authorization',
             'test_valid_legacy_return_preserves_identity_order_and_inputs'} <= names, 'Missing scope contracts')
    source = source_hashes()
    tested = {r['path']: r['remote_sha256'] for r in read(contracts/'source_snapshot.json')['files']}
    require(all(tested.get(k) == v for k, v in source.items()), 'Untested source/config identity')
    save_new(out, 'frozen.json', dict(plan=plan, config_sha256=sha(CONFIG), source_sha256=source,
        contracts_run=contracts.relative_to(ROOT).as_posix(),
        contract_status_sha256=sha(contracts/'status.json'),
        contract_snapshot_sha256=sha(contracts/'source_snapshot.json'),
        pytest_xml_sha256=sha(contracts/'outputs/pytest.xml'),
        git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        status='prepared_not_execution_authorized'))


def check_authorization(frozen_path, authorization):
    frozen = read(frozen_path)
    validate_plan(frozen['plan'])
    require(frozen['config_sha256'] == sha(CONFIG) and frozen['source_sha256'] == source_hashes(), 'Frozen source changed')
    contract = ROOT/frozen['contracts_run']
    require(contract.resolve().parent == ROOT/'research/sync/runs', 'Registered contract path')
    require(sha(contract/'status.json') == frozen['contract_status_sha256'] and
        sha(contract/'source_snapshot.json') == frozen['contract_snapshot_sha256'] and
        sha(contract/'outputs/pytest.xml') == frozen['pytest_xml_sha256'], 'Contract artifacts changed')
    approval = read(authorization)
    require(approval.get('approved') is True and approval.get('scope') == 'Native-Information-Shadow-v1'
        and approval.get('frozen_sha256') == sha(frozen_path)
        and approval.get('config_sha256') == sha(CONFIG)
        and approval.get('hard_timeout_seconds') == 120
        and approval.get('output_cap_bytes') == 33554432
        and isinstance(approval.get('human_authorization_record'), str)
        and bool(approval['human_authorization_record'].strip()), 'Separate explicit human authorization required')
    return frozen


def run(frozen_path, authorization, out):
    started = time.monotonic()
    def timeout(*_):
        raise TimeoutError('120-second diagnostic cap; no automatic extension')
    old_handler = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, 120)
    try:
        frozen = check_authorization(frozen_path, authorization)
        plan = frozen['plan']
        require(shutil.disk_usage(out).free >= plan['minimum_free_bytes'], 'Free disk gate')
        for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
            os.environ[name] = '1'
        # Imports and all scientific work happen only after identity/approval gates.
        from dataclasses import asdict
        from gosc.config import Config
        from extensions.causal_paid_service import CausalPolicy
        from extensions.paid_receiver_service import ServiceConfig
        from extensions.native_information_observer import NativeShadowHost, scientific_result, host_state_digest, digest
        from extensions.native_information_shadow import analyze_snapshot, benchmark_snapshot
        from scripts.audit_native_information_shadow import audit_records
        cfg = Config(**plan['config'])
        inputs, outputs, hosts, benchmarks = [], [], [], []
        for world in plan['worlds']:
            plain = NativeShadowHost(cfg, world, ServiceConfig(**plan['service']),
                CausalPolicy(**plan['policy']), plan['dl_loss'], capture=False)
            baseline = plain.run()
            save_new(out, f'baseline_{world}.json', baseline)
            observed = NativeShadowHost(cfg, world, ServiceConfig(**plan['service']),
                CausalPolicy(**plan['policy']), plan['dl_loss'], capture=True)
            result = observed.run()
            require(scientific_result(baseline) == scientific_result(result), 'Observation changed host result')
            require(plain.service.events == observed.service.events and
                plain.event_field_hashes == observed.event_field_hashes, 'Observation changed events/random field')
            require(host_state_digest(plain) == host_state_digest(observed), 'Observation changed final local state')
            hosts.append(dict(world=world, plain_result=baseline, observed_result=result,
                admissions=dict(observed.admissions), blocked=dict(observed.blocked),
                evid_admissions=dict(observed.evid_admissions), entries=observed.entry_log,
                captured=dict(observed.capture_counts), context_copy_process_seconds=observed.context_copy_seconds,
                plain_event_sha256=digest(plain.service.events), observed_event_sha256=digest(observed.service.events),
                plain_state_sha256=host_state_digest(plain), observed_state_sha256=host_state_digest(observed),
                observation_neutral=True))
            inputs.extend(dict(world=world, input=row) for row in observed.snapshot_rows)
            save_new(out, f'host_{world}.json', hosts[-1])
            save_new(out, f'inputs_{world}.json', [r for r in inputs if r['world'] == world])
            require(len(inputs) <= plan['max_snapshots'], 'Snapshot cap')
        save_new(out, 'hosts.json', hosts)
        save_new(out, 'inputs.json', inputs)
        # No alternate valuation occurs until both actual host trajectories end.
        prices = [plan['p_ref']*m for m in plan['price_multipliers']]
        for index, source in enumerate(inputs):
            outputs.append(dict(world=source['world'],
                analysis=analyze_snapshot(source['input'], cfg, prices)))
            benchmarks.append(dict(snapshot_sha256=source['input']['snapshot_sha256'],
                timing=benchmark_snapshot(source['input'], cfg, index)))
        save_new(out, 'shadows.json', outputs)
        save_new(out, 'timings.json', benchmarks)
        audit = audit_records(inputs, outputs, cfg, prices, hosts)
        save_new(out, 'audit.json', audit)
        decisions = []
        for world in plan['worlds']:
            rows = [r['analysis'] for r in outputs if r['world'] == world]
            coverage = any(len(r['prefixes']) >= 2 for r in rows)
            witness = any(r['nonproportional'] and any(s['content_witness'] for s in r['selections']) for r in rows)
            decisions.append(dict(world=world, snapshots=len(rows), multi_prefix_coverage=coverage, content_witness=witness))
        mechanism = ('Pending_coverage' if not all(r['multi_prefix_coverage'] for r in decisions) else
                     'Conditional_difference_within_declared_controls' if all(r['content_witness'] for r in decisions) else
                     'No-Go_content_route_within_diagnostic_scope')
        save_new(out, 'summary.json', dict(status='diagnostic_completed', mechanism_status=mechanism,
            worlds=decisions, cost_status='Pending_full_cost_inference_not_established',
            scientific_status='No-Go retained; no task-utility or publishability claim',
            efficacy_N=0, training=False, formal_test=False, new_stage_authorized=False,
            scope='Finite price grid, raw G0/G1 common units, no arbitrary-price exclusion or calibrated cross-ToM superiority',
            config=asdict(cfg), frozen_sha256=sha(frozen_path), authorization_sha256=sha(authorization),
            elapsed_seconds=time.monotonic()-started,
            artifacts_sha256={p.name: sha(p) for p in sorted(out.glob('*.json'))}))
    except Exception as exc:
        # Failure is a separate immutable artifact; never replace earlier outputs.
        failure = dict(status='failed', error=repr(exc), elapsed_seconds=time.monotonic()-started)
        with (out/'failure.json').open('x', encoding='utf-8') as stream:
            json.dump(failure, stream, ensure_ascii=False, indent=2)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=['prepare', 'run'])
    parser.add_argument('--contracts-run', type=Path)
    parser.add_argument('--frozen', type=Path)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    out = registered_output()
    if args.mode == 'prepare':
        if args.contracts_run is None:
            parser.error('--contracts-run required')
        prepare(args.contracts_run, out)
    else:
        if args.frozen is None or args.authorization is None:
            parser.error('--frozen and --authorization required; no default execution approval')
        run(args.frozen, args.authorization, out)


if __name__ == '__main__':
    main()
