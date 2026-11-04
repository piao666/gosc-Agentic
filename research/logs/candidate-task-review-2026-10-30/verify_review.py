"""Local file/hash/Git/link management only. No scientific imports or reductions."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
LOG = Path(__file__).resolve().parent


def git(*args):
    r = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    if r.returncode:
        raise RuntimeError((args, r.returncode, r.stderr))
    return r.stdout.strip()


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def sha(path, lf=False):
    data = (ROOT/path).read_bytes()
    if lf:
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def write(name, body):
    (LOG/name).write_text(json.dumps(body, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


frozen_path = 'research/sync/runs/hpc-native-information-freeze-20261030/outputs/frozen.json'
frozen = read(frozen_path)
source_changes = [p for p, expected in frozen['source_sha256'].items() if sha(p, True) != expected]
accepted = {
    'research/protocols/native_information_value_spec_v1.md': '4e961bd8b3f7ac41064c796d70f719fec39e0ad8145db93e80afda1a5d4db125',
    'research/reports/native_information_feasibility_review_2026-10-30.md': '7d2eee3d88faefa1d40ac930ffa01c673febfadce55006359b00fe16e4c8131b'}
accepted_changes = [p for p, expected in accepted.items() if sha(p) != expected]
if source_changes or accepted_changes:
    raise RuntimeError(('Protected source/document change', source_changes, accepted_changes))
head = git('rev-parse', 'HEAD')
if head != '014b85dfc472c45d8ea5f15e83e0c1ed8e938daf':
    raise RuntimeError('Baseline HEAD changed')
git('diff', '--exit-code', 'HEAD', '--', 'gosc', 'extensions')
git('diff', '--check')
reports = [ROOT/'research/reports'/n for n in (
    'candidate_expression_review_2026-10-30.md',
    'planner_search_task_fit_review_2026-10-30.md',
    'research_route_decision_2026-10-30.md')]
docs = reports + sorted(LOG.glob('*.md'))
links, whitespace = [], []
for path in docs:
    body = path.read_text(encoding='utf-8')
    for link in re.findall(r'\]\(([^)]+)\)', body):
        if '://' not in link and not (path.parent/link.split('#')[0]).exists():
            links.append(dict(file=str(path.relative_to(ROOT)), link=link))
    for i, line in enumerate(body.splitlines(), 1):
        if line != line.rstrip():
            whitespace.append(dict(file=str(path.relative_to(ROOT)), line=i))
if links or whitespace:
    raise RuntimeError(('Document management checks', links, whitespace))
inputs = [
    'research/reports/native_information_shadow_results_2026-10-30.md',
    'research/reports/information_calibration_results_2026-10-27.md',
    'research/reports/information_identifiability_acceptance_2026-10-27.md',
    'research/reports/budget_selector_acceptance_2026-10-27.md',
    'research/protocols/information_calibration_execution_2026-10-27.json',
    'research/protocols/budget_selector_execution_2026-10-27.json',
    'research/protocols/native_information_shadow_execution_2026-10-30.json',
    'research/sync/runs/hpc-native-information-shadow-report-20261030/outputs/report.json',
    'research/sync/runs/hpc-native-information-shadow-20261030/outputs/shadows.json',
    frozen_path]
manifest = dict(date='2026-10-30', task='candidate_expression_and_task_fit_static_review',
    baseline_commit=head, branch=git('branch', '--show-current'), remote=git('remote', '-v'),
    working_tree_status=git('status', '--short'),
    execution_host='local Windows; file/document management only',
    scientific_execution_host=None, new_scientific_runs=[], new_seeds=[], models_called=[],
    algorithms_modified=False, candidates_modified=False, task_environment_modified=False,
    value_function_modified=False, new_tests_run=False, new_statistics_or_reselection=False,
    hpc_sync_or_compute=False, paid_api=False, git_commit_or_push=False,
    frozen_scientific_sources_unchanged=True, accepted_documents_unchanged=True,
    inputs_sha256={p: sha(p) for p in inputs},
    outputs_sha256={str(p.relative_to(ROOT)): sha(p) for p in docs},
    scientific_status='G1 No-Go retained; route B static adapter specification recommended conditionally, no execution authorization',
    next='Stop and await research direction decision')
write('experiment_manifest.json', manifest)
write('verification.json', dict(scope='File/Git/document management only, not tests or scientific analysis',
    head=head, frozen_source_file_count=len(frozen['source_sha256']), frozen_source_mismatches=source_changes,
    accepted_document_changes=accepted_changes, accepted_document_sha256=accepted,
    protected_tracked_source_diff_exit_code=0, git_diff_check_exit_code=0,
    missing_local_report_links=links, trailing_whitespace=whitespace,
    new_test_results='not_run', new_hpc_runs=[], reports_written=[str(p.relative_to(ROOT)) for p in reports]))
write('actual_commands.json', dict(scope='Static reads and document management only',
    local_commands=[
        'Get-Content AGENTS.md', 'Get-Content 硕士论文研究与实施说明书.md', 'Get-Content README.md',
        'git status --short', 'git rev-parse HEAD', 'git remote -v',
        'rg --files research/reports research/protocols research/logs gosc extensions',
        'Get-Content <specified reports/spec, task logs, execution indices, existing audit/report records>',
        'Get-Content <schemes/native_task_wire/budget_feasible_selector and related source>; line-numbered static views',
        '$rows=Get-Content <existing shadows.json> -Raw|ConvertFrom-Json; inspect $rows[0] only; no aggregates or reranking',
        'rg -n <function/candidate/decision definitions> <source paths>',
        'python research/logs/candidate-task-review-2026-10-30/verify_review.py',
        'git diff --exit-code HEAD -- gosc extensions', 'git diff --check'],
    file_editing='apply_patch: new reports/logs plus research/README.md entry only',
    internet_read_tools=['web search/open/find/click: original papers and official pages',
        'GitHub fetch: official Collab-Overcooked/MASBench/CoLLAB_SEA main README files'],
    scientific_commands=[], hpc_commands=[], model_commands=[]))
print(json.dumps(dict(status='static_review_management_verified', frozen_sources_unchanged=True,
    accepted_documents_unchanged=True, missing_links=links, tests_run=False, scientific_runs=[])))
