"""Paired, reproducible statistics over retained local mission records."""
import argparse
from collections import defaultdict
import csv
import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np

from experiments_ext.reproduce import ROOT, save, sha


def describe(values):
    a = np.asarray(values, float)
    return dict(n=len(a), mean=float(a.mean()), q25=float(np.percentile(a, 25)),
                median=float(np.median(a)), q75=float(np.percentile(a, 75)),
                mean_ci_normal95=float(1.96*a.std(ddof=1)/np.sqrt(len(a))))


def paired(a, b, comparisons=1):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) != len(b): raise ValueError("Unpaired sample sizes")
    delta = a-b
    idx = np.random.default_rng(0).integers(0,len(a),(4000,len(a)))
    boots = delta[idx].mean(axis=1)
    return dict(n=len(a), mean=float(delta.mean()),
                ci95=[float(v) for v in np.percentile(boots,[2.5,97.5])],
                family_ci=[float(v) for v in np.percentile(boots,[2.5/comparisons,100-2.5/comparisons])],
                comparisons=comparisons, bootstrap_resamples=4000,
                positive_seeds=int((delta>0).sum()), negative_seeds=int((delta<0).sum()),
                zero_seeds=int((delta==0).sum()))


def ratio(a, b):
    a,b = np.asarray(a,float),np.asarray(b,float)
    idx=np.random.default_rng(0).integers(0,len(a),(4000,len(a)))
    boots=a[idx].mean(axis=1)/b[idx].mean(axis=1)
    return [float(a.mean()/b.mean()), *[float(v) for v in np.percentile(boots,[2.5,97.5])]]


def vectors(rows, key):
    ordered=sorted(rows,key=lambda r:r["seed"])
    seeds=[r["seed"] for r in ordered]
    if len(seeds)!=len(set(seeds)): raise ValueError("Duplicate seed in group")
    return [r["output"][key] for r in ordered]


def load(run, stage):
    manifest=json.loads((run/stage/"manifest.json").read_text())
    if manifest["status"]!="passed": raise RuntimeError("Stage not passed")
    rows=[json.loads(line) for line in (run/stage/"raw.jsonl").open(encoding="utf-8")]
    if len(rows)!=manifest["completed"]: raise RuntimeError("Incomplete records")
    return rows


