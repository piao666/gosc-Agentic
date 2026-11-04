"""Document/hash management only; no project tests or scientific computation."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

LOG = Path(__file__).resolve().parent
ROOT = LOG.parents[2]
def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))
def sha(path, lf=False):
    data = (ROOT / path).read_bytes()
    return hashlib.sha256(data.replace(b'\r\n', b'\n') if lf else data).hexdigest()
def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()
head = git('rev-parse', 'HEAD')
assert head == '014b85dfc472c45d8ea5f15e83e0c1ed8e938daf'
freeze = read('research/sync/runs/hpc-native-information-freeze-20261030/outputs/frozen.json')
assert all(sha(p, True) == value for p, value in freeze['source_sha256'].items())
prior = read('research/logs/masbench-reasoning-static-2026-10-30/experiment_manifest.json')
assert all(sha(p) == value for p, value in prior['protected_previous_report_sha256'].items())
earlier = read('research/logs/masbench-reasoning-static-2026-11-02/verification.json')
assert all(sha(p) == value for p, value in earlier['previous_log_sha256'].items())
git('diff', '--exit-code', 'HEAD', '--', 'gosc', 'extensions', 'tests', 'tests_ext', 'scripts')
git('diff', '--check')
inventory = json.loads((LOG / 'inventory.json').read_text(encoding='utf-8'))
assert all(item['exit_code'] == 0 for item in inventory['records'])
environment = inventory['records'][0]['inventory']
assert environment['uid'] == 8301880 and environment['git_head']['stdout'] == head
assert not environment['inference_requested'] and not inventory['llm_calls']
docs = list((ROOT / 'research/benchmarks').glob('masbench_reasoning_*.md')) + list(LOG.glob('*.md'))
for path in docs:
    body = path.read_text(encoding='utf-8')
    assert all(line == line.rstrip() for line in body.splitlines()), str(path)
    for target in re.findall(r'\]\(([^)]+)\)', body):
        if '://' not in target:
            destination = path.parent / target.split('#')[0]
            assert destination.exists() or destination == LOG / 'verification.json', str(destination)
for path in LOG.glob('*.json'):
    json.loads(path.read_text(encoding='utf-8'))
record = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              scope='Lightweight management only', head=head, frozen_sources_unchanged=73,
              protected_previous_reports_unchanged=True, original_static_logs_unchanged=True,
              git_diff_check_exit_code=0, protected_source_diff_exit_code=0,
              hpc_inventory_exit_codes=[item['exit_code'] for item in inventory['records']],
              project_tests_run=False, llm_calls=0, new_scientific_runs=[], git_commit_or_push=False,
              previous_failed_inventory_sha256=sha('research/logs/masbench-reasoning-static-2026-11-02/inventory.json'),
              previous_failed_verification_sha256=sha('research/logs/masbench-reasoning-static-2026-11-02/verification.json'),
              documents_sha256={str(p.relative_to(ROOT)): sha(p.relative_to(ROOT)) for p in docs},
              inventory_sha256=sha(LOG.relative_to(ROOT) / 'inventory.json'))
(LOG / 'verification.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n',
                                     encoding='utf-8', newline='\n')
print(json.dumps(dict(status='management_checks_passed', frozen_sources_unchanged=73,
                      hpc_inventory_exit_codes=[0, 0], project_tests_run=False, llm_calls=0)))
