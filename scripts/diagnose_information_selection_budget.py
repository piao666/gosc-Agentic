"""Registered HPC-only forensic scan; never alters simulation results."""
import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path


def bracket_diagnostic(d):
    """Independent transcription of the archived 40-step selector bracket."""
    groups = d['groups_before_age']
    if groups is None:
        return None
    factor = d['factor'] if d['form'] == 'scale' else 1.
    price = d['base_price'] if d['form'] == 'scale' else d['effective_price']
    def pick(multiplier):
        selected = []
        for group in groups:
            best = None
            best_u = 0.
            for option in group['options']:
                value = float.fromhex(option['value_hex']) * factor
                utility = value - multiplier * option['symbols']
                if utility > best_u:
                    best, best_u = option, utility
            if best is not None:
                selected.append(dict(kind=group['kind'], cell=group['cell'],
                    **{k:best[k] for k in ('rate','bits','symbols','n_records')}))
        return selected, sum(x['symbols'] for x in selected)
    high = max((float.fromhex(o['value_hex']) * factor / o['symbols']
                for g in groups for o in g['options']), default=1.)
    initial_high = high
    initial_selected, initial_used = pick(price + high)
    low = 0.
    for _ in range(40):
        mid = .5 * (low + high)
        if pick(price + mid)[1] <= d['budget']:
            high = mid
        else:
            low = mid
    selected, used = pick(price + high)
    return dict(initial_upper_bound=initial_high, initial_upper_bound_hex=initial_high.hex(),
        initial_used=initial_used, initial_upper_bound_feasible=initial_used<=d['budget'],
        final_upper_bound=high, final_used=used, final_selected=selected,
        final_matches_observed=selected==d['selected'],
        interpretation='An infeasible initial upper endpoint violates the archived bisection precondition; diagnostic only, no scheduler modification')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if (os.name != 'posix' or os.getuid() != 8301880 or
            str(root) != '/home/u202520081000097/jupyterlab/Paper/gosc' or
            not os.environ.get('GOSC_OUTPUT_DIR')):
        raise RuntimeError('Registered HPC execution required')
    data = json.loads(args.results.read_text())
    examples = []
    decisions = violations = material = 0
    maximum_excess = 0.
    cases = {}
    for row in data['rows']:
        path = args.results.parent / row['observation']['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['observation']['sha256']:
            raise ValueError('Input hash mismatch')
        with gzip.open(path, 'rt') as stream:
            for line in stream:
                d = json.loads(line)
                if d['event'] != 'decision':
                    continue
                decisions += 1
                symbols = [x['symbols'] for x in d['selected']]
                total = sum(symbols)
                if total > d['budget']:
                    excess = total - d['budget']
                    violations += 1
                    material += excess > 1e-9
                    maximum_excess = max(maximum_excess, excess)
                    cases[row['case_id']] = cases.get(row['case_id'], 0) + 1
                    if len(examples) < 20:
                        examples.append(dict(seed=row['seed'], case_id=row['case_id'],
                            t=d['t'], sender=d['sender'], budget=d['budget'],
                            total=total, fsum=math.fsum(symbols), excess=excess,
                            budget_hex=float(d['budget']).hex(), total_hex=float(total).hex(),
                            selected=d['selected'], bracket=bracket_diagnostic(d)))
    report = dict(results_sha256=hashlib.sha256(args.results.read_bytes()).hexdigest(),
        decisions=decisions, strict_violations=violations, excess_over_1e_9=material,
        max_excess=maximum_excess, by_case=cases, examples=examples,
        scope='Forensic diagnosis only; original audit failure and experiment preserved')
    out = Path(os.environ['GOSC_OUTPUT_DIR']) / 'diagnosis.json'
    with out.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'examples'}))


if __name__ == '__main__':
    main()
