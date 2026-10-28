"""One registered bounded acceptance job, sequential auditable substages."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def write(path,data):
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contracts-run',required=True);a=p.parse_args()
    if not (os.name=='posix' and os.getuid()==8301880 and str(ROOT)=='/home/u202520081000097/jupyterlab/Paper/gosc'
            and os.environ.get('GOSC_RUN_DIR') and os.environ.get('GOSC_OUTPUT_DIR')):
        raise RuntimeError('Registered HPC only')
    out=Path(os.environ['GOSC_OUTPUT_DIR']);records=[]
    def stage(name,script,args,seconds):
        directory=out/name;directory.mkdir(exist_ok=False)
        command=[sys.executable,str(ROOT/script),*map(str,args)]
        env=dict(os.environ,GOSC_OUTPUT_DIR=str(directory))
        record=dict(stage=name,status='running',command=command,timeout_seconds=seconds)
        write(directory/'stage_status.json',record)
        started=time.monotonic()
        try:
            with (directory/'stdout.log').open('w') as stdout,(directory/'stderr.log').open('w') as stderr:
                result=subprocess.run(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=seconds)
            record.update(status='completed' if result.returncode==0 else 'failed',exit_code=result.returncode)
            if result.returncode:raise RuntimeError('Substage failed: '+name)
        except Exception as exc:
            record.update(status='failed',error=repr(exc));raise
        finally:
            record['elapsed_seconds']=time.monotonic()-started
            write(directory/'stage_status.json',record);records.append(record)
            write(out/'stages.json',records)
            print(json.dumps({k:record[k] for k in ('stage','status','elapsed_seconds')}),flush=True)
    frozen=out/'prepare/frozen.json';replay=out/'replay/replay.json';fixtures=out/'fixtures/fixtures.json'
    stage('prepare','scripts/repro_budget_feasible_selector.py',
        ['--mode','prepare','--contracts-run',a.contracts_run],90)
    first=ROOT/'research/sync/runs/hpc-budget-selector-prepare-20261027/outputs/catalogs.jsonl.gz'
    current=out/'prepare/catalogs.jsonl.gz'
    if hashlib.sha256(current.read_bytes()).digest()!=hashlib.sha256(first.read_bytes()).digest():
        raise RuntimeError('Sample changed across numeric-domain guard revision')
    stage('binding','scripts/audit_budget_selector_input_binding.py',['--frozen',frozen],120)
    stage('replay','scripts/repro_budget_feasible_selector.py',['--mode','replay','--frozen',frozen],180)
    stage('fixtures','scripts/repro_budget_feasible_selector.py',['--mode','fixtures','--frozen',frozen],120)
    stage('audit','scripts/audit_budget_feasible_selector.py',
        ['--frozen',frozen,'--replay',replay,'--fixtures',fixtures],120)
    stage('summary','scripts/summarize_budget_selector_acceptance.py',
        ['--frozen',frozen,'--replay',replay,'--fixtures',fixtures,'--audit',out/'audit/audit.json',
         '--binding',out/'binding/binding.json'],60)
    summary=json.loads((out/'summary/summary.json').read_text())
    if summary['status']!='engineering_acceptance_passed':raise RuntimeError('Acceptance not passed')
    write(out/'acceptance.json',dict(status='passed',stages=records,efficacy_N=0,
        frozen_sha256=hashlib.sha256(frozen.read_bytes()).hexdigest(),
        scientific_status='Original No-Go retained',formal_test=False,training=False))


if __name__=='__main__':main()
