"""C01-C32. Fixed invented fixtures only; real data/model paths forbidden."""
import hashlib
import json
import os
from pathlib import Path
import signal
import time

import pytest

from extensions.masbench_reasoning.application import PrivateView, parse_answer, LocalAgent
from extensions.masbench_reasoning.client import ClientFailure
from extensions.masbench_reasoning.execution_safety import Limits, SafetyError
from extensions.masbench_reasoning.fair_final_v2 import (
    Agent, SYSTEM_SHA, public_clock, system_prompt, parse_output, run_episode, sha, canonical)
from extensions.masbench_reasoning.fair_final_v2_guard import (
    HTTP_CAPS, MODEL, CountProof, FixtureCounter, FairLedger, FixtureDriver,
    PacketBudget, FakeService, resource_guard, verify_receipt, jsonable)
from extensions.masbench_reasoning.fair_final_v2_scoring import score_episode, paired_summary
from extensions.masbench_reasoning.fixture_driver import fixture_rpc
from extensions.masbench_reasoning.wire import ContractTransport, ContractConfig, UL_DATA, Frame


def views():
    return [PrivateView("Alice", "Bob", "List the two invented colors.", "ALICE_PRIVATE red"),
            PrivateView("Bob", "Alice", "List the two invented colors.", "BOB_PRIVATE blue")]


def final(role, answer="red blue", evidence="LOCAL"):
    return f"{role}: FINAL\n<E>{evidence}</E>\n<A>{answer}</A>"


def script():
    return ["Alice: MESSAGE\n<R>red</R>", "Bob: MESSAGE\n<R>blue</R>",
            "Alice: MESSAGE\n<R>red</R>", "Bob: MESSAGE\n<R>blue</R>",
            final("Alice"), final("Bob")]


@pytest.fixture
def make(tmp_path):
    ledgers = []

    def build(condition="Full", outputs=None, plan=None, **kwargs):
        root = tmp_path / ("ledger-" + str(len(ledgers)))
        plan = plan or [dict(id="synthetic-case", family="invented-color", condition=condition, partition="task")]
        ledger = FairLedger(root, plan)
        ledgers.append(ledger)
        return FixtureDriver(ledger, script() if outputs is None else outputs, **kwargs)
    yield build
    for ledger in ledgers:
        ledger.close()


def execute(make, condition="Full", **kwargs):
    driver = make(condition, **kwargs)
    return run_episode(views(), driver, condition, "synthetic-case"), driver


def save(name, value):
    root = os.environ.get("GOSC_OUTPUT_DIR")
    if root:
        p = Path(root) / "evidence"
        p.mkdir(exist_ok=True)
        with (p / (name + ".json")).open("x", encoding="utf-8") as stream:
            json.dump(jsonable(value), stream, ensure_ascii=False, sort_keys=True, indent=2)


def test_C01_six_opportunities(make):
    results = {}
    for condition in ("Full", "No-A2A"):
        r, d = execute(make, condition)
        assert r["completed"] and len(d.traces) == 6
        assert [s["speaker"] for s in r["slots"]] == ["Alice", "Bob"] * 3
        assert [s["stage"] for s in r["slots"]] == ["exchange"] * 4 + ["local_final"] * 2
        assert len(d.ledger.state["requests"]) == 6
        assert d.ledger.state["outputs"] == 3072
        assert len(r["finals"]) == 2
        results[condition] = dict(result=r, counters=d.ledger.state["http"],
                                  counter_proofs=d.counter.calls, wire_events=d.transport.events,
                                  worker_traces=d.traces,
                                  journal=[json.loads(line) for line in (d.ledger.root / "ledger.jsonl").read_text().splitlines()])
    save("C01_complete", results)


def test_C02_clock_and_prompt_bytes(make):
    for role in ("Alice", "Bob"):
        assert sha(system_prompt(role)) == SYSTEM_SHA[role]
    a, _ = execute(make)
    b, _ = execute(make, "No-A2A")
    for i in range(6):
        ca = a["slots"][i]["request"][-1]
        assert ca == b["slots"][i]["request"][-1]
        assert ca["role"] == "user" and ca["content"] == public_clock(i)
        assert set(json.loads(ca["content"])) == {"kind", "protocol", "speaker", "stage", "turn"}


