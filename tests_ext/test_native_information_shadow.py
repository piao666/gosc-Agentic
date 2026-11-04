"""Unexecuted contracts; run only on HPC via hpc_runs after authorization."""
import copy
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from gosc.belief import Obs, SensorModel
from gosc.channel import Channel
from gosc.config import Config
from gosc.schemes import GOSC
from extensions.causal_paid_service import CausalPolicy
from extensions.paid_receiver_service import ServiceConfig
from extensions.native_information_value import (NativeInformationError, NativeValueContext,
    NativeValueWireGOSC, checked_records, evidence_values, weights)
from extensions.native_information_observer import (NativeShadowHost, OwnEvidenceLedger,
    verify_checkpoint, scientific_result, digest)
from extensions.native_information_shadow import (analyze_snapshot, structural,
    validate_snapshot, benchmark_snapshot)
from scripts.audit_native_information_shadow import audit_records, scalar_reference
from scripts import repro_native_information_shadow as runner


def context(**kw):
    values = dict(sender=0, t=2, grid=4, n_agents=2, radius=0, llr_pos=1., llr_neg=-1.,
        Lc=np.zeros((4, 4)), declared=np.zeros(16, dtype=bool), team_pos={}, team_intent={})
    values.update(kw)
    return NativeValueContext(**values)


def make_host(capture, dl_capacity=2000):
    cfg = Config(grid=4, n_agents=2, n_victims=1, sense_radius=0, max_steps=4, energy_price=1e-4)
    service = ServiceConfig(100, dl_capacity, 1., .001, .001)
    return NativeShadowHost(cfg, 27000000, service, CausalPolicy(), capture=capture)


def snapshot_fixture():
    host = make_host(True)
    host.run()
    assert host.snapshot_rows, 'Fixture must reach an actual EVID admission'
    return host.cfg, host.snapshot_rows[0]


def test_native_g0_matches_original_tv_without_private_double_counting():
    c = context()
    records = [Obs(0, 0, (0, 0), (0,)), Obs(1, 0, (1, 1), ())]
    cfg = Config(grid=4, n_agents=2, sense_radius=0)
    sensor = SensorModel(cfg.p_detect, cfg.p_false_alarm, 0, 4)
    c = replace(c, llr_pos=sensor.llr_pos, llr_neg=sensor.llr_neg)
    view = SimpleNamespace(Lc=c.Lc, declared=c.declared, sensor=sensor, t=c.t)
    baseline = GOSC(cfg, Channel(cfg, (0, 0)), voi_mode='tv').evidence_voi(view, records, [1, 2])
    assert evidence_values(c, records, [1, 2], 'g0') == baseline
    # The pure proxy has no private/pending/edge-state accessor at all.
    assert not hasattr(c, 'pending_llr') and not hasattr(c, 'agents')


def test_native_context_copies_inputs_and_backing_storage_is_immutable():
    source = np.zeros((4, 4))
    poses = {1: (0, 0)}
    c = context(Lc=source, team_pos=poses)
    source[0, 0] = 12
    poses[1] = (3, 3)
    assert c.Lc[0, 0] == 0 and c.team_pos[1] == (0, 0)
    with pytest.raises(ValueError):
        c.Lc.setflags(write=True)
    with pytest.raises(TypeError):
        c.team_pos[1] = (1, 1)


@pytest.mark.parametrize('changes', [dict(team_intent={1: True}), dict(team_intent={1: 16}),
    dict(team_pos={1: (4, 0)}), dict(Lc=np.full((4, 4), np.inf)), dict(t=True), dict(sender=2)])
def test_native_context_rejects_illegal_or_nonfinite_fields(changes):
    with pytest.raises(ValueError):
        context(**changes)


def test_native_context_json_rejects_hidden_fields_and_peer_aliases():
    row = context().to_json()
    row['world'] = {'victims': [0]}
    with pytest.raises(ValueError):
        NativeValueContext.from_json(row)
    row.pop('world')
    row['team_intent'] = {'01': 0}
    with pytest.raises(ValueError):
        NativeValueContext.from_json(row)


