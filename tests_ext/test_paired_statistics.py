import pytest

from experiments_ext.summarize import paired, vectors


def test_common_random_effects_cancel_in_paired_difference():
    # A large shared mission effect must not inflate a fixed treatment difference.
    baseline=[0,100,10000,-1000]
    treatment=[x+3 for x in baseline]
    result=paired(treatment,baseline,comparisons=6)
    assert result["mean"]==3
    assert result["ci95"]==[3,3]
    assert result["family_ci"]==[3,3]


def test_arrival_order_is_not_seed_pairing_order():
    rows=[{"seed":2,"output":{"completion_time":30}},
          {"seed":0,"output":{"completion_time":10}},
          {"seed":1,"output":{"completion_time":20}}]
    assert vectors(rows,"completion_time")==[10,20,30]
    with pytest.raises(ValueError,match="Duplicate seed"):
        vectors([rows[0],rows[0]],"completion_time")
