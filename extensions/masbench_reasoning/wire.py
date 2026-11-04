"""Bounded serial two-hop wire contract, not a deployed radio scheduler.

Fixture service parameters are explicit; no QA hidden state or random channel
is available here. GOSC stochastic-channel integration remains Pending.
"""
from dataclasses import dataclass
import math
import struct
import time
import zlib

HEADER = struct.Struct("!2sBBIIBBIHHH")
CRC = struct.Struct("!I")
UL_DATA, UL_ACK, DL_DATA, DL_ACK = range(1, 5)


@dataclass(frozen=True)
class Frame:
    kind: int
    episode: int
    message: int
    src: int
    dst: int
    created: int
    index: int
    count: int
    payload: bytes = b""

    def encode(self):
        if self.kind not in {UL_DATA, UL_ACK, DL_DATA, DL_ACK}:
            raise ValueError("kind")
        if self.src not in {0, 1, 2} or self.dst not in {0, 1, 2} or self.src == self.dst:
            raise ValueError("route")
        if ((self.kind in {UL_DATA, DL_ACK} and (self.src not in {0, 1} or self.dst != 2))
                or (self.kind in {UL_ACK, DL_DATA} and (self.src != 2 or self.dst not in {0, 1}))):
            raise ValueError("kind/route mismatch")
        if not 0 <= self.index < self.count <= 65535 or len(self.payload) > 16:
            raise ValueError("fragment")
        if self.kind in {UL_ACK, DL_ACK} and self.payload:
            raise ValueError("ACK payload")
        header = HEADER.pack(b"MR", 1, self.kind, self.episode, self.message,
                             self.src, self.dst, self.created, self.index,
                             self.count, len(self.payload))
        data = header + self.payload
        return data + CRC.pack(zlib.crc32(data))

    @classmethod
    def decode(cls, data):
        if len(data) < 28 or zlib.crc32(data[:-4]) != CRC.unpack(data[-4:])[0]:
            raise ValueError("CRC/short frame")
        magic, version, kind, ep, msg, src, dst, created, idx, count, length = HEADER.unpack(data[:24])
        if magic != b"MR" or version != 1 or len(data) != 28 + length:
            raise ValueError("header/length")
        obj = cls(kind, ep, msg, src, dst, created, idx, count, data[24:-4])
        if obj.encode() != data:
            raise ValueError("noncanonical")
        return obj


@dataclass(frozen=True)
class ContractConfig:
    rate: float = 4
    budget: int = 100
    ttl: int = 100000
    deadline: int = 100000
    attempts: int = 3
    rto: int = 6
    cpu_slots: int = 1
    max_body_bytes: int = 65536

    def __post_init__(self):
        if any(type(v) is not int for k, v in vars(self).items() if k != "rate"):
            raise TypeError("Integer service parameters required")
        if isinstance(self.rate, bool) or self.rate not in {0.25, 0.5, 1, 1.5, 2, 3, 4, 5, 6} or self.budget <= 0:
            raise ValueError("radio configuration")
        if min(self.ttl, self.deadline, self.attempts, self.rto, self.cpu_slots, self.max_body_bytes) <= 0:
            raise ValueError("positive bounded configuration required")
        if self.attempts > 3 or self.rto < 2 + 2*self.cpu_slots:
            raise ValueError("retry/RTT bound")
        if self.max_body_bytes > 16*65535:
            raise ValueError("fragment count capacity")


