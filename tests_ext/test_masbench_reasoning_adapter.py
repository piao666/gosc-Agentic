"""Synthetic-only contracts. All execution belongs on HPC; no model requests."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import socket
import struct
import sys
from types import ModuleType, SimpleNamespace
import zlib

import pytest

from extensions.masbench_reasoning.application import (LocalAgent, PrivateView, parse_answer,
                                                       peer_payload, private_view, run_fixed)
from extensions.masbench_reasoning.evaluation import f1, legacy_comm_words, legacy_summary, summarize
from extensions.masbench_reasoning.wire import (ContractConfig, ContractTransport, Frame,
                                               UL_DATA, UL_ACK, DL_DATA, DL_ACK, GOSCProbabilityContract)

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT/"research/logs/masbench-adapter-contract-2026-11-03/reference/Reasoning/src"


@pytest.fixture(scope="module")
def native():
    index = json.loads((ROOT/"research/logs/masbench-reasoning-static-2026-10-30/source_index_supplement.json").read_text())
    for entry in index["source_file_metadata"]:
        if entry["path"].startswith("Reasoning/src/"):
            data = (REF/Path(entry["path"]).name).read_bytes()
            assert hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest() == entry["git_blob_sha"]
    # Never import the upstream credentials loader or construct a real client.
    api = ModuleType("api_key_loader")

    def forbidden(*args, **kwargs):
        raise AssertionError("Network/model client forbidden in fixture contracts")

    api.get_api = api.get_model_name = forbidden
    old_api = sys.modules.get("api_key_loader")
    old_socket = socket.socket
    socket.socket = forbidden
    sys.modules["api_key_loader"] = api
    package = ModuleType("masbench_frozen_contract")
    package.__path__ = [str(REF)]
    sys.modules[package.__name__] = package
    modules = {}
    try:
        for name in ["agents", "conversation", "metrics", "prompts", "data_loader_v4_mas", "run_asymmetric_agents"]:
            full_name = package.__name__+"."+name
            spec = importlib.util.spec_from_file_location(full_name, REF/(name+".py"))
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_name] = module
            spec.loader.exec_module(module)
            modules[name] = module
        yield SimpleNamespace(**modules)
    finally:
        socket.socket = old_socket
        if old_api is None:
            sys.modules.pop("api_key_loader", None)
        else:
            sys.modules["api_key_loader"] = old_api
        for name in [package.__name__, *[package.__name__+"."+n for n in modules]]:
            sys.modules.pop(name, None)


def agents(native, style):
    template = getattr(native.prompts, "QA_INFO_EXCHANGE_PROMPT"+("_PROTOCOL" if style == "protocol" else ""))
    return [LocalAgent(PrivateView(name, partner, "SYNTHETIC QUESTION", info), template)
            for name, partner, info in [("Alice", "Bob", "PRIVATE_A_SENTINEL"),
                                         ("Bob", "Alice", "PRIVATE_B_SENTINEL")]]


FIXTURES = [
    ["<Q>question</Q>", "<R>one</R>", "<R>two</R>", "<A>Paris.</A>"],
    ["<A>answer</A>", "<A>final answer</A>", "<A></A>", "<A>yes</A>"],
    ["<A>first</A><A>second.</A>"],
    ["\\boxed{first} \\boxed{second}"],
    ["No tagged answer", "still no answer"],
    ["Alice: MESSAGE\n<R>one</R><R>one</R>", "Bob: MESSAGE\n<R> two </R><R>one</R>", "<A>done</A>"],
    ["Alice: internal <A>not-visible</A>\nAlice: MESSAGE\n<Q>request</Q>", "Bob: MESSAGE\n<A>visible</A>"],
    [" Alice: MESSAGE\n<R>中文🙂</R>", "bob: message\n<A>Unicode</A>"],
    ["", None, "<R> </R>", "<A>.</A>"],
    ["<A>good</A><A>answer</A>"],
    ["<A></A> \\boxed{ignored-by-native-empty-tag}"],
    ["<R>fact</R>", "<R>fact</R>", "<R>fact2</R>", "<A>answer:</A>"],
]


@pytest.mark.parametrize("style", ["base", "protocol"])
@pytest.mark.parametrize("responses", FIXTURES)
def test_native_identity_all_requests_memory_stop_and_legacy(native, style, responses):
    ours = agents(native, style)
    fixed_responses = iter(responses)
    requests = []
    native_agents = []
    for own in ours:
        agent = native.agents.OpenAIAgent.__new__(native.agents.OpenAIAgent)
        native.agents.BaseAgent.__init__(agent, own.view.name)
        agent.system_prompt = own.system
        agent.model_name, agent.temperature, agent.max_tokens = "FIXTURE-NO-MODEL", 0.0, 512

        def create(**kwargs):
            requests.append(kwargs["messages"])
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=next(fixed_responses)))])

        agent.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        native_agents.append(agent)
    runner = native.conversation.run_conversation_protocol if style == "protocol" else native.conversation.run_conversation
    transcript, answer = runner(native_agents, max_rounds=len(responses))
    transport = ContractTransport()
    result = run_fixed(ours, responses, style, transport, max_turns=len(responses))
    assert result["requests"] == requests
    assert result["transcript"] == transcript
    assert result["final_answer"] == answer
    assert result["memory"] == [[m.content for m in a.memory] for a in native_agents]
    assert legacy_comm_words(transcript, style) == native.run_asymmetric_agents.compute_comm_tokens(transcript, style)
    assert all(m["delivered"] for m in result["messages"])
    assert transport.slot > 0  # Identity uses real finite frame service, not an instant stub.
    assert all(c["process_ns"] >= 0 for c in result["cpu"]+transport.cpu)


@pytest.mark.parametrize("text", ["", "<A>answer</A>", "<A>answer.</A>", "<A>x</A><A></A>",
                                  "<A>x..</A>", "<a>x</a>", "\\boxed{a}", "<A> answer: </A>"])
def test_native_parser_exact_edge_cases(native, text):
    assert parse_answer(text) == native.conversation.parse_answer(text)


def test_private_view_has_no_peer_gold_or_loader_backreference(native):
    record = {"question": "Q", "answer": "GOLD_SENTINEL", "level": "HIDDEN_LEVEL",
              "raw": "RAW_SENTINEL", "context": {"agent_a": [["A", [" PRIVATE_A "]]],
                                                       "agent_b": [["B", ["PRIVATE_B"]]]}}
    a = private_view(record, "Alice")
    assert a.information == native.data_loader_v4_mas.V4MasDataLoader._build_context_for_agent(record, "agent_a")
    text = repr(a)
    assert all(x not in text for x in ["GOLD_SENTINEL", "HIDDEN_LEVEL", "RAW_SENTINEL", "PRIVATE_B"])
    assert not hasattr(a, "__dict__")
    record["context"]["agent_a"][0][1][0] = "MUTATED"
    assert "MUTATED" not in a.information


def test_lost_fact_never_reappears_via_board(native):
    local = agents(native, "protocol")
    result = run_fixed(local, ["<R>LOST_FACT</R>", "<Q>hello</Q>", "<R>DELIVERED_FACT</R>", "<A>ok</A>"],
                       "protocol", ContractTransport(), admit=lambda src, body, turn: turn != 0)
    assert "LOST_FACT" not in json.dumps(result["requests"][1])
    # Alice may legitimately re-send a fact in its own later payload, but this
    # fixed payload does not do so. Sender's cumulative board must not hitchhike.
    assert "LOST_FACT" not in json.dumps(result["requests"][3])
    assert local[1].facts == ["DELIVERED_FACT"]
    assert "LOST_FACT" in local[0].facts


@pytest.mark.parametrize("style", ["base", "protocol"])
def test_no_a2a_preserves_local_answer_and_private_inputs(native, style):
    transport = ContractTransport()
    result = run_fixed(agents(native, style), ["<Q>q</Q>", "<A>local answer</A>"], style,
                       transport, admit=lambda *args: False)
    assert result["final_answer"] == "local answer"
    assert len(result["memory"][0]) == len(result["memory"][1]) == 1
    assert len(result["requests"][1]) == 1
    assert transport.totals()["wire_bytes"] == 0
    assert transport.totals()["payload_offered_bytes"] > 0


def test_duplicate_delivery_is_idempotent(native):
    local = agents(native, "protocol")[0]
    assert local.receive((1, 1), b"Bob: <R>fact</R>", "protocol")
    assert not local.receive((1, 1), b"Bob: <R>fact</R>", "protocol")
    assert len(local.memory) == len(local.facts) == 1


@pytest.mark.parametrize("body", [b"", b"x", b"x"*16, b"x"*17, "跨片🙂测试".encode()*5])
def test_wire_actual_bytes_integer_budget_and_independent_ledger(body):
    transport = ContractTransport()
    result = transport.transfer(0, 0, body)
    assert result["delivered"] and result["body"] == body
    frames = [e for e in transport.events if e["event"] == "frame"]
    independent_ul = independent_dl = independent_bytes = 0
    for event in frames:
        raw = bytes.fromhex(event["raw_hex"])
        fields = struct.unpack("!2sBBIIBBIHHH", raw[:24])
        assert fields[0:2] == (b"MR", 1)
        assert len(raw) == 28 + fields[-1]
        assert zlib.crc32(raw[:-4]) == int.from_bytes(raw[-4:], "big")
        uses = (8*len(raw)+event["rate"]-1)//event["rate"]
        assert uses == event["uses"] <= event["budget"]
        independent_bytes += len(raw)
        if fields[2] in {UL_DATA, DL_ACK}:
            independent_ul += uses
        else:
            independent_dl += uses
    totals = transport.totals()
    assert (totals["wire_bytes"], totals["ul_uses"], totals["dl_uses"]) == (independent_bytes, independent_ul, independent_dl)
    assert len(frames) == 4*max(1, math.ceil(len(body)/16))
    assert result["receiver_receive"] < result["barrier_end"]
    assert result["visible"] is None  # Application visibility belongs to receive().


@pytest.mark.parametrize("kind", [UL_DATA, UL_ACK, DL_DATA, DL_ACK])
@pytest.mark.parametrize("fault", ["drop", "corrupt"])
def test_each_hop_fault_retries_are_paid_causal_and_identical(kind, fault):
    transport = ContractTransport(faults={(kind, 0, 0): fault})
    result = transport.transfer(0, 1, b"test")
    assert result["delivered"]
    frames = [e for e in transport.events if e["event"] == "frame"]
    assert any(e["attempt"] == 1 for e in frames)
    assert transport.totals()["wire_bytes"] > 4*28 + 2*4
    data_kind = UL_DATA if kind in {UL_DATA, UL_ACK} else DL_DATA
    repeats = [e for e in frames if e["kind"] == data_kind]
    assert len({e["raw_hex"] for e in repeats}) == 1
    assert repeats[1]["slot"]-repeats[0]["slot"] >= transport.config.rto


def test_all_ul_data_losses_exhaust_at_three():
    t = ContractTransport(faults={(UL_DATA, 0, i): "drop" for i in range(3)})
    result = t.transfer(0, 0, b"abc")
    assert not result["delivered"] and result["reason"] == "attempts_exhausted"
    assert len([e for e in t.events if e["event"] == "frame"]) == 3


def test_all_final_dl_ack_losses_do_not_revoke_delivery(native):
    t = ContractTransport(faults={(DL_ACK, 0, i): "drop" for i in range(3)})
    result = t.transfer(0, 0, b"abc")
    assert result["delivered"] and result["reason"] == "attempts_exhausted"
    a = agents(native, "base")[1]
    assert a.receive((1, 0), result["body"], "base")
    assert not a.receive((1, 0), result["body"], "base")


def test_ul_ack_exhaustion_does_not_destroy_edge_data():
    t = ContractTransport(faults={(UL_ACK, 0, i): "drop" for i in range(3)})
    result = t.transfer(0, 0, b"abc")
    assert result["delivered"] and result["ack_exhausted"] == ["UL_ACK"]
    assert len([e for e in t.events if e.get("kind") == UL_DATA]) == 3


@pytest.mark.parametrize("config", [ContractConfig(ttl=4), ContractConfig(deadline=4)])
def test_partial_service_preserves_cost_without_visible_prefix(config):
    t = ContractTransport(config)
    result = t.transfer(0, 0, "🙂".encode()*16)
    assert not result["delivered"] and result["body"] == b""
    assert result["reason"] == "expired"
    assert t.totals()["wire_bytes"] > 0
    assert result["application_unavailable_body_bytes"] == len("🙂".encode()*16)
    assert result["body_bytes_unreceived"]+result["unique_crc_received_body_bytes"] == result["body_bytes"]
    assert result["pending_background_frames"] == 0
    assert t.slot <= min(config.ttl, config.deadline)


def test_unfit_frame_is_unserved_not_free_success():
    t = ContractTransport(ContractConfig(rate=2))
    result = t.transfer(0, 0, b"abc")
    assert result["reason"] == "frame_unfit" and not result["delivered"]
    assert t.totals()["wire_bytes"] == 0
    assert any(e["event"] == "unserved" for e in t.events)


def test_deadline_cannot_publish_late_answer(native):
    t = ContractTransport(ContractConfig(deadline=3))
    result = run_fixed(agents(native, "base"), ["<A>late</A>"], "base", t)
    assert result["final_answer"] is None and result["end_reason"] == "deadline"


def test_capacity_reject_identifier_and_invalid_utf8():
    t = ContractTransport(ContractConfig(max_body_bytes=1))
    assert t.transfer(0, 0, b"large")["reason"] == "queue_capacity"
    with pytest.raises(ValueError):
        t.transfer(0, 0, b"a")
    with pytest.raises(UnicodeDecodeError):
        t.transfer(1, 0, b"\xff")


def test_frame_crc_length_header_and_ack_validation():
    frame = Frame(UL_DATA, 1, 2, 0, 2, 0, 0, 1, b"test").encode()
    assert len(frame) == 32 and Frame.decode(frame).payload == b"test"
    for bad in [b"", frame[:-1], frame[:-1]+bytes([frame[-1]^1]), frame+b"x"]:
        with pytest.raises(ValueError):
            Frame.decode(bad)
    with pytest.raises(ValueError):
        Frame(UL_ACK, 1, 0, 2, 0, 0, 0, 1, b"bad").encode()


def test_all_started_denominator_and_unstarted_explicit(native):
    records = [{"id": "a", "gold": "Paris", "answer": "Paris", "end_reason": "answer"},
               {"id": "b", "gold": "Paris", "answer": None, "end_reason": "turn_limit"},
               {"id": "c", "gold": "Paris", "answer": None, "end_reason": "model_error"},
               {"id": "d", "gold": "Paris", "answer": "Paris", "end_reason": "deadline"}]
    result = summarize(["a", "b", "c", "d", "e"], records)
    assert result["mean_F1_all"] == 0.25
    assert result["legacy_mean_F1_nonNone"] == 1
    assert result["N_started"] == 4 and result["N_not_started"] == 1
    assert result["not_started_ids"] == ["e"] and not result["complete_planned_set"]
    assert result["N_error"] == 1 and result["N_unanswered"] == 3
    for gold, answer in [("The Paris", "paris"), ("one one two", "one two"), ("", "")]:
        assert f1(gold, answer) == native.metrics.cal_f1_score(gold, answer)


def test_invalid_gold_duplicate_and_unplanned_records_fail():
    with pytest.raises(ValueError):
        summarize(["a"], [{"id": "a", "gold": "the", "answer": "the", "end_reason": "answer"}])
    with pytest.raises(ValueError):
        summarize(["a", "a"], [])
    with pytest.raises(ValueError):
        summarize(["a"], [{"id": "b"}])


@pytest.mark.parametrize("model", ["outage", "fbl"])
def test_gosc_probability_uses_actual_frame_n_and_explicit_public_draws(model):
    draws = {(1, 0, k, 0, a): 0.0 for k in [UL_DATA, UL_ACK, DL_DATA, DL_ACK] for a in range(3)}
    link = GOSCProbabilityContract(100, 50, draws, model)
    transport = ContractTransport(link_contract=link)
    result = transport.transfer(0, 0, b"abc")
    assert result["delivered"]
    frames = [e for e in transport.events if e["event"] == "frame"]
    assert len(frames) == 4
    for frame in frames:
        assert frame["link"]["n_actual_uses"] == frame["uses"]
        assert frame["link"]["snr_mean"] == (100 if frame["direction"] == "UL" else 50)
        if model == "outage":
            assert frame["link"]["probability"] == pytest.approx(math.exp(-15/frame["link"]["snr_mean"]))
    with pytest.raises(KeyError):
        GOSCProbabilityContract(1, 1, {}).evaluate(UL_DATA, 4, 88, (1, 0, 1, 0, 0))


def test_frame_kind_route_and_integer_service_rejected():
    with pytest.raises(ValueError):
        Frame(UL_DATA, 1, 0, 2, 0, 0, 0, 1, b"x").encode()
    with pytest.raises(TypeError):
        ContractConfig(ttl=4.0)
    with pytest.raises(ValueError):
        ContractConfig(rto=1)


@pytest.mark.parametrize("style", ["base", "protocol"])
def test_legacy_summary_all_fields_and_zero_denominator(native, style):
    transcripts = [["Alice: <Q>where?</Q>", "Bob: <A>Paris</A>"], ["Alice: no answer"]]
    episodes = [{"transcript": transcripts[0], "final_answer": "Paris"},
                {"transcript": transcripts[1], "final_answer": None}]
    result = legacy_summary(episodes, ["Paris", "Paris"], style)
    words = [native.run_asymmetric_agents.compute_comm_tokens(t, style) for t in transcripts]
    assert result == {"f1_team": [1.0, None], "comm_tokens": words,
                      "comm_tokens_per_turn": [words[0]/2, words[1]],
                      "average_f1_team": 1.0, "average_comm_tokens": sum(words)/2,
                      "f1_per_1k_tokens": 1000/sum(words)}
    assert legacy_summary([{"transcript": [], "final_answer": None}], ["Paris"], style)["f1_per_1k_tokens"] is None


def test_visibility_after_application_cpu_and_next_request(native):
    transport = ContractTransport()
    result = run_fixed(agents(native, "base"), ["hello", "<A>yes</A>"], "base", transport)
    first = result["messages"][0]
    assert first["receiver_receive"] < first["barrier_end"] < first["visible"]
    assert result["times"][1]["request_start_monotonic_ns"] >= first["visible_monotonic_ns"]
    assert all(t["inference_call"] is False for t in result["times"])