def baseline(run):
    rows=load(run,"r4")
    groups=defaultdict(list)
    for r in rows: groups[(r["campaign"],r.get("setting",""),r.get("family",""),r["scheme"],r["param"])].append(r)
    if any(len(v)!=100 for v in groups.values()): raise RuntimeError("R4 groups must each have N=100")
    for key, values in groups.items():
        expected=set(range(3000,3100)) if key[0]=="headline-frozen" else set(range(100))
        if {r["seed"] for r in values}!=expected: raise RuntimeError("R4 seed set mismatch")
    summary={"fresh_executions":len(rows),"group_count":len(groups),"reference_mismatches":0,
             "frozen":{},"private":{},"frontier":None}
    summary["group_quality"]=[dict(campaign=k[0],setting=k[1],family=k[2],scheme=k[3],param=k[4],
        n=len(rs),completion_rate=float(np.mean(vectors(rs,"completed"))),
        false_declarations_mean=float(np.mean(vectors(rs,"false_declarations")))) for k,rs in groups.items()]
    selected=json.loads((run/"r4/plan.json").read_text())["selections"]
    for setting, sel in selected.items():
        families={r["family"]:[] for r in rows if r.get("setting")==setting}
        for r in rows:
            if r.get("setting")==setting: families[r["family"]].append(r)
        g,p=families["gosc"],families["periodic"]
        metric="saved_fraction" if setting.startswith("rescue") else "completion_time"
        summary["frozen"][setting]={"metric":metric,"target":sel["target"],
            "gosc":describe(vectors(g,metric)),"periodic":describe(vectors(p,metric)),
            "gosc_uses":describe(vectors(g,"symbols")),"periodic_uses":describe(vectors(p,"symbols")),
            "outcome_gosc_minus_periodic":paired(vectors(g,metric),vectors(p,metric)),
            "ratio_periodic_over_gosc":ratio(vectors(p,"symbols"),vectors(g,"symbols"))}
    for setting in ("default","W50","snr-5"):
        modes={m:[r for r in rows if r["campaign"]=="private-original" and r["param"]==setting+"/"+m]
               for m in ("shared","oracle")}
        a,b=modes["shared"],modes["oracle"]
        summary["private"][setting]={"shared":describe(vectors(a,"completion_time")),
            "oracle":describe(vectors(b,"completion_time")),
            "time_shared_minus_oracle":paired(vectors(a,"completion_time"),vectors(b,"completion_time")),
            "ul_oracle_minus_shared":paired(vectors(b,"symbols"),vectors(a,"symbols")),
            "private_tv":describe(vectors(a,"private_tv"))}
    from experiments.plot_revision import table, matched
    original_rows=[dict(scheme=r["scheme"],param=r["param"],seed=r["seed"],**r["output"])
                   for r in rows if r["campaign"]=="frontier-W100"]
    curves={}
    for (scheme,param), rs in table(original_rows).items():
        setting,knob=param.split("/")
        curves.setdefault((setting,scheme),[]).append((knob,rs))
    summary["frontier"]=matched(curves,"W100")
    reference=json.loads((run/"upstream_workspace/results/summary_revision.json").read_text())["frontier"]["W100"]
    discrepancies=[]
    for budget, strategies in summary["frontier"].items():
        for scheme,value in strategies.items():
            expected=reference[str(budget)][scheme]
            if value is None or expected is None:
                if value!=expected: discrepancies.append([budget,scheme,"availability"])
            else:
                for k,v in value.items():
                    if abs(v-expected[k])>1e-9: discrepancies.append([budget,scheme,k,v,expected[k]])
    summary["matched_frontier_reference_differences"]=discrepancies
    save(run/"r4/statistics.json",summary)
    print("R4 statistics complete; matched-frontier differences:",len(discrepancies),flush=True)


def diagnostic(run):
    rows=load(run,"diagnostic")
    out={"seeds":"4000-4099","primary_comparison_family_size":6,"settings":{},
         "interpretation":"Privileged state, fixed eta, unmatched realized communication costs. No deployable-method or equal-cost-defect claim."}
    export=[]
    for setting in ("default","W50","snr-5"):
        groups={mode:[r for r in rows if r["setting"]==setting and r["mode"]==mode]
                for mode in ("shared","private","position","joint")}
        if any(len(rs)!=100 for rs in groups.values()): raise RuntimeError("Incomplete diagnostic group")
        if any({r["seed"] for r in rs}!=set(range(4000,4100)) for rs in groups.values()):
            raise RuntimeError("Diagnostic seed set mismatch")
        mode_stats={mode:{k:describe(vectors(rs,k)) for k in
                    ("completion_time","symbols","bits","dl_symbols","private_tv","completed","false_declarations")}
                    for mode,rs in groups.items()}
        contrasts={}
        shared=vectors(groups["shared"],"completion_time")
        for mode in ("private","position","joint"):
            factor=6 if mode in ("private","position") else 1
            time=paired(shared,vectors(groups[mode],"completion_time"),factor)
            time["relative_improvement_pct"]=100*time["mean"]/np.mean(shared)
            time["practical_threshold_slots"]=0.05*float(np.mean(shared))
            time["family_interval_exceeds_practical_threshold"]=time["family_ci"][0]>time["practical_threshold_slots"]
            ul=paired(vectors(groups[mode],"symbols"),vectors(groups["shared"],"symbols"))
            contrasts[mode]={"time_shared_minus_mode":time,"ul_mode_minus_shared":ul,
                "total_recorded_uses_mode_minus_shared":paired(
                    np.array(vectors(groups[mode],"symbols"))+np.array(vectors(groups[mode],"dl_symbols")),
                    np.array(vectors(groups["shared"],"symbols"))+np.array(vectors(groups["shared"],"dl_symbols")))}
            export.append(dict(setting=setting,mode=mode,mean_time_gain=time["mean"],ci_lo=time["ci95"][0],
                               ci_hi=time["ci95"][1],family_lo=time["family_ci"][0],family_hi=time["family_ci"][1],
                               gain_pct=time["relative_improvement_pct"],ul_delta=ul["mean"],
                               ul_ci_lo=ul["ci95"][0],ul_ci_hi=ul["ci95"][1]))
        # Improvement of the joint intervention minus the sum of single improvements.
        joint_gain=np.array(shared)-vectors(groups["joint"],"completion_time")
        private_gain=np.array(shared)-vectors(groups["private"],"completion_time")
        position_gain=np.array(shared)-vectors(groups["position"],"completion_time")
        out["settings"][setting]={"modes":mode_stats,"contrasts":contrasts,
            "interaction_joint_gain_minus_single_gains":paired(joint_gain,private_gain+position_gain)}
    save(run/"diagnostic/statistics.json",out)
    with (run/"diagnostic/contrasts.csv").open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(export[0]));w.writeheader();w.writerows(export)
    print(json.dumps(export,indent=2),flush=True)
    plots(run,export)


