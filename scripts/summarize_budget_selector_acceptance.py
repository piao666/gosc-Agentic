"""HPC engineering-cost summary; no task-effect estimates or sample expansion."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen',type=Path,required=True);p.add_argument('--replay',type=Path,required=True)
    p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--binding',type=Path,required=True);a=p.parse_args()
    if not (os.name=='posix' and os.getuid()==8301880 and str(ROOT)=='/home/u202520081000097/jupyterlab/Paper/gosc'
            and os.environ.get('GOSC_OUTPUT_DIR')):raise RuntimeError('Registered HPC only')
    audit=read(a.audit);binding=read(a.binding);fixture=read(a.fixtures);replay=read(a.replay)
    if audit['status']!='passed' or binding['status']!='passed' or binding['frozen_sha256']!=digest(a.frozen):
        raise ValueError('Independent gates have not passed')
    grouped={}
    for path in ('legacy_feasible','budget_repair'):
        rows=[r for r in replay['rows'] if r['decision']['selector_trace']['path']==path]
        grouped[path]=dict(catalogs=len(rows),first_call_process_seconds=sum(r['process_seconds'] for r in rows),
            first_call_wall_seconds=sum(r['wall_seconds'] for r in rows),
            max_expansions=max((r['decision']['selector_trace']['expansions'] for r in rows),default=0),
            max_bisection_steps=max((r['decision']['selector_trace']['bisection_steps'] for r in rows),default=0))
    timing={}
    for observe in (False,True):
        rows=[r for r in fixture['rows'] if r['observe']==observe]
        timing[str(observe)]=dict(rows=len(rows),process_seconds=sum(r['process_seconds'] for r in rows),
            end_to_end_wall_seconds=sum(r['end_to_end_wall_seconds'] for r in rows),
            selection_process_seconds=sum(r['result']['selection_process_seconds'] for r in rows),
            budget_repairs=sum(r['result']['budget_repairs'] for r in rows))
    actual={str(path.parent):sum(p.stat().st_size for p in path.parent.rglob('*') if p.is_file())
            for path in (a.frozen,a.replay,a.fixtures,a.audit,a.binding)}
    report=dict(status='engineering_acceptance_passed',scope='Fixed historical catalogs and short engineering fixtures only',
        historical_repaired=audit['historical_repaired'],feasible_compatible=audit['feasible_compatible'],
        fixture_rows=audit['fixture_rows'],catalog_first_call_timing=grouped,fixture_timing=timing,
        output_bytes=actual,input_sha256={str(x):digest(x) for x in (a.frozen,a.replay,a.fixtures,a.audit,a.binding)},
        efficacy_N=0,formal_test=False,training=False,scientific_status='Original No-Go retained',
        timing_scope='Real process/wall, not hardware-calibrated logical CPU. Catalog totals exclude repeated-call and diagnostic work; run elapsed includes it. No legacy/new speedup claim.')
    with (Path(os.environ['GOSC_OUTPUT_DIR'])/'summary.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report))


if __name__=='__main__':main()
