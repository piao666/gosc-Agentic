"""Provenance checks for the explicitly approved, limited ToM diagnostic."""
from collections import Counter
import json
from pathlib import Path
from experiments_ext.reproduce import ROOT,sha
from experiments_ext.campaign import differences

PROPOSAL=ROOT/'research/reproduction/2026-10-15-statistical/receiver_scope_proposal.md'
PROTOCOL=ROOT/'research/reproduction/receiver_tom_scope_protocol_v1.md'


def check_tom_rows(rows,jobs):
    ids=[r['job_id'] for r in rows]
    if len(ids)!=len(set(ids)):raise RuntimeError('Duplicate baseline mission')
    counts=Counter()
    for row in rows:
        j=jobs[row['job_id']]
        for key in ('campaign','scheme','param','seed','config_key'):
            if row[key]!=j[key]:raise RuntimeError('Baseline identity changed')
        if row['scheme']!='gosc':continue
        if row['status']!='completed' or row['reference_differences'] or differences(j['expected'],row['output']):
            raise RuntimeError('ToM saved-field agreement failed')
        counts[row['campaign']]+=1
    return dict(counts)


def verify_admission(run,policy='full-statistical',approval_file=None):
    gate=json.loads((run/'r4-statistical/gate.json').read_text())
    if policy=='full-statistical':
        if gate['status']!='scoped_statistical_agreement' or not gate['receiver_diagnostics_allowed']:
            raise RuntimeError('R4-S1 did not pass; default admission denied')
    elif policy=='tom-path-diagnostic-only':
        if approval_file is None:raise RuntimeError('Explicit scoped approval record required')
    else:raise ValueError('Unknown admission policy')
    if gate.get('primary_family')!=104 or gate.get('completed_fresh')!=5200:
        raise RuntimeError('Incomplete statistical gate')
    agreement_path=run/'r4-statistical/agreement.json'
    if sha(agreement_path)!=gate['agreement_sha256']:raise RuntimeError('Statistical evidence changed')
    agreement=json.loads(agreement_path.read_text())
    if len(agreement['results'])!=104:raise RuntimeError('Incomplete agreement intervals')
    if policy=='full-statistical':
        if not agreement['all_equivalent']:raise RuntimeError('Statistical intervals did not all pass')
        return gate,dict(policy=policy,scope='full_statistical_admission')
    approval_file=Path(approval_file).resolve()
    if not approval_file.is_relative_to((ROOT/'.local/reproduction').resolve()):
        raise RuntimeError('Scoped approval must be recorded with local experiment evidence')
    approval=json.loads(approval_file.read_text())
    if approval.get('status')!='approved' or approval.get('scope')!='tom_path_diagnostic_only':
        raise RuntimeError('Wrong approval scope')
    if approval.get('proposal_sha256')!=sha(PROPOSAL) or approval.get('protocol_sha256')!=sha(PROTOCOL):
        raise RuntimeError('Approved proposal/protocol changed')
    if approval.get('baseline_gate_sha256')!=sha(run/'r4-statistical/gate.json'):
        raise RuntimeError('Approval refers to different baseline evidence')
    execution=json.loads((run/'r4-statistical/execution_manifest.json').read_text())
    raw=run/'r4-statistical/raw.jsonl'
    if execution['completed']!=5200 or sha(raw)!=execution['raw_sha256']:
        raise RuntimeError('Baseline raw evidence changed')
    jobs=json.loads((run/'jobs.json').read_text())
    rows=[json.loads(line) for line in raw.open(encoding='utf-8')]
    if len(rows)!=5200 or {r['job_id'] for r in rows}!=set(range(5200)):
        raise RuntimeError('Baseline seed panel incomplete')
    counts=check_tom_rows(rows,jobs)
    if counts!={'frontier-W100':700,'private-original':600,'headline-frozen':600}:
        raise RuntimeError('ToM evidence panel incomplete')
    return gate,dict(policy=policy,scope='tom_path_diagnostic_only',approval_sha256=sha(approval_file),
        proposal_sha256=sha(PROPOSAL),protocol_sha256=sha(PROTOCOL),matching_tom_saved_field_records=1900,
        counts=counts,strict_r4='failed_preserved',r4_s1=gate['status'],
        interpretation='Limited diagnostic admission, not statistical agreement of all baselines; headline references have task/symbols only.')
