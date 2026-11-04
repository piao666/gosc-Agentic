"""Lightweight document/file/Git checks only; no benchmark imports or task statistics."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

LOG = Path(__file__).resolve().parent
ROOT = LOG.parents[2]
OLD = LOG.parent / 'masbench-reasoning-static-2026-10-30'

def digest(path, lf=False):
    body = path.read_bytes()
    if lf:
        body = body.replace(b'\r\n', b'\n')
    return hashlib.sha256(body).hexdigest()

def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError((args, result.returncode, result.stderr))
    return result.stdout.strip()

head = git('rev-parse', 'HEAD')
assert head == '014b85dfc472c45d8ea5f15e83e0c1ed8e938daf'
freeze = json.loads((ROOT / 'research/sync/runs/hpc-native-information-freeze-20261030/outputs/frozen.json').read_text(encoding='utf-8'))
source_changes = [name for name, value in freeze['source_sha256'].items()
                  if digest(ROOT / name, True) != value]
assert not source_changes, source_changes
previous = json.loads((OLD / 'experiment_manifest.json').read_text(encoding='utf-8'))
protected_changes = [name for name, value in previous['protected_previous_report_sha256'].items()
                     if digest(ROOT / name) != value]
assert not protected_changes, protected_changes
git('diff', '--exit-code', 'HEAD', '--', 'gosc', 'extensions', 'tests', 'tests_ext', 'scripts')
git('diff', '--check')
reports = [ROOT / 'research/benchmarks' / name for name in (
    'masbench_reasoning_adapter_spec_v1.md', 'masbench_reasoning_feasibility_review.md',
    'masbench_reasoning_gate_matrix.md')]
docs = reports + list(LOG.glob('*.md'))
missing_links = []
whitespace = []
for path in docs:
    body = path.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)', body):
        destination = path.parent / target.split('#')[0]
        if '://' not in target and destination != LOG / 'verification.json' and not destination.exists():
            missing_links.append((str(path), target))
    whitespace.extend((str(path), number) for number, line in enumerate(body.splitlines(), 1)
                      if line.rstrip() != line)
assert not missing_links, missing_links
assert not whitespace, whitespace
for path in LOG.glob('*.json'):
    text = path.read_text(encoding='utf-8')
    if not text and path.name in {'environment_stdout.json', 'model_storage_stdout.json'}:
        inventory = json.loads((LOG / 'inventory.json').read_text(encoding='utf-8'))
        index = 0 if path.name == 'environment_stdout.json' else 1
        assert inventory['records'][index].get('exit_code') == 255
        continue
    json.loads(text)
source = (LOG / 'conversation_source.txt').read_bytes()
blob = hashlib.sha1(b'blob ' + str(len(source)).encode('ascii') + b'\0' + source).hexdigest()
assert blob == 'cf6612da2c813753c3f20d48f4bdd45a6a16656b', blob
record = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              scope='Local document, Git, JSON, source-identity and hash management; no project tests',
              baseline_head=head, frozen_source_file_count=len(freeze['source_sha256']),
              frozen_source_changes=source_changes, protected_previous_report_changes=protected_changes,
              tracked_scientific_source_diff_exit_code=0, git_diff_check_exit_code=0,
              missing_local_links=missing_links, trailing_whitespace=whitespace,
              conversation_git_blob_sha1=blob, conversation_bytes=len(source),
              hpc_current_environment='Pending: SSH timed out; no inference requested',
              new_project_tests_run=False, new_task_experiments=[], llm_calls=0,
              training=False, benchmark_integration=False, git_commit_or_push=False,
              document_sha256={str(path.relative_to(ROOT)): digest(path) for path in docs},
              previous_log_sha256={str(path.relative_to(ROOT)): digest(path)
                                   for path in OLD.iterdir() if path.is_file()},
              inventory_sha256=digest(LOG / 'inventory.json'))
(LOG / 'verification.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n',
                                     encoding='utf-8', newline='\n')
print(json.dumps(dict(status='management_checks_passed', frozen_sources=len(freeze['source_sha256']),
                      protected_reports_unchanged=True, project_tests_run=False, llm_calls=0)))
