"""Reproduce the original baseline without writing to its result directory.

Run --help before execution. All completed stage manifests are exclusive-create.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
BASE = "387b49389385b51c275dc5a22ec1672087edda1d"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").strip()


def controlled_env(workspace):
    env = os.environ.copy()
    env.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg",
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONPATH=str(workspace), MPLCONFIGDIR=str(workspace / ".mplconfig"))
    return env


def run_logged(command, cwd, log, timeout=None):
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    t = time.perf_counter()
    with Path(log).open("x", encoding="utf-8") as f:
        r = subprocess.run(command, cwd=cwd, env=controlled_env(Path(cwd)),
                           stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
    record = dict(command=command, cwd=str(cwd), log=str(log), start_utc=started,
                  elapsed_seconds=time.perf_counter() - t, exit_code=r.returncode)
    print(json.dumps(record), flush=True)
    if r.returncode:
        raise RuntimeError(f"Command failed; inspect {log}")
    return record


def prepare(run):
    run.mkdir(parents=True, exist_ok=False)
    workspace = run / "upstream_workspace"
    workspace.mkdir()
    archive = subprocess.check_output(["git", "archive", BASE], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(workspace, filter="data")
    protected = {}
    for folder in ("gosc", "experiments", "tests", "results"):
        for p in (ROOT / folder).rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                protected[p.relative_to(ROOT).as_posix()] = sha(p)
    save(run / "protected_checkout_inputs.json", protected)
    save(run / "run_manifest.json", {
        "experiment_id": run.name, "date": "2026-10-15", "git_commit": git("rev-parse", "HEAD"),
        "upstream_commit": BASE, "working_tree_dirty": bool(git("status", "--porcelain")),
        "python_version": sys.version, "dependencies_lock": "requirements-windows.lock.txt",
        "dependencies_lock_sha256": sha(ROOT / "requirements-windows.lock.txt"),
        "hardware_manifest": "research/logs/environment-2026-10-12/hardware.json",
        "orchestrator_sha256": sha(__file__), "agent_models": [], "llm_cache_mode": "not_run",
        "protocol": "research/reproduction/repro_protocol.md", "status": "prepared",
        "notes": ["Pure Planner; no live LLM or model downloads.", "Completed stage manifests are stored separately."]})
    for name in ("noise", "overhead", "shared"):
        source = workspace / "results" / (name + ".jsonl.gz")
        target = source.with_suffix("")
        with gzip.open(source, "rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
    print("Prepared isolated baseline", workspace, flush=True)


def check_protected(run):
    before = json.loads((run / "protected_checkout_inputs.json").read_text())
    differences = [p for p, h in before.items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    if differences:
        raise RuntimeError(f"Original input changed: {differences}")
    return {"checked": len(before), "differences": []}


def r2(run):
    workspace = run / "upstream_workspace"
    logs = run / "r2_logs"
    logs.mkdir(exist_ok=False)
    commands = []
    try:
        for label, args in [("plot", ["-m", "experiments.plot"]),
                            ("plot_revision", ["-m", "experiments.plot_revision"]),
                            ("belief_table", ["-m", "experiments.run_belief_divergence", "--table"]),
                            ("plot_realistic", ["-m", "experiments.plot_realistic"])]:
            commands.append(run_logged([sys.executable, "-B", "-X", "utf8", *args], workspace,
                                       logs / (label + ".log")))
        expected = ["fig_rescue.pdf", "fig_noise.pdf", "fig_snr_pair.pdf", "fig_shared_col.pdf",
                    "table_validation.tex", "table_default.tex", "table_values.tex", "table_noise.tex",
                    "table_ablation.tex", "table_overhead.tex", "table_cost.tex", "table_shared.tex",
                    "table_llm_extended.tex", "table_frozen.tex", "table_private.tex"]
        missing = [n for n in expected if not (workspace / "figures" / n).is_file()]
        skipped = {p.name: [line for line in p.read_text(encoding="utf-8").splitlines()
                            if line.lower().startswith(("skip ", "skipping "))] for p in logs.glob("*.log")}
        skipped = {k: v for k, v in skipped.items() if v}
        if missing or skipped:
            raise RuntimeError(f"Missing outputs={missing}; skipped branches={skipped}")
        outputs = {p.name: sha(p) for p in (workspace / "figures").iterdir() if p.is_file()}
        save(run / "r2_manifest.json", dict(status="generated_pending_paper_audit", stage="R2",
             commands=commands, expected_outputs=expected, outputs=outputs,
             protected_inputs=check_protected(run), llm_evaluation="author-saved table analysis only"))
        print("R2 outputs generated", len(outputs), flush=True)
    except Exception:
        save(run / "r2_failure.json", dict(status="failed", commands=commands, traceback=traceback.format_exc()))
        raise


def r3(run):
    if not (run / "r2_audit.json").is_file():
        raise RuntimeError("Complete the R2 paper/number audit before R3")
    from dataclasses import asdict
    from gosc import Config, run_episode
    cfg = Config()
    t = time.perf_counter()
    out = run_episode(cfg, "gosc", 0)
    elapsed = time.perf_counter() - t
    source = json.loads((run / "upstream_workspace/results/default.json").read_text())["rows"]
    old = next(r for r in source if r["scheme"] == "gosc" and r["seed"] == 0)
    differences = []
    for k, v in old.items():
        if k in ("scheme", "seed", "param"):
            continue
        if k in out and v is not None and isinstance(v, (float, int)):
            if abs(out[k] - v) > 1e-9:
                differences.append(k)
        elif k in out and out[k] != v:
            differences.append(k)
    if (out["completion_time"], out["symbols"], out["bits"]) != (122, 13304, 17186):
        differences.append("reference_triple")
    save(run / "r3_output.json", dict(config=asdict(cfg), scheme="gosc", seed=0,
                                     elapsed_seconds=elapsed, output=out))
    save(run / "r3_manifest.json", dict(status="passed" if not differences else "failed", stage="R3",
         git_commit=git("rev-parse", "HEAD"), baseline_commit=BASE, config_sha256=sha(ROOT / "gosc/config.py"),
         seeds=[0], scheme="gosc", differences=differences, elapsed_seconds=elapsed,
         output_sha256=sha(run / "r3_output.json"), protected_inputs=check_protected(run)))
    print("R3", out["completion_time"], out["symbols"], out["bits"], "seconds", elapsed, "diff", differences, flush=True)
    if differences:
        raise RuntimeError("Fresh mission differs from baseline")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["prepare", "r2", "r3", "check"])
    ap.add_argument("--run-id", required=True, help="New run directory under ignored .local/reproduction")
    args = ap.parse_args()
    if Path(args.run_id).name != args.run_id or args.run_id in (".", ".."):
        ap.error("run-id must be a single directory name")
    run = ROOT / ".local/reproduction" / args.run_id
    if args.stage == "prepare": prepare(run)
    elif args.stage == "r2": r2(run)
    elif args.stage == "r3": r3(run)
    else: print(check_protected(run))


if __name__ == "__main__":
    main()
