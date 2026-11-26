"""Versioned registration adapter: source patch excludes HPC-owned data lane.

The upstream runner remains byte-identical. Full runtime records stay in their
original run store; they are not recursively embedded into every source patch.
All actual source/config changes and the upstream sync snapshot remain bound.
"""
import hashlib
import sys
from pathlib import Path
import subprocess

from scripts import hpc_runs

EXCLUDED = ['research/sync/runs/**', 'research/sync/receipts/**',
            'research/sync/dashboard.json', 'research/sync/STATUS.md']
ORIGINAL_OUTPUT = subprocess.check_output
ORIGINAL_WRITE = hpc_runs.write_json


def source_diff_only(command, *args, **kwargs):
    expected = ['git', '-C', str(hpc_runs.ROOT), 'diff', '--binary', 'HEAD']
    if command == expected:
        command = command + ['--', '.'] + [':(exclude)' + p for p in EXCLUDED]
    return ORIGINAL_OUTPUT(command, *args, **kwargs)


def annotated_write(path, value):
    if Path(path).name == 'manifest.json' and value.get('run_id', '').startswith('hpc-t3rv2i-'):
        value = dict(value, source_changes_scope='all worktree source except declared HPC-owned runtime lane',
                     source_changes_excluded=EXCLUDED,
                     registration_adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     upstream_runner_unchanged=True)
    return ORIGINAL_WRITE(path, value)


if __name__ == '__main__':
    assert len(sys.argv) > 2 and sys.argv[1] == 'run'
    index = sys.argv.index('--run-id')
    assert sys.argv[index + 1].startswith('hpc-t3rv2i-')
    subprocess.check_output = source_diff_only
    hpc_runs.write_json = annotated_write
    raise SystemExit(hpc_runs.main())
