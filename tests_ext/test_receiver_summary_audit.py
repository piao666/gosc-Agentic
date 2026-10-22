"""Audit contract checks, run on HPC only."""
import numpy as np
import pytest
from extensions.receiver_summary_audit import encode,decode,crc_frame,unframe,private_novelty_bucket,symbols

def test_codec_roundtrip_boundaries_and_actual_frame_bytes():
    for sender in [0,5,31]:
        for t in [0,255,256,399,511]:
            for bucket in [0,7]:
                for pose in [None,0,1023]:
                    app=encode(sender,t,bucket,pose)
                    assert len(app)==(3 if pose is None else 4)
                    wire=crc_frame(app)
                    assert len(wire)==len(app)+2
                    assert unframe(wire,t)=={'sender':sender,'created':t,'bucket':bucket,'pose':pose}
def test_corruption_is_detected():
    frame=bytearray(crc_frame(encode(2,30,5,3)));frame[2]^=1
    with pytest.raises(ValueError,match='CRC'):unframe(bytes(frame),30)
def test_future_expiry_padding_and_unknown_types_rejected():
    for data,now in [(encode(0,30,1),29),(encode(0,30,1),51),
                     (encode(0,30,1)[:-1]+bytes([encode(0,30,1)[-1]|1]),30),
                     (bytes([0xe0])+encode(0,30,1)[1:],30)]:
        with pytest.raises(ValueError):decode(data,now)
    assert decode(encode(0,30,1),50)['created']==30
@pytest.mark.parametrize('args',[(32,0,0),(0,512,0),(0,-1,0),(0,0,8),(0,0,0,1024)])
def test_unsupported_ranges_not_silently_wrapped(args):
    with pytest.raises(ValueError):encode(*args)
def test_same_public_state_different_private_summary_and_noninjectivity():
    common=np.full((32,32),-4.);declared=np.zeros(1024,bool)
    z=np.zeros_like(common);a=z.copy();a[1,1]=4.
    b=z.copy();b[8,9]=4.
    assert private_novelty_bucket(common,z,declared)[0]!=private_novelty_bucket(common,a,declared)[0]
    assert private_novelty_bucket(common,a,declared)==private_novelty_bucket(common,b,declared)
    assert not np.array_equal(a,b) # a scalar bucket cannot reproduce oracle spatial belief
def test_declared_mask_and_no_ground_truth_input():
    common=np.full((32,32),-4.);p=np.zeros_like(common);p[1,1]=4.
    declared=np.zeros(1024,bool);declared[33]=True
    assert private_novelty_bucket(common,p,declared)==(0,0.)
def test_full_frame_and_extra_overhead_are_not_double_counted():
    app=encode(0,0,0)
    assert symbols(len(app)*8,16,1)==len(crc_frame(app))*8==40
    assert symbols(len(app)*8,16,.25)>100
