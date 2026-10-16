"""Analyze Receiver-CF paired branches; never generate or select new missions."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

from experiments_ext.review_receiver_mechanisms import average_ranks, correlation


def read_rows(paths):
    return [json.loads(line) for p in sorted(paths) for line in p.read_text(encoding="utf-8").splitlines() if line]


def mean(x):
    return float(np.mean(x)) if len(x) else None


def rho(rows, field):
    # Predeclared before outcomes: fewer than 3 points / 2 missions is undefined.
    if len(rows) < 3 or len({r["seed"] for r in rows}) < 2:
        return None
    return correlation(average_ranks([r[field] for r in rows]), average_ranks([r["delta_T"] for r in rows]))


def mission_mean(rows, field):
    # Bootstrap copies of one mission must retain their draw multiplicity.
    key = lambda r: r.get("_bootstrap_cluster", r["seed"])
    ids = sorted({key(r) for r in rows})
    return mean([mean([r[field] for r in rows if key(r) == s]) for s in ids])


def cluster_sample(by, sampled_seeds):
    return [{**r, "_bootstrap_cluster": i} for i,s in enumerate(sampled_seeds) for r in by[int(s)]]


def interval(boots):
    values = [x for x in boots if x is not None and np.isfinite(x)]
    return {"ci95": np.percentile(values, [2.5, 97.5]).tolist() if values else None,
            "valid_bootstraps": len(values), "total_bootstraps": len(boots)}


def pair_points(features, branches):
    ids = [(r["point_id"], r["replicate"], r["success_branch"]) for r in branches]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate branch identity")
    lookup = dict(zip(ids, branches))
    points, missing = [], []
    for f in features:
        pairs = []
        for rr in range(4):
            a = lookup.get((f["point_id"], rr, False))
            b = lookup.get((f["point_id"], rr, True))
            if a is None or b is None or a["status"] != "ok" or b["status"] != "ok":
                continue
            assert a["packet_id"] == b["packet_id"] == f["packet_id"]
            assert a["snapshot_state_sha256"] == b["snapshot_state_sha256"]
            assert a["future_rng_initial_sha256"] == b["future_rng_initial_sha256"]
            for field in ("bits", "symbols"):
                assert a["current_slot"]["current_cost"][field] == b["current_slot"]["current_cost"][field]
            aa, bb = a["current_slot"]["attempts"], b["current_slot"]["attempts"]
            assert len(aa) == len(bb)
            for x, y in zip(aa, bb):
                if x["packet_id"] != f["packet_id"]:
                    assert x == y
            pairs.append((a,b))
        if len(pairs) != 4:
            missing.append({"point_id":f["point_id"], "complete_pairs":len(pairs)})
            continue
        deltas = [a["result"]["completion_time"]-b["result"]["completion_time"] for a,b in pairs]
        changes, shadow = [], []
        for a,b in pairs:
            da, db = a["next_actual_decision"], b["next_actual_decision"]
            if da is not None and db is not None:
                changes.append(sum(x["target"] != y["target"] for x,y in zip(da,db) if x["agent"] != f["sender"]))
            sa, sb = a["current_slot"]["shadow_pre_motion_replan"], b["current_slot"]["shadow_pre_motion_replan"]
            shadow.append(sum(x["target"] != y["target"] for x,y in zip(sa,sb) if x["agent"] != f["sender"]))
        p = {**f, "delta_T": mean(deltas), "mc_se_delta_T": float(np.std(deltas,ddof=1)/2),
             "pairs":4, "next_receiver_changes_mean":mean(changes),
             "comparable_next_decision_pairs":len(changes), "shadow_receiver_changes_mean":mean(shadow)}
        for prefix, branch_index in (("failure",0),("success",1)):
            rs = [pair[branch_index]["result"] for pair in pairs]
            for field in ("completion_time", "completed", "found", "false_declarations", "bits", "symbols", "dl_symbols", "delivered_bits"):
                p[f"{prefix}_{field}"] = mean([r[field] for r in rs])
        p["delta_total_recorded_uses_success_minus_failure"] = mean([
            b["result"]["symbols"]+b["result"]["dl_symbols"]-a["result"]["symbols"]-a["result"]["dl_symbols"] for a,b in pairs])
        points.append(p)
    return points, missing


def summarize(points, universe, nboot=4000):
    rng = np.random.default_rng(0)
    out = {}
    for kind in ("EVID", "INTENT"):
        rows = [p for p in points if p["kind"] == kind]
        by = {s:[r for r in rows if r["seed"]==s] for s in universe}
        boot = [cluster_sample(by, rng.choice(universe,len(universe))) for _ in range(nboot)]
        stats = {"points":len(rows), "missions_with_points":len({r["seed"] for r in rows}),
                 "delta_T_mission_equal_mean":mission_mean(rows,"delta_T"),
                 "delta_T_quantiles_point_level":np.percentile([r["delta_T"] for r in rows],[0,25,50,75,100]).tolist() if rows else None,
                 "positive_zero_negative_points":[sum(r["delta_T"]>0 for r in rows),sum(r["delta_T"]==0 for r in rows),sum(r["delta_T"]<0 for r in rows)],
                 "mean_interval":interval([mission_mean(b,"delta_T") for b in boot]),
                 "rho":{field:{"point_estimate":rho(rows,field), **interval([rho(b,field) for b in boot])}
                        for field in ("tom","tv","bits","aoi")}}
        out[kind] = stats
    allboot = []
    by = {s:[r for r in points if r["seed"]==s] for s in universe}
    for _ in range(nboot):
        allboot.append(cluster_sample(by, rng.choice(universe,len(universe))))
    out["all"] = {"missions":len({r["seed"] for r in points}), "points":len(points),
                  "delta_T_mission_equal_mean":mission_mean(points,"delta_T"),
                  **interval([mission_mean(b,"delta_T") for b in allboot]),
                  "delta_recorded_uses_success_minus_failure":mission_mean(points,"delta_total_recorded_uses_success_minus_failure"),
                  "mean_next_receiver_changes_point_level":mean([p["next_receiver_changes_mean"] for p in points if p["next_receiver_changes_mean"] is not None]),
                  "mean_shadow_receiver_changes_point_level":mean([p["shadow_receiver_changes_mean"] for p in points])}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()
    root = args.run_dir
    manifest = json.loads((root/"experiment_manifest.json").read_text(encoding="utf-8"))
    features = read_rows(root.glob("seed-*/features.jsonl"))
    branches = read_rows(root.glob("seed-*/branches.jsonl"))
    available = read_rows(root.glob("seed-*/availability.jsonl"))
    points, missing = pair_points(features, branches)
    stats = summarize(points, manifest["seeds"])
    doc = {"analysis_kind":"exploratory_conditional_decode_effect_not_new_policy", "run_commit":manifest["git_commit"],
           "raw_branch_rows":len(branches), "ok_branches":sum(r["status"]=="ok" for r in branches),
           "missing_or_incomplete_points":missing, "availability":available, "statistics":stats,
           "bootstrap_seed":0, "bootstrap_repetitions":4000, "cluster_unit":"mission",
           "rho_rule":"average ties; undefined if <3 points or <2 distinct missions or constant feature/outcome",
           "uncertainty_note":"8 mission clusters; percentile CI exploratory, no multiplicity-adjusted confirmatory claims; R=4 MC uncertainty reported per point, not separately propagated by cluster bootstrap",
           "cost_boundary":{"wire_bytes":"not_serialized_not_measured", "extra_ack_crc_phy_sync":"not_modeled_in_native_base",
                            "ul_uses":"native symbols", "dl_uses":"native ceil(broadcast_bits/dl_rate)", "llm_calls":0}}
    out = root/"analysis"
    out.mkdir(exist_ok=False)
    (out/"statistics.json").write_text(json.dumps(doc,indent=2,allow_nan=False),encoding="utf-8")
    with (out/"per_point.csv").open("x",newline="",encoding="utf-8") as f:
        fields = sorted(set().union(*(p.keys() for p in points))) if points else ["point_id"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(points)
    lines=["# Receiver-CF v1 exploratory results", "", "[RUN] Native selected packet conditional decode intervention; development seeds5000–5007.",
           f"Raw branches: {len(branches)}; complete points: {len(points)}; independent mission clusters at most8.", "",
           "|Type|Points|Missions|Mean DeltaT (failure-success), slots|Exploratory 95% cluster CI|Positive/zero/negative points|",
           "|---|---:|---:|---:|---|---|"]
    for k in ("EVID","INTENT"):
        s=stats[k]
        lines.append(f"|{k}|{s['points']}|{s['missions_with_points']}|{s['delta_T_mission_equal_mean']}|{s['mean_interval']['ci95']}|{s['positive_zero_negative_points']}|")
    lines += ["", "Correlations: average-tie Spearman; undefined values and valid bootstrap counts retained in statistics.json.",
              "No new estimator, no online oracle, no trained model, no cost-matched policy claim. Current attempt UL costs match; future total costs may differ.",
              "Completion time capped400; all failures/false declarations retained. Native sequential streams are not cell-aligned after path divergence."]
    (out/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"raw_branches":len(branches),"points":len(points),"all":stats["all"]},indent=2))


if __name__ == "__main__":
    main()
