"""Independent, no-network protection prototype. NOT a live Reasoning driver.

Linux process-group cancellation protects owned workers, not an external model
server. A timed-out/in-flight request permanently fences this run from dispatch.
Only writes through put_artifact are covered by the shared artifact reservation.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time


class SafetyError(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


@dataclass(frozen=True)
class Limits:
    requests: int = 98
    metadata: int = 106
    output_tokens: int = 50176
    input_tokens: int = 3161088  # proposal upper bound, not measured workload
    per_output: int = 512
    wall_seconds: float = 6000
    operation_seconds: float = 60
    artifact_bytes: int = 256 * 1024 * 1024

    def validate(self):
        for k, v in asdict(self).items():
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
                raise SafetyError('invalid limit: ' + k)
            if k not in ('wall_seconds', 'operation_seconds') and not isinstance(v, int):
                raise SafetyError('integer limit required')


class Ledger:
    """Exclusive fsync journal, monotonic reservations, immutable plan and identity.

    Reopening in the same boot resumes the original wall deadline. A partial or
    corrupt journal fails closed. No recovery edits, refunds or replay of IDs.
    This is crash detection, not tamper resistance against the account owner.
    """
    def __init__(self, root, identity, episode_ids, limits=Limits()):
        import fcntl
        limits.validate()
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        if len(set(episode_ids)) != len(episode_ids):
            raise SafetyError('duplicate planned episode')
        self.limits = limits
        self.lock = (self.root / 'ledger.lock').open('a+b')
        self.file = None
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            self.binding = digest({'identity': identity, 'plan': list(episode_ids), 'limits': asdict(limits)})
            self.state = {'episodes': {e: 'unstarted' for e in episode_ids}, 'requests': {},
                          'metadata': 0, 'inputs': 0, 'outputs': 0, 'bytes': 0, 'fenced': False}
            self.seq, self.previous = 0, '0' * 64
            p = self.root / 'ledger.jsonl'
            if p.exists():
                with p.open('rb') as stream:
                    for line in stream:
                        if len(line) > 1024*1024 or not line.endswith(b'\n'):
                            raise SafetyError('incomplete/oversize journal')
                        row = json.loads(line)
                        h = row.pop('hash')
                        if row['seq'] != self.seq or row['previous'] != self.previous or digest(row) != h:
                            raise SafetyError('journal chain mismatch')
                        self._apply(row['event'])
                        self.previous, self.seq = h, self.seq + 1
                if not self.seq:
                    raise SafetyError('empty existing journal')
                if any(v['status'] == 'inflight' for v in self.state['requests'].values()):
                    self.state['fenced'] = True
            self.file = p.open('ab', buffering=0)
            if not self.seq:
                self._append({'kind': 'init', 'binding': self.binding, 'boot': self.boot,
                              'started_mono': time.monotonic(), 'started_utc': time.time()})
        except BaseException:
            self.close()
            raise

    def _apply(self, event):
        s, k = self.state, event['kind']
        if k == 'init':
            if self.seq != 0 or event['binding'] != self.binding or event['boot'] != self.boot:
                raise SafetyError('identity/plan/limits/boot mismatch')
            s['started_mono'], s['started_utc'] = event['started_mono'], event['started_utc']
        elif k == 'episode':
            s['episodes'][event['id']] = event['status']
        elif k == 'request':
            s['requests'][event['id']] = event
            s['inputs'] += event['input']
            s['outputs'] += event['output']
        elif k == 'finish':
            s['requests'][event['id']]['status'] = event['status']
            s['requests'][event['id']]['observed_usage'] = event['usage']
            if event['uncertain']:
                s['fenced'] = True
        elif k == 'metadata':
            s['metadata'] += 1
        elif k == 'bytes':
            s['bytes'] += event['count']
        else:
            raise SafetyError('unknown event')

    def _append(self, event):
        row = {'seq': self.seq, 'previous': self.previous, 'event': event}
        h = digest(row)
        data = canonical({**row, 'hash': h}) + b'\n'
        reservation = event['count'] if event['kind'] == 'bytes' else 0
        if self.state['bytes'] + reservation + self.file.tell() + len(data) > self.limits.artifact_bytes:
            raise SafetyError('shared byte budget exhausted')
        if len(data) > 1024*1024:
            raise SafetyError('oversize audit event')
        if self.file.write(data) != len(data):
            raise SafetyError('short journal write')
        os.fsync(self.file.fileno())
        self._apply(event)
        self.previous, self.seq = h, self.seq + 1

    def remaining(self):
        return self.limits.wall_seconds - (time.monotonic() - self.state['started_mono'])

    def _admit(self):
        if self.state['fenced'] or self.remaining() <= 0:
            raise SafetyError('run fenced or wall budget expired')

    def episode(self, episode_id, status):
        if episode_id not in self.state['episodes']:
            raise SafetyError('unplanned episode')
        old = self.state['episodes'][episode_id]
        if status == 'started':
            self._admit()
            if old != 'unstarted':
                raise SafetyError('episode cannot restart')
        elif status not in ('completed', 'failed', 'interrupted') or old != 'started':
            raise SafetyError('invalid episode transition')
        if status == 'completed' and (self.state['fenced'] or any(
                r['episode'] == episode_id and r['status'] != 'completed' for r in self.state['requests'].values())):
            raise SafetyError('failed/inflight request cannot become success')
        self._append({'kind': 'episode', 'id': episode_id, 'status': status})

    def reserve_request(self, request_id, episode_id, exact_input, max_output):
        self._admit()
        s, l = self.state, self.limits
        if (type(exact_input) is not int or exact_input < 0 or type(max_output) is not int
                or max_output <= 0 or max_output > l.per_output):
            raise SafetyError('invalid token reservation')
        if s['episodes'].get(episode_id) != 'started' or request_id in s['requests']:
            raise SafetyError('episode not active or duplicate request')
        if any(r['status'] == 'inflight' for r in s['requests'].values()):
            raise SafetyError('concurrent generation forbidden')
        if len(s['requests']) >= l.requests or s['inputs'] + exact_input > l.input_tokens or s['outputs'] + max_output > l.output_tokens:
            raise SafetyError('request/token budget exhausted')
        self._append({'kind': 'request', 'id': request_id, 'episode': episode_id,
                      'input': exact_input, 'output': max_output, 'status': 'inflight'})

    def finish_request(self, request_id, status, usage=None, uncertain=False):
        if status not in ('completed', 'failed', 'timeout', 'interrupted'):
            raise SafetyError('invalid request status')
        r = self.state['requests'].get(request_id)
        if r is None or r['status'] != 'inflight':
            raise SafetyError('request not inflight')
        # Reservations never refund; missing usage is explicit, not zero tokens.
        if usage is not None and (set(usage) != {'prompt_tokens', 'completion_tokens'} or
                any(type(v) is not int or v < 0 for v in usage.values()) or
                usage['prompt_tokens'] != r['input'] or usage['completion_tokens'] > r['output']):
            raise SafetyError('usage mismatch')
        if status in ('timeout', 'interrupted'):
            uncertain = True
        self._append({'kind': 'finish', 'id': request_id, 'status': status,
                      'usage': usage, 'uncertain': bool(uncertain)})

    def metadata(self):
        self._admit()
        if self.state['metadata'] >= self.limits.metadata:
            raise SafetyError('metadata cap')
        self._append({'kind': 'metadata'})

    def put_artifact(self, relative, data):
        if not isinstance(data, bytes):
            raise SafetyError('artifact must be bytes')
        p = self.root / 'artifacts' / relative
        base = (self.root / 'artifacts').resolve()
        if base not in p.resolve().parents or p.exists():
            raise SafetyError('unsafe/existing artifact')
        # Charge before open/write; a failed/partial write does not refund space.
        self._append({'kind': 'bytes', 'path': relative, 'count': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

    def denominator(self):
        return {e: ('interrupted_pending' if v == 'started' else v)
                for e, v in self.state['episodes'].items()}

    def close(self):
        if self.file:
            self.file.close()
        if getattr(self, 'lock', None):
            self.lock.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def supervise_owned_worker(ledger, argv, relative='worker.log'):
    """Hard deadline for owned fake worker group; never targets Ollama PID.

    argv is trusted caller code, not a sandbox. External server cancellation and
    arbitrary worker writes are expressly outside this contract. Logs go through
    the shared cap after bounded collection. No shell, network or retries here.
    """
    ledger._admit()
    deadline = time.monotonic() + min(ledger.remaining(), ledger.limits.operation_seconds)
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, start_new_session=True)
    sel = selectors.DefaultSelector()
    sel.register(proc.stdout, selectors.EVENT_READ)
    chunks, size, reason = [], 0, 'completed'
    start = time.monotonic()
    max_rss_kib = 0
    try:
        while sel.get_map():
            if time.monotonic() >= deadline:
                reason = 'timeout'
                break
            try:
                rss = Path(f'/proc/{proc.pid}/status').read_text().split('VmRSS:')[1].split()[0]
                max_rss_kib = max(max_rss_kib, int(rss))
            except (OSError, IndexError, ValueError):
                pass
            for key, _ in sel.select(min(.02, max(0, deadline - time.monotonic()))):
                data = os.read(key.fileobj.fileno(), 4096)
                if not data:
                    sel.unregister(key.fileobj)
                    continue
                size += len(data)
                if size > min(1024*1024, ledger.limits.artifact_bytes - ledger.state['bytes'] - ledger.file.tell() - 2048):
                    reason = 'artifact_limit'
                    break
                chunks.append(data)
            if reason != 'completed':
                break
        if reason == 'completed':
            try:
                proc.wait(timeout=max(.001, deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                reason = 'timeout'
    finally:
        # Kill owned group even when direct child exited, to catch descendants.
        for sig, grace in ((signal.SIGTERM, .05), (signal.SIGKILL, 0)):
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                pass
            if grace:
                time.sleep(grace)
        proc.wait(timeout=2)
        sel.close()
        proc.stdout.close()
    ledger.put_artifact(relative, b''.join(chunks))
    return {'reason': reason, 'returncode': proc.returncode,
            'elapsed_seconds': time.monotonic()-start, 'sampled_rss_kib': max_rss_kib,
            'server_cancel_verified': False, 'gpu_peak_bytes': None,
            'owned_process_group': proc.pid}
