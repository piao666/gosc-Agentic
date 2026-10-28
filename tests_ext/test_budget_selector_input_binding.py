import copy
import pytest
from scripts.audit_budget_selector_input_binding import bind_lines


def sample():
    d=dict(event='decision',t=3,sender=1,budget=100,selected=[dict(symbols=76)])
    return dict(kind='feasible',decision=d,locator=dict(observation='old.jsonl.gz',line=7,t=3,sender=1))


def test_original_line_binding_accepts_exact_content_and_rejects_detached_claim():
    s=sample();raw={('old.jsonl.gz',7):copy.deepcopy(s['decision'])}
    bind_lines([s],raw)
    s['decision']['selected']=[]
    with pytest.raises(ValueError,match='Detached'):bind_lines([s],raw)


def test_original_line_binding_rejects_duplicate_or_invented_line():
    s=sample();raw={('old.jsonl.gz',7):s['decision']}
    with pytest.raises(ValueError,match='Duplicate'):bind_lines([s,s],raw)
    s['locator']['line']=8
    with pytest.raises(ValueError,match='Detached'):bind_lines([s],raw)


def test_original_line_binding_rejects_relabelled_kind_or_sender():
    s=sample();raw={('old.jsonl.gz',7):copy.deepcopy(s['decision'])}
    s['kind']='violation'
    with pytest.raises(ValueError,match='kind'):bind_lines([s],raw)
    s['kind']='feasible';s['locator']['sender']=2
    with pytest.raises(ValueError,match='sender'):bind_lines([s],raw)