def test_native_weights_intent_pose_uniform_fallback_and_bounds():
    intent = context(team_intent={1: 0}, team_pos={1: (3, 3)})
    w, anchors = weights(intent)
    assert anchors[0]['source'] == 'native_intent' and w[0, 0] > w[3, 3]
    pose, anchors = weights(context(team_pos={1: (3, 3)}))
    assert anchors[0]['source'] == 'native_pose' and pose[3, 3] > pose[0, 0]
    uniform, anchors = weights(context())
    np.testing.assert_array_equal(uniform, np.ones((4, 4)))
    assert anchors[0]['source'] == 'uniform_missing'
    assert .5 <= w.min() <= w.max() <= 2.
    assert abs(w.mean()-1) < 1e-14


def test_native_shuffled_weights_preserve_live_histogram_and_declared_mask():
    declared = np.zeros(16, dtype=bool)
    declared[0] = True
    c = context(team_intent={1: 0}, declared=declared)
    a, b = weights(c)[0], weights(c, True)[0]
    np.testing.assert_array_equal(np.sort(a[~declared.reshape(4, 4)]), np.sort(b[~declared.reshape(4, 4)]))
    assert a[0, 0] == b[0, 0] == 0


def test_native_prefix_cancellation_is_not_sum_of_absolute_record_changes():
    c = context()
    records = [Obs(0, 0, (0, 0), (0,)), Obs(1, 0, (0, 0), ())]
    values = evidence_values(c, records, [2, 1, 1])
    assert values[1] > 0 and values[2] == 0


def test_native_no_live_cells_empty_prefixes_and_proxy_bounds():
    records = [Obs(0, 0, (0, 0), (0,))]
    assert evidence_values(context(), [], []) == {}
    assert evidence_values(context(declared=np.ones(16, dtype=bool)), records, [1], 'g1') == {1: 0.}
    c = context(team_intent={1: 0})
    a, b = evidence_values(c, records, [1]), evidence_values(c, records, [1], 'g1')
    assert a[1]/2 <= b[1] <= 2*a[1]


def test_native_saturation_remains_zero_and_arithmetic_overflow_is_explicit():
    rec = Obs(0, 0, (0, 0), (0,))
    assert evidence_values(context(Lc=np.full((4, 4), 1000.)), [rec], [1]) == {1: 0.}
    huge = context(Lc=np.full((4, 4), np.finfo(np.float64).max), llr_pos=1e308, llr_neg=-1e308)
    with pytest.raises(NativeInformationError):
        evidence_values(huge, [rec], [1])


@pytest.mark.parametrize('records', [[Obs(3, 0, (0, 0), ())],
    [Obs(0, 1, (0, 0), ())], [Obs(0, 0, (0, 0), (1,))],
    [Obs(0, 0, (0, 0), (0, 0))], [Obs(0, 0, (0, 0), ()), Obs(0, 0, (0, 0), ())]])
def test_native_evidence_rejects_future_private_and_duplicate_identities(records):
    with pytest.raises(ValueError):
        checked_records(context(), records)


def test_native_local_identity_ledger_rejects_received_evidence_and_missing_boundary():
    c, rec = context(), Obs(0, 0, (0, 0), ())
    ledger = OwnEvidenceLedger(0)
    with pytest.raises(ValueError):
        ledger.checkpoint(c, [rec], ())
    ledger.register(c, [rec])
    with pytest.raises(ValueError):
        ledger.checkpoint(c, [rec], [(0, 0)])
    ledger.receive(7, [rec])
    ledger.receive(7, [rec])  # Same transport replay is idempotent.
    with pytest.raises(ValueError):
        ledger.checkpoint(c, [rec], ())
    checkpoint = ledger.checkpoint(c, [], ())
    verify_checkpoint(c, [], checkpoint)


def test_native_local_identity_ledger_rejects_conflicting_or_unknown_receipt():
    c, rec = context(), Obs(0, 0, (0, 0), ())
    ledger = OwnEvidenceLedger(0)
    with pytest.raises(ValueError):
        ledger.receive(0, [rec])
    ledger.register(c, [rec])
    with pytest.raises(ValueError):
        ledger.receive(0, [Obs(0, 0, (1, 1), ())])


def test_native_shadow_host_preserves_scientific_result():
    plain, observed = make_host(False), make_host(True)
    a, b = plain.run(), observed.run()
    assert scientific_result(a) == scientific_result(b)
    assert plain.service.events == observed.service.events
    assert plain.event_field_hashes == observed.event_field_hashes
    assert all(v <= 8 for v in observed.capture_counts.values())
    assert observed.snapshot_rows and not any(observed.service.knowledge.cache.values())
    assert observed.service.cost['ul_summary_bytes'] == 0


