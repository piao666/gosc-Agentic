"""Local file/hash/run-metadata documentation only; no scientific computation."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
LOG = Path(__file__).resolve().parent


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def write(path, obj):
    (ROOT/path).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


def sha(path, lf=False):
    data = (ROOT/path).read_bytes()
    if lf:
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


frozen_path = 'research/sync/runs/hpc-native-information-freeze-20261030/outputs/frozen.json'
frozen = read(frozen_path)
mismatches = [p for p, expected in frozen['source_sha256'].items() if sha(p, True) != expected]
if mismatches:
    raise RuntimeError(('Frozen scientific source changed', mismatches))
accepted = {
    'research/protocols/native_information_value_spec_v1.md': '4e961bd8b3f7ac41064c796d70f719fec39e0ad8145db93e80afda1a5d4db125',
    'research/reports/native_information_feasibility_review_2026-10-30.md': '7d2eee3d88faefa1d40ac930ffa01c673febfadce55006359b00fe16e4c8131b'}
for path, expected in accepted.items():
    if sha(path) != expected:
        raise RuntimeError(('Accepted document changed', path))

runs = []
for run_id, receipt in (
    ('hpc-native-information-freeze-20261030', '20261030T084147Z-875d34'),
    ('hpc-native-information-shadow-20261030', '20261030T084554Z-35b09b'),
    ('hpc-native-information-shadow-report-20261030', '20261030T085115Z-62116f')):
    base = 'research/sync/runs/'+run_id
    status, manifest = read(base+'/status.json'), read(base+'/manifest.json')
    recpath = 'research/sync/receipts/'+receipt+'.json'
    rec = read(recpath)
    if status['status'] != 'completed' or status['exit_code'] != 0 or not rec['all_outputs_mirrored']:
        raise RuntimeError(('Execution or delivery incomplete', run_id))
    runs.append(dict(run_id=run_id, status=status, manifest=base+'/manifest.json',
        source_snapshot=base+'/source_snapshot.json', command=manifest['command'],
        execution_host=manifest['execution_host'], project_root=manifest['project_root'],
        git_commit=manifest['git_commit'], working_tree_dirty=bool(manifest['working_tree_status']),
        source_sync_id=manifest['source_sync_id'], source_manifest_sha256=manifest['source_manifest_sha256'],
        python_executable=manifest['python_executable'], resource_limits=manifest['resource_limits'],
        seeds=manifest['seeds'], models=manifest['models'], cache_mode=manifest['cache_mode'],
        receipt=recpath, all_outputs_mirrored=True))

report_path = 'research/sync/runs/hpc-native-information-shadow-report-20261030/outputs/report.json'
report = read(report_path)  # Copy HPC-computed results verbatim; no local reduction.
execution = dict(protocol='Native-Information-Shadow-v1', date='2026-10-30',
    user_authorization='运行最小Shadow机制诊断',
    historical_plan_unchanged=True,
    frozen_path=frozen_path, frozen_sha256=sha(frozen_path),
    config_sha256=frozen['config_sha256'],
    authorization_path='research/protocols/native_information_shadow_authorization_2026-10-30.json',
    authorization_sha256=sha('research/protocols/native_information_shadow_authorization_2026-10-30.json'),
    final_contract_run='hpc-native-information-regression-v2-20261030', final_contract_passed=519,
    frozen_scientific_source_unchanged=True, accepted_documents_unchanged=True,
    limits=dict(hard_timeout_seconds=120, output_cap_bytes=33554432, max_snapshots=96,
        worlds=[27000000, 27000001], steps=24, workers=1, numeric_threads=1),
    runs=runs, hpc_descriptive_report=report_path, hpc_report_sha256=sha(report_path),
    result=report, audit=read('research/sync/runs/hpc-native-information-shadow-20261030/outputs/audit.json'),
    report='research/reports/native_information_shadow_results_2026-10-30.md',
    next_action='Stop current G1 content route; candidate-generation/task-fit static review requires a separate research decision. No automatic compute.',
    new_scientific_source_changes=False, efficacy_N=0, formal_test=False, training=False,
    git_commit_or_push=False)
index_path = 'research/protocols/native_information_shadow_execution_2026-10-30.json'
write(index_path, execution)
write(str(LOG.relative_to(ROOT)/'actual_commands.json'), dict(
    local_management=['python research/logs/native-information-shadow-2026-10-30/preflight.py',
        'python research/logs/native-information-shadow-2026-10-30/finalize_records.py',
        'git status --short', 'git rev-parse HEAD', 'git remote -v',
        'git diff --exit-code HEAD -- gosc extensions', 'git diff --check',
        'python scripts/sync_hpc.py'],
    hpc_registered=[dict(run_id=r['run_id'], command=r['command']) for r in runs]))
write(str(LOG.relative_to(ROOT)/'experiment_manifest.json'), execution)
protected = subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', 'gosc', 'extensions'],
    cwd=ROOT, capture_output=True, text=True)
if protected.returncode:
    raise RuntimeError('Tracked original source diff')
report_file = ROOT/execution['report']
body = report_file.read_text(encoding='utf-8')
missing = [link for link in re.findall(r'\]\(([^)]+)\)', body)
    if '://' not in link and not (report_file.parent/link.split('#')[0]).exists()]
if missing:
    raise RuntimeError(('Missing report evidence links', missing))
if any(line.rstrip() != line for line in body.splitlines()):
    raise RuntimeError('Report trailing whitespace')
write(str(LOG.relative_to(ROOT)/'verification.json'), dict(
    scope='Local file/hash/registered-status metadata only; all scientific reduction on HPC',
    frozen_source_mismatches=mismatches, frozen_source_file_count=len(frozen['source_sha256']),
    accepted_document_sha256=accepted, protected_tracked_source_diff_exit_code=protected.returncode,
    execution_index=index_path, all_three_runs_completed=True, all_outputs_mirrored=True,
    hpc_audit_path='research/sync/runs/hpc-native-information-shadow-20261030/outputs/audit.json',
    scientific_status=report['mechanism_status'], efficacy_N=0, training=False, formal_test=False,
    report_missing_links=missing, report_trailing_whitespace=False))

status_path = 'research/sync/project_status.json'
status = read(status_path)
if 'native_information_shadow_results_2026_10_30' not in status:
    status['pre_shadow_latest_pointer_snapshot_2026_10_30'] = {
        k: status.get(k) for k in ('as_of', 'current_progress_report', 'latest_scientific_report', 'next_compute_action', 'training_status')}
status['native_information_shadow_results_2026_10_30'] = dict(
    status=report['mechanism_status'], report=execution['report'], execution_index=index_path,
    diagnostic_run=runs[1]['run_id'], descriptive_run=runs[2]['run_id'],
    hpc_result=report, independent_audit=execution['audit'], all_outputs_mirrored=True,
    next=execution['next_action'])
status['as_of'] = '2026-10-30 minimal bounded Shadow completed; content route No-Go within diagnostic scope'
status['current_progress_report'] = execution['report']
status['latest_scientific_report'] = execution['report']
status['next_compute_action'] = execution['next_action']
status['training_status'] = 'not_started; current G1 route No-Go, no training or formal test authorized'
write(status_path, status)
print(json.dumps(dict(status='management_records_written', frozen_sources_unchanged=True,
    accepted_documents_unchanged=True, all_outputs_mirrored=True)))
