"""Layout-only derived rescue figure; immutable numerical artists."""
from pathlib import Path
import sys,os,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc,digest
def main():
    require_hpc();out=Path(os.environ['GOSC_OUTPUT_DIR'])
    work=ROOT/'.local/ordered-reproduction-20261019'
    sys.path.insert(0,str(work))
    import experiments.plot_revision as p
    from matplotlib.figure import Figure
    from matplotlib.ticker import LogLocator,NullFormatter
    old=Figure.savefig;records=[]
    def data(fig):
        return [[{'x':list(map(float,line.get_xdata())),'y':list(map(float,line.get_ydata()))} for line in ax.lines] for ax in fig.axes]
    def save(fig,path,*args,**kw):
        before=data(fig)
        for ax in fig.axes:
            ax.xaxis.set_major_locator(LogLocator(base=10,numticks=4))
            ax.xaxis.set_minor_formatter(NullFormatter())
        after=data(fig);assert before==after
        records.append({'line_xy_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
            'same_numerical_artists_before_after':True,'change':'Sparse log major ticks; hide minor labels only'})
        old(fig,str(out/'fig_rescue_display.pdf'),*args,**kw)
        old(fig,str(out/'fig_rescue_display.png'),dpi=180,bbox_inches='tight')
    Figure.savefig=save;p.FIG=str(out)
    try:p.rescue()
    finally:Figure.savefig=old
    (out/'layout_provenance.json').write_text(json.dumps({'scope':'Display derivative, not replacement of exact native export',
        'original_native_source':str(work/'experiments/plot_revision.py'),'source_sha256':digest(work/'experiments/plot_revision.py'),
        'changes':records,'original_figure_preserved':True,'new_simulations':0},indent=2)+'\n')
if __name__=='__main__':main()