def test_C03_no_a2a_final_not_waiting(make):
    r, d = execute(make, "No-A2A")
    assert r["completed"] and all(f["valid_answer"] for f in r["finals"].values())
    assert r["received_sources"] == [{}, {}]
    assert not any(e.get("event") == "frame" for e in d.transport.events)
    assert all("PEER_MESSAGE" not in canonical(s["request"]) for s in r["slots"])


def test_C04_early_answer_not_terminal(make):
    out = script()
    out[0] = "Alice: MESSAGE\n<A>red blue</A>"
    r, d = execute(make, outputs=out)
    assert r["slots"][0]["parsed"]["reason"] == "invalid_exchange"
    assert r["completed"] and len(d.traces) == 6
    assert len(r["messages"]) == 3 and "t0" not in r["received_sources"][1]
    assert r["finals"]["Alice"]["answer"] == "red blue"


def test_C05_full_string_no_fallback():
    valid = "Alice: MESSAGE\n<Q>color?</Q>\n<R>red</R>"
    assert parse_output(valid, "Alice", "exchange")["valid_format"]
    for text in [valid + "\nextra", "prefix\n" + valid, valid + "\nAlice: MESSAGE",
                 valid + "\n<R>x</R>\n<R>y</R>\n<R>z</R>"]:
        assert not parse_output(text, "Alice", "exchange")["valid_format"]


@pytest.mark.parametrize("text,reason", [(None, "empty_null"), ("", "empty_response"),
    (" \t\r\n", "empty_response"), ("Bob: MESSAGE\n<R>red</R>", "invalid_exchange"),
    ("Alice: MESSAGE\n<r>red</r>", "invalid_exchange"),
    (r"\boxed{red}", "invalid_exchange"), ("Alice: MESSAGE\n<R> </R>", "invalid_exchange")])
def test_C06_empty_and_invalid(text, reason, make):
    assert parse_output(text, "Alice", "exchange")["reason"] == reason
    out = script()
    out[0] = text
    r, d = execute(make, outputs=out)
    assert r["completed"] and len(d.traces) == 6
    assert r["slots"][0]["raw"] == text
    assert r["memory"][0][1]["content"] == ("" if text is None else text)


def test_C07_repeat_and_wrong_facts_not_fixed(make):
    out = script()
    out[0] = "Alice: MESSAGE\n<R>green</R>\n<R>green</R>"
    out[2] = "Alice: MESSAGE\n<R>red</R>"
    r, _ = execute(make, outputs=out)
    req = r["slots"][3]["request"]
    peer = [json.loads(m["content"]) for m in req if m["role"] == "user" and '"PEER_MESSAGE"' in m["content"]]
    assert peer[0]["text"] == out[0] and peer[1]["text"] == out[2]
    assert peer[0]["text"].count("green") == 2
    assert "KNOWLEDGE BOARD" not in canonical(r["memory"])


def test_C08_admission_and_condition_pin(make):
    a, _ = execute(make)
    b, d = execute(make, "No-A2A")
    assert len(a["messages"]) == len(b["messages"]) == 4
    assert all(m["delivered"] for m in a["messages"])
    assert all(not m["delivered"] and m["reason"] == "blocked_by_condition" for m in b["messages"])
    totals = d.transport.totals()
    assert all(totals[k] == 0 for k in ("wire_bytes", "ul_uses", "dl_uses"))
    # Candidate text is still generated/offered and charged locally. Admission
    # blocks all wire frames, not the existence of the candidate payload.
    assert totals["payload_offered_bytes"] > 0
    with pytest.raises(SafetyError, match="condition_plan"):
        run_episode(views(), make("Full"), "No-A2A", "synthetic-case")


def test_C09_last_exchange_delivery_and_source(make):
    r, _ = execute(make)
    msg = r["messages"][3]
    assert msg["source"]["request_sha256"] == r["slots"][3]["request_sha256"]
    assert msg["source"]["payload_sha256"] == sha(r["slots"][3]["parsed"]["text"])
    assert any('"turn":"t3"' in m["content"] for m in r["slots"][4]["request"])
    source = r["received_sources"][0]["t3"]
    assert source["sender"] == "Bob"
    agent = Agent(views()[0])
    with pytest.raises(SafetyError, match="SHA"):
        agent.receive(1, "Bob", script()[1], {"payload_sha256": "0" * 64})


