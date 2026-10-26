"""GP-v2 causal timing and bounded, delivery-blind catchup contracts."""
import math
import pytest
from extensions.paid_receiver_service import ServiceConfig,open_envelope
from extensions.causal_paid_service import CausalPaidService,CausalPolicy,feedback_floor
from extensions.receiver_summary_audit import encode

STARTS={0:(1,1),1:(2,2)}

def service(policy=None,**kw):
    fields=dict(ul_capacity=200,dl_capacity=2000,slot_seconds=1.,encode_seconds=.001,decode_seconds=.001,refresh=1)
    fields.update(kw)
    return CausalPaidService(STARTS,32,ServiceConfig(**fields),policy=policy)

@pytest.mark.parametrize('seconds,delay,expected',[(0,0,1),(.001,0,2),(1.,0,2),(1.001,0,3),(.001,3,5)])
def test_decode_floor_without_future_queue_information(seconds,delay,expected):
    s=service(decode_seconds=seconds,delay=delay)
    assert feedback_floor(s.c)==expected==s.lanes[0].retry_slots

def test_task_and_summary_do_not_retry_before_cpu_feedback_floor():
    s=service();s.submit_task(0,b'',0);s.submit_pose(1,0,0)
    for t in range(4):s.tick(t)
    assert [x['t'] for x in s.attempt_log]==[1]
    assert list(s.lanes[1].attempts)==[1]
    assert s.task_acks and s.lanes[1].pending is None
    assert s.finish()['retry_floor_slots']==2

def test_erased_feedback_retries_remain_paid_and_censored():
    s=service();s.submit_task(0,b'',0);s.submit_pose(1,0,0)
    for t in range(6):s.tick(t,dl_ok=lambda *_:False)
    assert [x['t'] for x in s.attempt_log]==[1,3,5]
    assert list(s.lanes[1].attempts)==[1,3,5]
    assert s.cost['ul_task_bytes']==30 and s.cost['ul_summary_bytes']==18
    assert s.finish()['pending_tasks']==1 and not s.task_received

def test_old_ack_does_not_clear_new_summary_generation():
    s=service(encode_seconds=0.)
    lane=s.lanes[0];lane.offer(encode(0,0,0,0),0);lane.attempt(0,200)
    lane.offer(encode(0,1,0,1),1)
    with pytest.raises(ValueError):lane.feedback(0,True,1)
    lane.feedback(0,True,2)
    assert lane.pending[0]==1
    assert lane.attempt(2,200).created==1

def test_valuation_is_reserved_before_encoding_and_charged_once():
    s=service(CausalPolicy(valuation_seconds=1.2),encode_seconds=.1)
    s.valuation_work(0,0);s.submit_task(0,b'',0)
    s.tick(0);s.tick(1);assert not s.seen
    s.tick(2);assert s.seen
    assert s.cost['valuation_cpu_seconds']==1.2
    assert s.cost['cpu_seconds']>=1.3 and s.cost['cpu_queue_wait_seconds']>=1.2
    assert [x['action'] for x in s.cpu_log[:2]]==['valuation','task_ready']

def test_bounded_replay_count_rate_age_and_missed_delivery_are_retained():
    s=service(CausalPolicy(replay_age=4,replay_limit=2,replay_frames_per_refresh=1),encode_seconds=0.,decode_seconds=0.)
    for k in range(2):s.submit_task(k,b'x',0)
    def dl(receiver,kind,wire):return kind!='task' or receiver==0
    for t in range(9):s.tick(t,dl_ok=dl)
    assert len(s.replay_log)==4
    assert max(s.replays.values())==2
    assert all(sum(x['t']==t for x in s.replay_log)<=1 for t in range(9))
    assert all(x['t']-s.accepted_at[x['sender'],x['ident']]<=4 for x in s.replay_log)
    assert not any(row[1]==1 for row in s.task_received)
    assert s.finish()['replay_aged_out_items']==2

def test_queue_suppression_keeps_partial_frame_and_no_unbounded_offers():
    s=service(CausalPolicy(replay_age=20,replay_limit=2,replay_frames_per_refresh=1),encode_seconds=0.,decode_seconds=0.,dl_capacity=1)
    s.submit_task(0,b'long payload',0)
    for t in range(7):s.tick(t)
    assert not s.replay_log  # Original task frame still queued behind paid ACKs.
    assert s.finish()['pending_dl_frames']>0
    assert s.cost['dl_uses']==7

def test_replay_zero_is_a_real_no_catchup_policy():
    s=service(CausalPolicy(replay_limit=0),encode_seconds=0.)
    s.submit_task(0,b'',0)
    for t in range(5):s.tick(t)
    assert not s.replay_log

def test_actual_ul_dl_ledger_and_per_slot_budget_under_loss():
    s=service(dl_capacity=13);s.submit_task(0,b'',0);s.submit_pose(1,0,0)
    for t in range(12):s.tick(t,ul_ok=lambda src,kind,wire:t%3!=0,dl_ok=lambda *_:t%2==0)
    assert s.cost['ul_uses']==sum(x['ul_uses'] for x in s.events if x['kind']=='ul')
    assert s.cost['dl_uses']==sum(x['uses'] for x in s.events if x['kind']=='dl')
    assert all(sum(x['uses'] for x in s.events if x['kind']=='dl' and x['t']==t)<=13 for t in range(12))
    before=s.finish();assert before==s.finish() and before['slots']==12

@pytest.mark.parametrize('kw',[{'replay_age':-1},{'replay_limit':1.5},{'valuation_seconds':float('nan')}])
def test_policy_rejects_unbounded_invalid_inputs(kw):
    with pytest.raises(ValueError):CausalPolicy(**kw)
