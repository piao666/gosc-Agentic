"""Versioned fair-final application; legacy base/protocol paths are untouched.

No dataset loader, gold, network or live authorization lives in this module.
The v2 entry deliberately rejects live clients in this implementation phase.
"""
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import string

from .application import PrivateView
from .client import ClientFailure
from .execution_safety import SafetyError

VERSION = "T3-R-v2-fair-final-candidate-v1"
TEMPLATE_SHA = "00c91af181b4bcedf62acbfee2ab77b8555392d07a52196d3878936d4a375fb4"
SYSTEM_SHA = {"Alice": "32a381227d081a3cb9e968ae4ba3312379f9bd61a0883dcaf979b01d641ca3e9",
              "Bob": "df0073267f3d594c6597dedbf92f07c70e3e3db647399f1c0e15778b9e1d1da1"}
REGISTRY_SHA = "6d14229ae0dd85a5b3c88b9309fcf86e54fab2523a3701914a7f7ebc06500a86"
SCHEDULE = tuple(("Alice" if t % 2 == 0 else "Bob",
                  "exchange" if t < 4 else "local_final") for t in range(6))
RAW_BYTES = 65536
TEXT_BYTES = 4096


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(value.encode("utf-8", errors="strict")).hexdigest()


def system_prompt(name):
    if name not in SYSTEM_SHA:
        raise SafetyError("role")
    raw = Path(__file__).with_name("fair_final_v2_prompt.txt").read_bytes()
    if hashlib.sha256(raw).hexdigest() != TEMPLATE_SHA:
        raise SafetyError("literal_prompt_SHA")
    peer = "Bob" if name == "Alice" else "Alice"
    text = raw.decode("utf-8").replace("{SELF}", name).replace("{PEER}", peer)
    if sha(text) != SYSTEM_SHA[name]:
        raise SafetyError("role_prompt_SHA")
    return text


def public_clock(turn):
    if type(turn) is not int or turn not in range(6):
        raise SafetyError("turn")
    name, stage = SCHEDULE[turn]
    return canonical(dict(kind="PUBLIC_CLOCK", protocol=VERSION,
                          speaker=name, stage=stage, turn=f"t{turn}"))


def normalized_answer(text):
    """Same mathematical normalization as legacy; no gold in application."""
    return " ".join(re.sub(r"\b(a|an|the)\b", " ", "".join(
        c for c in text.lower() if c not in string.punctuation)).split())


