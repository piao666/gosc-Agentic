"""Passive Public-ToM/BF host snapshots, not an online G1 policy.

The local identity ledger starts at mission initialization. Shadow evaluation is
deliberately absent here: it runs only after observed/unobserved host comparison.
"""
from collections import Counter
import hashlib
import json
import time

from .budget_feasible_information import BudgetInformationSimulation
from .budget_feasible_selector import selection_indices
from .information_identifiability import export_groups, local_age
from .native_information_value import (NativeInformationError, NativeValueContext,
    checked_records, record_json, record_from_json, integer)
from .native_task_wire import WireGOSC, decode_packet, encode_packet

SNAPSHOT_VERSION = 'Native-Shadow-Snapshot-v1'


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(data):
    return hashlib.sha256(canonical(data)).hexdigest()


class OwnEvidenceLedger:
    def __init__(self, sender):
        self.sender = sender
        self.generated = {}
        self.received = {}
        self.received_tasks = {}
        self.generation_t = -1

    def register(self, context, records):
        if context.sender != self.sender:
            raise NativeInformationError('Ledger observer mismatch')
        records = checked_records(context, records)
        for rec in records:
            key, row = rec.t, record_json(rec)
            old = self.generated.get(key)
            if old is not None and old != row:
                raise NativeInformationError('blocked_evidence_identity: generation conflict')
            self.generated[key] = row
        self.generation_t = context.t

    def receive(self, ident, records):
        rows = [record_json(r) for r in records]
        if ident in self.received_tasks:
            if self.received_tasks[ident] != rows:
                raise NativeInformationError('blocked_evidence_identity: task conflict')
            return
        for row in rows:
            if row['agent'] != self.sender or self.generated.get(row['t']) != row:
                raise NativeInformationError('blocked_evidence_identity: unknown own receipt')
            if row['t'] in self.received:
                raise NativeInformationError('blocked_evidence_identity: same Obs in two tasks')
            self.received[row['t']] = ident
        self.received_tasks[ident] = rows

    def checkpoint(self, context, records, outstanding):
        if context.sender != self.sender or self.generation_t != context.t or outstanding:
            raise NativeInformationError('Not a verified real admission boundary')
        records = checked_records(context, records)
        for rec in records:
            if self.generated.get(rec.t) != record_json(rec) or rec.t in self.received:
                raise NativeInformationError('blocked_evidence_identity: unknown/overlap')
        return dict(sender=self.sender, generation_t=self.generation_t,
                    complete_from_initialization=True,
                    generated=[self.generated[k] for k in sorted(self.generated)],
                    received_tasks=[dict(ident=k, records=v)
                                    for k, v in sorted(self.received_tasks.items())])


def verify_checkpoint(context, records, checkpoint):
    if set(checkpoint) != {'sender', 'generation_t', 'complete_from_initialization',
                           'generated', 'received_tasks'}:
        raise NativeInformationError('Checkpoint fields')
    if checkpoint['complete_from_initialization'] is not True:
        raise NativeInformationError('Unverifiable local history')
    ledger = OwnEvidenceLedger(integer(checkpoint['sender'], 0, context.n_agents-1))
    ledger.register(context, [record_from_json(r) for r in checkpoint['generated']])
    if checkpoint['generation_t'] != context.t:
        raise NativeInformationError('Checkpoint clock')
    task_ids = set()
    for item in checkpoint['received_tasks']:
        ident = integer(item['ident'], 0, 2**32-1)
        if ident in task_ids:
            raise NativeInformationError('Duplicate checkpoint task')
        task_ids.add(ident)
        ledger.receive(ident, [record_from_json(r) for r in item['records']])
    return ledger.checkpoint(context, records, ())


class CapturingTomWire(WireGOSC):
    def __init__(self, cfg, channel):
        super().__init__(cfg, channel, 'tom')
        self.last_groups, self.raw_tom = None, {}

    def evidence_voi(self, sim, records, prefixes, team=None):
        values = super().evidence_voi(sim, records, prefixes, team)
        self.raw_tom = dict(values)
        return values

    def build_groups(self, agent, known, view):
        self.raw_tom = {}
        self.last_groups = super().build_groups(agent, known, view)
        return self.last_groups


