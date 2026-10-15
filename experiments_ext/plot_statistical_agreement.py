"""Reviewed presentation of saved agreement data; does not recompute the gate."""
import argparse
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from experiments_ext.reproduce import ROOT,save,sha


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-id',required=True);args=ap.parse_args()
    if Path(args.run_id).name!=args.run_id:ap.error('Invalid run-id')
    out=ROOT/'.local/reproduction'/args.run_id/'r4-statistical'
    rows=list(csv.DictReader((out/'agreement.csv').open(encoding='utf-8-sig')))
    color={'equivalent':'#2166ac','inconclusive':'#b35806','incompatible':'#b2182b'}
    paths=[out/(name+'.'+ext) for name in ('agreement_reviewed_v2','unresolved_intervals_v2') for ext in ('png','pdf')]
    if any(p.exists() for p in paths):raise FileExistsError('Presentation artifacts already exist')
    fig,axes=plt.subplots(3,1,figsize=(11,9),layout='constrained')
    for ax,field,label,margin in zip(axes,('completion_time','saved_fraction','symbols'),
            ('Search time difference\n(% of reference mean)','Rescue saved fraction difference\n(percentage points)',
             'UL data uses difference\n(% of reference mean)'),(5,2,5)):
        for r in rows:
            if r['metric']!=field:continue
            x=int(r['group_index']);c=color[r['classification']]
            ax.plot([x,x],[100*float(r['family_lo']),100*float(r['family_hi'])],color=c,lw=1.1)
            ax.plot(x,100*float(r['normalized_delta']),'o',color=c,ms=3)
        ax.axhspan(-margin,margin,color='#dddddd',alpha=.45);ax.axhline(0,color='black',lw=.7)
        ax.set_ylabel(label);ax.set_xlabel('Group index (mapping in agreement.csv)')
    fig.suptitle('R4-S1: 100 paired seeds per point; simultaneous intervals across 104 endpoints')
    for ext in ('png','pdf'):fig.savefig(out/('agreement_reviewed_v2.'+ext),dpi=170)
    plt.close(fig)
    unresolved=[r for r in rows if r['classification']!='equivalent']
    fig,ax=plt.subplots(figsize=(9,4.3),layout='constrained')
    for i,r in enumerate(unresolved):
        ax.plot([100*float(r['family_lo']),100*float(r['family_hi'])],[i,i],lw=2,color='#b35806')
        ax.plot(100*float(r['normalized_delta']),i,'o',color='#b35806')
    ax.axvspan(-5,5,color='#dddddd',alpha=.5);ax.axvline(0,color='black',lw=.7)
    labels=[f"Bits, eta={r['param'].split('eta')[1]} / {'time' if r['metric']=='completion_time' else 'UL uses'}" for r in unresolved]
    ax.set_yticks(range(len(unresolved)),labels);ax.invert_yaxis()
    ax.set_xlabel('Fresh minus author mean (% of author mean)')
    ax.set_title('Four unresolved endpoints; 100 of 104 meet the fixed margins')
    fig.legend(handles=[Line2D([0],[0],color='#b35806',lw=2,label='Simultaneous 95% interval; N=100'),
        Line2D([0],[0],color='#dddddd',lw=8,label='Predefined +/-5% range')],loc='outside lower center',ncols=2,fontsize=8)
    for ext in ('png','pdf'):fig.savefig(out/('unresolved_intervals_v2.'+ext),dpi=170)
    plt.close(fig)
    save(out/'presentation_manifest_v2.json',dict(status='generated',source_sha256=sha(__file__),
        input_sha256=sha(out/'agreement.csv'),artifacts={p.name:sha(p) for p in paths},
        note='Original plot retained; reviewed versions use wrapped labels. Gate and numerical results unchanged.'))


if __name__=='__main__':main()