def test_C10_final_isolation(make):
    out = script()
    out[4] = final("Alice", "ALICE_FINAL_SENTINEL")
    r, d = execute(make, outputs=out)
    assert "ALICE_FINAL_SENTINEL" not in canonical(r["slots"][5]["request"])
    assert "ALICE_FINAL_SENTINEL" not in canonical(r["memory"][1])
    assert all(m["source"]["turn"] < 4 for m in r["messages"])
    assert all(e.get("message", 0) < 4 for e in d.transport.events)


def test_C11_private_and_gold_boundary(make):
    r, _ = execute(make)
    assert "BOB_PRIVATE" not in canonical(r["slots"][0]["request"])
    assert "ALICE_PRIVATE" not in canonical(r["slots"][1]["request"])
    assert "red" in canonical(r["slots"][1]["request"])
    assert set(json.loads(r["slots"][0]["request"][1]["content"])) == {"kind", "question", "information"}
    with pytest.raises(TypeError):
        run_episode(views(), make(), "Full", "synthetic-case", gold="FORBIDDEN")


def test_C12_no_controller_injection(make):
    with pytest.raises(TypeError):
        public_clock(0, hidden_state="FORBIDDEN")
    with pytest.raises(SafetyError, match="only_private_view"):
        Agent(dict(question="q", information="i", gold="FORBIDDEN"))
    a = Agent(views()[0])
    a.system += "FORBIDDEN"
    with pytest.raises(SafetyError, match="drift"):
        a.request(0)
    d = make()
    d.is_live = True
    with pytest.raises(SafetyError, match="live_not_authorized"):
        run_episode(views(), d, "Full", "synthetic-case")


@pytest.mark.parametrize("text,valid,answer", [
    (final("Alice"), True, True), ("Alice: FINAL\n<E>LOCAL</E>\n<U>INSUFFICIENT_EVIDENCE</U>", True, False),
    (final("Alice", evidence="LOCAL; PEER:t1"), False, False),
    (final("Alice", "answer"), False, False), (final("Alice", "your answer"), False, False),
    (final("Alice", "THE"), False, False), (final("Alice", ""), False, False),
    (final("Alice") + "<A>red</A>", False, False),
    (final("Alice") + "<U>INSUFFICIENT_EVIDENCE</U>", False, False)])
def test_C13_final_syntax(text, valid, answer):
    r = parse_output(text, "Alice", "local_final")
    assert r["valid_format"] == valid and r["valid_answer"] == answer
    assert parse_output(final("Alice", evidence="LOCAL; PEER:t1,t3"), "Alice", "local_final", {"t1", "t3"})["valid_answer"]
    for e in ("LOCAL; PEER:t3,t1", "LOCAL; PEER:t1,t1", "LOCAL; PEER:t0", "LOCAL; PEER:t1, t3"):
        assert not parse_output(final("Alice", evidence=e), "Alice", "local_final", {"t1", "t3"})["valid_format"]


def scored(a, b, started=True):
    return score_episode(dict(started=started, completed=True, finals={
        "Alice": parse_output(a, "Alice", "local_final"), "Bob": parse_output(b, "Bob", "local_final")}), "red blue")


@pytest.mark.parametrize("fa,fb,na,nb,sf,sn,delta", [
    ("red blue", "red", "blue", "@INVALID", 5/6, 1/3, 1/2),
    ("red blue", "red blue", "@U", "@U", 1, 0, 1),
    ("red", "blue", "red", "blue", 2/3, 2/3, 0),
    ("@DUP", "", "green", "@U", 0, 0, 0),
    ("red red", "green", "red", "green", 1/4, 1/3, -1/12)])
def test_C14_fixed_scoring_vectors(fa, fb, na, nb, sf, sn, delta):
    def pack(role, x):
        if x == "@U":
            return f"{role}: FINAL\n<E>LOCAL</E>\n<U>INSUFFICIENT_EVIDENCE</U>"
        if x == "@DUP":
            return final(role) + "<A>blue</A>"
        if x == "@INVALID":
            return "invalid final"
        return final(role, x) if x else ""
    f = scored(pack("Alice", fa), pack("Bob", fb))
    n = scored(pack("Alice", na), pack("Bob", nb))
    p = paired_summary(["invented"], {"invented": {"Full": f, "No-A2A": n}})
    assert f["mean_F1"] == pytest.approx(sf) and n["mean_F1"] == pytest.approx(sn)
    assert p["Delta_F1"] == pytest.approx(delta)
    if na == nb == "@U":
        assert n["valid_format_rate"] == n["unanswered_rate"] == 1
        assert n["valid_answer_rate"] == 0
    save("C14_" + hashlib.sha256(canonical([fa, fb, na, nb]).encode()).hexdigest()[:10],
         dict(answers=[fa, fb, na, nb], raw_finals=[pack("Alice", fa), pack("Bob", fb),
              pack("Alice", na), pack("Bob", nb)], Full=f, No_A2A=n, paired=p))


