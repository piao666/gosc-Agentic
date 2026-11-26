"""Persistent v2 counters and an explicitly fake-only execution adapter.

All HTTP labels below describe simulated operations; this file does not open
sockets, start Ollama, read datasets or accept a live backend/authorization.
"""
from dataclasses import dataclass, asdict
import hashlib
import json
import math
from pathlib import Path
import re
import time

from .client import ClientConfig, ClientFailure, ContextBinding, ControlledClient
from .execution_safety import Ledger, Limits, SafetyError
from .fixture_driver import fixture_rpc, _jsonable
from .wire import ContractTransport
from .fair_final_v2 import VERSION, SYSTEM_SHA, REGISTRY_SHA, canonical, sha

MODEL = "fixture-only-not-qwen"
MANIFEST = "0" * 64
HTTP_CAPS = dict(generation=50, render=50, get=160, cleanup_get=70,
                 unload=10, lifecycle_get=128)
PATHS = {"generation": ("POST", "/v1/chat/completions"),
         "render": ("POST", "/api/chat"), "unload": ("POST", "/api/chat")}
GET_PATHS = {"get": {"/api/ps", "/api/version"},
             "cleanup_get": {"/api/ps"},
             "lifecycle_get": {"/api/ps", "/api/version", "/api/tags"}}


def jsonable(value):
    return _jsonable(value)


class PacketBudget:
    def __init__(self, ordinary=65536, cumulative=524288, terminal=8388608):
        self.ordinary, self.cumulative, self.terminal = ordinary, cumulative, terminal
        self.used = 0

    def packet(self, value):
        n = len(canonical(jsonable(value)).encode("utf-8"))
        if n > self.ordinary or self.used + n > self.cumulative:
            raise SafetyError("IPC_packet_or_cumulative_cap")
        self.used += n
        return n

    def result(self, value):
        n = len(canonical(jsonable(value)).encode("utf-8"))
        if n > self.terminal:
            raise SafetyError("IPC_terminal_cap")
        return n


@dataclass(frozen=True)
class CountProof:
    request_sha256: str
    tokens: int
    manifest: str = MANIFEST
    context: int = 16384
    tokenizer_id: str = "fixture-byte-counter-not-qwen"

    def validate(self, messages):
        if (self.request_sha256 != sha(canonical(messages)) or type(self.tokens) is not int
                or self.tokens < 0 or self.manifest != MANIFEST or self.context != 16384
                or not self.tokenizer_id):
            raise SafetyError("complete_input_count_binding")
        if self.tokens + 512 > self.context:
            raise SafetyError("context_overflow_no_truncation")
        return self.tokens


