"""Analyze all completed approved R4-S1 records without changing configurations."""
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path
import numpy as np

from experiments_ext.reproduce import save,sha,check_protected
from experiments_ext.statistical_agreement import align_rows,bootstrap_means,simultaneous_agreement


def describe(a):
    a=np.asarray(a,float);se=float(a.std(ddof=1)/np.sqrt(len(a)))
    return dict(n=len(a),mean=float(a.mean()),q05=float(np.percentile(a,5)),q25=float(np.percentile(a,25)),
        median=float(np.median(a)),q75=float(np.percentile(a,75)),q95=float(np.percentile(a,95)),
        mean_ci_normal95=[float(a.mean()-1.96*se),float(a.mean()+1.96*se)])


def contrast(a,b,comparisons=1):
    a,b=np.asarray(a,float),np.asarray(b,float)
    if a.shape!=b.shape:raise ValueError('Unpaired contrast')
    idx=np.random.default_rng(20261015).integers(0,len(a),(20000,len(a)))
    boot=bootstrap_means(np.stack([a-b]),idx)[:,0]
    return dict(n=len(a),mean=float((a-b).mean()),ci95=np.percentile(boot,[2.5,97.5]).tolist(),
        bonferroni_ci=np.percentile(boot,[2.5/comparisons,100-2.5/comparisons]).tolist(),
        family_size=comparisons,bootstrap_resamples=20000)


def interp_frontier(x,y,budget):
    """Batched original log-linear lower envelope; no extrapolation."""
    x,y=np.asarray(x,float),np.asarray(y,float)
    if x.shape!=y.shape or x.ndim!=2 or not np.isfinite([x,y]).all() or (x<=0).any():
        raise ValueError('Invalid frontier')
    order=np.argsort(x,axis=1);x=np.take_along_axis(x,order,axis=1);y=np.take_along_axis(y,order,axis=1)
    y=np.minimum.accumulate(y,axis=1)
    valid=(budget>=x[:,0])&(budget<=x[:,-1])
    if x.shape[1]==1:return np.where(valid,y[:,0],np.nan)
    hi=np.clip((x<=budget).sum(axis=1),1,x.shape[1]-1);lo=hi-1;r=np.arange(len(x))
    span=np.log(x[r,hi])-np.log(x[r,lo]);weight=np.zeros(len(x))
    np.divide(np.log(budget)-np.log(x[r,lo]),span,out=weight,where=span>0)
    result=np.where(span>0,y[r,lo]+weight*(y[r,hi]-y[r,lo]),y[r,hi])
    return np.where(valid,result,np.nan)


def frontier_summary(group_records):
    schemes=defaultdict(list)
    for key,rs in group_records:
        if key[0]=='frontier-W100':schemes[key[3]].append(rs)
    idx=np.random.default_rng(20261015).integers(0,100,(20000,100))
    matrices={}
    for scheme,points in schemes.items():
        matrices[scheme]={}
        for source in ('fresh','reference'):
            x=np.array([[r[source]['symbols'] for r in rs] for rs in points])
            y=np.array([[r[source]['completion_time'] for r in rs] for rs in points])
            matrices[scheme][source]=(x.mean(1)[None,:],y.mean(1)[None,:],
                                     bootstrap_means(x,idx),bootstrap_means(y,idx))
    out={}
    for source in ('fresh','reference'):
        out[source]={}
        for B in (5000,10000,20000):
            base=matrices['gosc'][source]
            bt=interp_frontier(base[0],base[1],B)[0];bb=interp_frontier(base[2],base[3],B)
            row={}
            for scheme,versions in matrices.items():
                if scheme=='gosc':continue
                x,y,bx,by=versions[source];point=interp_frontier(x,y,B)[0];boots=interp_frontier(bx,by,B)
                good=np.isfinite(bb)&np.isfinite(boots);d=boots[good]-bb[good]
                row[scheme]=dict(available=bool(np.isfinite(point) and np.isfinite(bt)),
                    completion_time=float(point) if np.isfinite(point) else None,
                    gosc_completion_time=float(bt) if np.isfinite(bt) else None,
                    difference_vs_gosc=float(point-bt) if np.isfinite(point-bt) else None,
                    ci95=np.percentile(d,[2.5,97.5]).tolist() if len(d) else None,
                    inherited_bonferroni15_ci=np.percentile(d,[2.5/15,100-2.5/15]).tolist() if len(d) else None,
                    valid_bootstrap=int(good.sum()),total_bootstrap=len(good))
            out[source][B]=row
    out['interpretation']='Log-linear lower-envelope interpolation, UL data uses only. Not exact equal-cost mission interventions; conditional bootstrap availability retained.'
    return out


