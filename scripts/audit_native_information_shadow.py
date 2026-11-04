"""Independent scalar G0/G1 arithmetic plus source-bound shadow replay audit.

Called by the registered diagnostic runner, not a local analysis entry point.
The scalar reference does not call the production proxy or weight functions.
"""
import math


def scalar_reference(s):
    c = s['context']
    n, radius, sender = c['grid'], c['radius'], c['sender']
    live = [i for i, declared in enumerate(c['declared']) if not declared]
    ns = sorted({o['n_records'] for g in s['groups'] if g['kind'] == 'EVID' for o in g['options']})
    if not live:
        return {method: {str(k): 0. for k in ns} for method in ('g0', 'g1', 'shuffled')}
    u = []
    for cell in live:
        x, y = divmod(cell, n)
        kernels = []
        for peer in range(c['n_agents']):
            if peer == sender:
                continue
            target = c['team_intent'].get(str(peer))
            pos = divmod(target, n) if target is not None else c['team_pos'].get(str(peer))
            distance = (max(abs(x-pos[0])-radius, 0)+max(abs(y-pos[1])-radius, 0)) if pos is not None else 0
            kernels.append(1./(1.+distance/max(1, radius)))
        q = math.fsum(kernels)/len(kernels) if kernels else 1.
        u.append(.5+.5*q)
    mean = math.fsum(u)/len(u)
    weights = [v/mean for v in u]
    shift = len(live)//2
    shuffled = weights[-shift:]+weights[:-shift] if shift else list(weights)
    delta = [0.]*(n*n)
    base = [c['Lc'][x][y] for x in range(n) for y in range(n)]
    answer = {method: {} for method in ('g0', 'g1', 'shuffled')}
    for index, rec in enumerate(s['records'], 1):
        x, y = rec['pos']
        for px in range(max(0, x-radius), min(n, x+radius+1)):
            for py in range(max(0, y-radius), min(n, y+radius+1)):
                delta[px*n+py] += c['llr_neg']
        for cell in rec['det']:
            delta[cell] += c['llr_pos']-c['llr_neg']
        if index in ns:
            d = [abs(.5*(1.+math.tanh((base[cell]+delta[cell])*.5))-
                     .5*(1.+math.tanh(base[cell]*.5))) for cell in live]
            answer['g0'][str(index)] = math.fsum(d)
            answer['g1'][str(index)] = math.fsum(a*b for a, b in zip(d, weights))
            answer['shuffled'][str(index)] = math.fsum(a*b for a, b in zip(d, shuffled))
        if ns and index == ns[-1]:
            break
    return answer


def audit_records(inputs, outputs, cfg, prices, host_records=None):
    from extensions.native_information_observer import digest
    from extensions.native_information_shadow import analyze_snapshot
    if len(inputs) != len(outputs):
        raise ValueError('Incomplete shadow coverage')
    if host_records is not None:
        expected = []
        for host in host_records:
            a = {k: v for k, v in host['plain_result'].items() if k != 'selection_process_seconds'}
            b = {k: v for k, v in host['observed_result'].items() if k != 'selection_process_seconds'}
            if a != b:
                raise ValueError('Host scientific result mismatch')
            if (host['observation_neutral'] is not True or
                host['plain_event_sha256'] != host['observed_event_sha256'] or
                host['plain_state_sha256'] != host['observed_state_sha256']):
                raise ValueError('Host neutrality binding')
            count, entries = {}, set()
            for entry in host['entries']:
                key = (entry['t'], entry['sender'])
                if key in entries or not 0 <= key[0] < cfg.max_steps or not 0 <= key[1] < cfg.n_agents:
                    raise ValueError('Host admission identity')
                entries.add(key)
                if type(entry['has_evid']) is not bool:
                    raise ValueError('Host EVID flag')
                if entry['has_evid']:
                    k = entry['sender']
                    if count.get(k, 0) < 8:
                        expected.append((host['world'], k, entry['t']))
                    count[k] = count.get(k, 0)+1
        actual = [(r['world'], r['input']['snapshot']['context']['sender'],
                   r['input']['snapshot']['context']['t']) for r in inputs]
        if expected != actual:
            raise ValueError('Deterministic first-eight capture coverage')
    seen, checked = set(), 0
    for source, result in zip(inputs, outputs):
        envelope = source['input']
        key = (source['world'], envelope['snapshot']['context']['sender'], envelope['snapshot']['context']['t'])
        if key in seen or result['world'] != source['world']:
            raise ValueError('World/line identity')
        seen.add(key)
        if digest(envelope['snapshot']) != envelope['snapshot_sha256']:
            raise ValueError('Raw snapshot hash')
        reference = scalar_reference(envelope['snapshot'])
        for method, values in reference.items():
            if set(values) != set(result['analysis']['raw'][method]):
                raise ValueError('Reference prefix coverage')
            for prefix, value in values.items():
                actual = result['analysis']['raw'][method][prefix]
                if not math.isfinite(actual) or abs(actual-value) > 1e-12+1e-9*max(abs(actual), abs(value)):
                    raise ValueError('Independent scalar proxy mismatch')
        if analyze_snapshot(envelope, cfg, prices) != result['analysis']:
            raise ValueError('Bound selection/ranking replay mismatch')
        # Direct serialized constraints independent of BF's own postcondition.
        for row in result['analysis']['selections']:
            for method, selection in row['choices'].items():
                groups = envelope['snapshot']['groups']
                used, members = 0, set()
                if len(selection['selected']) != len(selection['signature']):
                    raise ValueError('Signature coverage')
                for index, signature in zip(selection['selected'], selection['signature']):
                    gi, oi = index['group_index'], index['option_index']
                    if type(gi) is not int or type(oi) is not int or gi in members:
                        raise ValueError('Unknown/repeated group')
                    if not 0 <= gi < len(groups) or not 0 <= oi < len(groups[gi]['options']):
                        raise ValueError('Unknown option')
                    members.add(gi)
                    group, option = groups[gi], groups[gi]['options'][oi]
                    expected = {k: option[k] for k in ('rate', 'bits', 'symbols', 'n_records')}
                    expected.update(kind=group['kind'], cell=group['cell'])
                    if signature != expected or type(option['symbols']) is not int or option['symbols'] <= 0:
                        raise ValueError('Selected wire/member signature')
                    used += option['symbols']
                if used > envelope['snapshot']['budget'] or used != selection['used']:
                    raise ValueError('Selected budget')
        checked += 1
    return dict(status='passed', checked_snapshots=checked,
        scope='Independent scalar arithmetic and integer/member/wire constraints; existing BF and production ranking logic additionally replayed, not an independent optimizer',
        deterministic_host_capture_coverage_checked=host_records is not None,
        efficacy_N=0, scientific_status='Original No-Go retained')