class ContractTransport:
    """One outstanding message; serial frame slots and explicitly paid ACKs.

    Faults is a fixture-only lookup {(kind, fragment, attempt): drop/corrupt}.
    Every served slot is one full frame; an unfit frame is never partly sent.
    CPU slot coefficients are synthetic contract parameters, not measurements.
    """
    def __init__(self, config=None, faults=None, episode_id=1, link_contract=None):
        if not 0 <= episode_id < 2**32:
            raise ValueError("episode identifier")
        self.config = config or ContractConfig()
        self.faults = dict(faults or {})
        if any(v not in {"drop", "corrupt"} for v in self.faults.values()):
            raise ValueError("Unsupported fixture fault")
        self.episode_id, self.slot = episode_id, 0
        self.link_contract = link_contract
        self.events, self.cpu, self.offers = [], [], []
        self.seen_messages = set()

    def expired(self):
        return self.slot >= self.config.deadline

    def application_cpu(self, stage):
        """Synthetic service slot, separate from measured Python process time."""
        start = self.slot
        self.slot = min(self.config.deadline, start+self.config.cpu_slots)
        self.events.append({"event": stage, "start": start, "end": self.slot,
                            "coefficient_scope": "synthetic_contract_only"})
        return not self.expired()

    def transfer(self, message_id, sender, body, admitted=True):
        if message_id in self.seen_messages or not 0 <= message_id < 2**32:
            raise ValueError("duplicate/invalid message identifier")
        if sender not in {0, 1} or not isinstance(body, bytes):
            raise ValueError("sender/body")
        body.decode("utf-8", errors="strict")
        self.seen_messages.add(message_id)
        created = self.slot
        expiry = min(created+self.config.ttl, self.config.deadline)
        result = {"created": created, "offered": created, "enqueued": None,
                  "delivered": False, "receiver_receive": None, "visible": None, "body": b"", "reason": None,
                  "body_bytes": len(body), "barrier_end": created,
                  "offered_fragments": max(1, math.ceil(len(body)/16)),
                  "unique_crc_received_body_bytes": 0, "body_bytes_unreceived": len(body),
                  "application_unavailable_body_bytes": len(body),
                  "pending_background_frames": 0}
        self.offers.append({"message": message_id, "body_bytes": len(body), "admitted": admitted})
        if not admitted or len(body) > self.config.max_body_bytes:
            result["reason"] = "rejected" if not admitted else "queue_capacity"
            return result
        if self.slot >= expiry:
            result["reason"] = "expired"
            return result
        result["enqueued"] = self.slot
        start = time.process_time_ns()
        parts = [body[i:i+16] for i in range(0, len(body), 16)] or [b""]
        self.cpu.append({"stage": "fragment", "process_ns": time.process_time_ns()-start})
        receiver_parts, edge_parts, ack_exhausted = {}, {}, []

        def cpu(stage):
            before = self.slot
            self.slot = min(expiry, self.slot+self.config.cpu_slots)
            self.events.append({"event": stage, "start": before, "end": self.slot})
            return self.slot < expiry

        def send(kind, idx, attempt):
            src, dst = {UL_DATA: (sender, 2), UL_ACK: (2, sender),
                        DL_DATA: (2, 1-sender), DL_ACK: (1-sender, 2)}[kind]
            frame = Frame(kind, self.episode_id, message_id, src, dst, created,
                          idx, len(parts), parts[idx] if kind == UL_DATA else edge_parts[idx] if kind == DL_DATA else b"")
            start_ns = time.process_time_ns()
            raw = frame.encode()
            self.cpu.append({"stage": "encode_crc", "process_ns": time.process_time_ns()-start_ns})
            uses = math.ceil(8*len(raw)/self.config.rate)
            direction = "UL" if kind in {UL_DATA, DL_ACK} else "DL"
            if uses > self.config.budget or self.slot >= expiry:
                self.events.append({"event": "unserved", "kind": kind, "uses_required": uses,
                                    "reason": "frame_unfit" if uses > self.config.budget else "expired"})
                return False, "frame_unfit" if uses > self.config.budget else "expired"
            slot = self.slot
            self.slot += 1
            fault = self.faults.get((kind, idx, attempt))
            link = None
            if self.link_contract is not None:
                link = self.link_contract.evaluate(kind, self.config.rate, uses,
                                                  (self.episode_id, message_id, kind, idx, attempt))
            received = raw if fault != "corrupt" else raw[:-1] + bytes([raw[-1] ^ 1])
            ok = fault != "drop" and (link is None or link["decoded"])
            start_ns = time.process_time_ns()
            try:
                if ok:
                    parsed = Frame.decode(received)
                    if kind == UL_DATA:
                        edge_parts[idx] = parsed.payload
                    elif kind == DL_DATA:
                        receiver_parts[idx] = parsed.payload
            except ValueError:
                ok = False
            self.cpu.append({"stage": "decode_crc", "process_ns": time.process_time_ns()-start_ns})
            self.events.append({"event": "frame", "slot": slot, "end": self.slot,
                                "direction": direction, "kind": kind, "index": idx,
                                "attempt": attempt, "bytes": len(raw), "uses": uses,
                                "rate": self.config.rate, "budget": self.config.budget,
                                "raw_hex": raw.hex(), "success": ok, "fault": fault, "link": link})
            return ok, None

        reason = None
        for idx in range(len(parts)):
            for kind, ack in [(UL_DATA, UL_ACK), (DL_DATA, DL_ACK)]:
                acknowledged = False
                decoded = False
                for attempt in range(self.config.attempts):
                    attempt_start = self.slot
                    if not cpu("encode_ready"):
                        reason = "expired"
                        break
                    ok, error = send(kind, idx, attempt)
                    if error:
                        reason = error
                        break
                    if ok and cpu("decode_ready"):
                        decoded = True
                        if kind == DL_DATA:
                            if len(receiver_parts) == len(parts) and not result["delivered"]:
                                start_ns = time.process_time_ns()
                                rebuilt = b"".join(receiver_parts[j] for j in range(len(parts)))
                                rebuilt.decode("utf-8", errors="strict")
                                self.cpu.append({"stage": "reassemble_utf8", "process_ns": time.process_time_ns()-start_ns})
                                result.update(delivered=True, body=rebuilt, receiver_receive=self.slot)
                        ack_ok, error = send(ack, idx, attempt)
                        if ack_ok and cpu("ack_decode_ready"):
                            acknowledged = True
                            break
                        if error:
                            reason = error
                            break
                    target = min(expiry, attempt_start+self.config.rto)
                    self.events.append({"event": "rto_wait", "start": self.slot,
                                        "end": max(self.slot, target)})
                    self.slot = max(self.slot, target)
                    if self.slot >= expiry:
                        reason = "expired"
                        break
                if not acknowledged:
                    if kind == UL_DATA and decoded and reason is None and self.slot < expiry:
                        # Edge already owns the decoded data. A lost UL ACK
                        # cannot erase it or create a hidden forwarding veto.
                        ack_exhausted.append("UL_ACK")
                        continue
                    reason = reason or "attempts_exhausted"
                    break
            if reason:
                break
        result.update(reason=reason or ("ack_exhausted" if ack_exhausted else "delivered"),
                      ack_exhausted=ack_exhausted, barrier_end=self.slot,
                      unique_crc_received_body_bytes=sum(map(len, receiver_parts.values())),
                      body_bytes_unreceived=len(body)-sum(map(len, receiver_parts.values())),
                      application_unavailable_body_bytes=0 if result["delivered"] else len(body),
                      unreceived_fragment_indices=[i for i in range(len(parts)) if i not in receiver_parts])
        return result

    def totals(self):
        frames = [e for e in self.events if e["event"] == "frame"]
        return {"wire_bytes": sum(e["bytes"] for e in frames),
                "ul_uses": sum(e["uses"] for e in frames if e["direction"] == "UL"),
                "dl_uses": sum(e["uses"] for e in frames if e["direction"] == "DL"),
                "payload_offered_bytes": sum(e["body_bytes"] for e in self.offers),
                "cpu_process_ns": sum(e["process_ns"] for e in self.cpu),
                "logical_slots": self.slot}


