"""Execute approved Receiver-CF v1 only: 8 development missions, <=128 branches.

Writes exclusively to a NEW .local/reproduction directory, never results/caches.
Requires clean committed sources, user approval record, and matching tested hashes.
"""
import os
for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"
os.environ["PYTHONUTF8"] = "1"

import argparse
import ctypes
import datetime as dt
from dataclasses import asdict
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import pickle
import platform
import subprocess
import sys
import time
import traceback

from extensions.counterfactual import (clone, communicate_taped, decide_observed,
    digest, features, future_streams, select_packet)
from gosc import Config, Simulation

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "research/reproduction/2026-10-16-mechanism/counterfactual_protocol_v1.md"
APPROVAL = ROOT / "research/reproduction/2026-10-16-cf-pilot/approval.json"
PROPOSAL = ROOT / "research/reproduction/2026-10-16-mechanism/pilot_proposal.json"
SOURCE_PATHS = ["extensions/counterfactual.py", "experiments_ext/run_receiver_cf.py",
                "experiments_ext/analyze_receiver_cf.py", "tests_ext/test_receiver_cf.py",
                "experiments_ext/review_receiver_mechanisms.py"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_default(x):
    if hasattr(x, "item"):
        return x.item()
    raise TypeError(type(x).__name__)


def save(path, value):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, default=json_default, allow_nan=False)


def append(path, value):
    # Per-worker/per-seed file, new parent directory, no concurrent writers.
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, default=json_default, allow_nan=False)+"\n")
        f.flush()


def peak_rss():
    """OS process lifetime peak working set, NOT incremental per-branch memory."""
    if os.name == "nt":
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (x, ctypes.c_size_t) for x in ("PeakWorkingSetSize", "WorkingSetSize",
                "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        stats = Counters()
        stats.cb = ctypes.sizeof(stats)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        fn = ctypes.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo
        fn.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
        if fn(kernel.GetCurrentProcess(), ctypes.byref(stats), stats.cb):
            return int(stats.PeakWorkingSetSize)
        return None
    import resource
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024))


def rng_hashes(sim):
    return {**{k: digest(getattr(sim, k)) for k in ("sense_rng", "chan_rng", "plan_rng", "dl_rng")},
            "decoder_rng": digest(sim.channel.rng)}


def branch(snapshot, tape, selected, seed, replicate, success, deadline):
    start, cpu = time.perf_counter(), time.process_time()
    s = clone(snapshot)
    row = {"point_id": f"{seed}:{s.t}", "seed": seed, "t": s.t,
           "packet_id": selected["packet_id"], "sender": selected["agent"],
           "kind": selected["kind"], "replicate": replicate, "success_branch": success,
           "status": "started", "snapshot_state_sha256": digest(snapshot)}
    try:
        if time.perf_counter() >= deadline:
            row["status"] = "timeout"
            return row
        current = communicate_taped(s, tape, selected["packet_id"], success, observe=True)
        row["current_slot"] = {k: current[k] for k in ("before_state_sha256", "after_state_sha256",
            "attempts", "done", "current_targets", "shadow_pre_motion_replan", "current_cost")}
        row["next_actual_decision"] = None
        row["next_decision_status"] = "terminal_at_intervention" if current["done"] else "pending"
        future_streams(s, seed, snapshot.t, selected["agent"], replicate)
        row["future_rng_initial_sha256"] = rng_hashes(s)
        row["future_seed_key"] = [seed, snapshot.t, selected["agent"], replicate]
        last_t, done = snapshot.t, current["done"]
        if not done:
            for t in range(snapshot.t+1, s.cfg.max_steps):
                if time.perf_counter() >= deadline:
                    row["status"] = "timeout"
                    break
                if t == snapshot.t+1:
                    row["next_actual_decision"] = decide_observed(s, t)
                    row["next_decision_status"] = "observed_after_motion_and_new_sensing"
                else:
                    s.phase_decide(t)
                last_t = t
                if s.phase_communicate(t):
                    done = True
                    break
        if row["status"] != "timeout":
            row["status"] = "ok"
        row.update(result=s.result(), last_simulated_slot=last_t, terminal=done,
                   trajectories=[a.trajectory for a in s.agents],
                   final_state_sha256=digest(s), future_rng_final_sha256=rng_hashes(s))
    except Exception:
        row.update(status="error", exception=traceback.format_exc())
    finally:
        row.update(wall_seconds=time.perf_counter()-start, cpu_seconds=time.process_time()-cpu,
                   process_lifetime_peak_rss_bytes=peak_rss())
    return row


