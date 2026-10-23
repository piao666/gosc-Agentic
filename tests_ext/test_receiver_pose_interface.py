"""HPC-only contracts; fixtures are synthetic and are not task-effect evidence."""
import copy
from types import SimpleNamespace

import numpy as np
import pytest

from gosc.belief import Obs
from gosc.config import Config
from gosc.messages import Packet
from gosc.schemes import GOSC
from gosc.realistic import RealisticGOSC, RealisticSimulation
from gosc.simulator import Simulation
from extensions.receiver_pose_interface import (
    NativePose, PoseKnowledge, PoseGOSC, PoseRealisticGOSC,
    PoseLedgerSimulation, PoseLedgerRealisticSimulation,
)
from extensions.receiver_summary_audit import encode, crc_frame
from extensions.receiver_transport_replay import batch


def fixture():
    sim = Simulation(Config(), 'gosc', 15000000)
    sim.phase_decide(0)
    return sim, PoseKnowledge(sim.team_pos, sim.cfg.grid)


def wire(source=1, created=0, pose=0, bucket=3):
    return crc_frame(encode(source, created, bucket, pose))


def signature(groups, values=True):
    return [(g.kind, g.cell, [(o.rate,o.bits,o.symbols,o.value if values else None,o.n_records)
                             for o in g.options]) for g in groups]


@pytest.mark.parametrize('realistic', [False, True])
def test_no_cache_exact_value_and_candidate_fallback(realistic):
    sim, knowledge = fixture()
    native = (RealisticGOSC if realistic else GOSC)(sim.cfg,sim.channel)
    candidate = (PoseRealisticGOSC if realistic else PoseGOSC)(sim.cfg,sim.channel,knowledge)
    for a in sim.agents:
        assert signature(native.build_groups(a,5.,sim)) == signature(candidate.build_groups(a,5.,sim))


def test_projection_contains_no_peer_state_and_preserves_native_arrays():
    sim, knowledge = fixture()
    sim.t = 1
    knowledge.receive_frame(0, wire(), 1)
    before = copy.deepcopy(sim.team_pos)
    projected = knowledge.value_view(sim,0,1)
    assert not hasattr(projected,'agents')
    assert projected.team_pos[1] == (0,0) and projected.team_pos != before
    assert sim.team_pos == before
    assert projected.Lc is sim.Lc and projected.declared is sim.declared
    assert projected.team_intent == sim.team_intent
    projected.team_intent[3] = 9
    assert 3 not in sim.team_intent


@pytest.mark.parametrize('realistic', [False, True])
def test_received_pose_changes_only_values_not_candidates_or_planner(realistic):
    sim, knowledge = fixture()
    sim.t=1
    knowledge.receive_frame(0,wire(),1)
    native=(RealisticGOSC if realistic else GOSC)(sim.cfg,sim.channel)
    candidate=(PoseRealisticGOSC if realistic else PoseGOSC)(sim.cfg,sim.channel,knowledge)
    before=copy.deepcopy(sim.agents[0].__dict__)
    a=sim.agents[0]
    x=native.build_groups(a,5.,sim);y=candidate.build_groups(a,5.,sim)
    assert signature(x,False)==signature(y,False)
    assert any(u.value != v.value for gx,gy in zip(x,y) for u,v in zip(gx.options,gy.options))
    for key in before:
        if isinstance(before[key],np.ndarray):np.testing.assert_array_equal(before[key],a.__dict__[key])
        else:assert before[key]==a.__dict__[key]


def test_bucket_ignored_and_novelty_only_cannot_invent_pose():
    sim, a = fixture();b=PoseKnowledge(sim.team_pos,sim.cfg.grid);sim.t=1
    assert not a.receive_frame(0,crc_frame(encode(1,0,7)),1)
    assert a.receive_frame(0,wire(bucket=0),1)
    assert b.receive_frame(0,wire(bucket=7),1)
    assert a.value_view(sim,0,1).team_pos==b.value_view(sim,0,1).team_pos