def write_csv(path,rows):
    with path.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def analyze(run):
    from experiments_ext.statistical_reproduction import verify_plan,OLD
    plan=verify_plan(run);out=run/'r4-statistical'
    execution=json.loads((out/'execution_manifest.json').read_text())
    if execution['status']!='completed_pending_statistical_gate' or execution['completed']!=5200:
        raise RuntimeError('Campaign incomplete')
    if sha(out/'raw.jsonl')!=execution['raw_sha256']:raise RuntimeError('Raw output hash changed')
    jobs=json.loads((run/'jobs.json').read_text());configs=json.loads((run/'configs.json').read_text())
    rows=[json.loads(line) for line in (out/'raw.jsonl').open(encoding='utf-8')]
    if len(rows)!=5200 or {r['job_id'] for r in rows}!=set(range(5200)):
        raise RuntimeError('Missing or duplicate mission')
    grouped=defaultdict(list);diffs=[]
    for row in rows:
        j=jobs[row['job_id']]
        if row['status']!='completed' or (row['seed'],row['config_key'])!=(j['seed'],j['config_key']):
            raise RuntimeError('Invalid record identity')
        key=(row['campaign'],row.get('setting',''),row.get('family',''),row['scheme'],row['param'])
        grouped[key].append(dict(seed=row['seed'],fresh=row['output'],reference=j['expected'],config_key=j['config_key']))
        for d in row['reference_differences']:
            diffs.append(dict(job_id=row['job_id'],campaign=row['campaign'],scheme=row['scheme'],param=row['param'],
                seed=row['seed'],field=d['field'],reference=d['expected'],fresh=d['actual']))
    if len(grouped)!=52:raise RuntimeError('Unexpected group count')
    ordered=[];metrics=[];descriptions=[];metadata={}
    fields=('completion_time','saved_fraction','symbols','bits','delivered_bits','dl_symbols','confirm_latency',
            'completed','found','false_declarations','private_tv')
    for gi,(key,rs) in enumerate(sorted(grouped.items())):
        cohort='validation' if key[0]=='headline-frozen' else 'evaluation'
        rs=align_rows(rs,range(3000,3100) if cohort=='validation' else range(100));ordered.append((key,rs))
        cfg=configs[rs[0]['config_key']];task='saved_fraction' if cfg['task']=='rescue' else 'completion_time'
        descriptor=dict(group_index=gi,campaign=key[0],setting=key[1],family=key[2],scheme=key[3],param=key[4],
            task_metric=task,config_key=rs[0]['config_key'],fresh={},reference={})
        for field in fields:
            for source in ('fresh','reference'):
                if all(field in r[source] and r[source][field] is not None for r in rs):
                    descriptor[source][field]=describe([r[source][field] for r in rs])
        descriptions.append(descriptor)
        for field in (task,'symbols'):
            a=[r['fresh'][field] for r in rs];b=[r['reference'][field] for r in rs]
            absolute=field=='saved_fraction';ident=f'{gi}/{field}'
            metrics.append(dict(id=ident,cohort=cohort,fresh=a,reference=b,
                scale=1.0 if absolute else float(np.mean(b)),margin=.02 if absolute else .05))
            metadata[ident]=dict(group_index=gi,campaign=key[0],setting=key[1],family=key[2],scheme=key[3],
                param=key[4],metric=field,fresh_mean=float(np.mean(a)),reference_mean=float(np.mean(b)))
    agreement=simultaneous_agreement(metrics,plan['gate']['bootstrap_resamples'],plan['gate']['statistical_seed'])
    if agreement['family_size']!=104:raise RuntimeError('Wrong primary family')
    summary_rows=[]
    for r in agreement['results']:
        m=metadata[r['id']];r['metadata']=m
        summary_rows.append(dict(**m,n=r['n'],delta_mean=r['delta_mean'],normalized_delta=r['normalized_delta_mean'],
            ci95_lo=r['normalized_ci95'][0],ci95_hi=r['normalized_ci95'][1],
            family_lo=r['simultaneous_interval'][0],family_hi=r['simultaneous_interval'][1],
            margin=r['margin'],classification=r['classification'],max_absolute_seed_difference=r['max_absolute_difference']))
    supplemental=dict(frozen={},private={})
    for setting in plan['selections']:
        pair={key[2]:rs for key,rs in ordered if key[0]=='headline-frozen' and key[1]==setting}
        task='saved_fraction' if setting.startswith('rescue') else 'completion_time'
        g,p=pair['gosc'],pair['periodic']
        ga=np.array([r['fresh']['symbols'] for r in g]);pa=np.array([r['fresh']['symbols'] for r in p])
        idx=np.random.default_rng(20261015).integers(0,100,(20000,100))
        boot=bootstrap_means(np.stack([pa,ga]),idx);ratio=boot[:,0]/boot[:,1]
        supplemental['frozen'][setting]=dict(task_metric=task,target=plan['selections'][setting]['target'],
            task_gosc_minus_periodic=contrast([r['fresh'][task] for r in g],[r['fresh'][task] for r in p],6),
            uses_ratio_periodic_over_gosc=dict(mean=float(pa.mean()/ga.mean()),ci95=np.percentile(ratio,[2.5,97.5]).tolist()),
            interpretation='Original frozen points; resource and task effects jointly reported, no retuning.')
    for setting in ('default','W50','snr-5'):
        pair={key[4].split('/')[1]:rs for key,rs in ordered if key[0]=='private-original' and key[4].startswith(setting+'/')}
        a,b=pair['shared'],pair['oracle']
        supplemental['private'][setting]=dict(
            task_shared_minus_oracle=contrast([r['fresh']['completion_time'] for r in a],[r['fresh']['completion_time'] for r in b],3),
            uses_oracle_minus_shared=contrast([r['fresh']['symbols'] for r in b],[r['fresh']['symbols'] for r in a],3),
            interpretation='Privileged joint oracle, fixed eta; realized communication cost not matched.')
    save(out/'agreement.json',agreement);write_csv(out/'agreement.csv',summary_rows)
    if diffs:write_csv(out/'exact_discrepancies.csv',diffs)
    save(out/'group_statistics.json',descriptions);save(out/'supplemental_contrasts.json',supplemental)
    save(out/'frontier_statistics.json',frontier_summary(ordered))
    classifications=dict(Counter(r['classification'] for r in agreement['results']))
    status=('scoped_statistical_agreement' if agreement['all_equivalent'] else
            'statistical_incompatibility' if classifications.get('incompatible') else 'statistically_inconclusive')
    save(out/'gate.json',dict(status=status,receiver_diagnostics_allowed=agreement['all_equivalent'],
        primary_family=104,classifications=classifications,exact_reference_mismatch_records=execution['exact_reference_mismatch_records'],
        strict_stage_status='failed_preserved',completed_fresh=5200,
        protocol_sha256=plan['protocol_sha256'],agreement_sha256=sha(out/'agreement.json'),
        protected_inputs=check_protected(OLD),
        interpretation='Amended finite-panel statistical agreement; historical source/environment unresolved; not full paper reproduction.'))
    plots(out,summary_rows)
    print('R4-S1 gate',status,classifications,flush=True)


def plots(out,rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,1,figsize=(12,9),layout='constrained')
    for ax,field,label,margin in zip(axes,('completion_time','saved_fraction','symbols'),
            ('Search time difference / reference mean (%)','Rescue saved fraction difference (percentage points)',
             'UL data channel uses difference / reference mean (%)'),(5,2,5)):
        relevant=[r for r in rows if r['metric']==field]
        for r in relevant:
            color={'equivalent':'#2166ac','inconclusive':'#b35806','incompatible':'#b2182b'}[r['classification']]
            ax.plot([r['group_index']]*2,[100*r['family_lo'],100*r['family_hi']],color=color,lw=1)
            ax.plot(r['group_index'],100*r['normalized_delta'],'o',color=color,ms=3)
        ax.axhspan(-margin,margin,color='#dddddd',alpha=.4)
        ax.axhline(0,color='black',lw=.6);ax.set_ylabel(label);ax.set_xlabel('Group index (see agreement.csv)')
    fig.suptitle('R4-S1: 100 paired seeds per point; simultaneous bootstrap intervals')
    for ext in ('png','pdf'):fig.savefig(out/('agreement.'+ext),dpi=170)
    plt.close(fig)
