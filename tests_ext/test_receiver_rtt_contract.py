import pytest

from extensions.receiver_rtt_contract import RTTLane
from extensions.receiver_summary_audit import encode
from extensions.receiver_transport_replay import feedback,read_feedback,batch


def app(t,pose=0):return encode(0,t,3,pose)


def test_no_overlap_and_supersession_cannot_reset_or_bypass_rto():
    lane=RTTLane(0,delay=2)
    lane.offer(app(0),0);assert lane.attempt(0,100)
    lane.offer(app(1,1),1);assert lane.attempt(1,100) is None
    lane.offer(app(2,2),2);assert lane.attempt(2,100) is None
    tx=lane.attempt(3,100)
    assert tx.created==2 and lane.next_retry==6


def test_received_old_ack_releases_lane_without_deleting_new_pending():
    lane=RTTLane(0,delay=2)
    lane.offer(app(0),0);lane.attempt(0,100)
    lane.offer(app(1),1)
    packet=feedback([(0,0,True)])
    for sender,tx,good in read_feedback(packet):
        assert sender==lane.sender;lane.feedback(tx,good,3)
    assert lane.pending[0]==1 and lane.inflight is None
    assert lane.attempt(3,100).created==1


def test_late_ack_does_not_release_newer_inflight_attempt():
    lane=RTTLane(0)
    lane.offer(app(0),0);lane.attempt(0,100)
    lane.offer(app(1),1);lane.attempt(1,100)
    lane.feedback(0,True,2)
    assert lane.inflight.created==1 and lane.pending[0]==1


def test_no_free_retry_or_packet_when_budget_full():
    lane=RTTLane(0)
    lane.offer(app(0),0)
    assert lane.attempt(0,50,original_used=50) is None
    assert lane.ul_bytes==lane.ul_uses==0
    assert lane.attempt(1,50,original_used=2).ul_uses==48
    assert lane.attempt(2,50,original_used=2).ul_uses==48
    assert lane.ul_bytes==12 and lane.ul_uses==96 and lane.retries==1
    assert lane.attempt(2,100) is None


def test_ack_causal_delay_crc_and_nack_allow_retry():
    lane=RTTLane(0,delay=2)
    lane.offer(app(0),0);lane.attempt(0,100)
    with pytest.raises(ValueError,match='causal'):lane.feedback(0,True,1)
    lane.feedback(0,False,3)
    assert lane.attempt(3,100)
    bad=bytearray(feedback([(0,3,True)]));bad[-1]^=1
    with pytest.raises(ValueError,match='CRC'):read_feedback(bytes(bad))


def test_expiry_censor_and_control_lengths_are_explicit():
    lane=RTTLane(0,ttl=1,delay=2)
    lane.offer(app(0),0);lane.attempt(0,100)
    assert lane.censored(1)['inflight']
    assert lane.attempt(2,100) is None and lane.pending is None
    assert len(feedback([(0,0,True)]))==6
    assert len(batch([app(0)]))==8


def test_generation_identity_bounds_and_monotone_clock():
    lane=RTTLane(0)
    with pytest.raises(ValueError):lane.offer(encode(1,0,2,0),0)
    lane.offer(app(0),0)
    with pytest.raises(ValueError):lane.offer(app(0),0)
    with pytest.raises(ValueError):lane.attempt(1,20,21)
    with pytest.raises(ValueError):lane.attempt(0,100)
    with pytest.raises(ValueError):lane.feedback(88,True,2)
