"""Guard against silently rerunning, mixing workspaces or resetting the budget."""
import json
from pathlib import Path
import pytest
from repro_resume import validate_state,ORIGINAL_PLAN_SHA
import repro_resume as mod

def setup_tree(tmp_path,monkeypatch):
    root=tmp_path/'root';work=root/'work'
    (root/'research/protocols').mkdir(parents=True);p=root/'research/protocols/ordered_reproduction_v1.json';p.write_text('{}')
    monkeypatch.setattr(mod,'ORIGINAL_PLAN_SHA',mod.digest(p));monkeypatch.setattr(mod,'STAGES',[(s,'',[],1,1) for s in mod.FIRST+['c-belief']])
    for folder in ['gosc','experiments']:
        (root/folder).mkdir();(root/folder/'a.py').write_text('x=1');(work/folder).mkdir(parents=True);(work/folder/'a.py').write_text('x=1')
    (root/'results/llm_cache').mkdir(parents=True);(work/'results').mkdir()
    base=root/'research/sync/runs';base.mkdir(parents=True)
    for rid,state in [('hpc-ordered-queue-20261019',{'status':'failed','started_at':'2026-10-19T10:36:15+00:00'}),('ordered-c-belief-20261019',{'status':'failed'})]:
        (base/rid/'outputs').mkdir(parents=True);(base/rid/'status.json').write_text(json.dumps(state))
    for name in mod.FIRST:
        p=base/('ordered-'+name+'-20261019');(p/'outputs').mkdir(parents=True)
        (p/'status.json').write_text('{"status":"completed","exit_code":0}');(p/'artifacts.json').write_text('{"files":[]}');(p/'outputs/legacy_outputs.json').write_text('{"changed_result_files":[]}')
    return root,work,base

def test_resume_skips_completed_preserves_failed_and_original_deadline(tmp_path,monkeypatch):
    root,work,base=setup_tree(tmp_path,monkeypatch);before=(base/'ordered-c-belief-20261019/status.json').read_bytes()
    r=validate_state(root,work,now=1792468800)
    assert len(r['completed_prefix'])==4 and r['pending']==[{'stage':'c-belief','run_id':'resume-c-belief-20261020'}]
    assert r['original_deadline_epoch']==1792665375
    assert (base/'ordered-c-belief-20261019/status.json').read_bytes()==before

def test_reject_workspace_source_drift(tmp_path,monkeypatch):
    root,work,base=setup_tree(tmp_path,monkeypatch);(work/'gosc/a.py').write_text('x=2')
    with pytest.raises(RuntimeError,match='Workspace source differs'):validate_state(root,work,now=1792468800)

def test_reject_unfinished_retry_and_expired_budget(tmp_path,monkeypatch):
    root,work,base=setup_tree(tmp_path,monkeypatch)
    with pytest.raises(RuntimeError,match='deadline exhausted'):validate_state(root,work,now=1792700000)
    p=base/'resume-c-belief-20261020';p.mkdir();(p/'status.json').write_text('{"status":"failed"}')
    with pytest.raises(RuntimeError,match='not completed'):validate_state(root,work,now=1792468800)

def test_reject_closed_artifact_change(tmp_path,monkeypatch):
    root,work,base=setup_tree(tmp_path,monkeypatch);p=base/'ordered-c-where-20261019';(p/'outputs/a.json').write_text('tampered')
    (p/'artifacts.json').write_text('{"files":[{"path":"outputs/a.json","sha256":"wrong"}]}')
    with pytest.raises(RuntimeError,match='Closed artifact changed'):validate_state(root,work,now=1792468800)
