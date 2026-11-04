"""Registered HPC descriptive reporting of an already completed shadow run.

No new policies, worlds, parameter selection, task-outcome comparison or CI.
Counts retain all declared prices and the raw run's original mechanism verdict.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-run', type=Path, required=True)
    args = p.parse_args()
    if not (os.name == 'posix' and os.getuid() == 8301880 and
            str(ROOT) == '/home/u202520081000097/jupyterlab/Paper/gosc'):
        raise RuntimeError('HPC only')
    run = args.input_run.resolve()
    out = Path(os.environ['GOSC_OUTPUT_DIR']).resolve()
    registered = Path(os.environ['GOSC_RUN_DIR']).resolve()
    if (run.parent != ROOT/'research/sync/runs' or registered.parent != run.parent
            or out != registered/'outputs'):
        raise RuntimeError('Registered run/output paths')
    status = read(run/'status.json')
    if status['status'] != 'completed' or status['exit_code'] != 0:
        raise RuntimeError('Do not summarize failed/incomplete run as successful')
    source = run/'outputs'
    summary, audit = read(source/'summary.json'), read(source/'audit.json')
    if audit['status'] != 'passed' or not audit['deterministic_host_capture_coverage_checked']:
        raise RuntimeError('Independent raw arithmetic/coverage audit required')
    for name, expected in summary['artifacts_sha256'].items():
        if Path(name).name != name or sha(source/name) != expected:
            raise RuntimeError('Input SHA mismatch')
    rows, timings = read(source/'shadows.json'), read(source/'timings.json')
    report = dict(input_run=run.name, input_summary_sha256=sha(source/'summary.json'),
        input_audit_sha256=sha(source/'audit.json'), mechanism_status=summary['mechanism_status'],
        scope=summary['scope'], cost_status=summary['cost_status'], worlds=[],
        efficacy_N=0, formal_test=False, training=False,
        next_stage_authorized=False, scientific_status=summary['scientific_status'])
    for world in summary['worlds']:
        items = [r['analysis'] for r in rows if r['world'] == world['world']]
        categories, flips, selected_prices = Counter(), Counter(), Counter()
        first_witness = None
        for item in items:
            for selection in item['selections']:
                categories[selection['difference_category']] += 1
                for flip in selection['robust_flips']:
                    flips[flip['level']] += 1
                selected_prices[str(selection['price'])] += int(selection['content_witness'])
                if selection['content_witness'] and first_witness is None:
                    first_witness = dict(snapshot_sha256=item['snapshot_sha256'],
                        t=item['t'], sender=item['sender'], price=selection['price'],
                        prefixes=item['prefixes'], raw=item['raw'],
                        g0=selection['choices']['g0']['signature'],
                        g1=selection['choices']['g1']['signature'],
                        same_state_scale=selection['choices']['same_state_scale']['signature'],
                        relevant_robust_flips=selection['relevant_robust_flips'])
        selections = [s for item in items for s in item['selections']]
        report['worlds'].append(dict(world=world['world'], snapshots=len(items),
            multi_prefix_snapshots=sum(len(r['prefixes']) >= 2 for r in items),
            nonproportional_snapshots=sum(r['nonproportional'] for r in items),
            witness_snapshots=sum(any(s['content_witness'] for s in r['selections']) for r in items),
            comparisons=len(selections), g0_g1_categories=dict(categories),
            control_unexplained_comparisons=sum(not s['declared_controls_explain_selection'] for s in selections),
            robust_flip_pair_price_counts=dict(flips), content_witnesses_by_price=dict(selected_prices),
            first_witness_in_input_price_order=first_witness))
    # Per-snapshot median of the three repeats; repeats are not independent N.
    cost = {m: [] for m in ('public', 'g0', 'g1')}
    cold = {m: [] for m in cost}
    for timing in timings:
        for method in cost:
            samples = [r for r in timing['timing']['rows'] if r['method'] == method]
            hot = [r['total_process_ns'] for r in samples if r['phase'] == 'hot_repeat']
            if len(hot) != 3:
                raise RuntimeError('Timing repeat coverage')
            cost[method].append(statistics.median(hot))
            cold[method].extend(r['total_process_ns'] for r in samples if r['phase'] == 'cold_first')
    report['replay_timing'] = {m: dict(snapshot_count=len(v),
        median_of_snapshot_hot_medians_process_ns=statistics.median(v) if v else None,
        median_cold_first_process_ns=statistics.median(cold[m]) if cold[m] else None) for m, v in cost.items()}
    report['timing_scope'] = ('Descriptive replay restore+native candidate/TeamModel/wire+BF total process time; '
        'not deployment queue timing or stable hardware savings; snapshots correlated, no inferential CI')
    report['raw_output_bytes'] = sum(x.stat().st_size for x in source.rglob('*') if x.is_file())
    body = (json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8')
    if len(body) > 1048576:
        raise RuntimeError('Descriptive report cap')
    with (out/'report.json').open('xb') as stream:
        stream.write(body)
    print(json.dumps(dict(mechanism_status=report['mechanism_status'],
        worlds=[{k: r[k] for k in ('world', 'snapshots', 'multi_prefix_snapshots', 'nonproportional_snapshots', 'witness_snapshots')} for r in report['worlds']],
        raw_output_bytes=report['raw_output_bytes']), ensure_ascii=False))


if __name__ == '__main__':
    main()
