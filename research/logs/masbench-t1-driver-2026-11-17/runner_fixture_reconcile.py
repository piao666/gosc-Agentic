"""Keep first-run evidence while moving three disposable proc fixture links."""
import json
from pathlib import Path
import shutil

run = Path('/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs/hpc-masbench-t1-runner-recovery-contract-20261118')
fixture = 'outputs/fixtures/test_runner_census_checks_parent_executable_model_and_start'
status = json.loads((run/'status.json').read_bytes())
assert status['status']=='failed' and status['error']=='Symlink artifact is not supported'
assert b'Ran 46 tests' in (run/'stderr.log').read_bytes()
regular = json.loads((run/'artifacts.json').read_bytes())['files']
indexed = {row['path'] for row in regular}
expected = {f'{fixture}/proc/{pid}/exe' for pid in (123,321,999)}
assert {p.relative_to(run).as_posix() for p in (run/'outputs').rglob('*') if p.is_symlink()}==expected
tmp = Path('/tmp/gosc-t1-runner-fixture-links-20261118')
tmp.mkdir(mode=0o700)
rows = []
for relative in sorted(expected):
    original = run/relative
    target = original.readlink()
    assert relative not in indexed and target==run/fixture/'ollama'
    destination = tmp/original.parent.name/'exe'
    destination.parent.mkdir()
    shutil.move(str(original),str(destination))
    assert destination.readlink()==target
    rows.append({'original':relative, 'symlink_target':str(target), 'preserved_at':str(destination)})
assert all((run/path).is_file() for path in indexed)
record = {'run_id':run.name,'status_preserved':'failed','relocated_fixture_symlinks':rows}
with (run/'fixture_symlink_reconciliation.json').open('x', encoding='utf-8') as stream:
    json.dump(record,stream,indent=2)
    stream.write('\n')
print(json.dumps(record))
