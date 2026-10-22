"""Post-audit conditional protocol diagnostic, all traces are reused calibration worlds."""
import os,sys,json,signal
from pathlib import Path
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc,digest
from repro_summary_audit import Observer,scalar_result
from extensions.receiver_transport_replay import replay
from gosc import Config
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
class PayloadObserver(Observer):
    def phase_decide(self,t):
        super().phase_decide(t)
        for a in self.agents:self.by_slot_agent[(t,a.idx)]['pose_cell']=int(a.pos[0]*self.cfg.grid+a.pos[1])
def main():
    require_hpc()
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('Transport audit10min bound')));signal.alarm(600)
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    old=ROOT/'research/sync/runs/hpc-summary-cost-audit-20261022/outputs'
    evidence=json.loads((old/'evidence.json').read_text());guards=json.loads((old/'guard_replays.json').read_text())
    old_rows=[json.loads(x) for x in (old/'observations.jsonl').read_text().splitlines()]
    expected={(x['W'],x['seed'],x['t'],x['agent']):x for x in old_rows}
    results=[];replays=[]
    with (out/'payload_observations.jsonl').open('x') as f,(out/'transport_events.jsonl').open('x') as events:
        for s in evidence['scenarios']:
            raw=dict(s['config']);raw['rates']=tuple(raw['rates']);raw['llm_agents']=tuple(raw['llm_agents'])
            sim=PayloadObserver(Config(**raw),'gosc',s['seed']);sim.seed_label=s['seed'];actual=sim.run()
            guard=next(g for g in guards if g['W']==s['W'] and g['seed']==s['seed'])
            assert scalar_result(actual)==guard['original_result'];assert sim.input_world_sha256==guard['world_sha256']
            for row in sim.audit_rows:
                prior=expected[(row['W'],row['seed'],row['t'],row['agent'])]
                assert {k:row[k] for k in prior}==prior
                f.write(json.dumps(row)+'\n')
            replays.append({'W':s['W'],'seed':s['seed'],'original_result_and_all_prior_observation_rows':'exact_match','world_sha256':sim.input_world_sha256})
            for interval in [1,5,10]:
                for with_pose in [False,True]:
                    for loss in [0.,.1]:
                        for delay in [0,2]:
                            r=replay(sim.audit_rows,interval,with_pose,loss,delay,s['seed'],s['W'])
                            r['scenario_id']=len(results)
                            for ev in r.pop('events'):events.write(json.dumps({'scenario_id':r['scenario_id'],**ev})+'\n')
                            results.append(r)
    save(out/'transport_replay.json',results);save(out/'observation_guards.json',replays)
    paths=['extensions/receiver_summary_audit.py','extensions/receiver_transport_replay.py','scripts/repro_summary_audit.py','scripts/repro_summary_transport_audit.py','tests_ext/test_receiver_transport_replay.py','research/protocols/receiver_summary_transport_audit_v1.json']
    save(out/'evidence.json',{'source_sha256':{p:digest(ROOT/p) for p in paths},'input_cost_audit_evidence_sha256':digest(old/'evidence.json'),
         'input_observations_sha256':digest(old/'observations.jsonl'),'calibration_worlds_reused':True,'new_test_worlds':0})
    save(out/'conclusion.json',{'status':'conditional_encoded_transport_replay_completed','scenario_count':len(results),'baseline_replays':len(replays),
        'all_budget_invariants_passed':all(x['ul_residual_budget_invariant'] for x in results),
        'task_policy_uses_receiver_summaries':False,'task_effect':'not_measured','complex_training_go':False,
        'scope':'R1 independent orthogonal residual-only summary transport on H0 native task traces; explicit CRC control/snapshot frames; DLloss/extra delay conditional model; not complete matched-H paid method or real RF measurement'})
    print(json.dumps({'status':'completed','transport_scenarios':len(results),'all_baseline_guards':'passed','all_UL_budget_guards':'passed'}))
if __name__=='__main__':main()