def test_native_zero_dl_cannot_provide_free_local_receipts():
    host = make_host(True, dl_capacity=0)
    initial = [v.Lc.copy() for v in host.local]
    host.run()
    assert host._outstanding and not host._local_seen
    assert not any(l.received for l in host.ledgers.values())
    for local, before in zip(host.local, initial):
        np.testing.assert_array_equal(local.Lc, before)


def test_native_wire_hook_preserves_menu_non_evid_and_exact_wire_success():
    from extensions.native_information_shadow import restore
    cfg, envelope = snapshot_fixture()
    _, _, agent, view, channel = restore(envelope['snapshot'], cfg)
    from extensions.native_task_wire import WireGOSC
    original = WireGOSC(cfg, channel, 'tom').build_groups(agent, envelope['snapshot']['known'], view)
    for method in ('g0', 'g1'):
        candidate = NativeValueWireGOSC(cfg, channel, method).build_groups(agent, envelope['snapshot']['known'], view)
        assert structural(original) == structural(candidate)
        assert all(a.value.hex() == b.value.hex() for x, y in zip(original, candidate)
                   if x.kind != 'EVID' for a, b in zip(x.options, y.options))


def test_native_shadow_independent_scalar_reference_and_one_prefix_degeneracy():
    cfg, envelope = snapshot_fixture()
    prices = [0., 1e-4]
    analysis = analyze_snapshot(envelope, cfg, prices)
    expected = scalar_reference(envelope['snapshot'])
    for method, values in expected.items():
        for n, value in values.items():
            assert analysis['raw'][method][n] == pytest.approx(value, abs=1e-12)
    if len(analysis['prefixes']) == 1:
        assert not analysis['nonproportional']
        assert not any(r['content_witness'] for r in analysis['selections'])


def test_native_shadow_audit_rejects_tampered_score():
    cfg, envelope = snapshot_fixture()
    analysis = analyze_snapshot(envelope, cfg, [0., 1e-4])
    sources = [dict(world=27000000, input=envelope)]
    results = [dict(world=27000000, analysis=analysis)]
    assert audit_records(sources, results, cfg, [0., 1e-4])['status'] == 'passed'
    changed = copy.deepcopy(results)
    first = next(iter(changed[0]['analysis']['raw']['g1']))
    changed[0]['analysis']['raw']['g1'][first] += .1
    with pytest.raises(ValueError):
        audit_records(sources, changed, cfg, [0., 1e-4])


def test_native_shadow_rejects_source_hash_and_payload_tampering():
    cfg, envelope = snapshot_fixture()
    changed = copy.deepcopy(envelope)
    changed['snapshot']['context']['Lc'][0][0] += 1
    with pytest.raises(ValueError):
        validate_snapshot(changed, cfg)
    changed = copy.deepcopy(envelope)
    changed['snapshot']['payloads'][0][0] = '00'
    changed['snapshot_sha256'] = digest(changed['snapshot'])
    with pytest.raises(ValueError):
        validate_snapshot(changed, cfg)


def test_native_shadow_timing_is_separate_and_cannot_mutate_snapshot():
    cfg, envelope = snapshot_fixture()
    before = digest(envelope)
    timing = benchmark_snapshot(envelope, cfg)
    assert len(timing['rows']) == 12 and digest(envelope) == before
    assert all(r['total_process_ns'] >= 0 for r in timing['rows'])


def test_native_shadow_execution_requires_explicit_authorization(monkeypatch, tmp_path):
    # Isolate the authorization condition; source/contract gates have separate tests.
    frozen = dict(plan={}, config_sha256='d', source_sha256={}, contracts_run='research/sync/runs/contract',
        contract_status_sha256='d', contract_snapshot_sha256='d', pytest_xml_sha256='d')
    monkeypatch.setattr(runner, 'validate_plan', lambda _: None)
    monkeypatch.setattr(runner, 'source_hashes', lambda: {})
    monkeypatch.setattr(runner, 'sha', lambda _: 'd')
    monkeypatch.setattr(runner, 'read', lambda path: frozen if str(path) == 'frozen' else {'approved': False})
    with pytest.raises(RuntimeError, match='Separate explicit human authorization'):
        runner.check_authorization('frozen', 'approval')


