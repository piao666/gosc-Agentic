import pytest
from extensions.paid_receiver_service import PaidReceiverService,ServiceConfig,envelope,open_envelope

STARTS={0:(1,1),1:(2,2)}

def service(**kw):
    fields=dict(ul_capacity=100,dl_capacity=200,slot_seconds=1.,encode_seconds=0.,decode_seconds=0.)
    fields.update(kw)
    return PaidReceiverService(STARTS,32,ServiceConfig(**fields))

def test_frame_common_crc_and_corruption():
    data=envelope(192,b'abc')
    assert len(data)==8 and open_envelope(data)==(192,b'abc')
    bad=bytearray(data);bad[-1]^=1
    with pytest.raises(ValueError):open_envelope(bytes(bad))

def test_paid_ul_dl_edge_cache_chain_and_no_same_slot_use():
    s=service();s.submit_pose(1,0,0);s.tick(0)
    assert s.edge and not s.knowledge.cache[0]
    s.tick(1)
    assert s.knowledge.cache[0][1].created==0
    assert s.cost['ul_summary_bytes']==6 and s.cost['ul_uses']==48
    assert s.cost['dl_uses']==24+32  # feedback6bytes + snapshot8bytes, rate2

def test_task_priority_no_extra_summary_lane_capacity():
    s=service(ul_capacity=80)
    s.submit_task(0,b'',0);s.submit_pose(0,0,0);s.tick(0)
    assert s.cost['ul_task_bytes']==10 and s.cost['ul_uses']==80
    assert not s.edge and s.lanes[0].count==0

def test_zero_dl_never_makes_edge_cache_public_or_ack_free():
    s=service(dl_capacity=0);s.submit_pose(1,0,0)
    for t in range(5):s.tick(t)
    assert not s.knowledge.cache[0] and s.cost['ul_summary_bytes']==30
    assert s.finish()['pending_dl_frames']>0 and s.finish()['cost']['dl_uses']==0

def test_cpu_encode_and_receive_wait_paid_without_freshening_created():
    s=service(encode_seconds=1.,decode_seconds=1.)
    s.submit_pose(1,0,0);s.tick(0)
    assert not s.edge
    s.tick(1);assert s.edge and not s.knowledge.cache[0]
    s.tick(2);assert not s.knowledge.cache[0]
    s.tick(3);assert not s.knowledge.cache[0]  # ACK and snapshot share one CPU
    s.tick(4);assert s.knowledge.cache[0][1].created==0
    assert s.cost['cpu_seconds']>=5 and s.cost['cpu_queue_wait_seconds']>=2

def test_dl_segment_budget_delays_whole_frame_delivery():
    s=service(dl_capacity=8);s.submit_pose(1,0,0)
    for t in range(3):s.tick(t)
    assert not s.knowledge.cache[0]
    assert s.cost['dl_uses']==24
    assert s.finish()['pending_dl_frames']>0

def test_per_receiver_loss_is_paid_once_not_free_broadcast():
    s=service();s.submit_pose(1,0,0);s.tick(0)
    s.tick(1,dl_ok=lambda observer,kind,wire:observer==1)
    assert not s.knowledge.cache[0] and s.knowledge.cache[1]
    assert s.cost['dl_uses']==56 and s.cost['dl_recipient_erasures']==2

def test_task_ack_and_payload_share_dl_and_are_causal():
    s=service(ul_capacity=160);s.submit_task(0,b'hello',0);s.tick(0)
    assert not s.task_received and s.tasks[0]
    s.tick(1)
    assert not s.tasks[0] and len(s.task_received)==2
    assert all(row[-1]==b'hello' for row in s.task_received)

def test_expired_encode_not_recreated_and_finish_has_no_fake_tail():
    s=service(ttl=1,encode_seconds=2.);s.submit_pose(1,0,0)
    for t in range(3):s.tick(t)
    assert not s.edge and s.cost['cpu_expired_summaries']==1
    before=s.finish();assert before==s.finish() and before['slots']==3

def test_change_trigger_uses_local_pose_only_and_no_false_refresh():
    s=service();assert s.submit_pose(1,0,0,True);s.tick(0)
    assert not s.submit_pose(1,0,1,True);s.tick(1)
    assert s.knowledge.cache[0][1].created==0

@pytest.mark.parametrize('kw',[{'slot_seconds':0},{'dl_capacity':-1},{'encode_seconds':float('nan')},
                              {'delay':1.5},{'ul_rate':0}])
def test_explicit_clock_and_capacity_inputs_required(kw):
    with pytest.raises(ValueError):service(**kw)

def test_no_skipped_or_reversed_service_slot():
    s=service()
    with pytest.raises(ValueError):s.tick(1)
    s.tick(0)
    with pytest.raises(ValueError):s.tick(0)

def test_cost_ledger_recomputes_from_attempts_including_partial_dl():
    s=service(dl_capacity=9);s.submit_task(0,b'',0);s.submit_pose(1,0,0)
    for t in range(4):s.tick(t)
    assert sum(e['ul_uses'] for e in s.events if e['kind']=='ul')==s.cost['ul_uses']
    assert sum(e['uses'] for e in s.events if e['kind']=='dl')==s.cost['dl_uses']
    for t in range(4):
        assert sum(e['uses'] for e in s.events if e['kind']=='dl' and e['t']==t)<=9
    assert s.cost['dl_offered_bytes']>=s.cost['dl_completed_bytes']
