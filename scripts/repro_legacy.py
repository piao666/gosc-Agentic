"""Run unmodified original entry points in an isolated workspace with capped pools.

Every returned job and every worker lifecycle event is retained before the legacy
entry point writes its final result. An exception aborts the stage, never a seed
replacement. The adapter changes parallelism and file locations, not algorithms.
"""
import argparse
import ast
import dataclasses
import importlib
import hashlib
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import resource
import signal
import sys
import time
import traceback

for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='1'

_LOCK=None
_EVENTS=None
_TIMEOUT=120


def serial(value):
    if dataclasses.is_dataclass(value):return serial(dataclasses.asdict(value))
    if isinstance(value,Path):return str(value)
    if isinstance(value,dict):return {str(k):serial(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [serial(v) for v in value]
    if hasattr(value,'tolist'):return serial(value.tolist())
    if hasattr(value,'item'):return serial(value.item())
    if isinstance(value,float) and not math.isfinite(value):return {'nonfinite_float':repr(value)}
    return value


def append(path,value,lock=None):
    line=(json.dumps(serial(value),allow_nan=False,separators=(',',':'))+'\n').encode()
    if lock:lock.acquire()
    try:
        with open(path,'ab',buffering=0) as stream:stream.write(line)
    finally:
        if lock:lock.release()


def initialize(lock,path,timeout):
    global _LOCK,_EVENTS,_TIMEOUT
    _LOCK=lock;_EVENTS=path;_TIMEOUT=timeout


def timed_job(envelope):
    function,index,argument=envelope
    start=time.monotonic();cpu=time.process_time();pid=os.getpid()
    append(_EVENTS,{'event':'start','index':index,'pid':pid,'function':function.__module__+'.'+function.__name__,
                    'argument_sha256':hashlib.sha256(json.dumps(serial(argument),sort_keys=True).encode()).hexdigest(),'time':time.time()},_LOCK)
    def timeout(signum,frame):raise TimeoutError('Original job exceeded '+str(_TIMEOUT)+' seconds')
    old=signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,_TIMEOUT)
    try:
        result=function(argument)
        value={'index':index,'status':'completed','result':result}
    except BaseException:
        value={'index':index,'status':'failed','error':traceback.format_exc()}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)
    value.update(pid=pid,wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
                 worker_process_max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    append(_EVENTS,{'event':'terminal','index':index,'pid':pid,'status':value['status'],'time':time.time()},_LOCK)
    return value


class CappedPool:
    """Legacy Pool-compatible subset, always at most two processes."""
    def __init__(self,processes=None,**unused):
        self.out=Path(os.environ['GOSC_OUTPUT_DIR'])
        self.out.mkdir(parents=True,exist_ok=True)
        self.invocation=int(os.environ.get('GOSC_POOL_COUNTER','0'))+1
        os.environ['GOSC_POOL_COUNTER']=str(self.invocation)
        self.log=self.out/f'pool-{self.invocation:03d}-jobs.jsonl'
        self.events=self.out/f'pool-{self.invocation:03d}-events.jsonl'
        self.context=mp.get_context('fork');self.lock=self.context.Lock()
        self.pool=self.context.Pool(2,initializer=initialize,
            initargs=(self.lock,str(self.events),int(os.environ.get('REPRO_JOB_TIMEOUT_SECONDS','120'))),maxtasksperchild=128)
        self.completed=0;self.closed=False
        self.configs=set()
        self.total=None;self.started=time.monotonic()
    def __enter__(self):return self
    def __exit__(self,kind,value,tb):
        if kind:self.pool.terminate()
        else:self.pool.close()
        self.pool.join();self.closed=True
        append(self.out/'pool-summary.jsonl',{'pool':self.invocation,'planned':self.total,'completed':self.completed,
            'elapsed_seconds':time.monotonic()-self.started,'workers':2,'normal_exit':kind is None})
    def _run(self,function,iterable,ordered):
        arguments=list(iterable);offset=self.total or 0;self.total=offset+len(arguments)
        def compact(value):
            value=serial(value)
            if isinstance(value,dict):
                if {'n_agents','max_steps','rates','llm_model'}<=set(value):
                    digest=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
                    if digest not in self.configs:
                        append(self.out/f'pool-{self.invocation:03d}-configs.jsonl',{'sha256':digest,'config':value});self.configs.add(digest)
                    return {'config_sha256':digest}
                return {k:compact(v) for k,v in value.items()}
            if isinstance(value,list):return [compact(v) for v in value]
            return value
        # The small immutable input catalog gives unstarted tasks explicit identity.
        append(self.out/'pool-plans.jsonl',{'pool':self.invocation,'function':function.__module__+'.'+function.__name__,
            'planned_this_call':len(arguments),'index_offset':offset,'arguments':[compact(a) for a in arguments]})
        envelopes=((function,i+offset,a) for i,a in enumerate(arguments))
        iterator=(self.pool.imap if ordered else self.pool.imap_unordered)(timed_job,envelopes,chunksize=1)
        for value in iterator:
            append(self.log,value)
            if value['status']!='completed':raise RuntimeError(value['error'])
            self.completed+=1
            if self.completed%25==0 or self.completed==self.total:
                progress={'pool':self.invocation,'planned':self.total,'completed':self.completed,
                    'elapsed_seconds':time.monotonic()-self.started,'workers':2}
                temp=self.out/'active_pool.json.tmp';temp.write_text(json.dumps(progress),encoding='utf-8');temp.replace(self.out/'active_pool.json')
            if self.completed%500==0:print(f'pool {self.invocation}: {self.completed}/{self.total}',flush=True)
            yield value['result']
    def map(self,function,iterable,chunksize=None):return list(self._run(function,iterable,True))
    def imap_unordered(self,function,iterable,chunksize=1):return self._run(function,iterable,False)
    def close(self):self.pool.close()
    def join(self):self.pool.join()



def invoke_entry(module):
    """Run the original CLI body after Pool interception, including scripts without main()."""
    entry = getattr(module, 'main', None)
    if callable(entry):
        return entry()
    source_path = Path(module.__file__)
    tree = ast.parse(source_path.read_text(encoding='utf-8'), filename=str(source_path))
    blocks = [node for node in tree.body if isinstance(node, ast.If)
              and isinstance(node.test, ast.Compare)
              and isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__'
              and len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq)
              and len(node.test.comparators) == 1
              and isinstance(node.test.comparators[0], ast.Constant)
              and node.test.comparators[0].value == '__main__']
    if len(blocks) != 1:
        raise RuntimeError('Expected one original CLI guard: ' + module.__name__)
    body = ast.Module(body=blocks[0].body, type_ignores=[])
    # Re-executing the whole module would undo the capped Pool patch. Run only its
    # unchanged original CLI body in the already imported/patched module globals.
    exec(compile(body, str(source_path), 'exec'), module.__dict__)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True);parser.add_argument('--module',required=True)
    parser.add_argument('--job-timeout',type=int,default=120);parser.add_argument('arguments',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    from hpc_runs import ROOT,require_hpc
    require_hpc()
    workspace=args.workspace.resolve()
    if ROOT/'.local' not in workspace.parents:raise ValueError('Legacy workspace must be isolated below project .local')
    if args.job_timeout not in [120,1800]:raise ValueError('Unregistered per-job timeout')
    os.environ['REPRO_JOB_TIMEOUT_SECONDS']=str(args.job_timeout)
    os.chdir(workspace);sys.path.insert(0,str(workspace))
    module=importlib.import_module(args.module)
    if hasattr(module,'Pool'):module.Pool=CappedPool
    sys.argv=[args.module,*(args.arguments[1:] if args.arguments[:1]==['--'] else args.arguments)]
    invoke_entry(module)


if __name__=='__main__':main()