def parse_output(raw, name, stage, received=()):
    """Full match only. Preserve raw, and distinguish null from an empty string.

    Known normal null is an explicit empty completion, not an infrastructure
    error. No mutation of content, role prefix, tag spelling or provenance.
    """
    if name not in SYSTEM_SHA or stage not in {"exchange", "local_final"}:
        raise SafetyError("parser_configuration")
    row = dict(valid_format=False, valid_answer=False, answer=None,
               provenance=[], text=None, reason=None, raw_is_null=raw is None)
    if raw is None:
        row["reason"] = "empty_null"
        return row
    if not isinstance(raw, str):
        raise SafetyError("raw_type")
    try:
        size = len(raw.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise SafetyError("raw_encoding") from exc
    if size > RAW_BYTES:
        raise SafetyError("raw_output_cap")
    text = raw.replace("\r\n", "\n").strip(" \t\r\n")
    row.update(text=text, raw_bytes=size, raw_sha256=sha(raw), text_sha256=sha(text))
    if not text:
        row["reason"] = "empty_response"
        return row
    invalid = "invalid_exchange" if stage == "exchange" else "invalid_final"
    row["reason"] = invalid
    if len(text.encode("utf-8")) > TEXT_BYTES:
        row["detail"] = "normalized_text_cap"
        return row
    # Unicode line separators are line breaks too; no invisible multiline tags.
    content = r"[^<>\x00-\x1f\x7f\x85\u2028\u2029]+"
    if stage == "exchange":
        lines = text.split("\n")
        if lines[0] != name + ": MESSAGE" or not 2 <= len(lines) <= 5:
            return row
        for line in lines[1:]:
            match = re.fullmatch(rf"<(Q|R)>({content})</\1>", line)
            if not match or not match[2].strip():
                return row
        row.update(valid_format=True, reason="message")
        return row
    match = re.fullmatch(rf"{name}: FINAL\n<E>({content})</E>\n"
                         rf"(?:<A>({content})</A>|<U>INSUFFICIENT_EVIDENCE</U>)", text)
    if not match:
        return row
    evidence, answer = match.groups()
    refs = []
    if evidence != "LOCAL":
        if not re.fullmatch(r"LOCAL; PEER:t[0-3](?:,t[0-3])*", evidence):
            row["detail"] = "invalid_provenance"
            return row
        refs = evidence[len("LOCAL; PEER:"):].split(",")
        legal = {"t1", "t3"} if name == "Alice" else {"t0", "t2"}
        if (refs != sorted(set(refs)) or not set(refs) <= legal
                or not set(refs) <= set(received)):
            row["detail"] = "invalid_provenance"
            return row
    if answer is not None and (not normalized_answer(answer) or answer.strip().lower()
                              in {"answer", "your answer", "final answer"}):
        row["detail"] = "placeholder_answer"
        return row
    row.update(valid_format=True, valid_answer=answer is not None, answer=answer,
               provenance=refs, reason="answer" if answer is not None else "abstain")
    return row


@dataclass
class Agent:
    view: PrivateView
    _history: list = field(default_factory=list, init=False, repr=False)
    _received: dict = field(default_factory=dict, init=False, repr=False)
    _requests: int = field(default=0, init=False)

    def __post_init__(self):
        if type(self.view) is not PrivateView:
            raise SafetyError("only_private_view")
        self.system = system_prompt(self.view.name)
        self._initial = {"kind": "LOCAL_TASK", "question": self.view.question,
                         "information": self.view.information}

    def request(self, turn):
        expected = (0 if self.view.name == "Alice" else 1) + 2 * self._requests
        if turn != expected or sha(self.system) != SYSTEM_SHA[self.view.name]:
            raise SafetyError("role_turn_or_prompt_drift")
        self._history.append({"role": "user", "content": public_clock(turn)})
        self._requests += 1
        return json.loads(canonical([
            {"role": "system", "content": self.system},
            {"role": "user", "content": canonical(self._initial)}, *self._history]))

    def remember(self, raw):
        # Explicit null representation; raw JSON null is preserved in result.
        self._history.append({"role": "assistant", "content": "" if raw is None else raw})

    def receive(self, turn, sender, text, source):
        if (turn not in range(4) or SCHEDULE[turn][0] != sender
                or sender == self.view.name or f"t{turn}" in self._received):
            raise SafetyError("peer_source")
        if not parse_output(text, sender, "exchange")["valid_format"]:
            raise SafetyError("invalid_delivered_payload")
        if source.get("payload_sha256") != sha(text):
            raise SafetyError("payload_source_SHA")
        self._received[f"t{turn}"] = dict(source)
        self._history.append({"role": "user", "content": canonical(dict(
            kind="PEER_MESSAGE", sender=sender, turn=f"t{turn}", text=text))})


def run_episode(views, driver, condition, episode_id):
    """Six opportunities; only the versioned model-free driver is admitted.

    No record/gold, controller dictionary, callback or global board argument.
    Infrastructure failure stops the campaign via its persistent ledger.
    """
    if condition not in {"Full", "No-A2A"} or len(views) != 2:
        raise SafetyError("episode_configuration")
    from .fair_final_v2_guard import FixtureDriver
    if type(driver) is not FixtureDriver or driver.is_live is not False:
        raise SafetyError("v2_live_not_authorized")
    if (episode_id not in driver.ledger.plan or
            driver.ledger.plan[episode_id]["condition"] != condition):
        raise SafetyError("condition_plan_binding")
    if [v.name for v in views] != ["Alice", "Bob"] or views[0].question != views[1].question:
        raise SafetyError("view_pair")
    agents = [Agent(v) for v in views]
    result = dict(version=VERSION, id=episode_id, condition=condition, started=False,
                  completed=False, slots=[dict(turn=t, speaker=SCHEDULE[t][0],
                  stage=SCHEDULE[t][1], status="not_dispatched") for t in range(6)],
                  finals={}, messages=[], error=None)
    driver.begin(episode_id)
    result["started"] = True
    try:
        for turn, slot in enumerate(result["slots"]):
            if driver.transport.expired():
                raise SafetyError("wire_deadline")
            speaker, listener = agents[turn % 2], agents[1 - turn % 2]
            slot["status"] = "preparing"
            request = speaker.request(turn)
            slot["request"] = request
            slot["request_sha256"] = sha(canonical(request))
            raw, audit = driver.generate(request, episode_id, turn)
            slot.update(raw=raw, client_audit=audit, status="returned")
            parsed = parse_output(raw, speaker.view.name, slot["stage"], speaker._received)
            slot["parsed"] = parsed
            speaker.remember(raw)
            if turn < 4 and parsed["valid_format"]:
                body = parsed["text"].encode("utf-8")
                ready = driver.transport.application_cpu("v2_payload_ready")
                if not ready:
                    raise SafetyError("wire_deadline")
                delivery = driver.transport.transfer(turn, turn % 2, body, condition == "Full")
                source = dict(turn=turn, sender=speaker.view.name,
                              request_sha256=slot["request_sha256"],
                              response_sha256=audit["response_sha256"], payload_sha256=sha(parsed["text"]))
                delivery["source"] = source
                delivery["reason"] = "offered" if condition == "Full" else "blocked_by_condition"
                result["messages"].append(delivery)
                ready = driver.transport.application_cpu("v2_receive_ready")
                if ready and delivery["delivered"]:
                    if delivery["body"] != body:
                        raise SafetyError("wire_payload_mismatch")
                    listener.receive(turn, speaker.view.name, parsed["text"], source)
            elif turn >= 4:
                result["finals"][speaker.view.name] = parsed
        driver.end(episode_id)
        result["completed"] = True
    except (ClientFailure, SafetyError, UnicodeError) as exc:
        result["error"] = getattr(exc, "reason", str(exc))
        active = next((s for s in result["slots"] if s["status"] == "preparing"), None)
        if active:
            active["status"] = "failed"
        driver.abort(episode_id, result["error"])
    result["memory"] = [json.loads(canonical(a._history)) for a in agents]
    result["received_sources"] = [dict(a._received) for a in agents]
    result["wire_totals"] = driver.transport.totals()
    requests = [v for v in driver.ledger.state["requests"].values() if v["episode"] == episode_id]
    result["accounting"] = dict(reserved_requests=len(requests),
        reserved_input=sum(r["input"] for r in requests), reserved_output=sum(r["output"] for r in requests),
        unknown_usage=sum(r.get("observed_usage") is None for r in requests),
        observed_input=sum((r.get("observed_usage") or {}).get("prompt_tokens", 0) for r in requests),
        observed_output=sum((r.get("observed_usage") or {}).get("completion_tokens", 0) for r in requests),
        http={k: v - driver.epoch_http[k] for k, v in driver.ledger.state["http"].items()},
        scope="synthetic backend and fixture-counter units; no real inference")
    driver.packets.result(result)
    return result