def mission(args):
    seed, output, deadline = args
    out = Path(output) / f"seed-{seed}"
    out.mkdir(exist_ok=False)
    start, cpu, count = time.perf_counter(), time.process_time(), 0
    try:
        s = Simulation(Config(), "gosc", seed)
        s._start()
        ended = False
        for t in range(25):
            if ended:
                if t in (8, 24):
                    append(out/"availability.jsonl", {"seed": seed, "t": t, "status": "already_terminal"})
                continue
            if time.perf_counter() >= deadline:
                raise TimeoutError("Global pilot wall-clock cap reached during prefix")
            s.phase_decide(t)
            if t in (8, 24):
                snapshot = clone(s)
                taped = clone(snapshot)
                tape = communicate_taped(taped)
                direct = clone(snapshot)
                native_done = direct.phase_communicate(t)
                assert native_done == tape["done"] and digest(direct) == digest(taped)
                selected = select_packet(tape, seed, t)
                save(out/f"tape-{t}.json", tape)
                with (out/f"snapshot-{t}.pkl").open("xb") as f:
                    pickle.dump(snapshot, f, protocol=5)
                save(out/f"checkpoint-{t}.json", {"seed": seed, "t": t,
                    "snapshot_state_sha256": digest(snapshot), "pickle_sha256": sha(out/f"snapshot-{t}.pkl"),
                    "trusted_self_generated_pickle_only": True, "tape_sha256": sha(out/f"tape-{t}.json"),
                    "native_replay_matches": True})
                append(out/"availability.jsonl", {"seed": seed, "t": t,
                    "status": "selected" if selected else "no_selected_E_or_I",
                    "selected_packet_id": None if selected is None else selected["packet_id"],
                    "selected_kind": None if selected is None else selected["kind"],
                    "available_attempts": [{"packet_id": x["packet_id"], "kind": x["kind"],
                                            "agent": x["agent"]} for x in tape["attempts"]]})
                if selected:
                    append(out/"features.jsonl", features(snapshot, selected, seed))
                    for rr in range(4):
                        for success in (False, True):
                            row = branch(snapshot, tape, selected, seed, rr, success, deadline)
                            append(out/"branches.jsonl", row)
                            count += 1
                            if row["status"] != "ok":
                                raise RuntimeError(f"Branch status {row['status']}: {row.get('exception', '')}")
            ended = bool(s.phase_communicate(t))
        summary = {"seed": seed, "status": "ok", "branches": count,
                   "prefix_last_slot": min(s.t, 24), "prefix_terminal": ended,
                   "prefix_state_sha256": digest(s)}
    except Exception:
        summary = {"seed": seed, "status": "error_or_timeout", "branches": count,
                   "exception": traceback.format_exc()}
    summary.update(wall_seconds=time.perf_counter()-start, cpu_seconds=time.process_time()-cpu,
                   process_lifetime_peak_rss_bytes=peak_rss())
    save(out/"completion.json", summary)
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, required=True, help="NEW directory under .local/reproduction")
    ap.add_argument("--gate-file", type=Path, required=True, help="Actual passing test record with tested source hashes")
    args = ap.parse_args()
    out = args.output_dir.resolve()
    if not out.is_relative_to((ROOT/".local/reproduction").resolve()) or out == (ROOT/".local/reproduction").resolve():
        raise SystemExit("Output must be a new child of .local/reproduction")
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).strip()
    if status:
        raise SystemExit("Commit tested implementation before execution; dirty checkout rejected")
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    assert approval["approved"] and approval["protocol_sha256"] == sha(PROTOCOL)
    proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    assert digest(asdict(Config())) == digest(proposal["config"])
    gate = json.loads(args.gate_file.read_text(encoding="utf-8"))
    assert gate["passed"] and gate["contract_test_count"] >= 10
    hashes = {p: sha(ROOT/p) for p in SOURCE_PATHS}
    assert hashes == gate["source_sha256"], "Source changed since tests"
    protected = json.loads((ROOT/"research/reproduction/2026-10-16-mechanism/input_hashes.json").read_text(encoding="utf-8"))["protected_checkout_inputs"]
    assert all(sha(ROOT/p) == h for p, h in protected.items()), "Protected upstream inputs changed"
    out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    deadline = start+900
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    save(out/"configs.json", asdict(Config()))
    save(out/"experiment_manifest.json", {"experiment_id": out.name,
        "date": dt.datetime.now(dt.timezone.utc).isoformat(), "client_date": "2026-10-16",
        "git_commit": commit, "working_tree_dirty": False, "scheme": "native_gosc_offline_decoder_intervention",
        "config_file": str(out/"configs.json"), "config_sha256": sha(out/"configs.json"),
        "python_version": sys.version, "dependencies_lock": "requirements-windows.lock.txt",
        "dependencies_lock_sha256": sha(ROOT/"requirements-windows.lock.txt"), "os": platform.platform(),
        "hardware": "research/logs/environment-2026-10-12/hardware.json", "agent_models": ["Planner"],
        "llm_cache_mode": "not_used", "seeds": list(range(5000,5008)),
        "train_calib_eval_split": "development diagnostic only; no training; not final evaluation",
        "wireless_channel": "native Rayleigh/outage/statistical CSI/ideal DL/orthogonal",
        "bandwidth_or_channel_budget": "100 UL channel uses/agent/slot", "commands": [sys.argv],
        "raw_output_paths": ["seed-*/branches.jsonl", "seed-*/features.jsonl", "seed-*/availability.jsonl"],
        "logs": ["execution.log", "seed-*/completion.json"], "status": "planned_immutable_start_record",
        "workers": 2, "numeric_threads_per_worker": 1, "wall_cap_seconds": 900, "max_branches":128,
        "protocol_sha256": sha(PROTOCOL), "approval_sha256": sha(APPROVAL), "gate_sha256":sha(args.gate_file),
        "source_sha256": hashes, "protected_inputs_sha256": protected,
        "notes": "Native sequential stream coupling; not cell aligned after trajectories diverge. Offline labels excluded from scheduler."})
    completed, failure, timed_out = [], None, False
    pool = mp.get_context("spawn").Pool(2)
    pending = {seed: pool.apply_async(mission, ((seed, str(out), deadline),)) for seed in range(5000,5008)}
    try:
        while pending:
            if time.perf_counter() >= deadline:
                timed_out = True
                break
            for seed, item in list(pending.items()):
                if item.ready():
                    answer = item.get()
                    completed.append(answer)
                    del pending[seed]
                    print(json.dumps(answer), flush=True)
                    if answer["status"] != "ok":
                        failure = answer
                        break
            if failure:
                break
            time.sleep(0.2)
    finally:
        if pending or failure or timed_out:
            pool.terminate()
        else:
            pool.close()
        pool.join()
    save(out/"execution_completion.json", {"status": "complete" if not pending and not failure and not timed_out else "partial_or_failed",
        "elapsed_wall_seconds": time.perf_counter()-start, "completed_workers": completed,
        "unfinished_seeds": list(pending), "timed_out": timed_out, "failure": failure,
        "parent_process_lifetime_peak_rss_bytes": peak_rss(), "original_inputs_unchanged": all(sha(ROOT/p)==h for p,h in protected.items()),
        "explicit_no_new_data_extension": True})
    if pending or failure or timed_out:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
