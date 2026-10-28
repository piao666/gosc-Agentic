"""Explicit resource-only GP-ID amendment; pending proposals cannot execute."""
import argparse
import copy
import math
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import repro_information_calibration as base


RESOURCE_OVERRIDES = dict(calibration_timeout_seconds=2400,
    calibration_projection_gate_seconds=2160, compressed_output_cap_bytes=402653184,
    minimum_free_bytes=939524096)
REQUIRED_CONTRACTS = {
    'test_amendment_requires_explicit_approval_and_exact_resource_limits',
    'test_amendment_rejects_scientific_override_and_unbound_inputs',
    'test_effective_frozen_changes_only_resources_and_adds_source_provenance',
    'test_amendment_contracts_require_passed_unskipped_junit_and_matching_snapshot',
    'test_amendment_parent_full_contract_proof_requires_379_and_unchanged_hashes',
    'test_amendment_accepts_audited_blocked_budget_only_with_exact_complete_matrix',
    'test_amendment_resource_gate_blocks_excess_projection_and_low_disk',
    'test_amendment_run_records_effective_freeze_before_unchanged_calibration_loop',
    'test_amendment_cli_exposes_only_explicit_run_with_all_proofs',
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def source_files():
    return [ROOT / 'scripts/repro_information_calibration_amendment.py',
            ROOT / 'tests_ext/test_information_calibration_amendment.py']


def validate_amendment(amendment, frozen_path, budget_path, audit_path):
    mandatory = {'status', 'user_authorized', 'parent_frozen_sha256', 'budget_sha256',
                 'budget_audit_sha256', 'resource_overrides', 'formal_test_authorized', 'training'}
    allowed = mandatory | {'amendment_id', 'date', 'authorization_evidence', 'notes'}
    require(mandatory <= set(amendment) <= allowed,
            'Amendment contains missing or unsupported fields; only four resource overrides allowed')
    require(amendment['status'] == 'approved' and amendment['user_authorized'] is True,
            'Explicit human resource approval required; pending amendment cannot execute')
    require(amendment['formal_test_authorized'] is False and amendment['training'] is False,
            'No formal-test or training authorization')
    overrides = amendment['resource_overrides']
    require(isinstance(overrides, dict) and overrides == RESOURCE_OVERRIDES
            and all(type(v) is int for v in overrides.values()),
            'Amendment must contain exactly the approved four resource keys and values')
    inputs = {'parent_frozen_sha256':frozen_path, 'budget_sha256':budget_path,
              'budget_audit_sha256':audit_path}
    for key, path in inputs.items():
        require(amendment[key] == base.digest(path), 'Amendment input SHA binding failed: ' + key)
    return dict(overrides)


def _passed_contracts(contracts, required_names):
    contracts = Path(contracts).resolve()
    require(contracts.parent == ROOT / 'research/sync/runs',
            'Contracts must be an immediate registered HPC test run')
    state, manifest = base.read(contracts / 'status.json'), base.read(contracts / 'manifest.json')
    require(state.get('status') == 'completed' and state.get('exit_code') == 0
            and manifest.get('kind') == 'test', 'Required HPC contracts have not passed')
    junit = ET.parse(contracts / 'outputs/pytest.xml').getroot()
    tests = list(junit.iter('testcase'))
    require(tests and not any(list(junit.iter(tag)) for tag in ('failure', 'error', 'skipped')),
            'JUnit must contain successful, unskipped tests')
    names = {t.attrib.get('name', '').split('[')[0] for t in tests}
    require(required_names <= names, 'Required amendment contracts missing from JUnit')
    return contracts, tests


def validate_contracts(contracts):
    contracts, tests = _passed_contracts(contracts, REQUIRED_CONTRACTS)
    snapshot = base.read(contracts / 'source_snapshot.json')
    tested = {entry['path']:entry['remote_sha256'] for entry in snapshot['files']}
    sources = {p.relative_to(ROOT).as_posix():base.digest(p) for p in source_files()}
    require(all(tested.get(name) == sha for name, sha in sources.items()),
            'Amendment code/tests differ from the passed contract snapshot')
    return dict(contracts_run=contracts.name, contract_tests=len(tests),
        source_sha256=sources, status_sha256=base.digest(contracts / 'status.json'),
        junit_sha256=base.digest(contracts / 'outputs/pytest.xml'),
        snapshot_sha256=base.digest(contracts / 'source_snapshot.json'))


def validate_parent_contracts(parent):
    """Keep the original complete-test proof separate from the new wrapper proof."""
    contracts = ROOT / 'research/sync/runs' / parent['contracts_run']
    require(contracts.resolve().parent == ROOT / 'research/sync/runs', 'Parent contracts path')
    require(base.digest(contracts / 'status.json') == parent['contracts_status_sha256']
            and base.digest(contracts / 'outputs/pytest.xml') == parent['junit_sha256'],
            'Parent full-contract proof changed')
    sources, count = base.validate_contracts(ROOT / parent['config_path'], contracts)
    require(count == parent['contract_tests'] and count >= 379,
            'Original full 379-test proof is required')
    require(sources == parent['source_sha256'], 'Parent tested source set differs from its freeze')
    return dict(contracts_run=contracts.name, contract_tests=count)


def _finite_nonnegative(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def validate_budget_proof(parent, frozen_path, budget_path, audit_path):
    """Use the existing 26 fixtures; no new budget mission or outcome selection."""
    budget_path, audit_path = Path(budget_path), Path(audit_path)
    results_path = budget_path.parent / 'results.json'
    budget, proof, data = base.read(budget_path), base.read(audit_path), base.read(results_path)
    frozen_sha, results_sha = base.digest(frozen_path), base.digest(results_path)
    require(proof.get('status') in ('blocked', 'passed') and proof.get('phase') == 'budget'
            and proof.get('rows') == 26, 'Independent audited 26-row budget proof required')
    require(proof.get('budget_sha256') == base.digest(budget_path)
            and proof.get('results_sha256') == results_sha
            and proof.get('frozen_sha256') == frozen_sha,
            'Independent budget proof input SHA binding failed')
    require(budget.get('results_sha256') == results_sha and budget.get('frozen_sha256') == frozen_sha
            and budget.get('source_sha256') == parent['source_sha256']
            and budget.get('config_sha256') == parent['config_sha256'],
            'Original budget input/source SHA binding failed')
    require(data.get('phase') == 'budget' and data.get('frozen') == parent
            and data.get('frozen_sha256') == frozen_sha
            and data.get('calibration_run') is False and data.get('formal_test_run') is False
            and data.get('training') is False, 'Budget result protocol/scope binding failed')
    rows = data['rows']
    expected = {(s, c['id']) for s in parent['plan']['budget_seeds'] for c in parent['cases']}
    keys = [(r['seed'], r['case_id']) for r in rows]
    require(len(expected) == 26 and len(keys) == len(set(keys)) == 26 and set(keys) == expected
            and all(r.get('status') == 'completed' and r.get('phase') == 'budget' for r in rows),
            'Original budget paired matrix is incomplete or duplicated')
    details = proof.get('details', [])
    audited_keys = [(r['seed'], r['case_id']) for r in details]
    require(len(audited_keys) == len(set(audited_keys)) == 26 and set(audited_keys) == expected,
            'Budget proof does not audit every original fixture')
    input_hashes = proof.get('input_sha256', {})
    require(input_hashes.get('results.json') == results_sha, 'Audited results SHA is missing')
    directory = budget_path.parent.resolve()
    for name, sha in input_hashes.items():
        artifact = directory / name
        require(not artifact.is_symlink() and directory in artifact.resolve().parents,
                'Budget proof artifact path escapes its registered output')
        require(base.digest(artifact) == sha, 'Original audited budget artifact changed: ' + name)
    projection = base.project_budget(rows, parent['plan'])
    for key in ('projected_seconds', 'projected_bytes'):
        require(_finite_nonnegative(projection[key]) and budget.get(key) == projection[key]
                and proof.get(key) == projection[key], 'Budget projection differs from original audited rows')
    return projection


def validate_resource_gate(projection, free_bytes):
    require(all(_finite_nonnegative(projection.get(k)) for k in ('projected_seconds', 'projected_bytes')),
            'Invalid amended projection')
    require(projection['projected_seconds'] <= RESOURCE_OVERRIDES['calibration_projection_gate_seconds']
            and projection['projected_bytes'] <= RESOURCE_OVERRIDES['compressed_output_cap_bytes']
            and free_bytes >= RESOURCE_OVERRIDES['minimum_free_bytes'],
            'Amended resource gate failed; no mission is authorized to start')


def effective_frozen(parent, amendment, amendment_path, frozen_path, budget_path, audit_path, contracts):
    overrides = validate_amendment(amendment, frozen_path, budget_path, audit_path)
    effective = copy.deepcopy(parent)
    effective['plan'].update(overrides)
    added = [*source_files(), Path(amendment_path).resolve()]
    for path in added:
        name = path.relative_to(ROOT).as_posix()
        require(name not in parent['source_sha256'], 'Amendment cannot replace an original source/config')
        effective['source_sha256'][name] = base.digest(path)
    effective['parent_frozen_sha256'] = base.digest(frozen_path)
    effective['amendment'] = dict(approval_path=Path(amendment_path).resolve().relative_to(ROOT).as_posix(),
        approval_sha256=base.digest(amendment_path), approval=copy.deepcopy(amendment),
        parent_frozen_path=str(Path(frozen_path).resolve()), parent_frozen_sha256=base.digest(frozen_path),
        budget_path=str(Path(budget_path).resolve()), budget_sha256=base.digest(budget_path),
        budget_audit_path=str(Path(audit_path).resolve()), budget_audit_sha256=base.digest(audit_path),
        resource_overrides=overrides, targeted_contracts=copy.deepcopy(contracts),
        scope='Four approved resource limits only; original worlds/cases/statistics/sources retained; no new budget fixtures, formal test or training')
    return effective


def run(frozen_path, budget_path, audit_path, amendment_path, contracts_run, output):
    parent, amendment = base.read(frozen_path), base.read(amendment_path)
    validate_amendment(amendment, frozen_path, budget_path, audit_path)
    base.validate_frozen(parent)
    validate_parent_contracts(parent)
    contracts = validate_contracts(contracts_run)
    projection = validate_budget_proof(parent, frozen_path, budget_path, audit_path)
    free = shutil.disk_usage(output).free
    validate_resource_gate(projection, free)
    derived = effective_frozen(parent, amendment, amendment_path, frozen_path, budget_path, audit_path, contracts)
    base.check_sources(derived)
    effective_path = Path(output) / 'effective_frozen.json'
    base.save(effective_path, derived)
    base.save(Path(output) / 'budget-authorization.json', dict(status='approved_resource_amendment',
        user_authorized=True, parent_frozen_sha256=base.digest(frozen_path),
        effective_frozen_sha256=base.digest(effective_path), approval_sha256=base.digest(amendment_path),
        budget_sha256=base.digest(budget_path), budget_audit_sha256=base.digest(audit_path),
        results_sha256=base.digest(Path(budget_path).parent / 'results.json'),
        resource_overrides=dict(RESOURCE_OVERRIDES), projection=projection,
        free_bytes=free, free_bytes_scope='Filesystem free bytes, not a quota measurement',
        targeted_contracts=contracts, formal_test_authorized=False, training=False))
    base.check_output_cap(output, RESOURCE_OVERRIDES['compressed_output_cap_bytes'])
    base.check_sources(derived)
    # The unchanged original calibrate() deliberately rejects the old budget.
    # Only this explicit, hashed amendment reaches the unchanged mission loop.
    return base.run_matrix(derived, Path(output), 'calibration', effective_path)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['run'], required=True)
    parser.add_argument('--frozen', type=Path, required=True)
    parser.add_argument('--budget', type=Path, required=True)
    parser.add_argument('--budget-audit', type=Path, required=True)
    parser.add_argument('--amendment', type=Path, required=True)
    parser.add_argument('--contracts-run', type=Path, required=True)
    return parser


def main():
    args = build_parser().parse_args()
    output = base.registered_output()
    run(args.frozen, args.budget, args.budget_audit, args.amendment, args.contracts_run, output)


if __name__ == '__main__':
    main()
