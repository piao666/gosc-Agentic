"""T1-A: fabricated model/counter/service only; no HTTP or model weights."""
from dataclasses import replace
from io import BytesIO, StringIO
import json,os,signal,socket,sys,time,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from extensions.masbench_reasoning import live_driver as live
from extensions.masbench_reasoning.client import ClientFailure
from extensions.masbench_reasoning.execution_safety import Limits,SafetyError
from extensions.masbench_reasoning.application import LocalAgent,PrivateView

ZERO='0'*64
MESSAGES=[{'role':'system','content':'entire fictional private evidence'}, {'role':'user','content':'synthetic only'}]
RUNNER={'pid':10000001,'stamp':'555'}

class FakeIO:
    is_live=False
    def __init__(self):
        self.mode='ok';self.n=8;self.requests=[];self.resident=False;self.last_render=None
        self.debug_drift=False;self.context_drift=False;self.driver=None
        self.runner_stamp=None
    def call(self,spec,timeout,crash=False):
        self.requests.append(spec)
        if spec['kind']=='counter':
            self.last_render=json.dumps(spec['input']['requests'][0]['messages'],sort_keys=True)
            return {'requests':[{'rendered':self.last_render,'token_count':self.n,'token_ids':list(range(self.n))}]}
        path=spec['path'];body=spec['body']
        if path=='/api/chat' and body.get('_debug_render_only'):
            self.resident=True
            if self.mode!='missing-runner':
                self.runner_stamp=RUNNER['stamp']
            return {'_debug_info':{'rendered_template':self.last_render+('changed' if self.debug_drift else '')}}
        if path=='/api/chat':
            if self.mode=='unload-fail':raise TimeoutError()
            self.resident=False
            if self.mode!='timeout-runner-persists':
                self.runner_stamp='777' if self.mode=='timeout-pid-reused' else None
            return {'done':True,'done_reason':'unload'}
        if path=='/api/ps':return {'models':[{'name':'t1-fixture','digest':ZERO,'context_length':65 if self.context_drift else 64}] if self.resident else []}
        if path=='/api/version':return {'version':'0.11.11'}
        if path=='/v1/chat/completions':
            # Check the actual reservation and durable input exist before dispatch.
            if self.driver:
                assert any(r['status']=='inflight' for r in self.driver.ledger.state['requests'].values())
                rows=[json.loads(x) for x in (self.driver.ledger.root/'ledger.jsonl').read_bytes().splitlines()]
                assert any(x['event']['kind']=='request' for x in rows)
                rows=(self.driver.root/'control.jsonl').read_bytes().rstrip(b'\0').splitlines()
                assert any(json.loads(row)['event']['kind']=='runner-dispatch-bound' for row in rows)
            if self.mode.startswith('timeout'):
                if self.mode in ('timeout-eager','timeout-pid-reused'):
                    self.resident=False
                    self.runner_stamp=None
                raise TimeoutError()
            if self.mode=='rpc-timeout':
                rpc=live.RPC(self.driver.control,time.monotonic()+4,self.driver.trace)
                return rpc.call({'kind':'fixture','mode':'hang-sent'},.5)
            if self.mode=='http-error':raise ClientFailure('HTTP 503')
            value={'model':'t1-fixture','choices':[{'finish_reason':'length' if self.mode=='length' else 'stop',
                    'message':{'content':'' if self.mode=='empty' else 'Alice: MESSAGE <R>fictional peer</R>'}}],
                   'usage':{'prompt_tokens':self.n+(1 if self.mode=='usage-mismatch' else 0),'completion_tokens':1,'total_tokens':self.n+1}}
            if self.mode=='missing-usage':value.pop('usage')
            return value
        raise AssertionError('unexpected path')

