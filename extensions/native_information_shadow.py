"""Post-host same-state shadows. No service calls, rollout, labels or learning."""
from dataclasses import replace
from itertools import combinations
from types import SimpleNamespace
import math
import time

import numpy as np

from gosc.belief import SensorModel, sigmoid
from gosc.channel import Channel
from gosc.schemes import Group, Option
from gosc.voi import TeamModel
from .budget_feasible_selector import select_feasible, selection_indices, validate_selection
from .native_information_observer import (SNAPSHOT_VERSION, digest, verify_checkpoint)
from .native_information_value import (NativeInformationError, NativeValueContext,
    NativeValueWireGOSC, checked_records, evidence_values, record_from_json, weights)
from .native_task_wire import WireGOSC, encode_packet
from .wire_periodic import WirePeriodic


def require(condition, message):
    if not condition:
        raise NativeInformationError(message)


def tolerance(a, b):
    return 1e-12 + 1e-9 * max(abs(a), abs(b))


def sign(a, b):
    require(math.isfinite(a) and math.isfinite(b), 'Nonfinite ranking')
    return 0 if abs(a-b) <= tolerance(a, b) else (1 if a > b else -1)


def groups_from_json(rows):
    return [Group(g['kind'], [Option(o['rate'], o['bits'], o['symbols'],
        float.fromhex(o['value_hex']), o['n_records']) for o in g['options']], cell=g['cell']) for g in rows]


def structural(groups):
    return [(g.kind, g.cell, [(o.rate, o.bits, o.symbols, o.n_records) for o in g.options]) for g in groups]


def alternate(groups, raw=None, probabilities=None, factor=1., restrict=None):
    result = []
    for gi, g in enumerate(groups):
        opts = []
        for oi, o in enumerate(g.options):
            if g.kind == 'EVID' and restrict is not None and o.n_records != restrict:
                continue
            value = o.value if g.kind != 'EVID' or raw is None else raw[o.n_records] * probabilities[gi][oi]
            value *= factor
            require(math.isfinite(value) and value >= 0, 'Alternate value')
            opts.append(replace(o, value=value))
        result.append(replace(g, options=opts))
    return result


def choose(groups, budget, price):
    chosen, trace = select_feasible(groups, budget, price)
    used = validate_selection(groups, chosen, budget)
    indices = selection_indices(groups, chosen)
    return dict(selected=indices, used=used, trace=trace,
        signature=[dict(kind=g.kind, cell=g.cell, rate=o.rate, bits=o.bits,
                        symbols=o.symbols, n_records=o.n_records) for g, o in chosen])


def signature_key(selection):
    return tuple(sorted((r['kind'], -1 if r['cell'] is None else r['cell'],
        r['rate'], r['bits'], r['symbols'], r['n_records']) for r in selection['signature']))


def evid(selection):
    return next((r for r in selection['signature'] if r['kind'] == 'EVID'), None)


def restore(snapshot, cfg):
    context = NativeValueContext.from_json(snapshot['context'])
    records = checked_records(context, [record_from_json(r) for r in snapshot['records']])
    meta = snapshot['agent']
    require(meta['idx'] == context.sender and cfg.grid == context.grid and
            cfg.n_agents == context.n_agents, 'Restored sender/config')
    sensor = SensorModel(cfg.p_detect, cfg.p_false_alarm, cfg.sense_radius, cfg.grid)
    require((sensor.radius, sensor.llr_pos, sensor.llr_neg) ==
            (context.radius, context.llr_pos, context.llr_neg), 'Sensor/config')
    view = SimpleNamespace(cfg=cfg, sensor=sensor, t=context.t, Lc=context.Lc,
        declared=context.declared, team_pos=dict(context.team_pos), team_intent=dict(context.team_intent))
    x, y = np.indices((cfg.grid, cfg.grid))
    agent = SimpleNamespace(idx=meta['idx'], pos=tuple(meta['pos']), target=meta['target'],
        shared_intent=meta['shared_intent'], acked_intent=meta['acked_intent'],
        acked_confirms=set(meta['acked_confirms']), confirmed_pending=set(meta['confirmed_pending']),
        pending_records=list(records), pending_llr=np.array(meta['pending_llr'], dtype=np.float64), _X=x, _Y=y)
    require(agent.pending_llr.shape == context.Lc.shape and np.isfinite(agent.pending_llr).all(),
            'Own private array shape/finite')
    # BS is not used by success_prob; only the already lawful known CSI is used.
    return context, records, agent, view, Channel(cfg, (0, 0))


