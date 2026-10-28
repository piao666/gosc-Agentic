"""HPC-only execution via hpc_runs; short fixtures are not efficacy samples."""
import copy
from dataclasses import replace
import itertools
import json
from pathlib import Path

import numpy as np
import pytest

from gosc.config import Config
from gosc.schemes import Group, Option
from extensions.causal_paid_simulation import CausalPaidSimulation
from extensions.information_identifiability import (
    InformationSimulation, ObservedCausalService, RULES, export_groups,
    local_age, local_summary_trace, selection_signature, select_rule, catalog_diagnostic,
)
from extensions.paid_receiver_service import ServiceConfig
from extensions.receiver_pose_interface import NativePose, ReceivedPose
from extensions.receiver_transport_replay import batch
from extensions.receiver_summary_audit import encode


SERVICE = ServiceConfig(100, 2000, 1., .001, .001)


def simulation(arm='public-fixed', observe=True, **kwargs):
    return InformationSimulation(Config(max_steps=12), 26000000, SERVICE,
                                 arm=arm, observe=observe, **kwargs)


def scientific_result(result):
    """Only labels and measured process-time (observer overhead) are excluded."""
    result = copy.deepcopy(result)
    for key in ('selection_process_seconds', 'scheme', 'scope', 'compute_scope'):
        result.pop(key, None)
    return result


def assert_same_state(a, b):
    assert scientific_result(a.result()) == scientific_result(b.result())
    assert a.service.events == b.service.events
    assert a.service.cpu_log == b.service.cpu_log
    assert a.service.attempt_log == b.service.attempt_log
    assert a.service.replay_log == b.service.replay_log
    assert a.service.task_received == b.service.task_received
    assert a._local_seen == b._local_seen
    assert a._outstanding == b._outstanding
    for name in ('sense_rng', 'plan_rng', 'dl_rng'):
        assert getattr(a, name).bit_generator.state == getattr(b, name).bit_generator.state
    assert a.channel.rng.bit_generator.state == b.channel.rng.bit_generator.state
    assert (a.chan_rng.t, a.chan_rng.k) == (b.chan_rng.t, b.chan_rng.k)
    for x, y in zip(a.local, b.local):
        np.testing.assert_array_equal(x.Lc, y.Lc)
        np.testing.assert_array_equal(x.declared, y.declared)
        assert x.team_pos == y.team_pos and x.team_intent == y.team_intent


@pytest.mark.parametrize('arm', list(RULES))
def test_observation_switch_preserves_scientific_results_and_noise_state(arm):
    a, b = simulation(arm, False), simulation(arm, True)
    a.run(); b.run()
    assert_same_state(a, b)
    assert a.observation() == [] and b.observation()


@pytest.mark.parametrize('mode', ['bits', 'aoi', 'periodic'])
def test_strong_simple_controls_observation_equivalence(mode):
    a = simulation(observe=False, mode=mode)
    b = simulation(observe=True, mode=mode)
    a.run(); b.run()
    assert_same_state(a, b)


@pytest.mark.parametrize('arm,legacy', [
    ('public-fixed', 'public'), ('paid-ignore', 'ignore'),
    ('paid-age', 'age'), ('paid-pose', 'pose'),
])
def test_existing_arms_preserve_legacy_gpv2_fixture(arm, legacy):
    a = simulation(arm)
    b = CausalPaidSimulation(Config(max_steps=12), 26000000, SERVICE, arm=legacy)
    a.run(); b.run()
    assert_same_state(a, b)


class ForbiddenCache:
    def __getitem__(self, key):
        raise AssertionError('Native timestamp rule read paid cache')


def test_native_age_never_reads_paid_cache():
    s = simulation('native-age'); v = s.local[0]; v.t = 5
    s.service.knowledge.cache = ForbiddenCache()
    factor, trace = local_age(s.service.knowledge, v, 0, 5, 'native', True)
    assert factor == pytest.approx(1 / 7)
    assert all(x['timestamp_source'] == 'native' for x in trace)


@pytest.mark.parametrize('item,eligible', [
    (ReceivedPose(3, 4, (10, 10), 23), True),
    (ReceivedPose(3, 6, (10, 10), 23), False),
    (ReceivedPose(3, 3, (10, 10), 23), False),
    (ReceivedPose(0, 1, (10, 10), 4), False),
    (ReceivedPose(-1, 1, (10, 10), 20), False),
])
def test_paid_timestamp_eligibility_and_fallback(item, eligible):
    s = simulation('paid-age'); v = s.local[0]; v.t = 5
    s.service.knowledge.cache[0][1] = item
    _, trace = local_age(s.service.knowledge, v, 0, 5, 'paid', True)
    row = next(x for x in trace if x['peer'] == 1)
    assert (row['timestamp_source'] == 'summary') == eligible
    assert local_summary_trace(s.service.knowledge, v, 0, 5)[0]['eligible'] == eligible


