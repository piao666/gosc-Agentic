"""Read-only structural review of one completed four-family diagnostic."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal

from scripts.hpc_runs import ROOT, require_hpc, write_json
from extensions.masbench_reasoning.fair_final_v2 import canonical, parse_output

LIVE = 'hpc-t3rv2i-task-live-final-20261126'
ANALYSIS = LIVE + '-final-attribution'
HDD = Path('/hdd/u202520081000097/gosc-t3rv2t-runs') / LIVE
RECEIPT_SHA = '487aaa0bfec874b170f6ad8cdb496d8cd7b488d9b533524542c7ddc7ec5b6774'
SCORE_SHA = '33fa41f8cadce06d5625b9df10f8556413cd030e5d3f6db9016e3fed84bac263'
SLOTS = {'Alice': (0, 2), 'Bob': (1, 3)}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, expected=None):
    raw = path.read_bytes()
    if expected and sha(raw) != expected:
        raise ValueError(f'source_drift:{path.name}')
    return json.loads(raw)


def need(test, label):
    if not test:
        raise ValueError(label)


def main():
    require_hpc()
    signal.alarm(60)
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2,) * 2)
    registered = Path(os.environ['GOSC_RUN_DIR'])
    need(registered.name == ANALYSIS, 'registered_analysis_identity')
    store = ROOT / 'research/sync/runs'
    original = store / LIVE
    receipt = read(ROOT / f'research/sync/receipts/{LIVE}.json', RECEIPT_SHA)
    need(receipt['all_outputs_mirrored'] and receipt['independent_audit_passed'], 'verified_parent_required')
    need(read(original / 'status.json')['status'] == 'completed', 'parent_not_completed')
    manifest = read(original / 'manifest.json')
    snapshot = read(original / 'source_snapshot.json', manifest['source_manifest_sha256'])
    source = {row['path']: row['remote_sha256'] for row in snapshot['files']}
    parser = 'extensions/masbench_reasoning/fair_final_v2.py'
    need(sha((ROOT / parser).read_bytes()) == source[parser], 'frozen_parser_source_drift')
    index = read(original / 'outputs/hdd_inventory.json', receipt['live_inventory_sha256'])
    files = {row['path']: row for row in index['files']}

    def artifact(rel):
        ref = files['budget/artifacts/' + rel]
        return read(HDD / ref['path'], ref['sha256'])

    previous = read(store / (LIVE + '-offline-score') / 'outputs/offline_score.json', SCORE_SHA)
    score = {row['id']: row for row in previous['episodes']}
    ids = [(f'f{i}-{condition}', condition) for i in range(1, 5) for condition in ('Full', 'No-A2A')]
    terminal_rows, chains = [], []
    checked = set()
    exchange = Counter()
    for eid, condition in ids:
        episode = artifact(f'episodes/{eid}.json')
        need(episode['id'] == eid and episode['condition'] == condition and episode['completed'], 'episode_identity')
        need(score[eid]['source_sha256'] == files[f'budget/artifacts/episodes/{eid}.json']['sha256'], 'score_episode_source')
        slots = {slot['turn']: slot for slot in episode['slots']}
        need(set(slots) == set(range(6)), 'slot_set')

        def originals(turn):
            slot = slots[turn]
            prefix = f'{eid}/t{turn}/client-'
            completion = artifact(prefix + 'completed.json')['data']
            request = artifact(prefix + 'request_ready.json')['data']
            need(slot['status'] == 'returned' and slot['request'] == request['messages']
                 and slot['request_sha256'] == request['request_sha256'] == sha(canonical(request['messages']).encode())
                 and slot['raw'] == completion['response']['choices'][0]['message']['content'], 'client_source_mismatch')
            checked.add((eid, turn))
            return slot

        delivered = {d['source']['turn']: d for d in episode.get('messages', []) if d['delivered']}
        need(not delivered or condition == 'Full', 'wrong_delivery_condition')
        for turn, role in ((4, 'Alice'), (5, 'Bob')):
            slot = originals(turn)
            received = sorted(episode['received_sources'][turn % 2])
            observed = sorted(f't{key}' for key, d in delivered.items() if d['source']['sender'] != role)
            need(received == observed and slot['speaker'] == role, 'received_set_mismatch')
            frozen = parse_output(slot['raw'], role, 'local_final', received)
            need(frozen == slot['parsed'] == episode['finals'][role], 'frozen_parse_mismatch')
            official = score[eid]['score']['scores'][role]
            need(official['valid_format'] == frozen['valid_format'] and official['valid_answer'] == frozen['valid_answer']
                 and official['reason'] == frozen['reason'] and official['EM'] == official['F1'] == 0, 'official_terminal_mismatch')
            raw = frozen['text']
            block = re.search(r'^<E>([^<>\n]*)</E>$', raw, re.M)
            need(block is not None, 'missing_E_block')
            e_text = block[1]
            declared = sorted(re.findall(r't[0-3]', e_text))
            comma_spaces = bool(re.search(r', +', e_text))
            variant = raw[:block.start(1)] + re.sub(r', +', ',', e_text) + raw[block.end(1):]
            punctuation_only = parse_output(variant, role, 'local_final', received)
            terminal_rows.append(dict(episode=eid, condition=condition, role=role, turn=turn,
                                      raw_sha256=frozen['raw_sha256'], response_sha256=slot['client_audit']['response_sha256'],
                                      request_sha256=slot['request_sha256'], reason=frozen['reason'], detail=frozen.get('detail'),
                                      explicit_block='A' if re.search(r'^<A>[^<>\n]+</A>$', raw, re.M) else 'U',
                                      received=received, declared=declared,
                                      declared_self=sorted(set(declared) & {f't{n}' for n in SLOTS[role]}),
                                      declared_unreceived=sorted(set(declared) - set(received)), comma_space=comma_spaces,
                                      comma_space_only_pass=bool(comma_spaces and not frozen['valid_format'] and punctuation_only['valid_answer'])))
        for turn, delivery in delivered.items():
            send, nxt = originals(turn), originals(turn + 1)
            receiver = nxt['speaker']
            final = slots[4 if receiver == 'Alice' else 5]
            raw_body = bytes.fromhex(delivery['body']['utf8_or_wire_hex']).decode()
            source_event = delivery['source']
            peer = {'role': 'user', 'content': canonical(dict(kind='PEER_MESSAGE', sender=send['speaker'], turn=f't{turn}', text=raw_body))}
            need(raw_body == send['parsed']['text'] and sha(raw_body.encode()) == source_event['payload_sha256']
                 and send['request_sha256'] == source_event['request_sha256']
                 and send['client_audit']['response_sha256'] == source_event['response_sha256'], 'payload_origin')
            need(nxt['request'].count(peer) == final['request'].count(peer) == 1, 'L1_visibility')
            original_link, = (row for row in score[eid]['representation_links'] if row['turn'] == turn)
            need(all(original_link[key] == value for key, value in
                     dict(receiver=receiver, payload_sha256=source_event['payload_sha256'], next_request_sha256=nxt['request_sha256'],
                          final_request_sha256=final['request_sha256']).items()), 'L1_index_mismatch')
            chains.append(dict(episode=eid, sender=send['speaker'], receiver=receiver, turn=turn, next_turn=turn + 1,
                               final_turn=final['turn'], payload_sha256=source_event['payload_sha256'],
                               next_request_sha256=nxt['request_sha256'], final_request_sha256=final['request_sha256'],
                               next_reply_sha256=nxt['parsed']['raw_sha256'], next_reply_reason=nxt['parsed']['reason'],
                               final_raw_sha256=final['parsed']['raw_sha256'], final_cites_source=original_link['final_cites_source']))
        for turn in range(4):
            exchange[(condition, slots[turn]['parsed']['reason'])] += 1
    need(len(terminal_rows) == 16 and len(chains) == 8, 'analysis_denominator')
    paired_byte_equal = [f'f{i}/{role}' for i in range(1, 5) for role in SLOTS
                         if len({row['raw_sha256'] for row in terminal_rows if row['episode'].startswith(f'f{i}-') and row['role'] == role}) == 1]
    counts = dict(reason=Counter(row['reason'] for row in terminal_rows), detail=Counter(row['detail'] or 'none' for row in terminal_rows),
                  explicit_block=Counter(row['explicit_block'] for row in terminal_rows), declared_self=sum(bool(row['declared_self']) for row in terminal_rows),
                  declared_unreceived=sum(bool(row['declared_unreceived']) for row in terminal_rows), comma_space=sum(row['comma_space'] for row in terminal_rows),
                  comma_space_only_pass=sum(row['comma_space_only_pass'] for row in terminal_rows))
    result = dict(run_id=ANALYSIS, reviewed_run=LIVE, source_receipt_sha256=RECEIPT_SHA, official_score_sha256=SCORE_SHA,
                  script_sha256=sha(Path(__file__).read_bytes()), parser_sha256=source[parser],
                  model_calls=0, client_slots_crosschecked=len(checked), counts=counts, exact_same_final_across_conditions=paired_byte_equal,
                  exchange_counts={c: {reason: n for (name, reason), n in exchange.items() if name == c} for c in ('Full', 'No-A2A')},
                  official_metrics=dict(Delta_F1=previous['Delta_F1'], scientific_continue_gate=previous['scientific_continue_gate']),
                  terminals=terminal_rows, l1=chains)
    write_json(Path(os.environ['GOSC_OUTPUT_DIR']) / 'final_attribution.json', result)
    print(json.dumps(dict(counts=counts, L1=len(chains), client_slots=len(checked), model_calls=0)))


if __name__ == '__main__':
    main()
