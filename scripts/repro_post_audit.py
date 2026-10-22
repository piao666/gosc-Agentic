"""Post-campaign audit; execute through hpc_runs on HPC only."""
import collections
import hashlib
import json
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key] = '1'
sys.path.insert(0, str(ROOT/'scripts'))
from hpc_runs import require_hpc, digest

WORK = ROOT/'.local/ordered-reproduction-20261019'
RUNS = ROOT/'research/sync/runs'
METRICS = ['completion_time','completed','found','symbols','bits','delivered_bits',
           'dl_symbols','false_declarations','llm_decisions','llm_fallbacks','llm_agree']

def save(out, name, value):
    (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def read(path):
    return json.loads(path.read_text())

def lines(path):
    with path.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def describe(values):
    values = sorted(float(v) for v in values if v is not None)
    if not values:
        return {'n':0}
    def q(p):
        x=(len(values)-1)*p; a=int(x); b=min(a+1,len(values)-1)
        return values[a]+(values[b]-values[a])*(x-a)
    return {'n':len(values),'sum':sum(values),'mean':statistics.mean(values),
            'median':statistics.median(values),'p95':q(.95),'min':values[0],'max':values[-1]}

def expected():
    result=[]
    for name in ['llm_mixed.jsonl','llm_extended.jsonl']:
        for row in lines(ROOT/'results'/name):
            team=row['team']
            model=row.get('model') or ('llama3.2:3b' if team=='mixed_llama' else 'qwen2.5:7b' if team=='mixed_qwen7b' else 'qwen2.5:3b')
            result.append((name,row,model))
    return result

def artifact_audit(out):
    pipeline=read(RUNS/'hpc-ordered-resume-20261020/outputs/pipeline_status.json')
    prefix=pipeline['skipped_completed']
    rows=prefix+pipeline['stages']
    report=[]; failures=[]; comparisons=[]
    for entry in rows:
        rid=entry['run_id']; run=RUNS/rid; state=read(run/'status.json')
        artifact=read(run/'artifacts.json'); bad=[]; total=0
        for item in artifact['files']:
            path=(run/item['path']).resolve()
            if run.resolve() not in path.parents or path.is_symlink():
                bad.append({'path':item['path'],'reason':'unsafe_path'}); continue
            if not path.is_file():
                bad.append({'path':item['path'],'reason':'missing'}); continue
            total+=path.stat().st_size
            if path.stat().st_size!=item['size'] or digest(path)!=item['sha256']:
                bad.append({'path':item['path'],'reason':'hash_or_size'})
        if entry in prefix:
            for key,name in [('status_sha256','status.json'),('artifacts_sha256','artifacts.json')]:
                if digest(run/name)!=entry[key]:
                    bad.append({'path':name,'reason':'frozen_prefix_modified'})
        audit=read(run/'outputs/stage_audit.json') if (run/'outputs/stage_audit.json').exists() else None
        pools=list(lines(run/'outputs/pool-summary.jsonl')) if (run/'outputs/pool-summary.jsonl').exists() else []
        if pools:
            if any(p['planned']!=p['completed'] or not p['normal_exit'] for p in pools):
                bad.append({'reason':'pool_not_complete'})
            if audit and sum(p['completed'] for p in pools)!=audit['raw_original_job_results']:
                bad.append({'reason':'pool_audit_count_mismatch'})
        integrity=read(run/'outputs/input_integrity.json') if (run/'outputs/input_integrity.json').exists() else None
        if integrity:
            before=integrity.get('before',{}); after=integrity.get('after',{})
            if before and after and before!=after:
                bad.append({'reason':'protected_input_changed'})
        comp=read(run/'outputs/original_comparison.json') if (run/'outputs/original_comparison.json').exists() else {}
        for f in comp.get('files',[]):
            short={k:v for k,v in f.items() if k not in ['mismatches','keys_without_scientific_metrics']}
            fields=collections.Counter()
            for mismatch in f.get('mismatches',[]):
                fields.update(mismatch.get('fields',[]))
            short['mismatch_fields']=dict(fields)
            short['run_id']=rid
            comparisons.append(short)
        item={'run_id':rid,'execution_status':state['status'],'exit_code':state['exit_code'],
              'artifact_files':len(artifact['files']),'artifact_bytes':total,'integrity_issues':bad,
              'pools':pools,'lifecycle_audit':audit,
              'scientific_status':'historical_comparison_separate_from_execution'}
        report.append(item)
        failures.extend([{'run_id':rid,**b} for b in bad])
    # Parent artifact index includes queue outputs, not child directories.
    parent=RUNS/'hpc-ordered-resume-20261020'
    for item in read(parent/'artifacts.json')['files']:
        if digest(parent/item['path'])!=item['sha256']:
            failures.append({'run_id':parent.name,'path':item['path'],'reason':'parent_artifact_hash'})
    protected=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only','--','gosc','experiments','tests','results','LICENSE']).decode().splitlines()
    if protected: failures.append({'reason':'protected_git_diff','files':protected})
    save(out,'stage_inventory.json',report)
    save(out,'comparison_inventory.json',comparisons)
    save(out,'artifact_integrity.json',{'status':'verified' if not failures else 'failed','issues':failures,
         'child_runs':len(report),'files_checked':sum(x['artifact_files'] for x in report),
         'bytes_checked':sum(x['artifact_bytes'] for x in report),'parent_artifact_checked':True,
         'scientific_equivalence_implied':False})
    return not failures

def llm_audit(out):
    run=RUNS/'resume-live-llm-20261020/outputs'
    missions=list(lines(run/'live_episodes.jsonl'))
    events=list(lines(run/'http_attempts.jsonl'))
    refs=expected(); issues=[]; groups=collections.defaultdict(list); evgroups=collections.defaultdict(list)
    if len(missions)!=len(refs): issues.append('mission_count')
    embedded=[]
    canonical=lambda row: json.dumps(row,sort_keys=True,separators=(',',':'))
    mismatches=collections.Counter(); roles=collections.Counter()
    options={'temperature':0,'seed':0,'num_predict':12,'num_ctx':1024}
    for index,row in enumerate(missions):
        source,ref,model=refs[index]
        if any([row['index']!=index,row['source_file']!=source,row['team']!=ref['team'],row['scheme']!=ref['scheme'],row['seed']!=ref['seed'],row['model']!=model]):
            issues.append('mission_identity_'+str(index))
        roles['planner_only' if row['team']=='planner' else 'mixed_llm']+=1
        if row['result'].get('llm_fallbacks',0): issues.append('fallback_'+str(index))
        embedded.extend(row.get('inference_events',[]))
        if len(row.get('inference_events',[]))!=row['http_calls']: issues.append('http_count_'+str(index))
        mismatches.update(row.get('reference_mismatches',[]))
        groups[(source,row['team'],model,row['scheme'])].append(row)
    if [canonical(x) for x in embedded]!=[canonical(x) for x in events]:
        issues.append('embedded_vs_transport_event_stream')
    for event in events:
        evgroups[event.get('model')].append(event)
        if event.get('options')!=options: issues.append('inference_options')
    table=[]
    for key,rows in groups.items():
        counts=collections.Counter(r['seed'] for r in rows)
        table.append({'source_file':key[0],'team':key[1],'model':key[2],'scheme':key[3],
            'missions':len(rows),'seeds':sorted(counts),'duplicate_seed_entries':{str(k):v for k,v in counts.items() if v>1},
            'completed_missions':sum(bool(r['result'].get('completed')) for r in rows),
            'historical_mismatch_missions':sum(bool(r.get('reference_mismatches')) for r in rows),
            'http_attempts':sum(r['http_calls'] for r in rows),'cache_hits':sum(r['cache_hits'] for r in rows),
            'fallbacks':sum(r['result'].get('llm_fallbacks',0) for r in rows),
            'mission_wall_seconds':describe([r['wall_s'] for r in rows]),
            'metrics':{k:describe([r['result'][k] for r in rows if k in r['result']]) for k in METRICS}})
    http=[]
    for model,rows in evgroups.items():
        http.append({'model':model,'attempts':len(rows),'status_counts':dict(collections.Counter(r['status'] for r in rows)),
          'invalid_format_attempts':sum(r.get('format_valid') is False for r in rows),
          'missing_prompt_token_counts':sum(r.get('prompt_eval_count') is None for r in rows),
          'missing_output_token_counts':sum(r.get('eval_count') is None for r in rows),
          'prompt_tokens':sum(r.get('prompt_eval_count') or 0 for r in rows),
          'output_tokens':sum(r.get('eval_count') or 0 for r in rows),
          'latency_seconds':describe([r['wall_seconds'] for r in rows]),
          'server_total_duration_seconds':sum(r.get('total_duration') or 0 for r in rows)/1e9,
          'server_load_duration_seconds':sum(r.get('load_duration') or 0 for r in rows)/1e9,
          'prompt_reuse_count':len(rows)-len({r.get('prompt_sha256') for r in rows})})
    save(out,'llm_mission_groups.json',table)
    save(out,'llm_http_by_model.json',http)
    summary={'status':'verified' if not issues else 'failed','integrity_issues':issues,'missions':len(missions),
             'mission_roles':dict(roles),'http_attempts':len(events),'cache_hits':sum(r['cache_hits'] for r in missions),
             'http_failed_attempts':sum(r['status']=='http_failed' for r in events),
             'format_invalid_attempts':sum(r.get('format_valid') is False for r in events),
             'fallbacks':sum(r['result'].get('llm_fallbacks',0) for r in missions),
             'historical_mismatch_missions':sum(bool(r.get('reference_mismatches')) for r in missions),
             'historical_mismatch_fields':dict(mismatches),
             'prompt_tokens':sum(r.get('prompt_eval_count') or 0 for r in events),
             'output_tokens':sum(r.get('eval_count') or 0 for r in events),
             'token_scope':'Ollama per actual attempt, includes retries; cache hit tokens not inferred',
             'cost_scope':'Stored logical UL/DL symbols and bits, not measured wire bytes or energy',
             'peak_gpu_memory_measured':False,'independent_N_scope':'Rows within shared seeds/teams are not independent mission panels',
             'unchanged_original_inference_options':options}
    save(out,'llm_audit_summary.json',summary)
    return not issues

def cache_inventory(out):
    inventory=[]
    for tag,directory in [('published',ROOT/'results/llm_cache'),('frozen_replay',WORK/'results/llm_cache'),
                           ('new_live',ROOT/'.local/ordered-live-20261019/results/llm_cache')]:
        for path in sorted(directory.glob('*.jsonl')):
            cache={}; duplicates=0; conflicts=0; invalid=0; choices=collections.Counter(); n=0
            for row in lines(path):
                n+=1
                if not isinstance(row.get('key'),str) or 'response' not in row:
                    invalid+=1;continue
                key=row['key']; response=row['response']
                if key in cache:
                    duplicates+=1; conflicts+=int(cache[key]!=response)
                cache[key]=response;choices[str(response)]+=1
            inventory.append({'tag':tag,'path':path.relative_to(ROOT).as_posix(),'sha256':digest(path),'bytes':path.stat().st_size,
                'rows':n,'unique_keys':len(cache),'duplicates':duplicates,'conflicting_duplicate_responses':conflicts,
                'invalid_rows':invalid,'choices':dict(choices)})
    save(out,'cache_inventory.json',inventory)
    return {r['path']:r['sha256'] for r in inventory}

def replay(out):
    # Use frozen campaign algorithms. No algorithm patches, no LLM service.
    sys.path.insert(0,str(WORK))
    from gosc import Config,run_episode,llm_agent
    refs=expected(); live_rows=list(lines(RUNS/'resume-live-llm-20261020/outputs/live_episodes.jsonl'))
    class CacheMiss(LookupError):
        def __init__(self,key,prompt,labels,model):
            self.key=key; self.prompt=prompt; self.labels=labels; self.model=model
            super().__init__('Missing cached key '+key)
    class ReadOnlyClient(llm_agent.LLMClient):
        def choose(self,prompt,labels):
            key=hashlib.sha256(f"{self.model}\n{prompt}\n{','.join(labels)}".encode()).hexdigest()
            if key not in self.cache:
                raise CacheMiss(key,prompt,labels,self.model)
            choice=self.cache[key]
            if choice not in labels:raise ValueError('Invalid stored label')
            self.hits+=1;return choice
    def forbidden(body):
        raise AssertionError('HTTP forbidden in diagnostic replay')
    def timeout(signum,frame):
        raise TimeoutError('Diagnostic per-mission time cap')
    signal.signal(signal.SIGALRM,timeout)
    scenarios=[('published',ROOT/'results/llm_cache'),('new_live',ROOT/'.local/ordered-live-20261019/results/llm_cache')]
    summary=[]; total_start=time.monotonic()
    for scenario,directory in scenarios:
        counts=collections.Counter(); compared=0; different=0; missing=collections.Counter(); models=collections.Counter()
        llm_agent._CLIENTS.clear()
        with (out/(scenario+'_replay.jsonl')).open('x') as stream:
            for index,(name,ref,model) in enumerate(refs):
                row={'index':index,'source_file':name,'team':ref['team'],'scheme':ref['scheme'],'model':model,'seed':ref['seed']}
                if time.monotonic()-total_start>1500:
                    row.update(status='not_run_budget')
                    counts[row['status']]+=1;stream.write(json.dumps(row)+'\n');continue
                if model not in llm_agent._CLIENTS:
                    llm_agent._CLIENTS[model]=ReadOnlyClient(model,cache_dir=str(directory),transport=forbidden)
                client=llm_agent._CLIENTS[model]; old=client.hits
                agents=() if ref['team']=='planner' else (0,2,4)
                cfg=Config().with_(llm_agents=agents,llm_model=model,**({'energy_price':.3} if ref['scheme']=='gosc_bits' else {}))
                start=time.monotonic();signal.setitimer(signal.ITIMER_REAL,30)
                try:
                    result=run_episode(cfg,ref['scheme'],ref['seed']);result.pop('curve')
                    assert result.get('llm_fallbacks',0)==0 and client.calls==0
                    reference=ref if scenario=='published' else live_rows[index]['result']
                    changed=[k for k in METRICS if k in reference and result.get(k)!=reference[k]]
                    row.update(status='completed',result=result,reference_mismatches=changed)
                    compared+=1;different+=int(bool(changed))
                except CacheMiss as e:
                    row.update(status='blocked_missing_key',missing_key=e.key,prompt_sha256=hashlib.sha256(e.prompt.encode()).hexdigest(),labels=e.labels)
                    missing[e.key]+=1;models[model]+=1
                    if not (out/(scenario+'_first_missing_prompt.json')).exists():
                        save(out,scenario+'_first_missing_prompt.json',dict(row,prompt=e.prompt))
                except Exception as e:
                    row.update(status='failed',error=repr(e))
                finally:
                    signal.setitimer(signal.ITIMER_REAL,0)
                row.update(wall_seconds=time.monotonic()-start,cache_hits=client.hits-old,http_calls=client.calls)
                counts[row['status']]+=1;stream.write(json.dumps(row)+'\n');stream.flush()
                if (index+1)%30==0:print(scenario,index+1,dict(counts),flush=True)
        summary.append({'scenario':scenario,'missions':len(refs),'status_counts':dict(counts),'completed_comparisons':compared,
            'different_completed_missions':different,'unique_first_missing_keys':len(missing),'blocked_by_model':dict(models),
            'http_attempts':0,'planner_fallback_on_missing':False,
            'scope':'Original algorithms, read-only cached responses; first missing key stops that mission, other mission identities continue'})
    save(out,'replay_coverage_summary.json',summary)

def main():
    require_hpc()
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    assert not [p for p in RUNS.glob('resume-*/status.json') if read(p)['status']=='running']
    source_before={str(p.relative_to(ROOT)):digest(p) for directory in ['gosc','experiments','results'] for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    ok=artifact_audit(out)
    ok=llm_audit(out) and ok
    caches=cache_inventory(out)
    replay(out)
    cache_unchanged=all(digest(ROOT/p)==h for p,h in caches.items())
    protected_unchanged=all(digest(ROOT/p)==h for p,h in source_before.items())
    save(out,'audit_conclusion.json',{'integrity_verified':ok,'cache_files_unchanged':cache_unchanged,
       'protected_files_unchanged':protected_unchanged,'execution_host':'hpc','http_calls_in_this_audit':0,
       'new_model_training':False,'historical_scientific_equivalence':'not_established_for_all_products',
       'calibration_process':'unavailable_in_checked_upstream_public_material',
       'scope':'Registered post-campaign artifact/transport audit plus isolated read-only cache replay'})
    if not (ok and cache_unchanged and protected_unchanged):
        raise RuntimeError('Audit integrity issue; inspect reports')

if __name__=='__main__':
    main()
