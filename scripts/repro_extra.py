"""Original matched analysis, strictly offline LLM replay, and explicit live readiness."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import urllib.request


def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def matched(out,work):
    from experiments.plot_revision import matched as original_matched,table
    rows=json.loads((work/'results/rev_frontier.json').read_text())['rows']
    rows+=json.loads((work/'results/rev_where_tom.json').read_text())['rows']
    rows += [json.loads(line) for line in (work/'results/belief_divergence.jsonl').read_text().splitlines()]
    curves={}
    for (scheme,param),values in table(rows).items():
        prefix,knob=param.split('/',1);curves.setdefault((prefix,scheme),[]).append((knob,values))
    stats={prefix:original_matched(curves,prefix) for prefix in ['W100','W50','K10','clustered']}
    save(out/'matched_statistics.json',{'status':'analyzed','seeds':[0,99],'resamples':10000,
        'budgets':[5000,10000,20000],'original_function':'experiments.plot_revision.matched',
        'bonferroni_simple_value_family':15,'statistics':stats,
        'note':'Original interpolation/envelope and valid-bootstrap counts retained; no same-price resource-equivalence claim.'})


def cached(out,root,work,live_mode=False):
    from gosc import Config,run_episode
    from gosc import llm_agent
    from repro_llm_transport import ObservedTransport
    def http(body):
        req=urllib.request.Request(llm_agent.OLLAMA_URL,json.dumps(body).encode(),{'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=300) as response:return json.load(response)
    observed=ObservedTransport(http,out/'http_attempts.jsonl') if live_mode else None
    class CacheOnly(llm_agent.LLMClient):
        def choose(self,prompt,labels):
            key=hashlib.sha256(f"{self.model}\n{prompt}\n{','.join(labels)}".encode()).hexdigest()
            if key not in self.cache:raise LookupError('Published cache lacks prompt key '+key+'; no HTTP or planner fallback permitted')
            return super().choose(prompt,labels)
    def forbidden(body):raise AssertionError('HTTP forbidden during cache replay')
    cases=[]
    for name in ['llm_mixed.jsonl','llm_extended.jsonl']:
        for line in (root/'results'/name).read_text().splitlines():cases.append((name,json.loads(line)))
    raw=out/('live_episodes.jsonl' if live_mode else 'cached_episodes.jsonl');mismatches=[];hits=0;calls=0
    llm_agent._CLIENTS.clear()
    def alarm(signum,frame):raise TimeoutError('LLM mission exceeded registered per-mission budget')
    signal.signal(signal.SIGALRM,alarm)
    with raw.open('x',encoding='utf-8') as stream:
        for index,(name,reference) in enumerate(cases):
            team=reference['team'];agents=() if team=='planner' else (0,2,4)
            model=reference.get('model') or ('llama3.2:3b' if team=='mixed_llama' else 'qwen2.5:7b' if team=='mixed_qwen7b' else 'qwen2.5:3b')
            if model not in llm_agent._CLIENTS:
                llm_agent._CLIENTS[model]=(llm_agent.LLMClient(model,cache_dir=str(work/'results/llm_cache'),transport=observed) if live_mode else CacheOnly(model,cache_dir=str(work/'results/llm_cache'),transport=forbidden))
            client=llm_agent._CLIENTS[model];oldhits=client.hits;oldcalls=client.calls
            old_attempts=len(observed.events) if observed else 0
            if observed:observed.context={'mission_index':index,'source_file':name,'team':team,'scheme':reference['scheme'],'seed':reference['seed']}
            cfg=Config().with_(llm_agents=agents,llm_model=model,**({'energy_price':.3} if reference['scheme']=='gosc_bits' else {}))
            started=time.monotonic();signal.setitimer(signal.ITIMER_REAL,1800 if live_mode else 120)
            try:
                result=run_episode(cfg,reference['scheme'],reference['seed']);result.pop('curve')
                assert result.get('llm_fallbacks',0)==0
                if not live_mode:assert client.calls==oldcalls
                delta=client.hits-oldhits;hits+=delta;client_misses=client.calls-oldcalls;http=(len(observed.events)-old_attempts) if observed else 0;calls+=http
                keys=['completion_time','completed','found','symbols','bits','false_declarations','llm_decisions','llm_fallbacks','llm_agree']
                changed=[k for k in keys if k in reference and result.get(k)!=reference[k]]
                if changed:mismatches.append({'index':index,'fields':changed})
                row={'index':index,'source_file':name,'team':team,'model':model,'scheme':reference['scheme'],
                    'seed':reference['seed'],'status':'completed','cache_hits':delta,'http_calls':http,
                    'wall_s':time.monotonic()-started,'client_cache_misses':client_misses,
                    'http_attempts_include_retries':True,'inference_events':observed.events[old_attempts:] if observed else [],
                    'token_scope':'Server token counts per actual HTTP attempt; replay tokens unavailable' if live_mode else 'No inference; cached response tokens unavailable',
                    'result':result,'reference_mismatches':changed}
            except BaseException as e:
                stream.write(json.dumps({'index':index,'source_file':name,'status':'failed','error':repr(e)})+'\n');stream.flush();raise
            finally:signal.setitimer(signal.ITIMER_REAL,0)
            stream.write(json.dumps(row)+'\n');stream.flush()
    if live_mode:assert calls>0,'Live stage made no model calls'
    records=[json.loads(line) for line in raw.read_text().splitlines()]
    for name in ['llm_mixed.jsonl','llm_extended.jsonl']:
        with (work/'results'/name).open('x',encoding='utf-8') as stream:
            for row in records:
                if row['source_file']==name:
                    stream.write(json.dumps({k:row[k] for k in ['team','model','scheme','seed','wall_s']}|row['result'])+'\n')
    save(out/('live_inference_summary.json' if live_mode else 'cache_replay_summary.json'),{'status':'completed','missions':len(cases),'cache_hits':hits,'http_calls':calls,
        'historical_mismatches':mismatches,'scope':'Actual model calls with new-run cache, no published responses' if live_mode else 'Published response replay, not new model inference'})


def live(out,root,work):
    config=root/'.local/reproduction-services.json'
    settings=json.loads(config.read_text()) if config.exists() else {}
    url=settings.get('ollama_base_url','http://127.0.0.1:11434').rstrip('/')
    required={'qwen2.5:3b','llama3.2:3b','qwen2.5:7b'}
    try:
        with urllib.request.urlopen(url+'/api/tags',timeout=5) as response:tags=json.load(response)
        available={m['name'] for m in tags['models']}
        missing=sorted(required-available)
        if missing:raise RuntimeError('Required models not available: '+str(missing))
    except Exception as e:
        save(out/'live_readiness.json',{'status':'not_started_missing_runtime','service':url,
            'error':repr(e),'scientific_missions_started':0,'fallback_permitted':False})
        raise RuntimeError('Live LLM stage requires working service and original model names; see live_readiness.json') from e
    # Live inference is isolated from the published replay cache and old result rows.
    livework=root/'.local/ordered-live-20261019'
    if livework.exists():raise RuntimeError('Live workspace already exists; inspect before any retry')
    (livework/'results/llm_cache').mkdir(parents=True);os.environ['OLLAMA_URL']=url+'/api/generate'
    save(out/'live_readiness.json',{'status':'ready','service':url,'tags':tags,'published_cache_used':False})
    cached(out,root,livework,live_mode=True)


def replot(out):
    from experiments import plot,plot_revision,plot_realistic,run_belief_divergence
    for module in [plot,plot_revision,plot_realistic]:module.main()
    run_belief_divergence.fill_table()
    import shutil
    shutil.copytree(Path.cwd()/'figures',out/'figures')


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['matched','cached','live','replot'],required=True);a=p.parse_args()
    out=Path(os.environ['GOSC_OUTPUT_DIR']);root=Path(os.environ['REPRO_PROJECT_ROOT']);work=Path.cwd()
    if a.mode=='matched':matched(out,work)
    elif a.mode=='cached':cached(out,root,work)
    elif a.mode=='live':live(out,root,work)
    else:replot(out)


if __name__=='__main__':main()
