"""T2 offline context sizing on the frozen development prompts and synthetic histories."""
import hashlib
import json
import os
from pathlib import Path
import resource
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from experiments_ext.masbench_t1a_contract import deny_network
from extensions.masbench_reasoning.application import LocalAgent, private_view, run_fixed
from extensions.masbench_reasoning.execution_safety import canonical
from extensions.masbench_reasoning.live_driver import HELPER_SHA, MANIFEST, MODEL_BLOB, SYSTEM, TEMPLATE
from extensions.masbench_reasoning.registry import digest
from extensions.masbench_reasoning.wire import ContractTransport
from hpc_runs import require_hpc, write_json

HELPER = Path('/tmp/gosc-hpc-masbench-context-build-v3-20261116/context-counter')
MODELS = ROOT.parents[1] / 'models/ollama-gosc'
ARCHIVE = ROOT / 'research/artifacts/native-masbench-20261104'
REGISTRY_SHA = '94b20ff4e199f8e6dc9eeeae8b0a8f91767c00576906f5589387a1266f4a4f1a'
OUTPUT_CAP = 512
WINDOWS = (1024, 2048, 4096, 8192, 16384, 32768)
NAMES = ('Alice', 'Bob')
FAMILIES = ('base', 'protocol')


def sha(body):
    return hashlib.sha256(body).hexdigest()


def check_pins():
    def verified(path, expected):
        assert path.is_file() and sha(path.read_bytes()) == expected, path.name

    verified(HELPER, HELPER_SHA)
    path = MODELS / 'manifests/registry.ollama.ai/library/qwen2.5/7b'
    verified(path, MANIFEST)
    for value in (TEMPLATE, SYSTEM):
        verified(MODELS / 'blobs' / f'sha256-{value}', value)
    manifest = json.loads(path.read_bytes())
    layer, = [item for item in manifest['layers'] if item['mediaType'] == 'application/vnd.ollama.image.model']
    assert layer['digest'].replace(':', '-') == MODEL_BLOB
    assert (MODELS / 'blobs' / MODEL_BLOB).stat().st_size == layer['size']


def count(requests=(), texts=()):
    payload = canonical({'model_path': str(MODELS / 'blobs' / MODEL_BLOB),
                         'template_path': str(MODELS / 'blobs' / f'sha256-{TEMPLATE}'),
                         'template_sha256': TEMPLATE, 'requests': [{'messages': m} for m in requests], 'texts': texts})
    process = subprocess.run([HELPER], input=payload, capture_output=True, timeout=40)
    if process.returncode or len(process.stdout) > 16 * 1024**2:
        raise RuntimeError(f'Offline counter failed or exceeded output budget, exit={process.returncode}')
    reply = json.loads(process.stdout)
    assert reply['vocab_only'] is True and reply['tensor_context_created'] is False
    assert reply['template_sha256'] == TEMPLATE and reply['input_sha256'] == sha(payload)
    assert reply['add_special'] is False and reply['parse_special'] is True
    assert len(reply['requests']) == len(requests) and len(reply['texts']) == len(texts)
    for row in reply['requests'] + reply['texts']:
        rendered = row['rendered'].encode()
        assert sha(rendered) == row['rendered_sha256'] and len(rendered) == row['utf8_bytes']
        assert len(row['token_ids']) == row['token_count']
        assert sha(canonical(row['token_ids'])) == row['token_ids_json_sha256']
    return reply


def development_inputs():
    registry = json.loads((ROOT / 'research/sync/runs/hpc-masbench-registry-v2-20261103'
                          / 'outputs/development_registry_v1.json').read_bytes())
    assert registry.pop('registry_content_sha256') == REGISTRY_SHA == digest(registry)
    raw = (ROOT / 'research/sync/runs/hpc-masbench-data-audit-v2-20261103/outputs/reasoning.json').read_bytes()
    assert sha(raw) == registry['data_sha256']
    path = ROOT / 'research/logs/masbench-adapter-contract-2026-11-03/reference/Reasoning/src/prompts.py'
    raw_template = path.read_bytes()
    blob = b'blob ' + str(len(raw_template)).encode() + b'\0' + raw_template
    assert hashlib.sha1(blob).hexdigest() == '4a39061fe2840f177f4169223d188448469e2ada'
    prompts = runpy.run_path(str(path))
    body = json.loads(raw)
    return registry['selected'], body, dict(zip(FAMILIES, (prompts['QA_INFO_EXCHANGE_PROMPT'],
                                                       prompts['QA_INFO_EXCHANGE_PROMPT_PROTOCOL'])))


