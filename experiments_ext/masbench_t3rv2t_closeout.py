"""Registered live run and automatic closeout, entered from the Windows host."""
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import time
import uuid

from experiments_ext.masbench_t3rv2t_admission_paths import AUDIT_ID, LIVE_HDD, LIVE_ID

ROOT = Path(__file__).resolve().parents[1]
REMOTE = '/home/u202520081000097/jupyterlab/Paper/gosc'
MODULE = 'experiments_ext.masbench_t3rv2t_closeout'
AUTH = ROOT / 'research/protocols/masbench_t3rv2t_authorization_2026-11-26.json'
CAP = 1024**3 + 32 * 1024**2
SSH = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'hpc']


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def require(condition, label):
    if not condition:
        raise ValueError(label)


def indexed_files(root, prefix):
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink() and (path.is_file() or path.is_dir()), 'unsupported_evidence_type')
        if path.is_file():
            yield str(PurePosixPath(prefix) / path.relative_to(root).as_posix()), path


def stream_archive(roots, output):
    paths = {}
    for root, prefix in roots:
        require(root.is_dir() and not root.is_symlink(), 'evidence_root')
        for key, path in indexed_files(root, prefix):
            require(key not in paths, 'duplicate_evidence_path')
            paths[key] = path
    require(sum(path.stat().st_size for path in paths.values()) <= CAP, 'closeout_byte_cap')
    index = {key: dict(bytes=path.stat().st_size, sha256=sha(path)) for key, path in paths.items()}
    raw = json.dumps(index, sort_keys=True).encode()
    require(len(raw) <= 8 * 1024**2, 'transfer_inventory_cap')
    with tarfile.open(fileobj=output, mode='w|') as tar:
        info = tarfile.TarInfo('transfer-index.json')
        info.size = len(raw)
        tar.addfile(info, io.BytesIO(raw))
        for key, path in paths.items():
            tar.add(path, arcname=key, recursive=False)


def restore_archive(archive, target):
    with tarfile.open(archive, mode='r|') as tar:
        first = tar.next()
        require(first and first.name == 'transfer-index.json' and first.isfile() and first.size <= 8*1024**2, 'transfer_index')
        expected = json.load(tar.extractfile(first))
        require(sum(row['bytes'] for row in expected.values()) <= CAP, 'transfer_byte_cap')
        seen = set()
        while member := tar.next():
            key = member.name
            path = PurePosixPath(key)
            require(member.isfile() and key in expected and key not in seen and not path.is_absolute()
                    and '..' not in path.parts and '\\' not in key and ':' not in key, 'transfer_file_set')
            row = expected[key]
            require(member.size == row['bytes'], 'transfer_file_size')
            dst = target.joinpath(*path.parts)
            dst.parent.mkdir(parents=True, exist_ok=True)
            require(target.resolve() in dst.resolve().parents, 'transfer_path_escape')
            with dst.open('xb') as output:
                shutil.copyfileobj(tar.extractfile(member), output, length=1024**2)
            require(sha(dst) == row['sha256'], 'transfer_file_sha')
            seen.add(key)
        require(seen == expected.keys(), 'incomplete_transfer')
    return expected


def paths():
    return ROOT / 'research/sync/runs' / LIVE_ID, ROOT / 'research/sync/runs' / AUDIT_ID


def register(run_id, kind, module):
    return subprocess.run([sys.executable, '-m', 'experiments_ext.masbench_t3rv2i_register', 'run',
                           '--run-id', run_id, '--kind', kind, '--stage', 'T3-R-v2-T', '--purpose', module,
                           '--gzip-source-patch', '--', sys.executable, '-m', 'experiments_ext.' + module]).returncode


