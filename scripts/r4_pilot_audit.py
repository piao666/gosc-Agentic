"""Independent raw-row, pairing and process-lifecycle audit of R4-A0 on HPC."""
from pathlib import Path
import argparse
import csv
import dataclasses
import hashlib
import json
import math
import os
import re
import sys

from hpc_runs import ROOT, require_hpc, write_json
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pilot-run',required=True);args=p.parse_args()
    require_hpc()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',args.pilot_run) or '..' in args.pilot_run:
        raise ValueError('Invalid pilot run ID')
    run=ROOT/'research/sync/runs'/args.pilot_run;source=run/'outputs';out=Path(os.environ['GOSC_OUTPUT_DIR'])
    plan=json.loads((source/'plan_snapshot.json').read_text());summary=json.loads((source/'pilot_summary.json').read_text())
    context=json.loads((source/'execution_context.json').read_text())
    assert hashlib.sha256((ROOT/'research/protocols/r4_plan_v1.json').read_bytes()).hexdigest()==context['plan_sha256']
    assert context['workers']==2 and context['worker_thread_limit']==1
    rows=[json.loads(line) for line in (source/'episodes.jsonl').read_text().splitlines()]
    expected={(scene['name'],seed,arm['scheme']) for scene in plan['pilot']['settings'] for seed in plan['pilot']['seeds'] for arm in scene['arms']}
    actual=[(r['setting'],r['seed'],r['scheme']) for r in rows]
    assert len(rows)==60 and len(set(actual))==60 and set(actual)==expected
    assert all(r['execution_status']=='completed' and r['process_exit_code']==0 for r in rows)
    from gosc import Config
    for scene in plan['pilot']['settings']:
        for arm in scene['arms']:
            expected_cfg=json.loads(json.dumps(dataclasses.asdict(Config().with_(**(scene['base_config']|arm['overrides'])))))
            for r in rows:
                if r['setting']==scene['name'] and r['scheme']==arm['scheme']:
                    assert r['config']==expected_cfg and r['output']['config']==expected_cfg
                    assert not r['config']['llm_agents'] and not r['config']['tom_oracle']
                    assert r['output']['worker_resources']['numeric_library_threads']==1
    for scene,seed in {(r['setting'],r['seed']) for r in rows}:
        assert len({r['output']['world_start_sha256'] for r in rows if r['setting']==scene and r['seed']==seed})==1
    groups=[]
    for group in summary['groups']:
        records=[r for r in rows if r['setting']==group['setting'] and r['scheme']==group['scheme']]
        results=[r['output']['result'] for r in records]
        assert len(results)==10
        for result_key,summary_key in [(group['metric'],'mean_outcome'),('symbols','mean_uplink_symbols'),('bits','mean_bits'),('found','mean_found'),('false_declarations','mean_false_declarations')]:
            assert math.isclose(math.fsum(r[result_key] for r in results)/10,group[summary_key],rel_tol=1e-12,abs_tol=1e-12)
        groups.append({'setting':group['setting'],'scheme':group['scheme'],'n':10,
                       'located_complete_missions':sum(r['completed'] for r in results),
                       'fully_saved_missions':sum(r.get('saved',-1)==8 for r in results) if group['metric']=='saved_fraction' else None})
    active=set();maximum=0;starts=0;ends=0
    for line in (source/'events.jsonl').read_text().splitlines():
        event=json.loads(line);key=event['job_id']
        if event['event']=='start':
            assert key not in active;active.add(key);starts+=1;maximum=max(maximum,len(active))
            assert len(active)<=2
        else:
            assert key in active;active.remove(key);ends+=1
    assert not active and starts==ends==60 and maximum==2
    csvrows=list(csv.DictReader((source/'metrics.csv').open()))
    assert len(csvrows)==60 and {r['job_id'] for r in csvrows}=={r['job_id'] for r in rows}
    for entry in json.loads((run/'artifacts.json').read_text())['files']:
        assert hashlib.sha256((run/entry['path']).read_bytes()).hexdigest()==entry['sha256'],entry['path']
    integrity=json.loads((source/'input_integrity.json').read_text());assert integrity['unchanged']
    for rel,digest in integrity['before'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,rel
    prior=ROOT/'research/sync/runs'/context['previous_unstarted_attempt']
    assert json.loads((prior/'status.json').read_text())['status']=='failed'
    assert not any((prior/'outputs'/name).exists() for name in ['events.jsonl','episodes.jsonl','execution_context.json'])
    assert not (ROOT/'.local/r4-worker-tmp'/prior.name).exists()
    value={'status':'verified','pilot_run':args.pilot_run,'unique_missions':60,'complete_three_arm_pairs':20,
           'configs_match_immutable_plan':True,'mean_metrics_match_raw_rows':True,
           'worker_starts':starts,'worker_terminals':ends,'max_concurrency':maximum,'unclosed_worker_events':len(active),
           'previous_failed_attempt_started_missions':0,'protected_inputs_unchanged':True,
           'task_outcome_counts':groups,'note':'Independent bookkeeping/mean audit; no additional scientific missions or parameter selection.'}
    write_json(out/'pilot_audit.json',value);print(json.dumps(value),flush=True)


if __name__=='__main__':main()
