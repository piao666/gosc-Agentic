"""Finish missing LLM tables with original analysis functions and verified live rows."""
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='1'
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc,digest
from repro_legacy import serial

def main():
    require_hpc();out=Path(os.environ['GOSC_OUTPUT_DIR'])
    source=ROOT/'.local/ordered-live-20261019/results'
    base=ROOT/'research/sync/runs/resume-final-replot-20261020/outputs'
    source_hashes={str(p):digest(p) for p in source.glob('*.jsonl')}
    base_hashes={str(p):digest(p) for p in (base/'figures').glob('*') if p.is_file()}
    work=ROOT/'.local/ordered-reproduction-20261019'
    sys.path.insert(0,str(work))
    import experiments.plot as plot
    import experiments.plot_realistic as realistic
    fig=out/'figures';shutil.copytree(base/'figures',fig)
    plot.RES=str(source);plot.FIG=str(fig)
    realistic.RES=str(source);realistic.OUT=str(source);realistic.FIG=str(fig);realistic.MACROS.clear()
    standard=plot.llm_table();extended=realistic.llm()
    numbers=fig/'numbers.tex'
    original=numbers.read_text()
    old_names=set(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}',original))
    overlap=old_names & set(realistic.MACROS)
    assert not overlap,overlap
    with numbers.open('a') as f:
        for key,value in realistic.MACROS.items():f.write('\\newcommand{\\'+key+'}{'+value+'}\n')
    (out/'llm_native_statistics.json').write_text(json.dumps(serial({'standard':standard,'extended':extended}),indent=2)+'\n')
    summaries=out/'summaries';summaries.mkdir()
    for name,stats in [('summary.json',standard),('summary_realistic.json',extended)]:
        raw=json.loads((base/'legacy_results'/name).read_text());raw['llm']=stats
        (summaries/name).write_text(json.dumps(serial(raw),indent=2)+'\n')
    shutil.copyfile(base/'legacy_results/summary_revision.json',summaries/'summary_revision.json')
    assert len(list(fig.glob('*.pdf')))==17
    assert len(list(fig.glob('*.tex')))==18
    assert all(digest(Path(p))==h for p,h in source_hashes.items())
    assert all(digest(Path(p))==h for p,h in base_hashes.items())
    manifest={'status':'completed','scope':'Original native analysis of verified new live result rows; no inference',
      'native_functions':['experiments.plot.llm_table','experiments.plot_realistic.llm'],
      'original_plot_source_sha256':digest(work/'experiments/plot.py'),
      'original_realistic_source_sha256':digest(work/'experiments/plot_realistic.py'),
      'input_hashes':source_hashes,'base_figures_unchanged':True,'input_results_unchanged':True,
      'pdf_count':17,'tex_count':18,'new_tables':['table_llm.tex','table_llm_extended.tex'],
      'macros_merged_into_copied_numbers_tex':list(realistic.MACROS),
      'pdf_visual_review':'Existing PDFs copied byte-for-byte; new PDF rendering not performed',
      'new_http_calls':0,'new_missions':0,
      'files':[{'path':p.relative_to(out).as_posix(),'sha256':digest(p),'size':p.stat().st_size} for p in fig.glob('*') if p.is_file()]}
    (out/'completion_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
