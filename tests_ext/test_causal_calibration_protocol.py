"""Protocol completeness and unchanged GP-v1 execution against committed source."""
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import pytest
from scripts.repro_causal_service import cases,make,ROOT

def test_candidate_grid_split_and_resource_budget_are_prespecified():
    p=json.loads((ROOT/'research/protocols/causal_service_stage_v2.json').read_text())
    cc=cases(p);assert len(cc)==21
    assert len([c for c in cc if c['mode']!='tom'])==10
    for arm in ('public','pose','age'):
        assert sorted(c['price'] for c in cc if c['mode']=='tom' and c['arm']==arm)==p['prices']
    assert not set(p['probe_seeds'])&set(p['calibration_seeds'])
    assert max(p['calibration_seeds'])<min(p['test_reserved_seeds'])
    assert p['bonferroni_family']==len(p['primary_comparisons'])*len(p['primary_endpoints'])==6
    assert p['new_llm_calls']==0 and not p['training'] and not p['test_execution_authorized']

@pytest.mark.parametrize('seed',[21000000,21000001])
def test_legacy_default_exactly_matches_archived_GP_v1_source(tmp_path,seed):
    archive=subprocess.check_output(['git','archive','47389eba9c6e2838139df3aa47863ab88634e97a','gosc','extensions'],cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tf:
        for member in tf:
            if member.isfile():
                target=tmp_path/member.name;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(tf.extractfile(member).read())
    code=('import json;from gosc.config import Config;from extensions.paid_receiver_service import ServiceConfig;'
          'from extensions.paired_paid_simulation import PairedPaidSimulation;'
          f's=PairedPaidSimulation(Config(max_steps=16),{seed},ServiceConfig(100,2000,1.,.001,.001),use_pose=True);'
          'print(json.dumps(s.run(),sort_keys=True))')
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    before=json.loads(subprocess.check_output([os.sys.executable,'-c',code],cwd=tmp_path,env=env))
    after=json.loads(subprocess.check_output([os.sys.executable,'-c',code],cwd=ROOT,env=env))
    assert before==after
