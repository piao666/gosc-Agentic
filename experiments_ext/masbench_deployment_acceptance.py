"""Bounded real-service synthetic acceptance; temporary context then restore."""
from pathlib import Path
import hashlib,http.client,json,os,signal,socket,subprocess,sys,threading,time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'experiments_ext')]
from hpc_runs import require_hpc,write_json
from masbench_context_build import group_rss
from masbench_context_offline_contract import MANIFEST_SHA,TEMPLATE_SHA,SYSTEM_SHA
BASE='/tmp/gosc-hpc-masbench-context-build-v3-20261116'
MODEL='qwen2.5:7b';START=time.monotonic();OUT=None
R={'status':'running','posts':{'debug':0,'generate':0,'unload':0},'gets':0,
   'real_task_inputs':0,'restored_original_service':False,'native_immediate_idle_verified':False,
   'production_driver_binding_verified':False,'universal_token_id_equivalence_verified':False}
env0=None;service_pid=None;monitor_stop=threading.Event();resource_error=[]
active_conn=None
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save():write_json(OUT/'acceptance.json',R)
def elapsed():return time.monotonic()-START
def check(cleanup=False):
    if elapsed()>(480 if cleanup else 350):raise RuntimeError('wall deadline')
    if resource_error and not cleanup:raise RuntimeError(resource_error[0])
    if sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())>16*1024**2:
        raise RuntimeError('artifact cap')
def reserve(category=None,cleanup=False):
    check(cleanup)
    if category:
        if R['posts'][category]>=2:raise RuntimeError('POST category cap')
        R['posts'][category]+=1
    else:
        if R['gets']>=40:raise RuntimeError('GET cap')
        R['gets']+=1
    save()
def request(path,body=None,category=None,cleanup=False):
    global active_conn
    reserve(category,cleanup)
    conn=http.client.HTTPConnection('127.0.0.1',11434,timeout=min(60,max(1,(480 if cleanup else 420)-elapsed())))
    active_conn=conn
    try:
        conn.request('GET' if body is None else 'POST',path,
                     body=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        res=conn.getresponse();raw=res.read(2*1024**2+1)
        if res.status!=200 or len(raw)>2*1024**2:raise RuntimeError('HTTP status/size '+str(res.status))
        return json.loads(raw)
    finally:conn.close();active_conn=None
def processes():
    rows=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            a=(p/'cmdline').read_bytes().decode().strip('\0').split('\0')
            if a and ('ollama' in Path(a[0]).name or '--ctx-size' in a):
                rows.append((int(p.name),a))
        except (OSError,UnicodeError):pass
    return rows
def runners():
    return {pid for pid,a in processes() if '--ctx-size' in a or 'runner' in a[1:3]}
def stop_service():
    global service_pid
    if not service_pid:return
    if runners():raise RuntimeError('runner remains before service stop')
    os.kill(service_pid,signal.SIGTERM)
    for _ in range(50):
        if not Path('/proc',str(service_pid)).exists():service_pid=None;return
        try:
            if Path('/proc',str(service_pid),'stat').read_text().split(') ')[1].startswith('Z'):
                service_pid=None;return
        except FileNotFoundError:service_pid=None;return
        time.sleep(.1)
    raise RuntimeError('service did not stop')
def start_service(env):
    global service_pid
    state=ROOT/'.local/ollama'
    binary=state/'runtime/0.11.11/bin/ollama'
    with (state/'service.log').open('ab') as f:
        p=subprocess.Popen([str(binary),'serve'],env=env,stdin=subprocess.DEVNULL,
            stdout=f,stderr=f,start_new_session=True)
    service_pid=p.pid
    write_json(state/'service.json',{'pid':p.pid,'binary':str(binary),'bind':'127.0.0.1:11434',
        'models':env['OLLAMA_MODELS'],'version':'0.11.11','started_at_unix':time.time(),
        'log':str(state/'service.log'),'auto_restart_after_container_reboot':False})
    for _ in range(10):
        try:
            if request('/api/version',cleanup=True).get('version')=='0.11.11':return
        except (ConnectionError,OSError):time.sleep(.5)
    raise RuntimeError('restart readiness failed')
def monitor():
    while not monitor_stop.wait(.5):
        try:
            rss=group_rss(service_pid) if service_pid else 0
            gpu=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],timeout=3).decode().strip())*1024**2
            R['sampled_peak_service_rss_bytes']=max(R.get('sampled_peak_service_rss_bytes',0),rss)
            R['sampled_peak_gpu_bytes']=max(R.get('sampled_peak_gpu_bytes',0),gpu)
            if rss>16*1024**3 or gpu>16*1024**3 or elapsed()>350:
                resource_error.append('16GiB RAM/GPU threshold')
                if active_conn and active_conn.sock:active_conn.sock.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            resource_error.append('resource monitor failure: '+type(e).__name__)
