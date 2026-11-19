"""Prepare small, byte-identical T1 records from the existing HPC mirror."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SYNC = ROOT / 'research/sync'
ARCHIVE = ROOT / 'research/artifacts/masbench-t1-20261119'
SELECTED_OUTPUTS = {
    'outputs/audit.json',
    'outputs/summary.json',
    'outputs/driver/control.jsonl',
    'outputs/driver/campaign/ledger.jsonl',
}


def load(path):
    return json.loads(path.read_bytes())


def fingerprint(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def write_index(name, contents):
    (ARCHIVE / name).write_text(json.dumps(contents, indent=2, ensure_ascii=False) + '\n',
                               encoding='utf-8', newline='\n')


def main():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    directories = sorted(path for path in (SYNC / 'runs').glob('hpc-masbench-t1*') if path.is_dir())
    names = {path.name for path in directories}
    receipts = []
    for path in sorted((SYNC / 'receipts').glob('2026111[89]T*.json')):
        receipt = load(path)
        rows = [entry for entry in receipt['files'] if len(Path(entry['path']).parts) > 4
                and Path(entry['path']).parts[:3] == ('research', 'sync', 'runs')
                and Path(entry['path']).parts[3] in names]
        if rows:
            receipts.append(dict(fingerprint(path), sync_id=receipt['sync_id'],
                                 all_outputs_mirrored=receipt.get('all_outputs_mirrored'),
                                 scope_complete=receipt.get('scope_complete'),
                                 bytes_downloaded=receipt.get('bytes_downloaded'),
                                 bytes_verified=receipt.get('bytes_verified'),
                                 total_inventory_files=len(receipt['files']),
                                 selected_run_files=rows))

    copies, runs = [], []
    for directory in directories:
        manifest_file = directory / 'manifest.json'
        status_file = directory / 'status.json'
        artifacts_file = directory / 'artifacts.json'
        manifest, status = load(manifest_file), load(status_file)
        artifacts = load(artifacts_file)['files']
        assert manifest['run_id'] == status['run_id'] == directory.name
        snapshot = fingerprint(directory / 'source_snapshot.json')
        assert snapshot['sha256'] == manifest['source_manifest_sha256']

        archived = []
        for entry in artifacts:
            if entry['path'] not in SELECTED_OUTPUTS:
                continue
            source = directory / entry['path']
            assert source.is_file() and not source.is_symlink() and source.stat().st_size <= 256 * 1024
            raw = source.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            assert len(raw) == entry['size'] and sha == entry['sha256'], str(source)
            target = ARCHIVE / f'{directory.name}__{source.name}'
            if target.exists():
                assert target.read_bytes() == raw, str(target)
            else:
                target.write_bytes(raw)
            item = dict(fingerprint(target), source_path=source.relative_to(ROOT).as_posix(),
                        run_id=directory.name, artifact_index=artifacts_file.relative_to(ROOT).as_posix())
            copies.append(item)
            archived.append(item['path'])

        runs.append({'run_id': directory.name, 'state': status, 'command': manifest['command'],
                     'git_commit': manifest['git_commit'], 'source_sync_id': manifest.get('source_sync_id'),
                     'registered_outputs': len(artifacts), 'registered_bytes': sum(e['size'] for e in artifacts),
                     'archived_outputs': archived, 'manifest': fingerprint(manifest_file),
                     'status': fingerprint(status_file), 'source_snapshot': snapshot,
                     'artifact_index': fingerprint(artifacts_file)})

    counts = dict(Counter(run['state']['status'] for run in runs))
    assert set(counts) == {'completed', 'failed'}
    write_index('run_index.json', {'status_counts': counts, 'runs': runs})
    write_index('provenance.json', {'policy': 'byte-identical copies from registered synthetic output', 'files': copies})
    write_index('receipt_index.json', {'policy': 'full receipts retained at their original paths; T1 entries only',
                                      'receipts': receipts})
    print(json.dumps({'runs': len(runs), 'states': counts, 'copies': len(copies),
                      'copy_bytes': sum(item['bytes'] for item in copies), 'receipts': len(receipts),
                      'receipt_original_bytes': sum(item['bytes'] for item in receipts)}))


if __name__ == '__main__':
    main()
