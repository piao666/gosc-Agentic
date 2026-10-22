import pytest
from extensions.receiver_summary_audit import encode
from extensions.receiver_transport_replay import feedback,read_feedback,batch,read_batch,replay

def rows(T=8,used=0):
    return [{'t':t,'agent':k,'original_used':used,'snr_instant':10.,'pose_cell':k,'bucket':3} for t in range(T) for k in range(6)]
def test_feedback_actual_identity_and_crc_bytes():
    items=[(0,255,False),(5,399,True)]
    packet=feedback(items)
    assert read_feedback(packet)==items and len(packet)==4+2*len(items)
    corrupted=bytearray(packet);corrupted[3]^=1
    with pytest.raises(ValueError,match='CRC'):read_feedback(bytes(corrupted))
def test_snapshot_nested_frame_sizes_timestamp_and_crc():
    apps=[encode(0,255,2),encode(5,399,3,1023)]
    packet=batch(apps)
    assert len(packet)==4+3+4
    assert [x['created'] for x in read_batch(packet,399)]==[255,399]
    bad=bytearray(packet);bad[-1]^=1
    with pytest.raises(ValueError,match='CRC'):read_batch(bytes(bad),399)
def test_no_delivery_in_same_slot_and_ack_clears_only_own_generation():
    result=replay(rows(),5,False,0.,0,12000000,100)
    assert result['age_summary']['min']==1
    assert result['counts']['uplink_pending_cleared_by_received_ack']>0
    assert result['ul_residual_budget_invariant']
def test_no_free_packet_when_original_budget_is_full():
    result=replay(rows(used=50),1,True,0.,0,12000000,50)
    assert result['counts']['uplink_attempts']==0
    assert result['counts']['usable_fraction']==0
    assert result['counts']['total_added_channel_uses']==0
def test_lost_feedback_causes_paid_retry_not_free_success():
    result=replay(rows(),10,False,1.,0,12000000,100)
    c=result['counts']
    assert c['retransmission_attempts']>0 and c['duplicate_uplink_decodes']>0
    assert c['usable_fraction']==0 and c['uplink_pending_cleared_by_received_ack']==0
def test_delayed_old_ack_cannot_clear_a_newer_summary():
    result=replay(rows(10),1,False,0.,2,12000000,100)
    assert result['counts']['uplink_pending_cleared_by_received_ack']==0
    assert result['age_summary']['min']==3
def test_crc_and_control_airtime_not_counted_as_one_bit_per_packet():
    result=replay(rows(1),10,False,0.,0,12000000,100)
    c=result['counts']
    assert c['uplink_symbols']==6*5*8
    assert c['downlink_feedback_bytes']==4+6*2
    assert c['downlink_snapshot_bytes']==4+6*3
    assert c['total_added_channel_uses']==240+64+88