class FixtureCounter:
    """Deterministic synthetic units; never asserted to be model token counts."""
    def __init__(self, tokens=None, wrong_hash=False):
        self.tokens, self.wrong_hash = tokens, wrong_hash
        self.calls = []

    def count(self, messages):
        text = canonical(messages)
        p = CountProof("f" * 64 if self.wrong_hash else sha(text),
                       len(text.encode("utf-8")) // 4 + 1 if self.tokens is None else self.tokens)
        self.calls.append(asdict(p))
        return p


class FairLedger(Ledger):
    """Separate immutable journal namespace; no refunds, no resume dispatch.

    Existing Ledger supplies locking, hash chaining, fsync, boot/deadline,
    token/bytes reservations and failed/inflight request protection.
    """
    def __init__(self, root, plan, *, limits=None, caps=None, registry_sha=REGISTRY_SHA):
        self.artifacts = {}
        if registry_sha != REGISTRY_SHA:
            raise SafetyError("registry_pin_no_loader")
        self.plan = {row["id"]: dict(row) for row in plan}
        if len(self.plan) != len(plan) or not plan:
            raise SafetyError("plan_identity")
        if any(set(r) != {"id", "family", "condition", "partition"} or
               r["condition"] not in {"Full", "No-A2A"} or
               r["partition"] not in {"task", "synthetic"} for r in plan):
            raise SafetyError("plan_schema")
        if any(not isinstance(r["id"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", r["id"])
               or ".." in r["id"] or not isinstance(r["family"], str) or not r["family"] for r in plan):
            raise SafetyError("plan_identifier")
        if (sum(r["partition"] == "task" for r in plan) > 8
                or sum(r["partition"] == "synthetic" for r in plan) > 2
                or any(sum(r["partition"] == "task" and r["condition"] == c for r in plan) > 4
                       for c in ("Full", "No-A2A"))):
            raise SafetyError("plan_episode_cap")
        self.caps = dict(HTTP_CAPS if caps is None else caps)
        if set(self.caps) != set(HTTP_CAPS) or any(type(v) is not int or v < 0 or
                v > HTTP_CAPS[k] for k, v in self.caps.items()):
            raise SafetyError("HTTP_cap_schema")
        limits = limits or Limits(requests=50, metadata=468, input_tokens=793600,
                                  output_tokens=25600, wall_seconds=120,
                                  operation_seconds=1, artifact_bytes=8 * 1024**2)
        if (limits.requests > 50 or limits.metadata > 468 or limits.input_tokens > 793600
                or limits.output_tokens > 25600 or limits.per_output != 512
                or limits.wall_seconds > 19100 or limits.operation_seconds > 180):
            raise SafetyError("candidate_caps_may_only_decrease")
        super().__init__(root, {"schema": "fair-final-v2-model-free-v1", "version": VERSION,
                               "plan": plan, "caps": self.caps, "registry": registry_sha,
                               "system_SHA": SYSTEM_SHA, "live_authorized": False}, self.plan, limits)
        if any(v == "started" for v in self.state["episodes"].values()):
            self.state["fenced"] = True
        try:
            for name, record in self.artifacts.items():
                p = self.root / "artifacts" / name
                if not p.is_file() or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest() != record["sha256"]:
                    raise SafetyError("reserved_artifact_missing_or_changed")
        except BaseException:
            self.close()
            raise

    def _apply(self, event):
        kind = event["kind"]
        if kind == "v2-http":
            self.state["http"][event["category"]] += 1
            if event["category"] == "generation":
                self.state["http_generated_ids"].append(event["request_id"])
            return
        if kind == "v2-fence":
            self.state["fenced"] = True
            self.state["failure"] = event["reason"]
            return
        if kind == "v2-slot":
            self.state["slots"][event["id"]] = event["status"]
            return
        if kind == "v2-cleanup":
            self.state["cleanup"][event["episode"]] = event["status"]
            return
        if kind == "v2-phase":
            self.state["phase_spent"][event["phase"]] += event["seconds"]
            return
        super()._apply(event)
        if kind == "bytes":
            if event["path"] in self.artifacts:
                raise SafetyError("artifact_replay")
            self.artifacts[event["path"]] = event
        if kind == "init":
            self.state.update(http=dict.fromkeys(HTTP_CAPS, 0), slots={}, cleanup={}, http_generated_ids=[],
                              phase_spent=dict(prepare=0., generate=0., cleanup=0.,
                                               lifecycle=0., application=0., audit=0.,
                                               transfer=0., reserve=0.))

    def fence(self, reason):
        self._append({"kind": "v2-fence", "reason": str(reason)})

    def put_artifact(self, relative, data):
        try:
            if relative in self.artifacts:
                raise SafetyError("artifact_replay")
            return super().put_artifact(relative, data)
        except (OSError, SafetyError):
            self.state["fenced"] = True
            try:
                self.fence("artifact_write_or_budget")
            except (OSError, SafetyError):
                pass  # In-memory fence and existing prefix survive disk failure.
            raise

    def slot(self, episode, turn, status):
        key = f"{episode}/t{turn}"
        if status == "preparing":
            self._admit()
            if key in self.state["slots"] or type(turn) is not int or turn not in range(6):
                raise SafetyError("slot_replay")
        elif key not in self.state["slots"]:
            raise SafetyError("unknown_slot")
        self._append(dict(kind="v2-slot", id=key, status=status))

    def charge_http(self, category, method, path, body=None):
        if category not in HTTP_CAPS:
            raise SafetyError("HTTP_category")
        if category in PATHS:
            if (method, path) != PATHS[category]:
                raise SafetyError("HTTP_path")
            if category == "unload" and body != dict(model=MODEL, messages=[], keep_alive=0, stream=False):
                raise SafetyError("unload_body")
            if category == "render" and (not isinstance(body, dict) or body.get("_debug_render_only") is not True):
                raise SafetyError("render_body")
        elif method != "GET" or path not in GET_PATHS[category] or body is not None:
            raise SafetyError("HTTP_path")
        if category not in {"cleanup_get", "unload", "lifecycle_get"}:
            self._admit()
        if self.state["http"][category] >= self.caps[category] or sum(self.state["http"].values()) >= 468:
            raise SafetyError("HTTP_budget")
        request_id = None
        if category == "generation":
            inflight = [k for k, r in self.state["requests"].items() if r["status"] == "inflight"]
            if len(inflight) != 1 or inflight[0] in self.state["http_generated_ids"]:
                raise SafetyError("generation_requires_unique_reservation")
            request_id = inflight[0]
        self._append(dict(kind="v2-http", category=category, method=method, path=path,
                          body_sha256=sha(canonical(body)), request_id=request_id, fake_operation=True))

    def reserve_dispatch(self, rid, episode, p):
        partition = self.plan[episode]["partition"]
        current = list(self.state["requests"].values())
        if (sum(r["episode"] == episode for r in current) >= (6 if partition == "task" else 1) or
            sum(self.plan[r["episode"]]["partition"] == partition for r in current)
                >= (48 if partition == "task" else 2)):
            raise SafetyError("partition_or_episode_cap")
        # Per-condition caps hold even when task/synthetic plans interleave.
        if partition == "task" and sum(self.plan[r["episode"]]["partition"] == "task" and
                self.plan[r["episode"]]["condition"] == self.plan[episode]["condition"]
                for r in current) >= 24:
            raise SafetyError("condition_cap")
        self.reserve_request(rid, episode, p, 512)

    def start_cleanup(self, episode):
        if episode in self.state["cleanup"]:
            raise SafetyError("cleanup_already_attempted")
        self._append(dict(kind="v2-cleanup", episode=episode, status="attempted"))

    def phase(self, phase, seconds):
        caps = dict(prepare=7500, generate=9000, cleanup=400, lifecycle=600,
                    application=600, audit=120, transfer=600, reserve=280)
        if phase not in caps or isinstance(seconds, bool) or not math.isfinite(seconds) or seconds < 0:
            raise SafetyError("phase_schema")
        if self.state["phase_spent"][phase] + seconds > caps[phase]:
            raise SafetyError("phase_budget")
        self._append(dict(kind="v2-phase", phase=phase, seconds=seconds))

    def dispatch_time(self, prepare=150, generate=180, cleanup=40, tail=1600):
        # Candidate wall semantics only; the fixture run has its own short cap.
        if self.remaining() < prepare + generate + cleanup + tail:
            raise SafetyError("tail_reserve")


class FakeService:
    """Synthetic identity observations, not evidence about a real server."""
    def __init__(self):
        self.identity = ("synthetic-service", 1)
        self.bound_identity = self.identity
        self.runner = None
        self.next_runner = 1
        self.old = None
        self.foreign = False
        self.stuck = False
        self.new_runner = False

    def observe(self):
        return [] if self.runner is None else [self.runner]

    def load(self):
        if self.runner is None:
            self.runner = ("synthetic-runner", self.next_runner)
            self.next_runner += 1
        self.old = self.runner

    def unload(self):
        if not self.stuck:
            self.runner = ("unbound-synthetic-runner", 9) if self.new_runner else None


def resource_guard(driver_bytes, service_bytes, gpu_bytes, *, shared=False):
    """Pure observation guard. 'shared' inputs use union/subtree subtraction."""
    if shared:
        driver_bytes -= service_bytes
    if min(driver_bytes, service_bytes, gpu_bytes) < 0 or any(
            v > limit for v, limit in zip((driver_bytes, service_bytes, gpu_bytes),
                                         (2 * 1024**3, 16 * 1024**3, 16 * 1024**3))):
        raise SafetyError("resource_observation_stop")
    return dict(driver_rss=driver_bytes, service_rss=service_bytes, gpu_bytes=gpu_bytes,
                scope="observation-not-hard-isolation")


class FixtureDriver:
    is_live = False

    def __init__(self, ledger, outputs, *, counter=None, transport=None, timeout=1,
                 modes=None, service=None):
        self.ledger = ledger
        self.outputs = list(outputs)
        self.counter = counter or FixtureCounter()
        self.transport = transport or ContractTransport()
        self.service = service or FakeService()
        self.packets = PacketBudget()
        self.timeout = timeout
        self.modes = dict(modes or {})
        self.traces, self.cleanup_errors = [], []
        self.client_audits = []
        self.touched = False

    def begin(self, episode):
        self.ledger.episode(episode, "started")
        self.epoch_http = dict(self.ledger.state["http"])

    def readiness(self, ready_after=0):
        self.ledger._admit()
        for i in range(61):
            self.ledger.charge_http("lifecycle_get", "GET", "/api/version")
            if i >= ready_after:
                return True
        raise SafetyError("readiness_cap")

    def generate(self, messages, episode, turn):
        l = self.ledger
        l.slot(episode, turn, "preparing")
        self.packets.packet(messages)
        proof = self.counter.count(messages)
        p = proof.validate(messages)
        if not self.touched:
            l.charge_http("get", "GET", "/api/ps")
            if self.service.observe():
                raise SafetyError("nonempty_epoch")
            self.touched = True
        l.charge_http("render", "POST", "/api/chat", {"_debug_render_only": True})
        self.service.load()
        l.charge_http("get", "GET", "/api/ps")
        l.charge_http("get", "GET", "/api/version")
        driver = self
        rid = f"{episode}/t{turn}"
        mode = self.modes.get(turn, {})

        class Backend:
            is_live = False

            def identity(self, timeout):
                l.charge_http("get", "GET", "/api/ps")
                if driver.service.identity != driver.service.bound_identity:
                    raise ClientFailure("service_identity_drift")
                return dict(model=MODEL, manifest_sha256=mode.get("manifest", MANIFEST))

            def create(self, payload, timeout):
                l.reserve_dispatch(rid, episode, p)
                l.charge_http("generation", "POST", "/v1/chat/completions", payload)
                l.slot(episode, turn, "dispatched")
                trace = {}
                try:
                    return fixture_rpc({"text": driver.outputs[turn], "prompt_usage_offset": p - 4,
                                        **mode}, "create", payload, timeout, trace)
                finally:
                    driver.traces.append(trace)

        cfg = ClientConfig(MODEL, MANIFEST, 16384, max_calls=1, timeout_seconds=self.timeout,
                           wall_seconds=max(.001, l.remaining()), max_request_bytes=65536,
                           max_response_bytes=524288)
        binding = ContextBinding(MANIFEST, 16384, proof.tokenizer_id, sha(canonical(asdict(proof))), True)
        def persist(event):
            # ControlledClient omits duplicate messages in 'completed'; the
            # request_ready artifact holds the exact original input once.
            relative = f"{rid}/{event['phase']}.json"
            l.put_artifact(relative, (canonical(event) + "\n").encode("utf-8"))
        client = ControlledClient(cfg, Backend(), lambda frozen: proof.validate(frozen), binding,
                                  audit_sink=persist)
        try:
            client.generate(messages)
            row = client.audit[-1]
            self.client_audits.append(row)
            if row["usage_missing"]:
                raise ClientFailure("usage_unknown")
            u = row["usage"]
            l.finish_request(rid, "completed", dict(prompt_tokens=u["prompt_tokens"],
                                                     completion_tokens=u["completion_tokens"]))
            raw = row["response"]["choices"][0]["message"]["content"]
            self.packets.packet(raw)
            l.slot(episode, turn, "returned")
            return raw, row
        except (ClientFailure, SafetyError, OSError):
            if client.audit and (not self.client_audits or self.client_audits[-1] is not client.audit[-1]):
                self.client_audits.append(client.audit[-1])
            raise

    def cleanup(self, episode):
        l = self.ledger
        l.start_cleanup(episode)
        if self.service.identity != self.service.bound_identity:
            raise SafetyError("foreign_service_do_not_unload")
        l.charge_http("cleanup_get", "GET", "/api/ps")
        old = self.service.old
        if not old or self.service.foreign or any(x != old for x in self.service.observe()):
            raise SafetyError("missing_or_unbound_runner")
        l.charge_http("unload", "POST", "/api/chat", dict(model=MODEL, messages=[], keep_alive=0, stream=False))
        self.service.unload()
        for _ in range(6):
            l.charge_http("cleanup_get", "GET", "/api/ps")
            if not self.service.observe() and self.service.runner != old:
                l._append(dict(kind="v2-cleanup", episode=episode, status="verified-fixture-only"))
                self.touched = False
                return
        raise SafetyError("runner_exit_unverified")

    def end(self, episode):
        self.cleanup(episode)
        self.ledger.episode(episode, "completed")

    def abort(self, episode, reason):
        l = self.ledger
        for rid, r in list(l.state["requests"].items()):
            if r["status"] == "inflight":
                l.finish_request(rid, "failed", None, True)
        l.fence(reason)
        if self.touched and episode not in l.state["cleanup"]:
            try:
                self.cleanup(episode)
            except SafetyError as exc:
                self.cleanup_errors.append(str(exc))
        l.episode(episode, "failed")


def verify_receipt(expected, downloaded, execution_completed):
    """Pure full-transfer verifier; never equates execution with mirror state."""
    if not isinstance(expected, dict) or not isinstance(downloaded, dict):
        raise SafetyError("receipt_schema")
    ok = set(expected) == set(downloaded) and all(
        isinstance(v, bytes) and hashlib.sha256(v).hexdigest() == expected[k]
        for k, v in downloaded.items())
    return dict(execution_completed=bool(execution_completed), all_outputs_mirrored=ok,
                engineering_accepted=bool(execution_completed) and ok)