def test_mismatched_view_does_not_admit_summary():
    s = simulation(); v = s.local[0]; v.t = 5
    s.service.knowledge.cache[0][1] = ReceivedPose(3, 4, (10, 10), 23)
    v.team_pos[1] = (20, 20)
    _, trace = local_age(s.service.knowledge, v, 0, 5, 'paid', True)
    assert trace[0]['timestamp_source'] == 'native'
    assert 'native_view_mismatch' in local_summary_trace(s.service.knowledge, v, 0, 5)[0]['reasons']


def test_position_projection_does_not_break_timestamp_matching():
    s = simulation('paid-pose-age'); v = s.local[0]; v.t = 5
    s.service.knowledge.cache[0][1] = ReceivedPose(3, 4, (10, 10), 23)
    projected = s.valuation_view(v, 0, 5)
    assert projected.team_pos[1] == (10, 10) and v.team_pos[1] != (10, 10)
    # Age is computed on pre-projection local information, never on that copy.
    _, trace = local_age(s.service.knowledge, v, 0, 5, 'paid', True)
    assert trace[0]['selected_created'] == 3
    assert not hasattr(projected, 'agents') and not hasattr(projected, 'event_seed')


@pytest.mark.parametrize('arm', list(RULES))
def test_purchase_status_and_complete_resource_accounting(arm):
    s = simulation(arm); r = s.run(); c = r['service']['cost']
    paid = RULES[arm].legacy_arm != 'public'
    assert (c['ul_summary_bytes'] > 0) == paid
    obs = s.observation()
    attempts = [x for x in obs if x['event'] == 'ul_attempt']
    assert sum(x['uses'] for x in attempts) == c['ul_uses']
    assert sum(x['bytes'] for x in attempts if x['message_kind'] == 'summary') == c['ul_summary_bytes']
    assert sum(x['uses'] for x in obs if x['event'] == 'dl_service') == c['dl_uses']
    assert sum(x['seconds'] for x in obs if x['event'] == 'cpu_admit') == pytest.approx(c['cpu_seconds'])
    assert sum(x['bytes'] for x in obs if x['event'] == 'dl_enqueue') == c['dl_offered_bytes']
    assert len([x for x in obs if x['event'] == 'decision']) == r['selection_calls']
    json.dumps(obs, allow_nan=False)


def test_typed_partial_dl_cpu_and_right_censoring():
    c = replace(SERVICE, dl_capacity=1, decode_seconds=2.)
    s = ObservedCausalService({0:(0, 0), 1:(1, 1)}, 4, c, observe=True)
    s._enqueue_dl(3, 'summary_snapshot', batch([encode(0, 0, 0, 1)]))
    s.tick(0); s.tick(1)
    end = s.observation_end()
    enqueue = next(x for x in s.observations if x['event'] == 'dl_enqueue')
    assert end['unserved'][0]['remaining_uses'] == enqueue['required_uses'] - 2
    assert not [x for x in s.observations if x['event'] == 'decoded']
    assert s.finish()['cost']['dl_uses'] == 2


def test_expired_received_generation_is_logged_but_not_rejuvenated():
    s = ObservedCausalService({0:(0, 0)}, 4, replace(SERVICE, ttl=1, encode_seconds=2.), observe=True)
    s.submit_pose(0, 1, 0)
    for t in range(3):
        s.tick(t)
    assert s.cost['cpu_expired_summaries'] == 1
    assert s.cost['ul_summary_bytes'] == 0
    assert any(x['event'] == 'cpu_complete' and x['message_kind'] == 'pose_ready' for x in s.observations)


def test_selector_scaling_price_and_ideal_objective_on_bounded_catalog():
    groups = [Group('EVID', [Option(1., 10, 10, .3), Option(2., 10, 5, .2)]),
              Group('INTENT', [Option(1., 4, 4, .09)])]
    original = copy.deepcopy(groups)
    for factor, price in itertools.product((1., .5, .125), (0., .01, .02)):
        a = select_rule(groups, 12, price, factor, 'scale')
        b = select_rule(groups, 12, price, factor, 'price')
        assert selection_signature(a) == selection_signature(b)
        feasible = []
        for options in itertools.product(*[[None, *g.options] for g in groups]):
            selected = [o for o in options if o is not None]
            if sum(o.symbols for o in selected) <= 12:
                feasible.append((sum(o.value for o in selected), sum(o.symbols for o in selected)))
        for value, symbols in feasible:
            assert factor * value - price * symbols == pytest.approx(factor * (value - price / factor * symbols))
    assert groups == original
    assert export_groups(groups)[0]['options'][0]['value_hex'] == (.3).hex()


@pytest.mark.parametrize('factor,price,form', [(0., 1., 'scale'), (-1., 1., 'scale'),
    (float('inf'), 1., 'price'), (1., -1., 'price'), (1., 0., 'invalid')])
def test_invalid_selector_inputs_fail_closed(factor, price, form):
    with pytest.raises(ValueError):
        select_rule([], 100, price, factor, form)


