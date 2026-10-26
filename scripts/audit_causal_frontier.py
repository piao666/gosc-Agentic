"""Independent GP-v2 frontier/ablation/stop-rule audit and static research plot.

Calibration only. No simulation or test execution. No interpolation of resource
support, no confirmatory inference after selecting on these same worlds.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def audit(fpath,folder,approval_path,out):
    f=read(fpath);p=f['plan'];cases={c['id']:c for c in f['cases']}
    rows=read(folder/'results.json');decision=read(folder/'decision.json');approval=read(approval_path)
    assert approval['status']=='passed' and approval['frozen_sha256']==digest(fpath)
    assert approval['hard_timeout']==1200 and approval['candidate_count']==21
    assert len(rows)==252 and len(cases)==21
    assert {(r['seed'],r['case_id']) for r in rows}=={(s,c) for s in p['calibration_seeds'] for c in cases}
    by={}
    for r in rows:
        assert r['status']=='completed' and r['phase']=='calibration' and r['case']==cases[r['case_id']]
        result=r['result'];t=result['completion_time']
        assert 1<=t<=p['calibration_steps'] and result['service']['slots']==t
        if not result['completed']:assert t==p['calibration_steps']
        assert result['world_sha256']==f['worlds'][str(r['seed'])]
        assert result['service']['retry_floor_slots']==2
        by[r['seed'],r['case_id']]=r
    for seed in p['calibration_seeds']:
        fields=[by[seed,c]['result']['event_field_hashes'] for c in cases]
        assert all(x==fields[0] for x in fields)
    def ordered(case):return [by[s,case] for s in p['calibration_seeds']]
    def vec(case,metric):
        rr=ordered(case)
        if metric=='T':return np.array([r['result']['completion_time'] for r in rr],float)
        if metric=='comm':return np.array([r['result']['service']['cost']['ul_uses']+r['result']['service']['cost']['dl_uses'] for r in rr],float)
        return np.array([r['result']['service']['cost']['cpu_seconds'] for r in rr],float)
    summary=[]
    for key,c in cases.items():
        rr=ordered(key);cc=[r['result']['service']['cost'] for r in rr]
        summary.append(dict(id=key,arm=c['arm'],mode=c['mode'],price=c['price'],N=len(rr),
          mean_T=float(vec(key,'T').mean()),T_quantiles=np.quantile(vec(key,'T'),[0,.25,.5,.75,1]).tolist(),
          mean_comm=float(vec(key,'comm').mean()),mean_cpu=float(vec(key,'cpu').mean()),
          mean_UL=float(np.mean([x['ul_uses'] for x in cc])),mean_DL=float(np.mean([x['dl_uses'] for x in cc])),
          mean_valuation_reservation_seconds=float(np.mean([x['valuation_cpu_seconds'] for x in cc])),
          completed=sum(r['result']['completed'] for r in rr),
          mean_coverage=float(np.mean([r['recipient_coverage'] for r in rr])),
          mean_mission_process_seconds=float(np.mean([r['cpu_seconds'] for r in rr])),
          mean_mission_wall_seconds=float(np.mean([r['wall_seconds'] for r in rr])),
          mean_selection_process_seconds=float(np.mean([r['result']['selection_process_seconds'] for r in rr])),
          total_replay_offers=sum(r['result']['service']['replay_offers'] for r in rr)))
    for old in decision['all_candidates']:
        new=next(r for r in summary if r['id']==old['id'])
        for k,v in old.items():
            if isinstance(v,(int,float)):assert math.isclose(v,new[k],rel_tol=1e-12,abs_tol=1e-12),(old['id'],k)
            else:assert v==new[k]
    # Independently rebuild within-arm three-resource Pareto membership.
    frontier=[]
    for a in summary:
        if a['mode']!='tom' or a['arm'] not in ('public','pose','age'):continue
        peers=[b for b in summary if b['mode']=='tom' and b['arm']==a['arm'] and b['id']!=a['id']]
        dominated=any(all(b[k]<=a[k] for k in ('mean_T','mean_comm','mean_cpu')) and any(b[k]<a[k] for k in ('mean_T','mean_comm','mean_cpu')) for b in peers)
        frontier.append(dict(id=a['id'],dominated=dominated))
    assert {r['id']:r['dominated'] for r in frontier}=={r['id']:r['dominated'] for r in decision['discrete_frontier']}
    supported=[]
    for a in summary:
        if a['arm']!='pose':continue
        for b in summary:
            if b['arm']!='public':continue
            cr=a['mean_comm']/b['mean_comm'];cp=a['mean_cpu']/b['mean_cpu']
            if .95<=cr<=1.05 and .95<=cp<=1.05:supported.append(dict(pose=a['id'],baseline=b['id'],comm_ratio=cr,cpu_ratio=cp))
    assert supported==decision['joint_cost_supported_pairs']
    expected=[]
    for e in decision['comparisons']:
        b=e['comparator']
        gain=vec(b,'T')-vec(e['pose'],'T')
        if not np.std(gain,ddof=1):expected.append('Degenerate task variance: '+b)
        for key in ('comm','cpu'):
            av=vec(e['pose'],key);bv=vec(b,key);ratio=av.mean()/bv.mean()
            influence=(av-ratio*bv)/bv.mean()/ratio
            if not np.std(influence,ddof=1):expected.append('Degenerate resource variance: '+b+'/'+key)
            if not .95<=ratio<=1.05:expected.append('Selected primary points lack joint matched resource support: '+b+'/'+key)
            if gain.mean()<=0 and ratio>1.05:expected.append('Nonpositive task gain with increased cost: '+b+'/'+key)
    if decision['candidate_test_N']>p['test_N_max']:expected.append('Planning N exceeds prespecified 200-world cap')
    assert sorted(set(expected))==decision['reasons']
    assert decision['status']==('No-Go' if expected else 'proposal_pending_formal_test_authorization')
    idx=np.random.default_rng(p['analysis_seed']).integers(0,len(p['calibration_seeds']),(p['bootstrap_resamples'],len(p['calibration_seeds'])))
    pose='pose_p1e-05';ablations=[]
    for baseline in ('public_p1e-05','ignore_p1e-05','age_p1e-05','shuffle_p1e-05'):
        gain=vec(baseline,'T')-vec(pose,'T')
        row=dict(pose=pose,baseline=baseline,N=len(p['calibration_seeds']),mean_gain_slots=float(gain.mean()),
                 exploratory_gain_95CI=np.quantile(gain[idx].mean(axis=1),[.025,.975]).tolist())
        for key in ('comm','cpu'):
            av=vec(pose,key);bv=vec(baseline,key)
            row[key+'_ratio']=float(av.mean()/bv.mean());row[key+'_ratio_95CI']=np.quantile(av[idx].mean(axis=1)/bv[idx].mean(axis=1),[.025,.975]).tolist()
        row['joint_resource_support']=.95<=row['comm_ratio']<=1.05 and .95<=row['cpu_ratio']<=1.05
        ablations.append(row)
    result=dict(status='passed',source_frozen_sha256=digest(fpath),decision_sha256=digest(folder/'decision.json'),
                approved_budget_sha256=digest(approval_path),missions=252,independent_calibration_N=12,
                common_first_slot_sensor_fields_verified=True,unchanged_case_grid_verified=True,
                frontier_membership_verified=True,all_joint_support_pairs_verified=True,stop_reasons_verified=True,
                matched_pose_baseline_pairs=len(supported),decision=decision['status'],reasons=decision['reasons'],
                supported_pair_scope='Pose versus non-paying baselines with arm=public; excludes paid ignore/age/shuffle mechanism controls',
                selected=dict(M0star=decision['selected_M0star'],public=decision['selected_public'],pose=decision['selected_pose']),
                candidate_test_N=decision['candidate_test_N'],executable_test_N=decision['executable_test_N'],
                summary=summary,ablations=ablations,frontier=frontier,supported_pairs=supported,
                scope='Exploratory calibration, same-world CRN; no held-out task execution or causal information-only effect. Service CPU assumed; measured process_time separate.')
    save(out/'frontier_audit.json',result)
    lines=['# GP-v2 calibration: discrete frontiers and ablations','',
      '[RUN] N=12 paired calibration worlds, 21 candidates, 252 missions. No confirmatory test or training.',
      'Selection and intervals use the same calibration data; intervals are exploratory, not selection-adjusted or confirmatory.',
      'CPU is reserved logical service seconds; measured process CPU is separately reported. No interpolation between points.','',
      '| Candidate | Completed | Mean T (slots) | UL+DL uses | CPU reservation (s) | Mean mission process (s) | Mean select process (s) |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for r in summary:lines.append(f'| {r["id"]} | {r["completed"]}/12 | {r["mean_T"]:.4f} | {r["mean_comm"]:.2f} | {r["mean_cpu"]:.4f} | {r["mean_mission_process_seconds"]:.4f} | {r["mean_selection_process_seconds"]:.4f} |')
    lines+=['','Fixed-price mechanism ablations: cost ratios=pose/control; gain=control T - pose T. All are descriptive; different closed-loop trajectories can change communication events.','',
      '| Control at price1e-5 | Gain slots [95% exploratory CI] | Comm ratio | CPU ratio | Joint resource support |',
      '|---|---:|---:|---:|---|']
    for r in ablations:lines.append(f'| {r["baseline"]} | {r["mean_gain_slots"]:.4f} [{r["exploratory_gain_95CI"][0]:.4f}, {r["exploratory_gain_95CI"][1]:.4f}] | {r["comm_ratio"]:.6f} | {r["cpu_ratio"]:.6f} | {r["joint_resource_support"]} |')
    lines+=['',f'Joint resource-supported pose/non-paying-baseline pairs (arm=public) across the finite grid: {len(supported)}.',
      'This count excludes paid-ignore/age/shuffle; their fixed-price support is separately shown above.',
      f'Decision: {decision["status"]}. Planning N={decision["candidate_test_N"]}; executable N={decision["executable_test_N"]}.',
      'Reasons: '+('; '.join(decision['reasons']) or 'No predeclared stop triggered; formal test still requires authorization.'),'',
      'Bounded replay/clock changes and new worlds differ from GP-v1; between-version differences do not isolate a causal service effect. Private peer states, future outcomes and reserved test worlds were not supplied to online estimators.']
    (out/'fair_comparison.md').write_text('\n'.join(lines)+'\n')
    plot(summary,decision,out)
    print(json.dumps({k:v for k,v in result.items() if k not in ('summary','ablations','frontier','supported_pairs')}))

def plot(rows,d,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(15,4.5),layout='constrained')
    colors={'simple':'#777777','public':'#2878B5','pose':'#C74440','age':'#268C55','ignore':'#B58A14','shuffle':'#8B5FBF'}
    for arm,color in colors.items():
        group=[r for r in rows if ('simple' if r['mode']!='tom' else r['arm'])==arm]
        for ax,x,y in zip(axes,('mean_comm','mean_cpu','mean_comm'),('mean_T','mean_T','mean_cpu')):
            ax.scatter([r[x] for r in group],[r[y] for r in group],s=42,color=color,label=arm,alpha=.85)
    for field,label in (('selected_M0star','M0*'),('selected_public','public*'),('selected_pose','pose*')):
        r=next(r for r in rows if r['id']==d[field])
        for ax,x,y in zip(axes,('mean_comm','mean_cpu','mean_comm'),('mean_T','mean_T','mean_cpu')):
            ax.scatter(r[x],r[y],s=130,facecolors='none',edgecolors='black',linewidths=1.)
            ax.annotate(label,(r[x],r[y]),xytext=(4,5),textcoords='offset points',fontsize=8)
    axes[0].set(xlabel='Mean UL + DL channel uses',ylabel='Mean capped completion time (slots)')
    axes[1].set(xlabel='Mean reserved service CPU (seconds)',ylabel='Mean capped completion time (slots)')
    axes[2].set(xlabel='Mean UL + DL channel uses',ylabel='Mean reserved service CPU (seconds)')
    for ax in axes:ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('GP-v2 calibration: 12 worlds, discrete observed points; no interpolation / no confirmatory claim',fontsize=11)
    fig.savefig(out/'discrete_frontier.png',dpi=160);fig.savefig(out/'discrete_frontier.svg');plt.close(fig)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--frozen',type=Path,required=True)
    ap.add_argument('--calibration',type=Path,required=True);ap.add_argument('--approved-budget',type=Path,required=True);a=ap.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    audit(a.frozen,a.calibration,a.approved_budget,Path(os.environ['GOSC_OUTPUT_DIR']))

if __name__=='__main__':main()
