import pytest
from types import SimpleNamespace
from gosc.config import Config
from extensions.paid_receiver_service import ServiceConfig
from extensions.causal_paid_simulation import CausalPaidSimulation
from extensions.receiver_pose_interface import ReceivedPose

def sim(arm='pose',mode='tom'):
    return CausalPaidSimulation(Config(max_steps=8),21000000,ServiceConfig(100,2000,1.,.001,.001),mode,arm)

def test_paid_ignore_sends_real_summary_and_keeps_public_valuation():
    s=sim('ignore');v=s.local[0];assert s.valuation_view(v,0,0) is v
    r=s.run();assert r['service']['cost']['ul_summary_bytes']>0
    assert r['service']['cost']['valuation_cpu_seconds']>0
    assert r['scheme']=='GP-v2_tom_ignore'

def test_shuffle_only_permutes_valid_newer_received_peers_without_mutation():
    s=sim('shuffle');v=s.local[0];v.t=5
    s.service.knowledge.cache[0]={1:ReceivedPose(3,4,(10,10),23),2:ReceivedPose(3,4,(11,11),23),
                                  3:ReceivedPose(0,1,(12,12),2),0:ReceivedPose(3,4,(13,13),23)}
    before=dict(v.team_pos);p=s.valuation_view(v,0,5);q=s.valuation_view(v,0,5)
    assert p.team_pos==q.team_pos and v.team_pos==before
    assert sorted(p.team_pos[k] for k in (1,2))==[(10,10),(11,11)]
    assert p.team_pos[3]==v.team_pos[3] and p.team_pos[0]==v.team_pos[0]
    assert not hasattr(p,'agents') and not hasattr(p,'event_seed')

@pytest.mark.parametrize('arm',['public','pose','ignore','age','shuffle'])
def test_all_arms_share_world_noise_protocol_and_complete_cost_ledger(arm):
    a=sim(arm);b=sim('public');assert a.input_world_sha256==b.input_world_sha256
    a.phase_decide(0);b.phase_decide(0);assert a.event_field_hashes==b.event_field_hashes
    assert a.decode_dl(0,'task',b'abc')==b.decode_dl(0,'task',b'abc')
    a=sim(arm);r=a.run();c=r['service']['cost']
    assert c['ul_uses']==sum(x['ul_uses'] for x in a.service.events if x['kind']=='ul')
    assert c['dl_uses']==sum(x['uses'] for x in a.service.events if x['kind']=='dl')
    assert r['service']['retry_floor_slots']==2 and r['selection_calls']>0

def test_public_has_no_summary_and_pays_valuation_cpu():
    s=sim('public');r=s.run();c=r['service']['cost']
    assert c['ul_summary_bytes']==0 and c['valuation_cpu_seconds']==pytest.approx(.001*r['selection_calls'])

def test_age_fallback_uses_native_timestamp_not_privileged_pose():
    s=sim('age');v=s.local[0];v.t=5
    assert not s._eligible(v,0,5) and s.valuation_view(v,0,5) is v
    # Poison entries not actually received by this boundary must not contribute.
    s.service.knowledge.cache[0][1]=ReceivedPose(4,6,(10,10),24)
    assert not s._eligible(v,0,5)
