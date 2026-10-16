"""Bounded synthetic runner contracts, not the seed5000-5007 pilot."""
import copy

import numpy as np
import pytest

from extensions.counterfactual import (clone, communicate_taped, decide_observed,
    digest, features, future_streams, select_packet, ONLINE_FEATURE_FIELDS)
from gosc import Config, Simulation
from gosc.belief import Obs
from gosc.messages import evidence_sizes, intent_bits, confirm_bits
from gosc.schemes import GOSC, Group, Option


def native():
    s = Simulation(Config(grid=7, n_agents=2, n_victims=2, max_steps=6), "gosc", 991235)
    s._start()
    s.phase_decide(0)
    return s


def synthetic(monkeypatch, terminal=False, fbl=False):
    c = Config(grid=7, n_agents=2, n_victims=1 if terminal else 2,
               sense_radius=0, max_steps=5, snr_ref_db=60,
               error_model="fbl" if fbl else "outage")
    s = Simulation(c, "gosc", 991235)
    s._start()
    a = s.agents[0]
    for b in s.agents:
        b.pos, b.target = (3, 3), 1
        b.queued_llr = np.zeros_like(s.Lc)
    a.confirmed_pending.add(next(iter(s.world.victims)))
    for t in [0, 1]:
        r = Obs(t, 0, (2, 2), ())
        a.pending_records.append(r)
        s.sensor.apply(a.pending_llr, r)
        s.sensor.apply(a.queued_llr, r)

    def groups(self, agent, mean, sim):
        if agent.idx:
            return []
        result = []
        for cell in sorted(agent.confirmed_pending):
            b = confirm_bits(c)
            result.append(Group("CONF", [Option(1., b, b, 100.)], cell=cell))
        if agent.target != getattr(agent, "acked_intent", agent.shared_intent):
            b = intent_bits(c)
            result.append(Group("INTENT", [Option(1., b, b, 100.)]))
        if agent.pending_records:
            b = evidence_sizes(agent.pending_records, c)[0]
            result.append(Group("EVID", [Option(1., b, b, 100., n_records=1)]))
        return result
    monkeypatch.setattr(GOSC, "build_groups", groups)
    return s


def test_native_tape_and_noop_twins_match_entire_continuation():
    s = native()
    taped, direct, replay = clone(s), clone(s), clone(s)
    tape = communicate_taped(taped)
    done = direct.phase_communicate(0)
    assert tape["done"] == done and digest(taped) == digest(direct)
    communicate_taped(replay, expected=tape)
    assert digest(replay) == digest(direct)
    for t in range(1, s.cfg.max_steps):
        if done:
            break
        direct.phase_decide(t)
        replay.phase_decide(t)
        done = direct.phase_communicate(t)
        assert replay.phase_communicate(t) == done
        assert digest(replay) == digest(direct)


def test_prefix_ack_queue_fusion_and_same_attempt_cost(monkeypatch):
    s = synthetic(monkeypatch)
    tape = communicate_taped(clone(s))
    assert [e["kind"] for e in tape["attempts"]] == ["CONF", "INTENT", "EVID"]
    e = tape["attempts"][-1]
    assert e["n_records"] == 1 and len(e["records"]) == 1
    yes, no = clone(s), clone(s)
    ty = communicate_taped(yes, tape, e["packet_id"], True, observe=True)
    tn = communicate_taped(no, tape, e["packet_id"], False, observe=True)
    assert ty["current_cost"]["bits"] == tn["current_cost"]["bits"]
    assert ty["current_cost"]["symbols"] == tn["current_cost"]["symbols"]
    assert len(yes.agents[0].pending_records) == 1
    assert len(no.agents[0].pending_records) == 2
    np.testing.assert_allclose(yes.local_llr(yes.agents[0]), no.local_llr(no.agents[0]))
    delta = np.zeros_like(s.Lc)
    s.sensor.apply(delta, s.agents[0].pending_records[0])
    np.testing.assert_allclose(yes.Lc-no.Lc, delta)
    np.testing.assert_allclose(no.agents[0].queued_llr-yes.agents[0].queued_llr, delta)
    assert ty["current_targets"] == tn["current_targets"]
    for ey, en in zip(ty["attempts"][:-1], tn["attempts"][:-1]):
        assert ey == en
    # Failure leaves a real retry available on the next native communication call.
    no.t = 1
    retry = communicate_taped(no)
    assert any(x["records"] == e["records"] for x in retry["attempts"] if x["kind"] == "EVID")


def test_intent_override_changes_ack_and_public_intent_only_for_that_packet(monkeypatch):
    s = synthetic(monkeypatch)
    tape = communicate_taped(clone(s))
    e = next(x for x in tape["attempts"] if x["kind"] == "INTENT")
    yes, no = clone(s), clone(s)
    ty = communicate_taped(yes, tape, e["packet_id"], True)
    tn = communicate_taped(no, tape, e["packet_id"], False)
    assert yes.agents[0].acked_intent == s.agents[0].target
    assert not hasattr(no.agents[0], "acked_intent")
    assert 0 in yes.team_intent and 0 not in no.team_intent
    np.testing.assert_array_equal(yes.Lc, no.Lc)
    assert ty["attempts"][-1] == tn["attempts"][-1]


