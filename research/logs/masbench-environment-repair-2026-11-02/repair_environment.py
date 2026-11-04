"""HPC-only infrastructure repair. Never generates text, loads models or runs benchmark tasks."""
import argparse
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc,write_json

MODELS={
    'qwen2.5:3b':'357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b',
    'llama3.2:3b':'a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72',
    'qwen2.5:7b':'845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'}
BASE='http://127.0.0.1:11434'
STORE=ROOT.parents[1]/'models/ollama-gosc'
ENV=ROOT/'.local/envs/masbench-reasoning-v1'
UV=Path.home()/'.local/bin/uv'
REQ=ROOT/'research/benchmarks/masbench_reasoning_requirements_v1.in'

def api(path,body=None,timeout=15):
    payload=None if body is None else json.dumps(body).encode()
    request=urllib.request.Request(BASE+path,payload,{'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=timeout) as response:return json.load(response)

def command(out,name,args,timeout):
    print('command:',name,flush=True)
    p=subprocess.run([str(x) for x in args],cwd=ROOT,capture_output=True,timeout=timeout)
    (out/(name+'.stdout')).write_bytes(p.stdout)
    (out/(name+'.stderr')).write_bytes(p.stderr)
    write_json(out/(name+'.command.json'),{'command':[str(x) for x in args],'exit_code':p.returncode})
    if p.returncode:raise RuntimeError(name+' failed; preserve command/stdout/stderr')
    return p.stdout

def original_packages():
    return {d.metadata['Name']:d.version for d in importlib.metadata.distributions()}

def plan(out):
    assert api('/api/version')['version']=='0.11.11'
    assert not api('/api/ps').get('models'), 'A model is active; do not interfere'
    manifest_rows=[];blobs={}
    for model,expected in MODELS.items():
        name,tag=model.split(':')
        url='https://registry.ollama.ai/v2/library/'+name+'/manifests/'+tag
        request=urllib.request.Request(url,headers={'Accept':'application/vnd.docker.distribution.manifest.v2+json'})
        with urllib.request.urlopen(request,timeout=30) as response:data=response.read(1024*1024)
        actual=hashlib.sha256(data).hexdigest()
        if actual!=expected:raise RuntimeError('Registry manifest changed: '+model+' '+actual)
        manifest=json.loads(data)
        write_json(out/(model.replace(':','_')+'.manifest.json'),manifest)
        for layer in [manifest['config']]+manifest['layers']:
            assert layer['digest'].startswith('sha256:')
            blobs[layer['digest']]=layer['size']
        manifest_rows.append({'model':model,'manifest_sha256':actual,'registry_url':url,
                              'declared_bytes':sum(x['size'] for x in [manifest['config']]+manifest['layers'])})
    total=sum(blobs.values())
    assert total<=10*1024**3, 'Model bytes exceed bounded repair plan'
    space=os.statvfs(STORE)
    assert space.f_bavail*space.f_frsize>total+1024**3, 'Insufficient visible filesystem capacity'
    result={'models':manifest_rows,'unique_blob_bytes':total,'declared_max_new_model_bytes':10*1024**3,
            'dependency_environment':str(ENV),'dependency_max_seconds':600,'model_max_seconds':3600,
            'quota_available':False,'quota_note':'statvfs is not account quota; EDQUOT stops; no automatic cleanup',
            'original_project_packages':original_packages(),'inference_requested':False,'model_load_requested':False}
    write_json(out/'repair_plan.json',result)
    print(json.dumps(result),flush=True)

def dependencies(out):
    before=original_packages()
    if ENV.exists():raise RuntimeError('Target environment already exists; inspect instead of overwriting')
    ENV.parent.mkdir(parents=True,exist_ok=True)
    command(out,'uv_version',[UV,'--version'],10)
    command(out,'create_venv',[UV,'venv','--python',sys.executable,str(ENV)],30)
    lock=out/'requirements-reasoning-linux.lock.txt'
    command(out,'compile_lock',[UV,'pip','compile',str(REQ),'--python',str(ENV/'bin/python'),
        '--generate-hashes','--no-emit-index-url','--output-file',str(lock)],150)
    command(out,'install_locked',[UV,'pip','sync','--python',str(ENV/'bin/python'),
        '--require-hashes','--only-binary',':all:',str(lock)],300)
    command(out,'dependency_check',[UV,'pip','check','--python',str(ENV/'bin/python')],30)
    code="""import importlib.metadata as m,json,sys
import openai,httpx,requests,dotenv
client=openai.OpenAI(api_key='local-placeholder',base_url='http://127.0.0.1:11434/v1',max_retries=0,timeout=1)
client.close()
print(json.dumps({'python':sys.executable,'version':sys.version,'packages':{d.metadata['Name']:d.version for d in m.distributions()},'inference_requested':False}))
"""
    imported=command(out,'imports',[ENV/'bin/python','-c',code],30)
    assert before==original_packages(), 'Original GOSC environment metadata changed'
    write_json(out/'dependencies_ready.json',{'environment':str(ENV),'lock_sha256':hashlib.sha256(lock.read_bytes()).hexdigest(),
        'original_gosc_packages_before':before,'original_gosc_packages_after':original_packages(),
        'import_check':json.loads(imported),'benchmark_executed':False,'inference_requested':False})
    print('Reasoning dependencies installed and checked in isolated environment; no inference.',flush=True)

def models(out):
    plan(out)
    existing={entry['name']:entry for entry in api('/api/tags').get('models',[])}
    assert all(name in MODELS and value['digest']==MODELS[name] for name,value in existing.items()), 'Unexpected registry state; preserve and inspect'
    for model,expected in MODELS.items():
        if model in existing:
            print('Reusing restored matching manifest',model,flush=True)
            continue
        print('Restoring',model,flush=True)
        request=urllib.request.Request(BASE+'/api/pull',json.dumps({'model':model,'stream':True}).encode(),
                                       {'Content-Type':'application/json'})
        last=None;complete=False
        with urllib.request.urlopen(request,timeout=300) as response,(out/(model.replace(':','_')+'.pull.jsonl')).open('w') as log:
            for line in response:
                value=json.loads(line)
                percent=int(100*value.get('completed',0)/max(value.get('total',1),1))
                key=(value.get('status'),value.get('digest'),percent)
                if key!=last:
                    log.write(json.dumps(value)+'\n');log.flush()
                    print(model,value.get('status'),percent,flush=True);last=key
                if value.get('error'):raise RuntimeError(value['error'])
                if value.get('status')=='success':complete=True
        assert complete, 'Pull stream ended without success'
        tagged={entry['name']:entry for entry in api('/api/tags')['models']}
        assert tagged[model]['digest']==expected, 'Restored manifest differs from historical identity'
    verified={};blobs={};licenses={}
    for model,expected in MODELS.items():
        name,tag=model.split(':')
        manifest_path=STORE/'manifests/registry.ollama.ai/library'/name/tag
        raw=manifest_path.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
        manifest=json.loads(raw)
        for layer in [manifest['config']]+manifest['layers']:
            blobs[layer['digest']]=layer
        model_licenses=[]
        for layer in manifest['layers']:
            if 'license' in layer['mediaType']:
                content=(STORE/'blobs'/layer['digest'].replace(':','-')).read_bytes()
                target=out/(model.replace(':','_')+'.'+layer['digest'].split(':',1)[1][:12]+'.license.txt')
                target.write_bytes(content);model_licenses.append({'path':target.name,'sha256':hashlib.sha256(content).hexdigest()})
        licenses[model]=model_licenses
        verified[model]={'manifest_sha256':expected,'manifest_path':str(manifest_path)}
    for digest,layer in blobs.items():
        path=STORE/'blobs'/digest.replace(':','-')
        assert path.is_file() and path.stat().st_size==layer['size'], str(path)
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        assert actual==digest.split(':',1)[1], 'Blob hash mismatch'
        layer['verified_sha256']=actual
    assert not api('/api/ps').get('models'), 'Unexpected model load'
    write_json(out/'models_ready.json',{'models':verified,'blobs':blobs,'licenses':licenses,
        'tags':api('/api/tags'),'service_version':api('/api/version'),'loaded':api('/api/ps'),
        'inference_requested':False,'model_capability':'Pending; no loading or generation performed'})
    print('Three historical model identities restored; every blob SHA256 checked; no model loaded.',flush=True)

def main():
    require_hpc()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['plan','dependencies','models'])
    parser.add_argument('--deadline-utc',help='Explicit newly user-authorized absolute maintenance deadline, without rewriting old runs')
    args=parser.parse_args()
    def stop(signum,frame):raise TimeoutError('Bounded infrastructure repair deadline')
    signal.signal(signal.SIGALRM,stop)
    seconds=600
    if args.action=='models':
        seconds=3600
        original=ROOT/'research/sync/runs/hpc-masbench-model-restore-20261102/status.json'
        if original.is_file() and not args.deadline_utc:
            started=json.loads(original.read_text()).get('started_at')
            if started:
                deadline=datetime.datetime.fromisoformat(started).timestamp()+3600
                seconds=int(deadline-time.time())
                if seconds<=0:raise TimeoutError('Original shared 3600s restoration budget exhausted')
        if args.deadline_utc:
            seconds=int(datetime.datetime.fromisoformat(args.deadline_utc).timestamp()-time.time())
            if seconds<=0 or seconds>1800:raise TimeoutError('Explicit remaining-model deadline must be within new approved 1800s window')
    signal.alarm(seconds)
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    {'plan':plan,'dependencies':dependencies,'models':models}[args.action](out)
if __name__=='__main__':main()
