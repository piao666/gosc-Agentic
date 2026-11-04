"""Native local belief-change proxies. No scheduler, receiver query or RNG.

New, unvalidated implementation of the accepted static specification. The only
wire override is evidence_voi; CONF/INTENT and candidate construction stay native.
"""
from dataclasses import dataclass
from numbers import Integral
from types import MappingProxyType
import math

import numpy as np

from gosc.belief import Obs, sigmoid
from .native_task_wire import WireGOSC

VERSION = 'Native-Information-Value-v1'


class NativeInformationError(ValueError):
    pass


def integer(value, lower, upper):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise NativeInformationError('Integer required')
    value = int(value)
    if not lower <= value <= upper:
        raise NativeInformationError('Integer bounds')
    return value


def finite(value):
    if isinstance(value, (bool, np.bool_)):
        raise NativeInformationError('Boolean is not a numeric parameter')
    value = float(value)
    if not math.isfinite(value):
        raise NativeInformationError('Nonfinite value')
    return value


def immutable_array(value, shape, dtype):
    array = np.asarray(value)
    if array.shape != shape or (dtype == np.bool_ and array.dtype != np.bool_):
        raise NativeInformationError('Array shape/type')
    if dtype == np.float64 and array.dtype.kind not in 'fi':
        raise NativeInformationError('Belief numeric dtype')
    array = np.asarray(array, dtype=dtype, order='C')
    if not np.isfinite(array).all():
        raise NativeInformationError('Nonfinite array')
    # Immutable backing bytes, not merely setflags(False) on a mutable owner.
    return np.frombuffer(array.tobytes(order='C'), dtype=dtype).reshape(shape)


@dataclass(frozen=True, eq=False)
class NativeValueContext:
    sender: int
    t: int
    grid: int
    n_agents: int
    radius: int
    llr_pos: float
    llr_neg: float
    Lc: np.ndarray
    declared: np.ndarray
    team_pos: object
    team_intent: object

    def __post_init__(self):
        n = integer(self.grid, 1, 32)
        count = integer(self.n_agents, 1, 31)
        for name, value in [('grid', n), ('n_agents', count),
                            ('sender', integer(self.sender, 0, count - 1)),
                            ('t', integer(self.t, 0, 511)),
                            ('radius', integer(self.radius, 0, 32))]:
            object.__setattr__(self, name, value)
        object.__setattr__(self, 'llr_pos', finite(self.llr_pos))
        object.__setattr__(self, 'llr_neg', finite(self.llr_neg))
        object.__setattr__(self, 'Lc', immutable_array(self.Lc, (n, n), np.float64))
        object.__setattr__(self, 'declared', immutable_array(self.declared, (n*n,), np.bool_))
        positions, intents = {}, {}
        for key, pos in dict(self.team_pos).items():
            peer = integer(key, 0, count - 1)
            if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                raise NativeInformationError('Pose shape')
            positions[peer] = tuple(integer(v, 0, n - 1) for v in pos)
        for key, cell in dict(self.team_intent).items():
            peer = integer(key, 0, count - 1)
            intents[peer] = None if cell is None else integer(cell, 0, n*n - 1)
        object.__setattr__(self, 'team_pos', MappingProxyType(positions))
        object.__setattr__(self, 'team_intent', MappingProxyType(intents))

    @classmethod
    def from_local(cls, view, sender):
        c = view.cfg
        if (c.tom_oracle or c.task != 'search' or c.shared_budget or c.llm_agents
                or c.value_mode != 'exact' or c.overhead_bits):
            raise NativeInformationError('Native support domain')
        return cls(sender, view.t, c.grid, c.n_agents, c.sense_radius,
                   view.sensor.llr_pos, view.sensor.llr_neg, view.Lc,
                   view.declared, view.team_pos, view.team_intent)

    def to_json(self):
        return dict(sender=self.sender, t=self.t, grid=self.grid,
                    n_agents=self.n_agents, radius=self.radius,
                    llr_pos=self.llr_pos, llr_neg=self.llr_neg,
                    Lc=self.Lc.tolist(), declared=self.declared.tolist(),
                    team_pos={str(k): list(v) for k, v in self.team_pos.items()},
                    team_intent={str(k): v for k, v in self.team_intent.items()})

    @classmethod
    def from_json(cls, data):
        if set(data) != set(cls.__dataclass_fields__):
            raise NativeInformationError('Context fields: no global/hidden metadata')
        row = dict(data)
        if any(not isinstance(k, str) or str(int(k)) != k
               for mapping in (data['team_pos'], data['team_intent']) for k in mapping):
            raise NativeInformationError('Noncanonical peer identity')
        row['team_pos'] = {int(k): v for k, v in data['team_pos'].items()}
        row['team_intent'] = {int(k): v for k, v in data['team_intent'].items()}
        return cls(**row)


