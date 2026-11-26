"""Focused admission contracts; existing C/D and task suites stay separate."""
import copy
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments_ext.masbench_t3rv2t_closeout import restore_archive, stream_archive
from experiments_ext.masbench_t3rv2t_live_audit import digest, inventory, journal, sha
from extensions.masbench_reasoning.fair_final_v2 import canonical, sha as app_sha
from extensions.masbench_reasoning.fair_final_v2_task import evidence_links, scientific_gate


def campaign():
    plan, results = [], []
    cleanup, requests, states = {}, {}, {}
    text = 'Alice: MESSAGE\n<R>The parcel is blue.</R>'
    peer = dict(role='user', content=canonical(dict(kind='PEER_MESSAGE', sender='Alice', turn='t0', text=text)))
    for family in 'abcd':
        for condition in ('Full', 'No-A2A'):
            eid = family + condition
            plan.append(dict(id=eid, family=family, condition=condition))
            slots = []
            for turn in range(6):
                request = [peer] if condition == 'Full' and turn in (1, 5) else []
                slots.append(dict(turn=turn, status='returned', speaker='Alice' if turn % 2 == 0 else 'Bob',
                                  stage='exchange' if turn < 4 else 'local_final', request=request,
                                  request_sha256=app_sha(canonical(request)), client_audit={'response_sha256': 'r'}))
                requests[f'{eid}/t{turn}'] = dict(status='completed', observed_usage={})
            slots[0]['parsed'] = dict(text=text, valid_format=True)
            source = dict(turn=0, sender='Alice', payload_sha256=app_sha(text),
                          request_sha256=slots[0]['request_sha256'], response_sha256='r')
            messages = [dict(delivered=True, body=text.encode(), source=source)] if condition == 'Full' else []
            results.append(dict(id=eid, condition=condition, completed=True, slots=slots, messages=messages,
                                finals={'Bob': dict(valid_answer=True, provenance=['t0'])}, accounting={'scope': 'task_real: fixture'}))
            states[eid] = 'completed'
            cleanup[eid] = 'verified'
    ledger = SimpleNamespace(fixture=False, state=dict(fenced=False, episodes=states, requests=requests, cleanup=cleanup))
    paired = dict(complete_pairs=True, N_families=4, Delta_F1=.2, conditions={'Full': {'both_correct_families': 2}},
                  pairs=[dict(family=f, delta=.4 if f in 'ab' else 0, valid_both_conditions=True) for f in 'abcd'])
    infrastructure = dict.fromkeys(('runtime_bound', 'resource_monitor_passed', 'rollback_verified',
                                    'independent_audit_passed', 'all_outputs_mirrored', 'deadline_met'), True)
    return plan, results, ledger, paired, infrastructure


def review(episode, family):
    row, = evidence_links(episode)
    return dict(row, family=family, episode_id=episode['id'], supports_final=True, rationale='Fixture confirms receiver used the color.')


@pytest.mark.parametrize('failure', [None, 'nonpositive', 'wrong_final', 'visibility', 'duplicate', 'late'])
def test_gate_binds_review_to_positive_full_evidence(failure):
    plan, results, ledger, paired, infrastructure = campaign()
    candidate = review(results[0], 'a')
    if failure == 'nonpositive':
        candidate = review(results[4], 'c')
    elif failure == 'wrong_final':
        candidate['final_request_sha256'] = 'wrong'
    elif failure == 'visibility':
        results[0]['slots'][1]['request'] = []
    elif failure == 'duplicate':
        paired['pairs'][1] = copy.deepcopy(paired['pairs'][0])
    elif failure == 'late':
        infrastructure['deadline_met'] = False
    result = scientific_gate(plan, results, ledger, paired, [candidate], infrastructure=infrastructure)
    assert result['passed'] is (failure is None)


def test_independent_inventory_and_journal_fail_closed(tmp_path):
    file = tmp_path / 'ledger.jsonl'
    row = dict(seq=0, previous='0'*64, event={'kind': 'init'})
    file.write_text(json.dumps(dict(row, hash=digest(row)))+'\n')
    listing = [dict(path=file.name, bytes=file.stat().st_size, sha256=sha(file))]
    assert inventory(tmp_path, listing) == listing[0]['bytes']
    assert list(journal(file)) == [row['event']]
    file.write_text(json.dumps(dict(row, hash='0'*64))+'\n')
    with pytest.raises(ValueError, match='HDD_file_binding'):
        inventory(tmp_path, listing)
    with pytest.raises(ValueError, match='journal_chain'):
        list(journal(file))


def test_scoped_transfer_checks_complete_members_and_bytes(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'partial-failure.json').write_bytes(b'failed episode retained')
    out = io.BytesIO()
    stream_archive([(source, 'hdd')], out)
    raw = out.getvalue()
    archive = tmp_path / 'evidence.tar'
    archive.write_bytes(raw)
    assert len(restore_archive(archive, tmp_path / 'mirror')) == 1
    archive.write_bytes(raw.replace(b'failed episode retained', b'failed episode modified'))
    with pytest.raises(ValueError, match='transfer_file_sha'):
        restore_archive(archive, tmp_path / 'broken')
