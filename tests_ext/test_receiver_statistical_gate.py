import json
import pytest
from experiments_ext import run_receiver_factorial as runner
from experiments_ext.receiver_admission import check_tom_rows,verify_admission


@pytest.mark.parametrize('gate',[dict(status='statistically_inconclusive',receiver_diagnostics_allowed=False),
    dict(status='scoped_statistical_agreement',receiver_diagnostics_allowed=True,primary_family=103,completed_fresh=5200)])
def test_receiver_refuses_unpassed_or_incomplete_gate_without_creating_data(tmp_path,monkeypatch,gate):
    (tmp_path/'r4-statistical').mkdir()
    (tmp_path/'r4-statistical/gate.json').write_text(json.dumps(gate))
    monkeypatch.setattr(runner,'verify_plan',lambda run:None)
    with pytest.raises(RuntimeError):runner.execute(tmp_path,1)
    assert not (tmp_path/'diagnostic').exists()


def test_scoped_admission_is_explicit_not_a_default_bypass(tmp_path):
    (tmp_path/'r4-statistical').mkdir()
    (tmp_path/'r4-statistical/gate.json').write_text(json.dumps(dict(status='statistically_inconclusive',receiver_diagnostics_allowed=False)))
    with pytest.raises(RuntimeError,match='approval record'):
        verify_admission(tmp_path,'tom-path-diagnostic-only')
    with pytest.raises(RuntimeError,match='default admission'):
        verify_admission(tmp_path)


def tom_fixture():
    job=dict(campaign='private-original',scheme='gosc',param='default/shared',seed=0,config_key='frozen',expected={'symbols':100})
    row=dict(job_id=0,**{k:v for k,v in job.items() if k!='expected'},status='completed',
             output={'symbols':100},reference_differences=[])
    return row,job


def test_tom_admission_requires_actual_reference_agreement_not_a_status_flag():
    row,job=tom_fixture()
    assert check_tom_rows([row],[job])=={'private-original':1}
    row['output']['symbols']=101
    with pytest.raises(RuntimeError,match='agreement failed'):check_tom_rows([row],[job])


def test_tom_evidence_rejects_duplicates_and_wrong_pairing():
    row,job=tom_fixture()
    with pytest.raises(RuntimeError,match='Duplicate'):check_tom_rows([row,row],[job])
    row['seed']=1
    with pytest.raises(RuntimeError,match='identity'):check_tom_rows([row],[job])
