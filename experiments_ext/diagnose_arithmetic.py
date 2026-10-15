"""Bounded, explicitly intervened numerical probes of a blocked baseline.

No result below is a replacement baseline. All files are exclusive-created.
"""
import argparse
from dataclasses import asdict
import datetime as dt
import importlib.metadata as md
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import subprocess

from experiments_ext.reproduce import ROOT, save, sha, git


def selected(groups, chosen):
    return [dict(group=next(i for i, x in enumerate(groups) if x is g),
                 kind=g.kind, cell=g.cell, option=asdict(o)) for g, o in chosen]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--modes", nargs="+", default=["original", "realistic", "power-math", "scalar-math"],
                    choices=["original", "realistic", "power-math", "scalar-math"])
    ap.add_argument("--price", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    import numpy as np
    from gosc import Config, Simulation
    from gosc.channel import Channel
    from gosc.realistic import RealisticSimulation
    cfg = Config().with_(energy_price=args.price)
    original = Channel.success_prob
    start = time.perf_counter()
    outputs = []
    for mode in args.modes:
        def probability(self, rate, snr_mean, n=None):
            if self.csit or self.fbl:
                return original(self, rate, snr_mean, n)
            rates = np.asarray(rate)
            exponents = np.asarray([-(math.pow(2.0, float(r)) - 1.0) / snr_mean
                                    for r in rates.flat]).reshape(rates.shape)
            if mode == "power-math":
                return np.exp(exponents)
            return np.asarray([math.exp(float(x)) for x in exponents.flat]).reshape(rates.shape)
        Channel.success_prob = probability if mode in ("power-math", "scalar-math") else original
        sim = (RealisticSimulation if mode == "realistic" else Simulation)(cfg, "gosc_bits", args.seed)
        sim.scheme.log = []
        transmit = sim.scheme.transmit
        count = 0
        with (args.output / f"{mode}-trace.jsonl").open("x", encoding="utf-8") as f:
            def traced(agent, t, snr_mean, snr_inst, view):
                nonlocal count
                out = transmit(agent, t, snr_mean, snr_inst, view)
                groups, chosen, price, budget = sim.scheme.log[-1]
                f.write(json.dumps(dict(t=t, agent=agent.idx, pos=list(agent.pos),
                    snr_mean=snr_mean, snr_inst=snr_inst, price=price, budget=budget,
                    groups=[asdict(g) for g in groups], chosen=selected(groups, chosen),
                    tx_bits=out.bits, tx_symbols=out.symbols,
                    delivered=[p.kind for p in out.delivered]), default=lambda x: x.item()) + "\n")
                count += 1
                return out
            sim.scheme.transmit = traced
            t0 = time.perf_counter()
            result = sim.run()
            elapsed = time.perf_counter() - t0
        row = dict(mode=mode, output=result, trace_records=count, elapsed_seconds=elapsed,
                   trace_sha256=sha(args.output / f"{mode}-trace.jsonl"))
        save(args.output / f"{mode}-output.json", row)
        outputs.append(row)
        print(mode, {k: result[k] for k in ("completion_time", "symbols", "bits")}, flush=True)
    Channel.success_prob = original
    try:
        commit, dirty = git("rev-parse", "HEAD"), bool(git("status", "--short"))
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    import gosc
    source_dir = Path(gosc.__file__).parent
    save(args.output / "manifest.json", dict(status="completed", timestamp=dt.datetime.now(dt.timezone.utc).isoformat(),
        git_commit=commit, working_tree_dirty=dirty,
        gosc_source_sha256={p.name: sha(p) for p in sorted(source_dir.glob("*.py"))},
        source_sha256=sha(__file__), config=asdict(cfg), seed=args.seed, scheme="gosc_bits",
        modes=args.modes, python=sys.version, numpy=md.version("numpy"), os=platform.platform(),
        elapsed_seconds=time.perf_counter()-start, llm_cache_mode="not_used", models=[],
        notes="power-math/scalar-math are arithmetic interventions, not baseline reproduction; realistic is an upstream parallel code path."))


if __name__ == "__main__":
    main()
