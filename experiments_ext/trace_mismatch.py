"""Non-intervening scheduling trace for the first blocked replication case."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

from gosc import Config, Simulation
from experiments_ext.reproduce import ROOT, save, sha


def main():
    if len(sys.argv)!=2: raise SystemExit("usage: python -m experiments_ext.trace_mismatch OUTPUT_DIRECTORY")
    out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
    cfg=Config().with_(energy_price=0.0)
    sim=Simulation(cfg,"gosc_bits",0)
    sim.scheme.log=[]
    original=sim.scheme.transmit
    count=0
    with (out/"scheduling.jsonl").open("x",encoding="utf-8") as f:
        def traced(agent,t,snr_mean,snr_inst,view):
            nonlocal count
            result=original(agent,t,snr_mean,snr_inst,view)
            groups,chosen,price,budget=sim.scheme.log[-1]
            row=dict(t=t,agent=agent.idx,position=list(agent.pos),snr_mean=float(snr_mean),
                snr_inst=float(snr_inst),price=price,budget=budget,
                groups=[asdict(g) for g in groups],
                chosen=[dict(group_index=next(i for i,x in enumerate(groups) if x is g),
                             kind=g.kind,option=asdict(o),value_float_hex=float(o.value).hex()) for g,o in chosen],
                tx_bits=result.bits,tx_symbols=result.symbols,
                delivered_kinds=[p.kind for p in result.delivered])
            f.write(json.dumps(row,default=lambda x:x.item())+"\n");count+=1
            return result
        sim.scheme.transmit=traced
        started=time.perf_counter();result=sim.run();elapsed=time.perf_counter()-started
    if (result["completion_time"],result["symbols"],result["bits"])!=(76,29596,22109):
        raise RuntimeError("Instrumentation changed the known local outcome")
    save(out/"manifest.json",dict(status="trace_matches_uninstrumented_local_run",
         config=asdict(cfg),seed=0,scheme="gosc_bits",source_sha256=sha(__file__),
         baseline_source_sha256=sha(ROOT/"gosc/schemes.py"),scheduling_records=count,
         trace_sha256=sha(out/"scheduling.jsonl"),elapsed_seconds=elapsed,output=result,
         notes="Diagnostic trace only. No changes to selection, options, channel or RNG. Does not reproduce saved author result."))
    print("Trace records",count,"local outcome",result["completion_time"],result["symbols"],result["bits"])


if __name__=="__main__":main()
