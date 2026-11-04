"""HPC-only model-free registry/client contracts. Network forbidden."""
from dataclasses import replace
import json
from types import SimpleNamespace
import socket

import pytest

from extensions.masbench_reasoning.registry import build_registry, graph, digest
from extensions.masbench_reasoning.client import (ClientConfig, ContextBinding, ControlledClient,
    ClientFailure, OllamaHTTPBackend, LivePermit, run_controlled, sha, canonical, JsonlAuditSink)
from extensions.masbench_reasoning.application import LocalAgent, PrivateView, run_fixed
from extensions.masbench_reasoning.evaluation import summarize
from extensions.masbench_reasoning.wire import ContractTransport

DIGEST = "a"*64


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    attempts = []
    def forbidden(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("Real network/model calls forbidden")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    yield
    assert not attempts, "Even caught real-network attempts invalidate the fixture"


def item(i, level="easy", q=None, title=None, text="fact"):
    title = title or f"Title{i}"
    return {"id": str(i), "question": q or f"Question{i}", "level": level,
            "context": {"agent_a": [[title, [text]]], "agent_b": [[f"Other{i}", [f"Other fact{i}"]]]},
            "supporting_facts": {"agent_a": [[title, 0, text]], "agent_b": [[f"Other{i}", 0, f"Other fact{i}"]]}}


def test_blank_support_no_longer_connects_unrelated_records():
    rows = [item(0, text=""), item(1, text="")]
    assert len(graph(rows, legacy=True)["components"]) == 1
    fixed = graph(rows)
    assert len(fixed["components"]) == 2
    assert len(fixed["rejected_keys"]) == 2


def test_common_sentence_is_bound_to_article():
    rows = [item(0, text="Common fact"), item(1, text="Common fact")]
    assert len(graph(rows, legacy=True)["components"]) == 1
    assert len(graph(rows)["components"]) == 2


def test_empty_title_not_a_source_identity():
    rows = [item(0), item(1)]
    for row in rows:
        row["context"]["agent_a"][0][0] = ""
        row["supporting_facts"]["agent_a"][0][0] = ""
    assert len(graph(rows, legacy=True)["components"]) == 1
    assert len(graph(rows)["components"]) == 2


def test_shared_distractor_and_same_question_are_still_hard_edges():
    rows = [item(0), item(1)]
    rows[0]["context"]["agent_a"].append(["Shared distractor", ["x"]])
    rows[1]["context"]["agent_b"].append(["Shared distractor", ["x"]])
    assert len(graph(rows)["components"]) == 1
    rows = [item(0, q="  SAME QUESTION "), item(1, q="same question", level="hard")]
    assert len(graph(rows)["components"]) == 1


def test_registry_four_families_two_strata_and_anomaly_whole_family():
    rows = [item(i, "easy" if i < 3 else "hard") for i in range(6)]
    rows.append(item(6, "hard", q="Question0"))
    result = build_registry(rows, DIGEST, {0})
    assert result["pilot_ineligible_family_rows"] == [0, 6]
    assert len(result["selected"]) == 4
    assert [s["level"] for s in result["selected"]] == ["easy", "easy", "hard", "hard"]
    assert len({s["family_sha256"] for s in result["selected"]}) == 4
    assert all(s["row"] not in {0, 6} for s in result["selected"])
    assert result == build_registry(rows, DIGEST, {0})


def test_registry_component_diversity_is_predeclared_preference():
    rows = [item(i, "easy" if i < 2 else "hard", title="All shared") for i in range(4)]
    result = build_registry(rows, DIGEST, set())
    assert len(result["selected"]) == 4
    assert len(result["reserved_components"]) == 1
    assert result["development_reserved_rows"] == [0, 1, 2, 3]
    assert not result["actual_model_exposure"] and not result["calibration_eval_split_frozen"]


def test_registry_missing_stratum_blocks_without_replacement():
    result = build_registry([item(i) for i in range(4)], DIGEST, set())
    assert result["selected"] == []
    assert result["status"] == "blocked_strata_component_coverage"


def test_registry_never_reads_gold_or_uses_length_rank():
    class SafeRecord(dict):
        def __getitem__(self, key):
            if key in {"answer", "score", "raw", "context_raw"}:
                raise AssertionError("Forbidden selection feature")
            return super().__getitem__(key)
    rows = [SafeRecord(item(i, "easy" if i < 2 else "hard")) for i in range(4)]
    result = build_registry(rows, DIGEST, set())
    assert len(result["selected"]) == 4 and not result["selection_uses_gold_or_outputs"]


def response(text="<A>Paris</A>", **kwargs):
    result = {"model": "fixture-model", "choices": [{"finish_reason": "stop", "message": {"content": text}}],
              "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}}
    result.update(kwargs)
    return result


class FakeBackend:
    is_live = False
    def __init__(self, responses=None, error=None, identity=None):
        self.responses = iter(responses or [response()])
        self.error = error
        self.observed_identity = identity or {"model": "fixture-model", "manifest_sha256": DIGEST}
        self.requests, self.metadata_timeouts = [], []
    def identity(self, timeout):
        self.metadata_timeouts.append(timeout)
        return self.observed_identity
    def create(self, payload, timeout):
        self.requests.append((payload, timeout))
        if self.error:
            raise self.error
        return next(self.responses)


def client(backend=None, counter=lambda x:10, binding=None, clock=None, **config):
    cfg = ClientConfig("fixture-model", DIGEST, 32768, **config)
    binding = binding or ContextBinding(DIGEST, 32768, "fixture-exact-template-counter", "b"*64, True)
    kwargs = {} if clock is None else {"clock": clock}
    return ControlledClient(cfg, backend or FakeBackend(), counter, binding, **kwargs)


MESSAGES = [{"role": "system", "content": "Own evidence only"}]


@pytest.mark.parametrize("endpoint", ["https://api.openai.com/v1", "http://localhost:11434/v1",
    "http://127.0.0.1:11434/v1/", "http://user@127.0.0.1:11434/v1", "http://127.0.0.1:11434/v1?x=y",
    "http://127.0.0.1:11434/v1#fragment", "http://127.0.0.1.evil/v1"])
def test_only_exact_loopback_endpoint(endpoint):
    with pytest.raises(ValueError):
        ClientConfig("x", DIGEST, 32768, endpoint=endpoint)


def test_live_default_blocked_before_any_http_or_dependency_import():
    cfg = ClientConfig("x", DIGEST, 32768)
    with pytest.raises(ClientFailure, match="live_execution_not_authorized"):
        OllamaHTTPBackend(cfg)
    backend = FakeBackend()
    backend.is_live = True
    with pytest.raises(ClientFailure, match="live_execution_not_authorized"):
        client(backend)
    assert backend.requests == []


def test_success_hash_identity_usage_and_caller_memory_frozen():
    fake = FakeBackend()
    c = client(fake)
    messages = [dict(MESSAGES[0])]
    assert c.generate(messages) == "<A>Paris</A>"
    row = c.audit[0]
    messages[0]["content"] = "Changed after call"
    assert row["messages"] == MESSAGES
    assert row["request_sha256"] == sha(MESSAGES)
    assert row["response_sha256"] == sha(row["response"])
    assert row["payload_sha256"] == sha(fake.requests[0][0])
    assert c.calls == 1 and not row["usage_missing"] and row["error"] is None
    assert fake.requests[0][1] <= c.config.timeout_seconds


@pytest.mark.parametrize("binding,reason", [
    (ContextBinding(DIGEST, 32768, "x", "b"*64, False), "context_tokenizer_binding_unverified"),
    (ContextBinding("c"*64, 32768, "x", "b"*64, True), "context_model_binding_mismatch"),
    (ContextBinding(DIGEST, 1024, "x", "b"*64, True), "context_model_binding_mismatch")])
def test_context_evidence_fail_closed(binding, reason):
    c = client(binding=binding)
    with pytest.raises(ClientFailure, match=reason):
        c.generate(MESSAGES)
    assert c.calls == 0 and not c.audit[0]["http_attempted"]


def test_context_overflow_does_not_trim_or_send():
    c = client(counter=lambda x:32767)
    with pytest.raises(ClientFailure, match="context_overflow_no_truncation"):
        c.generate(MESSAGES)
    assert c.calls == 0 and c.audit[0]["messages"] == MESSAGES


@pytest.mark.parametrize("bad", [[], [{"role": "user", "content": "x"}],
    [{"role": "system", "content": "x", "gold": "not allowed"}],
    [{"role": "system", "content": "x"}, {"role": "tool", "content": "x"}]])
def test_request_schema_rejects_extra_fields(bad):
    c = client()
    with pytest.raises(ClientFailure, match="request_schema"):
        c.generate(bad)
    assert c.calls == 0


@pytest.mark.parametrize("error,reason", [(TimeoutError(), "timeout"), (ConnectionError(), "connection_error"),
    (RuntimeError("sensitive exception text"), "backend_or_protocol_error")])
def test_errors_are_counted_once_without_retry_or_sensitive_exception_dump(error, reason):
    fake = FakeBackend(error=error)
    c = client(fake)
    with pytest.raises(ClientFailure, match=reason):
        c.generate(MESSAGES)
    assert c.calls == len(fake.requests) == 1
    assert c.audit[0]["error"] == reason and "sensitive" not in canonical(c.audit)


def test_model_digest_mismatch_blocks_generation():
    fake = FakeBackend(identity={"model": "fixture-model", "manifest_sha256": "f"*64})
    c = client(fake)
    with pytest.raises(ClientFailure, match="model_identity_changed"):
        c.generate(MESSAGES)
    assert not fake.requests and c.calls == 0


@pytest.mark.parametrize("finish,reason", [("length", "output_truncated"), (None, "unsupported_finish_reason"),
    ("content_filter", "unsupported_finish_reason")])
def test_truncated_or_unsupported_finish_not_parsed_as_answer(finish, reason):
    answer = response()
    answer["choices"][0]["finish_reason"] = finish
    c = client(FakeBackend([answer]))
    with pytest.raises(ClientFailure, match=reason):
        c.generate(MESSAGES)


@pytest.mark.parametrize("usage,reason", [
    ({"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 99}, "usage_invalid"),
    ({"prompt_tokens": 10, "completion_tokens": 513, "total_tokens": 523}, "output_token_cap"),
    ({"prompt_tokens": 9, "completion_tokens": 2, "total_tokens": 11}, "prompt_token_count_mismatch_possible_truncation"),
    ({"prompt_tokens": True, "completion_tokens": 2, "total_tokens": 3}, "usage_invalid")])
def test_usage_and_silent_input_truncation_guard(usage, reason):
    c = client(FakeBackend([response(usage=usage)]))
    with pytest.raises(ClientFailure, match=reason):
        c.generate(MESSAGES)


def test_missing_usage_is_explicit_not_zero_or_estimated():
    c = client(FakeBackend([response(usage=None)]))
    c.generate(MESSAGES)
    assert c.audit[0]["usage"] is None and c.audit[0]["usage_missing"]


@pytest.mark.parametrize("bad,reason", [
    (response(model="other-model"), "response_model_mismatch"),
    (response(choices=[]), "response_schema"),
    (response(choices=[{"finish_reason":"stop", "message":{"content":17}}]), "response_schema")])
def test_response_schema_and_model_identity(bad, reason):
    c = client(FakeBackend([bad]))
    with pytest.raises(ClientFailure, match=reason):
        c.generate(MESSAGES)


def test_request_and_wall_caps_have_no_extra_generation():
    fake = FakeBackend()
    c = client(fake, max_calls=1)
    c.generate(MESSAGES)
    with pytest.raises(ClientFailure, match="request_count_cap"):
        c.generate(MESSAGES)
    assert len(fake.requests) == 1
    now = [0]
    fake = FakeBackend()
    c = client(fake, clock=lambda:now[0], wall_seconds=1)
    now[0] = 2
    with pytest.raises(ClientFailure, match="wall_cap"):
        c.generate(MESSAGES)
    assert not fake.requests


def test_metadata_and_generation_share_one_operation_timeout():
    now = [0.0]
    class SlowIdentity(FakeBackend):
        def identity(self, timeout):
            now[0] += 50
            return super().identity(timeout)
    fake = SlowIdentity()
    c = client(fake, clock=lambda:now[0], timeout_seconds=60)
    c.generate(MESSAGES)
    assert fake.requests[0][1] == 10
    now[0] = 0
    class ExpiredIdentity(FakeBackend):
        def identity(self, timeout):
            now[0] += 61
            return super().identity(timeout)
    fake = ExpiredIdentity()
    c = client(fake, clock=lambda:now[0], timeout_seconds=60)
    with pytest.raises(ClientFailure, match="timeout"):
        c.generate(MESSAGES)
    assert not fake.requests and c.calls == 0


def test_late_response_cannot_be_used_even_if_backend_ignores_timeout():
    now = [0.0]
    class SlowResponse(FakeBackend):
        def create(self, payload, timeout):
            result = super().create(payload, timeout)
            now[0] += 61
            return result
    c = client(SlowResponse(), clock=lambda:now[0])
    with pytest.raises(ClientFailure, match="timeout"):
        c.generate(MESSAGES)
    assert c.calls == 1


def test_request_size_cap_does_not_clip_or_send():
    c = client(max_request_bytes=1)
    with pytest.raises(ClientFailure, match="request_size_cap_no_truncation"):
        c.generate(MESSAGES)
    assert c.calls == 0


def test_append_only_request_response_failure_audit(tmp_path):
    sink = JsonlAuditSink(tmp_path/"requests.jsonl", tmp_path)
    cfg = ClientConfig("fixture-model",DIGEST,32768)
    backend = FakeBackend(error=TimeoutError())
    c = ControlledClient(cfg,backend,lambda _:10,ContextBinding(DIGEST,32768,"fixture","b"*64,True),audit_sink=sink)
    with pytest.raises(ClientFailure,match="timeout"):
        c.generate(MESSAGES)
    sink.close()
    events = [json.loads(line) for line in (tmp_path/"requests.jsonl").read_text().splitlines()]
    assert [e["phase"] for e in events] == ["started","request_ready","completed"]
    assert events[1]["data"]["messages"] == MESSAGES
    assert events[-1]["data"]["error"] == "timeout"
    with pytest.raises(FileExistsError):
        JsonlAuditSink(tmp_path/"requests.jsonl",tmp_path)
    bounded = JsonlAuditSink(tmp_path/"bounded.jsonl",tmp_path,max_bytes=1)
    with pytest.raises(ClientFailure,match="audit_storage_cap"):
        bounded({"x":"y"})
    bounded.close()


class FakeHTTP:
    def __init__(self, body, status=200, metadata_digest=DIGEST):
        self.body, self.status, self.metadata_digest = body, status, metadata_digest
        self.calls = []
    def get(self, url, timeout):
        self.calls.append(("GET", url, timeout))
        return SimpleNamespace(status_code=200, json=lambda:{"models":[{"name":"fixture-model", "digest":self.metadata_digest}]})
    def stream(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self
    def __enter__(self):
        self.status_code = self.status
        return self
    def __exit__(self, *args):
        return False
    def iter_bytes(self):
        yield self.body
    def close(self):
        pass


@pytest.mark.parametrize("body,status,reason", [(b"bad json", 200, "response_json_invalid"),
    (b"{}", 302, "model_http_error_302"), (b"{}", 503, "model_http_error_503"),
    (b"x"*100, 200, "response_size_cap")])
def test_http_transport_errors_with_no_network(body, status, reason):
    cfg = ClientConfig("fixture-model", DIGEST, 32768, max_response_bytes=64)
    backend = OllamaHTTPBackend(cfg, permit=LivePermit("c"*64, "d"*64), http_client=FakeHTTP(body, status))
    with pytest.raises(ClientFailure, match=reason):
        backend.create({}, 1)


def local_agents():
    template = "${name} ${partner} ${question} ${information}"
    return [LocalAgent(PrivateView("Alice", "Bob", "Q", "PRIVATE_A"), template),
            LocalAgent(PrivateView("Bob", "Alice", "Q", "PRIVATE_B"), template)]


@pytest.mark.parametrize("style", ["base", "protocol"])
@pytest.mark.parametrize("communicate", [True, False])
def test_controlled_loop_uses_only_visible_inputs_and_no_a2a_can_answer(style, communicate):
    fake = FakeBackend([response("<R>FIRST_FACT</R>"), response("<A>local answer</A>")])
    c = client(fake)
    result = run_controlled(local_agents(), c, ContractTransport(), style,
                            admit=lambda *args:communicate)
    assert result["started"] and result["final_answer"] == "local answer"
    assert result["end_reason"] == "answer" and c.calls == 2
    second = fake.requests[1][0]["messages"]
    assert ("FIRST_FACT" in canonical(second)) == communicate
    assert "PRIVATE_A" not in second[0]["content"] and "PRIVATE_B" in second[0]["content"]
    assert all("request_sha256" in d and "payload_sha256" in d for d in result["messages"])


@pytest.mark.parametrize("failure", [TimeoutError(), ClientFailure("output_truncated"), RuntimeError()])
def test_first_request_failure_stays_in_all_started_denominator(failure):
    c = client(FakeBackend(error=failure))
    result = run_controlled(local_agents(), c, ContractTransport(), "base")
    assert result["started"] and result["final_answer"] is None
    assert len(c.audit) == 1 and result["error_flags"]
    record = {"id":"one", "started":True, "gold":"Paris", "answer":result["final_answer"], "end_reason":result["end_reason"]}
    totals = summarize(["one"], [record])
    assert totals["N_started"] == 1 and totals["mean_F1_all"] == 0


from tests_ext.test_masbench_reasoning_adapter import FIXTURES


@pytest.mark.parametrize("style",["base","protocol"])
@pytest.mark.parametrize("responses",FIXTURES)
def test_controlled_driver_preserves_native_identity_fixture_requests(style,responses):
    from pathlib import Path
    import runpy
    root=Path(__file__).resolve().parents[1]
    templates=runpy.run_path(str(root/"research/logs/masbench-adapter-contract-2026-11-03/reference/Reasoning/src/prompts.py"))
    template=templates["QA_INFO_EXCHANGE_PROMPT"+("_PROTOCOL" if style=="protocol" else "")]
    def pair():
        return [LocalAgent(PrivateView("Alice","Bob","SYNTHETIC Q","PRIVATE_A"),template),
                LocalAgent(PrivateView("Bob","Alice","SYNTHETIC Q","PRIVATE_B"),template)]
    reference=run_fixed(pair(),responses,style,ContractTransport(),max_turns=len(responses))
    c=client(FakeBackend([response(text) for text in responses]))
    result=run_controlled(pair(),c,ContractTransport(),style,max_turns=len(responses))
    assert [a["messages"] for a in c.audit] == reference["requests"]
    for field in ["transcript","memory","final_answer","end_reason"]:
        assert result[field] == reference[field]
