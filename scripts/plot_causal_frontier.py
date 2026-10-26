"""HPC-only presentation of audited discrete points; no statistics or simulation."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--audit',type=Path,required=True);a=ap.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    data=json.loads(a.audit.read_text());assert data['status']=='passed'
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows=data['summary'];out=Path(os.environ['GOSC_OUTPUT_DIR'])
    fig,axes=plt.subplots(1,3,figsize=(15,4.5),layout='constrained')
    colors={'simple':'#777777','public':'#2878B5','pose':'#C74440','age':'#268C55','ignore':'#B58A14','shuffle':'#8B5FBF'}
    for arm,color in colors.items():
        group=[r for r in rows if ('simple' if r['mode']!='tom' else r['arm'])==arm]
        for ax,x,y in zip(axes,('mean_comm','mean_cpu','mean_comm'),('mean_T','mean_T','mean_cpu')):
            ax.scatter([r[x] for r in group],[r[y] for r in group],s=42,color=color,label=arm,alpha=.85)
    labels={'M0star':('M0*',(7,8),'left'),'public':('public*',(-7,-13),'right'),'pose':('pose*',(8,-8),'left')}
    for key,case in data['selected'].items():
        row=next(r for r in rows if r['id']==case);label,offset,align=labels[key]
        for ax,x,y in zip(axes,('mean_comm','mean_cpu','mean_comm'),('mean_T','mean_T','mean_cpu')):
            ax.scatter(row[x],row[y],s=130,facecolors='none',edgecolors='black',linewidths=1.)
            ax.annotate(label,(row[x],row[y]),xytext=offset,textcoords='offset points',fontsize=8,ha=align)
    axes[0].set(xlabel='Mean UL + DL channel uses',ylabel='Mean capped completion time (slots)')
    axes[1].set(xlabel='Mean reserved service CPU (seconds)',ylabel='Mean capped completion time (slots)')
    axes[2].set(xlabel='Mean UL + DL channel uses',ylabel='Mean reserved service CPU (seconds)')
    for ax in axes:ax.grid(alpha=.2)
    for ax in (axes[0],axes[2]):ax.ticklabel_format(axis='x',style='sci',scilimits=(0,0),useMathText=True)
    axes[0].legend(fontsize=8)
    fig.suptitle('GP-v2: 12 calibration worlds, discrete observed points; no interpolation / no confirmatory claim',fontsize=11)
    fig.savefig(out/'discrete_frontier.png',dpi=160);fig.savefig(out/'discrete_frontier.svg');plt.close(fig)
    proof=dict(status='rendered',source_audit=str(a.audit),source_audit_sha256=hashlib.sha256(a.audit.read_bytes()).hexdigest(),
               data_modified=False,change='Label offsets and compact numeric ticks only; audited observed points unchanged')
    with (out/'figure_provenance.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
    print(json.dumps(proof))

if __name__=='__main__':main()
