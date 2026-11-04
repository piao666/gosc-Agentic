"""Local-only application state; no model/network client or reference answers.

Parser/format semantics adapted from BUPT-GAMMA/MASBench c0301a6,
Reasoning/src/{agents,conversation}.py, MIT; see the pinned reference LICENSE
in research/logs/masbench-adapter-contract-2026-11-03/reference/.
"""
from dataclasses import dataclass, field
import re
from string import Template
import time

ANSWER = re.compile(r"<A>(.*?)</A>", re.DOTALL)
BOXED = re.compile(r"\\boxed\{(.+?)\}")
FACT = re.compile(r"<R>(.*?)</R>", re.DOTALL)


def parse_answer(text):
    if not text:
        return None
    for candidate in reversed(ANSWER.findall(text)):
        cleaned = candidate.strip()
        if cleaned.lower() in {"answer", "final answer", "the answer", "answer:"}:
            continue
        if cleaned.endswith("."):
            cleaned = cleaned[:-1]
        return cleaned
    match = BOXED.search(text)
    return match.group(1).strip() if match else None


def peer_payload(full, name, style):
    if style == "base":
        return full
    if style != "protocol":
        raise ValueError("Unsupported prompt family")
    match = re.search(rf"^\s*{re.escape(name)}:\s*MESSAGE\b", full,
                      re.MULTILINE | re.IGNORECASE)
    return (full[match.start():].strip() if match else full) or full


@dataclass(frozen=True, slots=True)
class PrivateView:
    name: str
    partner: str
    question: str
    information: str

    def __post_init__(self):
        if {self.name, self.partner} != {"Alice", "Bob"}:
            raise ValueError("Only Alice/Bob")
        if not all(isinstance(x, str) for x in
                   (self.question, self.information)):
            raise TypeError("Private view must contain strings")


def private_view(record, name):
    """Offline boundary: copy only question and the selected native context.

    Caller retains the dataset trust domain. No record is stored in the view.
    This is API isolation, not a security sandbox for untrusted Python code.
    """
    if name not in {"Alice", "Bob"}:
        raise ValueError(name)
    lines = []
    for title, passages in record["context"]["agent_a" if name == "Alice" else "agent_b"]:
        lines.append(f"Article: {title}")
        for passage in passages:
            passage = (passage or "").strip()
            if passage:
                lines.append(f"Sentence: {passage}")
        lines.append("")
    return PrivateView(name, "Bob" if name == "Alice" else "Alice",
                       record["question"], "\n".join(lines).strip())


@dataclass
class LocalAgent:
    view: PrivateView
    template: str | Template
    memory: list = field(default_factory=list, init=False)
    facts: list = field(default_factory=list, init=False)
    received: set = field(default_factory=set, init=False)

    def __post_init__(self):
        template = self.template if isinstance(self.template, Template) else Template(self.template)
        self.system = template.safe_substitute(
            name=self.view.name, partner=self.view.partner, question=self.view.question,
            information=self.view.information or f"(empty for {self.view.name})")

    def request(self):
        return [{"role": "system", "content": self.system}] + [
            {"role": "assistant" if text.strip().startswith(self.view.name + ":") else "user",
             "content": text} for text in self.memory]

    def add_facts(self, visible):
        for fact in FACT.findall(visible):
            fact = fact.strip()
            if fact and fact not in self.facts:
                self.facts.append(fact)

    def generate_fixed(self, response, style):
        """Apply native postprocessing to an injected fixed string, never an LLM."""
        full = (response or "").strip()
        if not full.startswith(self.view.name + ":"):
            full = f"{self.view.name}: {full}"
        self.memory.append(full)
        visible = peer_payload(full, self.view.name, style)
        if style == "protocol":
            self.add_facts(visible)
        return full, visible

    def receive(self, message_id, body, style):
        if message_id in self.received:
            return False
        visible = body.decode("utf-8", errors="strict")
        if style == "protocol":
            self.add_facts(visible)
            if self.facts:
                board = "\n".join(f"{i+1}. {fact}" for i, fact in enumerate(self.facts))
                visible += ("\n\n--- SHARED KNOWLEDGE BOARD (Cumulative Facts) ---\n"
                            + board + "\n-------------------------------------------------")
        self.memory.append(visible)
        self.received.add(message_id)
        return True


def run_fixed(agents, responses, style, transport, max_turns=10, admit=None):
    """Synthetic contract harness, deliberately no live model entry point."""
    if len(agents) != 2 or [a.view.name for a in agents] != ["Alice", "Bob"]:
        raise ValueError("Ordered Alice/Bob pair required")
    if style not in {"base", "protocol"} or max_turns < 0:
        raise ValueError("Invalid application configuration")
    transcript, requests, costs, messages, times = [], [], [], [], []
    final, reason = None, "turn_limit"
    for turn, response in enumerate(responses[:max_turns]):
        if transport.expired():
            reason = "deadline"
            break
        speaker, listener = agents[turn % 2], agents[1 - turn % 2]
        start = time.process_time_ns()
        wall_start = time.monotonic_ns()
        requests.append(speaker.request())
        full, visible = speaker.generate_fixed(response, style)
        transcript.append(full)
        body = visible.encode("utf-8", errors="strict")
        costs.append({"stage": "request_fixed_generation_payload", "process_ns": time.process_time_ns()-start,
                      "model_calls": 0, "model_usage": None})
        times.append({"turn": turn, "request_start_monotonic_ns": wall_start,
                      "fixed_return_monotonic_ns": time.monotonic_ns(), "inference_call": False})
        if not transport.application_cpu("request_and_payload_ready"):
            reason = "deadline"
            break
        # Admission sees sender-side payload metadata only. No peer state or gold.
        allowed = True if admit is None else bool(admit(turn % 2, body, turn))
        result = transport.transfer(turn, turn % 2, body, allowed)
        messages.append(result)
        start = time.process_time_ns()
        ready = transport.application_cpu("application_receive_parse_ready")
        if result["delivered"] and ready:
            listener.receive((transport.episode_id, turn), result["body"], style)
            result["visible"] = transport.slot
            result["visible_monotonic_ns"] = time.monotonic_ns()
        answer = parse_answer(visible)
        costs.append({"stage": "receive_board_parse", "process_ns": time.process_time_ns()-start})
        if transport.expired():
            reason = "deadline"
            break
        if answer:
            final, reason = answer, "answer"
            break
    return {"transcript": transcript, "requests": requests, "final_answer": final,
            "end_reason": reason, "memory": [list(a.memory) for a in agents],
            "facts": [list(a.facts) for a in agents], "cpu": costs, "messages": messages,
            "times": times}