def plots(run, rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8.2,5.4),layout="constrained")
    for i,r in enumerate(rows):
        color={"private":"#2166ac","position":"#b35806","joint":"#555555"}[r["mode"]]
        ax.plot([r["family_lo"],r["family_hi"]],[i,i],color=color,alpha=.35,lw=5)
        ax.plot([r["ci_lo"],r["ci_hi"]],[i,i],color=color,lw=1.7)
        ax.plot(r["mean_time_gain"],i,"o",color=color)
    ax.axvline(0,color="black",lw=.8,ls="--")
    ax.set_yticks(range(len(rows)),[r["setting"]+" / "+r["mode"] for r in rows]);ax.invert_yaxis()
    ax.set_xlabel("Shared minus intervention completion time (slots); positive = faster")
    ax.set_title("Receiver-state oracle diagnostic: 100 paired seeds per setting")
    fig.text(.5,-.025,"Thin: 95% CI; thick: family-adjusted CI for single factors. Privileged state; costs not matched.",ha="center",fontsize=8)
    for suffix in ("pdf","png"): fig.savefig(run/"diagnostic"/("time_contrasts."+suffix),dpi=170,bbox_inches="tight")
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(9.0,4.6),layout="constrained")
    for r in rows:
        color={"default":"#2166ac","W50":"#b35806","snr-5":"#6a3d9a"}[r["setting"]]
        marker={"private":"o","position":"s","joint":"^"}[r["mode"]]
        ax.errorbar(r["ul_delta"],r["mean_time_gain"],
            xerr=[[r["ul_delta"]-r["ul_ci_lo"]],[r["ul_ci_hi"]-r["ul_delta"]]],
            yerr=[[r["mean_time_gain"]-r["ci_lo"]],[r["ci_hi"]-r["mean_time_gain"]]],
            fmt=marker,color=color,alpha=.8,capsize=2,label=r["setting"]+" / "+r["mode"])
    ax.axvline(0,color="black",lw=.7);ax.axhline(0,color="black",lw=.7)
    ax.set_xlabel("Extra mean UL data channel uses versus shared")
    ax.set_ylabel("Completion-time improvement (slots)")
    ax.set_title("Task effects and communication effects must be read together")
    ax.legend(loc="center left",bbox_to_anchor=(1.01,.5),fontsize=8,frameon=False)
    for suffix in ("pdf","png"): fig.savefig(run/"diagnostic"/("time_and_resources."+suffix),dpi=170,bbox_inches="tight")
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage",choices=["r4","diagnostic"]);ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    if Path(args.run_id).name!=args.run_id: ap.error("Invalid run-id")
    run=ROOT/".local/reproduction"/args.run_id
    if args.stage=="r4": baseline(run)
    else: diagnostic(run)


if __name__=="__main__": main()
