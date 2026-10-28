"""Independent serialized budget/group/wire and service audit; no selector import."""
import argparse
import binascii
from collections import Counter,defaultdict
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.audit_information_identifiability import resource_audit,decision_audit


def require(test,message):
    if not test:raise ValueError(message)


def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit_indexed(d):
    periodic=d['selector_version']=='WirePeriodic-contract-v1'
    require(periodic or d['selector_version']=='BF-selector-v1','Unknown selector version')
    groups=d['periodic_admitted_groups'] if periodic else d['groups_before_age']
    require(isinstance(groups,list),'Missing versioned catalog')
    require(len(d['selected'])==len(d['selected_indices']),'Selected index count')
    used=0;seen=set()
    for chosen,index in zip(d['selected'],d['selected_indices']):
        gi,oi=index['group_index'],index['option_index']
        require(type(gi) is int and type(oi) is int and 0<=gi<len(groups),'Invalid group index')
        require(gi not in seen,'Repeated selected group');seen.add(gi)
        g=groups[gi]
        require(0<=oi<len(g['options']),'Invalid option index')
        o=g['options'][oi]
        require(chosen['kind']==g['kind'] and chosen['cell']==g['cell'],'Group identity')
        require(all(chosen[k]==o[k] for k in ('rate','bits','symbols','n_records')),'Option identity')
        require(type(o['symbols']) is int and o['symbols']>0 and type(o['bits']) is int and o['bits']>0,'Wire integer bounds')
        require(math.isfinite(o['rate']) and o['rate']>0 and o['symbols']==math.ceil(o['bits']/o['rate']),'Candidate wire symbols')
        require(math.isfinite(o['value']) and float.fromhex(o['value_hex'])==o['value'],'Candidate float')
        used+=o['symbols']
    require(type(d['budget']) is int and used<=d['budget'],'Selected budget')
    trace=d['selector_trace']
    require(trace['selector_version']==d['selector_version'] and trace['final_used']==used,'Trace binding')
    if periodic:
        require(d['mode']=='periodic' and d['groups_before_age'] is None and trace['path']=='periodic_independent','Periodic path')
    elif trace['path']=='legacy_feasible':
        require(trace['legacy_used']==used and trace['legacy_used']<=d['budget'] and not trace['upper_checks'],'Legacy path')
    else:
        require(trace['path']=='budget_repair' and trace['legacy_used']>d['budget'],'Repair reason')
        checks=trace['upper_checks']
        require(checks and checks[-1]['used']<=d['budget'],'Feasible upper endpoint')
        require(trace['expansions']==len(checks)-1 and 0<=trace['expansions']<=64,'Expansion bound')
        require(trace['max_expansions']==64 and 0<=trace['bisection_steps']<=40,'Iteration bounds')
        require(all(math.isfinite(x['upper']) for x in checks),'Nonfinite upper endpoint')
        require(all(b['upper']>a['upper'] for a,b in zip(checks,checks[1:])),'Upper progress')
    return used


def audit_submissions(events):
    decisions={(d['t'],d['sender']):d for d in events if d['event']=='decision'}
    require(len(decisions)==sum(d['event']=='decision' for d in events),'Duplicate decision')
    submissions=defaultdict(list);wires={};cpu=Counter()
    for e in events:
        if e['event']=='cpu_admit' and e['action']=='task_ready':cpu[e['t'],e['observer']]+=1
        if e['event']!='task_submit':continue
        key=e['t'],e['sender'];submissions[key].append(e)
        payload=bytes.fromhex(e['payload_hex'])
        body=bytes([192])+(len(payload)+5).to_bytes(2,'big')+bytes([e['sender']])+e['ident'].to_bytes(4,'big')+payload
        wire=body+binascii.crc_hqx(body,0xffff).to_bytes(2,'big')
        require(e['wire_bytes']==len(wire) and hashlib.sha256(wire).hexdigest()==e['wire_sha256'],'Submitted wire SHA/CRC')
        require(e['wire_sha256'] not in wires,'Duplicate submitted wire')
        wires[e['wire_sha256']]=e
    require(set(submissions)<=set(decisions),'Detached submission')
    for key,d in decisions.items():
        got=submissions[key]
        require(len(got)==len(d['selected'])==cpu[key],'Decision vs actual encode admissions')
        for s,e in zip(d['selected'],got):
            payload=bytes.fromhex(e['payload_hex'])
            require(payload[:3]==b'GP\x01' and payload[4]==d['sender'] and int.from_bytes(payload[5:7],'big')==d['t'],'Native task namespace/time')
            kind={0:'CONF',1:'INTENT',2:'EVID'}.get(payload[3])
            require(kind==s['kind'] and e['rate']==s['rate'] and 8*e['wire_bytes']==s['bits'],'Selected vs submitted frame')
            if kind=='EVID':require(int.from_bytes(payload[7:9],'big')==s['n_records'],'Selected evidence prefix')
            else:
                cell=s['cell'] if kind=='CONF' else d['candidate_context']['intent_target']
                require(len(payload)==9 and int.from_bytes(payload[7:9],'big')==cell,'Selected task cell')
    for e in events:
        if e['event']=='ul_attempt' and e['message_kind']=='task':
            require(e['wire_sha256'] in wires,'Unsubmitted task UL')
            s=wires[e['wire_sha256']]
            require(s['t']<=e['t'] and s['sender']==e['sender'] and e['bytes']==s['wire_bytes'] and e['rate']==s['rate'],'UL submission binding')
    return sum(map(len,submissions.values()))


