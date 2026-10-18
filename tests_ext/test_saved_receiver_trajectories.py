"""Small saved-log alignment contracts; no simulator invocation or rollouts."""
import pytest

from experiments_ext.review_saved_receiver_trajectories import (
    assert_attempt_cost_equal, changed_agents, choose_cases, first_difference,
    hold_context, movement_divergence)


def test_current_attempt_cost_excludes_decode_dependent_delivery_and_DL():
    a={"bits":238,"symbols":143,"delivered_bits":199,"dl_bits":199}
    b={**a,"delivered_bits":238,"dl_bits":238}
    assert_attempt_cost_equal(a,b)
    with pytest.raises(AssertionError):assert_attempt_cost_equal(a,{**b,"symbols":144})


def test_unequal_trajectory_tail_is_not_movement_divergence():
    a=[[0,0],[1,0],[2,0],[3,0]]
    result=movement_divergence(a,a+[[4,0]],1)
    assert result["first_motion_slot"] is None
    assert result["unequal_recorded_lengths"]


def test_motion_time_alignment_and_forbidden_current_slot_difference():
    a=[[0,0],[1,0],[2,0],[3,0]]
    b=[[0,0],[1,0],[2,0],[2,1]]
    assert movement_divergence(a,b,1)["first_motion_slot"]==2
    assert movement_divergence(a,b,1)["slots_after_intervention"]==1
    with pytest.raises(AssertionError,match="current motion"):
        movement_divergence(a,b,2)


def test_first_difference_zero_index_and_no_padding():
    assert first_difference([0,1],[1,1])==0
    assert first_difference([0],[0,1]) is None


def test_receiver_comparison_joins_by_id_excludes_sender_keeps_missing():
    a=[{"agent":1,"target":4},{"agent":0,"target":2}]
    b=[{"agent":0,"target":3},{"agent":1,"target":5}]
    assert changed_agents(a,b,0)==[1]
    assert changed_agents(None,b,0) is None
    with pytest.raises(AssertionError):changed_agents(a,b[:1],0)


def test_hysteresis_context_not_a_causal_ablation_and_arrival_exception():
    r={"old_target":3,"target":3,"distance_to_old_target":2,
       "score_best_without_tie_jitter":1.1,"score_old_without_tie_jitter":1.,
       "hysteresis_margin_without_tie_jitter":-.1}
    assert hold_context(r)
    assert not hold_context({**r,"distance_to_old_target":0,"target":7})
    with pytest.raises(AssertionError,match="keep-target"):
        hold_context({**r,"target":7})


def test_posthoc_case_selection_and_nearest_pair_ties_are_explicit():
    ps=[{"point_id":p,"delta_T_mean":m} for p,m in (("a",2.),("b",-3.),("c",.1))]
    rs=[{"point_id":p["point_id"],"replicate":r,"delta_T":d} for p in ps for r,d in ((0,0),(1,4))]
    selected=choose_cases(ps,rs)
    assert selected["positive"]["point"]["point_id"]=="a"
    assert selected["negative"]["point"]["point_id"]=="b"
    assert selected["near_zero"]["point"]["point_id"]=="c"
    assert selected["positive"]["illustrative_pair"]["replicate"]==0
    assert choose_cases([ps[0]],rs)["negative"] is None
