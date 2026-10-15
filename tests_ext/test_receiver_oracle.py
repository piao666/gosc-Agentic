import numpy as np
import pytest

from gosc import Config, Simulation, run_episode, run_realistic
from gosc.voi import TeamModel
from extensions.receiver_oracle import model_factory, receiver_oracle


@pytest.mark.parametrize("mode", ["shared", "joint"])
@pytest.mark.parametrize("runner", [run_episode, run_realistic])
def test_diagnostic_endpoints_reproduce_original_modes(mode, runner):
    cfg = Config().with_(max_steps=40)
    reference = runner(cfg.with_(tom_oracle=mode == "joint"), "gosc", 1)
    with receiver_oracle(mode):
        actual = runner(cfg, "gosc", 1)
    assert actual == reference


def test_each_single_factor_changes_only_its_receiver_assumption():
    sim = Simulation(Config(), "gosc", 0)
    sender, mate = sim.agents[:2]
    sim.team_pos[1] = (0, 0)
    mate.pos = (10, 10)
    mate.pending_llr[4, 4] = 3.0
    shared = model_factory("shared")(sim, sender, 0.1)
    private = model_factory("private")(sim, sender, 0.1)
    position = model_factory("position")(sim, sender, 0.1)
    joint = model_factory("joint")(sim, sender, 0.1)
    np.testing.assert_array_equal(private.dist[1], shared.dist[1])
    np.testing.assert_array_equal(position.dist[1], joint.dist[1])
    assert not np.array_equal(shared.dist[1], position.dist[1])
    np.testing.assert_array_equal(private._belief_mass(1), joint._belief_mass(1))
    np.testing.assert_array_equal(position._belief_mass(1), shared._belief_mass(1))
    assert not np.array_equal(private._belief_mass(1), shared._belief_mass(1))
    assert sim.cfg.tom_oracle is False
    np.testing.assert_array_equal(mate.pending_llr[4, 4], 3.0)


def test_patch_restores_both_paths_even_on_exception():
    import gosc.schemes as schemes
    import gosc.realistic as realistic
    with pytest.raises(RuntimeError):
        with receiver_oracle("private"):
            assert schemes.TeamModel is realistic.TeamModel
            assert schemes.TeamModel is not TeamModel
            raise RuntimeError("intentional contract check")
    assert schemes.TeamModel is TeamModel
    assert realistic.TeamModel is TeamModel
