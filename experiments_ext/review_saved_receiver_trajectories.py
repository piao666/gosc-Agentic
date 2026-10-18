"""Review saved receiver-CF logs only. Never import or run the simulator.

Outputs a NEW local directory; input JSON/JSONL/CSV is read-only. All 14 points
and 448 paired repetitions are retained. Post-treatment strata are descriptive.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "research/reproduction/2026-10-18-cf-precision"
REVIEW_SOURCE = "experiments_ext/review_saved_receiver_trajectories.py"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False)


def first_difference(a, b):
    """Only compare actual overlapping samples; a longer tail is NOT divergence."""
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)


def movement_divergence(a, b, t):
    # trajectory[0] = initial position; index k = after motion of slot k-1.
    # Same preselected current target => identical motion at intervention slot t.
    assert a[:t+2] == b[:t+2], "Pre-intervention/current motion changed"
    first = first_difference(a, b)
    assert first is None or first >= t+2
    return {"first_position_index": first,
            "first_motion_slot": None if first is None else first-1,
            "slots_after_intervention": None if first is None else first-1-t,
            "overlap_positions": min(len(a), len(b)),
            "failure_positions": len(a), "success_positions": len(b),
            "unequal_recorded_lengths": len(a) != len(b)}


def changed_agents(a, b, sender):
    if a is None or b is None:
        return None
    aa = {x["agent"]: x for x in a}; bb = {x["agent"]: x for x in b}
    assert len(aa) == len(a) and len(bb) == len(b) and aa.keys() == bb.keys()
    return [j for j in sorted(aa) if j != sender and aa[j]["target"] != bb[j]["target"]]


def hold_context(row, tolerance=1e-9):
    """Observed context compatible with a hysteresis hold; no causal ablation."""
    old = row["old_target"]
    if old is None or row["distance_to_old_target"] == 0:
        return False
    best, previous = row["score_best_without_tie_jitter"], row["score_old_without_tie_jitter"]
    margin = row["hysteresis_margin_without_tie_jitter"]
    if margin < -tolerance:
        assert row["target"] == old, "Native keep-target rule contradicted away from tie tolerance"
    return bool(row["target"] == old and best > previous+tolerance and margin < -tolerance)


def assert_attempt_cost_equal(failure_cost, success_cost):
    # Delivery and broadcast bytes are outcomes of decode; they need not match.
    assert all(failure_cost[k] == success_cost[k] for k in ("bits", "symbols"))


def pair_summary(failure, success, feature):
    f, s, t, sender = failure, success, feature["t"], feature["sender"]
    assert f["status"] == s["status"] == "ok"
    assert f["snapshot_state_sha256"] == s["snapshot_state_sha256"]
    assert f["future_seed_key"] == s["future_seed_key"]
    assert f["future_rng_initial_sha256"] == s["future_rng_initial_sha256"]
    assert_attempt_cost_equal(f["current_slot"]["current_cost"],s["current_slot"]["current_cost"])
    assert f["current_slot"]["current_targets"] == s["current_slot"]["current_targets"]
    assert len(f["current_slot"]["attempts"]) == len(s["current_slot"]["attempts"])
    intervention_count = 0
    for a, b in zip(f["current_slot"]["attempts"], s["current_slot"]["attempts"]):
        if a["packet_id"] != feature["packet_id"]:
            assert a == b
        else:
            assert not a["effective_decode"] and b["effective_decode"]
            assert {k:v for k,v in a.items() if k != "effective_decode"} == {k:v for k,v in b.items() if k != "effective_decode"}
            intervention_count += 1
    assert intervention_count == 1
    actual = changed_agents(f["next_actual_decision"], s["next_actual_decision"], sender)
    shadow = changed_agents(f["current_slot"]["shadow_pre_motion_replan"], s["current_slot"]["shadow_pre_motion_replan"], sender)
    assert actual is not None, "This approved dataset should have real next decisions; do not silently drop missing pairs"
    assert len(f["trajectories"]) == len(s["trajectories"])
    paths = [dict(agent=j, **movement_divergence(a,b,t)) for j,(a,b) in enumerate(zip(f["trajectories"],s["trajectories"]))]
    next_rows = {"failure": f["next_actual_decision"], "success": s["next_actual_decision"]}
    hold = {k:[r["agent"] for r in rs if r["agent"] != sender and hold_context(r)] for k,rs in next_rows.items()}
    for label, r in (("failure",f),("success",s)):
        # In the present completed search setting terminal slot skips motion.
        assert r["result"]["completed"] and r["terminal"]
        assert all(len(x) == r["result"]["completion_time"] for x in r["trajectories"])
        assert all(tuple(x["position"]) == tuple(r["trajectories"][x["agent"]][t+1]) for x in r["next_actual_decision"])
    curve_first = first_difference(f["result"]["curve"],s["result"]["curve"])
    assert curve_first is None or curve_first >= t
    receiver_paths = [p for p in paths if p["agent"] != sender]
    first_receiver = min((p["first_motion_slot"] for p in receiver_paths if p["first_motion_slot"] is not None),default=None)
    fr, sr = f["result"],s["result"]
    return {"point_id":feature["point_id"],"seed":feature["seed"],"t":t,"sender":sender,"kind":feature["kind"],
        "replicate":f["replicate"],"receiver_target_changes":len(actual),"receiver_changed_agents":actual,
        "shadow_target_changes":len(shadow),"shadow_changed_agents":shadow,
        "shadow_and_actual_changed_sets_differ":actual != shadow,
        "first_receiver_motion_divergence_slot":first_receiver,
        "receiver_path_diverged":first_receiver is not None,
        "first_found_count_divergence_slot":curve_first,
        "delta_T":fr["completion_time"]-sr["completion_time"],
        "failure_completion":fr["completion_time"],"success_completion":sr["completion_time"],
        "delta_false_declarations_success_minus_failure":sr["false_declarations"]-fr["false_declarations"],
        "delta_UL_uses_success_minus_failure":sr["symbols"]-fr["symbols"],
        "delta_DL_uses_success_minus_failure":sr["dl_symbols"]-fr["dl_symbols"],
        "delta_total_uses_success_minus_failure":sr["symbols"]+sr["dl_symbols"]-fr["symbols"]-fr["dl_symbols"],
        "delta_bits_success_minus_failure":sr["bits"]-fr["bits"],
        "hysteresis_compatible_hold_receivers":hold,
        "trajectory_alignment":paths,
        "future_rng_final_equal_by_stream":{k:f["future_rng_final_sha256"][k] == s["future_rng_final_sha256"][k] for k in f["future_rng_final_sha256"]}}


def choose_cases(points, pairs):
    selected={}
    positive=sorted((p for p in points if p["delta_T_mean"] > 0),key=lambda p:(-p["delta_T_mean"],p["point_id"]))
    negative=sorted((p for p in points if p["delta_T_mean"] < 0),key=lambda p:(p["delta_T_mean"],p["point_id"]))
    nearest=sorted(points,key=lambda p:(abs(p["delta_T_mean"]),p["point_id"]))
    for label, pool in (("positive",positive),("negative",negative),("near_zero",nearest)):
        if not pool:
            selected[label]=None;continue
        point=pool[0]
        pair=min((r for r in pairs if r["point_id"] == point["point_id"]),key=lambda r:(abs(r["delta_T"]-point["delta_T_mean"]),r["replicate"]))
        selected[label]={"point":point,"illustrative_pair":pair}
    return selected


def export_csv(path, rows):
    fields=sorted(set().union(*(r.keys() for r in rows)))
    with path.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        w.writerows({k:json.dumps(v,sort_keys=True) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir",type=Path,required=True,help="Completed precision raw root, read-only")
    ap.add_argument("--output-dir",type=Path,required=True,help="NEW local review directory")
    args=ap.parse_args();start=time.perf_counter();cpu=time.process_time()
    raw=args.run_dir.resolve();out=args.output_dir.resolve()
    assert out.is_relative_to((ROOT/".local/reproduction").resolve()) and out != (ROOT/".local/reproduction").resolve()
    assert not out.exists() and out != raw
    m=read(raw/"experiment_manifest.json");prior=Path(m["prior_run"])
    assert read(raw/"execution_completion.json")["status"] == "complete"
    verified={}
    def verify(path, expected):
        assert sha(path) == expected, str(path)
        verified[str(path)] = expected
    for p,v in m["prior_files"].items():verify(prior/p,v["sha256"])
    for p,h in {**m["prior_protected_inputs"],**m["prior_source_sha256"],**m["source_sha256"]}.items():verify(ROOT/p,h)
    for p,v in read(ARCHIVE/"artifact_hashes.json")["files"].items():verify(ROOT/p,v["sha256"])
    index=read(ARCHIVE/"raw_artifact_index.json")
    assert Path(index["raw_root"]).resolve() == raw
    for p,v in index["files"].items():verify(raw/p,v["sha256"])
    source_paths=[REVIEW_SOURCE,"tests_ext/test_saved_receiver_trajectories.py"]
    source_hashes={p:sha(ROOT/p) for p in source_paths}
    base=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(["git","status","--porcelain"],cwd=ROOT,text=True).strip())
    # Read no pickle; only append-only JSON lines and static feature JSON.
    loaded=[]
    for p in sorted(prior.glob("seed-*/branches.jsonl"))+sorted(raw.glob("point-*/branches.jsonl")):
        loaded.extend(json.loads(line) for line in p.read_text(encoding="utf-8").splitlines())
    features=[p["feature"] for p in read(raw/"fixed_points.json")]
    assert len(loaded) == 896 and len(features) == 14
    lookup={(r["point_id"],r["replicate"],r["success_branch"]):r for r in loaded}
    assert len(lookup) == 896
    pairs=[];points=[]
    with (ARCHIVE/"per_point_by_R.csv").open(encoding="utf-8") as f:old_points={r["point_id"]:r for r in csv.DictReader(f) if r["R"] == "32"}
    for f in features:
        rows=[]
        for rep in range(32):
            a,b=(lookup[(f["point_id"],rep,v)] for v in (False,True))
            assert a["packet_id"] == b["packet_id"] == f["packet_id"]
            rows.append(pair_summary(a,b,f))
        pairs.extend(rows)
        differences=[r["delta_T"] for r in rows]
        mean=st.mean(differences);se=st.stdev(differences)/math.sqrt(32)
        assert math.isclose(mean,float(old_points[f["point_id"]]["delta_T"]),abs_tol=1e-12)
        assert math.isclose(se,float(old_points[f["point_id"]]["mc_se_delta_T"]),abs_tol=1e-12)
        point={**f,"pairs":32,"delta_T_mean":mean,"delta_T_MC_SE":se,
            "delta_T_median":st.median(differences),"delta_T_min":min(differences),"delta_T_max":max(differences),
            "pair_positive":sum(x>0 for x in differences),"pair_zero":sum(x==0 for x in differences),"pair_negative":sum(x<0 for x in differences),
            "actual_target_change_pairs":sum(r["receiver_target_changes"]>0 for r in rows),
            "mean_changed_receivers":st.mean(r["receiver_target_changes"] for r in rows),
            "shadow_target_change_pairs":sum(r["shadow_target_changes"]>0 for r in rows),
            "shadow_actual_changed_set_disagreement_pairs":sum(r["shadow_and_actual_changed_sets_differ"] for r in rows),
            "receiver_path_divergence_pairs":sum(r["receiver_path_diverged"] for r in rows),
            "no_next_target_change_but_receiver_path_diverges":sum(r["receiver_target_changes"]==0 and r["receiver_path_diverged"] for r in rows),
            "no_next_target_change_but_nonzero_delta_T":sum(r["receiver_target_changes"]==0 and r["delta_T"]!=0 for r in rows),
            "delta_total_uses_mean_success_minus_failure":st.mean(r["delta_total_uses_success_minus_failure"] for r in rows),
            "false_declarations_failure_sum":sum(lookup[(f["point_id"],rep,False)]["result"]["false_declarations"] for rep in range(32)),
            "false_declarations_success_sum":sum(lookup[(f["point_id"],rep,True)]["result"]["false_declarations"] for rep in range(32)),
            "first_receiver_motion_divergence_slot_min":min((r["first_receiver_motion_divergence_slot"] for r in rows if r["receiver_path_diverged"]),default=None),
            "first_receiver_motion_divergence_slot_max":max((r["first_receiver_motion_divergence_slot"] for r in rows if r["receiver_path_diverged"]),default=None)}
        points.append(point)
    out.mkdir(parents=True,exist_ok=False)
    write(out/"experiment_manifest.json",{"experiment_id":out.name,"date":dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_commit":base,"working_tree_dirty":dirty,"review_source_sha256":source_hashes,"commands":[sys.argv],
        "analysis_kind":"saved_logs_only_no_simulation_no_pickle","seeds":m["seeds"],"independent_worlds":8,"fixed_points":14,
        "paired_repetitions":448,"new_rollouts":0,"agent_models":["Planner saved outputs"],"llm_cache_mode":"not_used",
        "python_version":sys.version,"dependencies_lock_sha256":sha(ROOT/"requirements-windows.lock.txt"),
        "original_execution_commit":m["git_commit"],"prior_execution_commit":m["prior_execution_commit"],
        "input_hashes":verified,"status":"immutable_analysis_start_record",
        "notes":"All inputs exposed development data. Cases post hoc. No causal mediator or online-feature validation."})
    export_csv(out/"point_matrix.csv",points);export_csv(out/"paired_chain.csv",pairs)
    cases=choose_cases(points,pairs)
    for case in cases.values():
        if case is None:continue
        p=case["point"];r=case["illustrative_pair"]
        a,b=(lookup[(p["point_id"],r["replicate"],v)] for v in (False,True))
        event=next(e for e in a["current_slot"]["attempts"] if e["packet_id"]==p["packet_id"])
        case["packet"]={k:v for k,v in event.items() if not k.startswith("decoder_rng")}
        case["next_context"]={"failure":a["next_actual_decision"],"success":b["next_actual_decision"]}
        case["shadow_context"]={"failure":a["current_slot"]["shadow_pre_motion_replan"],"success":b["current_slot"]["shadow_pre_motion_replan"]}
        case["first_divergent_positions"]=[]
        for path in r["trajectory_alignment"]:
            i=path["first_position_index"]
            if i is not None:
                j=path["agent"]
                case["first_divergent_positions"].append({"agent":j,"position_index":i,"motion_slot":i-1,
                    "common_previous_position":a["trajectories"][j][i-1],"failure_position":a["trajectories"][j][i],"success_position":b["trajectories"][j][i]})
    write(out/"cases.json",{"selection":"Post hoc extremal positive/negative/nearest-zero point means; representative pair nearest mean, tie by smallest rep. Not representative or inferential.","cases":cases})
    table={f"shadow_{a}_actual_{b}":sum(bool(r["shadow_target_changes"])==a and bool(r["receiver_target_changes"])==b for r in pairs) for a in (False,True) for b in (False,True)}
    stratified={}
    for changed in (False,True):
        rs=[r for r in pairs if bool(r["receiver_target_changes"])==changed]
        stratified[str(changed)]={"pairs":len(rs),"point_ids":len({r["point_id"] for r in rs}),"missions":len({r["seed"] for r in rs}),
            "pair_weighted_mean_delta_T_descriptive":st.mean(r["delta_T"] for r in rs) if rs else None,
            "nonzero_delta_T_pairs":sum(r["delta_T"]!=0 for r in rs),"receiver_path_divergence_pairs":sum(r["receiver_path_diverged"] for r in rs),
            "warning":"Post-treatment strata; not mediation effects, independent N or mission-equal causal contrasts."}
    summary={"analysis":"descriptive_saved_trajectory_chain","points":14,"pairs":448,"worlds":8,"new_branches":0,
        "point_means_and_MC_SE_match_R32":True,"shadow_actual_any_change_2x2":table,"posttreatment_strata":stratified,
        "shadow_actual_changed_set_disagreement_pairs":sum(r["shadow_and_actual_changed_sets_differ"] for r in pairs),
        "receiver_path_divergence_pairs":sum(r["receiver_path_diverged"] for r in pairs),
        "no_observed_receiver_path_divergence_but_nonzero_delta_T":sum(not r["receiver_path_diverged"] and r["delta_T"]!=0 for r in pairs),
        "actual_or_shadow_hysteresis_hold_not_causal_ablation":True,
        "actual_next_context_hysteresis_compatible_hold_receiver_decisions":sum(len(v) for r in pairs for v in r["hysteresis_compatible_hold_receivers"].values()),
        "all_current_motion_prefixes_matched":True,"all_current_attempt_costs_and_nonintervened_packets_matched":True,
        "all_real_next_context_positions_match_saved_trajectories":True,
        "first_path_divergence_mapping":"trajectory index k is after motion of slot k-1; unequal lengths alone never called divergence",
        "limitations":["No full per-slot belief/target/sensing/transmission logs after next real plan","Hysteresis/private belief/time-order effects not isolated","Post-treatment stratification not mediator causality","8 development worlds; 448 pairs not independent worlds","Conditional decode effect not new scheduling policy or cost-matched gain"]}
    write(out/"summary.json",summary)
    lines=["# 全部14点的已有日志证据链","","[RUN] 分母每点32对；所有点保留。DeltaT=failure−success；uses差为success−failure。以下为描述性审查，不是机制因果效应检验。","",
        "|point|kind|ToM|DeltaT±MCSE|下一次目标改变/32|shadow改变/32|改变集合不一致/32|receiver轨迹分叉/32|无下一次目标改变但DeltaT非零|平均uses差|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for p in points:
        lines.append(f"|{p['point_id']}|{p['kind']}|{p['tom']:.6g}|{p['delta_T_mean']:+.4f}±{p['delta_T_MC_SE']:.4f}|{p['actual_target_change_pairs']}|{p['shadow_target_change_pairs']}|{p['shadow_actual_changed_set_disagreement_pairs']}|{p['receiver_path_divergence_pairs']}|{p['no_next_target_change_but_nonzero_delta_T']}|{p['delta_total_uses_mean_success_minus_failure']:+.2f}|")
    with (out/"point_matrix.md").open("x",encoding="utf-8") as f:f.write("\n".join(lines)+"\n")
    assert all(sha(Path(p))==h for p,h in verified.items()),"Read-only input changed during review"
    write(out/"completion.json",{"status":"complete","new_simulations":0,"pickle_loads":0,"wall_seconds":time.perf_counter()-start,
        "CPU_seconds":time.process_time()-cpu,"all_input_hashes_unchanged":True,"verified_input_files":len(verified)})
    write(out/"output_hashes.json",{p.name:{"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(out.iterdir()) if p.is_file()})
    print(json.dumps(summary,indent=2,ensure_ascii=False));print((out/"completion.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
