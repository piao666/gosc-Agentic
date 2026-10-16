"""Synthetic mechanism contracts, not a mission-performance experiment.

The fixtures deliberately expose assumptions; their frequency is not estimated.
No upstream result writer or diagnostic main() is called.
"""
import copy

import numpy as np

from experiments.analyze_fidelity import rk
from experiments.diagnose_value import force
from gosc import Config, Simulation
from gosc.agent import Agent
from gosc.belief import Obs
from gosc.messages import Packet, evidence_sizes
from gosc.schemes import TxResult
from gosc.voi import TeamModel


def fixture():
    c = Config(grid=7, n_agents=2, n_victims=1, sense_radius=0,
               distance_discount=0, max_steps=3)
    s = Simulation(c, "gosc", 991234)
    s._start()
    for a in s.agents:
        a.pos = (3, 3)
        a.target = 1
        a.queued_llr = np.zeros_like(s.Lc)
    return s


def evidence(s):
    a = s.agents[0]
    rec = Obs(0, 0, (0, 0), ())
    a.pending_records.append(rec)
    s.sensor.apply(a.pending_llr, rec)
    s.sensor.apply(a.queued_llr, rec)
    return a, rec


def test_real_planner_remembers_old_target():
    s = fixture()
    p = np.zeros_like(s.Lc)
    p.flat[1], p.flat[2] = 0.9, 1.0
    old = s.agents[1]
    fresh = Agent(1, old.pos, s.cfg)
    old.plan(p, [], np.random.default_rng(42))
    fresh.plan(p, [], np.random.default_rng(42))
    assert old.target == 1
    assert fresh.target == 2


def test_proxy_does_not_condition_on_receiver_old_target():
    s = fixture()
    a = s.agents[0]
    d = np.zeros_like(s.Lc)
    d.flat[2] = 0.5
    before = TeamModel(s, a, s.cfg.tom_temperature).evidence_voi([d], [a.pos])
    s.agents[1].target = 2
    after = TeamModel(s, a, s.cfg.tom_temperature).evidence_voi([d], [a.pos])
    np.testing.assert_array_equal(before, after)


def test_full_clone_isolated_and_internal_alias_preserved():
    s = fixture()
    evidence(s)
    b = copy.deepcopy(s)
    assert b.scheme.channel is b.channel
    assert b.channel is not s.channel
    assert b.plan_rng.bit_generator.state == s.plan_rng.bit_generator.state
    b.Lc.flat[0] += 1
    b.agents[0].pending_llr.flat[0] += 1
    b.agents[0].pending_records.clear()
    b.plan_rng.random()
    assert b.Lc.flat[0] != s.Lc.flat[0]
    assert b.agents[0].pending_llr.flat[0] != s.agents[0].pending_llr.flat[0]
    assert len(s.agents[0].pending_records) == 1
    assert b.plan_rng.bit_generator.state != s.plan_rng.bit_generator.state
    # This upstream helper is a broadcast view, not a full simulator checkpoint.
    assert len(s._snapshot()) == 4


def test_author_force_preserves_sender_local_belief_and_clears_queue():
    s = fixture()
    a, rec = evidence(s)
    local = s.local_llr(a).copy()
    common = s.Lc.copy()
    force(s, 0, "E")
    np.testing.assert_allclose(s.local_llr(a), local)
    np.testing.assert_allclose(a.pending_llr, 0)
    np.testing.assert_allclose(a.queued_llr, 0)
    assert not a.pending_records
    assert not np.array_equal(common, s.Lc)
    assert s.team_pos[0] == rec.pos
    assert s.skip_tx == {0}
    # Instant delivery is not charged as an actual uplink attempt.
    assert s.bits == s.symbols == 0
    assert s.delivered_bits > 0


def test_native_uplink_decisions_precede_all_fusion_and_motion_keeps_target():
    s = fixture()
    a, rec = evidence(s)
    before = s.Lc.copy()
    seen = []

    def tx(agent, t, mean, instantaneous, view):
        seen.append(view.Lc.copy())
        if agent.idx == 0:
            return TxResult([Packet("EVID", 0, evidence_sizes([rec], s.cfg)[0],
                                    0, records=[rec])])
        return TxResult([])

    s.scheme.transmit = tx
    s.phase_communicate(0)
    assert len(seen) == 2
    for common_at_transmit in seen:
        np.testing.assert_array_equal(common_at_transmit, before)
    assert not np.array_equal(s.Lc, before)
    assert [a.target for a in s.agents] == [1, 1]
    assert [a.pos for a in s.agents] == [(2, 3), (2, 3)]


def test_author_force_changes_other_uplink_inputs_before_native_fusion():
    s = fixture()
    evidence(s)
    b = copy.deepcopy(s)
    common = s.Lc.copy()
    force(b, 0, "E")
    seen = []

    def tx(agent, t, mean, instantaneous, view):
        seen.append((agent.idx, view.Lc.copy()))
        return TxResult([])

    b.scheme.transmit = tx
    b.phase_communicate(0)
    assert len(seen) == 1 and seen[0][0] == 1
    assert not np.array_equal(seen[0][1], common)


def test_equal_rng_seed_is_not_cell_aligned_sensor_noise_after_path_split():
    c = Config(grid=7, n_agents=2, n_victims=1, sense_radius=2)
    s = Simulation(c, "gosc", 991234)
    edge_rng = np.random.default_rng(42)
    middle_rng = copy.deepcopy(edge_rng)
    s.world.sense((0, 0), s.sensor, edge_rng)  # 3 x 3 draws
    s.world.sense((3, 3), s.sensor, middle_rng)  # 5 x 5 draws
    assert edge_rng.bit_generator.state != middle_rng.bit_generator.state


def test_upstream_ordinal_ranks_split_equal_values():
    ranks = rk(np.array([0.0, 0.0, 1.0]))
    assert ranks[0] != ranks[1]
    assert sorted(ranks.tolist()) == [0, 1, 2]
