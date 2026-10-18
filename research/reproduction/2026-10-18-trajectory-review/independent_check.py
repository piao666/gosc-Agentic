"""Independent saved-log cross-check. No imports from review or simulator."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

root=Path(__file__).resolve().parents[3]
run=root/'.local/reproduction/2026-10-18-trajectory-review-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
new=root/'.local/reproduction/2026-10-18-cf-precision-v1'
old=Path(read(new/'experiment_manifest.json')['prior_run'])
raw={}
for p in sorted(old.glob('seed-*/branches.jsonl'))+sorted(new.glob('point-*/branches.jsonl')):
    for line in p.read_text(encoding='utf-8').splitlines():
        row=json.loads(line);key=(row['point_id'],row['replicate'],row['success_branch'])
        assert key not in raw;raw[key]=row
with (run/'paired_chain.csv').open(encoding='utf-8') as f:chains=list(csv.DictReader(f))
with (run/'point_matrix.csv').open(encoding='utf-8') as f:matrix=list(csv.DictReader(f))
assert len(chains)==448 and len(matrix)==14 and len(raw)==896
cells={f'shadow_{a}_actual_{b}':0 for a in (False,True) for b in (False,True)}
no_target_task=no_target_path=path_pairs=path_but_zero_task=changed_sets=0
for r in chains:
    a,b=(raw[(r['point_id'],int(r['replicate']),v)] for v in (False,True))
    sender=int(r['sender']);t=int(r['t'])
    real=[];shadow=[]
    for name,dest in (('next_actual_decision',real),('shadow_pre_motion_replan',shadow)):
        aa=a[name] if name=='next_actual_decision' else a['current_slot'][name]
        bb=b[name] if name=='next_actual_decision' else b['current_slot'][name]
        for j in range(len(a['trajectories'])):
            if j==sender:continue
            if next(x for x in aa if x['agent']==j)['target']!=next(x for x in bb if x['agent']==j)['target']:dest.append(j)
    assert real==json.loads(r['receiver_changed_agents'])
    assert shadow==json.loads(r['shadow_changed_agents'])
    cells[f'shadow_{bool(shadow)}_actual_{bool(real)}']+=1
    changed_sets+=real!=shadow
    delta=a['result']['completion_time']-b['result']['completion_time']
    assert delta==int(r['delta_T'])
    firsts=[]
    for j in range(len(a['trajectories'])):
        x,y=a['trajectories'][j],b['trajectories'][j]
        assert x[:t+2]==y[:t+2]
        differences=[i for i in range(min(len(x),len(y))) if x[i]!=y[i]]
        if j!=sender and differences:firsts.append(differences[0]-1)
    first=min(firsts) if firsts else None
    assert ('' if first is None else str(first))==r['first_receiver_motion_divergence_slot']
    no_target_task+=not real and delta!=0
    no_target_path+=not real and first is not None
    path_pairs+=first is not None
    path_but_zero_task+=first is not None and delta==0
for p in matrix:
    rs=[r for r in chains if r['point_id']==p['point_id']]
    assert len(rs)==32
    assert statistics.mean(int(r['delta_T']) for r in rs)==float(p['delta_T_mean'])
s=read(run/'summary.json')
assert s['shadow_actual_any_change_2x2']==cells
assert s['shadow_actual_changed_set_disagreement_pairs']==changed_sets
assert s['posttreatment_strata']['False']['nonzero_delta_T_pairs']==no_target_task
assert s['posttreatment_strata']['False']['receiver_path_divergence_pairs']==no_target_path
assert s['receiver_path_divergence_pairs']==path_pairs
result={'status':'passed','branches':len(raw),'pairs':len(chains),'point_means_verified':len(matrix),
 'shadow_actual_2x2':cells,'changed_set_disagreements':changed_sets,
 'no_next_target_change_but_nonzero_task_delta':no_target_task,'no_next_target_change_but_later_receiver_path_difference':no_target_path,
 'receiver_path_difference_pairs':path_pairs,'receiver_path_difference_but_zero_task_delta':path_but_zero_task,
 'input_hashes_unchanged':all(sha(Path(p))==h for p,h in read(run/'experiment_manifest.json')['input_hashes'].items()),
 'audit_script_sha256':sha(Path(__file__)),'new_simulations':0}
assert result['input_hashes_unchanged']
with (run/'independent_audit.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