def test_future_or_oracle_timestamp_boundary():
    s = simulation(); v = s.local[0]
    s.service.knowledge.native[0][1] = NativePose(1, v.team_pos[1])
    with pytest.raises(ValueError, match='Future'):
        local_age(s.service.knowledge, v, 0, 0, 'native')
    v.cfg = replace(v.cfg, tom_oracle=True)
    with pytest.raises(ValueError, match='oracle'):
        local_age(s.service.knowledge, v, 0, 0, 'native')


def test_protocol_has_no_calibration_test_or_training_permission():
    root = Path(__file__).resolve().parents[1]
    p = json.loads((root / 'research/protocols/information_identifiability_v1.json').read_text())
    assert p['stage'] == 'contracts_then_bounded_cost_probe'
    assert not p['calibration_authorized'] and not p['test_execution_authorized'] and not p['training']
    assert p['probe_steps'] < 400 and p['workers'] == 1
    assert set(p['arms']) == set(RULES)
    assert len(set(p['fixture_seeds'] + p['probe_seed_candidates'])) == 3


def test_independent_audit_accepts_observed_fixture_and_rejects_tampering():
    from scripts.audit_information_identifiability import resource_audit, decision_audit
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / 'research/protocols/information_identifiability_v1.json').read_text())
    s = simulation('paid-pose-age'); result = s.run(); events = s.observation()
    resource_audit(events, result, plan)
    decision_audit(events, result)
    altered = copy.deepcopy(events)
    next(e for e in altered if e['event'] == 'decision')['factor'] += .25
    with pytest.raises(ValueError, match='factor'):
        decision_audit(altered, result)
    altered = copy.deepcopy(events)
    next(e for e in altered if e['event'] == 'dl_service')['uses'] += 1
    with pytest.raises(ValueError):
        resource_audit(altered, result, plan)


def test_paid_native_control_ignores_newer_paid_timestamp():
    s = simulation('paid-native-age'); v = s.local[0]; v.t = 5
    s.service.knowledge.cache[0][1] = ReceivedPose(3, 4, (10, 10), 23)
    native, _ = local_age(s.service.knowledge, v, 0, 5, 'native')
    paid, _ = local_age(s.service.knowledge, v, 0, 5, 'paid')
    assert native < paid and s.use_pose
    assert s.valuation_view(v, 0, 5) is v


@pytest.mark.parametrize('arm', ['native-age', 'native-price', 'paid-age', 'paid-price', 'paid-pose-age'])
def test_same_logged_catalog_replays_actual_rule_without_assuming_cross_form_equality(arm):
    s = simulation(arm); s.run()
    for decision in s.decisions:
        diagnostic = catalog_diagnostic(decision)
        assert diagnostic['replay_matches_actual']
        assert diagnostic['scale_price_same'] == (diagnostic['selected']['scale'] == diagnostic['selected']['price'])


def test_independent_audit_rejects_selector_claim_detached_from_actual_decision(tmp_path):
    from scripts.audit_information_identifiability import audit
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / 'research/protocols/information_identifiability_v1.json').read_text())
    plan.update(probe_seed_candidates=[26000000], probe_max_missions=2)
    rows = []
    observed = None
    for observe in (False, True):
        s = simulation(observe=observe); result = s.run()
        rows.append(dict(seed=26000000, case={'id':'fixture'}, observe=observe,
                         id='fixture'+str(int(observe)), result=result))
        if observe:
            observed = s
    events = observed.observation()
    diagnostics = [catalog_diagnostic(d) for d in observed.decisions]
    assert any(d['selected'][d['original_form']] for d in diagnostics)
    data = dict(calibration_run=False, formal_test_run=False, training=False, efficacy_N=0,
        rows=rows, frozen={'plan':plan, 'cases':[{'id':'fixture'}],
                          'worlds':{'26000000':observed.input_world_sha256}})
    result_file = tmp_path / 'results.json'
    result_file.write_text(json.dumps(data))
    (tmp_path / 'fixture1-observations.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    numeric_file = tmp_path / 'fixture1-selector.json'
    numeric_file.write_text(json.dumps(dict(decisions=diagnostics,
        same_catalog_mismatches=sum(not d['scale_price_same'] for d in diagnostics), replay_mismatches=0)))
    assert audit(result_file)['status'] == 'passed'
    # Internally consistent producer assertions, contradicting real selections.
    for d in diagnostics:
        d.update(selected={'scale':[], 'price':[]}, replay_matches_actual=True, scale_price_same=True)
    numeric_file.write_text(json.dumps(dict(decisions=diagnostics, same_catalog_mismatches=0, replay_mismatches=0)))
    with pytest.raises(ValueError, match='[Ss]elector|[Rr]eplay|[Dd]ecision'):
        audit(result_file)


@pytest.mark.parametrize('seed', [0, 1001, 3001, 4001, 20000001, 24000001])
def test_all_archived_reserved_range_interiors_are_protected(seed):
    from scripts import repro_information_identifiability as runner
    assert runner.is_reserved_seed(seed)
