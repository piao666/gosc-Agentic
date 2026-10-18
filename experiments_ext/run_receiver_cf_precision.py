"""Approved fixed-checkpoint extension only: replicas4..31, <=784 branches.

No new worlds, sampling, estimator, or upstream writes. Requires verified local
self-generated snapshots and original implementation/environment hashes.
"""
import os
for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"
os.environ["PYTHONUTF8"] = "1"

import argparse
import csv
import datetime as dt
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
from pathlib import Path
import pickle
import platform
import subprocess
import sys
import time
import traceback

from dataclasses import asdict
from experiments_ext.run_receiver_cf import ROOT, append, branch, peak_rss, save, sha
from extensions.counterfactual import clone, communicate_taped, digest, features, select_packet

PRIOR = ROOT/".local/reproduction/2026-10-16-cf-pilot-v1"
PRIOR_DOC = ROOT/"research/reproduction/2026-10-16-cf-pilot"
DOC = ROOT/"research/reproduction/2026-10-18-cf-precision"
SOURCE_PATHS = ["experiments_ext/run_receiver_cf_precision.py",
                "experiments_ext/analyze_receiver_cf_precision.py",
                "tests_ext/test_receiver_cf_precision.py"]
NEW_REPLICATES = tuple(range(4,32))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verified_unpickle(path, expected_sha256):
    # Read once, hash those exact bytes BEFORE executing any pickle deserialization.
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("Snapshot hash mismatch; pickle not loaded")
    return pickle.loads(data)


def normalized_files(index):
    files={k.replace("\\", "/"):v for k,v in index["files"].items()}
    if len(files)!=len(index["files"]):
        raise ValueError("Colliding normalized artifact paths")
    return files


def validate_prior():
    index = read_json(PRIOR_DOC/"raw_artifact_index.json")
    index["files"]=normalized_files(index)
    for rel, meta in index["files"].items():
        path = (PRIOR/rel).resolve()
        if not path.is_relative_to(PRIOR.resolve()) or sha(path) != meta["sha256"]:
            raise ValueError(f"Prior artifact mismatch: {rel}")
    manifest = read_json(PRIOR/"experiment_manifest.json")
    if sys.version != manifest["python_version"] or sha(ROOT/"requirements-windows.lock.txt") != manifest["dependencies_lock_sha256"]:
        raise ValueError("Python/lock mismatch with original snapshots")
    installed = {}
    for line in (ROOT/"requirements-windows.lock.txt").read_text(encoding="utf-8").splitlines():
        if "==" in line and not line.startswith("#"):
            name, version = line.split("==")
            installed[name] = importlib.metadata.version(name)
            if installed[name] != version:
                raise ValueError(f"Installed dependency mismatch: {name}")
    for p, h in {**manifest["source_sha256"], **manifest["protected_inputs_sha256"]}.items():
        if sha(ROOT/p) != h:
            raise ValueError(f"Original source/input mismatch: {p}")
    old_features = [json.loads(l) for p in sorted(PRIOR.glob("seed-*/features.jsonl"))
                    for l in p.read_text(encoding="utf-8").splitlines()]
    published = list(csv.DictReader((PRIOR_DOC/"per_point.csv").open(encoding="utf-8")))
    ids = {(r["point_id"], r["packet_id"]) for r in old_features}
    if len(old_features) != 14 or len(ids) != 14 or ids != {(r["point_id"],r["packet_id"]) for r in published}:
        raise ValueError("Fixed14 point/packet identities changed")
    plan=[]
    for row in sorted(old_features, key=lambda r:(r["seed"],r["t"])):
        seed,t=row["seed"],row["t"]
        if seed not in range(5000,5008) or t not in (8,24):
            raise ValueError("Unexpected fixed point")
        folder=f"seed-{seed}"
        plan.append({"feature":row, "snapshot_rel":f"{folder}/snapshot-{t}.pkl",
                     "snapshot_sha256":index["files"][f"{folder}/snapshot-{t}.pkl"]["sha256"],
                     "tape_rel":f"{folder}/tape-{t}.json",
                     "tape_sha256":index["files"][f"{folder}/tape-{t}.json"]["sha256"],
                     "checkpoint":read_json(PRIOR/folder/f"checkpoint-{t}.json")})
    return plan,manifest,installed,index


def load_point(point):
    f=point["feature"]
    path=(PRIOR/point["snapshot_rel"]).resolve()
    tape_path=(PRIOR/point["tape_rel"]).resolve()
    if not path.is_relative_to(PRIOR.resolve()) or not tape_path.is_relative_to(PRIOR.resolve()):
        raise ValueError("Snapshot path outside trusted original run")
    if sha(tape_path)!=point["tape_sha256"]:
        raise ValueError("Tape hash mismatch")
    sim=verified_unpickle(path,point["snapshot_sha256"])
    tape=read_json(tape_path)
    assert sim.t==f["t"] and sim.channel is sim.scheme.channel
    assert digest(asdict(sim.cfg))==digest(read_json(PRIOR/"configs.json"))
    assert digest(sim)==point["checkpoint"]["snapshot_state_sha256"]==tape["before_state_sha256"]
    selected=select_packet(tape,f["seed"],f["t"])
    assert selected is not None and selected["packet_id"]==f["packet_id"]
    assert features(sim,selected,f["seed"])==f
    # One native SLOT replay, not a new mission or continuation repetition.
    replay=communicate_taped(clone(sim),expected=tape)
    assert replay["after_state_sha256"]==tape["after_state_sha256"]
    return sim,tape,selected


