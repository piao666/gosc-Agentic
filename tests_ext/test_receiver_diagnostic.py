"""Meaningful isolation checks before any receiver pilot outcomes are collected."""
import numpy as np
from types import SimpleNamespace
from gosc import Config
from gosc.schemes import GOSC
from extensions.receiver_diagnostic import EventSimulation,project_view

SEED=14000000
def shape(groups):
    return [(g.kind,[(o.rate,o.bits,o.symbols,o.value,o.n_records) for o in g.options]) for g in groups]

def test_no_receiver_private_field_read_when_masked():
    class Poison:
        def __getattribute__(self,name):raise AssertionError('Forbidden receiver field '+name)
    sim=SimpleNamespace(cfg=Config(),sensor=None,t=0,Lc=np.zeros((32,32)),declared=np.zeros(1024,bool),
        team_pos={j:(j,j) for j in range(6)},team_intent={},agents=[Poison() for _ in range(6)])
    view=project_view(sim,False,False)
    assert all(not a.pending_llr.any() and not a.confirmed_pending for a in view.agents)

def test_masked_public_projection_matches_native_public_values():
    public=EventSimulation(Config(),'gosc',SEED);public._start();public.phase_decide(0)
    projected=EventSimulation(Config().with_(tom_oracle=True),'diag_receiver_public_projection',SEED)
    projected._start();projected.phase_decide(0)
    a=public.agents[0];b=projected.agents[0]
    assert shape(public.scheme.build_groups(a,1.0,public))==shape(projected.scheme.build_groups(b,1.0,projected))

def test_full_projection_matches_original_oracle_values():
    cfg=Config().with_(tom_oracle=True)
    native=EventSimulation(cfg,'gosc',SEED);native._start();native.phase_decide(0)
    projected=EventSimulation(cfg,'diag_receiver_both',SEED);projected._start();projected.phase_decide(0)
    assert shape(native.scheme.build_groups(native.agents[0],1.0,native))==shape(projected.scheme.build_groups(projected.agents[0],1.0,projected))

def test_sensing_coupled_by_global_cell_not_rng_consumption():
    a=EventSimulation(Config(),'gosc',SEED);b=EventSimulation(Config(),'gosc_bits',SEED)
    a.t=b.t=7
    x=set(a.world.sense((10,10),a.sensor,None));y=set(b.world.sense((10,11),b.sensor,None))
    overlap={i*32+j for i in range(8,13) for j in range(9,13)}
    assert x&overlap==y&overlap
    assert a.input_world_sha256==b.input_world_sha256

def test_identical_policy_replay_and_event_prefix():
    a=EventSimulation(Config(),'gosc',SEED+1);b=EventSimulation(Config(),'gosc',SEED+1)
    x=a.run();y=b.run();x.pop('curve');y.pop('curve')
    assert x==y and a.event_field_hashes==b.event_field_hashes
