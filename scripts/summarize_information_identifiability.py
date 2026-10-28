"""HPC-only read-only summary of audited cost fixtures, never efficacy analysis."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    a = parser.parse_args()
    if os.name != 'posix' or os.getuid() != 8301880 or str(ROOT) != '/home/u202520081000097/jupyterlab/Paper/gosc':
        raise RuntimeError('HPC-only')
    if not os.environ.get('GOSC_RUN_DIR') or not os.environ.get('GOSC_OUTPUT_DIR'):
        raise RuntimeError('Registered runner required')
    audit, data = read(a.audit), read(a.results)
    if audit['status'] != 'passed' or data['efficacy_N'] != 0:
        raise RuntimeError('Audited cost-only input required')
    for name, expected in audit['input_sha256'].items():
        if sha(a.results.parent / name) != expected:
            raise RuntimeError('Audited input changed: ' + name)
    plan = data['frozen']['plan']
    details = {(d['seed'], d['case']):d for d in audit['details']}
    rows = []
    total_catalogs = total_mismatches = decision_count = eligibility_count = 0
    for case in data['frozen']['cases']:
        off = [r for r in data['rows'] if r['case']['id'] == case['id'] and not r['observe']]
        on = [r for r in data['rows'] if r['case']['id'] == case['id'] and r['observe']]
        actual_summary_ul = []
        log_bytes = []
        for r in on:
            events_path = a.results.parent / (r['id'] + '-observations.jsonl')
            events = [json.loads(line) for line in events_path.read_text().splitlines() if line]
            actual_summary_ul.append(sum(e['uses'] for e in events if e['event'] == 'ul_attempt' and e['message_kind'] == 'summary'))
            log_bytes.append(events_path.stat().st_size)
            numeric = read(a.results.parent / (r['id'] + '-selector.json'))
            total_catalogs += len(numeric['decisions'])
            total_mismatches += numeric['same_catalog_mismatches']
            for e in events:
                if e['event'] == 'decision':
                    decision_count += 1
                    eligibility_count += any(x['eligible'] for x in e['summary_cache'])
        n = len(on)
        typed_summary_dl = [sum(v['served_uses'] for k, v in details[r['seed'], case['id']]['typed_DL'].items()
                                if k in ('summary_ack', 'summary_snapshot')) for r in on]
        rows.append(dict(case=case['id'], worlds=n,
            mean_UL_DL_uses=sum(r['result']['service']['cost']['ul_uses'] + r['result']['service']['cost']['dl_uses'] for r in on)/n,
            mean_direct_summary_UL_uses=sum(actual_summary_ul)/n,
            mean_direct_summary_DL_served_uses=sum(typed_summary_dl)/n,
            mean_logical_CPU_seconds=sum(r['result']['service']['cost']['cpu_seconds'] for r in on)/n,
            mean_wall_off=sum(r['wall_seconds'] for r in off)/len(off),
            mean_wall_on=sum(r['wall_seconds'] for r in on)/n,
            max_wall_on=max(r['wall_seconds'] for r in on),
            mean_observation_bytes=sum(log_bytes)/n,
            max_observation_bytes=max(log_bytes)))
    # Hypothetical sizing only; 12 worlds is an exploratory review choice,
    # never a power-derived or already authorized independent calibration N.
    hypothetical_n, horizon = 12, 400
    estimate = 2 * hypothetical_n * horizon / plan['probe_steps'] * sum(r['max_wall_on'] for r in rows)
    storage = math.ceil(hypothetical_n * horizon / plan['probe_steps'] * sum(r['max_observation_bytes'] for r in rows))
    proposal = dict(status='review_candidate_not_executable', hypothetical_calibration_worlds=hypothetical_n,
        hypothetical_cases=len(rows), hypothetical_missions=hypothetical_n*len(rows), horizon_slots=horizon,
        projected_mission_wall_seconds_2x=estimate, projected_observation_bytes_linear=storage,
        possible_timeout_proposal_seconds=1200 if estimate <= 1080 else None,
        formal_test_N=None, calibration_authorized=False, formal_test_authorized=False, training=False,
        caveat='Short-horizon timing/log-size extrapolation can underestimate queue/candidate growth; excludes offline selector replays, output serialization, source synchronization and result download. A complete runner budget must add those before authorization. No task outcomes used.')
    summary = dict(status='audited_cost_probe_summary', probe_missions=len(data['rows']),
        distinct_probe_worlds=len(data['frozen']['worlds']), efficacy_N=0,
        same_catalog_diagnostics=total_catalogs, numerical_cross_form_mismatches=total_mismatches,
        decisions=decision_count, decisions_with_eligible_local_summary=eligibility_count,
        rows=rows, prospective_sizing_review=proposal,
        inputs={'results':sha(a.results), 'audit':sha(a.audit)},
        limitations='No task quality estimates, ranking, CI, power, arm selection or net information-value conclusion. Off/on order fixed. Direct-summary fees are realized protocol accounting, not a causal cost decomposition. Cache permissions come from frozen source/contracts; serialized local-cache checks do not reconstruct payloads from wire.')
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    with (out / 'summary.json').open('x') as f:
        json.dump(summary, f, indent=2, allow_nan=False); f.write('\n')
    text = '# GP-ID-v1 audited cost fixtures\n\n52 short fixtures on two cost-probe worlds; efficacy N=0. No task benefit claim.\n\n'
    text += '| Case | UL+DL uses | Summary UL | Summary DL served | Logical CPU s | Wall off/on s |\n|---|---:|---:|---:|---:|---:|\n'
    for r in rows:
        text += '| {} | {:.2f} | {:.2f} | {:.2f} | {:.4f} | {:.4f}/{:.4f} |\n'.format(
            r['case'], r['mean_UL_DL_uses'], r['mean_direct_summary_UL_uses'],
            r['mean_direct_summary_DL_served_uses'], r['mean_logical_CPU_seconds'], r['mean_wall_off'], r['mean_wall_on'])
    text += '\nSame-catalog numerical comparisons: {}; cross-form mismatches: {}. Not a universal equivalence proof.\n'.format(total_catalogs, total_mismatches)
    text += '\nSizing is hypothetical and incomplete; see summary.json limitations. No new calibration/test/training execution.\n'
    (out / 'cost_probe.md').write_text(text)
    print(json.dumps(dict(status=summary['status'], probe_missions=len(data['rows']), efficacy_N=0,
                         catalog_diagnostics=total_catalogs, numerical_mismatches=total_mismatches,
                         projected_mission_only_seconds_2x=estimate)))


if __name__ == '__main__':
    main()