class NativeShadowHost(BudgetInformationSimulation):
    """Same Public-ToM host; capture at most 8 EVID admissions per sender."""
    def __init__(self, cfg, seed, service_config, policy=None, dl_loss=.05,
                 capture=False, per_sender_cap=8):
        if per_sender_cap != 8:
            raise NativeInformationError('No automatic coverage expansion')
        super().__init__(cfg, seed, service_config, mode='tom', arm='public-fixed',
                         policy=policy, dl_loss=dl_loss, observe=False)
        self.capture = bool(capture)
        self.snapshot_rows = []
        self.admissions, self.blocked, self.capture_counts = Counter(), Counter(), Counter()
        self.evid_admissions, self.entry_log = Counter(), []
        self.ledgers = {k: OwnEvidenceLedger(k) for k in range(cfg.n_agents)}
        self.context_copy_seconds = 0.
        if self.capture:
            self.scheme = CapturingTomWire(cfg, self.channel)

    def phase_decide(self, t):
        super().phase_decide(t)
        if self.capture:
            for agent in self.agents:
                view = self.view(agent)
                context = NativeValueContext.from_local(view, agent.idx)
                self.ledgers[agent.idx].register(context, agent.pending_records)

    def _local_packet(self, receiver, source, ident, payload):
        new = (receiver, source, ident) not in self._local_seen
        super()._local_packet(receiver, source, ident, payload)
        if self.capture and new and receiver == source:
            self.ledgers[receiver].receive(ident, decode_packet(payload, self.cfg).records)

    def phase_communicate(self, t):
        for agent in self.agents:
            if any(k == agent.idx for k, _ in self._outstanding):
                self.blocked[agent.idx] += 1
        return super().phase_communicate(t)

    def select(self, agent, known, view):
        context = checkpoint = records = None
        self.admissions[agent.idx] += 1
        if self.capture and self.capture_counts[agent.idx] < 8 and agent.pending_records:
            start = time.process_time()
            context = NativeValueContext.from_local(view, agent.idx)
            records = checked_records(context, agent.pending_records)
            checkpoint = self.ledgers[agent.idx].checkpoint(context, records,
                [key for key in self._outstanding if key[0] == agent.idx])
            self.context_copy_seconds += time.process_time()-start
        chosen = super().select(agent, known, view)
        if self.capture:
            has_evid = any(g.kind == 'EVID' for g in self.scheme.last_groups)
            self.evid_admissions[agent.idx] += int(has_evid)
            self.entry_log.append(dict(t=view.t, sender=agent.idx, has_evid=has_evid))
        if context is not None:
            groups = self.scheme.last_groups
            if any(g.kind == 'EVID' for g in groups):
                probs, wires = [], []
                for g in groups:
                    probs.append([float(self.channel.success_prob(o.rate, known, n=o.symbols))
                                  for o in g.options])
                    wires.append([encode_packet(self.scheme.packet(agent, g, o, view.t), self.cfg).hex()
                                  for o in g.options])
                factor, stamps = local_age(self.service.knowledge, view, agent.idx, view.t, 'native', True)
                row = dict(schema=SNAPSHOT_VERSION, context=context.to_json(),
                    records=[record_json(r) for r in records], own_history=checkpoint,
                    groups=export_groups(groups), probabilities=probs, payloads=wires,
                    raw_tom={str(k): v for k, v in self.scheme.raw_tom.items()},
                    known=float(known), budget=self.cfg.symbols_per_slot,
                    price=self.scheme.price, native_factor=factor, native_stamps=stamps,
                    selected=selection_indices(groups, chosen),
                    agent=dict(idx=agent.idx, pos=list(agent.pos), target=agent.target,
                        shared_intent=agent.shared_intent,
                        acked_intent=getattr(agent, 'acked_intent', agent.shared_intent),
                        acked_confirms=sorted(getattr(agent, 'acked_confirms', set())),
                        confirmed_pending=sorted(agent.confirmed_pending),
                        pending_llr=agent.pending_llr.tolist()))
                self.snapshot_rows.append(dict(snapshot_sha256=digest(row), snapshot=row))
                self.capture_counts[agent.idx] += 1
        return chosen


def scientific_result(result):
    """One explicitly measured timing field is excluded, nothing scientific."""
    return {k: v for k, v in result.items() if k != 'selection_process_seconds'}


def host_state_digest(host):
    """Outer audit only; never an input to any proxy or selector."""
    return digest(dict(local=[dict(Lc=s.Lc.tolist(), declared=s.declared.tolist(),
        team_pos={str(k): list(v) for k, v in s.team_pos.items()},
        team_intent={str(k): v for k, v in s.team_intent.items()}) for s in host.local],
        agents=[dict(idx=a.idx, pos=list(a.pos), target=a.target,
            pending_llr=a.pending_llr.tolist(), queued_llr=a.queued_llr.tolist(),
            pending_records=[record_json(r) for r in a.pending_records]) for a in host.agents],
        outstanding=sorted([list(k) for k in host._outstanding]),
        local_seen=sorted([list(k) for k in host._local_seen])))