def test_C15_no_real_data_or_scoring_import():
    import inspect
    from extensions.masbench_reasoning import fair_final_v2 as app
    assert "fair_final_v2_scoring" not in inspect.getsource(app)
    assert "red blue" not in system_prompt("Alice")
    with pytest.raises(ValueError, match="reference"):
        score_episode({"started": True}, "the")


def test_C16_disagreement_and_rates():
    r = scored(final("Alice", "red"), final("Bob", "blue"))
    assert r["agreement"] == "different" and r["joint"] == "00"
    r = scored(final("Alice"), "")
    assert r["joint"] == "10" and r["valid_answer_rate"] == .5
    assert r["agreement"] == "at_least_one_unanswered" and r["mean_F1"] == .5


def test_C17_started_and_not_started_denominators(make):
    r, d = execute(make, modes={0: {"usage": False}})
    s = score_episode(r, "red blue")
    assert r["started"] and not r["completed"] and s["mean_F1"] == 0
    assert d.ledger.state["outputs"] == 512
    n = score_episode(dict(started=False), "red blue")
    p = paired_summary(["invented"], {"invented": {"Full": s, "No-A2A": n}})
    assert p["Delta_F1"] is None and p["N_pairs_started"] == 0


def test_C18_full_input_boundaries(make):
    ok, d = execute(make, counter=FixtureCounter(15872))
    assert ok["completed"] and d.ledger.state["inputs"] == 6 * 15872
    bad, d = execute(make, counter=FixtureCounter(15873))
    assert not bad["completed"] and len(d.traces) == 0
    assert d.ledger.state["http"]["generation"] == 0
    assert "overflow" in bad["error"]


def test_C19_identity_and_counter_drift(make):
    r, d = execute(make, modes={0: {"manifest": "1" * 64}})
    assert not r["completed"] and not d.traces and d.ledger.state["fenced"]
    r, d = execute(make, counter=FixtureCounter(wrong_hash=True))
    assert not d.traces and "binding" in r["error"]
    with pytest.raises(SafetyError):
        CountProof("0" * 64, 4, context=1024).validate([])


@pytest.mark.parametrize("mode,reason", [({"usage": False}, "usage_unknown"),
    ({"finish_reason": "length"}, "output_truncated"), ({"create_mode": "error"}, "fixture_worker_RuntimeError"),
    ({"create_mode": "hang"}, "timeout")])
def test_C20_failure_no_replay(make, mode, reason):
    r, d = execute(make, modes={0: mode}, timeout=.5 if mode.get("create_mode") == "hang" else 1)
    assert r["error"] == reason and len(d.traces) == 1
    assert d.ledger.state["fenced"] and d.ledger.state["outputs"] == 512
    assert all(s["status"] == "not_dispatched" for s in r["slots"][1:])
    with pytest.raises(SafetyError):
        d.begin("synthetic-case")
    assert len(d.traces) == 1
    save("C20_" + reason, dict(result=r, state=d.ledger.state, trace=d.traces))


def test_C21_all_http_caps_and_partition(tmp_path):
    cap_plan = [dict(id=f"e{i}", family=f"invented{i // 2}", condition="Full" if i % 2 == 0 else "No-A2A",
                     partition="task" if i < 8 else "synthetic") for i in range(10)]
    with FairLedger(tmp_path / "caps", cap_plan) as l:
        for category, limit in HTTP_CAPS.items():
            for i in range(limit):
                if category in {"get", "cleanup_get", "lifecycle_get"}:
                    args = (category, "GET", "/api/ps", None)
                elif category == "unload":
                    args = (category, "POST", "/api/chat", dict(model=MODEL, messages=[], keep_alive=0, stream=False))
                elif category == "render":
                    args = (category, "POST", "/api/chat", {"_debug_render_only": True})
                else:
                    args = (category, "POST", "/v1/chat/completions", {})
                    ep = f"e{i // 6}" if i < 48 else f"e{i - 40}"
                    if l.state["episodes"][ep] == "unstarted":
                        l.episode(ep, "started")
                    l.reserve_dispatch(f"req{i}", ep, 4)
                l.charge_http(*args)
                if category == "generation":
                    l.finish_request(f"req{i}", "completed", dict(prompt_tokens=4, completion_tokens=1))
            with pytest.raises(SafetyError, match="budget"):
                l.charge_http(*args)
        assert sum(l.state["http"].values()) == 468
    plan = [dict(id=x, family="invented", condition="Full", partition="synthetic") for x in ("x", "y")]
    with FairLedger(tmp_path / "partition", plan) as l:
        for i in range(2):
            ep = "x" if i == 0 else "y"
            l.episode(ep, "started")
            l.reserve_dispatch(str(i), ep, 4)
            l.finish_request(str(i), "completed", dict(prompt_tokens=4, completion_tokens=1))
        with pytest.raises(SafetyError, match="partition"):
            l.reserve_dispatch("2", "x", 4)
        assert l.state["outputs"] == 1024


