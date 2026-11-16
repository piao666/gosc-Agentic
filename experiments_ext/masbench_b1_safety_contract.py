"""Registered HPC-only unittest entry. No real HTTP/model calls."""
import json
import os
from pathlib import Path
import resource
import signal
import socket
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'scripts'))
from hpc_runs import require_hpc


def main():
    require_hpc()
    signal.alarm(120)
    resource.setrlimit(resource.RLIMIT_CPU, (60,60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16*1024*1024,16*1024*1024))
    def no_network(*args, **kwargs):
        raise AssertionError('network forbidden in B1-pre safety contracts')
    socket.socket.connect = no_network
    socket.socket.connect_ex = no_network
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    suite=unittest.defaultTestLoader.loadTestsFromName('tests_ext.test_masbench_b1_safety')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (out/'safety_contract.json').write_text(json.dumps({
        'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'successful':result.wasSuccessful(),'real_http_requests':0,'model_generations':0,
        'scope':'new independent safety prototype only; not previous 147+5 rerun',
        'python':sys.version},indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