def validate_snapshot(envelope, cfg):
    s = envelope['snapshot']
    require(set(envelope) == {'snapshot', 'snapshot_sha256'} and set(s) == {
        'schema', 'context', 'records', 'own_history', 'groups', 'probabilities', 'payloads',
        'raw_tom', 'known', 'budget', 'price', 'native_factor', 'native_stamps', 'selected', 'agent'},
        'Unexpected snapshot fields')
    require(s['schema'] == SNAPSHOT_VERSION and digest(s) == envelope['snapshot_sha256'], 'Snapshot binding')
    require(math.isfinite(s['known']) and s['known'] > 0, 'Lawful finite CSI')
    ctx, records, agent, view, channel = restore(s, cfg)
    verify_checkpoint(ctx, records, s['own_history'])
    stamps = s['native_stamps']
    require({row['peer'] for row in stamps} == set(range(ctx.n_agents))-{ctx.sender}
            and len(stamps) == ctx.n_agents-1, 'Native timestamp coverage')
    ages = []
    for row in stamps:
        created = row['native_created']
        require(type(created) is int and -1 <= created <= ctx.t and
                row['timestamp_source'] == 'native' and row['selected_created'] == created
                and tuple(row['native_pos']) == ctx.team_pos[row['peer']], 'Native timestamp source')
        ages.append(max(0, ctx.t-created))
    require(s['native_factor'] == (1./(1.+sum(ages)/len(ages)) if ages else 1.), 'Native factor')
    groups = groups_from_json(s['groups'])
    require(s['budget'] == cfg.symbols_per_slot and s['price'] == cfg.energy_price, 'Budget/price config')
    require(len(groups) == len(s['probabilities']) == len(s['payloads']), 'Catalog rows')
    original = WireGOSC(cfg, channel, 'tom')
    rebuilt = original.build_groups(agent, s['known'], view)
    require(structural(groups) == structural(rebuilt), 'Native candidate identity')
    for gi, g in enumerate(groups):
        require(len(g.options) == len(s['probabilities'][gi]) == len(s['payloads'][gi]), 'Option rows')
        for oi, o in enumerate(g.options):
            require(o.value == s['groups'][gi]['options'][oi]['value'], 'Hex/decimal binding')
            probability = float(channel.success_prob(o.rate, s['known'], n=o.symbols))
            require(probability == s['probabilities'][gi][oi], 'Success probability')
            pkt = original.packet(agent, g, o, ctx.t)
            require(encode_packet(pkt, cfg).hex() == s['payloads'][gi][oi], 'Payload identity')
            require(o.value.hex() == rebuilt[gi].options[oi].value.hex(), 'Original ToM value')
    raw = original.evidence_voi(view, records,
        [o.n_records for g in groups if g.kind == 'EVID' for o in g.options],
        TeamModel(view, agent, cfg.tom_temperature))
    require(raw == {int(k): v for k, v in s['raw_tom'].items()}, 'Raw ToM binding')
    require(choose(groups, s['budget'], s['price'])['selected'] == s['selected'], 'Actual selection replay')
    return ctx, records, groups


