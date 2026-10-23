"""Received-pose valuation contracts, not a paid closed-loop method.

The cache accepts serialized delivered frames only. No peer private state is read.
Native EVID timestamps follow the snapshot actually received by each observer.
Transport scheduling and system-wide DL/CPU costs remain separate experiments.
"""
from dataclasses import dataclass
from types import SimpleNamespace

from gosc.schemes import GOSC
from gosc.realistic import RealisticGOSC, RealisticSimulation
from gosc.simulator import Simulation
from .receiver_summary_audit import unframe
from .receiver_transport_replay import read_batch


@dataclass(frozen=True)
class NativePose:
    created: int
    pos: tuple


@dataclass(frozen=True)
class ReceivedPose:
    created: int
    received: int
    pos: tuple
    valid_until: int


class PoseKnowledge:
    """Mission-local namespace. An independent local map belongs to each observer."""

    def __init__(self, starts, grid, ttl=20):
        if grid < 1 or grid > 32 or ttl < 0:
            raise ValueError("Unsupported grid/TTL")
        self.grid, self.ttl = grid, ttl
        initial = {k: NativePose(-1, tuple(p)) for k, p in starts.items()}
        self.native = {k: dict(initial) for k in starts}
        self.cache = {k: {} for k in starts}
        self.conflicts = []

    def receive_native(self, observer, snapshot):
        # Assign the received snapshot, not max(timestamp): native may regress.
        if observer not in self.native:
            raise ValueError("Unknown observer")
        if set(snapshot) != set(self.native[observer]):
            raise ValueError("Native peer set changed")
        self.native[observer] = dict(snapshot)

    def _accept(self, observer, item, received):
        if observer not in self.cache or item['sender'] not in self.native[observer]:
            raise ValueError("Unknown observer/source")
        if item['pose'] is None:
            return False  # novelty-only frames cannot create a pose or belief.
        if item['pose'] >= self.grid * self.grid:
            raise ValueError("Pose outside grid")
        # Caller must have received the bytes before a later decision boundary.
        if not item['created'] < received <= item['created'] + self.ttl:
            return False
        pos = divmod(item['pose'], self.grid)
        old = self.cache[observer].get(item['sender'])
        if old and old.created > item['created']:
            return False
        if old and old.created == item['created'] and old.pos != pos:
            # Fail closed: poison the generation rather than choosing a winner.
            self.conflicts.append((observer, item['sender'], item['created']))
            del self.cache[observer][item['sender']]
            return False
        if (observer, item['sender'], item['created']) in self.conflicts:
            return False
        self.cache[observer][item['sender']] = ReceivedPose(
            item['created'], received, pos, item['created'] + self.ttl)
        return True

    def receive_frame(self, observer, frame, received):
        item = unframe(frame, received, max_age=self.ttl)
        return self._accept(observer, item, received)

    def receive_snapshot(self, observer, frame, received):
        items = read_batch(frame, received)  # whole frame CRC validated first
        return [self._accept(observer, item, received) for item in items]

    def value_view(self, view, sender, now):
        if view.cfg.tom_oracle:
            raise ValueError("Oracle information is forbidden")
        if sender not in self.native or now != view.t:
            raise ValueError("Observer/time mismatch")
        positions = dict(view.team_pos)
        for peer, item in self.cache[sender].items():
            native = self.native[sender].get(peer)
            if peer == sender or peer not in positions or native is None:
                continue
            # Ledger must describe the public value actually visible now.
            if native.pos != tuple(positions[peer]):
                continue
            if not item.received <= now <= item.valid_until:
                continue
            if item.created == native.created and item.pos != native.pos:
                continue
            if item.created > native.created:
                positions[peer] = item.pos
        # Deliberately no .agents accessor: native nonoracle TeamModel needs none.
        return SimpleNamespace(cfg=view.cfg, sensor=view.sensor, t=view.t,
                               Lc=view.Lc, declared=view.declared,
                               team_pos=positions, team_intent=dict(view.team_intent))


class _PoseValueMixin:
    def __init__(self, cfg, channel, knowledge=None, **kwargs):
        if cfg.tom_oracle or cfg.task != 'search' or cfg.shared_budget or cfg.llm_agents:
            raise ValueError("Only nonoracle Planner search with orthogonal UL is supported")
        self.pose_knowledge = knowledge
        super().__init__(cfg, channel, name='pose_cache_tom_contract', **kwargs)

    def build_groups(self, agent, snr_mean, sim):
        if self.pose_knowledge is None:
            raise RuntimeError("A received native timestamp ledger is required")
        projected = self.pose_knowledge.value_view(sim, agent.idx, sim.t)
        return super().build_groups(agent, snr_mean, projected)


class PoseGOSC(_PoseValueMixin, GOSC):
    pass


class PoseRealisticGOSC(_PoseValueMixin, RealisticGOSC):
    pass


class _LedgerSimulationMixin:
    """Timestamp bookkeeping only; original world, policy, frames and RNG unchanged."""

    def __init__(self, cfg, scheme, seed, **kwargs):
        super().__init__(cfg, scheme, seed, **kwargs)
        self.pose_knowledge = PoseKnowledge(self.team_pos, cfg.grid)
        self._pose_edge = dict(self.pose_knowledge.native[0])
        self._pose_snaps = {-1: dict(self._pose_edge)}

    def deliver(self, agent, pkt, t):
        super().deliver(agent, pkt, t)
        if pkt.records:
            last = pkt.records[-1]
            self._pose_edge[agent.idx] = NativePose(last.t, tuple(last.pos))

    def _downlink(self, t):
        self._pose_snaps[t] = dict(self._pose_edge)
        super()._downlink(t)
        for observer in self.pose_knowledge.native:
            cutoff = t if self.ideal_dl else self.view_t[observer]
            self.pose_knowledge.receive_native(observer, self._pose_snaps[cutoff])
        oldest = t if self.ideal_dl else min(self.view_t)
        for stamp in list(self._pose_snaps):
            if stamp < oldest:
                del self._pose_snaps[stamp]

    def enable_pose_values(self):
        """Explicit contract hook; no paid transport is installed by this call."""
        cls = PoseRealisticGOSC if isinstance(self, RealisticSimulation) else PoseGOSC
        self.scheme = cls(self.cfg, self.channel, self.pose_knowledge)


class PoseLedgerSimulation(_LedgerSimulationMixin, Simulation):
    pass


class PoseLedgerRealisticSimulation(_LedgerSimulationMixin, RealisticSimulation):
    pass
