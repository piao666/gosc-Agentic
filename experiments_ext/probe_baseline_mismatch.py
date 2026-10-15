"""Small, pure-Planner environment probes; never overwrite baseline outputs."""
import argparse
from dataclasses import asdict
import importlib.metadata as md
import json
import math
import os
from pathlib import Path
import sys
import time


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--scheme",default="gosc_bits")
    ap.add_argument("--price",default=0.0,type=float)
    ap.add_argument("--seed",default=0,type=int)
    ap.add_argument("--repeat",default=2,type=int,choices=range(1,4))
    ap.add_argument("--probability-backend",choices=["original","math-exp"],default="original",
                    help="math-exp is a numerical sensitivity intervention, NOT baseline reproduction")
    args=ap.parse_args()
    from gosc import Config,run_episode
    import numpy as np
    if args.probability_backend=="math-exp":
        from gosc.channel import Channel
        original=Channel.success_prob
        def math_exp_probability(self,rate,snr_mean,n=None):
            if self.csit or self.fbl:return original(self,rate,snr_mean,n)
            exponent=-(2.0**np.asarray(rate)-1.0)/snr_mean
            return np.asarray([math.exp(float(x)) for x in np.asarray(exponent).flat]).reshape(np.shape(exponent))
        Channel.success_prob=math_exp_probability
    cfg=Config().with_(energy_price=args.price)
    rows=[]
    for _ in range(args.repeat):
        t=time.perf_counter();out=run_episode(cfg,args.scheme,args.seed)
        rows.append(dict(output=out,elapsed_seconds=time.perf_counter()-t))
    record=dict(python=sys.version,numpy=md.version("numpy"),probability_backend=args.probability_backend,
                disabled_cpu_features=os.environ.get("NPY_DISABLE_CPU_FEATURES"),config=asdict(cfg),
                scheme=args.scheme,seed=args.seed,records=rows)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as f:json.dump(record,f,indent=2)
    print(json.dumps({"numpy":record["numpy"],"probability_backend":args.probability_backend,"disabled_cpu_features":record['disabled_cpu_features'],"scheme":args.scheme,"price":args.price,
          "outcomes":[{k:r['output'][k] for k in ('completion_time','symbols','bits','confirm_latency')} for r in rows]}),flush=True)


if __name__=="__main__":main()
