"""Registered task-only model-free acceptance; prior contracts are not rerun."""
import hashlib,json,os,resource,signal,subprocess,sys,tarfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
from scripts.hpc_runs import require_hpc
from extensions.masbench_reasoning.fair_final_v2_task import MATERIAL_FILES


def main():
    require_hpc();start=time.monotonic()
    resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(TimeoutError('contract120')));signal.alarm(120)
    out=Path(os.environ['GOSC_OUTPUT_DIR']);run=Path(os.environ['GOSC_RUN_DIR'])
    tmp=Path('/hdd/u202520081000097/gosc-t3rv2t-contracts')/run.name
    tmp.mkdir(parents=True,exist_ok=False,mode=0o700)
    code=1
    try:
        code=subprocess.run([sys.executable,'-m','pytest','-q','tests_ext/test_masbench_t3rv2t_task.py','-p','no:cacheprovider','--basetemp',str(tmp/'pytest-tmp'),'--junitxml',str(out/'pytest.xml')],timeout=110,env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1')).returncode
    finally:
        files=[]
        for p in sorted(tmp.rglob('*')):
            if p.is_file() and not p.is_symlink():files.append(dict(path=p.relative_to(tmp).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        total=sum(p['bytes'] for p in files)
        if total>64*1024**2:raise RuntimeError('64MiB fixture cap')
        (out/'hdd_inventory.json').write_text(json.dumps(dict(root=str(tmp),files=files),indent=2)+'\n')
        with tarfile.open(out/'fixture_raw.tar.gz','w:gz') as tar:
            for row in files:tar.add(tmp/row['path'],arcname=row['path'],recursive=False)
        cases=[]
        if (out/'pytest.xml').exists():
            for c in ET.parse(out/'pytest.xml').iter('testcase'):cases.append(dict(name=c.attrib['name'],passed=not any(c.find(k) is not None for k in ('failure','error','skipped'))))
        labels={f'T{i:02d}':sum(c['passed'] and f'T{i:02d}' in c['name'] for c in cases) for i in range(1,17)}
        paths=list(MATERIAL_FILES)+['tests_ext/test_masbench_t3rv2t_task.py','experiments_ext/masbench_t3rv2t_contract.py']
        report=dict(passed=code==0 and bool(cases) and all(labels.values()),tests=len(cases),cases=cases,labels=labels,elapsed_seconds=time.monotonic()-start,fixture_bytes=total,source_files={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths},model_calls=0,real_HTTP=0,real_helper_calls=0,service_switches=0,real_task_records_read=0,fixture_AS_bytes=256*1024**2,max_workers=1)
        (out/'contract.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
