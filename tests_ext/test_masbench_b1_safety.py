"""New B1-pre contracts: no HTTP, no model, only synthetic IDs and owned workers."""
from dataclasses import replace
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest

from extensions.masbench_reasoning.execution_safety import Ledger, Limits, SafetyError, supervise_owned_worker


class SafetyContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.limits = replace(Limits(), artifact_bytes=32768)

    def tearDown(self):
        self.tmp.cleanup()

    def ledger(self, **kw):
        return Ledger(self.root, {'model': 'synthetic', 'registry': 'fixture'}, ['a', 'b'],
                      replace(self.limits, **kw))

    def test_crash_preserves_denominator_reservation_and_fences(self):
        with self.ledger() as l:
            l.episode('a', 'started')
            l.reserve_request('r', 'a', 4, 10)
        with self.ledger() as l:
            self.assertTrue(l.state['fenced'])
            self.assertEqual(l.state['outputs'], 10)
            self.assertEqual(l.denominator(), {'a': 'interrupted_pending', 'b': 'unstarted'})
            with self.assertRaises(SafetyError):
                l.reserve_request('s', 'a', 4, 10)
            l.episode('a', 'interrupted')

    def test_failed_request_never_refunds_or_replays(self):
        with self.ledger(requests=1) as l:
            l.episode('a', 'started')
            l.reserve_request('r', 'a', 4, 10)
            l.finish_request('r', 'failed')
            self.assertIsNone(l.state['requests']['r']['observed_usage'])
            self.assertEqual(l.state['outputs'], 10)
            with self.assertRaises(SafetyError):
                l.reserve_request('r2', 'a', 1, 1)
            with self.assertRaises(SafetyError):
                l.episode('a', 'completed')
            l.episode('a', 'failed')
        with self.ledger(requests=1) as l:
            with self.assertRaises(SafetyError):
                l.episode('a', 'started')
            self.assertEqual(l.denominator()['a'], 'failed')

    def test_identity_and_limits_and_plan_binding(self):
        with self.ledger():
            pass
        for identity, plan, limits in [({'model':'other'}, ['a','b'], self.limits),
                                        ({'model':'synthetic','registry':'fixture'}, ['b','a'], self.limits),
                                        ({'model':'synthetic','registry':'fixture'}, ['a','b'], replace(self.limits,requests=99))]:
            with self.assertRaises(SafetyError):
                Ledger(self.root, identity, plan, limits)

    def test_exclusive_process_lock(self):
        with self.ledger():
            with self.assertRaises(BlockingIOError):
                self.ledger()

    def test_corruption_and_partial_line_fail_closed(self):
        with self.ledger():
            pass
        p = self.root/'ledger.jsonl'
        raw = p.read_bytes()
        for data in [raw[:-1], raw.replace(b'init', b'xxxx'), b'']:
            p.write_bytes(data)
            with self.assertRaises((SafetyError, ValueError)):
                self.ledger()

    def test_wall_budget_includes_resume_downtime(self):
        with self.ledger(wall_seconds=.08):
            pass
        time.sleep(.1)
        with self.ledger(wall_seconds=.08) as l:
            with self.assertRaises(SafetyError):
                l.episode('a', 'started')

    def test_input_output_caps_and_single_generation(self):
        with self.ledger(input_tokens=6, output_tokens=10) as l:
            l.episode('a', 'started')
            l.reserve_request('r', 'a', 4, 8)
            with self.assertRaises(SafetyError):
                l.reserve_request('r2', 'a', 1, 1)
            with self.assertRaises(SafetyError):
                l.finish_request('r', 'completed', {'prompt_tokens':3,'completion_tokens':2})
            l.finish_request('r', 'completed', {'prompt_tokens':4,'completion_tokens':2})
            with self.assertRaises(SafetyError):
                l.reserve_request('r2', 'a', 3, 1)
            with self.assertRaises(SafetyError):
                l.reserve_request('r2', 'a', 1, 3)
            l.reserve_request('r2', 'a', 2, 2)

    def test_metadata_separate_persistent_cap(self):
        with self.ledger(metadata=1) as l:
            l.metadata()
        with self.ledger(metadata=1) as l:
            with self.assertRaises(SafetyError):
                l.metadata()

    def test_jsonl_and_wire_and_journal_share_cap(self):
        with self.ledger(artifact_bytes=4096) as l:
            l.put_artifact('requests.jsonl', b'a'*1000)
            l.put_artifact('wire.bin', b'b'*1000)
            with self.assertRaises(SafetyError):
                l.put_artifact('other.bin', b'c'*2000)
            total = sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
            self.assertLessEqual(total, 4096)
            self.assertEqual(l.state['bytes'],2000)
        with self.ledger(artifact_bytes=4096) as l:
            self.assertEqual(l.state['bytes'],2000)

    def test_artifact_path_and_no_overwrite(self):
        with self.ledger() as l:
            for path in ['../../escape', '/tmp/escape']:
                with self.assertRaises(SafetyError):
                    l.put_artifact(path, b'a')
            l.put_artifact('one',b'a')
            with self.assertRaises(SafetyError):
                l.put_artifact('one',b'b')

    def test_timeout_fences_even_with_no_usage(self):
        with self.ledger() as l:
            l.episode('a','started')
            l.reserve_request('r','a',0,1)
            l.finish_request('r','timeout')
            self.assertTrue(l.state['fenced'])
            with self.assertRaises(SafetyError):
                l.episode('b','started')

    def test_unplanned_ids_invalid_limits_and_tokens(self):
        with self.assertRaises(SafetyError):
            self.ledger(wall_seconds=float('nan'))
        with self.ledger() as l:
            with self.assertRaises(SafetyError):
                l.episode('gold_unplanned','started')
            l.episode('a','started')
            for inp,out in [(-1,1),(True,1),(1,513),(1,0)]:
                with self.assertRaises(SafetyError):
                    l.reserve_request('r','a',inp,out)

    def test_worker_timeout_kills_term_ignoring_group(self):
        with self.ledger(operation_seconds=.2) as l:
            result=supervise_owned_worker(l,[sys.executable,'-c',
                'import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print("fake",flush=True); time.sleep(20)'])
            self.assertEqual(result['reason'],'timeout')
            self.assertEqual(result['returncode'],-signal.SIGKILL)
            self.assertLess(result['elapsed_seconds'],2)
            self.assertFalse(result['server_cancel_verified'])
            with self.assertRaises(ProcessLookupError):
                os.killpg(result['owned_process_group'],0)

    def test_global_wall_precedes_request_deadline(self):
        with self.ledger(wall_seconds=.2,operation_seconds=5) as l:
            result=supervise_owned_worker(l,[sys.executable,'-c','import time; time.sleep(20)'])
            self.assertEqual(result['reason'],'timeout')
            self.assertLess(result['elapsed_seconds'],2)
            with self.assertRaises(SafetyError):
                l.episode('a','started')

    def test_successful_worker_has_bounded_recorded_output(self):
        with self.ledger() as l:
            result=supervise_owned_worker(l,[sys.executable,'-c','print("fixture")'])
            self.assertEqual(result['returncode'],0)
            self.assertEqual((self.root/'artifacts/worker.log').read_bytes(),b'fixture\n')
            self.assertIsNone(result['gpu_peak_bytes'])

    def test_streaming_output_limit_stops_worker(self):
        with self.ledger(artifact_bytes=8192) as l:
            result=supervise_owned_worker(l,[sys.executable,'-c',
                'import os,time\nwhile True: os.write(1,b"x"*1024); time.sleep(.001)'])
            self.assertEqual(result['reason'],'artifact_limit')
            self.assertLessEqual(sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file()),8192)

    def test_child_exits_but_inherited_pipe_descendant_is_killed(self):
        with self.ledger(operation_seconds=.2) as l:
            result=supervise_owned_worker(l,[sys.executable,'-c',
                'import os,time,signal\np=os.fork()\nif p==0:\n signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(20)\nelse: print(p,flush=True)'])
            self.assertEqual(result['reason'],'timeout')
            pid=int((self.root/'artifacts/worker.log').read_text().strip())
            # A reparented killed descendant can briefly remain a zombie.
            path=Path(f'/proc/{pid}/stat')
            until=time.monotonic()+.5
            while path.exists() and path.read_text().split(') ')[1].split()[0]!='Z' and time.monotonic()<until:
                time.sleep(.01)
            if path.exists():
                self.assertEqual(path.read_text().split(') ')[1].split()[0],'Z')


if __name__ == '__main__':
    unittest.main()
