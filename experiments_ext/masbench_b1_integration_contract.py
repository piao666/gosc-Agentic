"""HPC-only registered, model-free integration contract entry."""
import json
import os
from pathlib import Path
import resource
import signal
import socket
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc


def main():
    require_hpc()
    signal.alarm(120)
    resource.setrlimit(resource.RLIMIT_CPU,(60,60))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
    def forbidden(*args,**kwargs):raise AssertionError('network forbidden')
    socket.socket.connect=forbidden;socket.socket.connect_ex=forbidden
    suite=unittest.defaultTestLoader.loadTestsFromName('tests_ext.test_masbench_fixture_driver')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    (out/'integration_contract.json').write_text(json.dumps({
        'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'successful':result.wasSuccessful(),'real_model_generations':0,'real_reasoning_episodes':0,
        'real_http_requests':0,'python':sys.version,
        'scope':'new fixture-only driver integration; historical 147+5 and 17 not rerun'},indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