def remote_entry(action):
    from scripts.hpc_runs import require_hpc
    require_hpc()
    run, audit = paths()
    if action == 'run':
        auth = read(AUTH)
        require(auth['approved'] is True and auth['run_id'] == LIVE_ID and not run.exists() and not audit.exists(), 'single_use_authorization')
        code = register(LIVE_ID, 'test', 'masbench_t3rv2t_task')
        if (run / 'status.json').exists():
            audited = register(AUDIT_ID, 'analysis', 'masbench_t3rv2t_live_audit')
            code = code or audited
        return code
    if action == 'stream':
        for item in (run, audit):
            require(read(item / 'status.json')['status'] in ('completed', 'failed', 'interrupted'), 'closeout_requires_terminal_run')
        roots = [(run, 'run'), (audit, 'audit')]
        hdd = LIVE_HDD / LIVE_ID
        if hdd.exists():
            roots.append((hdd, 'hdd'))
        stream_archive(roots, sys.stdout.buffer)
        return 0
    if action == 'ack':
        receipt = json.load(sys.stdin)
        require(receipt['run_id'] == LIVE_ID and receipt['all_outputs_mirrored'] is True, 'receipt_scope')
        artifact = run / 'outputs/hdd_inventory.json'
        source = LIVE_HDD / LIVE_ID / 'budget/ledger.jsonl'
        receipt['live_inventory_sha256'] = sha(artifact) if artifact.exists() else None
        result = audit / 'outputs/live_audit.json'
        audit_report = read(result) if result.exists() else {}
        # Use registered UTC start, earlier than any request or journal reservation.
        started = datetime.fromisoformat(read(run / 'status.json')['started_at']).timestamp()
        receipt['elapsed_since_registered_start_seconds'] = time.time() - started
        receipt['deadline_met'] = 0 <= receipt['elapsed_since_registered_start_seconds'] <= 18360
        receipt['independent_audit_passed'] = audit_report.get('passed') is True
        receipt['ledger_sha256'] = sha(source) if source.exists() else None
        path = ROOT / 'research/sync/receipts' / (LIVE_ID + '.json')
        # Keep the first terminal receipt, including a late or failed disposition.
        raw = json.dumps(receipt, indent=2, sort_keys=True).encode() + b'\n'
        with path.open('xb') as stream:
            stream.write(raw)
        sys.stdout.buffer.write(raw)
        return 0
    raise ValueError('unknown_closeout_action')


def local_entry(collect_only=False):
    """One launch permission covers execution, audit, transfer and receipt."""
    if not collect_only:
        require(read(AUTH)['approved'] is True, 'local_authorization_required')
    target = ROOT / '.local/hpc-runs' / LIVE_ID / ('return-' + uuid.uuid4().hex[:10] if collect_only else 'first')
    target.mkdir(parents=True, exist_ok=False, mode=0o700)
    command = SSH + [f'cd {REMOTE} && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m {MODULE}']
    if not collect_only:
        try:
            subprocess.run(command[:-1] + [command[-1] + ' run'], timeout=17760, check=False)
        except subprocess.TimeoutExpired:
            print('Execution connection timed out. Attempting terminal evidence transfer.', file=sys.stderr)
    start = time.monotonic()
    archive = target / 'complete.tar'
    with archive.open('xb') as stream:
        subprocess.run(command[:-1] + [command[-1] + ' stream'], timeout=600, stdout=stream, check=True)
    require(archive.stat().st_size <= CAP + 32*1024**2, 'tar_file_cap')
    files = restore_archive(archive, target / 'mirror')
    receipt = dict(run_id=LIVE_ID, all_outputs_mirrored=True, archive_sha256=sha(archive),
                   files=len(files), bytes=sum(row['bytes'] for row in files.values()))
    remaining = 600 - (time.monotonic() - start)
    require(remaining > 0, 'transfer_600s_exceeded')
    raw = subprocess.check_output(command[:-1] + [command[-1] + ' ack'], input=json.dumps(receipt).encode(), timeout=remaining)
    (target / 'receipt.json').write_bytes(raw)
    final = json.loads(raw)
    print(json.dumps(final))
    return 0 if final['deadline_met'] and final['independent_audit_passed'] else 1


if __name__ == '__main__':
    action = sys.argv[1]
    if action in ('launch', 'collect-only'):
        raise SystemExit(local_entry(action == 'collect-only'))
    raise SystemExit(remote_entry(action))
