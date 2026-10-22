"""Bounded cache diagnosis across existing NumPy environments; HPC only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.local/ordered-reproduction-20261019'
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='1'

def child(mode):
    sys.path.insert(0,str(WORK))
    import numpy as np
    from gosc import Config,run_episode,llm_agent
    if mode!='default':
        original=np.argsort
        def alternative(a,*args,**kwargs):
            if len(args)<2 and 'kind' not in kwargs:kwargs['kind']=mode
            return original(a,*args,**kwargs)
        np.argsort=alternative
    class Miss(Exception):pass
    clients={};prompts=[]
    class ReadOnly(llm_agent.LLMClient):
        def choose(self,prompt,labels):
            key=hashlib.sha256(f"{self.model}\n{prompt}\n{','.join(labels)}".encode()).hexdigest()
            prompts.append({'key':key,'cache_hit':key in self.cache,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()})
            if key not in self.cache:raise Miss(key)
            self.hits+=1;return self.cache[key]
    def forbidden(body):raise AssertionError('No HTTP')
    model='qwen2.5:3b';client=ReadOnly(model,cache_dir=str(ROOT/'results/llm_cache'),transport=forbidden)
    llm_agent._CLIENTS.clear();llm_agent._CLIENTS[model]=client
    cfg=Config().with_(llm_agents=(0,2,4),llm_model=model)
    def alarm(signum,frame):raise TimeoutError('probe60s')
    signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,60)
    result=None;error=None
    try:
        result=run_episode(cfg,'sem',0);result.pop('curve')
        status='completed'
    except Miss as e:status='blocked_missing_key';error=str(e)
    except Exception as e:status='failed';error=repr(e)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    print(json.dumps({'numpy':np.__version__,'python':sys.version,'sort_mode':mode,
       'disabled_features':os.environ.get('NPY_DISABLE_CPU_FEATURES'),'status':status,'cache_hits':client.hits,
       'http_calls':client.calls,'prompt_attempts':len(prompts),'first_prompt':prompts[0] if prompts else None,
       'first_missing':next((p for p in prompts if not p['cache_hit']),None),'result':result,'error':error}))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--child');args=parser.parse_args()
    if args.child:return child(args.child)
    sys.path.insert(0,str(ROOT/'scripts'))
    from hpc_runs import require_hpc,digest
    require_hpc();out=Path(os.environ['GOSC_OUTPUT_DIR'])
    caches={str(p):digest(p) for p in (ROOT/'results/llm_cache').glob('*.jsonl')}
    import shutil
    snapshot=out/'new_live_cache_snapshot';snapshot.mkdir()
    copied=[]
    for path in sorted((ROOT/'.local/ordered-live-20261019/results/llm_cache').glob('*.jsonl')):
        target=snapshot/path.name;shutil.copyfile(path,target)
        assert digest(target)==digest(path)
        copied.append({'source':path.relative_to(ROOT).as_posix(),'snapshot':target.relative_to(out).as_posix(),'sha256':digest(target)})
    (out/'new_live_cache_snapshot.json').write_text(json.dumps(copied,indent=2)+'\n')
    interpreters=[ROOT/'.venv/bin/python',ROOT/'.local/diagnostic-numpy-1.26.4/bin/python',ROOT/'.local/diagnostic-numpy-2.2.6/bin/python']
    results=[]
    for interpreter in interpreters:
        for mode in ['default','stable','quicksort','heapsort','mergesort']:
            env=os.environ.copy()
            r=subprocess.run([str(interpreter),str(Path(__file__).resolve()),'--child',mode],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
            row={'interpreter':str(interpreter),'exit_code':r.returncode,'stderr':r.stderr.decode()[-1200:]}
            if r.returncode==0:row.update(json.loads(r.stdout.decode()))
            else:row['stdout']=r.stdout.decode()[-1000:]
            results.append(row);print(str(interpreter.parent.parent.name),mode,row.get('status'),row.get('cache_hits'),flush=True)
    (out/'cache_sort_probe.json').write_text(json.dumps({'scope':'15 bounded diagnostic variants of first failed original mission, no acceptance by patched sorting','results':results,'cache_unchanged':all(digest(Path(p))==v for p,v in caches.items()),'http_calls':sum(r.get('http_calls',0) for r in results)},indent=2)+'\n')

if __name__=='__main__':main()
