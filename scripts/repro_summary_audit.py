"""Bounded HPC audit of payload information and observable synchronization costs; no policy intervention."""
import os,sys,json,time,math,hashlib,statistics,dataclasses,signal
from pathlib import Path
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc,digest
from gosc import Config
from extensions.receiver_diagnostic import EventSimulation
from extensions.receiver_summary_audit import encode,crc_frame,unframe,private_novelty_bucket,symbols
import numpy as np
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def scalar_result(r):return {k:v for k,v in r.items() if k!='curve'}
class Observer(EventSimulation):
    def __init__(self,cfg,scheme,seed):
        super().__init__(cfg,scheme,seed);self.audit_rows=[];self.by_slot_agent={};self.timings=[];self.first_sample=None
        native=self.scheme.transmit
        def wrapper(a,t,mean,instant,view):
            res=native(a,t,mean,instant,view)
            row=self.by_slot_agent[(t,a.idx)]
            row.update(snr_mean=float(mean),snr_instant=float(instant),original_used=int(res.symbols))
            return res
        self.scheme.transmit=wrapper
    def phase_decide(self,t):
        super().phase_decide(t)
        for a in self.agents:
            view=self.view(a)
            started=time.perf_counter_ns()
            bucket,tv=private_novelty_bucket(view.Lc,a.pending_llr,view.declared)
            app=encode(a.idx,t,bucket);pose=a.pos[0]*self.cfg.grid+a.pos[1]
            both=encode(a.idx,t,bucket,pose)
            elapsed=time.perf_counter_ns()-started
            self.timings.append(elapsed)
            if self.first_sample is None:self.first_sample=(view.Lc.copy(),a.pending_llr.copy(),view.declared.copy(),a.idx,t,pose)
            row={'seed':self.seed_label,'W':self.cfg.symbols_per_slot,'t':t,'agent':a.idx,'bucket':bucket,'local_private_tv':tv,
               'target_matches_received_intent':a.target==view.team_intent.get(a.idx),
               'target_matches_edge_intent':a.target==self.team_intent.get(a.idx),
               'pose_matches_edge_last_record':tuple(a.pos)==tuple(self.team_pos[a.idx]),
               'application_bytes_novelty':len(app),'application_bytes_with_pose':len(both),
               'crc16_wire_bytes_novelty':len(crc_frame(app)),'crc16_wire_bytes_with_pose':len(crc_frame(both))}
            self.audit_rows.append(row);self.by_slot_agent[(t,a.idx)]=row
def shadow(sim,interval,pose):
    # Side ledger only: attempts do not take resources, generate ACK, or alter original simulator.
    c=sim.cfg;H=16;appbits=32 if pose else 24
    selected=[r for r in sim.audit_rows if r['t']%interval==0]
    attempts=success=nofit=overlap=ul=deficit=0;rates={};delivered_by_t={};attempts_by_t={};next_use=[]
    for row in selected:
        r0=sim.channel.fixed_rate(row['snr_mean'])
        fits=[float(r) for r in c.rates if r>=r0 and symbols(appbits,H,r)<=c.symbols_per_slot]
        if not fits:nofit+=1;continue
        rate=min(fits);n=symbols(appbits,H,rate);attempts+=1;ul+=n
        rates[str(rate)]=rates.get(str(rate),0)+1
        attempts_by_t[row['t']]=attempts_by_t.get(row['t'],0)+1
        shortfall=max(0,row['original_used']+n-c.symbols_per_slot);deficit+=shortfall;overlap+=shortfall>0
        good=math.log2(1+row['snr_instant'])>=rate
        if good:
            success+=1;delivered_by_t[row['t']]=delivered_by_t.get(row['t'],0)+appbits;next_use.append(row['t']+1)
    payload=sum(delivered_by_t.values())
    new_headers=sum(H for t,b in delivered_by_t.items() if b and not sim.bcast_bits.get(t,0))
    # Incremental rounding against the existing per-slot frame, rather than summing fictitious fractional symbols.
    dl=sum(math.ceil((sim.bcast_bits.get(t,0)+(H if sim.bcast_bits.get(t,0) else 0)+b+(H if not sim.bcast_bits.get(t,0) else 0))/c.dl_rate)
           -math.ceil((sim.bcast_bits.get(t,0)+(H if sim.bcast_bits.get(t,0) else 0))/c.dl_rate) for t,b in delivered_by_t.items())
    ack=sum(math.ceil(k*c.ack_bits/c.dl_rate) for k in attempts_by_t.values())
    return {'seed':sim.seed_label,'W':c.symbols_per_slot,'refresh_slots':interval,'with_pose':pose,'header_crc_example_bits':H,
       'scheduled_samples':len(selected),'attempts':attempts,'no_feasible_rate':nofit,'decoded_on_observed_original_fade':success,
       'outage_on_observed_original_fade':attempts-success,'ul_symbols':ul,'ul_attempts_that_exceed_original_residual_budget':overlap,
       'sum_excess_over_original_residual_symbols':deficit,'new_dl_application_bits':payload,'incremental_dl_header_bits':new_headers,
       'incremental_dl_broadcast_symbols':dl,'reliable_ack_symbols_per_slot_rounding':ack,
       'example_total_added_symbols':ul+dl+ack,'rate_counts':rates,'first_possible_use_slot':min(next_use) if next_use else None,
       'increased_mission_time_measured':False,'paid_information_used_by_policy':False,
       'excludes':['UL scheduling requests/grants in shared mode','lossy DL/catch-up and ACK loss','preambles/guard/real radio stack','elapsed compute mapped to task slots','retry until success or stale supersession'],
       'interpretation':'Passive shadow attempt cost and conflict count, not a feasible integrated paid policy or measured mission gain'}
