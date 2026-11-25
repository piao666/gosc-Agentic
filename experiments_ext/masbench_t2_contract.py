"""Re-run the existing no-network driver contracts, then check the T2 profile."""
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
import hpc_ollama
from experiments_ext import masbench_t1a_contract as existing
from experiments_ext.masbench_t1b_live import process_rss
from extensions.masbench_reasoning import live_driver as live
from extensions.masbench_reasoning.execution_safety import Limits, SafetyError


def main():
    if existing.main():
        return 1
    output = Path(os.environ['GOSC_OUTPUT_DIR'])
    authorization = ROOT/live.T2_AUTH
    with patch.dict(os.environ,{'GOSC_RUN_DIR':str(ROOT/'research/sync/runs/hpc-masbench-t2-live-v3-20261125')}):
        approved = live.require_authorization(authorization)
        assert approved['scope']=='T2 synthetic only' and approved['context']==16384
        assert approved['generation_seconds']==180
        for method,path,seconds in [('POST','/v1/chat/completions',180),('GET','/api/ps',60)]:
            spec={'kind':'http','method':method,'path':path}
            assert live.rpc_seconds(spec,True,180)==seconds and live.rpc_seconds(spec,False,180)==60
        runtime = live.Runtime(str(output),'/unopened',1,'fixture','0'*64)
        try:
            live.LiveDriver(output/'wrong-context',runtime,Limits(),authorization=authorization)
        except SafetyError as error:
            assert 'runtime profile' in str(error)
        else:
            raise AssertionError('mismatched authorized context was accepted')
        assert not (output/'wrong-context').exists()
    candidate = output/'fixture_context_profile.json'
    with patch.object(hpc_ollama,'CONTEXT_PROFILE',candidate):
        assert hpc_ollama.settings(base_env={})[3]['OLLAMA_CONTEXT_LENGTH']=='1024'
        candidate.write_text(json.dumps({'context_tokens':16384}),encoding='utf-8')
        assert hpc_ollama.settings(base_env={})[3]['OLLAMA_CONTEXT_LENGTH']=='16384'
        assert hpc_ollama.settings(base_env={})[3]['OLLAMA_CONTEXT_LENGTH']=='16384'
    page = os.sysconf('SC_PAGE_SIZE')
    processes = {100:(1,20),101:(100,7),102:(101,9),200:(100,37),201:(200,80),202:(201,40)}
    assert process_rss(100,200,processes)==(36*page,157*page)
    processes[200]=(1,37)
    assert process_rss(100,200,processes)==(36*page,157*page)
    print('T2 profile contracts passed: frozen scope, runtime drift refusal, persistent startup, disjoint RSS accounting')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