def test_C22_epoch_get_and_readiness(make):
    r, d = execute(make)
    assert r["completed"] and d.ledger.state["http"]["get"] == 19
    assert d.ledger.state["http"]["render"] == 6
    assert d.readiness(60)
    assert d.ledger.state["http"]["lifecycle_get"] == 61
    with pytest.raises(SafetyError, match="readiness_cap"):
        d.readiness(61)
    assert d.ledger.state["http"]["lifecycle_get"] == 122


def test_C23_seven_get_one_unload(make):
    service = FakeService()
    service.stuck = True
    r, d = execute(make, service=service)
    assert not r["completed"] and d.ledger.state["fenced"]
    assert d.ledger.state["http"]["cleanup_get"] == 7
    assert d.ledger.state["http"]["unload"] == 1
    with pytest.raises(SafetyError, match="already"):
        d.cleanup("synthetic-case")


def test_C24_unbound_foreign_and_drift(make):
    for flags in ({"foreign": True}, {"new_runner": True}):
        service = FakeService()
        for k, v in flags.items():
            setattr(service, k, v)
        r, d = execute(make, service=service)
        assert not r["completed"] and d.ledger.state["fenced"]
        if flags.get("foreign"):
            assert d.ledger.state["http"]["unload"] == 0
    d = make()
    d.service.identity = ("foreign", 3)
    r = run_episode(views(), d, "Full", "synthetic-case")
    assert not r["completed"] and d.ledger.state["http"]["unload"] == 0


def test_C25_real_owned_worker_exit_and_crash_fence(tmp_path):
    read_fd, write_fd = os.pipe()
    term_pid = os.fork()
    if term_pid == 0:
        os.close(read_fd)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.write(write_fd, b"R")
        time.sleep(10)
        os._exit(1)
    os.close(write_fd)
    assert os.read(read_fd, 1) == b"R"
    os.close(read_fd)
    os.kill(term_pid, signal.SIGTERM)
    _, term_status = os.waitpid(term_pid, 0)
    assert os.WIFSIGNALED(term_status) and os.WTERMSIG(term_status) == signal.SIGTERM
    trace = {}
    with pytest.raises(TimeoutError):
        fixture_rpc({"create_mode": "hang"}, "create", {}, .05, trace)
    assert trace["pid"] > 0 and os.WIFSIGNALED(trace["exit_status"])
    trace["separate_SIGTERM"] = dict(pid=term_pid, wait_status=term_status)
    with pytest.raises(ProcessLookupError):
        os.kill(trace["pid"], 0)
    plan = [dict(id="x", family="invented", condition="Full", partition="task")]
    root = tmp_path / "crash"
    pid = os.fork()
    if pid == 0:
        l = FairLedger(root, plan)
        l.episode("x", "started")
        l.reserve_dispatch("x/t0", "x", 7)
        os.kill(os.getpid(), signal.SIGKILL)
        os._exit(1)
    _, status = os.waitpid(pid, 0)
    assert os.WIFSIGNALED(status)
    with FairLedger(root, plan) as l:
        assert l.state["fenced"] and l.state["outputs"] == 512
        with pytest.raises(SafetyError):
            l.reserve_dispatch("x/t1", "x", 7)
    save("C25_worker_exit", trace)


def test_C26_stage_and_tail_reserve(make):
    l = make().ledger
    with pytest.raises(SafetyError, match="tail_reserve"):
        l.dispatch_time()
    l.phase("cleanup", 400)
    with pytest.raises(SafetyError, match="phase_budget"):
        l.phase("cleanup", .001)
    assert l.state["phase_spent"]["generate"] == 0
    with pytest.raises(SafetyError):
        l.phase("generate", float("inf"))