def benchmark(sim):
    L,p,d,k,t,pose=sim.first_sample
    feature=[];codec=[]
    for _ in range(1000):
        start=time.perf_counter_ns();bucket,tv=private_novelty_bucket(L,p,d);feature.append(time.perf_counter_ns()-start)
        start=time.perf_counter_ns();frame=crc_frame(encode(k,t,bucket,pose));unframe(frame,t);codec.append(time.perf_counter_ns()-start)
    def describe(x):return {'n':len(x),'p50_ns':float(np.quantile(x,.5)),'p95_ns':float(np.quantile(x,.95)),'mean_ns':float(np.mean(x))}
    return {'scope':'1000 repeated first observed local states on HPC; no task-clock mapping, pure Python NumPy plus binary CRC codec',
            'local_feature':describe(feature),'encode_crc_decode_crc':describe(codec),'raw_feature_ns':feature,'raw_codec_ns':codec}
def main():
    require_hpc()
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('Audit10min bound')));signal.alarm(600)
    out=Path(os.environ['GOSC_OUTPUT_DIR']);selected_path=ROOT/'research/sync/runs/hpc-receiver-headroom-pilot-20261022/outputs/frozen_operating_points.json'
    pts=json.loads(selected_path.read_text())['selected']
    frozen_path=ROOT/'research/sync/runs/hpc-receiver-protocol-20261022/outputs/protocol.json'
    frozen=json.loads(frozen_path.read_text())
    assert all(digest(ROOT/p)==h for p,h in frozen['source_sha256'].items())
    scenarios=[];shadows=[];info=[];guards=[];benches=[]
    with (out/'observations.jsonl').open('x') as f:
        for W in [100,50]:
            raw=dict(pts['search-W'+str(W)]['public_tom']['case']['config'])
            raw['rates']=tuple(raw['rates']);raw['llm_agents']=tuple(raw['llm_agents'])
            cfg=Config(**raw)
            for seed in [12000000,12000001]:
                control=EventSimulation(cfg,'gosc',seed);expected=control.run()
                observed=Observer(cfg,'gosc',seed);observed.seed_label=seed;actual=observed.run()
                assert expected.keys()==actual.keys()
                for key in expected:
                    assert np.array_equal(expected[key],actual[key]) if key=='curve' else expected[key]==actual[key],key
                assert control.input_world_sha256==observed.input_world_sha256
                guards.append({'W':W,'seed':seed,'status':'identical_original_result_and_full_curve','world_sha256':control.input_world_sha256,
                               'original_result':scalar_result(expected),'observed_result':scalar_result(actual)})
                for row in observed.audit_rows:f.write(json.dumps(row)+'\n')
                rs=observed.audit_rows
                info.append({'W':W,'seed':seed,'rows':len(rs),'slot_count':len(rs)//cfg.n_agents,
                   'nonzero_private_tv':sum(x['local_private_tv']>0 for x in rs),
                   'target_not_already_in_received_intent':sum(not x['target_matches_received_intent'] for x in rs),
                   'pose_not_equal_edge_last_evidence':sum(not x['pose_matches_edge_last_record'] for x in rs),
                   'novelty_bucket_counts':{str(k):sum(x['bucket']==k for x in rs) for k in range(8)},
                   'meaning':'Within calibration examples, not independent held-out task value or sufficient receiver belief'})
                for interval in [1,5,10]:
                    for pose in [False,True]:shadows.append(shadow(observed,interval,pose))
                benches.append({'W':W,'seed':seed,**benchmark(observed)})
                scenarios.append({'W':W,'seed':seed,'scheme':'original public ToM frozen calibration point','config':raw})
    cost=[]
    for name,appbits in [('novelty_audit24',24),('novelty_pose_audit32',32),('old32_payload_plus_application_header',40)]:
        for H in [0,16,64]:
            for rate in [.25,1.,2.,6.]:
                n=symbols(appbits,H,rate)
                cost.append({'format':name,'application_bits':appbits,'extra_overhead_bits':H,'rate':rate,'ul_symbols':n,'fits_W50':n<=50,'fits_W100':n<=100})
    default_examples=[]
    for name,appbits in [('novelty',24),('novelty_pose',32),('old_payload32_with_header',40)]:
        ul=6*symbols(appbits,16,1)
        dl=math.ceil((6*appbits+16)/2)
        ack=math.ceil(6/2)
        default_examples.append({'format':name,'six_agent_UL':ul,'DL_one_broadcast_in_previously_empty_slot':dl,'reliable_ACK_symbols':ack,'total_example':ul+dl+ack,'assumptions':'R1,H16,DL_R2,6successes,oneDLframe,noexistingDLframe,noULshared-control/no losses'})
    save(out/'cost_tables.json',{'table':cost,'six_agent_single_refresh_examples':default_examples,'crc16_application_example':'24bit application +16CRC=5bytes;32bit application+16CRC=6bytes; extra H is not added again to already CRC-framed bytes'})
    save(out/'shadow_cost.json',shadows);save(out/'observability_summary.json',info);save(out/'guard_replays.json',guards);save(out/'codec_benchmark.json',benches)
    source=['extensions/receiver_summary_audit.py','scripts/repro_summary_audit.py','tests_ext/test_receiver_summary_audit.py']
    source += list(frozen['source_sha256'])
    save(out/'evidence.json',{'source_sha256':{p:digest(ROOT/p) for p in source},'frozen_point_file_sha256':digest(selected_path),
       'scenarios':scenarios,'observation_runs':4,'control_runs':4,'used_original_calibration_seeds':True,
       'new_independent_test_worlds':0,'new_llm_calls':0,'training':False,'original_core_hashes_unchanged':True})
    save(out/'conclusion.json',{'status':'bounded_information_and_cost_audit_completed','observed_missions':4,'control_missions':4,
       'control_equality':True,'complex_training_go':False,'paid_policy_task_improvement':'not_tested',
       'candidate_fields':'local novelty3bit may be additional but not spatially sufficient; current target redundant mechanism; current pose a freshness update of existing EVID',
       'architecture':'ToM valuation is built at sender; edge-only summary not available without a downlink dissemination path',
       'clock':'Samples generated after decision and sent inUL t cannot inform that same decision; ideal broadcast earliest next t+1',
       'limits':'Encoded lengths and measured local compute are real within software, PHY/control/retries/cost competition remains conditional modeling, not real over-air deployment'})
    print(json.dumps({'status':'completed','observations':sum(x['rows'] for x in info),'control_missions':len(guards),'frozen_sources_unchanged':True}))
if __name__=='__main__':main()