def unload():
    old=runners()
    value=request('/api/chat',{'model':MODEL,'messages':[],'keep_alive':0,'stream':False},'unload',True)
    for _ in range(8):
        ps=request('/api/ps',cleanup=True)
        if not ps.get('models') and not (old & runners()):
            R.setdefault('unload_barriers',[]).append({'response':value,'old_runner_pids':sorted(old),'ps_empty':True,'old_runner_exited':True});save();return
        time.sleep(.5)
    raise RuntimeError('unload barrier not verified')
def main():
    global OUT,env0,service_pid,active_conn
    require_hpc();OUT=Path(os.environ['GOSC_OUTPUT_DIR']);save()
    rows=processes();servers=[(p,a) for p,a in rows if a[1:]==['serve']]
    if len(servers)!=1 or runners():raise RuntimeError('service identity/idle precondition')
    service_pid=servers[0][0]
    expected=ROOT/'.local/ollama/runtime/0.11.11/bin/ollama'
    if Path('/proc',str(service_pid),'exe').resolve()!=expected:raise RuntimeError('service executable identity')
    env0=dict(x.split('=',1) for x in Path('/proc',str(service_pid),'environ').read_bytes().decode().split('\0') if '=' in x)
    if env0.get('OLLAMA_CONTEXT_LENGTH')!='1024' or env0.get('OLLAMA_NUM_PARALLEL')!='1':raise RuntimeError('original service configuration drift')
    if request('/api/ps').get('models'):raise RuntimeError('resident model before test')
    if request('/api/version').get('version')!='0.11.11':raise RuntimeError('version drift')
    if not any(x.get('name')==MODEL and x.get('digest')==MANIFEST_SHA for x in request('/api/tags')['models']):raise RuntimeError('model identity drift')
    models=ROOT.parents[1]/'models/ollama-gosc'
    manifest=models/'manifests/registry.ollama.ai/library/qwen2.5/7b'
    if sha(manifest)!=MANIFEST_SHA:raise RuntimeError('manifest drift')
    build=json.loads((ROOT/'research/sync/runs/hpc-masbench-cpp17-helper-build-20261116/outputs/build.json').read_text())
    offline=json.loads((ROOT/'research/sync/runs/hpc-masbench-context-offline-contract-v3-20261117/outputs/contract.json').read_text())
    helper=Path(build['binary'])
    if sha(helper)!=build['binary_sha256'] or offline['status']!='passed_within_synthetic_offline_domain':raise RuntimeError('offline prerequisite')
    template=models/'blobs'/('sha256-'+TEMPLATE_SHA)
    if sha(template)!=TEMPLATE_SHA or sha(models/'blobs'/('sha256-'+SYSTEM_SHA))!=SYSTEM_SHA:raise RuntimeError('template/system drift')
    small=[{'role':'system','content':'Synthetic deployment test. Answer exactly OK.'},{'role':'user','content':'Answer exactly OK.'}]
    long=[small[0],{'role':'user','content':'synthetic evidence alpha beta gamma. '*400},
        {'role':'assistant','content':'Synthetic evidence acknowledged.'},small[1]]
    payload={'model_path':str(models/'blobs/sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730'),
        'template_path':str(template),'template_sha256':TEMPLATE_SHA,'requests':[{'messages':small},{'messages':long}],'texts':[]}
    e=dict(os.environ,CUDA_VISIBLE_DEVICES='',OLLAMA_LIBRARY_PATH=str(helper.parent/'no-backend-libraries'))
    p=subprocess.run([str(helper)],input=json.dumps(payload).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=e,timeout=30)
    (OUT/'offline-stderr.log').write_bytes(p.stderr)
    if p.returncode:raise RuntimeError('offline helper failed')
    counts=json.loads(p.stdout)['requests'];write_json(OUT/'inputs-and-counts.json',{'messages':[small,long],'counts':counts})
    if not (1024<counts[1]['token_count']+512<=32768):raise RuntimeError('synthetic length precondition')
    original=json.loads((ROOT/'.local/ollama/service.json').read_text())
    write_json(OUT/'original-service-metadata.json',{k:original.get(k) for k in ['pid','binary','bind','models','version']})
    R.update(original_context=1024,test_context=32768,helper_sha256=build['binary_sha256'],old_service_pid=service_pid)
    thread=None
    try:
        stop_service();testenv=dict(env0,OLLAMA_CONTEXT_LENGTH='32768')
        start_service(testenv);R['test_service_pid']=service_pid
        thread=threading.Thread(target=monitor,daemon=True);thread.start()
        render=[]
        for i,msgs in enumerate([small,long]):
            value=request('/api/chat',{'model':MODEL,'messages':msgs,'_debug_render_only':True,'stream':False,
                'options':{'num_thread':2}},'debug')
            write_json(OUT/f'debug-{i}.json',value)
            actual=value['_debug_info']['rendered_template']
            if actual!=counts[i]['rendered']:raise RuntimeError('deployed render mismatch '+str(i))
            render.append(True)
        R['render_matches']=render
        ps=request('/api/ps');write_json(OUT/'loaded-model.json',ps)
        model=next(x for x in ps['models'] if x['name']==MODEL)
        R['observed_effective_context']=model.get('context_length')
        if model.get('context_length')!=32768 or model.get('size_vram',0)<=0:raise RuntimeError('effective context/GPU not verified')
        R['runner_context_args']=[{'pid':pid,'ctx_size':a[a.index('--ctx-size')+1]} for pid,a in processes() if '--ctx-size' in a]
        response=request('/v1/chat/completions',{'model':MODEL,'messages':long,'temperature':0,'max_tokens':16,'stream':False},'generate')
        write_json(OUT/'normal-response.json',response)
        if response['choices'][0]['finish_reason']!='stop' or response['usage']['prompt_tokens']!=counts[1]['token_count']:
            raise RuntimeError('normal finish/count mismatch')
        R['normal_usage_matches']=True;R['normal_usage']=response['usage'];save()
        reserve('generate');conn=http.client.HTTPConnection('127.0.0.1',11434,timeout=60);active_conn=conn
        try:
            conn.request('POST','/v1/chat/completions',json.dumps({'model':MODEL,'messages':[{'role':'system','content':'Follow the synthetic counting instruction. Produce one integer per line.'},
                {'role':'user','content':'List the integers from 1 to 10000, one per line.'}],'temperature':0,'max_tokens':512,'stream':True}),{'Content-Type':'application/json'})
            resp=conn.getresponse()
            if resp.status!=200:raise RuntimeError('cancel request HTTP error')
            observed=False
            for _ in range(64):
                check()
                line=resp.readline(65536)
                if line.startswith(b'data: ') and b'[DONE]' not in line:
                    value=json.loads(line[6:]);choice=value['choices'][0]
                    if choice.get('finish_reason'):raise RuntimeError('request finished before cancellation')
                    if choice.get('delta',{}).get('content'):
                        observed=True;break
            if not observed:raise RuntimeError('no content before cancellation')
            R['cancel_content_observed_before_disconnect']=True
            if conn.sock:conn.sock.shutdown(socket.SHUT_RDWR)
            resp.close()
        finally:conn.close();active_conn=None
        R['cancel_disconnect_performed']=True;save();unload()
        R['status']='limited_deployment_checks_passed_native_idle_unobserved'
    except BaseException as e:
        R.update(status='failed',error=type(e).__name__+': '+str(e));raise
    finally:
        try:
            if runners():unload()
            monitor_stop.set()
            if thread:thread.join(timeout=4)
            stop_service();start_service(env0)
            R['restored_original_service']=True;R['restored_service_pid']=service_pid
        except BaseException as e:R['cleanup_error']=type(e).__name__+': '+str(e)
        R['elapsed_seconds']=elapsed();save()
    if not R['restored_original_service']:raise RuntimeError('original service restoration failed')
if __name__=='__main__':main()
