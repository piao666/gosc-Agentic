"""Descriptive plot of ALL completed pilot points; no new simulations or tests.

Error bars are one Monte Carlo SE across R=4 paired differences, NOT population CIs.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir",type=Path,required=True)
    args=ap.parse_args()
    source=args.run_dir/"analysis/per_point.csv"
    rows=list(csv.DictReader(source.open(encoding="utf-8")))
    outputs=[source.parent/f"point_effects.{ext}" for ext in ("png","svg")]
    meta=source.parent/"figure_manifest.json"
    if any(p.exists() for p in outputs+[meta]):
        raise FileExistsError("Figure output already exists; use a new analysis copy")
    colors={"EVID":"#2067a5","INTENT":"#b85718"}
    markers={"EVID":"o","INTENT":"s"}
    fig,(ax,bx)=plt.subplots(1,2,figsize=(12.8,6.7),gridspec_kw={"width_ratios":[1.15,1]})
    for i,r in enumerate(rows):
        d,se=float(r["delta_T"]),float(r["mc_se_delta_T"])
        kw=dict(fmt=markers[r["kind"]],color=colors[r["kind"]],capsize=2,markersize=5)
        ax.errorbar(d,i,xerr=se,**kw)
        bx.errorbar(float(r["tom"]),d,yerr=se,**kw)
    ax.set_yticks(range(len(rows)),[f"{r['seed']}:{r['t']}  {'E' if r['kind']=='EVID' else 'I'}" for r in rows])
    ax.invert_yaxis()
    ax.axvline(0,color="0.5",lw=1,ls="--")
    ax.set_xlabel("Completion-time difference, failure - success (slots)")
    ax.set_title("All selected packets; mean +/- 1 MC SE")
    bx.set_xscale("log")
    bx.axhline(0,color="0.5",lw=1,ls="--")
    bx.set_xlabel("Unclipped ToM (sender-belief proxy; log scale)")
    bx.set_ylabel("Completion-time difference (slots)")
    bx.set_title("Proxy versus conditional task effect")
    for k in ("EVID","INTENT"):
        bx.plot([],[],markers[k],color=colors[k],label=k)
    bx.legend(frameon=False)
    for a in (ax,bx):
        a.spines[["top","right"]].set_visible(False)
        a.grid(axis="x",alpha=.15)
    fig.suptitle("Receiver-CF pilot: 8 development missions, 14 packets, R=4 paired repetitions",fontsize=12)
    fig.text(.5,.015,"Positive = successful decoding finishes earlier. Error bars reflect Monte Carlo variation, not population 95% confidence intervals.",ha="center",fontsize=9)
    fig.tight_layout(rect=(0,.045,1,.95))
    for p in outputs:
        fig.savefig(p,dpi=160,bbox_inches="tight")
    plt.close(fig)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    with meta.open("x",encoding="utf-8") as f:
        json.dump({"kind":"descriptive_all_points_postrun_visualization","csv_sha256":sha(source),
                   "script_sha256":sha(Path(__file__)),"points":len(rows),"error_bar":"1 paired MC SE, not population CI",
                   "files":{p.name:sha(p) for p in outputs}},f,indent=2)
    print("Saved all-point descriptive figure (PNG/SVG); no new simulations.")


if __name__=="__main__":
    main()