def analyze_snapshot(envelope, cfg, prices):
    ctx, records, groups = validate_snapshot(envelope, cfg)
    s = envelope['snapshot']
    prefixes = sorted({o.n_records for g in groups if g.kind == 'EVID' for o in g.options})
    require(prefixes, 'Shadow snapshot must have EVID')
    raw = {method: evidence_values(ctx, records, prefixes, method)
           for method in ('g0', 'g1', 'shuffled')}
    positive = [n for n in prefixes if raw['g0'][n] > 0]
    scalar = raw['g1'][positive[0]]/raw['g0'][positive[0]] if positive else 1.
    scaled = {n: scalar*v for n, v in raw['g0'].items()}
    nonproportional = any(sign(raw['g1'][n], scaled[n]) != 0 for n in prefixes)
    catalogs = {method: alternate(groups, values, s['probabilities']) for method, values in raw.items()}
    catalogs['same_state_scale'] = alternate(groups, scaled, s['probabilities'])
    catalogs['public'] = alternate(groups)
    catalogs['native_age'] = alternate(groups, factor=s['native_factor'])
    tom = {int(k): v for k, v in s['raw_tom'].items()}
    catalogs['native_evid_age'] = alternate(groups,
        {n: v*s['native_factor'] for n, v in tom.items()}, s['probabilities'])
    catalogs['evid_periodic'] = alternate(groups,
        {n: v if (ctx.t+1) % 8 == 0 else 0. for n, v in tom.items()}, s['probabilities'])
    for method, catalog in catalogs.items():
        require(structural(catalog) == structural(groups), 'Shadow changed menu')
        if method != 'native_age':
            require(all(o.value.hex() == b.value.hex()
                for g, original in zip(catalog, groups) if g.kind != 'EVID'
                for o, b in zip(g.options, original.options)), 'Changed non-EVID value')
    selections = []
    all_evid = [(gi, oi, o) for gi, g in enumerate(groups) if g.kind == 'EVID'
                for oi, o in enumerate(g.options)]
    content_pairs = [(a, b) for a, b in combinations(all_evid, 2) if a[2].n_records != b[2].n_records]
    for price in prices:
        choices = {k: choose(v, s['budget'], price) for k, v in catalogs.items()}
        choices['native_price'] = choose(groups, s['budget'], price/s['native_factor'])
        flips = []
        for (gi, oi, a), (gj, oj, b) in combinations(all_evid, 2):
            if a.n_records == b.n_records:
                continue
            for level in ('raw', 'expected', 'net'):
                if level == 'raw':
                    v0 = (raw['g0'][a.n_records], raw['g0'][b.n_records])
                    v1 = (raw['g1'][a.n_records], raw['g1'][b.n_records])
                else:
                    v0 = (catalogs['g0'][gi].options[oi].value, catalogs['g0'][gj].options[oj].value)
                    v1 = (catalogs['g1'][gi].options[oi].value, catalogs['g1'][gj].options[oj].value)
                    if level == 'net':
                        v0 = (v0[0]-price*a.symbols, v0[1]-price*b.symbols)
                        v1 = (v1[0]-price*a.symbols, v1[1]-price*b.symbols)
                if sign(*v0) * sign(*v1) == -1:
                    flips.append(dict(level=level, option_indices=[oi, oj],
                        prefixes=[a.n_records, b.n_records], same_symbols=a.symbols == b.symbols))
        a, b = evid(choices['g0']), evid(choices['g1'])
        category = ('on_off' if (a is None) != (b is None) else
                    'prefix' if a and b and a['n_records'] != b['n_records'] else
                    'rate' if a and b and a['rate'] != b['rate'] else 'same_evid')
        non_evid_a = [r for r in choices['g0']['signature'] if r['kind'] != 'EVID']
        non_evid_b = [r for r in choices['g1']['signature'] if r['kind'] != 'EVID']
        selections.append(dict(price=price, choices=choices, robust_flips=flips,
            different_prefix_pair_count=len(content_pairs),
            same_symbols_pair_count=sum(a[2].symbols == b[2].symbols for a, b in content_pairs),
            non_evid_selection_changed=non_evid_a != non_evid_b, difference_category=category))
    controls = {signature_key(row['choices'][method]) for row in selections
        for method in ('public', 'g0', 'same_state_scale', 'native_age', 'native_price', 'native_evid_age', 'evid_periodic')}
    for row in selections:
        row['declared_controls_explain_selection'] = signature_key(row['choices']['g1']) in controls
        a, b = evid(row['choices']['g0']), evid(row['choices']['g1'])
        relevant = [f for f in row['robust_flips'] if a and b and
                    sorted(f['prefixes']) == sorted([a['n_records'], b['n_records']])]
        row['relevant_robust_flips'] = relevant
        row['content_witness'] = bool(nonproportional and relevant and
            row['difference_category'] == 'prefix' and not row['declared_controls_explain_selection'])
    restricted = {k: choose(alternate(groups, raw[k], s['probabilities'], restrict=prefixes[0]),
                            s['budget'], s['price']) for k in ('g0', 'g1')}
    _, _, agent, view, channel = restore(s, cfg)
    periodic = WirePeriodic(cfg.with_(sem_interval=8), channel)
    periodic_chosen = periodic.select(agent, s['known'], view)
    periodic_groups = [g for g, _ in periodic_chosen]
    validate_selection(periodic_groups, periodic_chosen, s['budget'])
    w, anchors = weights(ctx)
    return dict(snapshot_sha256=envelope['snapshot_sha256'], sender=ctx.sender, t=ctx.t,
        raw={m: {str(n): v for n, v in values.items()} for m, values in raw.items()},
        prefixes=prefixes, scalar=scalar, nonproportional=nonproportional,
        selections=selections, single_prefix=restricted,
        periodic_reference=dict(selected=selection_indices(periodic_groups, periodic_chosen),
            signature=[dict(kind=g.kind, cell=g.cell, rate=o.rate, n_records=o.n_records)
                       for g, o in periodic_chosen], scope='Independent WirePeriodic, not BF or identical menu; k8/eps.02, not historic eps0'),
        anchors=anchors, live_cells=int((~ctx.declared).sum()),
        base_saturated_cells=int(np.count_nonzero((sigmoid(ctx.Lc) == 0.) | (sigmoid(ctx.Lc) == 1.))),
        weight_range=[float(w[~ctx.declared.reshape(ctx.grid, ctx.grid)].min()),
                      float(w.max())] if (~ctx.declared).any() else None,
        comparison_scope='G0/G1 raw common units, alpha1; ToM cross-family selections uncalibrated, no superiority screen')


