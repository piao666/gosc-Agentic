"""Prospective information-use controls and passive GP-v2 observation.

No historical logs are backfilled. Observation has no controller input or RNG.
Logical service reservations are inherited assumptions, not measured hardware.
"""
from collections import defaultdict, deque
from dataclasses import dataclass, replace
import hashlib
import math
import time

from gosc.schemes import Group, Option, lagrangian_select
from .causal_paid_service import CausalPaidService
from .causal_paid_simulation import CausalPaidSimulation
from .wire_periodic import WirePeriodic


@dataclass(frozen=True)
class InformationRule:
    legacy_arm: str
    age_source: str = 'none'
    form: str = 'scale'


# paid-native-age is needed to separate information use from purchasing service.
# Position x age controls prevent attributing a changed threshold to pose content.
RULES = {
    'public-fixed': InformationRule('public'),
    'native-age': InformationRule('public', 'native'),
    'native-price': InformationRule('public', 'native', 'price'),
    'paid-ignore': InformationRule('ignore'),
    'paid-native-age': InformationRule('ignore', 'native'),
    'paid-age': InformationRule('age', 'paid'),
    'paid-price': InformationRule('age', 'paid', 'price'),
    'paid-pose': InformationRule('pose'),
    'paid-pose-native-age': InformationRule('pose', 'native'),
    'paid-pose-age': InformationRule('pose', 'paid'),
}


def local_age(knowledge, view, sender, now, source, include_trace=False):
    """Only this sender's received ledger/cache. Native-only never reads cache."""
    if source not in ('none', 'native', 'paid'):
        raise ValueError('Unknown timestamp source')
    if view.cfg.tom_oracle or now != view.t or sender not in knowledge.native:
        raise ValueError('Observer/time/oracle boundary')
    eligible = {}
    if source == 'paid':
        for peer, item in knowledge.cache[sender].items():
            native = knowledge.native[sender].get(peer)
            if (peer != sender and peer in view.team_pos and native is not None
                    and native.pos == tuple(view.team_pos[peer])
                    and item.created < item.received <= now <= item.valid_until
                    and item.created > native.created):
                eligible[peer] = item
    ages, trace = [], []
    for peer, native in knowledge.native[sender].items():
        if peer == sender:
            continue
        if native.created > now:
            raise ValueError('Future native timestamp')
        item = eligible.get(peer)
        created = item.created if item is not None else native.created
        age = max(0, now - created)
        ages.append(age)
        if include_trace:
            trace.append(dict(peer=int(peer), native_created=int(native.created),
                              native_pos=list(native.pos),
                              selected_created=int(created), age=int(age),
                              timestamp_source='summary' if item is not None else 'native',
                              received=None if item is None else int(item.received),
                              valid_until=None if item is None else int(item.valid_until)))
    mean = sum(ages) / len(ages) if ages else 0.
    return (1. if source == 'none' else 1. / (1. + mean)), trace


def selection_signature(chosen):
    return [dict(kind=g.kind, cell=None if g.cell is None else int(g.cell),
                 rate=float(o.rate), bits=int(o.bits), symbols=int(o.symbols),
                 n_records=int(o.n_records)) for g, o in chosen]


def local_summary_trace(knowledge, view, sender, now):
    """Diagnostic local cache only; rejected entries never become inputs."""
    rows = []
    for peer, item in sorted(knowledge.cache[sender].items()):
        native = knowledge.native[sender].get(peer)
        reasons = []
        if peer == sender:
            reasons.append('self')
        if native is None or peer not in view.team_pos:
            reasons.append('missing_native_peer')
        elif native.pos != tuple(view.team_pos[peer]):
            reasons.append('native_view_mismatch')
        elif item.created <= native.created:
            reasons.append('not_newer_than_native')
        if item.created >= item.received or item.received > now:
            reasons.append('not_causally_received')
        if now > item.valid_until:
            reasons.append('expired')
        rows.append(dict(peer=int(peer), created=int(item.created),
                         received=int(item.received), valid_until=int(item.valid_until),
                         pose=list(item.pos), eligible=not reasons, reasons=reasons))
    return rows


def export_groups(groups):
    return [dict(kind=g.kind, cell=None if g.cell is None else int(g.cell),
                 options=[dict(rate=float(o.rate), bits=int(o.bits),
                               symbols=int(o.symbols), value=float(o.value),
                               value_hex=float(o.value).hex(), n_records=int(o.n_records))
                          for o in g.options]) for g in groups]