def long_responses():
    cases = [[f'{NAMES[turn % 2]}: MESSAGE\n' + '\n'.join(
        f'<R>Parcel {turn+1}-{n+1} is filed in the sample archive.</R>' for n in range(length))
              for length in range(16, 36, 2)] for turn in range(6)]
    rows = count(texts=[text for group in cases for text in group])['texts']
    width = len(cases[0])
    responses, sizes = [], []
    for i, group in enumerate(cases):
        tokens, text = max((r['token_count'], text) for r, text in
                           zip(rows[i*width:(i+1)*width], group, strict=True) if r['token_count'] <= OUTPUT_CAP)
        assert 440 <= tokens <= OUTPUT_CAP
        responses.append(text)
        sizes.append(tokens)
    return responses, sizes


def main():
    require_hpc()
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    deny_network()
    check_pins()
    selected, items, templates = development_inputs()
    responses, sizes = long_responses()
    previous = json.loads((ARCHIVE / 'masbench_context_budget.json').read_bytes())
    initial_pins = {(r['record_id'], r['style'], r['agent']): r['request_content_sha256']
                    for r in previous['initial_requests']}
    labels, requests = [], []
    for ordinal, entry in enumerate(selected, 1):
        for style in FAMILIES:
            views = [private_view(items[entry['row']], name) for name in NAMES]
            for view in views:
                messages = LocalAgent(view, templates[style]).request()
                assert digest(messages) == initial_pins[(entry['record_id'], style, view.name)]
                labels.append({'case': ordinal, 'level': entry['level'], 'style': style, 'agent': view.name,
                               'kind': 'initial'})
                requests.append(messages)
            for condition in ('Full', 'No-A2A'):
                agents = [LocalAgent(view, templates[style]) for view in views]
                result = run_fixed(agents, responses, style, ContractTransport(), max_turns=6,
                                   admit=(lambda *_: condition == 'Full'))
                assert result['end_reason'] == 'turn_limit' and len(result['requests']) == 6
                assert all(message['delivered'] == (condition == 'Full') for message in result['messages'])
                if style == 'protocol' and condition == 'Full':
                    assert any('SHARED KNOWLEDGE BOARD' in message['content']
                               for message in result['requests'][-1][1:])
                for turn, messages in enumerate(result['requests'], 1):
                    labels.append({'case': ordinal, 'level': entry['level'], 'style': style,
                                   'agent': NAMES[(turn-1) % 2], 'kind': 'pressure',
                                   'condition': condition, 'turn': turn})
                    requests.append(messages)
    assert len(labels) == 112 and len(initial_pins) == 16
    measured = count(requests=requests)['requests']
    rows = [dict(label, prompt_tokens=row['token_count'], output_reserve=OUTPUT_CAP,
                 total_required=row['token_count'] + OUTPUT_CAP, message_count=len(messages),
                 application_request_bytes=len(canonical({'kind':'generate', 'messages':messages}))+1,
                 rendered_bytes=row['utf8_bytes'], request_sha256=digest(messages),
                 render_sha256=row['rendered_sha256'], token_ids_sha256=row['token_ids_json_sha256'])
            for label, messages, row in zip(labels, requests, measured, strict=True)]
    peak = max(r['total_required'] for r in rows)
    initial = [r['total_required'] for r in rows if r['kind'] == 'initial']
    summary = {'registry_sha256':REGISTRY_SHA, 'helper_sha256':HELPER_SHA, 'model_manifest_sha256':MANIFEST,
               'template_sha256':TEMPLATE, 'initial_count':len(initial), 'pressure_count':len(rows)-len(initial),
               'initial_above_1024':sum(n > 1024 for n in initial), 'initial_max_required':max(initial),
               'pressure_peak_required':peak, 'pressure_max_application_request_bytes':max(r['application_request_bytes'] for r in rows),
               'candidate_windows':list(WINDOWS), 'smallest_test_candidate':next((n for n in WINDOWS if peak <= n),None),
               'synthetic_response_tokens':sizes, 'http_requests':0, 'model_generations':0,
               'deployment_verified':False, 'rows':rows}
    write_json(Path(os.environ['GOSC_OUTPUT_DIR']) / 'window_demand.json', summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'}))


if __name__ == '__main__':
    main()
