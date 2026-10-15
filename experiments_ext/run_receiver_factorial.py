"""Execute the previously frozen receiver diagnostic only after R4-S1 passes."""
import argparse
import datetime as dt
from dataclasses import asdict
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
import traceback

for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
os.environ.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',MPLBACKEND='Agg')

from experiments_ext.reproduce import ROOT,save,sha,git,check_protected
from experiments_ext.campaign import diagnostic_jobs,_job,config_key
from experiments_ext.statistical_reproduction import verify_plan,OLD


def execute(run,workers):
    verify_plan(run)
    gate=json.loads((run/'r4-statistical/gate.json').read_text())
    if gate['status']!='scoped_statistical_agreement' or not gate['receiver_diagnostics_allowed']:
        raise RuntimeError('R4-S1 did not pass; receiver diagnostic remains forbidden')
    if gate.get('primary_family')!=104 or gate.get('completed_fresh')!=5200:
        raise RuntimeError('Incomplete statistical gate')
    agreement_path=run/'r4-statistical/agreement.json'
    if sha(agreement_path)!=gate['agreement_sha256']:
        raise RuntimeError('Statistical evidence changed')
    agreement=json.loads(agreement_path.read_text())
    if not agreement['all_equivalent'] or len(agreement['results'])!=104:
        raise RuntimeError('Statistical intervals did not all pass')
    contract=json.loads((OLD/'diagnostic_contract_tests.json').read_text())
    if contract['status']!='passed' or contract['code_sha256']!=sha(ROOT/'extensions/receiver_oracle.py'):
        raise RuntimeError('Diagnostic adapter contract no longer matches tested source')
    prereg=json.loads((OLD/'diagnostic_preregistration.json').read_text())
    if prereg['seeds']!=list(range(4000,4100)) or prereg['modes']!=['shared','private','position','joint']:
        raise RuntimeError('Frozen diagnostic differs')
    jobs=diagnostic_jobs()
    if len(jobs)!=1200:raise RuntimeError('Wrong diagnostic count')
    out=run/'diagnostic';out.mkdir(exist_ok=False)
    configs={config_key(j['cfg']):asdict(j['cfg']) for j in jobs}
    save(out/'configs.json',configs)
    with (out/'campaign_source.py').open('xb') as f:f.write(Path(__file__).read_bytes())
    save(out/'plan.json',dict(stage='receiver-factorial',jobs=1200,workers=workers,
        git_commit=git('rev-parse','HEAD'),working_tree_dirty=bool(git('status','--short')),
        python=sys.version,dependencies_lock_sha256=sha(ROOT/'requirements-windows.lock.txt'),
        configs_sha256=sha(out/'configs.json'),seeds=list(range(4000,4100)),
        modes=prereg['modes'],source_sha256=sha(__file__),adapter_sha256=contract['code_sha256'],
        inherited_preregistration_sha256=sha(OLD/'diagnostic_preregistration.json'),
        gate_sha256=sha(run/'r4-statistical/gate.json'),bootstrap_resamples=4000,
        primary_comparisons=6,practical_threshold_shared_time_fraction=.05,
        max_elapsed_seconds=1500,
        notes='Privileged states, original fixed eta, synchronization cost uncharged. Not deployable or cost-matched.'))
    start=time.perf_counter();count=0;started=dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        with (out/'raw.jsonl').open('x',encoding='utf-8') as f,mp.Pool(workers) as pool:
            iterator=pool.imap_unordered(_job,jobs,chunksize=1)
            while count<len(jobs):
                if time.perf_counter()-start>1500:raise TimeoutError('Diagnostic budget exceeded')
                try:row=iterator.next(timeout=30)
                except mp.TimeoutError:
                    print('Receiver heartbeat',count,round(time.perf_counter()-start),flush=True);continue
                f.write(json.dumps(row,allow_nan=False)+'\n');count+=1
                if row['status']!='completed':raise RuntimeError('Diagnostic mission failed')
                if count%100==0 or count==len(jobs):
                    f.flush();print(f'Receiver {count}/1200 elapsed={time.perf_counter()-start:.1f}s',flush=True)
    except Exception:
        save(out/'failure.json',dict(status='failed',completed=count,traceback=traceback.format_exc()));raise
    save(out/'manifest.json',dict(status='passed',meaning='Complete valid execution, not performance improvement',
        completed=1200,seeds=list(range(4000,4100)),start_utc=started,elapsed_seconds=time.perf_counter()-start,
        raw_output_paths=[str(out/'raw.jsonl')],raw_sha256=sha(out/'raw.jsonl'),
        original_r4_status='failed_preserved',r4_s1_gate=gate['status'],
        protected_inputs=check_protected(OLD),notes='No training/tuning; uncharged privileged information; fixed realized costs not matched.'))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id',required=True);ap.add_argument('--workers',type=int,choices=range(1,5),default=4)
    args=ap.parse_args()
    if Path(args.run_id).name!=args.run_id or args.run_id in ('.','..'):ap.error('Invalid run-id')
    execute(ROOT/'.local/reproduction'/args.run_id,args.workers)


if __name__=='__main__':
    mp.freeze_support();main()