def select_rule(groups, budget, price, factor, form):
    """Separate implementations; ideal equivalence is not a bitwise guarantee."""
    if (form not in ('scale', 'price') or not math.isfinite(factor) or factor <= 0
            or not math.isfinite(price) or price < 0):
        raise ValueError('Invalid selector parameters')
    if form == 'price':
        return lagrangian_select(groups, budget, price / factor)
    # Avoid multiplying by 1 for fixed controls; preserve legacy operation order.
    adjusted = groups if factor == 1. else [
        replace(g, options=[replace(o, value=o.value * factor) for o in g.options])
        for g in groups]
    return lagrangian_select(adjusted, budget, price)


def catalog_diagnostic(decision):
    """Post-run same-catalog numerical replay, never an online controller input."""
    if decision['groups_before_age'] is None:
        return None
    groups = [Group(g['kind'], [Option(o['rate'], o['bits'], o['symbols'],
                                     float.fromhex(o['value_hex']), o['n_records'])
                               for o in g['options']], cell=g['cell'])
              for g in decision['groups_before_age']]
    selected = {form: selection_signature(select_rule(groups, decision['budget'],
                        decision['base_price'], decision['factor'], form))
                for form in ('scale', 'price')}
    return dict(t=decision['t'], sender=decision['sender'],
                original_form=decision['form'], selected=selected,
                replay_matches_actual=selected[decision['form']] == decision['selected'],
                scale_price_same=selected['scale'] == selected['price'],
                scope='Same logged pre-age option catalog; not a task rollout or universal equivalence proof')


def _wire_id(wire):
    return hashlib.sha256(wire).hexdigest()


class ObservedCausalService(CausalPaidService):
    """Observe inherited service calls without inserting work into its queues."""
    def __init__(self, *args, observe=False, **kwargs):
        self.observe = observe
        self.observations = []
        self._frames = {}
        self._observed_jobs = defaultdict(deque)
        super().__init__(*args, **kwargs)

    def _enqueue_dl(self, priority, kind, wire):
        super()._enqueue_dl(priority, kind, wire)
        if self.observe:
            row = dict(event='dl_enqueue', t=self.next_t, frame_id=self.seq,
                       frame_kind=kind, priority=priority, bytes=len(wire),
                       wire_sha256=_wire_id(wire),
                       required_uses=math.ceil(len(wire) * 8 / self.c.dl_rate))
            self._frames[self.seq] = row
            self.observations.append(row)

    def _cpu(self, observer, t, seconds, action, data):
        start = max(t * self.c.slot_seconds, self.cpu_free[observer])
        super()._cpu(observer, t, seconds, action, data)
        if self.observe:
            # id(data) is bookkeeping only; never serialized or fed to selection.
            self._observed_jobs[observer, action, id(data)].append(self.seq)
            kind = data[0] if action == 'received' else action
            self.observations.append(dict(event='cpu_admit', t=t, job_id=self.seq,
                observer=observer, action=action, message_kind=kind, seconds=seconds,
                wire_sha256=_wire_id(data[1]) if action == 'received' else None,
                start_seconds=start, end_seconds=self.cpu_free[observer],
                ready=math.ceil(self.cpu_free[observer] / self.c.slot_seconds - 1e-12)))

    def _job(self, action, observer, data, t):
        super()._job(action, observer, data, t)
        if self.observe:
            ids = self._observed_jobs[observer, action, id(data)]
            job_id = ids.popleft()
            if not ids:
                del self._observed_jobs[observer, action, id(data)]
            self.observations.append(dict(event='cpu_complete', t=t, job_id=job_id,
                observer=observer, action=action,
                message_kind=data[0] if action == 'received' else action))

    def _receive(self, kind, receiver, wire, t):
        super()._receive(kind, receiver, wire, t)
        if self.observe:
            self.observations.append(dict(event='decoded', t=t, observer=receiver,
                message_kind=kind, bytes=len(wire), wire_sha256=_wire_id(wire)))

    def tick(self, t, ul_ok=lambda source, kind, wire: True,
             dl_ok=lambda receiver, kind, wire: True):
        before = len(self.events)
        super().tick(t, ul_ok, dl_ok)
        if self.observe:
            for event in self.events[before:]:
                if event['kind'] == 'dl':
                    frame = self._frames[event['frame_id']]
                    self.observations.append(dict(event='dl_service', t=t,
                        frame_id=event['frame_id'], frame_kind=frame['frame_kind'],
                        uses=event['uses']))

    def observation_end(self):
        return dict(event='service_end', t=self.next_t,
                    unserved=[dict(frame_id=f[1], frame_kind=f[2], remaining_uses=f[4])
                              for f in sorted(self.dl)],
                    inflight=[dict(arrival_t=f[0], frame_kind=f[2], bytes=len(f[3]),
                                   wire_sha256=_wire_id(f[3])) for f in sorted(self.arrivals)],
                    pending_cpu=[dict(job_id=f[1], ready=f[0], action=f[2], observer=f[3],
                                      message_kind=f[4][0] if f[2] == 'received' else f[2])
                                 for f in sorted(self.jobs)])


