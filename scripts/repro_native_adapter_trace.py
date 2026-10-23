"""HPC-only bounded repeat of contract fixtures, not an effect experiment."""
from pathlib import Path
import argparse,json,os,sys,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gosc.config import Config
from extensions.paid_receiver_service import ServiceConfig
from extensions.native_paid_adapter import NativePaidSimulation

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    args.output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for label,dl,mode in [('finite_dl_bits',2000,'bits'),('zero_dl_bits',0,'bits'),('finite_dl_tom',2000,'tom')]:
        service=ServiceConfig(100,dl,1.,0.,0.)
        sim=NativePaidSimulation(Config(max_steps=4,energy_price=0.),16000002,service,
                                 mode=mode,use_pose=True,record_traj=True)
        out=sim.run()
        assert sum(e['ul_uses'] for e in sim.service.events if e['kind']=='ul')==sim.service.cost['ul_uses']
        assert sum(e['uses'] for e in sim.service.events if e['kind']=='dl')==sim.service.cost['dl_uses']
        if dl==0:assert not sim._local_seen and not any(sim.service.knowledge.cache.values())
        record={'label':label,'fixture_seed':16000002,'new_independent_N':0,
                'value_mode':mode,'assumptions':'4slot contract repeat, price0, CPU0seconds, slot1second; not deployment parameters',
                'result':out,'events':sim.service.events,'received_unique_task_items':len(sim._local_seen),
                'edge_unique_task_items':len(sim._edge_seen),
                'cache_sizes':{str(k):len(v) for k,v in sim.service.knowledge.cache.items()}}
        path=args.output/(label+'.json');path.write_text(json.dumps(record,indent=2)+'\n')
        rows.append({'label':label,'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (args.output/'index.json').write_text(json.dumps({'scope':'Repeated short implementation fixtures, not effect or power data','files':rows},indent=2)+'\n')
    print(json.dumps(rows))

if __name__=='__main__':main()
