import pytest
from gosc.config import Config
from gosc.belief import Obs
from extensions.paid_receiver_service import PaidReceiverService,ServiceConfig
from extensions.paired_paid_simulation import PairedPaidSimulation
from extensions.sync_cost_diagnostic import ReviewSimulation,ServiceTrace


@pytest.mark.parametrize('pose',[False,True])
def test_observer_keeps_complete_result_and_random_fields_exact(pose):
    args=(Config(max_steps=8,energy_price=0.),17000000,ServiceConfig(100,2000,1.,.001,.001))
    bare=PairedPaidSimulation(*args,use_pose=pose)
    reviewed=ReviewSimulation(*args,use_pose=pose)
    assert reviewed.run()==bare.run()
    assert reviewed.trace.result()['ledger_identities']=='passed'
    if pose:
        assert reviewed.decisions
        for row in reviewed.decisions:
            if not any(p['changed'] for p in row['peers']):
                assert not row['exact_value_changed'] and not row['selection_changed']


def test_edge_accepted_task_retries_while_ack_is_still_in_cpu_queue():
    service=PaidReceiverService({0:(0,0)},32,ServiceConfig(100,1000,1.,.001,.001),replay_tasks=True)
    trace=ServiceTrace(service);service.submit_task(0,b'foo',0,rate=2.)
    for t in range(4):service.tick(t)
    assert [x['category'] for x in trace.ul]==['task_first','task_retry_after_edge']
    assert trace.feedback_delays[0]['delay']==2
    assert trace.result()['cpu']['task_ready']['ready_minus_submit_slots']==1


def test_history_replay_is_separate_from_initial_data_and_partial_dl_is_censored():
    service=PaidReceiverService({0:(0,0)},32,ServiceConfig(100,20,1.,0.,0.,refresh=2),replay_tasks=True)
    trace=ServiceTrace(service);service.submit_task(0,b'x'*12,0,rate=2.)
    for t in range(4):service.tick(t)
    out=trace.result();kinds={x['kind'] for x in out['dl_frames']}
    assert 'task_initial' in kinds and 'task_replay' in kinds
    assert any(x['served']<x['need'] and x['completed'] is None for x in out['dl_frames'])


def test_shadow_uses_same_records_and_does_not_mutate_private_pending():
    cfg=Config(max_steps=2);s=ReviewSimulation(cfg,17000000,ServiceConfig(100,2000,1.,0.,0.),use_pose=True)
    s.phase_decide(0);a=s.agents[0];before=list(a.pending_records)
    s.select(a,1.,s.service.knowledge.value_view(s.local[0],0,0))
    assert a.pending_records==before and not s.decisions[-1]['selection_changed']


def test_same_slot_other_snapshot_does_not_repeat_unchanged_cache_entry_count():
    from extensions.receiver_summary_audit import encode
    from extensions.receiver_transport_replay import batch
    service=PaidReceiverService({0:(0,0),1:(1,1)},32,ServiceConfig(100,1000,1.,0.,0.))
    trace=ServiceTrace(service)
    first=batch([encode(0,0,0,0)]);second=batch([encode(1,0,0,33)])
    service._receive('summary_snapshot',0,first,2)
    service._receive('summary_snapshot',0,second,2)
    assert trace.receipts['summary_new_generation']==2
    assert trace.receipts['summary_same_generation']==0
    service._receive('summary_snapshot',0,second,2)
    assert trace.receipts['summary_same_generation']==1
