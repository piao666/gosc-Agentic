"""HPC-only verify an explicitly human-approved budget amendment; no simulations."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--approval',type=Path,required=True);a=ap.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    approval=a.approval.resolve();m=read(approval)
    assert m['status']=='human_approved_budget_amendment'
    fpath=ROOT/m['frozen'];bpath=ROOT/m['original_probe_budget'];auditpath=ROOT/m['probe_audit']
    frozen=read(fpath);p=frozen['plan'];old=read(bpath);audit=read(auditpath)
    assert old['status']=='blocked' and audit['status']=='passed' and audit['budget_gate']=='blocked'
    assert p['calibration_projection_gate_seconds']==m['original_projection_gate_seconds']==480
    assert p['calibration_timeout_seconds']==m['original_hard_timeout_seconds']==600
    assert len(frozen['cases'])==m['candidate_count']==21
    assert len(p['calibration_seeds'])==m['independent_calibration_N']==12
    assert p['calibration_seeds']==m['calibration_seeds']
    assert m['calibration_missions']==252 and p['calibration_steps']==m['max_steps']==400
    assert p['per_mission_timeout_seconds']==m['per_mission_timeout_seconds']==60
    assert m['approved_projection_gate_seconds']==1080 and m['approved_hard_timeout_seconds']==1200
    assert m['workers']==m['numeric_threads']==1 and not m['training'] and not m['test_execution_authorized'] and m['new_llm_calls']==0
    for name,expected in frozen['source_sha256'].items():assert sha(ROOT/name)==expected,name
    # Recompute the registered probe projection, without any task-effect analysis.
    rows=read(bpath.parent/'results.json')
    assert len(rows)==42
    projection=2*sum(max(r['wall_seconds'] for r in rows if r['case_id']==c['id']) for c in frozen['cases'])/p['probe_steps']*p['calibration_steps']*len(p['calibration_seeds'])
    assert math.isclose(projection,old['projection_seconds_2x']) and math.isclose(projection,audit['budget_projection_recomputed'])
    assert projection<=m['approved_projection_gate_seconds']<m['approved_hard_timeout_seconds']
    result=dict(status='passed',basis='Direct human budget approval; original probe remains blocked under old gate',
                authorization=m['authorization'],approval_file=m['proposal'],effective_amendment_path=str(approval.relative_to(ROOT)),
                approval_sha256=sha(approval),frozen_path=m['frozen'],frozen_sha256=sha(fpath),
                original_budget_path=m['original_probe_budget'],original_budget_sha256=sha(bpath),
                probe_audit_sha256=sha(auditpath),projection_seconds_2x=projection,
                projection_limit=m['approved_projection_gate_seconds'],hard_timeout=m['approved_hard_timeout_seconds'],
                candidate_count=21,calibration_N=12,calibration_missions=252,
                method_source_verified=True,original_files_modified=False,test_execution_authorized=False,training=False)
    out=Path(os.environ['GOSC_OUTPUT_DIR'])/'approved_budget.json'
    with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))

if __name__=='__main__':main()
