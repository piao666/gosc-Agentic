"""One-sender RTT lane and cost contracts. No channel oracle or task policy."""
import math
from dataclasses import dataclass

from .receiver_summary_audit import crc_frame, unframe


@dataclass(frozen=True)
class Attempt:
    tx_slot: int
    created: int
    frame: bytes
    ul_uses: int
    number: int


class RTTLane:
    def __init__(self, sender, delay=0, ttl=20, rate=1.0):
        if not 0 <= sender < 32 or delay < 0 or ttl < 0 or rate <= 0 or not math.isfinite(rate):
            raise ValueError("Invalid lane parameters")
        self.sender, self.delay, self.ttl, self.rate = sender, delay, ttl, rate
        self.pending = None
        self.inflight = None
        self.next_retry = 0
        self.attempts = {}
        self.count = 0
        self.ul_bytes = self.ul_uses = self.retries = 0
        self._attempted_generations = set()
        self._acked = set()
        self._last_generated = -1
        self._last_now = -1
        self._last_tx = -1

    def _clock(self, now):
        if not isinstance(now, int) or not 0 <= now < 512 or now < self._last_now:
            raise ValueError("Nonmonotone/out-of-range mission clock")
        self._last_now = now

    def offer(self, app, now):
        return self._offer(app, now, require_new=True)

    def offer_ready(self, app, now):
        """CPU-completed generation; retain original creation time and TTL."""
        return self._offer(app, now, require_new=False)

    def _offer(self, app, now, require_new):
        self._clock(now)
        frame = crc_frame(app)
        item = unframe(frame, now, max_age=self.ttl)
        if item['sender'] != self.sender or (require_new and item['created'] != now):
            raise ValueError("Offer must be this sender's newly created data")
        if item['created'] <= self._last_generated:
            raise ValueError("At most one new generation per sender/slot")
        self._last_generated = item['created']
        self.pending = (item['created'], frame)
        # Do not reset inflight or its retry deadline when superseding pending.

    def attempt(self, now, capacity, original_used=0):
        self._clock(now)
        if capacity < 0 or original_used < 0 or original_used > capacity:
            raise ValueError("Invalid residual budget")
        if self.pending and now - self.pending[0] > self.ttl:
            self.pending = None
        if self.inflight and now >= self.next_retry:
            self.inflight = None  # timeout expires even if a newer generation waits
        if not self.pending or self.inflight or self._last_tx == now:
            return None
        created, wire = self.pending
        need = math.ceil(len(wire) * 8 / self.rate)
        if need > capacity - original_used:
            return None
        self.count += 1
        result = Attempt(now, created, wire, need, self.count)
        self.attempts[now] = result
        self.inflight = result
        self.next_retry = now + 1 + self.delay
        self._last_tx = now
        self.ul_bytes += len(wire)
        self.ul_uses += need
        self.retries += created in self._attempted_generations
        self._attempted_generations.add(created)
        return result

    def feedback(self, tx_slot, success, now):
        """Consume a decoded ACK entry; wire CRC/cost are validated by the caller."""
        self._clock(now)
        if not isinstance(success, bool) or tx_slot not in self.attempts:
            raise ValueError("Unknown attempt/invalid feedback")
        original = self.attempts[tx_slot]
        if now < tx_slot + 1 + self.delay:
            raise ValueError("Feedback arrived before configured causal latency")
        if success:
            self._acked.add(original.created)
            if self.pending and self.pending[0] == original.created:
                self.pending = None
            # A late ACK may cancel an outstanding retry of this generation only.
            if self.inflight and self.inflight.created == original.created:
                self.inflight = None
        elif self.inflight and self.inflight.tx_slot == tx_slot:
            self.inflight = None
        return original.created

    def censored(self, now):
        self._clock(now)
        return {'pending': self.pending is not None,
                'inflight': self.inflight is not None,
                'ul_bytes': self.ul_bytes, 'ul_uses': self.ul_uses,
                'attempts': self.count, 'retries': self.retries}
