"""Fixed R4/8/16/32 convergence analysis; no new simulations or selection."""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from experiments_ext.analyze_receiver_cf import read_rows, summarize

LEVELS=(4,8,16,32)


def merge_rows(old, new, features):
    fixed={f["point_id"]:f["packet_id"] for f in features}
    if len(features)!=len(fixed):
        raise ValueError("Duplicate fixed points")
    lookup={}
    for origin,rows,allowed in (("old",old,range(4)),("new",new,range(4,32))):
        for r in rows:
            key=(r["point_id"],r["replicate"],r["success_branch"])
            if key in lookup or r["replicate"] not in allowed:
                raise ValueError("Duplicate or out-of-scope replicate")
            if r["point_id"] not in fixed or r["packet_id"]!=fixed[r["point_id"]]:
                raise ValueError("Point/packet changed")
            lookup[key]=r
    return lookup


def point_at_R(f, lookup, R):
    pairs=[];missing=[]
    for rr in range(R):
        a=lookup.get((f["point_id"],rr,False)); b=lookup.get((f["point_id"],rr,True))
        if a is None or b is None or a["status"]!="ok" or b["status"]!="ok":
            missing.append(rr);continue
        assert a["snapshot_state_sha256"]==b["snapshot_state_sha256"]
        assert a["future_rng_initial_sha256"]==b["future_rng_initial_sha256"]
        for row in (a,b):
            assert row["future_seed_key"]==[f["seed"],f["t"],f["sender"],rr]
        for field in ("bits","symbols"):
            assert a["current_slot"]["current_cost"][field]==b["current_slot"]["current_cost"][field]
        aa,bb=a["current_slot"]["attempts"],b["current_slot"]["attempts"]
        assert len(aa)==len(bb)
        for x,y in zip(aa,bb):
            if x["packet_id"]!=f["packet_id"]:assert x==y
            else:assert x["effective_decode"] is False and y["effective_decode"] is True
        pairs.append((a,b))
    if missing:
        return None,{"point_id":f["point_id"],"R":R,"missing_or_failed_replicates":missing}
    d=np.asarray([a["result"]["completion_time"]-b["result"]["completion_time"] for a,b in pairs],float)
    changes=[];shadow=[]
    for a,b in pairs:
        da,db=a["next_actual_decision"],b["next_actual_decision"]
        if da is not None and db is not None:
            changes.append(sum(x["target"]!=y["target"] for x,y in zip(da,db) if x["agent"]!=f["sender"]))
        sa,sb=a["current_slot"]["shadow_pre_motion_replan"],b["current_slot"]["shadow_pre_motion_replan"]
        shadow.append(sum(x["target"]!=y["target"] for x,y in zip(sa,sb) if x["agent"]!=f["sender"]))
    result={**f,"R":R,"pairs":R,"delta_T":float(d.mean()),
            "mc_se_delta_T":float(d.std(ddof=1)/math.sqrt(R)),
            "pair_positive":int((d>0).sum()),"pair_zero":int((d==0).sum()),"pair_negative":int((d<0).sum()),
            "next_receiver_changes_mean":float(np.mean(changes)) if changes else None,
            "comparable_next_decision_pairs":len(changes),"shadow_receiver_changes_mean":float(np.mean(shadow)),
            "delta_total_recorded_uses_success_minus_failure":float(np.mean([
                b["result"]["symbols"]+b["result"]["dl_symbols"]-a["result"]["symbols"]-a["result"]["dl_symbols"] for a,b in pairs]))}
    for label,index in (("failure",0),("success",1)):
        for field in ("completion_time","completed","found","false_declarations","bits","symbols","dl_symbols","delivered_bits"):
            result[f"{label}_{field}"]=float(np.mean([p[index]["result"][field] for p in pairs]))
    return result,None


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir",type=Path,required=True)
    args=ap.parse_args();root=args.run_dir
    m=json.loads((root/"experiment_manifest.json").read_text())
    prior=Path(m["prior_run"])
    plan=json.loads((root/"fixed_points.json").read_text());features=[p["feature"] for p in plan]
    old=read_rows(prior.glob("seed-*/branches.jsonl"));new=read_rows(root.glob("point-*/branches.jsonl"))
    lookup=merge_rows(old,new,features)
    out=root/"analysis";out.mkdir(exist_ok=False)
    all_points=[];levels={};convergence=[]
    for R in LEVELS:
        points=[];missing=[]
        for f in features:
            p,error=point_at_R(f,lookup,R)
            if error:missing.append(error)
            else:points.append(p)
        if missing:
            levels[str(R)]={"status":"incomplete_no_subset_inference","missing":missing}
            continue
        all_points.extend(points)
        levels[str(R)]={"status":"complete","statistics":summarize(points,m["seeds"]),
            "precision":{"median_MC_SE":float(np.median([p["mc_se_delta_T"] for p in points])),
                "max_MC_SE":max(p["mc_se_delta_T"] for p in points),
                "nonzero_points":sum(p["delta_T"]!=0 for p in points),
                "nonzero_MC_SE_ge_abs_mean":sum(p["mc_se_delta_T"]>=abs(p["delta_T"]) for p in points if p["delta_T"]!=0),
                "point_positive_zero_negative":[sum(p["delta_T"]>0 for p in points),sum(p["delta_T"]==0 for p in points),sum(p["delta_T"]<0 for p in points)]}}
    # Reproduce the original R4 statistics exactly before interpreting extensions.
    prior_stats=json.loads((prior/"analysis/statistics.json").read_text())["statistics"]
    assert levels["4"]["statistics"]==prior_stats,"Original R4 statistics did not rebuild exactly"
    for f in features:
        series=[p for p in all_points if p["point_id"]==f["point_id"]]
        row={"point_id":f["point_id"],"kind":f["kind"]}
        for p in series:
            row.update({f"mean_R{p['R']}":p["delta_T"],f"MC_SE_R{p['R']}":p["mc_se_delta_T"]})
        if len(series)==4:
            a,b=series[0],series[-1]
            row.update(mean_drift_R32_minus_R4=b["delta_T"]-a["delta_T"],
                sign_changed_R4_R32=bool(np.sign(a["delta_T"])!=np.sign(b["delta_T"])),
                same_nonzero_sign_all_levels=bool(all(np.sign(p["delta_T"])==np.sign(a["delta_T"]) for p in series) and a["delta_T"]!=0),
                MC_SE_ratio_R32_over_R4=b["mc_se_delta_T"]/a["mc_se_delta_T"] if a["mc_se_delta_T"] else None)
        convergence.append(row)
    doc={"analysis":"fixed14 cumulative R4/8/16/32 MC precision; no new policy",
         "old_branches":len(old),"new_branches":len(new),"merged_branches":len(lookup),
         "old_R4_rebuilt_exactly":True,"mission_clusters":8,"fixed_points":14,
         "levels":levels,"bootstrap_repetitions":4000,"bootstrap_seed":0,
         "notes":"Nested cumulative levels are dependent, not independent confirmations. Cluster CIs exploratory; do not separately propagate finite MC noise. No multiple-comparison/causal-mechanism claim."}
    (out/"statistics_by_R.json").write_text(json.dumps(doc,indent=2,allow_nan=False),encoding="utf-8")
    for name,rows in (("per_point_by_R.csv",all_points),("convergence.csv",convergence)):
        fields=sorted(set().union(*(r.keys() for r in rows))) if rows else ["point_id"]
        with (out/name).open("x",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    if len(all_points)==56:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig,axes=plt.subplots(1,2,figsize=(11,4.6))
        for f in features:
            ps=[p for p in all_points if p["point_id"]==f["point_id"]]
            color="#2067a5" if f["kind"]=="EVID" else "#b85718"
            axes[0].plot(LEVELS,[p["mc_se_delta_T"] for p in ps],"o-",color=color,alpha=.55,ms=3)
            axes[1].plot(LEVELS,[p["delta_T"] for p in ps],"o-",color=color,alpha=.55,ms=3)
        for ax in axes:
            ax.set_xscale("log",base=2);ax.set_xticks(LEVELS,LEVELS);ax.set_xlabel("Cumulative paired repetitions R")
            ax.spines[["top","right"]].set_visible(False);ax.grid(alpha=.15)
        axes[0].set_ylabel("Paired Monte Carlo SE (slots)");axes[0].set_title("All fixed packets: precision")
        axes[1].set_ylabel("Mean DeltaT, failure - success (slots)");axes[1].set_title("All fixed packets: point estimates");axes[1].axhline(0,color=".4",ls="--",lw=1)
        for kind,color in (("EVID","#2067a5"),("INTENT","#b85718")):
            axes[1].plot([],[],"o-",color=color,label=kind)
        axes[1].legend(frameon=False)
        fig.suptitle("Fixed-checkpoint MC convergence: 14 packets, 8 development worlds")
        fig.tight_layout();fig.savefig(out/"convergence.png",dpi=160);plt.close(fig)
    print(json.dumps({"old_branches":len(old),"new_branches":len(new),"merged_branches":len(lookup),
                      "R32":levels.get("32")},indent=2))


if __name__=="__main__":
    main()
