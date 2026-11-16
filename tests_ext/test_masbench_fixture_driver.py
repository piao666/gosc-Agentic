"""B1 model-free integration; zero real questions, endpoints or model weights."""
from dataclasses import replace
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest

from extensions.masbench_reasoning.application import LocalAgent, PrivateView
from extensions.masbench_reasoning.execution_safety import Limits, SafetyError
from extensions.masbench_reasoning.fixture_driver import (
    FixtureCampaign, CampaignLedger, fixture_rpc, guard_fixture_process, CONTROL_RESERVE)


def agents(information='synthetic private A'):
    return [LocalAgent(PrivateView('Alice','Bob','fixture question',information),'$name $question $information'),
            LocalAgent(PrivateView('Bob','Alice','fixture question','synthetic private B'),'$name $question $information')]


def plan(style='base', partition='task'):
    return [{'id':'full','family':'synthetic-family','style':style,'condition':'Full','partition':partition},
            {'id':'none','family':'synthetic-family','style':style,'condition':'No-A2A','partition':partition}]


class IntegrationContracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/'campaign'
        self.limits=replace(Limits(),requests=6,per_output=8,output_tokens=48,
                            wall_seconds=20,operation_seconds=2,artifact_bytes=512*1024)

    def tearDown(self): self.tmp.cleanup()

    def campaign(self, rows=None, **kw):
        return FixtureCampaign(self.root,{'only':'synthetic'},rows or plan(),
                               kw.pop('limits',self.limits),kw.pop('task_cap',4),kw.pop('synthetic_cap',2),**kw)

    def events(self,suffix):
        return [json.loads(p.read_bytes()) for p in sorted((self.root/'artifacts').glob('*-'+suffix+'.jsonl'))]

    def test_base_full_no_a2a_actual_client_wire_next_request(self):
        self.compare_paths('base')

    def test_protocol_full_no_a2a_board_next_request(self):
        self.compare_paths('protocol')

    def compare_paths(self,style):
        fixture=[{'text':'Alice: MESSAGE <R>synthetic-shared</R>'}, {'text':'Bob: <A>fixture-final</A>'}]
        with self.campaign(plan(style)) as d:
            full=d.run_episode('full',agents(),fixture)
            none=d.run_episode('none',agents(),fixture)
            self.assertEqual(full['final_answer'],'fixture-final')
            self.assertEqual(none['final_answer'],'fixture-final')
            self.assertTrue(full['messages'][0]['delivered'])
            self.assertFalse(none['messages'][0]['delivered'])
            self.assertGreater(full['wire_totals']['wire_bytes'],0)
            self.assertEqual(none['wire_totals']['wire_bytes'],0)
            ready=[x['data'] for x in self.events('client') if x['phase']=='request_ready']
            self.assertIn('synthetic-shared',str(ready[1]['messages']))
            self.assertNotIn('synthetic-shared',str(ready[3]['messages']))
            self.assertNotIn('synthetic private A',str(ready[1]['messages'][0]))
            self.assertEqual('SHARED KNOWLEDGE BOARD' in str(ready[1]['messages']),style=='protocol')
            self.assertEqual(d.ledger.state['metadata'],4)
            self.assertEqual(len(d.ledger.state['requests']),4)
            self.assertEqual(d.ledger.state['outputs'],32)  # 4 reserved maxima, not observed 4.
            self.assertTrue(all(x['max_rss_kib']>0 and x['gpu_peak_bytes'] is None for x in self.events('fixture-worker-cost')))
            self.assertTrue(self.events('wire-events'))
            d.ledger.check_storage()

    def test_seccomp_denies_file_network_fork_exec_and_stdout(self):
        path=Path(self.tmp.name)/'must-not-exist'
        result=fixture_rpc({'identity_mode':'probe','probe_path':str(path)},'identity',None,2)
        self.assertTrue(all(result.values()),result)
        self.assertFalse(path.exists())

    def test_generation_timeout_settles_failed_and_persistent_fence(self):
        limits=replace(self.limits,operation_seconds=.12)
        with self.campaign(limits=limits) as d:
            r=d.run_episode('full',agents(),[{'create_mode':'hang'}],1)
            self.assertEqual(r['end_reason'],'timeout')
            self.assertTrue(d.ledger.state['fenced'])
            self.assertEqual(d.ledger.denominator(),{'full':'failed','none':'unstarted'})
            self.assertEqual(len(d.ledger.state['requests']),1)
            self.assertEqual(d.ledger.state['outputs'],8)
        with self.campaign(limits=limits) as d:
            with self.assertRaises(SafetyError):
                d.run_episode('none',agents(),[{}],1)

    def test_metadata_timeout_is_charged_and_never_generates(self):
        limits=replace(self.limits,operation_seconds=.12)
        with self.campaign(limits=limits) as d:
            r=d.run_episode('full',agents(),[{'identity_mode':'hang'}],1)
            self.assertEqual(r['end_reason'],'timeout')
            self.assertEqual(d.ledger.state['metadata'],1)
            self.assertEqual(len(d.ledger.state['requests']),0)
        with self.campaign(limits=limits) as d:
            self.assertTrue(d.ledger.state['fenced'])

    def test_audit_time_consumes_shared_operation_deadline(self):
        limits=replace(self.limits,operation_seconds=.15)
        with self.campaign(limits=limits) as d:
            emit=d.ledger.emit
            def slow(kind,value):
                if kind=='client' and value['phase']=='request_ready':time.sleep(.18)
                return emit(kind,value)
            d.ledger.emit=slow
            r=d.run_episode('full',agents(),[{}],1)
            self.assertEqual(r['end_reason'],'timeout')
            costs=self.events('fixture-worker-cost')
            self.assertEqual([x['phase'] for x in costs],['identity'])
            self.assertTrue(d.ledger.state['fenced'])

    def test_validation_failure_after_dispatch_never_becomes_completed(self):
        for key,value in [('finish_reason','length'),('prompt_usage_offset',1),('create_mode','error'),('create_mode','oversize')]:
            with self.subTest(key=key,value=value):
                self.root=Path(self.tmp.name)/(key+str(value))
                with self.campaign() as d:
                    r=d.run_episode('full',agents(),[{key:value}],1)
                    self.assertEqual(r['end_reason'],'model_error')
                    self.assertEqual(d.ledger.state['episodes']['full'],'failed')
                    self.assertEqual(next(iter(d.ledger.state['requests'].values()))['status'],'failed')
                    self.assertEqual(d.ledger.state['outputs'],8)

    def test_missing_usage_explicit_null_and_reservation_retained(self):
        with self.campaign() as d:
            r=d.run_episode('full',agents(),[{'text':'<A>fixture</A>','usage':False}],1)
            self.assertTrue(r['usage_missing'])
            self.assertIsNone(next(iter(d.ledger.state['requests'].values()))['observed_usage'])
            self.assertEqual(d.ledger.state['outputs'],8)

    def test_synthetic_partition_cannot_spend_task_allowance(self):
        rows=plan(partition='synthetic')
        with self.campaign(rows,synthetic_cap=1) as d:
            d.run_episode('full',agents(),[{}],1)
            r=d.run_episode('none',agents(),[{}],1)
            self.assertEqual(r['end_reason'],'model_error')
            self.assertEqual(len(d.ledger.state['requests']),1)
        with self.campaign(rows,synthetic_cap=1) as d:
            self.assertEqual(len(d.ledger.state['requests']),1)
            with self.assertRaises(SafetyError): d.run_episode('none',agents(),[{}],1)

    def test_task_partition_cannot_spend_preflight_allowance(self):
        with self.campaign(task_cap=1) as d:
            d.run_episode('full',agents(),[{}],1)
            r=d.run_episode('none',agents(),[{}],1)
            self.assertEqual(r['end_reason'],'model_error')
            self.assertEqual(len(d.ledger.state['requests']),1)

    def test_global_budget_does_not_reset_between_episodes_or_resume(self):
        limits=replace(self.limits,output_tokens=8)
        with self.campaign(limits=limits) as d:
            d.run_episode('full',agents(),[{}],1)
        with self.campaign(limits=limits) as d:
            r=d.run_episode('none',agents(),[{}],1)
            self.assertEqual(r['end_reason'],'model_error')
            self.assertEqual(d.ledger.state['outputs'],8)

    def test_crash_between_turns_fences_even_without_inflight_request(self):
        with self.campaign() as d:
            d.ledger.episode('full','started')
        with self.campaign() as d:
            self.assertTrue(d.ledger.state['fenced'])
            self.assertEqual(d.ledger.denominator()['full'],'interrupted_pending')
            with self.assertRaises(SafetyError):d.run_episode('none',agents(),[{}],1)

    def test_paired_observation_change_rejected_before_second_start(self):
        with self.campaign() as d:
            d.run_episode('full',agents(),[{}],1)
            with self.assertRaises(SafetyError):d.run_episode('none',agents('changed'),[{}],1)
            self.assertEqual(d.ledger.state['episodes']['none'],'unstarted')

    def test_paired_prompt_change_rejected_before_second_start(self):
        with self.campaign() as d:
            d.run_episode('full',agents(),[{}],1)
            changed=agents();changed[0].system+=' altered template'
            with self.assertRaises(SafetyError):d.run_episode('none',changed,[{}],1)
            self.assertEqual(d.ledger.state['episodes']['none'],'unstarted')

    def test_resume_rejects_plan_change_or_artifact_tampering(self):
        with self.campaign() as d:
            d.run_episode('full',agents(),[{}],1)
        rows=plan();rows[0]['condition']='No-A2A'
        with self.assertRaises(SafetyError):self.campaign(rows)
        p=next((self.root/'artifacts').iterdir());p.write_bytes(b'changed')
        with self.assertRaises(SafetyError):self.campaign()

    def test_storage_exhaustion_preserves_started_and_bounded_files(self):
        limits=replace(self.limits,artifact_bytes=CONTROL_RESERVE+4097)
        with self.campaign(limits=limits) as d:
            with self.assertRaises(SafetyError):
                d.run_episode('full',agents(),[{'text':'x'*10000}],1)
            self.assertNotEqual(d.ledger.denominator()['full'],'unstarted')
            total=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
            self.assertLessEqual(total,limits.artifact_bytes)

    def test_unknown_files_and_symlinks_rejected(self):
        with self.campaign() as d:
            (self.root/'outside').write_bytes(b'not registered')
            with self.assertRaises(SafetyError):d.ledger.check_storage()
        with self.assertRaises(SafetyError):self.campaign()
        (self.root/'outside').unlink()
        (self.root/'unsafe-link').symlink_to(Path(self.tmp.name))
        with self.assertRaises(SafetyError):self.campaign()

    def test_more_than_six_turns_and_live_schema_rejected(self):
        with self.campaign() as d:
            with self.assertRaises(SafetyError):d.run_episode('full',agents(),[{}],7)
        rows=plan();rows[0]['endpoint']='http://127.0.0.1:11434/v1'
        with self.assertRaises(SafetyError):self.campaign(rows)

    def test_outer_watchdog_kills_controller_and_inherited_child_on_hang(self):
        marker=Path(self.tmp.name)/'pid'
        code='import os,time\np=os.fork()\nif p==0: time.sleep(30)\nelse:\n open('+repr(str(marker))+',"w").write(str(p)); time.sleep(30)'
        result=guard_fixture_process([sys.executable,'-c',code],self.root,.35)
        self.assertEqual(result['reason'],'timeout')
        self.assertLess(result['elapsed_seconds'],1.5)
        pid=int(marker.read_text())
        self.assert_dead(pid)
        self.assertFalse(result['server_cancel_verified'])

    def test_outer_guard_cleans_child_after_controller_crash(self):
        marker=Path(self.tmp.name)/'crash-pid'
        code='import os,time\np=os.fork()\nif p==0: time.sleep(30)\nelse:\n open('+repr(str(marker))+',"w").write(str(p)); os._exit(77)'
        result=guard_fixture_process([sys.executable,'-c',code],self.root,2)
        self.assertEqual(result['returncode'],77)
        self.assert_dead(int(marker.read_text()))

    def test_outer_guard_interrupts_actual_campaign_and_preserves_inflight(self):
        # Exercise the entire chain, not only the supervisor in isolation.
        code=('from dataclasses import asdict\n'
              'from extensions.masbench_reasoning.fixture_driver import FixtureCampaign\n'
              'from extensions.masbench_reasoning.execution_safety import Limits\n'
              'from tests_ext.test_masbench_fixture_driver import agents,plan\n'
              'd=FixtureCampaign('+repr(str(self.root))+', {"only":"synthetic"},plan(),Limits(**'+
              repr(vars(self.limits))+'),4,2)\n'
              'd.run_episode("full",agents(),[{"create_mode":"hang"}],1)\n')
        result=guard_fixture_process([sys.executable,'-c',code],self.root,1)
        self.assertEqual(result['reason'],'timeout')
        with self.campaign() as d:
            self.assertTrue(d.ledger.state['fenced'])
            self.assertEqual(d.ledger.denominator()['full'],'interrupted_pending')
            self.assertEqual(len(d.ledger.state['requests']),1)
            self.assertEqual(next(iter(d.ledger.state['requests'].values()))['status'],'inflight')
        until=time.monotonic()+.5
        while True:
            live=[]
            for p in Path('/proc').iterdir():
                if not p.name.isdigit():continue
                try: fields=(p/'stat').read_text().split(') ')[1].split()
                except (OSError,IndexError):continue
                if int(fields[2])==result['group'] and fields[0]!='Z':live.append(p.name)
            if not live or time.monotonic()>=until:break
            time.sleep(.01)
        self.assertEqual(live,[])

    def test_outer_resume_uses_original_wall_not_new_start(self):
        limits=replace(self.limits,wall_seconds=.15)
        with self.campaign(limits=limits):pass
        time.sleep(.2)
        with self.assertRaises(SafetyError):
            guard_fixture_process([sys.executable,'-c','pass'],self.root,.15)

    def test_control_reserve_cannot_reset_on_repeat_launch(self):
        self.root.mkdir()
        (self.root/'guard.jsonl').write_bytes(b'x'*(CONTROL_RESERVE-100))
        with self.assertRaises(SafetyError):
            guard_fixture_process([sys.executable,'-c','pass'],self.root,2)

    def test_outer_guard_resume_cannot_increase_cap_or_change_command(self):
        argv=[sys.executable,'-c','pass']
        guard_fixture_process(argv,self.root,2)
        with self.assertRaises(SafetyError):guard_fixture_process(argv,self.root,3)
        with self.assertRaises(SafetyError):
            guard_fixture_process([sys.executable,'-c','print("changed")'],self.root,2)

    def assert_dead(self,pid):
        p=Path(f'/proc/{pid}/stat');until=time.monotonic()+.5
        while p.exists() and p.read_text().split(') ')[1].split()[0]!='Z' and time.monotonic()<until:
            time.sleep(.01)
        if p.exists(): self.assertEqual(p.read_text().split(') ')[1].split()[0],'Z')


if __name__=='__main__':unittest.main()