def checked_events(directory,meta):
    path=(directory/meta['path']).resolve()
    require(directory.resolve() in path.parents and not path.is_symlink(),'Artifact path')
    require(digest(path)==meta['sha256'],'Observation hash')
    with gzip.open(path,'rt') as stream:return [json.loads(line) for line in stream]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen',type=Path,required=True);p.add_argument('--replay',type=Path,required=True)
    p.add_argument('--fixtures',type=Path,required=True);a=p.parse_args()
    require(os.name=='posix' and os.getuid()==8301880 and str(ROOT)=='/home/u202520081000097/jupyterlab/Paper/gosc' and os.environ.get('GOSC_OUTPUT_DIR'),'Registered HPC only')
    frozen=read(a.frozen);replay=read(a.replay);fixture=read(a.fixtures)
    require(replay['frozen_sha256']==fixture['frozen_sha256']==digest(a.frozen),'Frozen binding')
    require(replay['input_sha256']==frozen['samples_sha256'],'Sample binding')
    samples=checked_events(a.frozen.parent,frozen['samples'])
    require(len(samples)==len(replay['rows']),'Replay matrix')
    repaired=compatible=0
    for sample,row in zip(samples,replay['rows']):
        d=sample['decision'];new=row['decision']
        require(row['locator']==sample['locator'],'Replay locator')
        require(all(new[k]==v for k,v in d.items() if k not in ('selected',)),'Replay input changed')
        audit_indexed(new)
        require(row['repeat_identical'] and row['identity_preserved']==(sample['kind']=='feasible'),'Repeat/identity claim')
        if sample['kind']=='feasible':
            require(new['selected']==d['selected'] and new['selector_trace']['path']=='legacy_feasible','Feasible compatibility')
            compatible+=1
        else:
            require(sum(x['symbols'] for x in d['selected'])>d['budget'] and new['selector_trace']['path']=='budget_repair','Historical counterexample')
            repaired+=1
    require(repaired==7 and compatible==192,'Frozen replay coverage')
    rows=fixture['rows'];require(len(rows)==52,'Fixture matrix size')
    seen=set();details=[]
    for row in rows:
        key=row['seed'],row['case']['id'],row['observe'];require(key not in seen,'Duplicate fixture');seen.add(key)
        require(row['result']['world_sha256']==frozen['fixture_worlds'][str(row['seed'])],'Fixture world')
        if row['observe']:
            events=checked_events(a.fixtures.parent,row['observation'])
            decisions=[e for e in events if e['event']=='decision']
            for d in decisions:audit_indexed(d)
            decision_audit(events,row['result']);ledger=resource_audit(events,row['result'],frozen['legacy_plan'])
            submits=audit_submissions(events)
            actual={(d['t'],d['sender']):d for d in decisions if d['groups_before_age'] is not None}
            require(len(actual)==len(row['diagnostics']),'Diagnostic count')
            bound=set()
            for diagnostic in row['diagnostics']:
                key=diagnostic['t'],diagnostic['sender']
                require(key in actual and key not in bound,'Diagnostic binding');bound.add(key)
                d=actual[key];form=d['form']
                require(diagnostic['selector_version']==d['selector_version'] and diagnostic['original_form']==form,'Diagnostic version/form')
                require(diagnostic['selected'][form]==d['selected'] and diagnostic['selected_indices'][form]==d['selected_indices']
                        and diagnostic['replay_matches_actual'],'Diagnostic actual replay')
                require(diagnostic['scale_price_same']==(diagnostic['selected']['scale']==diagnostic['selected']['price']),'Numerical comparison claim')
            details.append(dict(seed=row['seed'],case=row['case']['id'],decisions=len(decisions),submissions=submits,ledger=ledger))
        other=next(x for x in rows if x['seed']==row['seed'] and x['case']==row['case'] and x['observe']!=row['observe'])
        omit={'selection_process_seconds'}
        require({k:v for k,v in row['result'].items() if k not in omit}=={k:v for k,v in other['result'].items() if k not in omit},'Observer scientific equivalence')
        require(row['noise_state']==other['noise_state'],'Observer random state')
    require(seen=={(s,c['id'],o) for s in frozen['plan']['fixture_seeds'] for c in frozen['cases'] for o in (False,True)},'Fixture coverage')
    for name,sha in frozen['protected_sha256'].items():require(digest(ROOT/name)==sha,'Protected source changed')
    report=dict(status='passed',scope='Engineering acceptance only; efficacy N0; original scientific No-Go unchanged',
        historical_repaired=repaired,feasible_compatible=compatible,fixture_rows=len(rows),details=details,
        inputs={str(x):digest(x) for x in (a.frozen,a.replay,a.fixtures)},formal_test=False,training=False)
    with (Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k!='details'}))


if __name__=='__main__':main()