def extend_point(args):
    point,output,deadline=args
    f=point["feature"];out=Path(output)/f"point-{f['seed']}-{f['t']}"
    out.mkdir(exist_ok=False)
    start,cpu,count=time.perf_counter(),time.process_time(),0
    try:
        sim,tape,selected=load_point(point)
        save(out/"source.json",point)
        for rr in NEW_REPLICATES:
            for success in (False,True):
                row=branch(sim,tape,selected,f["seed"],rr,success,deadline)
                append(out/"branches.jsonl",row)
                count+=1
                if row["status"]!="ok":
                    raise RuntimeError(f"Branch {row['status']}: {row.get('exception','')}")
        result={"point_id":f["point_id"],"status":"ok","new_branches":count}
    except Exception:
        result={"point_id":f["point_id"],"status":"error_or_timeout","new_branches":count,
                "exception":traceback.format_exc()}
    result.update(wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,
                  process_lifetime_peak_rss_bytes=peak_rss())
    save(out/"completion.json",result)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--gate-file",type=Path,required=True)
    args=ap.parse_args();out=args.output_dir.resolve()
    local=(ROOT/".local/reproduction").resolve()
    if not out.is_relative_to(local) or out==local:
        raise SystemExit("Use a NEW child of .local/reproduction")
    if subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True).strip():
        raise SystemExit("Commit tested sources first; dirty checkout rejected")
    approval=read_json(DOC/"approval.json")
    assert approval["approved"] and approval["proposal_sha256"]==sha(PRIOR_DOC/"next_stage_plan.md")
    gate=read_json(args.gate_file)
    hashes={p:sha(ROOT/p) for p in SOURCE_PATHS}
    assert gate["passed"] and gate["source_sha256"]==hashes
    plan,prior_manifest,installed,index=validate_prior()
    out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();deadline=start+900
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    save(out/"fixed_points.json",plan)
    save(out/"experiment_manifest.json",{
        "experiment_id":out.name,"date":dt.datetime.now(dt.timezone.utc).isoformat(),"client_date":"2026-10-18",
        "git_commit":commit,"working_tree_dirty":False,"scheme":"native_gosc_fixed_checkpoint_MC_extension",
        "config_file":str(PRIOR/"configs.json"),"config_sha256":sha(PRIOR/"configs.json"),
        "python_version":sys.version,"dependencies_lock":"requirements-windows.lock.txt",
        "dependencies_lock_sha256":sha(ROOT/"requirements-windows.lock.txt"),"installed_versions":installed,
        "os":platform.platform(),"hardware":"research/logs/environment-2026-10-12/hardware.json",
        "agent_models":["Planner"],"llm_cache_mode":"not_used","seeds":list(range(5000,5008)),
        "train_calib_eval_split":"same8 exposed development worlds, no training/no final evaluation",
        "wireless_channel":prior_manifest["wireless_channel"],"bandwidth_or_channel_budget":prior_manifest["bandwidth_or_channel_budget"],
        "commands":[sys.argv],"raw_output_paths":["point-*/branches.jsonl"],"logs":["point-*/completion.json"],
        "status":"immutable_start_record","source_sha256":hashes,"prior_source_sha256":prior_manifest["source_sha256"],
        "prior_manifest_sha256":sha(PRIOR/"experiment_manifest.json"),"prior_raw_index_sha256":sha(PRIOR_DOC/"raw_artifact_index.json"),
        "prior_run":str(PRIOR),"prior_execution_commit":prior_manifest["git_commit"],
        "prior_protected_inputs":prior_manifest["protected_inputs_sha256"],"prior_files":index["files"],
        "approval_sha256":sha(DOC/"approval.json"),"gate_sha256":sha(args.gate_file),
        "fixed_points_sha256":sha(out/"fixed_points.json"),"new_replicates":list(NEW_REPLICATES),
        "retained_replicates":[0,1,2,3],"workers":2,"numeric_threads_per_worker":1,
        "max_new_branches":784,"wall_cap_seconds":900,"new_worlds":0,"notes":"No resampling; native sequential stream coupling."})
    completed,pending,failure,timed_out=[],{},None,False
    pool=mp.get_context("spawn").Pool(2)
    for p in plan:
        pending[p["feature"]["point_id"]]=pool.apply_async(extend_point,((p,str(out),deadline),))
    progress_at=start
    try:
        while pending:
            if time.perf_counter()>=deadline:
                timed_out=True;break
            for point,item in list(pending.items()):
                if item.ready():
                    ans=item.get();completed.append(ans);del pending[point]
                    print(json.dumps(ans),flush=True)
                    if ans["status"]!="ok":failure=ans;break
            if failure:break
            if time.perf_counter()-progress_at>=30:
                n=sum(sum(1 for _ in p.open(encoding="utf-8")) for p in out.glob("point-*/branches.jsonl"))
                print(json.dumps({"progress_branch_rows":n,"completed_points":len(completed)}),flush=True)
                progress_at=time.perf_counter()
            time.sleep(.2)
    finally:
        if pending or failure or timed_out:pool.terminate()
        else:pool.close()
        pool.join()
    unchanged=all(sha(PRIOR/p)==m["sha256"] for p,m in index["files"].items())
    save(out/"execution_completion.json",{"status":"complete" if not pending and not failure and not timed_out and unchanged else "partial_or_failed",
         "elapsed_wall_seconds":time.perf_counter()-start,"completed_points":completed,"unfinished_points":list(pending),
         "failure":failure,"timed_out":timed_out,"prior_indexed_artifacts_unchanged":unchanged,
         "parent_process_lifetime_peak_rss_bytes":peak_rss()})
    if pending or failure or timed_out or not unchanged:raise SystemExit(1)


if __name__=="__main__":
    main()
