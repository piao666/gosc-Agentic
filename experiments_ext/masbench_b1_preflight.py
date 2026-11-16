"""HPC-only offline B1-pre inventory. No HTTP, generation, data edits or weights load."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hpc_runs import require_hpc, resource_limits


def sha(data):
    return hashlib.sha256(data).hexdigest()


def gguf_metadata(path):
    # GGUF v2/v3 little-endian metadata only. Never read tensor data.
    formats = {0:'B', 1:'b', 2:'H', 3:'h', 4:'I', 5:'i', 6:'f',
               7:'?', 10:'Q', 11:'q', 12:'d'}
    with path.open('rb') as f:
        def unpack(fmt):
            size = struct.calcsize('<' + fmt)
            data = f.read(size)
            if len(data) != size:
                raise ValueError('short GGUF')
            return struct.unpack('<' + fmt, data)[0]

        def string():
            n = unpack('Q')
            if n > 16 * 1024 * 1024:
                raise ValueError('metadata string too large')
            data = f.read(n)
            if len(data) != n:
                raise ValueError('short string')
            return data.decode('utf-8')

        def value(kind, capture=True):
            if kind == 8:
                return string()
            if kind == 9:
                subtype, count = unpack('I'), unpack('Q')
                if count > 2_000_000 or subtype == 9:
                    raise ValueError('unsupported array')
                start = f.tell()
                for _ in range(count):
                    value(subtype, False)
                end = f.tell()
                f.seek(start)
                digest = hashlib.sha256()
                remaining = end - start
                while remaining:
                    data = f.read(min(remaining, 65536))
                    digest.update(data)
                    remaining -= len(data)
                return {'type': subtype, 'count': count, 'raw_sha256': digest.hexdigest()}
            if kind not in formats:
                raise ValueError('unsupported GGUF type')
            return unpack(formats[kind])

        if f.read(4) != b'GGUF':
            raise ValueError('not little-endian GGUF')
        version, tensors, count = unpack('I'), unpack('Q'), unpack('Q')
        if version not in (2, 3) or count > 10000:
            raise ValueError('unsupported GGUF header')
        selected = {}
        for _ in range(count):
            key, kind = string(), unpack('I')
            val = value(kind)
            if key.startswith('tokenizer.') or key in ('general.architecture', 'qwen2.context_length'):
                if isinstance(val, str) and len(val) > 160:
                    val = {'utf8_bytes': len(val.encode()), 'sha256': sha(val.encode())}
                selected[key] = val
        end = f.tell()
        f.seek(0)
        return {'version': version, 'tensor_count': tensors, 'metadata_end': end,
                'metadata_prefix_sha256': sha(f.read(end)), 'selected': selected,
                'weight_tensors_read': False, 'exact_token_counter_verified': False}


def inventory():
    models = ROOT.parents[1] / 'models/ollama-gosc'
    mp = models / 'manifests/registry.ollama.ai/library/qwen2.5/7b'
    raw = mp.read_bytes()
    if sha(raw) != '845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e':
        raise ValueError('candidate manifest mismatch')
    manifest = json.loads(raw)
    layers = []
    for layer in [manifest['config'], *manifest['layers']]:
        p = models / 'blobs' / layer['digest'].replace(':', '-')
        row = {**layer, 'actual_size': p.stat().st_size}
        if row['actual_size'] != layer['size']:
            raise ValueError('blob size mismatch')
        if layer.get('mediaType', '').endswith('.model'):
            row['gguf'] = gguf_metadata(p)
        elif p.stat().st_size < 1024 * 1024:
            data = p.read_bytes()
            row['actual_sha256'] = sha(data)
            if 'params' in layer.get('mediaType', '') or 'config' in layer.get('mediaType', ''):
                row['json'] = json.loads(data)
        layers.append(row)
    whitelist = ['OLLAMA_CONTEXT_LENGTH', 'OLLAMA_MODELS', 'OLLAMA_NUM_PARALLEL',
                 'OLLAMA_MAX_LOADED_MODELS', 'OLLAMA_HOST', 'OLLAMA_NO_CLOUD']
    processes = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            args = (proc / 'cmdline').read_bytes().split(b'\0')
            if not args or Path(os.fsdecode(args[0])).name != 'ollama' or b'serve' not in args:
                continue
            env = dict(x.split(b'=', 1) for x in (proc / 'environ').read_bytes().split(b'\0') if b'=' in x)
            processes.append({'pid': int(proc.name), 'exe': os.readlink(proc/'exe'),
                              'environment_whitelist': {k: os.fsdecode(env[k.encode()]) for k in whitelist if k.encode() in env}})
        except (OSError, ValueError):
            continue
    packages = {}
    for name in ['openai', 'httpx', 'transformers', 'tokenizers', 'sentencepiece', 'tiktoken', 'llama-cpp-python', 'gguf']:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {'manifest_sha256': sha(raw), 'layers': layers, 'serve_processes': processes,
            'python': sys.version, 'packages': packages,
            'effective_num_ctx_verified': False, 'no_http_requests': True}


def data_summary():
    p = ROOT / 'research/sync/runs/hpc-masbench-registry-v2-20261103/outputs/development_registry_v1.json'
    raw = p.read_bytes()
    if sha(raw) != '6d14229ae0dd85a5b3c88b9309fcf86e54fab2523a3701914a7f7ebc06500a86':
        raise ValueError('frozen registry mismatch')
    r = json.loads(raw)
    families, comps = r['families'], r['component_rows']
    allrows = {i for c in comps for i in c}
    reserved = set(r['development_reserved_rows'])
    rest = set(r['not_reserved_rows'])
    if reserved & rest or reserved | rest != allrows:
        raise ValueError('partition inconsistency')
    selected = {x['family_sha256'] for x in r['selected']}
    d2reserved = {i for f in families if f['family_sha256'] in selected for i in f['rows']}
    def describe(rows):
        fs = [f for f in families if set(f['rows']) & rows]
        cs = [c for c in comps if set(c) & rows]
        return {'records': len(rows), 'families': len(fs), 'components_touched': len(cs),
                'families_fully_contained': sum(set(f['rows']) <= rows for f in fs),
                'components_fully_contained': sum(set(c) <= rows for c in cs),
                'component_intersection_sizes': sorted([len(set(c) & rows) for c in cs], reverse=True),
                'easy_records': sum(level == 'easy' for f in fs for i, level in zip(f['rows'], f['record_levels']) if i in rows),
                'hard_records': sum(level == 'hard' for f in fs for i, level in zip(f['rows'], f['record_levels']) if i in rows),
                'pilot_ineligible_records': len(rows & set(r['pilot_ineligible_family_rows']))}
    return {'registry_file_sha256': sha(raw), 'registry_content_sha256': r['registry_content_sha256'],
            'all': describe(allrows), 'D1_reserved': describe(reserved), 'D1_remaining': describe(rest),
            'D2_hypothetical_reserved': describe(d2reserved),
            'D2_hypothetical_remaining': describe(allrows - d2reserved),
            'D2_components_crossing_reservation': sum(bool(set(c)&d2reserved) and bool(set(c)-d2reserved) for c in comps),
            'selected': r['selected'], 'registry_modified': False,
            'actual_model_exposure': r['actual_model_exposure'], 'new_task_scores': False}


def main():
    require_hpc()
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    result = {'inventory': inventory(), 'data': data_summary(), 'resources': resource_limits(),
              'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()}
    (out / 'preflight.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'model_generation_requests': 0, 'data': result['data']}))


if __name__ == '__main__':
    main()