def test_causal_delivery_crc_and_future_rejection():
    sim, knowledge=fixture()
    assert not knowledge.receive_frame(0,wire(),0)
    bad=bytearray(wire());bad[-1]^=1
    with pytest.raises(ValueError,match='CRC'):knowledge.receive_frame(0,bytes(bad),1)
    with pytest.raises(ValueError):knowledge.receive_frame(0,wire(created=2),1)
    assert not knowledge.cache[0]


def test_stale_conflicting_unknown_ledger_and_ttl_fall_back():
    sim, k=fixture();sim.t=3
    k.receive_frame(0,wire(),1)
    snap=dict(k.native[0]);snap[1]=NativePose(2,sim.team_pos[1]);k.receive_native(0,snap)
    assert k.value_view(sim,0,3).team_pos==sim.team_pos
    k.receive_frame(0,wire(created=2,pose=1),3)
    assert k.value_view(sim,0,3).team_pos==sim.team_pos  # equal timestamp conflict
    del k.native[0][1]
    assert k.value_view(sim,0,3).team_pos==sim.team_pos
    sim.t=23
    assert k.value_view(sim,0,23).team_pos==sim.team_pos


def test_reordered_and_duplicate_conflicting_generations_fail_closed():
    sim,k=fixture()
    k.receive_frame(0,wire(created=2,pose=1),3)
    assert not k.receive_frame(0,wire(created=0,pose=2),3)
    assert not k.receive_frame(0,wire(created=2,pose=3),3)
    assert not k.receive_frame(0,wire(created=2,pose=1),4)
    assert 1 not in k.cache[0]


def test_batch_only_updates_actual_observer_and_retains_real_age():
    sim,k=fixture()
    encoded=batch([encode(1,0,3,0),encode(2,0,2,1)])
    assert k.receive_snapshot(0,encoded,1)==[True,True]
    assert not k.cache[1] and k.cache[0][1].created==0


@pytest.mark.parametrize('change', [{'tom_oracle':True},{'shared_budget':100},
                                   {'llm_agents':(0,)},{'task':'rescue'}])
def test_unsupported_oracle_shared_llm_rescue_rejected(change):
    cfg=Config().with_(**change)
    with pytest.raises(ValueError):PoseGOSC(cfg,None)


@pytest.mark.parametrize('cls', [PoseLedgerSimulation,PoseLedgerRealisticSimulation])
def test_native_evid_timestamp_does_not_arrive_before_lossy_delayed_snapshot(cls):
    cfg=Config(dl_delay=2)
    sim=cls(cfg,'gosc',15000001)
    a=sim.agents[1]
    rec=Obs(0,1,(0,0),())
    packet=Packet('EVID',1,39,0,records=[rec])
    sim.deliver(a,packet,0)
    sim._downlink(0)
    assert sim.pose_knowledge.native[0][1].created==-1
    sim._downlink(1)
    assert sim.pose_knowledge.native[0][1].created==-1
    sim._downlink(2)
    assert sim.pose_knowledge.native[0][1]==NativePose(0,(0,0))
    # A newer-delivered old record overwrites native's position; ledger follows it.
    sim.deliver(a,Packet('EVID',1,39,3,records=[Obs(0,1,(1,1),())]),3)
    sim._downlink(3);sim._downlink(4);sim._downlink(5)
    assert sim.pose_knowledge.native[0][1]==NativePose(0,(1,1))


@pytest.mark.parametrize('realistic', [False,True])
def test_ledger_only_preserves_native_short_trajectory(realistic):
    cfg=Config(max_steps=3)
    native=(RealisticSimulation if realistic else Simulation)(cfg,'gosc',15000002,record_traj=True)
    ledger=(PoseLedgerRealisticSimulation if realistic else PoseLedgerSimulation)(cfg,'gosc',15000002,record_traj=True)
    assert native.run()==ledger.run()


def test_native_snapshot_replacement_not_timestamp_maximum():
    sim,k=fixture()
    newer=dict(k.native[0]);newer[1]=NativePose(4,(2,2));k.receive_native(0,newer)
    older=dict(newer);older[1]=NativePose(2,(1,1));k.receive_native(0,older)
    assert k.native[0][1]==NativePose(2,(1,1))
