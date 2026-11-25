"""T3-R offline auditor. Standard library only; no network or model execution.

Run on HPC through hpc_runs.py. Historical sources are opened O_NOATIME and
O_NOFOLLOW. Writes are restricted to the new registered output directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import stat
import time
import re
import struct
import zlib
import ast
from string import Template
from collections import Counter, defaultdict

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
OLD = ROOT/'research/sync/runs/hpc-masbench-t3-live-20261125'
HDD = Path('/hdd/u202520081000097/gosc-t3-runs/hpc-masbench-t3-live-20261125')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(obj):
    return sha(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def read(path):
    path = Path(path)
    for parent in [*reversed(path.parents), path]:
        if parent.is_symlink():
            raise RuntimeError('symlink: '+str(parent))
    before = path.stat()
    fd = os.open(path, os.O_RDONLY | os.O_NOATIME | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        raw = stream.read()
    after = path.stat()
    if (before.st_atime_ns, before.st_mtime_ns, before.st_ctime_ns, before.st_size) != (
            after.st_atime_ns, after.st_mtime_ns, after.st_ctime_ns, after.st_size):
        raise RuntimeError('source metadata changed: '+str(path))
    return raw


def load(path):
    return json.loads(read(path))


def walk(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOATIME | os.O_NOFOLLOW)
    try:
        names = sorted(os.listdir(fd))
    finally:
        os.close(fd)
    for name in names:
        child = path/name
        mode = child.lstat().st_mode
        if stat.S_ISDIR(mode):
            yield from walk(child)
        else:
            yield child


def write(name, value):
    out = Path(os.environ['GOSC_OUTPUT_DIR']).resolve()
    if out.parent.name.startswith('hpc-masbench-t3r-') is False:
        raise RuntimeError('new T3-R output directory required')
    target = out/name
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def chain(raw):
    rows = [json.loads(line) for line in raw.rstrip(b'\0\n ').splitlines() if line.strip()]
    previous = '0'*64
    for i, row in enumerate(rows):
        if 'seq' in row and row['seq'] != i:
            raise RuntimeError('chain sequence')
        if 'hash' in row:
            body={k:v for k,v in row.items() if k!='hash'}
            actual=sha(json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
            if row['previous']!=previous or row['hash']!=actual:
                raise RuntimeError('chain SHA')
            previous=row['hash']
    return rows


def inventory():
    manifest_raw = read(OLD/'outputs/hdd_manifest.json')
    manifest = json.loads(manifest_raw)
    expected = {e['path']: e for e in manifest['files']}
    anomalies = []
    if len(expected) != len(manifest['files']):
        anomalies.append({'kind':'duplicate_manifest_path'})
    actual = {p.relative_to(HDD).as_posix():p for p in walk(HDD)}
    rows, cache = [], {}
    for name, item in expected.items():
        rel = PurePosixPath(name)
        row = dict(item, exists=name in actual)
        safe = not (rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name)
        row['safe_path'] = safe
        if not safe or name not in actual:
            anomalies.append({'kind':'unsafe_or_missing','path':name}); rows.append(row); continue
        p = actual[name]
        row['regular_file'] = stat.S_ISREG(p.lstat().st_mode)
        if not row['regular_file']:
            anomalies.append({'kind':'non_regular','path':name}); rows.append(row); continue
        try:
            raw = read(p)
            row.update(readable=True, actual_size=len(raw), actual_sha256=sha(raw),
                       size_match=len(raw)==item['size'], sha_match=sha(raw)==item['sha256'],
                       source_timestamps_preserved=True)
            suffix = p.suffix
            if suffix == '.json':
                value = json.loads(raw); row['content_type'] = 'JSON'; cache[name] = value
            elif suffix == '.jsonl':
                value = chain(raw); row['content_type'] = 'JSONL'; row['records'] = len(value); cache[name] = value
            else:
                raw.decode('utf-8'); row['content_type'] = 'UTF-8 text'
            if not row['size_match'] or not row['sha_match']:
                anomalies.append({'kind':'byte_or_sha_mismatch','path':name})
        except Exception as exc:
            row['error'] = type(exc).__name__+': '+str(exc)
            anomalies.append({'kind':'read_or_type_error','path':name,'error':row['error']})
        rows.append(row)
    extra = sorted(set(actual)-set(expected))
    for name in extra:
        anomalies.append({'kind':'extra','path':name})
    result = {'schema_version':1,'generation':'audit_t3r.py inventory; O_NOATIME/O_NOFOLLOW; stdlib only',
              'hdd_root':str(HDD),'manifest_source':str(OLD/'outputs/hdd_manifest.json'),
              'manifest_sha256':sha(manifest_raw),'expected_files':len(manifest['files']),
              'actual_entries':len(actual),'read_files':sum(r.get('readable',False) for r in rows),
              'sha_pass':sum(r.get('sha_match',False) for r in rows),
              'size_pass':sum(r.get('size_match',False) for r in rows),
              'expected_bytes':manifest['bytes'],'actual_listed_bytes':sum(r.get('actual_size',0) for r in rows),
              'anomalies':anomalies,'files':rows,'new_model_calls':0,'raw_text_exported':False}
    write('evidence_inventory.json',result)
    # Shape-only exploratory index. No private text is copied.
    shapes=[]
    for name,value in cache.items():
        if any(x in name for x in ('application-result','provider-request','wire-events')) or name.endswith('ledger.jsonl'):
            shapes.append({'path':name,'shape':list(value) if isinstance(value,dict) else list(value[0]) if value else [],
                           'nested':{k:list(v) if isinstance(v,dict) else ('list '+str(len(v))) if isinstance(v,list) else type(v).__name__
                                     for k,v in value.items()} if isinstance(value,dict) else {}})
    write('source_shapes.json',shapes)
    print(json.dumps({k:v for k,v in result.items() if k!='files'}))


ANSWER=re.compile(r'<A>(.*?)</A>',re.S)
FACT=re.compile(r'<R>(.*?)</R>',re.S)
QUESTION=re.compile(r'<Q>(.*?)</Q>',re.S)


def answer(text):
    for value in reversed(ANSWER.findall(text)):
        v=value.strip()
        if v.lower() in {'answer','final answer','the answer','answer:'}:
            continue
        return v[:-1] if v.endswith('.') else v
    found=re.search(r'\\boxed\{(.+?)\}',text)
    return found.group(1).strip() if found else None


def norm(value):
    import string
    return ' '.join(re.sub(r'\b(a|an|the)\b',' ',''.join(c for c in value.lower() if c not in string.punctuation)).split())


def score(gold,value):
    if not value:
        return 0.,0.
    a,b=norm(gold).split(),norm(value).split()
    f=2*sum((Counter(a)&Counter(b)).values())/(len(a)+len(b)) if a and b else float(a==b)
    return float(norm(gold)==norm(value)),f


def traces():
    raw_index=load(OLD/'outputs/hdd_manifest.json')
    listing={e['path']:e for e in raw_index['files']}
    ledger=chain(read(HDD/'live/campaign/ledger.jsonl'))
    control=chain(read(HDD/'live/control.jsonl'))
    archived=load(ROOT/'research/sync/runs/hpc-masbench-t3-audit-20261125/outputs/t3_audit.json')
    summary=load(OLD/'outputs/live_summary.json')
    plan=load(ROOT/'research/protocols/masbench_t3_candidate_plan_2026-11-25.json')['episodes']
    registry=load(ROOT/'research/sync/runs/hpc-masbench-registry-v2-20261103/outputs/development_registry_v1.json')
    data_raw=read(ROOT/'research/sync/runs/hpc-masbench-data-audit-v2-20261103/outputs/reasoning.json')
    assert sha(data_raw)==registry['data_sha256']
    dataset=json.loads(data_raw)
    selected={i+1:dataset[e['row']] for i,e in enumerate(registry['selected'])}
    prompt_path=ROOT/'research/logs/masbench-adapter-contract-2026-11-03/reference/Reasoning/src/prompts.py'
    prompt_raw=read(prompt_path); templates={}
    for node in ast.parse(prompt_raw).body:
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in ('QA_INFO_EXCHANGE_PROMPT','QA_INFO_EXCHANGE_PROMPT_PROTOCOL'):
                    templates['protocol' if target.id.endswith('PROTOCOL') else 'base']=Template(ast.literal_eval(node.value.args[0]))
    expected_system={}; coverage=[]
    for i,record in selected.items():
        views=[]; info_by_side={}
        for name,side,partner in [('Alice','agent_a','Bob'),('Bob','agent_b','Alice')]:
            lines=[]
            for title,passages in record['context'][side]:
                lines.append('Article: '+title)
                lines.extend('Sentence: '+s.strip() for s in passages if s and s.strip())
                lines.append('')
            information='\n'.join(lines).strip(); info_by_side[side]=information
            view=dict(name=name,partner=partner,question=record['question'],information=information);views.append(view)
            for style,template in templates.items():
                expected_system[i,style,name]=template.safe_substitute(**view)
        for p in plan:
            if p['case']!=i:continue
            assert digest(views)==p['private_view_sha256']
            assert [digest([{'role':'system','content':expected_system[i,p['style'],name]}]) for name in ['Alice','Bob']]==p['initial_request_sha256']
        coverage.append({'case':i,'family_sha256':next(p['family_sha256'] for p in plan if p['case']==i),
                         'side_coverage':{side:[{'support_owner':owner,'support_index':j,'support_sha256':sha(fact[2].encode()),
                                               'present_in_private_context':fact[2].strip() in info}
                                               for owner in ('agent_a','agent_b') for j,fact in enumerate(record['supporting_facts'][owner])]
                                          for side,info in info_by_side.items()}})
    requests={}; finishes={}; providers=defaultdict(list); outputs={}; wires={}; barriers=[]
    pending=None; last_wire=None
    for row in ledger:
        e=row['event']; kind=e['kind']
        if kind=='request': requests[e['id']]=dict(e,ledger_seq=row['seq'])
        if kind=='finish': finishes[e['id']]=dict(e,ledger_seq=row['seq'])
        if kind=='barrier':
            c=control[e['receipt']['control_event_seq']]
            obs=c['event']['observation']
            assert c['hash']==e['receipt']['control_event_hash'] and c['event']['kind']=='unload-complete'
            assert obs['ledger_tip']==row['previous'] and obs['ledger_seq']==row['seq']
            assert obs['ps']['models']==[] and obs['remaining_runners']==[]
            assert obs['process_observations'] and all(x['stamp']!=x['observed_stamp'] for x in obs['process_observations'])
            barriers.append({'ledger_seq':row['seq'],'control_seq':c['seq'],'control_sha256':c['hash']})
        if kind!='bytes': continue
        path='live/campaign/artifacts/'+e['path']; raw=read(HDD/path)
        assert sha(raw)==e['sha256']==listing[path]['sha256'] and len(raw)==e['count']
        v=json.loads(raw) if path.endswith('.json') else None
        if path.endswith('-provider-request.json'):
            pending=dict(v,path=path,file_sha256=sha(raw),ledger_seq=row['seq'])
        elif path.endswith('-client.json') and v['phase']=='completed':
            assert pending is not None
            pending['client']=v['data'];pending['client_source']={'path':path,'sha256':sha(raw),'ledger_seq':row['seq']}
            providers[pending['episode_id']].append(pending);pending=None
        elif path.endswith('-wire-events.json'):
            last_wire=dict(v,source={'path':path,'sha256':sha(raw),'ledger_seq':row['seq']})
        elif path.endswith('-application-result.json'):
            outputs[v['id']]=dict(v,source={'path':path,'sha256':sha(raw),'ledger_seq':row['seq']})
            wires[v['id']]=last_wire;last_wire=None
    assert len(requests)==len(finishes)==51 and len(outputs)==16
    assert ledger[-1]['hash']==summary['ledger_tip'] and control[-1]['hash']==summary['control_tip']
    episodes=[]; private_review=[]; discrepancies=[]
    old={e['id']:e for e in archived['episodes']}
    for p in plan:
        key=p['id']; result=outputs[key]; wire=wires[key]; reqs=providers[key]
        record=selected[p['case']]; gold=record['answer']
        memory=[[],[]];facts=[[],[]]; fact_sources=[{},{}];turns=[];next_uses=[]
        assert len(reqs)==len(result['transcript'])==len(result['messages'])
        ep=dict(p,source=result['source'],wire_source=wire['source'],end_reason=result['end_reason'],
                requests=len(reqs),final_answer_sha256=sha((result['final_answer'] or '').encode()),
                final_answer_bytes=len((result['final_answer'] or '').encode()),error_flags=result['error_flags'],
                usage_missing=result['usage_missing'],private_context_side_sha256={},turns=turns,
                application_cpu_process_ns=sum(x['value'] for x in result['cpu_process_ns']),
                wire_cpu_process_ns=sum(x['process_ns'] for x in wire['cpu']))
        for side in ('agent_a','agent_b'):
            ep['private_context_side_sha256'][side]=digest(record['context'][side])
        for t,(req,full,m) in enumerate(zip(reqs,result['transcript'],result['messages'])):
            s=t%2; dest=1-s; name=['Alice','Bob'][s]; messages=req['payload']['messages']; client=req['client']
            assert messages[0]=={'role':'system','content':expected_system[p['case'],p['style'],name]}
            expected=[{'role':'system','content':messages[0]['content']}]+[
                {'role':'assistant' if text.strip().startswith(name+':') else 'user','content':text} for text in memory[s]]
            assert messages==expected, (key,t,'memory differs')
            assert digest(messages)==client['request_sha256']
            response=client['response']; text=response['choices'][0]['message']['content'] or ''
            post=text.strip();post=post if post.startswith(name+':') else name+': '+post
            assert post==full
            visible=full
            if p['style']=='protocol':
                found=re.search(r'^\s*'+name+r':\s*MESSAGE\b',full,re.M|re.I)
                if found: visible=full[found.start():].strip()
            body=visible.encode();parsed=answer(visible)
            assert sha(body)==m['payload_sha256'] and len(body)==m['body_bytes']
            memory[s].append(full)
            tags={tag:exp.findall(visible) for tag,exp in [('A',ANSWER),('Q',QUESTION),('R',FACT)]}
            added=[[],[]]
            def add(side):
                for n,f in enumerate(tags['R']):
                    f=f.strip()
                    if f and f not in facts[side]:
                        facts[side].append(f);fact_sources[side][f]=(t,n)
                        added[side].append({'sha256':sha(f.encode()),'source_turn':t,'R_index':n})
            if p['style']=='protocol':add(s)
            board=[]
            if m['delivered'] and m['visible'] is not None:
                assert bytes.fromhex(m['body']['utf8_or_wire_hex'])==body
                if p['style']=='protocol':
                    add(dest)
                    board=[{'sha256':sha(f.encode()),'source_turn':fact_sources[dest][f][0],
                            'R_index':fact_sources[dest][f][1]} for f in facts[dest]]
                    if facts[dest]:
                        visible+='\n\n--- SHARED KNOWLEDGE BOARD (Cumulative Facts) ---\n'+'\n'.join(
                            f'{i+1}. {fact}' for i,fact in enumerate(facts[dest]))+'\n-------------------------------------------------'
                memory[dest].append(visible)
            receiver_request=None
            if t+1<len(reqs) and m['delivered'] and m['visible'] is not None:
                nxt=reqs[t+1]['payload']['messages']
                assert any(x['content']==visible for x in nxt[1:])
                receiver_request=digest(nxt);next_uses.append({'turn':t+1,'payload_sha256':sha(body),'receiver_request_sha256':receiver_request})
            frames=[];indices=[];ul={};dl={}
            for i,e in enumerate(wire['events']):
                if e['event']!='frame':continue
                rawframe=bytes.fromhex(e['raw_hex']); head=struct.unpack('!2sBBIIBBIHHH',rawframe[:24])
                if head[4]!=t:continue
                assert head[0]==b'MR' and head[1]==1 and len(rawframe)==e['bytes']==28+head[-1]
                assert zlib.crc32(rawframe[:-4])==struct.unpack('!I',rawframe[-4:])[0]
                assert e['uses']==int((8*len(rawframe)+e['rate']-1)//e['rate'])
                if e['success'] and head[2] in (1,3): (ul if head[2]==1 else dl)[head[8]]=rawframe[24:-4]
                frames.append(e);indices.append(i)
            if m['delivered']:
                assert b''.join(dl[i] for i in sorted(dl))==body and b''.join(ul[i] for i in sorted(ul))==body
            turn={'turn':t,'speaker':name,'request_id':req['request_id'],
                  'provider_source':{k:req[k] for k in ('path','file_sha256','ledger_seq')},'response_source':req['client_source'],
                  'request_sha256':digest(messages),'response_sha256':client['response_sha256'],
                  'raw_response_text_sha256':sha(text.encode()),'postprocessed_text_sha256':sha(full.encode()),
                  'parsed_answer_sha256':sha(parsed.encode()) if parsed is not None else None,
                  'parser_action':'A' if ANSWER.findall(body.decode()) else 'boxed' if parsed else 'nonterminal',
                  'tag_counts':{k:len(v) for k,v in tags.items()},'tag_sha256':{k:[sha(x.encode()) for x in v] for k,v in tags.items()},
                  'output_utf8_bytes':len(text.encode()),'finish_reason':client['finish_reason'],'usage':client['usage'],
                  'raw_completion_empty':not text,'exact_response_binding_matches':digest(response)==client['response_sha256'],
                  'model':req['payload']['model'],'temperature':req['payload']['temperature'],'max_tokens':req['payload']['max_tokens'],
                  'input_segments':[{'role':x['role'],'sha256':sha(x['content'].encode()),'utf8_bytes':len(x['content'].encode())} for x in messages],
                  'message':{k:v for k,v in m.items() if k not in ('body',)},
                  'wire_event_indices':indices,'wire_bytes':sum(e['bytes'] for e in frames),
                  'ul_uses':sum(e['uses'] for e in frames if e['direction']=='UL'),
                  'dl_uses':sum(e['uses'] for e in frames if e['direction']=='DL'),
                  'wire_success_frames':sum(e['success'] for e in frames),'wire_retries':sum(e['attempt']>0 for e in frames),
                  'receiver_next_request_sha256':receiver_request,'delivered_but_not_consumed':bool(m['delivered'] and not receiver_request),
                  'local_facts_added':added,'receiver_board':board,'board_policy':'exact_string_dedup_append_no_overwrite',
                  'model_start_monotonic':client['start_monotonic'],'model_end_monotonic':client['end_monotonic']}
            turns.append(turn)
            # Minimal controlled read aids remain on HPC; not part of exported index.
            private_review.append({'episode':key,'turn':t,'Q':tags['Q'],'R':tags['R'],'A':tags['A'],
                                   'non_tag_excerpt':re.sub(r'<[AQR]>.*?</[AQR]>','[TAG]',body.decode(),flags=re.S)[:220]})
            if parsed:
                assert t==len(reqs)-1 and parsed==result['final_answer']
        assert memory==result['memory']
        em,f=score(gold,result['final_answer'] if result['end_reason']=='answer' else None)
        ep.update(EM=em,F1=f,receiver_next_requests=next_uses,
                  wire_bytes=sum(t['wire_bytes'] for t in turns),channel_uses=sum(t['ul_uses']+t['dl_uses'] for t in turns),
                  prompt_tokens=sum(t['usage']['prompt_tokens'] for t in turns),completion_tokens=sum(t['usage']['completion_tokens'] for t in turns),
                  final_memory_reconstruction_matches=True)
        for name in ['end_reason','EM','F1','requests','receiver_next_requests','wire_bytes','channel_uses']:
            if ep[name]!=old[key][name]:discrepancies.append({'episode':key,'field':name,'old':old[key][name],'new':ep[name]})
        episodes.append(ep)
    pairs=[]
    for p in episodes:
        if p['condition']!='Full':continue
        n=next(x for x in episodes if x['id']==p['id'].replace('Full','No-A2A'))
        pairs.append({'full':p['id'],'no_a2a':n['id'],'style':p['style'],'F1_difference':p['F1']-n['F1'],
                      'initial_request_match':p['turns'][0]['request_sha256']==n['turns'][0]['request_sha256'],
                      'final_answer_text_equal':outputs[p['id']]['final_answer']==outputs[n['id']]['final_answer'],
                      'response_text_sha_sequences_equal':[x['raw_response_text_sha256'] for x in p['turns']]==[x['raw_response_text_sha256'] for x in n['turns']],
                      'private_view_sha_match':p['private_view_sha256']==n['private_view_sha256']})
    usage={k:sum(x['usage'][k] for seq in providers.values() for x in [r['client'] for r in seq]) for k in ['prompt_tokens','completion_tokens']}
    verification={'schema_version':1,'episodes':16,'task_requests':49,'synthetic_requests':2,'all_requests':len(requests),
                  'usage':usage,'barriers':barriers,'ledger_records':len(ledger),'control_records':len(control),
                  'raw_comparison_discrepancies':discrepancies,'pairs':pairs,'new_model_calls':0,
                  'historical_results_modified':False,'original_task_or_code_modified':False,
                  'causal_content_effect':'Unidentifiable; no intervention','independent_new_family_N':0}
    source_snapshot=load(OLD/'source_snapshot.json')
    source_paths=['extensions/masbench_reasoning/'+x+'.py' for x in ['application','evaluation','wire','registry','client','live_driver']]+[
        'experiments_ext/masbench_t3_live.py','experiments_ext/masbench_t3_audit.py',
        'research/logs/masbench-adapter-contract-2026-11-03/reference/Reasoning/src/prompts.py']
    source_entries={e['path']:e for e in source_snapshot['files']}
    verification['execution_source_bindings']=[{'path':p,'snapshot_sha256':source_entries[p]['remote_sha256'],
        'actual_sha256':sha(read(ROOT/p)),'matches':sha(read(ROOT/p))==source_entries[p]['remote_sha256']} for p in source_paths]
    verification['private_system_and_initial_views_reconstructed']=True
    verification['support_coverage']=coverage
    verification['empty_task_completions']=[{'episode':e['id'],'turn':t['turn'],'source':t['response_source']} for e in episodes for t in e['turns'] if t['raw_completion_empty']]
    verification['wire_totals_by_group']={style:{'messages':sum(e['requests'] for e in episodes if e['style']==style and e['condition']=='Full'),
        'delivered_without_next_request':sum(t['delivered_but_not_consumed'] for e in episodes if e['style']==style and e['condition']=='Full' for t in e['turns']),
        'unconsumed_wire_bytes':sum(t['wire_bytes'] for e in episodes if e['style']==style and e['condition']=='Full' for t in e['turns'] if t['delivered_but_not_consumed']),
        'wire_bytes':sum(e['wire_bytes'] for e in episodes if e['style']==style and e['condition']=='Full'),
        'ul_uses':sum(t['ul_uses'] for e in episodes if e['style']==style and e['condition']=='Full' for t in e['turns']),
        'dl_uses':sum(t['dl_uses'] for e in episodes if e['style']==style and e['condition']=='Full' for t in e['turns'])} for style in ['base','protocol']}
    write('episode_trace_index.json',{'schema_version':1,'generation':'Independent stdlib reconstruction from immutable requests/responses/frames; no production imports',
                                     'hdd_root':str(HDD),'turn_index_base':0,'episodes':episodes,'pairs':pairs})
    write('verification_summary.json',verification)
    # This read aid contains selected private excerpts: kept in HPC output, not pulled or published.
    write('controlled_read_aid.private.json',{'turns':private_review,'cases':[{'case':i,'question':r['question'],'gold':r['answer'],
          'supporting_facts':r['supporting_facts']} for i,r in selected.items()]})
    print(json.dumps({k:v for k,v in verification.items() if k not in ('barriers','pairs')}))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['inventory','traces'])
    args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    if os.getuid()!=8301880:
        raise RuntimeError('unexpected UID')
    start=time.monotonic()
    if args.mode=='inventory':inventory()
    else:traces()
    print(json.dumps({'wall_seconds':time.monotonic()-start,'usage':list(resource.getrusage(resource.RUSAGE_SELF))}))


if __name__=='__main__':
    main()
