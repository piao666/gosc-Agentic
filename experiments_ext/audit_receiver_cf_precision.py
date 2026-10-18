"""Independent saved-data precision audit. No rollouts or changes to raw files."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir",type=Path,required=True)
    args=ap.parse_args();root=args.run_dir
    read=lambda p:json.loads(p.read_text(encoding="utf-8"))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    m=read(root/"experiment_manifest.json");prior=Path(m["prior_run"])
    assert read(root/"execution_completion.json")["status"]=="complete"
    assert all(sha(prior/p)==v["sha256"] for p,v in m["prior_files"].items())
    project=Path(__file__).resolve().parents[1]
    assert all(sha(project/p)==h for p,h in m["prior_protected_inputs"].items())
    assert all(sha(project/p)==h for p,h in {**m["source_sha256"],**m["prior_source_sha256"]}.items())
    rows=lambda paths:[json.loads(line) for p in sorted(paths) for line in p.read_text(encoding="utf-8").splitlines()]
    old=rows(prior.glob("seed-*/branches.jsonl"));new=rows(root.glob("point-*/branches.jsonl"))
    assert len(old)==112 and len(new)==784 and all(r["status"]=="ok" for r in new)
    lookup={(r["point_id"],r["replicate"],r["success_branch"]):r for r in old+new}
    assert len(lookup)==896
    points=list(csv.DictReader((root/"analysis/per_point_by_R.csv").open(encoding="utf-8")))
    assert len(points)==56
    for p in points:
        R=int(p["R"])
        d=[lookup[(p["point_id"],r,False)]["result"]["completion_time"]-lookup[(p["point_id"],r,True)]["result"]["completion_time"] for r in range(R)]
        np.testing.assert_allclose(float(p["delta_T"]),np.mean(d),atol=1e-12)
        np.testing.assert_allclose(float(p["mc_se_delta_T"]),np.std(d,ddof=1)/np.sqrt(R),atol=1e-12)
    stats=read(root/"analysis/statistics_by_R.json")
    independent={}
    for R in (4,8,16,32):
        rng=np.random.default_rng(0)
        selected=[p for p in points if int(p["R"])==R]
        summary={}
        for kind in ("EVID","INTENT","all"):
            rs=[p for p in selected if kind=="all" or p["kind"]==kind]
            by={s:np.mean([float(p["delta_T"]) for p in rs if int(p["seed"])==s]) for s in m["seeds"] if any(int(p["seed"])==s for p in rs)}
            boots=[]
            for _ in range(4000):
                sample=[by[int(s)] for s in rng.choice(m["seeds"],8) if int(s) in by]
                if sample:boots.append(np.mean(sample))
            ci=np.percentile(boots,[2.5,97.5]).tolist()
            target=stats["levels"][str(R)]["statistics"][kind]
            np.testing.assert_allclose(np.mean(list(by.values())),target["delta_T_mission_equal_mean"],atol=1e-12)
            np.testing.assert_allclose(ci,target["ci95"] if kind=="all" else target["mean_interval"]["ci95"],atol=1e-12)
            summary[kind]={"mean":float(np.mean(list(by.values()))),"ci95":ci,"valid_bootstraps":len(boots)}
        independent[str(R)]=summary
    result={"status":"passed","old_branches":112,"new_branches":784,"merged_branches":896,
        "paired_MC_repetitions":448,"independent_worlds":8,"point_level_cells_checked":56,
        "old_indexed_files_unchanged":len(m["prior_files"]),"protected_inputs_unchanged":len(m["prior_protected_inputs"]),
        "all_runtime_source_hashes_match":True,"independent_mean_CIs_all_levels":independent,
        "completed_new_branch_missions":sum(r["result"]["completed"] for r in new),
        "new_false_declarations_retained":sum(r["result"]["false_declarations"] for r in new),
        "all_branch_false_declarations":sum(r["result"]["false_declarations"] for r in old+new),
        "new_completion_time_range":[min(r["result"]["completion_time"] for r in new),max(r["result"]["completion_time"] for r in new)],
        "audit_script_sha256":sha(Path(__file__)),"method":"Raw paired-difference reconstruction plus independent scalar mission-means cluster bootstrap."}
    with (root/"analysis/independent_audit.json").open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
