"""Factorial privileged-state diagnostics, not a deployable value estimator.

Expose private evidence and/or true positions only inside TeamModel's receiver
model. The original agents, scheduler, channel and simulator state are unchanged.
"""
from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
from gosc.voi import TeamModel


class _ReceiverView:
    def __init__(self, source, private, position):
        self.source = source
        self.cfg = source.cfg.with_(tom_oracle=True)
        self.agents = [SimpleNamespace(
            pos=agent.pos if position else source.team_pos.get(i, agent.pos),
            pending_llr=agent.pending_llr if private else np.zeros_like(agent.pending_llr),
            confirmed_pending=agent.confirmed_pending if private else set())
            for i, agent in enumerate(source.agents)]

    def __getattr__(self, name):
        return getattr(self.source, name)


def model_factory(mode):
    if mode not in ("shared", "private", "position", "joint"):
        raise ValueError(mode)

    def build(sim, sender, temperature):
        if mode == "shared":
            # Override only the model-view flag, never the live simulation config.
            view = _ReceiverView(sim, False, False)
            view.cfg = sim.cfg.with_(tom_oracle=False)
        else:
            view = _ReceiverView(sim, mode in ("private", "joint"), mode in ("position", "joint"))
        return TeamModel(view, sender, temperature)

    return build


@contextmanager
def receiver_oracle(mode):
    """Process-local diagnostic injection, restoring both parallel code paths."""
    import gosc.schemes as schemes
    import gosc.realistic as realistic
    old = schemes.TeamModel, realistic.TeamModel
    replacement = model_factory(mode)
    schemes.TeamModel = realistic.TeamModel = replacement
    try:
        yield
    finally:
        schemes.TeamModel, realistic.TeamModel = old
