"""Derive byte-only evidence from retained failed pressure outputs; no replay.

No tokenizer, model, production application or client is imported or invoked.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import tarfile


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def main():
    from scripts.hpc_runs import require_hpc, ROOT
    require_hpc()
    p = argparse.ArgumentParser()
    p.add_argument('--pressure-run', required=True)
    args = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    src = ROOT/'research/sync/runs'/args.pressure_run/'outputs'
    requests = json.loads((src/'synthetic-requests.json').read_bytes())
    payload = json.loads((src/'counter-input.json').read_bytes())
    assert [r['messages'] for r in payload['requests']] == requests
    labels = [(n,c) for n in ('ascii','multibyte','json_escape') for c in ('Full','No-A2A')]
    index = -1
    rows = []
    for req in requests:
        clock = json.loads(req[-1]['content'])
        t = int(clock['turn'][1:])
        if t == 0:
            index += 1
        case, condition = labels[index]
        raw = canonical(req)
        rows.append(dict(case=case, condition=condition, turn=t, serialized_bytes=len(raw),
                         sha256=hashlib.sha256(raw).hexdigest()))
    assert index == 5 and len(rows) == 35
    states = {}
    for case, condition in labels:
        path = src/(case+'-'+condition)/'ledger.jsonl'
        if path.is_file():
            ledger_bytes=path.read_bytes()
        else:
            with tarfile.open(src/'fixture-prefix-raw.tar.gz') as archive:
                ledger_bytes=archive.extractfile(case+'-'+condition+'/ledger.jsonl').read()
        events = [json.loads(line)['event'] for line in ledger_bytes.splitlines()]
        final = [e for e in events if e['kind']=='episode'][-1]
        fences = [e['reason'] for e in events if e['kind']=='v2-fence']
        if final['status'] != 'completed':
            assert (case,condition)==('json_escape','Full') and fences==['IPC_packet_or_cumulative_cap']
        states[case+'-'+condition] = dict(status=final['status'],fences=fences)
    stderr = (src/'counter-stderr.log').read_bytes()
    assert b'runtime: out of memory' in stderr
    report = dict(schema='t3rv2i-retained-byte-pressure-audit-v1',source_run=args.pressure_run,
                  rows=rows,case_states=states,input_path=str(src/'synthetic-requests.json'),
                  requests_sha256=hashlib.sha256((src/'synthetic-requests.json').read_bytes()).hexdigest(),
                  counter_input_sha256=hashlib.sha256((src/'counter-input.json').read_bytes()).hexdigest(),
                  counter_stderr_sha256=hashlib.sha256(stderr).hexdigest(),
                  exact_counter=dict(status='failed_resource_limit',valid_reply=False,attempts=1,
                                     tokens=None,reason='Go runtime allocation failure under inherited 1GiB AS'),
                  byte_pressure_verified=True,model_calls=0,additional_fake_generations=0,
                  additional_helper_calls=0,max_serialized_bytes=max(r['serialized_bytes'] for r in rows))
    out = Path(os.environ['GOSC_OUTPUT_DIR'])/'pressure_summary.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('byte_pressure_verified','max_serialized_bytes','additional_helper_calls')}))


if __name__=='__main__':
    main()
