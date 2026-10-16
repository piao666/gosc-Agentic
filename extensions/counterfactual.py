"""Offline decoder interventions around unchanged native GOSC methods.

Only supports the approved base search/Planner/ideal-DL/orthogonal setting.
Hooks are instance-local, synchronous, and always removed before checkpointing.
No label is used by the scheduler. Original GOSC authors retain attribution.
"""
import copy
import hashlib
import json
import math

import numpy as np

from gosc.belief import box_sum, sigmoid
from gosc.schemes import GOSC
from gosc.voi import TeamModel


def plain(x):
    if isinstance(x, np.ndarray):
        return {"array_dtype": str(x.dtype), "shape": list(x.shape),
                "sha256": hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()}
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.random.Generator):
        return plain(x.bit_generator.state)
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (set, frozenset)):
        return sorted((plain(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(x, (tuple, list)) or type(x).__name__ == "deque":
        return [plain(v) for v in x]
    if hasattr(x, "__dict__"):
        return {"class": type(x).__name__, "fields": plain(vars(x))}
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    raise TypeError(f"Unsupported state type: {type(x)}")


def digest(x):
    return hashlib.sha256(json.dumps(plain(x), sort_keys=True, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def clone(sim):
    out = copy.deepcopy(sim)
    assert out.channel is out.scheme.channel and out.channel is not sim.channel
    assert digest(out) == digest(sim)
    return out


def validate_scope(sim):
    c = sim.cfg
    if not (type(sim.scheme) is GOSC and c.task == "search" and not c.llm_agents
            and sim.ideal_dl and not c.shared_budget and not c.tom_oracle
            and c.value_mode == "exact"):
        raise ValueError("Unsupported scope: base GOSC search, Planner, ideal DL, orthogonal only")
    if sim.scheme.log is not None:
        raise ValueError("Native scheme.log must be None before instrumentation")


def record_id(rec):
    return [int(rec.t), int(rec.agent), list(rec.pos), list(rec.det)]


def packet_description(agent, group, option, ordinal, records):
    identity = {"agent": int(agent.idx), "kind": group.kind, "ordinal": ordinal,
                "rate": float(option.rate), "bits": int(option.bits),
                "symbols": int(option.symbols), "n_records": int(option.n_records),
                "records": [record_id(r) for r in records[:option.n_records]],
                "intent": int(agent.target) if group.kind == "INTENT" else None,
                "confirm": int(group.cell) if group.kind == "CONF" else None}
    return {**identity, "packet_id": digest(identity)}


def planner_context(agent, p, others):
    """Offline diagnostic context; not an online feature table."""
    c = agent.cfg
    X, Y = agent._X, agent._Y
    score = box_sum(p, c.sense_radius)
    score = score / (1 + c.distance_discount * (abs(X-agent.pos[0]) + abs(Y-agent.pos[1])))
    for ox, oy in others:
        score = score * (1 - np.exp(-((X-ox)**2 + (Y-oy)**2) / (2*c.repulsion_sigma**2)))
    best = float(score.max())
    old = None if agent.target is None else float(score.flat[agent.target])
    return {"agent": agent.idx, "old_target": agent.target, "position": list(agent.pos),
            "distance_to_old_target": None if agent.target is None else
            sum(abs(a-b) for a, b in zip(agent.pos, divmod(agent.target, c.grid))),
            "score_best_without_tie_jitter": best, "score_old_without_tie_jitter": old,
            "hysteresis_margin_without_tie_jitter": None if old is None else best-c.hysteresis*old,
            "private_llr_l1": float(np.abs(agent.pending_llr).sum())}


def shadow_replan(sim):
    rng = copy.deepcopy(sim.plan_rng)
    rows = []
    for a in sim.agents:
        b = copy.deepcopy(a)
        p = sigmoid(sim.local_llr(a)).reshape(-1)
        p[sim.declared] = 0
        if a.confirmed_pending:
            p[list(a.confirmed_pending)] = 0
        p = p.reshape(sim.Lc.shape)
        others = list(sim.teammates(a.idx))
        row = planner_context(a, p, others)
        b.plan(p, others, rng)
        row["target"] = b.target
        rows.append(row)
    return rows


def decide_observed(sim, t):
    rows, originals = [], []
    def wrap(a, original):
        def plan(p, others, rng):
            others = list(others)
            row = planner_context(a, p, others)
            original(p, others, rng)
            row["target"] = a.target
            rows.append(row)
        return plan
    try:
        for a in sim.agents:
            if "plan" in vars(a):
                raise ValueError("Unexpected existing instance plan hook")
            originals.append(a)
            a.plan = wrap(a, a.plan)
        sim.phase_decide(t)
    finally:
        for a in originals:
            del a.plan
    return rows


def communicate_taped(sim, expected=None, selected_id=None, success=None, observe=False):
    """Run native communication, recording/verifying attempts and overriding one decode.

    Native decodes is ALWAYS called, including for the overridden packet, preserving
    RNG consumption. No early edge fusion and no alternative scheduling algorithm.
    """
    validate_scope(sim)
    if (selected_id is None) != (success is None):
        raise ValueError("Specify both selected_id and success, or neither")
    before = digest(sim)
    if expected is not None and before != expected["before_state_sha256"]:
        raise ValueError("Tape/state hash mismatch")
    old_tx, old_decode, old_step = sim.scheme.transmit, sim.channel.decodes, sim.agents[0].step
    if "transmit" in vars(sim.scheme) or "decodes" in vars(sim.channel) or "step" in vars(sim.agents[0]):
        raise ValueError("Unexpected existing hooks")
    attempts, agents, context, shadow = [], [], {}, []
    initial_counts = {k: getattr(sim, k) for k in ("bits", "symbols", "delivered_bits", "dl_bits")}
    old_targets = [a.target for a in sim.agents]
    def tx(a, t, known, instantaneous, view):
        context.update(agent=a, records=list(a.pending_records), ordinal=0,
                       known=float(known), instantaneous=float(instantaneous))
        ans = old_tx(a, t, known, instantaneous, view)
        groups, chosen, price, budget = sim.scheme.log[-1]
        agents.append({"agent": a.idx, "known_snr": float(known),
                       "instantaneous_snr": float(instantaneous), "price": price, "budget": budget,
                       "groups": [{"kind": g.kind, "cell": g.cell,
                                   "options": [vars(o) for o in g.options]} for g in groups]})
        return ans
    def decodes(rate, snr, n=None):
        _, chosen, _, _ = sim.scheme.log[-1]
        ordinal = context["ordinal"]
        group, option = chosen[ordinal]
        assert float(rate) == float(option.rate) and n == option.symbols
        desc = packet_description(context["agent"], group, option, ordinal, context["records"])
        pre = digest(sim.channel.rng)
        natural = bool(old_decode(rate, snr, n=n))
        event = {**desc, "natural_decode": natural, "decoder_rng_before": pre,
                 "decoder_rng_after": digest(sim.channel.rng),
                 "known_snr": context["known"], "instantaneous_snr": context["instantaneous"],
                 "success_probability": float(sim.channel.success_prob(rate, context["known"], n=n)),
                 "option_value": float(option.value)}
        if expected is not None:
            ref = expected["attempts"][len(attempts)]
            assert all(event[k] == ref[k] for k in event), "Native attempt/draw changed before fusion"
        event["effective_decode"] = bool(success) if desc["packet_id"] == selected_id else natural
        attempts.append(event)
        context["ordinal"] += 1
        return event["effective_decode"]
    def step():
        shadow.extend(shadow_replan(sim))
        old_step()
    sim.scheme.log = []
    sim.scheme.transmit = tx
    sim.channel.decodes = decodes
    if observe:
        sim.agents[0].step = step
    try:
        done = bool(sim.phase_communicate(sim.t))
        if observe and not shadow:  # terminal slot: native motion was correctly skipped
            shadow.extend(shadow_replan(sim))
    finally:
        del sim.scheme.transmit
        del sim.channel.decodes
        if observe:
            del sim.agents[0].step
        sim.scheme.log = None
    if expected is not None:
        assert len(attempts) == len(expected["attempts"])
        assert digest(agents) == digest(expected["agents"])
    if selected_id is not None:
        assert sum(e["packet_id"] == selected_id for e in attempts) == 1
    assert old_targets == [a.target for a in sim.agents], "Communication unexpectedly replanned"
    return {"before_state_sha256": before, "after_state_sha256": digest(sim),
            "attempts": attempts, "agents": agents, "done": done,
            "current_targets": old_targets, "shadow_pre_motion_replan": shadow,
            "current_cost": {k: getattr(sim, k)-v for k, v in initial_counts.items()}}


def select_packet(tape, seed, t):
    available = [e for e in tape["attempts"] if e["kind"] in ("EVID", "INTENT")]
    def key(e):
        return hashlib.sha256(f"Receiver-CF-v1|{seed}|{t}|{e['packet_id']}".encode()).hexdigest()
    return min(available, key=key) if available else None


ONLINE_FEATURE_FIELDS = {"point_id", "packet_id", "seed", "t", "sender", "kind", "rate",
                         "bits", "symbols", "tom", "tom_clipped", "option_value", "ps",
                         "tv", "aoi", "sender_position", "sender_target"}


def features(sim, event, seed):
    """Outcome-blind, sender-available features, stored apart from offline outcomes."""
    a, t = sim.agents[event["agent"]], sim.t
    team = TeamModel(sim, a, sim.cfg.tom_temperature)
    if event["kind"] == "EVID":
        records = a.pending_records[:event["n_records"]]
        assert [record_id(r) for r in records] == event["records"]
        delta = np.zeros_like(sim.Lc)
        for r in records:
            sim.sensor.apply(delta, r)
        tom = float(team.evidence_voi([delta], [records[-1].pos])[0])
        tv = float(np.abs(sigmoid(sim.Lc+delta)-sigmoid(sim.Lc))[~sim.declared.reshape(sim.Lc.shape)].sum())
        aoi = float(sum(t-r.t+1 for r in records))
    elif event["kind"] == "INTENT":
        tom, tv = float(team.intent_voi(a.target)), 0.0
        aoi = float(t-getattr(a, "_intent_t", t)+1)
    else:
        raise ValueError("Only EVID/INTENT are feature candidates")
    assert math.isclose(max(tom, 0)*event["success_probability"], event["option_value"],
                        rel_tol=1e-9, abs_tol=1e-12)
    out = {"point_id": f"{seed}:{t}", "packet_id": event["packet_id"], "seed": seed, "t": t,
           "sender": a.idx, "kind": event["kind"], "rate": event["rate"],
           "bits": event["bits"], "symbols": event["symbols"], "tom": tom,
           "tom_clipped": max(tom, 0), "option_value": event["option_value"],
           "ps": event["success_probability"], "tv": tv, "aoi": aoi,
           "sender_position": list(a.pos), "sender_target": a.target}
    assert set(out) == ONLINE_FEATURE_FIELDS
    return out


def future_streams(sim, seed, t, sender, replicate):
    key = [seed, t, sender, replicate]
    sim.sense_rng = np.random.default_rng(key+[1])
    sim.chan_rng = np.random.default_rng(key+[2])
    sim.plan_rng = np.random.default_rng(key+[3])
    sim.channel.rng = np.random.default_rng(key+[4])
    sim.dl_rng = np.random.default_rng(key+[5])