def test_decoder_rng_draw_consumed_even_when_overridden(monkeypatch):
    s = synthetic(monkeypatch, fbl=True)
    tape = communicate_taped(clone(s))
    e = tape["attempts"][-1]
    yes, no = clone(s), clone(s)
    communicate_taped(yes, tape, e["packet_id"], True)
    communicate_taped(no, tape, e["packet_id"], False)
    assert digest(yes.channel.rng) == digest(no.channel.rng)
    assert digest(yes.channel.rng) != digest(s.channel.rng)


def test_terminal_slot_has_no_extra_motion_and_shadow_is_nonmutating(monkeypatch):
    s = synthetic(monkeypatch, terminal=True)
    direct, observed = clone(s), clone(s)
    positions = [a.pos for a in s.agents]
    assert direct.phase_communicate(0)
    tape = communicate_taped(observed, observe=True)
    assert tape["done"] and tape["shadow_pre_motion_replan"]
    assert [a.pos for a in observed.agents] == positions
    assert digest(direct) == digest(observed)


def test_real_next_decision_observer_is_nonmutating_and_separate_from_shadow():
    a, b = native(), native()
    done = communicate_taped(a, observe=True)["done"]
    assert b.phase_communicate(0) == done
    if not done:
        rows = decide_observed(a, 1)
        b.phase_decide(1)
        assert digest(a) == digest(b)
        assert [r["target"] for r in rows] == [x.target for x in a.agents]


def test_empty_attempts_and_unavailable_selection():
    s = Simulation(Config(grid=7, n_agents=2, n_victims=2, max_steps=3,
                          energy_price=1e12), "gosc", 991235)
    s._start()
    s.phase_decide(0)
    tape = communicate_taped(clone(s))
    assert not tape["attempts"] and select_packet(tape, 991235, 0) is None


def test_tamper_rejected_and_hooks_cleaned_up(monkeypatch):
    s = synthetic(monkeypatch)
    tape = communicate_taped(clone(s))
    bad = copy.deepcopy(tape)
    bad["attempts"][0]["packet_id"] = "wrong"
    b = clone(s)
    with pytest.raises(AssertionError):
        communicate_taped(b, bad)
    assert "transmit" not in vars(b.scheme) and "decodes" not in vars(b.channel)
    assert b.scheme.log is None
    s.Lc.flat[0] += 1
    with pytest.raises(ValueError, match="hash mismatch"):
        communicate_taped(s, tape)


def test_feature_whitelist_and_outcome_blind_hash_selection():
    s = native()
    tape = communicate_taped(clone(s))
    chosen = select_packet(tape, 991235, 0)
    assert chosen is not None
    before = digest(s)
    f = features(s, chosen, 991235)
    assert set(f) == ONLINE_FEATURE_FIELDS and digest(s) == before
    changed = copy.deepcopy(tape)
    for e in changed["attempts"]:
        e["natural_decode"] = not e["natural_decode"]
        e["option_value"] = 9999999
    assert select_packet(changed, 991235, 0)["packet_id"] == chosen["packet_id"]


def test_all_five_future_streams_are_paired_and_replicates_differ():
    a, b = native(), native()
    future_streams(a, 991235, 0, 0, 1)
    future_streams(b, 991235, 0, 0, 1)
    assert digest(a) == digest(b)
    future_streams(b, 991235, 0, 0, 2)
    for field in ["sense_rng", "chan_rng", "plan_rng", "dl_rng"]:
        assert digest(getattr(a, field)) != digest(getattr(b, field))
    assert digest(a.channel.rng) != digest(b.channel.rng)


def test_statistics_preserve_bootstrap_mission_draw_multiplicity():
    from experiments_ext.analyze_receiver_cf import cluster_sample, mission_mean
    by = {1:[{"seed":1,"delta_T":1.}], 2:[{"seed":2,"delta_T":9.}]}
    sampled = cluster_sample(by, [1,1,2])
    assert mission_mean(sampled,"delta_T") == pytest.approx(11/3)
    # Different counts of points must not turn into mission weighting.
    assert mission_mean(by[1]+by[1]+by[2],"delta_T") == 5.


def test_statistics_keep_constant_rho_undefined_and_missing_pairs_visible():
    from experiments_ext.analyze_receiver_cf import rho, pair_points
    rows = [{"seed":i,"tom":1.,"delta_T":float(i)} for i in range(3)]
    assert rho(rows,"tom") is None
    points, missing = pair_points([{"point_id":"1:8"}], [])
    assert points == [] and missing == [{"point_id":"1:8","complete_pairs":0}]
    with pytest.raises(ValueError, match="Duplicate"):
        pair_points([], [{"point_id":"1:8","replicate":0,"success_branch":True}]*2)


def test_branch_timeout_is_a_record_not_a_fabricated_capped_result(monkeypatch):
    from experiments_ext.run_receiver_cf import branch
    s=synthetic(monkeypatch)
    tape=communicate_taped(clone(s))
    e=tape["attempts"][-1]
    row=branch(s,tape,e,991235,0,True,deadline=0)
    assert row["status"] == "timeout" and "result" not in row
    assert row["wall_seconds"] >= 0
