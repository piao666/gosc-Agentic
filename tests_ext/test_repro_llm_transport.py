import json
from pathlib import Path
import pytest
from repro_llm_transport import ObservedTransport

def test_retries_and_tokens_observed_without_prompt_or_option_changes(tmp_path,monkeypatch):
    from gosc.llm_agent import LLMClient
    monkeypatch.setattr('gosc.llm_agent.time.sleep',lambda _:None)
    bodies=[]
    def send(body):
        bodies.append(body)
        return {'response':'bad-json' if len(bodies)==1 else '{"choice":"A"}','prompt_eval_count':12,'eval_count':4}
    observed=ObservedTransport(send,tmp_path/'http.jsonl');client=LLMClient('fixture',str(tmp_path/'cache'),observed)
    assert client.choose('private prompt',['A'])=='A'
    assert client.calls==1 and len(observed.events)==2
    assert not observed.events[0]['format_valid'] and observed.events[1]['format_valid']
    assert observed.events[0]['prompt_eval_count']==12 and bodies[0]==bodies[1]
    assert client.choose('private prompt',['A'])=='A' and len(observed.events)==2
    assert 'private prompt' not in (tmp_path/'http.jsonl').read_text()

def test_transport_failure_preserved_and_missing_tokens_are_not_zero(tmp_path):
    def fail(body):raise ConnectionError('fixture offline')
    observed=ObservedTransport(fail,tmp_path/'http.jsonl')
    with pytest.raises(ConnectionError):observed({'model':'fixture','prompt':'x'})
    assert observed.events[0]['status']=='http_failed' and 'eval_count' not in observed.events[0]
