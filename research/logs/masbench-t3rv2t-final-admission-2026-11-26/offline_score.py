"""Offline result summary for the registered, single-use v2-T run."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal

from scripts.hpc_runs import ROOT, require_hpc, write_json
from extensions.masbench_reasoning.fair_final_v2_scoring import score_episode, paired_summary
from extensions.masbench_reasoning.fair_final_v2_task import evidence_links

RUN = 'hpc-t3rv2i-task-live-final-20261126'
HDD = Path('/hdd/u202520081000097/gosc-t3rv2t-runs') / RUN
SCORE_RUN = RUN + '-offline-score'
HISTORICAL = 'hpc-masbench-t3r-bindings-20261125'


def read(path):
    return json.loads(path.read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    require_hpc()
    signal.alarm(45)
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2,) * 2)
    registered = Path(os.environ['GOSC_RUN_DIR'])
    if registered.name != SCORE_RUN:
        raise ValueError('registered_offline_identity')
    store = ROOT / 'research/sync/runs'
    run = store / RUN
    status = read(run / 'status.json')['status']
    receipt = read(ROOT / f'research/sync/receipts/{RUN}.json')
    if status not in {'completed', 'failed', 'interrupted'} or not receipt['all_outputs_mirrored']:
        raise ValueError('requires_closed_run')
    source = store / HISTORICAL
    source_relative = 'outputs/controlled_read_aid.private.json'
    evidence = (source / source_relative).read_bytes()
    pinned, = (row for row in read(source / 'artifacts.json')['files'] if row['path'] == source_relative)
    if sha(evidence) != pinned['sha256']:
        raise ValueError('historical_reference_drift')
    historical = {row['case']: row for row in json.loads(evidence)['cases']}
    auth = read(HDD / 'authorization.json')
    view_bytes = Path(auth['view_bundle_path']).read_bytes()
    if sha(view_bytes) != auth['view_bundle_sha256'] or len(historical) != 4:
        raise ValueError('reference_or_view_bundle_drift')
    families = json.loads(view_bytes)['families']
    trace = read(ROOT / 'research/logs/masbench-t3r-2026-11-25/episode_trace_index.json')['episodes']
    family_to_case = {episode['family_sha256']: episode['case'] for episode in trace}
    references = {}
    for family in families:
        key = family['family']
        ref = historical[family_to_case[key]]
        if not all(view['question'] == ref['question'] for view in family['views']):
            raise ValueError('reference_question_binding')
        references[key] = ref['gold']
    plan = read(ROOT / 'research/protocols/masbench_t3rv2t_plan_2026-11-26.json')['episodes']
    if set(references) != {row['family'] for row in plan}:
        raise ValueError('reference_plan_binding')
    journal_bytes = (HDD / 'budget/ledger.jsonl').read_bytes()
    if sha(journal_bytes) != receipt['ledger_sha256']:
        raise ValueError('returned_journal_binding')
    ledger_states = {}
    for line in journal_bytes.splitlines():
        event = json.loads(line)['event']
        if event['kind'] == 'episode':
            ledger_states[event['id']] = event['status']
    scored, rows = {}, []
    for row in plan:
        eid, family, condition = (row[name] for name in ('id', 'family', 'condition'))
        path = HDD / f'budget/artifacts/episodes/{eid}.json'
        episode = read(path) if path.is_file() else {}
        episode['started'] = ledger_states.get(eid) in {'started', 'completed', 'failed'}
        score = score_episode(episode, references[family])
        if score['scores']:
            for role in score['scores'].values():
                role.pop('normalized')
        scored.setdefault(family, {})[condition] = score
        links = evidence_links(episode) if condition == 'Full' else []
        rows.append(dict(id=eid, family=family, condition=condition, score=score,
                         source_sha256=sha(path.read_bytes()) if path.is_file() else None,
                         representation_links=links, error=episode.get('error'),
                         wire_totals=episode.get('wire_totals'), accounting=episode.get('accounting')))
    result = paired_summary([row['family'] for row in families], scored)
    positive = {pair['family'] for pair in result['pairs'] if pair['valid_both_conditions']
                and pair['delta'] is not None and pair['delta'] > 0}
    result['positive_valid_families'] = sorted(positive)
    result['positive_full_l1_linked_families'] = sorted({row['family'] for row in rows if row['family'] in positive
                                                       and row['representation_links']})
    result['positive_full_l1_final_citation_candidates'] = sorted({row['family'] for row in rows if row['family'] in positive
                                                                  and any(link['final_cites_source'] for link in row['representation_links'])})
    result['numeric_continue_gate'] = (result['complete_pairs'] and result['Delta_F1'] >= .1
                                       and result['conditions']['Full']['both_correct_families'] >= 2 and len(positive) >= 2)
    result['independent_l2_completed'] = False
    result['scientific_continue_gate'] = False
    result['run_id'] = RUN
    result['reference_source_sha256'] = sha(evidence)
    result['score_script_sha256'] = sha(Path(__file__).read_bytes())
    result['episodes'] = rows
    result['infra'] = {key: receipt[key] for key in ('independent_audit_passed', 'all_outputs_mirrored', 'deadline_met')}
    write_json(Path(os.environ['GOSC_OUTPUT_DIR']) / 'offline_score.json', result)


if __name__ == '__main__':
    main()
