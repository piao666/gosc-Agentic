"""Bounded original replication and independently seeded oracle diagnostics.

All outputs are append-only within a new stage directory. No upstream result writes.
"""
import argparse
import datetime as dt
from dataclasses import asdict
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
import traceback

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_name] = "1"
os.environ.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")

from experiments_ext.reproduce import ROOT, BASE, save, sha, check_protected


def config_key(cfg):
    return hashlib.sha256(json.dumps(asdict(cfg), sort_keys=True).encode()).hexdigest()


def differences(expected, actual):
    diff = []
    for key, value in expected.items():
        if key in ("scheme", "param", "seed"):
            continue
        if key not in actual:
            diff.append({"field": key, "expected": value, "actual": "missing"})
        elif isinstance(value, (float, int)) and value is not None:
            if actual[key] is None or abs(actual[key] - value) > 1e-9:
                diff.append({"field": key, "expected": value, "actual": actual[key]})
        elif actual[key] != value:
            diff.append({"field": key, "expected": value, "actual": actual[key]})
    return diff


def _job(job):
    from gosc import run_episode
    cfg, scheme, seed = job["cfg"], job["scheme"], job["seed"]
    assert not cfg.llm_agents
    record = {k: v for k, v in job.items() if k not in ("cfg", "expected")}
    record["config_key"] = config_key(cfg)
    start = time.perf_counter()
    try:
        if job.get("mode"):
            from extensions.receiver_oracle import receiver_oracle
            with receiver_oracle(job["mode"]):
                output = run_episode(cfg, scheme, seed)
        else:
            output = run_episode(cfg, scheme, seed)
        record.update(output=output, status="completed",
                      reference_differences=differences(job.get("expected", {}), output))
    except Exception:
        record.update(status="failed", traceback=traceback.format_exc())
    record["elapsed_seconds"] = time.perf_counter() - start
    return record


def r4_jobs(run):
    from experiments.run_revision import experiments
    from experiments.validate_headline import select, SETTINGS
    src = run / "upstream_workspace/results"
    ex = experiments()
    frontier = json.loads((src / "rev_frontier.json").read_text())["rows"]
    private = json.loads((src / "rev_private.json").read_text())["rows"]
    frozen = json.loads((src / "rev_validation.json").read_text())
    jobs, selections = [], {}
    for campaign, points, rows in [("frontier-W100", [p for p in ex["frontier"] if p[1].startswith("W100/")], frontier),
                                   ("private-original", ex["private"], private)]:
        index = {(r["scheme"], r["param"], r["seed"]): r for r in rows}
        for scheme, param, cfg in points:
            for seed in range(100):
                jobs.append(dict(campaign=campaign, scheme=scheme, param=param, cfg=cfg,
                                 seed=seed, expected=index[(scheme, param, seed)]))
    for setting in SETTINGS:
        target, points = select(setting)
        selections[setting] = dict(target=target, points={})
        for family, point in points.items():
            _, label, scheme, cfg = point
            old = frozen[setting][family]
            if label != old["point"] or scheme != old["scheme"]:
                raise RuntimeError(f"Frozen selection mismatch: {setting}/{family}")
            selections[setting]["points"][family] = dict(label=label, scheme=scheme, config=asdict(cfg))
            for i, seed in enumerate(range(3000, 3100)):
                jobs.append(dict(campaign="headline-frozen", setting=setting, family=family,
                     scheme=scheme, param=label, cfg=cfg, seed=seed,
                     expected={frozen[setting]["metric"]: old["metric_per_seed"][i],
                               "symbols": old["ksym_per_seed"][i] * 1000}))
    if len(jobs) != 5200:
        raise RuntimeError(f"Unexpected preregistered job count: {len(jobs)}")
    return jobs, selections


def diagnostic_jobs():
    from gosc import Config
    b = Config().with_(log_private=True)
    settings = {"default": b, "W50": b.with_(symbols_per_slot=50), "snr-5": b.with_(snr_ref_db=-5)}
    return [dict(campaign="receiver-factorial", setting=setting, mode=mode, scheme="gosc", param=mode,
                 cfg=cfg, seed=seed) for setting, cfg in settings.items()
            for seed in range(4000, 4100) for mode in ("shared", "private", "position", "joint")]


def execute(run, stage, workers):
    if stage == "r4":
        manifest = json.loads((run / "r3_manifest.json").read_text())
        if manifest["status"] != "passed": raise RuntimeError("R3 is not passed")
        jobs, selections = r4_jobs(run)
    else:
        if json.loads((run / "r4/manifest.json").read_text())["status"] != "passed":
            raise RuntimeError("R4 must pass before diagnostics")
        if not (run / "diagnostic_contract_tests.json").is_file():
            raise RuntimeError("Diagnostic contract tests must pass")
        jobs, selections = diagnostic_jobs(), {}
    out = run / stage
    out.mkdir(exist_ok=False)
    configs = {config_key(j["cfg"]): asdict(j["cfg"]) for j in jobs}
    save(out / "configs.json", configs)
    save(out / "plan.json", dict(stage=stage, jobs=len(jobs), workers=workers,
         selections=selections, seeds=sorted(set(j["seed"] for j in jobs)),
         config_sha256=sha(out / "configs.json"), source_code_sha256=sha(__file__),
         intervention_sha256=sha(ROOT / "extensions/receiver_oracle.py") if stage != "r4" else None))
    start = time.perf_counter()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    failures, mismatches, completed = [], [], 0
    try:
        with (out / "raw.jsonl").open("x", encoding="utf-8") as f, mp.Pool(workers) as pool:
            for row in pool.imap_unordered(_job, jobs, chunksize=1):
                f.write(json.dumps(row, allow_nan=False) + "\n")
                completed += 1
                if row["status"] != "completed": failures.append(row)
                if row.get("reference_differences"): mismatches.append(row)
                if completed % 100 == 0 or completed == len(jobs):
                    f.flush()
                    print(f"{stage} {completed}/{len(jobs)} elapsed={time.perf_counter()-start:.1f}s failures={len(failures)} mismatches={len(mismatches)}", flush=True)
                if failures or mismatches:
                    f.flush()
                    raise RuntimeError("Fresh result differs or a mission failed; inspect retained raw record")
    except Exception:
        save(out / "failure.json", dict(status="failed", traceback=traceback.format_exc(),
             completed=completed, failures=failures, mismatches=mismatches))
        raise
    save(out / "manifest.json", dict(status="passed", stage=stage, git_commit=BASE,
         config_file="configs.json", config_sha256=sha(out / "configs.json"),
         raw_output_paths=[str(out / "raw.jsonl")], raw_sha256=sha(out / "raw.jsonl"),
         jobs_planned=len(jobs), completed=completed, failures=0, reference_mismatches=0,
         start_utc=started, elapsed_seconds=time.perf_counter()-start,
         numerical_tolerance=1e-9, protected_inputs=check_protected(run),
         notes="Diagnostic oracle states are privileged and synchronization cost is uncharged." if stage != "r4" else "Scoped baseline replication; full paper-wide resimulation not claimed."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["r4", "diagnostic"])
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--workers", type=int, default=4, choices=range(1, 5))
    args = ap.parse_args()
    if Path(args.run_id).name != args.run_id or args.run_id in (".", ".."):
        ap.error("Invalid run-id")
    run = ROOT / ".local/reproduction" / args.run_id
    os.environ["MPLCONFIGDIR"] = str(run / "mplconfig")
    execute(run, args.stage, args.workers)


if __name__ == "__main__":
    mp.freeze_support()
    main()
