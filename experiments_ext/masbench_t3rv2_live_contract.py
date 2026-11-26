"""Registered new model-free deployment contracts; all transient files on HDD."""
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def main():
    from scripts.hpc_runs import require_hpc
    require_hpc();start=time.monotonic()
    resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    run=Path(os.environ['GOSC_RUN_DIR']);out=Path(os.environ['GOSC_OUTPUT_DIR'])
    tmp=Path('/hdd/u202520081000097/gosc-t3rv2-contracts')/run.name
    tmp.mkdir(parents=True,mode=0o700,exist_ok=False)
    command=[sys.executable,'-m','pytest','-q','tests_ext/test_masbench_t3rv2_live.py',
             '-p','no:cacheprovider','--basetemp',str(tmp/'pytest-tmp'),'--junitxml',str(out/'pytest.xml')]
    p=subprocess.run(command,timeout=110,env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1'))
    calls=[]
    for case in ET.parse(out/'pytest.xml').iter('testcase'):
        calls.append(dict(name=case.attrib['name'],passed=not any(case.find(k) is not None for k in ('failure','error','skipped'))))
    passed=p.returncode==0 and all(c['passed'] for c in calls)
    labels={f'D{i:02d}':sum(r['passed'] and f'D{i:02d}' in r['name'] for r in calls) for i in range(1,13)}
    passed=passed and all(labels.values())
    regular=[p for p in tmp.rglob('*') if p.is_file() and not p.is_symlink()]
    fixture_bytes=sum(p.stat().st_size for p in regular)
    passed=passed and fixture_bytes<=32*1024**2
    report=dict(passed=passed,tests=len(calls),calls=calls,labels=labels,model_calls=0,
                source_files={p:__import__('hashlib').sha256(Path(p).read_bytes()).hexdigest() for p in (
                    'extensions/masbench_reasoning/fair_final_v2_live.py','extensions/masbench_reasoning/fair_final_v2_runtime.py',
                    'experiments_ext/masbench_t3rv2_live_probe.py','tests_ext/test_masbench_t3rv2_live.py')},
                elapsed_seconds=time.monotonic()-start,hdd_fixture_root=str(tmp),
                hdd_fixture_regular_files=len(regular),hdd_fixture_bytes=fixture_bytes)
    (out/'contract.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=passed,tests=len(calls),labels=labels)))
    if not passed:raise SystemExit(1)


if __name__=='__main__':main()