class Contracts(unittest.TestCase):
    def setUp(self):
        self.base=Path(os.environ['T1_FIXTURE_ROOT'])/self.id().split('.')[-1];self.base.mkdir(parents=True,exist_ok=False)
        self.runtime=live.Runtime(str(self.base/'project'),'/never-executed-helper',123,'fixture-start',ZERO,64,'t1-fixture')
        self.limits=replace(Limits(),requests=4,per_output=8,output_tokens=32,input_tokens=500,
            wall_seconds=120,operation_seconds=4,artifact_bytes=512*1024)
        self.io=FakeIO();self.d=None
        self.scan_runners = live.runner_identities
        self.runners = patch.object(live,'runner_identities',
            side_effect=lambda runtime:[dict(RUNNER)] if self.io.runner_stamp==RUNNER['stamp'] else [])
        self.scan = self.runners.start()
        real_stamp = live.proc_stamp
        self.stamps = patch.object(live,'proc_stamp',
            side_effect=lambda pid:self.io.runner_stamp if pid==RUNNER['pid'] else real_stamp(pid))
        self.stamps.start()
    def tearDown(self):
        if self.d:self.d.close()
        self.stamps.stop()
        self.runners.stop()
    def open(self):
        self.d=live.LiveDriver(self.base/'driver',self.runtime,self.limits,transport=self.io,validator=lambda r:self.base/'models')
        self.io.driver=self.d;return self.d
    def test_kernel_disallows_network(self):
        with self.assertRaises(PermissionError):socket.socket()
    def test_actual_transport_requires_separate_authorization(self):
        with self.assertRaises(SafetyError):live.LiveDriver(self.base/'blocked',self.runtime,self.limits)
    def test_fixture_cannot_create_qwen_binding(self):
        runtime=replace(self.runtime,model='qwen2.5:7b')
        with self.assertRaisesRegex(SafetyError,'separate model identity'):
            live.LiveDriver(self.base/'blocked',runtime,self.limits,transport=self.io)
        d=self.open()
        d.operation_deadline=time.monotonic()+2
        binding=d.attest(MESSAGES,8)
        self.assertEqual(binding.model_manifest_sha256,ZERO)
        self.assertEqual(binding.tokenizer_id,'t1-fixture-counter')
    def test_service_lease_single_writer(self):
        self.open()
        with self.assertRaises(SafetyError):live.LiveDriver(self.base/'other',self.runtime,self.limits,transport=FakeIO(),validator=lambda r:self.base)
    def test_normal_fsync_full_input_and_real_client(self):
        d=self.open();d.generate(MESSAGES,max_output=8)
        self.assertEqual(len(d.ledger.state['requests']),1)
        self.assertEqual(d.ledger.state['outputs'],8)
        self.assertEqual(d.audit[0]['messages'],MESSAGES)
        self.assertFalse(d.audit[0]['backend_is_live'])
    def test_window_c_minus_1(self):
        d=self.open();self.io.n=55;d.generate(MESSAGES,max_output=8)
    def test_window_c(self):
        d=self.open();self.io.n=56;d.generate(MESSAGES,max_output=8)
    def test_window_c_plus_1_no_dispatch(self):
        d=self.open();self.io.n=57
        with self.assertRaises(ClientFailure):d.generate(MESSAGES,max_output=8)
        self.assertFalse(any(x.get('path')=='/v1/chat/completions' for x in self.io.requests))
    def test_schema_rejects_before_any_counter_or_http(self):
        d=self.open()
        with self.assertRaises(ClientFailure):d.generate([{'role':'user','content':'no explicit system'}])
        self.assertEqual(self.io.requests,[])
    def test_render_drift_blocks(self):
        d=self.open();self.io.debug_drift=True
        with self.assertRaises(SafetyError):d.generate(MESSAGES,max_output=8)
        self.assertEqual(len(d.ledger.state['requests']),0)
    def test_runtime_context_drift_blocks(self):
        d=self.open();self.io.context_drift=True
        with self.assertRaises(SafetyError):d.generate(MESSAGES,max_output=8)
        self.assertEqual(len(d.ledger.state['requests']),0)
    def test_identity_validation_prevents_unload(self):
        d=self.open()
        def bad(r):raise SafetyError('PID changed')
        d.validate=bad
        with self.assertRaises(SafetyError):d.recover()
        self.assertEqual(self.io.requests,[])
    def test_timeout_retained_then_permit_and_budget(self):
        d=self.open();self.io.mode='timeout'
        with self.assertRaises(ClientFailure):d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['requests']['synthetic/0']['status'],'timeout')
        self.assertIsNone(d.ledger.state['requests']['synthetic/0']['observed_usage'])
        self.assertTrue(d.ledger.state['fenced'])
        self.io.mode='ok';d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['outputs'],16)
        self.assertEqual(len(d.ledger.state['requests']),2)
    def test_unload_failure_keeps_fence(self):
        d=self.open();self.io.mode='timeout'
        original=self.io.call
        def call(spec,timeout,crash=False):
            if spec.get('path')=='/api/chat' and spec.get('body',{}).get('keep_alive')==0:raise TimeoutError()
            return original(spec,timeout,crash)
        self.io.call=call
        with self.assertRaises(TimeoutError):d.generate(MESSAGES,max_output=8)
        with self.assertRaises(SafetyError):d.ledger._admit()
    def test_plain_boolean_receipt_rejected(self):
        d=self.open()
        with self.assertRaises(SafetyError):d.ledger.barrier({'ps_empty':True,'old_runner_exited':True})
    def test_resume_keeps_deadline_and_cost_and_requires_new_barrier(self):
        d=self.open();d.generate(MESSAGES,max_output=8);started=d.ledger.state['started_mono'];d.close();self.d=None
        d=self.open()
        self.assertEqual(d.ledger.state['started_mono'],started)
        self.assertEqual(d.ledger.state['outputs'],8)
        self.assertTrue(d.ledger.recovery_required)
        with self.assertRaises(SafetyError):d.ledger._admit()
        d.recover();d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['outputs'],16)
    def test_duplicate_id_rejected(self):
        d=self.open();d.generate(MESSAGES,max_output=8)
        with self.assertRaises(SafetyError):d.ledger.reserve_partition('synthetic/0','synthetic',8,8,'synthetic')
    def test_generation_cap_not_refunded(self):
        d=self.open()
        for _ in range(4):d.generate(MESSAGES,max_output=8)
        with self.assertRaises(SafetyError):d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['outputs'],32)
    def test_missing_usage_is_failed_unknown(self):
        d=self.open();self.io.mode='missing-usage'
        with self.assertRaises(ClientFailure):d.generate(MESSAGES,max_output=8)
        self.assertIsNone(d.ledger.state['requests']['synthetic/0']['observed_usage'])
        self.assertEqual(d.ledger.state['outputs'],8)
    def test_invalid_usage_fenced_and_retained(self):
        d=self.open();self.io.mode='usage-mismatch'
        with self.assertRaises(ClientFailure):d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['requests']['synthetic/0']['status'],'failed')
    def test_length_is_failure_not_success(self):
        d=self.open();self.io.mode='length'
        with self.assertRaises(ClientFailure):d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['requests']['synthetic/0']['status'],'failed')
    def test_empty_answer_retains_original_client_semantics(self):
        d=self.open();self.io.mode='empty';self.assertEqual(d.generate(MESSAGES,max_output=8),'')
        self.assertTrue(d.audit[-1]['empty_completion'])
    def test_http_error_retained(self):
        d=self.open();self.io.mode='http-error'
        with self.assertRaises(ClientFailure):d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['outputs'],8)
    def test_unknown_file_blocks_before_dispatch(self):
        d=self.open();(d.root/'unknown').write_bytes(b'x')
        with self.assertRaises(SafetyError):d.generate(MESSAGES,max_output=8)
    def test_symlink_root_rejected(self):
        target=self.base/'target';target.mkdir();link=self.base/'link';link.symlink_to(target,target_is_directory=True)
        try:
            with self.assertRaises(SafetyError):live.LiveDriver(link,self.runtime,self.limits,transport=self.io,validator=lambda r:self.base)
        finally:
            link.unlink()
    def test_control_single_writer_and_cleanup_reserve(self):
        d=self.open()
        with self.assertRaises(SafetyError):live.ControlJournal(d.root/'control.jsonl',d.ledger.binding)
        for _ in range(24):d.control.charge('get')
        with self.assertRaises(SafetyError):d.control.charge('get')
        d.control.charge('cleanup_get');d.control.charge('unload')
    def test_control_quota_failure_prevents_start(self):
        with patch.object(live.os,'posix_fallocate',side_effect=OSError(122,'quota')):
            with self.assertRaises(OSError):self.open()
        self.assertEqual(self.io.requests,[])
    def test_audit_failure_before_dispatch(self):
        d=self.open()
        with patch.object(d.ledger,'put_artifact',side_effect=OSError('quota')):
            with self.assertRaises(OSError):d.generate(MESSAGES,max_output=8)
        self.assertFalse(any(x.get('path')=='/v1/chat/completions' for x in self.io.requests))
    def test_control_partial_line_refused(self):
        d=self.open();path=d.root/'control.jsonl';d.close();self.d=None
        b=path.read_bytes().rstrip(b'\0');path.write_bytes(b[:-1])
        with self.assertRaises(SafetyError):self.open()
    def test_rpc_timeout_sends_real_worker_signals(self):
        d=self.open();rpc=live.RPC(d.control,time.monotonic()+4,lambda k,b:None)
        with self.assertRaises(TimeoutError):rpc.call({'kind':'fixture','mode':'hang'},.5)
        events=[r['event'] for r in d.control.rows]
        self.assertTrue(any(e['kind']=='signal' and e['signal']==int(signal.SIGKILL) and e['sent'] for e in events))
    def test_rpc_exit_is_failure(self):
        d=self.open();rpc=live.RPC(d.control,time.monotonic()+4,lambda k,b:None)
        with self.assertRaises(ClientFailure):rpc.call({'kind':'fixture','mode':'exit'},2)
    def test_rpc_oversize_refused(self):
        d=self.open();rpc=live.RPC(d.control,time.monotonic()+4,lambda k,b:None)
        with self.assertRaises(ClientFailure):rpc.call({'kind':'fixture','mode':'oversize'},2)

    def test_rpc_cold_render_uses_remaining_guardian_budget(self):
        spec = {'kind':'http','method':'POST','path':'/api/chat','body':{'_debug_render_only':True}}
        stdin = SimpleNamespace(buffer=BytesIO(live.canonical(spec)))
        stdout = StringIO()
        with (patch.object(live,'stop_with_parent'),
              patch.object(live,'require_authorization'),
              patch.object(sys,'stdin',stdin),patch.object(sys,'stdout',stdout),
              patch.object(live.time,'monotonic',return_value=100),
              patch('http.client.HTTPConnection') as connection):
            worker = connection.return_value
            worker.getresponse.return_value.status = 200
            worker.getresponse.return_value.read.return_value = b'{}'
            live.rpc_worker(10,145)
        connection.assert_called_once_with('127.0.0.1',11434,timeout=45)
        self.assertEqual([json.loads(line)['phase'] for line in stdout.getvalue().splitlines()],['sent','result'])

    def test_rpc_expired_guardian_budget_does_not_open_http_connection(self):
        spec = {'kind':'http','method':'GET','path':'/api/ps','body':None}
        stdin = SimpleNamespace(buffer=BytesIO(live.canonical(spec)))
        stdout = StringIO()
        with (patch.object(live,'stop_with_parent'),
              patch.object(live,'require_authorization'),
              patch.object(sys,'stdin',stdin),patch.object(sys,'stdout',stdout),
              patch.object(live.time,'monotonic',return_value=100),
              patch('http.client.HTTPConnection') as connection):
            with self.assertRaises(SystemExit):
                live.rpc_worker(10,99)
        connection.assert_not_called()
        self.assertEqual(json.loads(stdout.getvalue())['error'],'TimeoutError')

    def test_formal_only_metadata_render_uses_extended_rpc_cap(self):
        spec={'kind':'http','method':'POST','path':'/api/chat','body':{'_debug_render_only':True}}
        self.assertEqual(live.rpc_seconds(spec,True),120)
        self.assertEqual(live.rpc_seconds(spec,False),60)
        self.assertEqual(live.rpc_seconds(dict(spec,path='/v1/chat/completions'),True),60)
        self.assertEqual(live.rpc_seconds(dict(spec,body={'messages':[],'keep_alive':0}),True),60)

    def test_binding_and_generation_have_separate_clocks_with_fixture(self):
        self.limits=replace(self.limits,wall_seconds=480,operation_seconds=60)
        d=self.open()
        d.prepare_seconds=150
        d.generate(MESSAGES,max_output=8)
        clocks=self.runner_events('phase-clock')
        self.assertEqual([row['phase'] for row in clocks],['prepare','generate'])
        self.assertAlmostEqual(clocks[0]['deadline_mono']-clocks[0]['start_mono'],150,places=2)
        self.assertAlmostEqual(clocks[1]['deadline_mono']-clocks[1]['start_mono'],60,places=2)
        self.assertLess(clocks[0]['start_mono'],clocks[1]['start_mono'])

    def application_driver(self, style):
        plan = [
            {'id': 'full', 'family': 'fictional', 'style': style, 'condition': 'Full', 'partition': 'synthetic'},
            {'id': 'none', 'family': 'fictional', 'style': style, 'condition': 'No-A2A', 'partition': 'synthetic'},
        ]
        self.d = live.LiveDriver(self.base/'driver', self.runtime, self.limits,
            transport=self.io, validator=lambda r: self.base/'models', plan=plan)
        self.io.driver = self.d
        return self.d

    def agents(self, evidence='fictional Alice evidence'):
        return [
            LocalAgent(PrivateView('Alice', 'Bob', 'invented question', evidence),
                       '$name $question $information'),
            LocalAgent(PrivateView('Bob', 'Alice', 'invented question', 'fictional Bob evidence'),
                       '$name $question $information'),
        ]

    def assert_application_delivery(self, style):
        d = self.application_driver(style)
        full = d.run_episode('full', self.agents())
        none = d.run_episode('none', self.agents())
        self.assertTrue(full['messages'][0]['delivered'])
        self.assertFalse(none['messages'][0]['delivered'])
        self.assertIn('fictional peer', str(d.audit[1]['messages']))
        self.assertNotIn('fictional peer', str(d.audit[3]['messages']))
        self.assertNotIn('fictional Alice evidence', str(d.audit[1]['messages']))
        self.assertEqual(d.ledger.state['episodes'], {'full': 'completed', 'none': 'completed'})
        self.assertEqual(d.ledger.state['outputs'], 32)

    def test_application_base_delivery(self):
        self.assert_application_delivery('base')

    def test_application_protocol_delivery(self):
        self.assert_application_delivery('protocol')

    def test_application_preserves_large_terminal_wire_evidence(self):
        self.limits=replace(self.limits,artifact_bytes=4*1024**2)
        d=self.application_driver('protocol')
        text='Alice: MESSAGE ' + 'x'*8000
        original=self.io.call

        def long_fixture(spec,timeout,crash=False):
            value=original(spec,timeout,crash)
            if spec.get('path')=='/v1/chat/completions':
                value['choices'][0]['message']['content']=text
            return value

        with patch.object(self.io,'call',side_effect=long_fixture):
            result=d.run_episode('full',self.agents(),max_turns=2)
        self.assertEqual(result['transcript'][0],text)
        self.assertTrue(result['messages'][0]['delivered'])
        self.assertEqual(d.ledger.state['episodes']['full'],'completed')
        wire,=[row for row in d.ledger.artifacts.values() if row['path'].endswith('-wire-events.json')]
        self.assertGreater(wire['count'],512*1024)

    def test_application_rejects_changed_large_terminal_checksum(self):
        d=self.application_driver('base')
        original=live.application_frames

        def corrupt(packet,limit):
            if packet['kind']=='result':
                packet['wire']['fixture_padding']='z'*80000
                header,body=original(packet,limit)
                return header,b'x'+body[1:]
            return original(packet,limit)

        with patch.object(live,'application_frames',side_effect=corrupt):
            with self.assertRaisesRegex(SafetyError,'large application result identity changed'):
                d.run_episode('full',self.agents(),max_turns=1)
        self.assertEqual(d.ledger.state['episodes']['full'],'failed')
        self.assertFalse(any(row['path'].endswith('-wire-events.json') for row in d.ledger.artifacts.values()))

    def test_application_pair_mismatch_refused(self):
        d = self.application_driver('base')
        d.run_episode('full', self.agents(), max_turns=1)
        with self.assertRaisesRegex(SafetyError, 'paired private'):
            d.run_episode('none', self.agents('changed fictional evidence'), max_turns=1)
        self.assertEqual(d.ledger.state['episodes']['none'], 'unstarted')

    def test_application_crash_retains_started_failure(self):
        d = self.application_driver('base')
        with self.assertRaises(SafetyError):
            d.run_episode('full', self.agents(), fixture_fault='exit')
        self.assertEqual(d.ledger.state['episodes']['full'], 'failed')
        self.assertEqual(d.ledger.state['requests'], {})
        self.assertEqual(self.io.requests, [])

    def test_interrupted_inflight_keeps_unknown_cost_and_requires_cleanup(self):
        d = self.open()
        d.operation_deadline=time.monotonic()+2
        d.attest(MESSAGES,8)
        d.ledger.reserve_partition('synthetic/0', 'synthetic', 17, 8, 'synthetic')
        d.close()
        self.d = None
        d = self.open()
        with self.assertRaises(SafetyError):
            d.ledger._admit()
        d.recover()
        row = d.ledger.state['requests']['synthetic/0']
        self.assertEqual(row['status'], 'interrupted')
        self.assertIsNone(row['observed_usage'])
        self.assertEqual(d.ledger.state['inputs'], 17)
        self.assertEqual(d.ledger.state['outputs'], 8)
        d.generate(MESSAGES, max_output=8)
        self.assertEqual(d.ledger.state['outputs'], 16)

    def test_paid_worker_timeout_then_cleanup_and_resumed_dispatch(self):
        d=self.open()
        self.io.mode='rpc-timeout'
        with self.assertRaisesRegex(ClientFailure,'timeout'):
            d.generate(MESSAGES,max_output=8)
        first=d.ledger.state['requests']['synthetic/0']
        self.assertEqual(first['status'],'timeout')
        self.assertIsNone(first['observed_usage'])
        self.io.mode='ok'
        d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['outputs'],16)

    def test_other_campaign_cannot_bypass_recovery_after_close(self):
        d=self.open()
        d.generate(MESSAGES,max_output=8)
        d.close()
        self.d=None
        with self.assertRaisesRegex(SafetyError,'previous campaign'):
            live.LiveDriver(self.base/'other',self.runtime,self.limits,transport=FakeIO(),validator=lambda r:self.base)
        d=self.open()
        self.assertTrue(d.ledger.recovery_required)
        d.recover()
        self.assertEqual(d.service_lease.owner(),b'')

    def test_overflow_is_rejected_before_any_http(self):
        d=self.open()
        self.io.n=57
        with self.assertRaisesRegex(ClientFailure,'context_overflow'):
            d.generate(MESSAGES,max_output=8)
        self.assertEqual([r['kind'] for r in self.io.requests],['counter'])

    def runner_events(self, kind):
        return [r['event'] for r in self.d.control.rows if r['event']['kind']==kind]

    def test_early_empty_residency_still_proves_exit_of_pre_dispatch_runner(self):
        d=self.open()
        self.io.mode='timeout-eager'
        with self.assertRaisesRegex(ClientFailure,'timeout'):
            d.generate(MESSAGES,max_output=8)
        bound, = self.runner_events('runner-dispatch-bound')
        self.assertEqual(bound['runner'],RUNNER)
        self.assertEqual(self.runner_events('unload-start')[0]['present_before_unload'],[])
        proof, = self.runner_events('unload-complete')
        self.assertEqual(proof['observation']['process_observations'],[dict(RUNNER,observed_stamp=None)])
        self.assertTrue(self.runner_events('dispatch-permit-evaluated')[0]['permitted'])
        self.assertIsNone(d.ledger.state['requests']['synthetic/0']['observed_usage'])
        self.io.mode='ok'
        d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['outputs'],16)

    def test_empty_runner_witness_blocks_dispatch_and_retains_recovery_lease(self):
        d=self.open()
        self.io.mode='missing-runner'
        with self.assertRaisesRegex(SafetyError,'keep fenced'):
            d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['requests'],{})
        self.assertEqual(self.runner_events('unload-complete'),[])
        self.assertEqual(self.runner_events('dispatch-permit-evaluated'),[])
        self.assertEqual(d.service_lease.owner(),d.lease_owner)
        with self.assertRaises(SafetyError):
            d.ledger._admit()
        d.close()
        self.d=None
        d=self.open()
        with self.assertRaisesRegex(SafetyError,'cleanup already attempted'):
            d.recover()
        self.assertEqual(len(self.runner_events('unload-start')),1)

    def test_empty_residency_cannot_release_a_surviving_runner(self):
        d=self.open()
        self.io.mode='timeout-runner-persists'
        with self.assertRaisesRegex(SafetyError,'exit not verified'):
            d.generate(MESSAGES,max_output=8)
        self.assertFalse(self.io.resident)
        self.assertEqual(self.io.runner_stamp,RUNNER['stamp'])
        self.assertEqual(d.service_lease.owner(),d.lease_owner)
        self.assertEqual(self.runner_events('dispatch-permit-evaluated'),[])

    def test_reused_pid_proves_old_identity_gone_but_is_not_owned(self):
        d=self.open()
        self.io.mode='timeout-pid-reused'
        with self.assertRaisesRegex(ClientFailure,'timeout'):
            d.generate(MESSAGES,max_output=8)
        observation=self.runner_events('unload-complete')[0]['observation']
        self.assertEqual(observation['process_observations'],[dict(RUNNER,observed_stamp='777')])
        self.assertEqual(observation['remaining_runners'],[])

    def test_runner_change_between_attestation_and_dispatch_stops_generation(self):
        d=self.open()
        replacement=dict(RUNNER,stamp='557')
        self.scan.side_effect=[[RUNNER],[replacement],[replacement],[]]
        with self.assertRaisesRegex(SafetyError,'keep fenced'):
            d.generate(MESSAGES,max_output=8)
        self.assertEqual(d.ledger.state['requests'],{})
        self.assertEqual(self.runner_events('runner-dispatch-bound'),[])
        self.assertEqual(self.runner_events('dispatch-permit-evaluated'),[])
        self.assertEqual(d.service_lease.owner(),d.lease_owner)

    def test_render_defaults_and_successful_response_recheck(self):
        d=self.open()
        d.generate(MESSAGES,max_output=8)
        render, = [r['body'] for r in self.io.requests if r.get('path')=='/api/chat']
        self.assertNotIn('options',render)
        response, = self.runner_events('runner-response-bound')
        self.assertEqual(response['present_after_response'],[RUNNER])
        self.assertEqual(response['runner'],self.runner_events('runner-dispatch-bound')[0]['runner'])

    def test_new_runner_after_provider_response_is_tracked_and_keeps_fence(self):
        d=self.open()
        replacement=dict(RUNNER,pid=RUNNER['pid']+1,stamp='557')
        self.scan.side_effect=[[RUNNER],[RUNNER],[replacement],[],[]]
        with self.assertRaisesRegex(SafetyError,'keep fenced'):
            d.generate(MESSAGES,max_output=8)
        self.assertIsNone(d.ledger.state['requests']['synthetic/0']['observed_usage'])
        drift, = self.runner_events('runner-response-drift')
        self.assertEqual(drift['present_after_response'],[replacement])
        proof, = self.runner_events('unload-unverified')
        self.assertEqual(proof['observation']['process_observations'],
                         [dict(r,observed_stamp=None) for r in (RUNNER,replacement)])
        self.assertEqual(self.runner_events('dispatch-permit-evaluated'),[])
        self.assertEqual(d.service_lease.owner(),d.lease_owner)

    def test_resource_verification_failure_after_unload_keeps_fence(self):
        d=self.open()
        self.io.mode='timeout-eager'
        calls=[]

        def verify_resources(force=False):
            calls.append(force)
            raise SafetyError('resource sample failed')

        d.resource_monitor=verify_resources
        with self.assertRaisesRegex(SafetyError,'resource sample failed'):
            d.generate(MESSAGES,max_output=8)
        self.assertEqual(calls,[True])
        self.assertEqual(self.runner_events('unload-unverified')[0]['resource_error'],'resource sample failed')
        self.assertEqual(self.runner_events('dispatch-permit-evaluated'),[])
        self.assertEqual(d.service_lease.owner(),d.lease_owner)

    def test_runner_census_checks_parent_executable_model_and_start(self):
        workspace=TemporaryDirectory(prefix='gosc-t1-fake-proc-')
        self.addCleanup(workspace.cleanup)
        proc=Path(workspace.name)
        exe=self.base/'ollama'
        model=Path(self.runtime.root).parents[1]/'models/ollama-gosc/blobs'/live.MODEL_BLOB

        def entry(pid,parent,stamp,args):
            path=proc/str(pid)
            path.mkdir(parents=True)
            (path/'stat').write_text(f"{pid} (with ) space) S {parent} "+'0 '*17+stamp+'\n')
            (path/'exe').symlink_to(exe)
            (path/'cmdline').write_bytes(b'\0'.join(str(x).encode() for x in args)+b'\0')
            return path

        service=replace(self.runtime,service_stamp='1234')
        entry(service.service_pid,1,'1234',[exe,'serve'])
        child=entry(321,service.service_pid,'555',[exe,'runner','--ollama-engine','--model',model])
        entry(999,1,'666',[exe,'runner','--model',model])
        self.assertEqual(self.scan_runners(service,proc),[{'pid':321,'stamp':'555'}])
        (child/'cmdline').write_bytes(b'ollama\0runner\0--model\0wrong\0')
        with self.assertRaisesRegex(SafetyError,'model blob'):
            self.scan_runners(service,proc)
        with self.assertRaisesRegex(SafetyError,'PID identity drift'):
            self.scan_runners(replace(service,service_stamp='8765'),proc)

if __name__=='__main__':unittest.main()
