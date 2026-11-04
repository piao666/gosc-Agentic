"""Controlled request interface. Default is fixture-only; no implicit LLM calls.

No credential loader, environment API key, cloud fallback, implicit retry or
model/tokenizer download. Live use needs a separately approved execution task,
verified context/tokenizer binding, and an explicit LivePermit from its driver.
"""
from dataclasses import dataclass, asdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

ENDPOINT = "http://127.0.0.1:11434/v1"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class ClientFailure(RuntimeError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def validate_endpoint(endpoint):
    parsed = urlsplit(endpoint)
    if endpoint != ENDPOINT or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Only exact HPC loopback endpoint is supported")


@dataclass(frozen=True)
class ClientConfig:
    model: str
    manifest_sha256: str
    context_tokens: int
    max_output_tokens: int = 512
    timeout_seconds: float = 60
    max_calls: int = 98
    wall_seconds: float = 2400
    endpoint: str = ENDPOINT
    temperature: float = 0.0
    retries: int = 0
    max_response_bytes: int = 1024*1024
    max_request_bytes: int = 1024*1024

    def __post_init__(self):
        validate_endpoint(self.endpoint)
        if not self.model or not re.fullmatch("[0-9a-f]{64}", self.manifest_sha256):
            raise ValueError("Explicit model/manifest identity required")
        for field in ["context_tokens", "max_output_tokens", "max_calls", "max_response_bytes", "max_request_bytes"]:
            if type(getattr(self, field)) is not int or getattr(self, field) <= 0:
                raise ValueError(field)
        if self.context_tokens <= self.max_output_tokens or self.retries != 0:
            raise ValueError("Context reservation or retry policy")
        if not all(math.isfinite(x) and x > 0 for x in [self.timeout_seconds, self.wall_seconds]):
            raise ValueError("Explicit positive bounded timeouts required")
        if not math.isfinite(self.temperature) or self.temperature != 0:
            raise ValueError("Initial diagnostic fixes temperature=0")


@dataclass(frozen=True)
class LivePermit:
    """Execution-driver contract, not an OS security boundary or user approval.

    This round only tests one with fake HTTP objects. A future driver must bind an explicitly
    approved protocol and development registry; config flags cannot grant user
    authorization by themselves.
    """
    approved_protocol_sha256: str
    registry_sha256: str

    def __post_init__(self):
        if not all(re.fullmatch("[0-9a-f]{64}", x) for x in asdict(self).values()):
            raise ValueError("Execution identity bindings required")


class OllamaHTTPBackend:
    """Actual HTTP implementation is dormant unless explicitly permitted.

    A verified ContextBinding supplies effective context evidence; model
    metadata capacity alone does not set Ollama's configured num_ctx.
    """
    is_live = True

    def __init__(self, config, *, permit=None, http_client=None):
        if not isinstance(permit, LivePermit):
            raise ClientFailure("live_execution_not_authorized")
        validate_endpoint(config.endpoint)
        self.config, self.permit = config, permit
        self.timeout_types = (TimeoutError,)
        self.connection_types = (ConnectionError,)
        try:
            import httpx  # Available in the isolated Reasoning environment.
        except ImportError:
            if http_client is None:
                raise ClientFailure("httpx_dependency_unavailable") from None
        else:
            self.timeout_types += (httpx.TimeoutException,)
            self.connection_types += (httpx.NetworkError,)
        if http_client is None:
            http_client = httpx.Client(timeout=config.timeout_seconds,
                                      follow_redirects=False, trust_env=False)
        self.http = http_client

    def identity(self, timeout):
        try:
            response = self.http.get("http://127.0.0.1:11434/api/tags", timeout=timeout)
            if response.status_code != 200:
                raise ClientFailure("model_metadata_http_error")
            data = response.json()
        except self.timeout_types:
            raise TimeoutError() from None
        except self.connection_types:
            raise ConnectionError() from None
        entries = [x for x in data.get("models", []) if x.get("name") == self.config.model]
        if len(entries) != 1:
            raise ClientFailure("model_identity_missing_or_ambiguous")
        return {"model": entries[0]["name"], "manifest_sha256": entries[0].get("digest")}

    def create(self, payload, timeout):
        # Streaming disabled: a partial body is never treated as a completed answer.
        started = time.monotonic()
        try:
            with self.http.stream("POST", self.config.endpoint+"/chat/completions",
                                  json=payload, timeout=timeout) as response:
                if response.status_code != 200:
                    raise ClientFailure("model_http_error_"+str(response.status_code))
                body = bytearray()
                for chunk in response.iter_bytes():
                    if time.monotonic()-started >= timeout:
                        raise TimeoutError()
                    body.extend(chunk)
                    if len(body) > self.config.max_response_bytes:
                        raise ClientFailure("response_size_cap")
                try:
                    return json.loads(body)
                except (ValueError, UnicodeDecodeError):
                    raise ClientFailure("response_json_invalid") from None
        except self.timeout_types:
            raise TimeoutError() from None
        except self.connection_types:
            raise ConnectionError() from None

    def close(self):
        self.http.close()


@dataclass(frozen=True)
class ContextBinding:
    model_manifest_sha256: str
    effective_context_tokens: int
    tokenizer_id: str
    evidence_sha256: str
    verified: bool = False


class ControlledClient:
    def __init__(self, config, backend, token_counter, binding, *, clock=time.monotonic,
                 permit=None, audit_sink=None):
        self.config, self.backend = config, backend
        self.token_counter, self.binding = token_counter, binding
        self.clock, self.start = clock, clock()
        self.calls, self.audit = 0, []
        self.audit_sink = audit_sink
        self.permit = permit
        if getattr(backend, "is_live", True) and not isinstance(permit, LivePermit):
            raise ClientFailure("live_execution_not_authorized")
        if getattr(backend, "is_live", True) and audit_sink is None:
            raise ClientFailure("live_audit_sink_required")

    def persist(self, phase, row):
        if self.audit_sink is not None:
            data = dict(row)
            if phase == "completed":
                data.pop("messages", None)  # Request is already in request_ready.
            self.audit_sink({"phase": phase, "data": data})

    def generate(self, messages):
        cfg, binding = self.config, self.binding
        row = {"attempt": len(self.audit), "model": cfg.model, "manifest_sha256": cfg.manifest_sha256,
               "endpoint": cfg.endpoint, "retries": 0, "http_attempted": False,
               "usage": None, "usage_missing": True, "error": None,
               "backend_is_live": getattr(self.backend, "is_live", True), "start_monotonic": self.clock()}
        row["execution_binding"] = asdict(self.permit) if isinstance(self.permit, LivePermit) else None
        self.audit.append(row)
        try:
            self.persist("started", row)
            if not binding.verified or not binding.tokenizer_id or not re.fullmatch("[0-9a-f]{64}", binding.evidence_sha256):
                raise ClientFailure("context_tokenizer_binding_unverified")
            if binding.model_manifest_sha256 != cfg.manifest_sha256 or binding.effective_context_tokens != cfg.context_tokens:
                raise ClientFailure("context_model_binding_mismatch")
            if not isinstance(messages, list) or not messages:
                raise ClientFailure("request_schema")
            for index, message in enumerate(messages):
                if (not isinstance(message, dict) or set(message) != {"role", "content"}
                        or message["role"] not in ({"system"} if index == 0 else {"user", "assistant"})
                        or not isinstance(message["content"], str)):
                    raise ClientFailure("request_schema")
            encoded_request = canonical(messages)
            if len(encoded_request.encode()) > cfg.max_request_bytes:
                raise ClientFailure("request_size_cap_no_truncation")
            request = json.loads(encoded_request)  # Freeze caller-owned objects.
            row["messages"] = request
            row["request_sha256"] = sha(request)
            row["context_evidence_sha256"] = binding.evidence_sha256
            prompt_tokens = self.token_counter(request)
            if type(prompt_tokens) is not int or prompt_tokens < 0:
                raise ClientFailure("token_counter_invalid")
            row["prompt_tokens_preflight"] = prompt_tokens
            if prompt_tokens+cfg.max_output_tokens > cfg.context_tokens:
                raise ClientFailure("context_overflow_no_truncation")
            if self.calls >= cfg.max_calls:
                raise ClientFailure("request_count_cap")
            remaining = cfg.wall_seconds-(self.clock()-self.start)
            if remaining <= 0:
                raise ClientFailure("wall_cap")
            operation_left = cfg.timeout_seconds-(self.clock()-row["start_monotonic"])
            if operation_left <= 0:
                raise ClientFailure("timeout")
            identity = self.backend.identity(min(operation_left, remaining))
            row["observed_identity"] = identity
            if identity != {"model": cfg.model, "manifest_sha256": cfg.manifest_sha256}:
                raise ClientFailure("model_identity_changed")
            remaining = cfg.wall_seconds-(self.clock()-self.start)
            if remaining <= 0:
                raise ClientFailure("wall_cap")
            operation_left = cfg.timeout_seconds-(self.clock()-row["start_monotonic"])
            if operation_left <= 0:
                raise ClientFailure("timeout")
            payload = {"model": cfg.model, "messages": request, "temperature": cfg.temperature,
                       "max_tokens": cfg.max_output_tokens, "stream": False}
            row["payload_sha256"] = sha(payload)
            self.persist("request_ready", row)
            self.calls += 1
            row["http_attempted"] = True
            row["generation_timeout_seconds"] = min(operation_left, remaining)
            response = self.backend.create(payload, row["generation_timeout_seconds"])
            row["response"] = response
            row["response_sha256"] = sha(response)
            if self.clock()-self.start >= cfg.wall_seconds:
                raise ClientFailure("wall_cap")
            if self.clock()-row["start_monotonic"] >= cfg.timeout_seconds:
                raise ClientFailure("timeout")
            if len(canonical(response).encode()) > cfg.max_response_bytes:
                raise ClientFailure("response_size_cap")
            if response.get("model") != cfg.model:
                raise ClientFailure("response_model_mismatch")
            choices = response.get("choices")
            if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
                raise ClientFailure("response_schema")
            choice = choices[0]
            reason = choice.get("finish_reason")
            row["finish_reason"] = reason
            if reason == "length":
                raise ClientFailure("output_truncated")
            if reason != "stop":
                raise ClientFailure("unsupported_finish_reason")
            message = choice.get("message", {})
            if not isinstance(message, dict) or not (message.get("content") is None or isinstance(message.get("content"), str)):
                raise ClientFailure("response_schema")
            # Native OpenAIAgent uses `content or ""`; a valid null/empty
            # completion must not silently become a new terminal model error.
            row["empty_completion"] = not message.get("content")
            usage = response.get("usage")
            if usage is not None:
                names = ["prompt_tokens", "completion_tokens", "total_tokens"]
                if (not isinstance(usage, dict) or any(type(usage.get(n)) is not int or usage[n] < 0 for n in names)
                        or usage["prompt_tokens"]+usage["completion_tokens"] != usage["total_tokens"]):
                    raise ClientFailure("usage_invalid")
                row["usage"], row["usage_missing"] = dict(usage), False
                if usage["completion_tokens"] > cfg.max_output_tokens:
                    raise ClientFailure("output_token_cap")
                if usage["prompt_tokens"] != prompt_tokens:
                    raise ClientFailure("prompt_token_count_mismatch_possible_truncation")
            return message.get("content") or ""
        except (TimeoutError, ConnectionError) as e:
            row["error"] = "timeout" if isinstance(e, TimeoutError) else "connection_error"
            raise ClientFailure(row["error"]) from None
        except ClientFailure as e:
            row["error"] = e.reason
            raise
        except Exception as e:
            # No arbitrary exception/HTTP body is printed (could contain secrets).
            row["error"] = "backend_or_protocol_error"
            row["exception_type"] = type(e).__name__
            raise ClientFailure(row["error"]) from None
        finally:
            row["end_monotonic"] = self.clock()
            self.persist("completed", row)


class JsonlAuditSink:
    """Exclusive new bounded local run artifact; flush each phase, never replace."""
    def __init__(self, path, output_root, max_bytes=256*1024*1024):
        path, root = Path(path), Path(output_root).resolve()
        if path.is_symlink() or root not in path.resolve().parents or max_bytes <= 0:
            raise ValueError("Audit path must be a new regular output artifact")
        self.file = path.open("xb")
        self.size, self.max_bytes = 0, max_bytes

    def __call__(self, event):
        body = (canonical(event)+"\n").encode("utf-8")
        if self.size+len(body) > self.max_bytes:
            raise ClientFailure("audit_storage_cap")
        self.file.write(body)
        self.file.flush()
        os.fsync(self.file.fileno())
        self.size += len(body)

    def close(self):
        self.file.close()


def run_controlled(agents, client, transport, style, *, max_turns=6, admit=None,
                   allow_live=False):
    """Sequential application driver; tested with a fake backend this round.

    Returns one started episode even on a failed first request. Gold is never
    an argument. Offline evaluation supplies it after this function returns.
    """
    from .application import parse_answer
    if style not in {"base", "protocol"} or max_turns <= 0 or len(agents) != 2:
        raise ValueError("application configuration")
    if [a.view.name for a in agents] != ["Alice", "Bob"]:
        raise ValueError("ordered Alice/Bob pair required")
    if getattr(client.backend, "is_live", True) and not allow_live:
        raise ClientFailure("live_execution_not_authorized")
    result = {"started": True, "final_answer": None, "end_reason": "turn_limit",
              "transcript": [], "messages": [], "request_audit_indices": [],
              "backend_is_live": getattr(client.backend, "is_live", True),
              "error_flags": [], "usage_missing": False, "cpu_process_ns": []}
    for turn in range(max_turns):
        if transport.expired():
            result["end_reason"] = "deadline"
            break
        speaker, listener = agents[turn % 2], agents[1-turn % 2]
        request_start = time.process_time_ns()
        messages = speaker.request()
        result["cpu_process_ns"].append({"stage": "request", "value": time.process_time_ns()-request_start})
        result["request_audit_indices"].append(len(client.audit))
        try:
            content = client.generate(messages)
        except ClientFailure as e:
            result["error_flags"].append(e.reason)
            result["end_reason"] = "timeout" if e.reason in {"timeout", "wall_cap"} else "model_error"
            break
        row = client.audit[-1]
        result["usage_missing"] |= row["usage_missing"]
        cpu_start = time.process_time_ns()
        full, visible = speaker.generate_fixed(content, style)  # Native postprocessing only.
        body = visible.encode("utf-8")
        result["transcript"].append(full)
        transport.application_cpu("request_and_payload_ready")
        decision = True if admit is None else bool(admit(turn % 2, body, turn))
        delivery = transport.transfer(turn, turn % 2, body, decision)
        delivery["request_sha256"] = row["request_sha256"]
        delivery["response_sha256"] = row["response_sha256"]
        delivery["payload_sha256"] = hashlib.sha256(body).hexdigest()
        result["messages"].append(delivery)
        ready = transport.application_cpu("application_receive_parse_ready")
        if ready and delivery["delivered"]:
            listener.receive((transport.episode_id, turn), delivery["body"], style)
            delivery["visible"] = transport.slot
        answer = parse_answer(visible)
        result["cpu_process_ns"].append({"stage": "postprocess_transport_receive_parse",
                                         "value": time.process_time_ns()-cpu_start})
        if transport.expired():
            result["end_reason"] = "deadline"
            break
        if answer:
            result["final_answer"], result["end_reason"] = answer, "answer"
            break
    result["memory"] = [list(a.memory) for a in agents]
    return result
