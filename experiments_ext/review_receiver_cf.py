"""Descriptive postrun checks of all Receiver-CF points; no new rollouts."""
import argparse
import csv
import json
from pathlib import Path


def review(root):
    rows=[json.loads(l) for p in sorted(root.glob("seed-*/branches.jsonl"))
          for l in p.read_text(encoding="utf-8").splitlines()]
    if not rows or any(r["status"]!="ok" for r in rows):
        raise ValueError("This completed-run review requires all branches ok; preserve partial data separately")
    lookup={(r["point_id"],r["replicate"],r["success_branch"]):r for r in rows}
    if len(lookup)!=len(rows):
        raise ValueError("Duplicate branch IDs")
    deltas=[]
    for (point,rep,success),a in lookup.items():
        if success:
            continue
        b=lookup[(point,rep,True)]
        deltas.append(a["result"]["completion_time"]-b["result"]["completion_time"])
    points=list(csv.DictReader((root/"analysis/per_point.csv").open(encoding="utf-8")))
    return {"completed_branch_missions":sum(r["result"]["completed"] for r in rows),
            "branches":len(rows),
            "false_declarations_across_branch_runs":sum(r["result"]["false_declarations"] for r in rows),
            "completion_time_range":[min(r["result"]["completion_time"] for r in rows),max(r["result"]["completion_time"] for r in rows)],
            "point_positive_zero_negative":[sum(float(r["delta_T"])>0 for r in points),sum(float(r["delta_T"])==0 for r in points),sum(float(r["delta_T"])<0 for r in points)],
            "paired_MC_positive_zero_negative":[sum(d>0 for d in deltas),sum(d==0 for d in deltas),sum(d<0 for d in deltas)],
            "nonzero_points_MC_SE_ge_absolute_mean":sum(float(r["mc_se_delta_T"])>=abs(float(r["delta_T"])) for r in points if float(r["delta_T"])!=0),
            "nonzero_points":sum(float(r["delta_T"])!=0 for r in points),
            "points_any_next_receiver_change":sum(float(r["next_receiver_changes_mean"])>0 for r in points),
            "points_any_shadow_receiver_change":sum(float(r["shadow_receiver_changes_mean"])>0 for r in points),
            "comparable_next_decision_pairs":sum(int(r["comparable_next_decision_pairs"]) for r in points),
            "mc_se_range":[min(float(r["mc_se_delta_T"]) for r in points),max(float(r["mc_se_delta_T"]) for r in points)],
            "interpretation":"Descriptive postrun checks only; paired continuations and points are not independent mission samples."}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir",type=Path,required=True)
    ap.add_argument("--output-name",default="outcome_review.json")
    args=ap.parse_args()
    if Path(args.output_name).name!=args.output_name:
        raise SystemExit("Output name must be a single filename")
    result=review(args.run_dir)
    with (args.run_dir/"analysis"/args.output_name).open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
