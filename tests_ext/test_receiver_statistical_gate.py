import json
import pytest
from experiments_ext import run_receiver_factorial as runner


@pytest.mark.parametrize('gate',[dict(status='statistically_inconclusive',receiver_diagnostics_allowed=False),
    dict(status='scoped_statistical_agreement',receiver_diagnostics_allowed=True,primary_family=103,completed_fresh=5200)])
def test_receiver_refuses_unpassed_or_incomplete_gate_without_creating_data(tmp_path,monkeypatch,gate):
    (tmp_path/'r4-statistical').mkdir()
    (tmp_path/'r4-statistical/gate.json').write_text(json.dumps(gate))
    monkeypatch.setattr(runner,'verify_plan',lambda run:None)
    with pytest.raises(RuntimeError):runner.execute(tmp_path,1)
    assert not (tmp_path/'diagnostic').exists()
