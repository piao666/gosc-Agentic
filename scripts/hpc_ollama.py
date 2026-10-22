"""User-level pinned Ollama deployment and real GPU inference smoke, HPC only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

from hpc_runs import ROOT, require_hpc, resource_limits, write_json
sys.path.insert(0, str(ROOT))

CONFIG = ROOT / 'research/protocols/ollama_hpc_v1.json'
STATE = ROOT / '.local/ollama'
BASE = 'http://127.0.0.1:11434'


def api(path, body=None, timeout=30):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def settings():
    cfg = json.loads(CONFIG.read_text())
    prefix = STATE / 'runtime' / cfg['version']
    models = ROOT.parents[1] / 'models/ollama-gosc'
    env = os.environ.copy()
    env.update(OLLAMA_HOST=cfg['bind'], OLLAMA_MODELS=str(models),
               OLLAMA_NUM_PARALLEL='1', OLLAMA_MAX_LOADED_MODELS='1',
               OLLAMA_MAX_QUEUE='4', OLLAMA_CONTEXT_LENGTH='1024',
               OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2',
               OLLAMA_KEEP_ALIVE='5m', OLLAMA_NO_CLOUD='1')
    return cfg, prefix, models, env


def ready():
    try:
        return api('/api/version', timeout=3)
    except Exception:
        return None


def start():
    cfg, prefix, models, env = settings()
    current = ready()
    if current:
        if current.get('version') != cfg['version']:
            raise RuntimeError('Existing service version differs; do not replace another service')
        return {'reused': True, 'version': current}
    binary = prefix / 'bin/ollama'
    if not binary.is_file():
        raise RuntimeError('Pinned runtime not installed')
    STATE.mkdir(parents=True, exist_ok=True)
    models.mkdir(parents=True, exist_ok=True)
    log = STATE / 'service.log'
    with log.open('ab') as stream:
        proc = subprocess.Popen([str(binary), 'serve'], env=env, stdin=subprocess.DEVNULL,
                                stdout=stream, stderr=stream, start_new_session=True)
    write_json(STATE / 'service.json', {'pid': proc.pid, 'binary': str(binary),
               'bind': cfg['bind'], 'models': str(models), 'version': cfg['version'],
               'started_at_unix': time.time(), 'log': str(log), 'auto_restart_after_container_reboot': False})
    for _ in range(60):
        if proc.poll() is not None:
            raise RuntimeError('Ollama service exited; inspect .local/ollama/service.log')
        value = ready()
        if value:
            return {'pid': proc.pid, 'reused': False, 'version': value}
        time.sleep(1)
    raise RuntimeError('Service did not become ready in 60 seconds')


def install(out, url_file):
    cfg, prefix, models, env = settings()
    archive = STATE / 'downloads/ollama-linux-amd64-0.11.11.tgz'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists() or hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest() != cfg['archive_sha256']:
        url = json.loads(Path(url_file).read_text())['download_url'] if url_file else cfg['archive_url']
        # URL may be an official release-asset redirect, kept only in ignored runtime config.
        subprocess.run(['curl', '-fLsS', '--retry', '5', '--retry-delay', '5',
                        '--connect-timeout', '20', '--max-time', '7200', '-C', '-',
                        '-o', str(archive), url], check=True, timeout=7300)
    with archive.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    write_json(out / 'archive_verification.json', {'official_url': cfg['archive_url'],
               'sha256': actual, 'expected_sha256': cfg['archive_sha256'],
               'size': archive.stat().st_size, 'verified': actual == cfg['archive_sha256']})
    if actual != cfg['archive_sha256']:
        raise RuntimeError('Archive checksum mismatch; preserve file, do not execute')
    if not prefix.exists():
        staging = prefix.with_name(prefix.name + '.extracting')
        if staging.exists():
            write_json(out / 'partial_extraction_before_retry.json', {'files': [
                {'path': str(p.relative_to(staging)), 'size': p.stat().st_size}
                for p in staging.rglob('*') if p.is_file()],
                'note': 'Own failed extraction only; retry same checksum-verified archive, failure ledger preserved'})
        staging.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, 'r:gz') as bundle:
            bundle.extractall(staging, filter='data')
        staging.rename(prefix)
    binary = prefix / 'bin/ollama'
    version = subprocess.check_output([str(binary), '--version'], stderr=subprocess.STDOUT, env=env).decode()
    wrapper = Path.home() / '.local/bin/ollama'
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    body = '#!/bin/sh\n' + ''.join('export ' + k + '=' + shlex.quote(env[k]) + '\n' for k in
           ['OLLAMA_HOST','OLLAMA_MODELS','OLLAMA_NUM_PARALLEL','OLLAMA_MAX_LOADED_MODELS',
            'OLLAMA_CONTEXT_LENGTH','OMP_NUM_THREADS','OLLAMA_NO_CLOUD'])
    body += 'exec ' + shlex.quote(str(binary)) + ' "$@"\n'
    if wrapper.exists() and (wrapper.is_symlink() or wrapper.read_text() != body):
        raise RuntimeError('Existing Ollama wrapper differs; refusing to overwrite')
    wrapper.write_text(body); wrapper.chmod(0o755)
    deployment = {'version_command': version, 'prefix': str(prefix), 'binary': str(binary),
                  'wrapper': str(wrapper), 'models': str(models), 'resources': resource_limits(),
                  'glibc': subprocess.check_output(['getconf','GNU_LIBC_VERSION']).decode().strip(),
                  'platform': platform.platform(), 'service': start()}
    write_json(out / 'deployment.json', deployment)
    print(json.dumps(deployment), flush=True)


def prepare(out):
    cfg, prefix, models, env = settings()
    start()
    observations = []
    for model in cfg['models']:
        tag_path = out / (model.replace(':','_') + '-pull.jsonl')
        req = urllib.request.Request(BASE + '/api/pull', json.dumps({'model': model, 'stream': True}).encode(),
                                     {'Content-Type': 'application/json'})
        last = None
        with urllib.request.urlopen(req, timeout=7200) as response, tag_path.open('a') as stream:
            for line in response:
                value = json.loads(line)
                progress = (value.get('status'), value.get('digest'),
                            int(value.get('completed',0) / max(value.get('total',1),1) * 20))
                if progress != last:
                    stream.write(json.dumps(value)+'\n'); stream.flush()
                    print(model, value.get('status'), progress[-1]*5, '%', flush=True)
                    last = progress
                if value.get('error'):
                    raise RuntimeError(value['error'])
        # Match the original LLM request shape; only the thread cap is additional.
        body = {'model': model, 'prompt': 'Choose A. Answer with a JSON object containing choice A.',
                'format': {'type':'object','properties':{'choice':{'type':'string','enum':['A','B']}},
                           'required':['choice']}, 'stream': False, 'keep_alive':'5m',
                'options':{'temperature':0,'seed':0,'num_predict':12,'num_ctx':1024,'num_thread':2}}
        started = time.monotonic()
        generated = api('/api/generate', body, timeout=600)
        loaded = api('/api/ps')
        record = {'model': model, 'request': body, 'response': generated,
                  'wall_s': time.monotonic()-started, 'loaded': loaded,
                  'show': api('/api/show', {'model':model}),
                  'gpu': subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.used',
                                                   '--format=csv,noheader']).decode(),
                  'ps': subprocess.check_output([str(prefix/'bin/ollama'),'ps'], env=env).decode()}
        write_json(out/(model.replace(':','_')+'-smoke.json'), record)
        if json.loads(generated.get('response','{}')).get('choice') != 'A':
            raise RuntimeError('JSON schema generation smoke failed: '+model)
        running = [item for item in loaded['models'] if item['name'] == model]
        if not running or running[0].get('size_vram',0) <= 0 or '100% GPU' not in record['ps']:
            raise RuntimeError('Actual full GPU inference not verified: '+model)
        # Integration uses the unchanged original client with an isolated empty cache.
        from gosc import llm_agent
        llm_agent.OLLAMA_URL = BASE + '/api/generate'
        client = llm_agent.LLMClient(model, cache_dir=str(out/'integration-cache'))
        choice = client.choose('Choose A for the GPU installation check; return choice A.', ['A','B'])
        integration = {'choice':choice,'calls':client.calls,'cache_hits':client.hits,'seconds':client.seconds}
        write_json(out/(model.replace(':','_')+'-integration.json'),integration)
        if choice != 'A' or client.calls != 1 or client.hits != 0:
            raise RuntimeError('Original real-HTTP client integration failed: '+model)
        observations.append({'model':model,'full_gpu':True,'integration':integration,
                             'digest':running[0].get('digest'),'details':running[0].get('details')})
        write_json(out/'model_progress.json',{'completed':observations,'expected':cfg['models']})
        api('/api/generate',{'model':model,'keep_alive':0},timeout=120)
    value = {'ollama_base_url':BASE,'version':cfg['version'],'models':observations,
             'validated_at_unix':time.time(),'bind':'loopback only','readiness':'all three real GPU/HTTP checks passed'}
    target = ROOT/'.local/reproduction-services.json'
    if target.exists():
        current = json.loads(target.read_text())
        if current.get('ollama_base_url',BASE) != BASE:
            raise RuntimeError('Existing runtime config points elsewhere; preserved')
        value = current | value
    write_json(target,value)
    write_json(out/'readiness.json',value)
    write_json(out/'tags.json',api('/api/tags'))
    print('All three models passed real GPU inference and original HTTP client integration.',flush=True)


def main():
    require_hpc()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['install','start','prepare'])
    parser.add_argument('--download-url-file')
    args = parser.parse_args()
    if args.action == 'start':
        print(json.dumps(start()));return
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    if args.action == 'install':install(out,args.download_url_file)
    else:prepare(out)


if __name__ == '__main__':
    main()
