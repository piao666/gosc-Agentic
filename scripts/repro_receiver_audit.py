"""Independent integrity and arithmetic audit of the frozen receiver pilot."""
import os,sys,json,hashlib,math
from pathlib import Path
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc,digest
import numpy as np
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def main():
 require_hpc()
 pth=ROOT/'research/sync/runs/hpc-receiver-protocol-20261022/outputs/protocol.json'
 p=read(pth);base=ROOT/'research/sync/runs/hpc-receiver-headroom-pilot-20261022/outputs'
 cal=rows(base/'calibration.jsonl');val=rows(base/'validation.jsonl')
 frozen=read(base/'frozen_operating_points.json');effects=read(base/'paired_effects.json')
 checks=[]
 def check(name,value):
  checks.append({'name':name,'passed':bool(value)})
  assert value,name
 check('protocol_hash_in_selection',frozen['protocol_sha256']==digest(pth))
 check('frozen_sources_unchanged',all(digest(ROOT/n)==h for n,h in p['source_sha256'].items()))
 check('disjoint_calibration_validation_guard_training',len(set(p['calibration_seeds']+p['test_seeds']+p['guard_seeds']+p['train_reserved_not_used']))==sum(map(len,[p['calibration_seeds'],p['test_seeds'],p['guard_seeds'],p['train_reserved_not_used']])))
 check('all_jobs_completed_without_removed_errors',all(r['status']=='completed' for r in cal+val))
 check('unique_calibration_keys',len({(r['case_id'],r['seed']) for r in cal})==len(cal)==p['max_calibration_missions'])
 check('calibration_cartesian_coverage',{(r['case_id'],r['seed']) for r in cal}=={(c['id'],s) for c in p['cases'] for s in p['calibration_seeds']})
 cases={c['id']:c for c in p['cases']};selected=frozen['selected']
 aliases=[];ineligible=[]
 def averages(cid):
  rs=[r for r in cal if r['case_id']==cid]
  return sum(x['result']['completion_time'] for x in rs)/len(rs),sum(x['result']['symbols'] for x in rs)/len(rs)
 for setting,groups in selected.items():
  for fam,chosen in groups.items():
   if fam=='m0star':continue
   eligible=[]
   for cid,c in cases.items():
    if c['setting']!=setting or c['family']!=fam:continue
    T,UL=averages(cid)
    if UL<=p['mean_ul_calibration_cap']:eligible.append((T,UL,cid))
   best=min(eligible) if eligible else None
   check('selection_'+setting+'_'+fam,(chosen is None and best is None) or (chosen is not None and best is not None and chosen['case']['id']==best[2]))
   if chosen is None:ineligible.append({'setting':setting,'family':fam,'reason':'No calibration candidate within declared mean UL cap'})
  opts=[groups[f] for f in ['m0_bits','m0_aoi','m0_periodic'] if groups[f]]
  best=min(opts,key=lambda z:(z['calibration_mean_T'],z['calibration_mean_UL'],z['case']['id'])) if opts else None
  check('m0star_'+setting,best==groups['m0star'])
 wanted={v['case']['id'] for g in selected.values() for v in g.values() if v}
 check('validation_cartesian_coverage',{(r['case_id'],r['seed']) for r in val}=={(cid,s) for cid in wanted for s in p['test_seeds']})
 check('validation_no_alias_double_count',len(val)==len(wanted)*len(p['test_seeds']))
 check('selection_written_before_validation', (base/'frozen_operating_points.json').stat().st_mtime <= (base/'validation.jsonl').stat().st_mtime)
 field_by_seed={}
 for r in cal+val:
  W=cases[r['case_id']]['config']['symbols_per_slot']
  check_key=p['world_fingerprints'][str(W)+'/'+str(r['seed'])]
  assert r['world_sha256']==check_key
  value=(r['world_sha256'],r['first_slot_potential_field_hashes'])
  if r['seed'] in field_by_seed:assert field_by_seed[r['seed']]==value
  else:field_by_seed[r['seed']]=value
 check('world_and_first_slot_potential_fields_aligned',True)
 n=len(p['test_seeds']);idx=np.random.default_rng(p['stat_seed']).integers(0,n,(p['bootstrap_resamples'],n))
 alpha=p['alpha']/p['bonferroni_family']
 for e in effects:
  if e['status']=='not_comparable_no_calibrated_point':continue
  g=selected[e['setting']]
  a=sorted([r for r in val if r['case_id']==g['m0star']['case']['id']],key=lambda r:r['seed'])
  b=sorted([r for r in val if r['case_id']==g[e['family']]['case']['id']],key=lambda r:r['seed'])
  check('paired_seeds_'+e['setting']+'_'+e['family'],[r['seed'] for r in a]==[r['seed'] for r in b]==p['test_seeds'])
  d=np.array([x['result']['completion_time']-y['result']['completion_time'] for x,y in zip(a,b)])
  ca=np.array([x['result']['symbols']+x['result']['dl_symbols'] for x in a])
  cb=np.array([x['result']['symbols']+x['result']['dl_symbols'] for x in b])
  task=[float(d.mean()),*map(float,np.quantile(d[idx].mean(1),[alpha/2,1-alpha/2]))]
  cost=[float(cb.mean()/ca.mean()),*map(float,np.quantile(cb[idx].mean(1)/ca[idx].mean(1),[alpha/2,1-alpha/2]))]
  check('recomputed_intervals_'+e['setting']+'_'+e['family'],np.allclose(task,e['task_gain_slots'],atol=1e-12,rtol=1e-12) and np.allclose(cost,e['cost_ratio_UL_plus_DL'],atol=1e-12,rtol=1e-12))
  check('declared_decision_rule_'+e['setting']+'_'+e['family'],e['task_gate']==(task[0]>=3 and task[1]>0) and e['cost_gate']==(cost[2]<=1.05))
 report={'status':'passed','checks':checks,'calibration_missions':len(cal),'validation_missions':len(val),'validation_unique_cases':len(wanted),'ineligible_families':ineligible,'test_worlds_unique_across_two_W':len({r['world_sha256'] for r in val}),'validation_uncompleted_missions':sum(not r['result']['completed'] for r in val),'calibration_uncompleted_missions':sum(not r['result']['completed'] for r in cal),'frozen_source_sha256':p['source_sha256'],'limits':['Arithmetic audit is not an external simulator validation','Only first-slot potential-field hashes logged; overlapping-cell and repeated-run tests cover code behavior, not every event dump','Shared worlds across W are not independent extra N','Calibration mean UL cap is not matched validation expenditure or a hard per-mission cap','Privileged state acquisition is free and not deployable','Small N20 corrected percentile intervals are exploratory and do not establish equivalence']}
 (Path(os.environ['GOSC_OUTPUT_DIR'])/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['status','calibration_missions','validation_missions','ineligible_families','test_worlds_unique_across_two_W','validation_uncompleted_missions']}))
if __name__=='__main__':main()