def test_C27_resources_are_observations():
    gib = 1024**3
    assert resource_guard(5 * gib, 4 * gib, 0, shared=True)["driver_rss"] == gib
    for values in ((3 * gib, 0, 0), (0, 17 * gib, 0), (0, 0, 17 * gib)):
        with pytest.raises(SafetyError, match="resource"):
            resource_guard(*values)


def test_C28_size_and_storage_no_truncate(make, monkeypatch):
    # Normalization can shrink whitespace; raw safety limit is checked first.
    with pytest.raises(SafetyError, match="raw_output_cap"):
        parse_output(" " * 65537, "Alice", "exchange")
    r = parse_output("Alice: MESSAGE\n<R>" + "x" * 4100 + "</R>", "Alice", "exchange")
    assert r["reason"] == "invalid_exchange" and r["detail"] == "normalized_text_cap"
    for check in (lambda: PacketBudget(ordinary=1).packet("xx"),
                  lambda: PacketBudget(cumulative=1).packet("xx"),
                  lambda: PacketBudget(terminal=1).result("xx")):
        with pytest.raises(SafetyError, match="IPC"):
            check()
    d = make()
    with pytest.raises(SafetyError, match="budget"):
        d.ledger.put_artifact("too-big", b"x" * (8 * 1024**2))
    assert not (d.ledger.root / "artifacts" / "too-big").exists()
    assert d.ledger.state["fenced"]
    d = make()
    original_open = Path.open
    def fail_only_artifact(path, *args, **kwargs):
        if path.name == "write-failure":
            raise OSError("synthetic_disk_write_error")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", fail_only_artifact)
    with pytest.raises(OSError):
        d.ledger.put_artifact("write-failure", b"synthetic")
    assert d.ledger.state["fenced"] and d.ledger.state["bytes"] == 9


def test_C29_wire_loss_crc_and_ttl(make):
    for fault in ("drop", "corrupt"):
        transport = ContractTransport(faults={(UL_DATA, i, a): fault for i in range(4) for a in range(3)})
        r, _ = execute(make, transport=transport)
        assert r["received_sources"] == [{}, {}]
        assert all(not m["delivered"] for m in r["messages"])
    r, _ = execute(make, transport=ContractTransport(ContractConfig(ttl=1)))
    assert not any(r["received_sources"])
    f = Frame(UL_DATA, 1, 0, 0, 2, 0, 0, 1, b"red").encode()
    with pytest.raises(ValueError, match="CRC"):
        Frame.decode(f[:-1] + bytes([f[-1] ^ 1]))


def test_C30_registry_pin_no_body_loader(tmp_path):
    with pytest.raises(SafetyError, match="registry_pin"):
        FairLedger(tmp_path, [dict(id="x", family="invented", condition="Full", partition="task")], registry_sha="0" * 64)
    with pytest.raises(TypeError):
        Agent(views()[0], registry_path="reasoning.json")


def test_C31_synthetic_failure_consumes_no_task(make):
    plan = [dict(id="synthetic-case", family="invented", condition="Full", partition="synthetic"),
            dict(id="task-never-started", family="invented2", condition="Full", partition="task")]
    d = make(plan=plan, modes={0: {"usage": False}})
    r = run_episode(views(), d, "Full", "synthetic-case")
    assert not r["completed"]
    with pytest.raises(SafetyError):
        d.begin("task-never-started")
    assert d.ledger.state["episodes"]["task-never-started"] == "unstarted"
    assert len(d.traces) == 1


def test_C32_receipt_failures_separate_execution():
    expected = {"invented": hashlib.sha256(b"synthetic").hexdigest()}
    assert verify_receipt(expected, {"invented": b"synthetic"}, True)["engineering_accepted"]
    for downloaded in ({}, {"invented": b"corrupt"}, {"invented": b"synthetic", "extra": b"x"}):
        r = verify_receipt(expected, downloaded, True)
        assert r["execution_completed"] and not r["all_outputs_mirrored"] and not r["engineering_accepted"]


def test_legacy_semantics_unchanged():
    assert parse_answer("Alice: MESSAGE\n<A>red.</A>") == "red"
    a = LocalAgent(views()[0], "$name")
    _, payload = a.generate_fixed("<A>red</A>", "protocol")
    assert payload == "Alice: <A>red</A>"