class GOSCProbabilityContract:
    """Read-only reuse of GOSC probability law with explicit fixture draws.

    Does not invent QA geometry, access private task state, or generate future
    random values. A real keyed exogenous channel driver is a later gate.
    NumPy/GOSC imports occur only when this optional contract is constructed.
    """
    def __init__(self, snr_ul, snr_dl, draws, error_model="outage"):
        if error_model not in {"outage", "fbl"}:
            raise ValueError("error model")
        if not all(math.isfinite(x) and x > 0 for x in [snr_ul, snr_dl]):
            raise ValueError("finite public SNR required")
        from gosc.channel import Channel
        from gosc.config import Config
        cfg = Config(error_model=error_model, csit=False)
        self.channel = Channel(cfg, (0, 0))
        self.snr_ul, self.snr_dl, self.draws = snr_ul, snr_dl, dict(draws)

    def evaluate(self, kind, rate, uses, key):
        draw = self.draws[key]
        if not math.isfinite(draw) or not 0 <= draw < 1:
            raise ValueError("explicit fixture draw in [0,1) required")
        snr = self.snr_ul if kind in {UL_DATA, DL_ACK} else self.snr_dl
        probability = float(self.channel.success_prob(rate, snr, n=uses))
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("GOSC probability invalid")
        return {"probability": probability, "draw": draw, "decoded": draw < probability,
                "snr_mean": snr, "n_actual_uses": uses}
