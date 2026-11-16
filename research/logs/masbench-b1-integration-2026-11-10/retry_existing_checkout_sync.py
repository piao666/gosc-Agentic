"""Management-only retry of the exact failed archive, preserving all guards.

An existing Git checkout is mandatory; the archived bundle is never used in
that path. Avoid materializing its duplicate under low quota. Keep any original
backup from the first attempt instead of replacing it with a partial file.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import remote_script
from sync_hpc import RECEIVER


def main():
    log=Path(__file__).resolve().parent
    info=json.loads((log/'failed_sync_archive_inventory.json').read_bytes())
    for e in info['manifest']['files']:
        p=ROOT/e['path']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=e['source_sha256']:
            raise RuntimeError('Local source changed; stale archive cannot be replayed: '+e['path'])
    assert info['manifest']['head']=='4754bede84bb6e6defd8e646a63e81ccd6a20b4b'
    assert info['manifest']['sync_id']=='20261110T035141Z'
    source=RECEIVER.replace(
        "        bundle.write_bytes(tf.extractfile('meta/repository.bundle').read())",
        "        if not (root / '.git').is_dir():\n            raise RuntimeError('Existing checkout required; bootstrap prohibited in retry')")
    source=source.replace('                shutil.copy2(dst,saved)',
                          '                if not saved.exists():\n                    shutil.copy2(dst,saved)')
    if source==RECEIVER or 'bundle.write_bytes(' in source:
        raise RuntimeError('Unexpected receiver implementation; refuse retry')
    prefix=('ARCHIVE='+repr(info['archive'])+'\nREMOTE_ROOT='+repr(info['manifest']['remote_root'])+
            '\nfrom pathlib import Path\nimport hashlib\n'+
            'assert hashlib.sha256(Path(ARCHIVE).read_bytes()).hexdigest()=='+repr(info['archive_sha256'])+'\n')
    r=remote_script(prefix+source)
    (log/'final_upload_retry_stdout.txt').write_bytes(r.stdout)
    (log/'final_upload_retry_stderr.txt').write_bytes(r.stderr)
    result={'exit_code':r.returncode,'same_archive_sha256':info['archive_sha256'],
            'retained_git_head_origin_running_payload_final_hash_guards':True,
            'original_backups_preserved':True,'no_tests_or_model_calls':True}
    if r.returncode==0:
        result['verified_receipt']=json.loads(r.stdout.decode().strip().splitlines()[-1])
    (log/'final_upload_retry_status.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
    raise SystemExit(r.returncode)


if __name__=='__main__':main()
