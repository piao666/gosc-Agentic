"""Network-denied tests for the one-render diagnostic and exact prior marker."""
import json
import os
from pathlib import Path
import resource
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch
from io import StringIO

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from hpc_runs import require_hpc
from experiments_ext.masbench_t1a_contract import deny_network
from experiments_ext import masbench_t1_cold_load as diag


class Tests(unittest.TestCase):
    def test_kernel_socket_denial(self):
        with self.assertRaises(PermissionError):
            socket.socket()

    def test_render_is_frozen_and_generation_route_unavailable(self):
        method,path,body=diag.request_spec('render')
        self.assertEqual((method,path),('POST','/api/chat'))
        self.assertIs(body['_debug_render_only'],True)
        self.assertEqual(body['messages'],json.loads(diag.PLAN.read_bytes())['cases'][0]['messages'])
        for route in ('generate','chat','/v1/chat/completions'):
            with self.assertRaises(diag.SafetyError):
                diag.request_spec(route)

    def test_http_worker_publishes_metadata_send_and_response(self):
        stdout=StringIO()
        with (patch.object(diag.live,'stop_with_parent'), patch.object(diag,'authorization'),
              patch.object(sys,'stdin',StringIO('version\n')),patch.object(sys,'stdout',stdout),
              patch('http.client.HTTPConnection') as factory):
            conn=factory.return_value
            conn.getresponse.return_value.status=200
            conn.getresponse.return_value.read.return_value=b'{"version":"0.11.11"}'
            diag.endpoint_worker(123,diag.time.monotonic()+3)
        self.assertEqual(factory.call_args.args,('127.0.0.1',11434))
        self.assertEqual(conn.request.call_args.args[:2],('GET','/api/version'))
        self.assertEqual([json.loads(line)['phase'] for line in stdout.getvalue().splitlines()],
                         ['sent','response'])

    def test_recovery_evidence_and_marker_exact(self):
        marker=diag.LEASE.read_bytes()
        self.assertEqual(diag.validate_old_marker(marker)['source_run'],diag.OLD)
        with self.assertRaises(RuntimeError):
            diag.validate_old_marker(marker+b'!')
        self.assertEqual(diag.LEASE.read_bytes(),marker)

    def test_single_render_charge_fails_before_process_spawn(self):
        with tempfile.TemporaryDirectory() as folder:
            control=diag.live.ControlJournal(Path(folder)/'control.jsonl','fixture',diag.CAPS)
            try:
                control.charge('debug')
                campaign=diag.Campaign(Path(folder),control,Path(folder))
                with patch.object(diag.subprocess,'Popen') as spawn:
                    with self.assertRaises(diag.SafetyError):
                        campaign.request('render','debug',diag.time.monotonic()+5)
                    spawn.assert_not_called()
            finally:
                control.close()

    def test_proc_sample_preserves_stamp_and_mapping(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            proc=root/'123'
            proc.mkdir()
            fields=['0']*22
            fields[0]='S'
            fields[7]='7'
            fields[9]='9'
            fields[19]='99'
            (proc/'stat').write_text('123 (fixture) '+' '.join(fields))
            (proc/'io').write_text('rchar: 10\nread_bytes: 11\n')
            model=root/'model'
            (proc/'maps').write_text(f'1000-2000 r--p 000000 00:00 0 {model}\n')
            row=diag.runner_sample({'pid':123,'stamp':'99'},model,root)
            self.assertEqual((row['minflt'],row['majflt'],row['io']['read_bytes']),(7,9,11))
            self.assertTrue(row['model_mapped'])
            self.assertEqual(diag.runner_sample({'pid':123,'stamp':'100'},model,root)['status'],'identity-changed')


if __name__=='__main__':
    require_hpc()
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    os.environ['CUDA_VISIBLE_DEVICES']=''
    deny_network()
    unittest.main(verbosity=2)
