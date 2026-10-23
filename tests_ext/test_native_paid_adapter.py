import math
import pytest
import numpy as np
from gosc.config import Config
from gosc.belief import Obs
from gosc.messages import Packet
from gosc.simulator import Simulation
from gosc.channel import Channel
from extensions.native_task_wire import encode_packet,decode_packet,service_bits,WireGOSC
from extensions.native_paid_adapter import NativePaidSimulation
from extensions.paid_receiver_service import ServiceConfig,envelope,open_envelope


@pytest.mark.parametrize('pkt',[
    Packet('CONF',1,18,2,confirm=7),Packet('INTENT',1,18,2,intent=9),
    Packet('EVID',1,99,5,records=[Obs(1,1,(2,3),(67,)),Obs(5,1,(3,4),())])])
def test_semantics_roundtrip_and_envelope_accounting(pkt):
    cfg=Config();body=encode_packet(pkt,cfg);decoded=decode_packet(body,cfg)
    assert (decoded.kind,decoded.sender,decoded.created,decoded.confirm,decoded.intent,decoded.records)==(pkt.kind,pkt.sender,pkt.created,pkt.confirm,pkt.intent,pkt.records)
    wire=envelope(192,bytes([pkt.sender])+bytes(4)+body)
    assert len(wire)*8==service_bits(pkt,cfg)
    assert open_envelope(wire)[1][5:]==body


@pytest.mark.parametrize('bad',[
    Packet('RAW',0,0,0),Packet('EVID',0,0,0),Packet('CONF',0,0,0,confirm=1024),
    Packet('EVID',0,0,0,records=[Obs(1,0,(0,0),())]),
    Packet('EVID',0,0,1,records=[Obs(0,1,(0,0),())])])
def test_codec_rejects_unsupported_or_hidden_metadata(bad):
    with pytest.raises(ValueError):encode_packet(bad,Config())


def test_wire_rejects_truncation_trailing_bad_namespace_crc():
    cfg=Config();body=encode_packet(Packet('EVID',0,0,0,records=[Obs(0,0,(0,0),(0,))]),cfg)
    for invalid in (body[:-1],body+b'\0',b'bad'+body[3:]):
        with pytest.raises(ValueError):decode_packet(invalid,cfg)
    frame=bytearray(envelope(192,body));frame[-1]^=1
    with pytest.raises(ValueError):open_envelope(bytes(frame))


@pytest.mark.parametrize('mode',['tom','bits','aoi'])
def test_wire_lengths_prefix_and_success_probability_rebuilt(mode):
    cfg=Config(symbols_per_slot=70)
    sim=Simulation(cfg,'gosc',16000000);sim.phase_decide(0)
    sch=WireGOSC(cfg,sim.channel,mode);a=sim.agents[0]
    a.pending_records=[Obs(0,0,(1,1),()),Obs(0,0,(1,2),())]
    groups=sch.build_groups(a,10.,sim)
    for g in groups:
        for opt in g.options:
            pkt=sch.packet(a,g,opt,sim.t)
            assert opt.bits==service_bits(pkt,cfg)
            assert opt.symbols==math.ceil(opt.bits/opt.rate)<=70
            if g.kind=='EVID':
                n=opt.n_records
                if n<len(a.pending_records):
                    assert math.ceil(service_bits(Packet('EVID',0,0,0,records=a.pending_records[:n+1]),cfg)/opt.rate)>70


def sc(**kw):
    args=dict(ul_capacity=100,dl_capacity=2000,slot_seconds=1.,encode_seconds=0.,decode_seconds=0.)
    args.update(kw);return ServiceConfig(**args)


def test_native_receipt_no_duplicate_evidence_and_sender_pending_cleared_only_once():
    sim=NativePaidSimulation(Config(max_steps=3),16000001,sc(),mode='bits')
    rec=Obs(0,0,(0,0),());pkt=Packet('EVID',0,0,0,records=[rec]);body=encode_packet(pkt,sim.cfg)
    before=sim.local[1].Lc.copy();private=sim.agents[0].pending_llr.copy()
    sim.sensor.apply(sim.agents[0].pending_llr,rec)
    sim._local_packet(1,0,0,body);after=sim.local[1].Lc.copy()
    assert not np.array_equal(before,after)
    sim._local_packet(1,0,0,body);np.testing.assert_array_equal(after,sim.local[1].Lc)
    sim._local_packet(0,0,0,body)
    np.testing.assert_allclose(sim.agents[0].pending_llr,private,atol=1e-15)
    assert sim.service.knowledge.native[1][0].created==0


def test_edge_confirmation_cannot_clear_uninformed_agent_pending():
    sim=NativePaidSimulation(Config(),16000001,sc(),mode='bits')
    sim.agents[1].confirmed_pending.add(5)
    sim._edge_packet(Packet('CONF',0,0,0,confirm=5),0)
    assert not sim.local[1].declared[5] and 5 in sim.agents[1].confirmed_pending
    sim._local_packet(1,0,0,encode_packet(Packet('CONF',0,0,0,confirm=5),sim.cfg))
    assert sim.local[1].declared[5] and 5 not in sim.agents[1].confirmed_pending


def test_short_native_loop_uses_actual_multirate_wire_and_paid_dl():
    sim=NativePaidSimulation(Config(max_steps=4,energy_price=0.),16000002,sc(),mode='bits')
    out=sim.run()
    assert out['service']['slots']==4 and out['service']['cost']['ul_uses']>0
    assert out['service']['cost']['dl_uses']>0 and sim._local_seen
    assert 'symbols' not in out and out['scheme']=='native_paid_bits_public'
    for e in sim.service.events:
        if e['kind']=='ul':assert e['ul_uses']<=100


def test_zero_dl_native_loop_cannot_update_public_views_or_free_ack():
    sim=NativePaidSimulation(Config(max_steps=3,energy_price=0.),16000002,sc(dl_capacity=0),mode='bits',use_pose=True)
    initial=[s.Lc.copy() for s in sim.local];out=sim.run()
    assert not sim._local_seen and sim._outstanding
    for x,s in zip(initial,sim.local):np.testing.assert_array_equal(x,s.Lc)
    assert not any(sim.service.knowledge.cache.values())
    assert out['service']['pending_dl_frames']>0


def test_task_specific_rate_is_used_by_service_not_default_summary_rate():
    from extensions.paid_receiver_service import PaidReceiverService
    s=PaidReceiverService({0:(0,0)},32,sc(ul_capacity=40))
    s.submit_task(0,b'',0,rate=2.)  # 10 bytes at rate2 =>40 uses, fits
    s.tick(0)
    assert s.cost['ul_uses']==40 and s.seen=={(0,0)}
