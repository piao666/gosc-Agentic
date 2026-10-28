"""Independent stdlib audit of prospective GP-ID observations; HPC-only.

Does not import the simulator, selector or producer's analysis helpers.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def close(actual, expected, reason):
    check(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-9), reason)


def resource_audit(events, result, plan):
    costs = result['service']['cost']
    by_type = defaultdict(list)
    for event in events:
        by_type[event['event']].append(event)
    attempts = by_type['ul_attempt']
    check(all(e['uses'] == math.ceil(e['bytes'] * 8 / e['rate']) for e in attempts), 'UL frame length/rate')
    close(sum(e['uses'] for e in attempts), costs['ul_uses'], 'UL actual uses')
    for kind in ('task', 'summary'):
        close(sum(e['bytes'] for e in attempts if e['message_kind'] == kind),
              costs['ul_' + kind + '_bytes'], 'UL bytes: ' + kind)
    by_sender_slot = defaultdict(int)
    for e in attempts:
        by_sender_slot[e['t'], e['sender']] += e['uses']
    check(all(v <= plan['service']['ul_capacity'] for v in by_sender_slot.values()), 'UL capacity')

    enqueues = by_type['dl_enqueue']
    frames = {e['frame_id']:e for e in enqueues}
    check(len(frames) == len(enqueues), 'Duplicate DL frame identity')
    close(sum(e['bytes'] for e in enqueues), costs['dl_offered_bytes'], 'DL offered bytes')
    served, by_slot = Counter(), Counter()
    for e in by_type['dl_service']:
        check(e['frame_id'] in frames, 'Service of unknown frame')
        check(e['frame_kind'] == frames[e['frame_id']]['frame_kind'], 'Service kind mismatch')
        check(e['uses'] > 0 and e['t'] >= frames[e['frame_id']]['t'], 'Noncausal DL service')
        served[e['frame_id']] += e['uses']; by_slot[e['t']] += e['uses']
    check(all(v <= plan['service']['dl_capacity'] for v in by_slot.values()), 'DL capacity')
    close(sum(served.values()), costs['dl_uses'], 'DL actual uses')
    check(len(by_type['service_end']) == 1, 'Missing unique right-censor boundary')
    end = by_type['service_end'][0]
    pending = {e['frame_id']:e['remaining_uses'] for e in end['unserved']}
    completed_bytes = 0
    typed = defaultdict(lambda: dict(offered_uses=0, served_uses=0, unserved_uses=0))
    for ident, frame in frames.items():
        required = math.ceil(frame['bytes'] * 8 / plan['service']['dl_rate'])
        check(required == frame['required_uses'], 'DL actual length/rate')
        remaining = required - served[ident]
        check(0 <= remaining <= required and remaining == pending.get(ident, 0), 'DL censor conservation')
        if remaining == 0:
            completed_bytes += frame['bytes']
        item = typed[frame['frame_kind']]
        item['offered_uses'] += required; item['served_uses'] += served[ident]
        item['unserved_uses'] += remaining
    check(set(pending) <= set(frames), 'Unknown pending DL')
    close(completed_bytes, costs['dl_completed_bytes'], 'Completed bytes')
    check(len(pending) == result['service']['pending_dl_frames'], 'Pending DL count')
    check(len(end['inflight']) == result['service']['inflight_dl_frames'], 'Inflight count')

    admissions = {e['job_id']:e for e in by_type['cpu_admit']}
    check(len(admissions) == len(by_type['cpu_admit']), 'Duplicate CPU job id')
    close(sum(e['seconds'] for e in admissions.values()), costs['cpu_seconds'], 'CPU reservation')
    close(sum(e['start_seconds'] - e['t'] * plan['service']['slot_seconds'] for e in admissions.values()),
          costs['cpu_queue_wait_seconds'], 'CPU queue wait')
    ready_received = Counter()
    completed = set()
    for e in by_type['cpu_complete']:
        check(e['job_id'] in admissions and e['job_id'] not in completed, 'Unknown/duplicate CPU completion')
        a = admissions[e['job_id']]; completed.add(e['job_id'])
        check(e['observer'] == a['observer'] and e['message_kind'] == a['message_kind'], 'CPU identity/kind')
        check(e['t'] >= a['ready'], 'CPU completed early')
        if a['action'] == 'received':
            ready_received[e['t'], e['observer'], e['message_kind'], a['wire_sha256']] += 1
    pending_jobs = {e['job_id'] for e in end['pending_cpu']}
    check(set(admissions) - completed == pending_jobs, 'CPU censor conservation')
    check(len(pending_jobs) == result['service']['pending_cpu_jobs'], 'Pending CPU count')
    decoded = Counter((e['t'], e['observer'], e['message_kind'], e['wire_sha256']) for e in by_type['decoded'])
    check(ready_received == decoded, 'Received decode completion')
    successful_arrivals = Counter((e['t'], e['observer'], e['message_kind'], e['wire_sha256'])
                                  for e in by_type['dl_arrival'] if e['success'])
    receive_admissions = Counter((e['t'], e['observer'], e['message_kind'], e['wire_sha256'])
                                 for e in admissions.values() if e['action'] == 'received')
    check(successful_arrivals == receive_admissions, 'Actual arrivals vs CPU admission')
    close(sum(not e['success'] for e in by_type['dl_arrival']), costs['dl_recipient_erasures'], 'DL erasures')
    return dict(typed_DL=dict(typed), CPU_by_kind={kind:sum(e['seconds'] for e in admissions.values()
                if e['message_kind'] == kind) for kind in {e['message_kind'] for e in admissions.values()}},
                decision_count=len(by_type['decision']))


def decision_audit(events, result, *, selection_budget_findings=None):
    decisions = [e for e in events if e['event'] == 'decision']
    check(len(decisions) == result['selection_calls'], 'Decision count')
    for d in decisions:
        native = {x['peer']:x for x in d['timestamps']}
        eligible = {}
        for cached in d['summary_cache']:
            peer = cached['peer']; stamp = native.get(peer); key = str(peer)
            valid = (peer != d['sender'] and stamp is not None and key in d['native_positions']
                     and stamp['native_pos'] == d['native_positions'][key]
                     and cached['created'] < cached['received'] <= d['t'] <= cached['valid_until']
                     and cached['created'] > stamp['native_created'])
            check(cached['eligible'] == valid and bool(cached['reasons']) == (not valid), 'Cache eligibility audit')
            if valid:
                eligible[peer] = cached
        ages = []
        for stamp in d['timestamps']:
            check(stamp['native_created'] <= d['t'], 'Future native state')
            if stamp['timestamp_source'] == 'summary':
                check(d['age_source'] == 'paid', 'Paid timestamp used by native control')
                check(stamp['selected_created'] < stamp['received'] <= d['t'] <= stamp['valid_until'], 'Timestamp causal/TTL boundary')
                check(stamp['selected_created'] > stamp['native_created'], 'Paid timestamp not newer')
                check(stamp['peer'] in eligible and eligible[stamp['peer']]['created'] == stamp['selected_created'], 'Selected timestamp not in received cache')
            else:
                check(stamp['selected_created'] == stamp['native_created'], 'Native fallback')
                check(d['age_source'] != 'paid' or stamp['peer'] not in eligible, 'Missed eligible paid timestamp')
            age = max(0, d['t'] - stamp['selected_created'])
            check(age == stamp['age'], 'Age arithmetic'); ages.append(age)
        f = 1. if d['age_source'] == 'none' or not ages else 1 / (1 + sum(ages) / len(ages))
        close(d['factor'], f, 'Age factor')
        close(d['effective_price'], d['base_price'] / f, 'Effective price')
        expected_positions = dict(d['native_positions'])
        if d['arm'] in ('paid-pose', 'paid-pose-age', 'paid-pose-native-age'):
            expected_positions.update({str(k):v['pose'] for k, v in eligible.items()})
        check(expected_positions == d['valuation_positions'], 'Unexpected/missing pose projection')
        selected_symbols = sum(x['symbols'] for x in d['selected'])
        if selected_symbols > d['budget']:
            # Strict mode remains the default. Diagnostic continuation records
            # the violation and still checks the remainder of this decision.
            if selection_budget_findings is None:
                check(False, 'Selected budget')
            selection_budget_findings.append(dict(t=d['t'], sender=d['sender'],
                selected_symbols=selected_symbols, budget=d['budget'],
                excess=selected_symbols-d['budget'], selected=d['selected']))
        if d['groups_before_age'] is not None:
            catalog = Counter()
            for g in d['groups_before_age']:
                for o in g['options']:
                    check(float.fromhex(o['value_hex']) == o['value'], 'Candidate float serialization')
                    catalog[g['kind'], g['cell'], o['rate'], o['bits'], o['symbols'], o['n_records']] += 1
            for selected in d['selected']:
                key = tuple(selected[k] for k in ('kind', 'cell', 'rate', 'bits', 'symbols', 'n_records'))
                check(catalog[key] > 0, 'Selected option absent from catalog')
                catalog[key] -= 1
    return len(decisions)


def audit(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    plan = data['frozen']['plan']; rows = data['rows']
    check(not data['calibration_run'] and not data['formal_test_run'] and not data['training'], 'Execution scope')
    check(data['efficacy_N'] == 0 and len(rows) == plan['probe_max_missions'], 'Probe scope/matrix size')
    index = {(r['seed'], r['case']['id'], r['observe']):r for r in rows}
    check(len(index) == len(rows), 'Duplicate probe cell')
    details, inputs = [], {path.name:hashlib.sha256(path.read_bytes()).hexdigest()}
    omitted = {'selection_process_seconds', 'scheme', 'scope', 'compute_scope'}
    for seed in plan['probe_seed_candidates']:
        for case in data['frozen']['cases']:
            a, b = index[seed, case['id'], False], index[seed, case['id'], True]
            check(a['result']['world_sha256'] == b['result']['world_sha256'] == data['frozen']['worlds'][str(seed)], 'World identity')
            check({k:v for k,v in a['result'].items() if k not in omitted} ==
                  {k:v for k,v in b['result'].items() if k not in omitted}, 'Observation equivalence')
            file = path.parent / (b['id'] + '-observations.jsonl')
            events = [json.loads(line) for line in file.read_text(encoding='utf-8').splitlines() if line]
            inputs[file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
            resources = resource_audit(events, b['result'], plan)
            decisions = decision_audit(events, b['result'])
            numeric_file = path.parent / (b['id'] + '-selector.json')
            numeric = json.loads(numeric_file.read_text(encoding='utf-8'))
            inputs[numeric_file.name] = hashlib.sha256(numeric_file.read_bytes()).hexdigest()
            actual = [e for e in events if e['event'] == 'decision' and e['groups_before_age'] is not None]
            actual_index = {(e['t'], e['sender'], e['form']):e for e in actual}
            check(len(actual_index) == len(actual), 'Duplicate observed decision key')
            check(len(numeric['decisions']) == len(actual), 'Catalog diagnostic count')
            seen, replay_mismatches = set(), 0
            for d in numeric['decisions']:
                key = (d['t'], d['sender'], d['original_form'])
                check(key in actual_index and key not in seen, 'Selector decision binding')
                seen.add(key)
                check(set(d['selected']) == {'scale', 'price'}, 'Selector form coverage')
                matches = d['selected'][d['original_form']] == actual_index[key]['selected']
                check(d['replay_matches_actual'] == matches, 'Selector replay claim contradicts observed decision')
                replay_mismatches += not matches
                check(d['scale_price_same'] == (d['selected']['scale'] == d['selected']['price']), 'Catalog comparison accounting')
            check(seen == set(actual_index), 'Missing selector decision binding')
            check(numeric['same_catalog_mismatches'] == sum(not d['scale_price_same'] for d in numeric['decisions']), 'Catalog mismatch count')
            check(numeric['replay_mismatches'] == replay_mismatches == 0, 'Actual replay mismatch')
            details.append(dict(seed=seed, case=case['id'], decisions=decisions,
                                selector_mismatches=numeric['same_catalog_mismatches'], **resources))
    return dict(status='passed', probe_rows=len(rows), details=details, input_sha256=inputs,
                efficacy_N=0, formal_test=False, paid_benefit_established=False,
                scope='Independent serialized decision/resource/observation accounting; not task causality or universal selector equivalence')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    args = parser.parse_args()
    if os.name != 'posix' or os.getuid() != 8301880 or str(ROOT) != '/home/u202520081000097/jupyterlab/Paper/gosc':
        raise RuntimeError('HPC-only')
    if not os.environ.get('GOSC_RUN_DIR') or not os.environ.get('GOSC_OUTPUT_DIR'):
        raise RuntimeError('Registered runner required')
    result = audit(args.results)
    with (Path(os.environ['GOSC_OUTPUT_DIR']) / 'audit.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(dict(status=result['status'], probe_rows=result['probe_rows'], efficacy_N=0)))


if __name__ == '__main__':
    main()