def checked_records(context, records):
    result, keys, previous = [], set(), -1
    for rec in records:
        stamp = integer(rec.t, 0, context.t)
        sender = integer(rec.agent, 0, context.n_agents - 1)
        if sender != context.sender or (sender, stamp) in keys or stamp <= previous:
            raise NativeInformationError('Evidence sender/duplicate identity')
        if len(rec.pos) != 2:
            raise NativeInformationError('Evidence pose')
        pos = tuple(integer(v, 0, context.grid - 1) for v in rec.pos)
        det = tuple(integer(v, 0, context.grid**2 - 1) for v in rec.det)
        if len(set(det)) != len(det):
            raise NativeInformationError('Duplicate detection cell')
        if any(max(abs(x-pos[0]), abs(y-pos[1])) > context.radius
               for x, y in (divmod(c, context.grid) for c in det)):
            raise NativeInformationError('Detection outside sensing footprint')
        keys.add((sender, stamp))
        previous = stamp
        result.append(Obs(stamp, sender, pos, det))
    return tuple(result)


def record_json(rec):
    return dict(t=int(rec.t), agent=int(rec.agent), pos=list(rec.pos), det=list(rec.det))


def record_from_json(row):
    if set(row) != {'t', 'agent', 'pos', 'det'}:
        raise NativeInformationError('Evidence fields')
    return Obs(row['t'], row['agent'], tuple(row['pos']), tuple(row['det']))


def weights(context, shuffled=False):
    n, r = context.grid, context.radius
    live = ~context.declared.reshape(n, n)
    if not live.any():
        return np.zeros((n, n)), []
    x, y = np.indices((n, n))
    total = np.zeros((n, n), dtype=np.float64)
    anchors = []
    for peer in range(context.n_agents):
        if peer == context.sender:
            continue
        intent = context.team_intent.get(peer)
        if intent is not None:
            anchor, source = divmod(intent, n), 'native_intent'
        elif peer in context.team_pos:
            anchor, source = context.team_pos[peer], 'native_pose'
        else:
            anchor, source = None, 'uniform_missing'
        if anchor is None:
            total += 1.
        else:
            distance = np.maximum(abs(x-anchor[0])-r, 0) + np.maximum(abs(y-anchor[1])-r, 0)
            total += 1. / (1. + distance / max(1, r))
        anchors.append(dict(peer=peer, source=source,
                            anchor=None if anchor is None else list(anchor)))
    q = total / len(anchors) if anchors else np.ones((n, n))
    u = .5 + .5 * q
    w = np.zeros((n, n), dtype=np.float64)
    w[live] = u[live] / float(u[live].mean())
    if shuffled:
        w[live] = np.roll(w[live], int(live.sum()) // 2)
    if not np.isfinite(w).all() or np.any(w[live] < .5) or np.any(w[live] > 2.):
        raise NativeInformationError('Weight arithmetic/bounds')
    return w, anchors


def evidence_values(context, records, prefixes, method='g0'):
    if method not in ('g0', 'g1', 'shuffled'):
        raise NativeInformationError('Unknown proxy')
    records = checked_records(context, records)
    ns = sorted({integer(k, 1, len(records)) for k in prefixes})
    if not ns:
        return {}
    live = ~context.declared.reshape(context.grid, context.grid)
    if not live.any():
        return {n: 0. for n in ns}
    w = None if method == 'g0' else weights(context, method == 'shuffled')[0]
    base = sigmoid(context.Lc)
    delta = np.zeros_like(context.Lc)
    answer, index = {}, 0
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        try:
            for length in ns:
                while index < length:
                    rec = records[index]
                    x, y = rec.pos
                    r, n = context.radius, context.grid
                    delta[max(0, x-r):min(n, x+r+1), max(0, y-r):min(n, y+r+1)] += context.llr_neg
                    if rec.det:
                        delta.reshape(-1)[list(rec.det)] += context.llr_pos-context.llr_neg
                    index += 1
                posterior = context.Lc + delta
                if not np.isfinite(posterior).all():
                    raise NativeInformationError('Nonfinite posterior')
                change = np.abs(sigmoid(posterior)-base)
                value = float((change if w is None else change*w)[live].sum(dtype=np.float64))
                if not math.isfinite(value) or value < 0:
                    raise NativeInformationError('Nonfinite/negative proxy')
                answer[length] = value
        except FloatingPointError as exc:
            raise NativeInformationError('Evidence arithmetic') from exc
    return answer


class NativeValueWireGOSC(WireGOSC):
    """Explicit evaluation-only wire hook, never installed by the host observer."""
    def __init__(self, cfg, channel, method, scale=1.):
        super().__init__(cfg, channel, 'tom')
        if method not in ('g0', 'g1', 'shuffled') or finite(scale) <= 0:
            raise NativeInformationError('Proxy/scale')
        self.method, self.scale = method, float(scale)
        self.name = 'Native-Information-'+method+'-v1'
        self.value_version = VERSION

    def evidence_voi(self, sim, records, prefixes, team=None):
        ctx = NativeValueContext.from_local(sim, records[0].agent)
        values = evidence_values(ctx, records, prefixes, self.method)
        result = {n: finite(v*self.scale) for n, v in values.items()}
        return result