def test_native_shadow_rejects_source_changes_before_any_authorized_work(monkeypatch):
    frozen = dict(plan={}, config_sha256='d', source_sha256={'old': 'hash'})
    monkeypatch.setattr(runner, 'validate_plan', lambda _: None)
    monkeypatch.setattr(runner, 'source_hashes', lambda: {'new': 'hash'})
    monkeypatch.setattr(runner, 'sha', lambda _: 'd')
    monkeypatch.setattr(runner, 'read', lambda _: frozen)
    with pytest.raises(RuntimeError, match='Frozen source changed'):
        runner.check_authorization('frozen', 'approval')


def test_native_shadow_writer_never_overwrites_or_exceeds_cap(tmp_path):
    runner.save_new(tmp_path, 'one.json', {'status': 'first'})
    with pytest.raises(FileExistsError):
        runner.save_new(tmp_path, 'one.json', {'status': 'overwrite'})
    with pytest.raises(RuntimeError, match='Output cap'):
        runner.save_new(tmp_path, 'too_large.json', {'data': 'x'*100}, limit=100)
    assert not (tmp_path/'too_large.json').exists()


def armed_own_evidence_bookkeeping_fixture():
    """Synthetic adapter-state fixture, not a claim about transport arrival time."""
    from gosc.messages import Packet
    from extensions.native_task_wire import encode_packet
    host = make_host(True)
    host._start()
    host.phase_decide(0)
    agent = host.agents[0]
    assert agent.pending_records
    rec = agent.pending_records[0]
    packet = Packet('EVID', 0, 0, 0, records=[rec])
    host._tx[0, 77] = packet
    host._outstanding.add((0, 77))
    return host, agent, rec, encode_packet(packet, host.cfg)


def test_native_own_broadcast_before_ack_blocks_overlap_and_duplicate_receipt():
    host, agent, rec, payload = armed_own_evidence_bookkeeping_fixture()
    host._local_packet(0, 0, 77, payload)
    local_after = host.local[0].Lc.copy()
    private_after = agent.pending_llr.copy()
    host._local_packet(0, 0, 77, payload)
    np.testing.assert_array_equal(host.local[0].Lc, local_after)
    np.testing.assert_array_equal(agent.pending_llr, private_after)
    assert rec in agent.pending_records
    ctx = NativeValueContext.from_local(host.view(agent), 0)
    with pytest.raises(NativeInformationError, match='admission boundary'):
        host.ledgers[0].checkpoint(ctx, agent.pending_records, [(0, 77)])
    with pytest.raises(NativeInformationError, match='unknown/overlap'):
        host.ledgers[0].checkpoint(ctx, agent.pending_records, ())
    # Exercise the unchanged adapter's ACK-removal path with explicit state input.
    host.service.task_acks.append((0, 77))
    host.phase_communicate(0)
    assert rec not in agent.pending_records and (0, 77) not in host._outstanding
    host.ledgers[0].checkpoint(NativeValueContext.from_local(host.view(agent), 0),
                               agent.pending_records, ())


def test_native_ack_before_own_broadcast_does_not_fuse_local_lc_or_clear_private_early():
    host, agent, rec, payload = armed_own_evidence_bookkeeping_fixture()
    local_before, private_before = host.local[0].Lc.copy(), agent.pending_llr.copy()
    host.service.task_acks.append((0, 77))
    host.phase_communicate(0)
    assert rec not in agent.pending_records
    np.testing.assert_array_equal(host.local[0].Lc, local_before)
    np.testing.assert_array_equal(agent.pending_llr, private_before)
    assert not host.ledgers[0].received
    host._local_packet(0, 0, 77, payload)
    assert not np.array_equal(host.local[0].Lc, local_before)
    np.testing.assert_allclose(agent.pending_llr, np.zeros_like(private_before), atol=1e-15)
    assert host.ledgers[0].received == {rec.t: 77}


def test_native_audit_rejects_simultaneous_input_output_omission():
    cfg = Config(grid=4, n_agents=2, max_steps=4)
    host_records = [dict(world=27000000, plain_result={}, observed_result={},
        observation_neutral=True, plain_event_sha256='same', observed_event_sha256='same',
        plain_state_sha256='same', observed_state_sha256='same',
        entries=[dict(t=0, sender=0, has_evid=True)])]
    with pytest.raises(ValueError, match='first-eight capture coverage'):
        audit_records([], [], cfg, [0.], host_records)