class InformationSimulation(CausalPaidSimulation):
    """Independent name; legacy GP-v2 and its frozen protocol are unchanged."""
    def __init__(self, cfg, seed, service_config, mode='tom', arm='public-fixed',
                 policy=None, dl_loss=.05, observe=False):
        if arm not in RULES:
            raise ValueError('Unknown information arm')
        if mode != 'tom' and arm != 'public-fixed':
            raise ValueError('Only fixed public controls can use other value modes')
        self.information_arm = arm
        self.rule = RULES[arm]
        self.observe = observe
        self.decisions = []
        self.channel_observations = []
        super().__init__(cfg, seed, service_config, mode, self.rule.legacy_arm,
                         policy, dl_loss)

    def make_service(self, starts, grid, config, task_window):
        return ObservedCausalService(starts, grid, config, task_window,
                                     self.causal_policy, observe=self.observe)

    def select(self, agent, known, view):
        self.service.valuation_work(agent.idx, view.t)
        start = time.process_time()
        self.selection_calls += 1
        try:
            public = self.view(agent)  # Received local view, before pose projection.
            factor, stamps = local_age(self.service.knowledge, public, agent.idx,
                                      view.t, self.rule.age_source, self.observe)
            if isinstance(self.scheme, WirePeriodic):
                chosen = self.scheme.select(agent, known, view)
                groups = None  # Periodic does not enumerate a GOSC option catalog.
            else:
                groups = self.scheme.build_groups(agent, known, view)
                chosen = select_rule(groups, self.cfg.symbols_per_slot,
                                     self.scheme.price, factor, self.rule.form)
            if self.observe:
                self.decisions.append(dict(event='decision', t=view.t, sender=agent.idx,
                    arm=self.information_arm, mode=self.scheme.voi_mode,
                    age_source=self.rule.age_source, form=self.rule.form,
                    timestamps=stamps, factor=factor, base_price=self.scheme.price,
                    summary_cache=(local_summary_trace(self.service.knowledge, public,
                                   agent.idx, view.t) if self.use_pose else []),
                    effective_price=self.scheme.price / factor,
                    budget=self.cfg.symbols_per_slot,
                    native_positions={str(k):list(v) for k, v in public.team_pos.items()},
                    valuation_positions={str(k):list(v) for k, v in view.team_pos.items()},
                    candidate_context=dict(intent_target=agent.target,
                        pending_records=[dict(created=int(r.t), pos=list(r.pos),
                                              detections=[int(x) for x in r.det])
                                         for r in agent.pending_records]),
                    # Values below already include pose projection if enabled,
                    # but precede age scaling; no extra shadow valuation is run.
                    groups_before_age=None if groups is None else export_groups(groups),
                    selected=selection_signature(chosen)))
            return chosen
        finally:
            self.selection_process_seconds += time.process_time() - start

    def decode_ul(self, sender, kind, wire, rate, snr):
        good = super().decode_ul(sender, kind, wire, rate, snr)
        if self.observe:
            self.channel_observations.append(dict(event='ul_attempt', t=self.t,
                sender=sender, message_kind=kind, bytes=len(wire), rate=rate,
                uses=math.ceil(len(wire) * 8 / rate), wire_sha256=_wire_id(wire), success=good))
        return good

    def decode_dl(self, receiver, kind, wire):
        good = super().decode_dl(receiver, kind, wire)
        if self.observe:
            self.channel_observations.append(dict(event='dl_arrival', t=self.t,
                observer=receiver, message_kind=kind, bytes=len(wire),
                wire_sha256=_wire_id(wire), success=good))
        return good

    def observation(self):
        if not self.observe:
            return []
        return [*self.decisions, *self.channel_observations,
                *self.service.observations, self.service.observation_end()]

    def result(self):
        out = super().result()
        out.update(scheme='GP-ID-v1_' + self.scheme.voi_mode + '_' + self.information_arm,
                   scope='Prospective mechanism/observation fixtures; no confirmatory information-value claim',
                   compute_scope='Inherited fixed logical CPU reservations. Instrumentation is uncharged in the logical model and included in measured selection/mission process time; paired on/off timings must be reported.')
        return out