def benchmark_snapshot(envelope, cfg, rotation=0):
    """Replay cost: restore/context, native candidate build and BF, not deployment."""
    rows = []
    methods = ['public', 'g0', 'g1']
    methods = methods[rotation % 3:] + methods[:rotation % 3]
    for repetition in range(4):
        for method in methods:
            start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
            _, _, agent, view, channel = restore(envelope['snapshot'], cfg)
            copied_wall, copied_cpu = time.perf_counter_ns(), time.process_time_ns()
            scheme = (WireGOSC(cfg, channel, 'tom') if method == 'public' else
                      NativeValueWireGOSC(cfg, channel, method))
            groups = scheme.build_groups(agent, envelope['snapshot']['known'], view)
            built_wall, built_cpu = time.perf_counter_ns(), time.process_time_ns()
            choose(groups, cfg.symbols_per_slot, cfg.energy_price)
            end_wall, end_cpu = time.perf_counter_ns(), time.process_time_ns()
            rows.append(dict(method=method, repetition=repetition,
                phase='cold_first' if repetition == 0 else 'hot_repeat',
                restore_wall_ns=copied_wall-start_wall, restore_process_ns=copied_cpu-start_cpu,
                candidate_wall_ns=built_wall-copied_wall, candidate_process_ns=built_cpu-copied_cpu,
                bf_wall_ns=end_wall-built_wall, bf_process_ns=end_cpu-built_cpu,
                total_wall_ns=end_wall-start_wall, total_process_ns=end_cpu-start_cpu))
    return dict(rows=rows, scope='Independent replay total includes restoration, native TeamModel/wire/candidates and BF. Not a deployment clock; no per-method peak memory measured.')
