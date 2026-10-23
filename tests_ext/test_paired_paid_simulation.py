import math
import numpy as np
import pytest
from gosc.belief import Obs
from gosc.config import Config
from extensions.paid_receiver_service import ServiceConfig
from extensions.native_task_wire import service_bits
from extensions.paired_paid_simulation import PairedPaidSimulation,event_rng


def sim(mode='periodic',**kw):
    cfg=Config(max_steps=4,sem_interval=4,energy_price=0.,**kw)
    return PairedPaidSimulation(cfg,17000000,ServiceConfig(100,2000,1.,0.,0.),mode=mode)


def test_periodic_gates_admission_but_conf_is_immediate():
    s=sim();s.phase_decide(0);a=s.agents[0]
    assert not s.select(a,10.,s.local[0])
    a.confirmed_pending.add(7)
    selected=s.select(a,10.,s.local[0]);assert selected and all(g.kind=='CONF' for g,o in selected)
    a.confirmed_pending.clear();s.local[0].t=3
    # Initial negative observation may be removed by the shared source filter.
    a.pending_records=[Obs(0,0,(0,0),())]
    # Isolate evidence admission: an INTENT can exhaust the residual slot.
    a.target=None
    assert any(g.kind=='EVID' for g,o in s.select(a,10.,s.local[0]))


@pytest.mark.parametrize('interval',[1,2,4,8])
def test_periodic_actual_prefix_rate_budget_and_fifo(interval):
    s=sim();s.scheme.cfg=s.cfg.with_(sem_interval=interval);s.phase_decide(0)
    a=s.agents[0];a.target=None
    a.pending_records=[Obs(0,0,(0,i%32),tuple(range(i%4))) for i in range(20)]
    s.local[0].t=interval-1
    chosen=s.select(a,.8,s.local[0]);assert len(chosen)==1
    g,o=chosen[0];pkt=s.scheme.packet(a,g,o,interval-1)
    assert pkt.records==a.pending_records[:o.n_records]
    assert o.bits==service_bits(pkt,s.cfg) and o.symbols==math.ceil(o.bits/o.rate)<=100
    expected=[]
    for rate in s.cfg.rates:
        fits=[]
        for n in range(1,21):
            p=s.scheme.packet(a,g,type('O',(),{'n_records':n})(),interval-1)
            bits=service_bits(p,s.cfg);uses=math.ceil(bits/rate)
            if uses<=100:fits.append((n,bits,uses))
        if fits:
            n,b,u=fits[-1];expected.append((b-80)*float(s.channel.success_prob(rate,.8,n=u))/u)
    assert o.value/o.symbols==max(expected)


def test_potential_fields_independent_of_unrelated_random_consumption():
    a=sim('bits');b=sim('tom')
    assert a.input_world_sha256==b.input_world_sha256
    a.sense_rng.random(100);a.plan_rng.random(50);a.channel.rng.random(90)
    a.phase_decide(0);b.phase_decide(0)
    assert a.event_field_hashes==b.event_field_hashes
    assert [x.pos for x in a.agents]==[x.pos for x in b.agents]
    assert a.chan_rng.exponential()==b.chan_rng.exponential()
    assert a.decode_dl(1,'task',b'x')==b.decode_dl(1,'task',b'x')


def test_sensor_overlap_uses_global_cell_potential_field():
    s=sim();s.t=0
    # Same agent potential field, different footprint; compare intersection.
    s._sense_t=0;s._sense_k=0;x=set(s.world.sense((4,4),s.sensor,None))
    s._sense_k=0;y=set(s.world.sense((4,5),s.sensor,None))
    ax,ay=s.sensor.window((4,4));bx,by=s.sensor.window((4,5))
    overlap={i*32+j for i in range(max(ax.start,bx.start),min(ax.stop,bx.stop))
             for j in range(max(ay.start,by.start),min(ay.stop,by.stop))}
    assert x&overlap==y&overlap


def test_fbl_and_dl_events_reproducible_without_stream_alignment():
    a=sim('tom',error_model='fbl');b=sim('tom',error_model='fbl')
    a.t=b.t=3
    before=[a.decode_ul(2,'task',b'abc',1.,1.) for _ in range(3)]
    a.decode_ul(0,'summary',b'other',2.,4.)
    assert before==[b.decode_ul(2,'task',b'abc',1.,1.)]*3
    assert event_rng(17000000,204,3,2,'task',b'abc').random()!=event_rng(17000000,204,4,2,'task',b'abc').random()
    for k in range(6):
        assert not PairedPaidSimulation(a.cfg,17000000,a.service.c,dl_loss=1.).decode_dl(k,'task',b'x')


def test_repeated_paired_mission_exact_and_cost_ledger():
    a=sim();b=sim();x=a.run();y=b.run();assert x==y
    assert x['service']['cost']['ul_uses']==sum(e['ul_uses'] for e in a.service.events if e['kind']=='ul')
    assert x['service']['cost']['dl_uses']==sum(e['uses'] for e in a.service.events if e['kind']=='dl')
    assert x['scheme']=='native_paid_periodic_public'


def test_dl_erasures_cannot_deliver_private_state_or_ack():
    s=sim('bits');s.event_dl_loss=1.;s.run()
    assert not s._local_seen and not s.service.task_acks
    assert s._outstanding and s.service.cost['dl_recipient_erasures']>0


def test_invalid_periodic_interval_rejected():
    from extensions.wire_periodic import WirePeriodic
    s=sim()
    with pytest.raises(ValueError):WirePeriodic(s.cfg.with_(sem_interval=0),s.channel)
