"""Remove only two explicitly inventoried unrelated HPC projects per user authorization."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from hpc_runs import ROOT, require_hpc, write_json


def main():
    require_hpc()
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    plan=json.loads((ROOT/'research/protocols/ollama_storage_cleanup_v1.json').read_text())
    parent=Path(plan['allowed_parent']).resolve()
    protected=ROOT.resolve()
    targets=[]
    mountpoints=[Path(line.split()[4].replace('\\040',' ')) for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    for item in plan['targets']:
        path=parent/item['name']
        resolved=path.resolve(strict=True)
        assert path.is_dir() and not path.is_symlink() and path.stat().st_uid==8301880
        assert resolved.parent==parent and resolved!=protected and resolved not in protected.parents and protected not in resolved.parents
        assert not any(m==resolved or resolved in m.parents for m in mountpoints)
        actual=int(subprocess.check_output(['du','-sxB1',str(resolved)]).split()[0])
        assert actual==item['size_before_bytes'],'Inventory changed; stop before any deletion'
        targets.append({'path':str(resolved),'uid':path.stat().st_uid,'size_before_bytes':actual})
    # All target checks finish before any recursive removal. Preserve the current source digest.
    protected=ROOT/'AGENTS.md';before=hashlib.sha256(protected.read_bytes()).hexdigest()
    write_json(out/'cleanup_plan_verified.json',{'targets':targets,'protected_project':str(ROOT),'protected_agents_sha256':before,'authorization':plan['authorization']})
    started=time.monotonic()
    for item in targets:
        path=Path(item['path'])
        assert path.resolve().parent==parent and path.name in ['Github--llm','HM']
        shutil.rmtree(path)
        item['deleted']=not path.exists()
        write_json(out/'cleanup_progress.json',{'targets':targets})
        print('Deleted unrelated project '+str(path),flush=True)
    assert hashlib.sha256(protected.read_bytes()).hexdigest()==before
    write_json(out/'cleanup_result.json',{'status':'completed','targets':targets,
        'inventory_allocated_bytes_removed':sum(item['size_before_bytes'] for item in targets),
        'current_project_preserved':True,'elapsed_seconds':time.monotonic()-started,
        'note':'Bytes from pre-delete du allocation; quota accounting may update asynchronously.'})
    # Restore our official archive to persistent project storage once quota is released.
    source=Path('/tmp/gosc-ollama-8301880/ollama-linux-amd64-0.11.11.tgz')
    destination=ROOT/'.local/ollama/downloads/ollama-linux-amd64-0.11.11.tgz'
    assert not destination.exists() and not source.is_symlink()
    for attempt in range(12):
        temp=destination.with_suffix('.restoring')
        try:
            shutil.copyfile(source,temp)
            with temp.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
            assert actual=='1d2988c29346e6af0216c847db20f7df7794412ae56674eeec21e0917113843f'
            temp.rename(destination)
            source.unlink()
            write_json(out/'archive_restored.json',{'path':str(destination),'sha256':actual,'size':destination.stat().st_size,'tmp_copy_removed_after_verification':True})
            return
        except OSError as error:
            if error.errno!=122:raise
            if temp.exists():temp.unlink()
            if attempt==11:raise
            time.sleep(5)


if __name__=='__main__':main()
