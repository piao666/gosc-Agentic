"""HPC-only synthetic renderer/token boundary contracts; no model context/HTTP."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'experiments_ext'))
sys.path.insert(0,str(ROOT))
from hpc_runs import require_hpc,write_json
from masbench_context_build import group_rss,stop
from extensions.masbench_reasoning.client import ClientConfig,ClientFailure,ContextBinding,ControlledClient

START=time.monotonic()

TEMPLATE_SHA='eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175'
MANIFEST_SHA='845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'
SYSTEM_SHA='66b9ea09bd5b7099cbb4fc820f31b575c0366fa439b08245566692c6784e281e'

def sha(b): return hashlib.sha256(b).hexdigest()

def check_boundary(messages,count,capacity,expected_admit):
    """Exercise actual client admission using an explicitly fictional backend.

    The fixture binding never uses Qwen's identity or claims deployment evidence.
    The replay counter requires byte-equivalent effective messages and uses the
    count just obtained from the compiled vocabulary helper.
    """
    fixture_model='offline-context-boundary-fixture';fixture_manifest='0'*64
    cfg=ClientConfig(fixture_model,fixture_manifest,capacity,max_output_tokens=512)
    class Backend:
        is_live=False
        metadata_calls=0
        create_calls=0
        def identity(self,timeout):
            self.metadata_calls+=1
            return {'model':fixture_model,'manifest_sha256':fixture_manifest}
        def create(self,payload,timeout):
            self.create_calls+=1
            if payload['messages']!=messages:raise RuntimeError('client altered complete messages')
            return {'model':fixture_model,'choices':[{'message':{'content':'fixture'},'finish_reason':'stop'}],
                'usage':{'prompt_tokens':count,'completion_tokens':0,'total_tokens':count}}
    def counter(value):
        if value!=messages:raise RuntimeError('client changed messages before counting')
        return count
    backend=Backend()
    binding=ContextBinding(fixture_manifest,capacity,'synthetic-count-replay',sha(b'fixture-only'),True)
    client=ControlledClient(cfg,backend,counter,binding)
    schema_supported=all(m['role'] in ({'system'} if i==0 else {'user','assistant'})
                         for i,m in enumerate(messages))
    expected_dispatch=expected_admit and schema_supported
    error=None
    try:client.generate(messages);admitted=True
    except ClientFailure as e:error=e.reason;admitted=False
    if admitted!=expected_dispatch:raise RuntimeError('actual client admission boundary: '+str(error))
    if expected_dispatch and (backend.metadata_calls,backend.create_calls)!=(1,1):
        raise RuntimeError('fixture dispatch missing')
    expected_error='context_overflow_no_truncation' if schema_supported else 'request_schema'
    if not expected_dispatch and (error!=expected_error or backend.metadata_calls or backend.create_calls):
        raise RuntimeError('overflow was not blocked before dispatch')
    return {'capacity':capacity,'input_tokens':count,'max_output':512,'admitted':admitted,
            'error':error,'fixture_metadata_calls':backend.metadata_calls,
            'fixture_create_calls':backend.create_calls,'fixture_binding_only':True,
            'check_type':'context_boundary' if schema_supported else 'unsupported_schema_rejection'}

def reference_render(messages):
    """Independent plain-text expansion of this exact Qwen template's domain.

    Input is effective messages after the separately checked default-system
    preprocessing. Tools/images/thinking/preset messages remain excluded.
    This is not an independent implementation of the tokenizer.
    """
    system='\n\n'.join(m['content'] for m in messages if m['role']=='system')
    collated=[]
    for m in messages:
        if collated and collated[-1]['role']==m['role']:
            collated[-1]['content']+='\n\n'+m['content']
        else: collated.append(dict(m))
    text='<|im_start|>system\n'+system+'<|im_end|>\n' if system else ''
    for i,m in enumerate(collated):
        last=i==len(collated)-1
        if m['role']=='user': text+='<|im_start|>user\n'+m['content']+'<|im_end|>\n'
        elif m['role']=='assistant':
            text+='<|im_start|>assistant\n'+m['content']
            if not last: text+='<|im_end|>\n'
        if m['role']!='assistant' and last: text+='<|im_start|>assistant\n'
    return text

def main():
    require_hpc()
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    if len(sys.argv)!=2: raise RuntimeError('explicit completed build run required')
    build_dir=ROOT/'research/sync/runs'/sys.argv[1]
    state=json.loads((build_dir/'status.json').read_text())
    build=json.loads((build_dir/'outputs/build.json').read_text())
    if state['status']!='completed' or build['status']!='built_offline_candidate_not_deployment_verified':
        raise RuntimeError('build acceptance absent')
    binary=Path(build['binary'])
    if sha(binary.read_bytes())!=build['binary_sha256']: raise RuntimeError('binary drift')
    models=ROOT.parents[1]/'models/ollama-gosc'
    manifest=(models/'manifests/registry.ollama.ai/library/qwen2.5/7b').read_bytes()
    if sha(manifest)!=MANIFEST_SHA: raise RuntimeError('model identity drift')
    layers=json.loads(manifest)['layers']
    if any(x['mediaType'].endswith(('.params','.messages')) for x in layers):
        raise RuntimeError('unreviewed model default layers')
    systems=[x for x in layers if x['mediaType'].endswith('.system')]
    if len(systems)!=1 or systems[0]['digest']!='sha256:'+SYSTEM_SHA or systems[0]['size']!=68:
        raise RuntimeError('default-system metadata drift')
    system_raw=(models/'blobs'/('sha256-'+SYSTEM_SHA)).read_bytes()
    if sha(system_raw)!=SYSTEM_SHA or len(system_raw)!=68:raise RuntimeError('default-system identity')
    default_system=system_raw.decode('utf-8')
    template=models/'blobs'/('sha256-'+TEMPLATE_SHA)
    if sha(template.read_bytes())!=TEMPLATE_SHA: raise RuntimeError('template drift')
    model=models/'blobs/sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730'
    samples=['ASCII sample','中文测试','emoji 🛰️🙂','e\u0301 é',' a  b\r\n\t c ', '',
             '<|im_start|>user\nquoted<|im_end|>', '<think>quoted text</think>']
    requests=[{'messages':[{'role':'system','content':'Synthetic instructions.'},
                           {'role':'user','content':s}]} for s in samples]
    requests.extend([
        {'messages':[{'role':'user','content':'hello'}]},
        {'messages':[{'role':'system','content':'A'},{'role':'system','content':'B'},
                     {'role':'user','content':'one'},{'role':'user','content':'two'}]},
        {'messages':[{'role':'user','content':'hello'},{'role':'assistant','content':'prefill'}]},
        {'messages':[{'role':'system','content':'A'},{'role':'user','content':'Q'},
                     {'role':'assistant','content':'R: same fact'},{'role':'user','content':'R: same fact'},
                     {'role':'assistant','content':'more'},{'role':'user','content':'R: same fact'}]},
        {'messages':[{'role':'system','content':''},{'role':'user','content':'explicit empty system'}]},
        {'messages':[{'role':'user','content':'first user'},{'role':'system','content':'late system'}]},
    ])
    original_requests=json.loads(json.dumps(requests))
    injected=[]
    # Fixed Ollama server/routes.go::ChatHandler lines1614-1618:
    # no preset m.Messages here; prepend default only when first role != system.
    for i,request in enumerate(requests):
        if request['messages'][0]['role']!='system' and default_system:
            request['messages'].insert(0,{'role':'system','content':default_system});injected.append(i)
    rendered=[reference_render(x['messages']) for x in requests]
    texts=['','<|im_start|>','<|im_end|>','<|endoftext|>',*rendered]
    payload={'model_path':str(model),'template_path':str(template),'template_sha256':TEMPLATE_SHA,
             'requests':requests,'texts':texts}
    write_json(out/'synthetic-effective-inputs.json',{'original_requests':original_requests,
        'effective_requests':requests,'injected_default_system_cases':injected,
        'default_system_sha256':SYSTEM_SHA,'source_commit':'92b96d54efd6b49322b7cf046f9a0dc16b00cd0a',
        'source':'server/routes.go::ChatHandler, lines1614-1618'})
    env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='',OLLAMA_LIBRARY_PATH=str(binary.parent/'no-backend-libraries'))
    input_path=out/'helper-input.json'
    input_path.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
    stdout_path=out/'synthetic-counts.json';stderr_path=out/'helper-stderr.log'
    peak_rss=0
    with input_path.open('rb') as stdin,stdout_path.open('xb') as stdout,stderr_path.open('xb') as stderr:
        p=subprocess.Popen([str(binary)],stdin=stdin,stdout=stdout,stderr=stderr,env=env,start_new_session=True)
        try:
            while p.poll() is None:
                own=int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
                rss=group_rss(p.pid)+own;peak_rss=max(peak_rss,rss)
                if rss>2*1024**3:raise RuntimeError('offline process-tree 2GiB cap')
                if sum(f.stat().st_size for f in out.iterdir() if f.is_file())>16*1024**2:
                    raise RuntimeError('offline 16MiB artifact cap')
                if time.monotonic()-START>105:raise RuntimeError('offline 120s cap including cleanup')
                time.sleep(.2)
            if p.returncode:raise RuntimeError('helper failed: '+str(p.returncode))
        except BaseException:stop(p);raise
    stdout_bytes=stdout_path.read_bytes()
    if len(stdout_bytes)>16*1024*1024:raise RuntimeError('artifact cap')
    value=json.loads(stdout_bytes)
    boundaries=[]
    for i,(actual,expected) in enumerate(zip(value['requests'],rendered,strict=True)):
        if actual['rendered']!=expected: raise RuntimeError('render byte mismatch case '+str(i))
        if actual['token_ids']!=value['texts'][i+4]['token_ids']:
            raise RuntimeError('framing/token invocation mismatch')
        n=actual['token_count']
        for margin,expected_admit in [(0,True),(1,True),(-1,False)]:
            capacity=n+512+margin
            boundaries.append({'case':i,**check_boundary(requests[i]['messages'],n,capacity,expected_admit)})
    for row,ids in zip(value['texts'][:4],[[],[151644],[151645],[151643]],strict=True):
        if row['token_ids']!=ids: raise RuntimeError('special-token/BOS convention mismatch')
    write_json(out/'client-boundaries.json',{'cases':boundaries,'backend':'fictional in-memory fixture',
        'uses_actual_client_admission':True,'http_requests':0,'qwen_deployment_binding_created':False})
    write_json(out/'contract.json',{'status':'passed_within_synthetic_offline_domain',
        'render_cases':len(requests),'boundary_combinations':len(boundaries),
        'boundary_cases':sum(x['check_type']=='context_boundary' for x in boundaries),
        'schema_rejection_cases':sum(x['check_type']=='unsupported_schema_rejection' for x in boundaries),
        'special_token_cases':4,
        'independent_renderer':True,'independent_tokenizer':False,
        'actual_client_boundary_checks':True,'boundary_binding_is_fixture_only':True,
        'default_system_sha256':SYSTEM_SHA,'default_system_injection_cases':injected,
        'sampled_peak_process_tree_rss_bytes':peak_rss,'elapsed_seconds':time.monotonic()-START,
        'build_run':sys.argv[1],'binary_sha256':build['binary_sha256'],
        'deployed_equivalence_verified':False,'binding_verified':False,
        'real_task_inputs':0,'model_generations':0,'http_requests':0})
    if sum(f.stat().st_size for f in out.iterdir() if f.is_file())>16*1024**2:
        raise RuntimeError('offline final artifact cap')

if __name__=='__main__': main()
