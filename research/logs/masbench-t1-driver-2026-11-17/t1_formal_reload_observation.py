"""Capture only runner-option metadata and scoped service events from the failed tail."""
import hashlib
import json
import os
from pathlib import Path
import re

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
models=root.parents[1]/'models/ollama-gosc'
manifest=models/'manifests/registry.ollama.ai/library/qwen2.5/7b'
log=root/'.local/ollama/service.log'
assert os.getuid()==8301880
pin=hashlib.sha256(manifest.read_bytes()).hexdigest()
assert pin=='845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'
options={}
for layer in json.loads(manifest.read_bytes())['layers']:
    if layer['mediaType']!='application/vnd.ollama.image.params':
        continue
    digest=layer['digest']
    assert re.fullmatch('sha256:[a-f0-9]{64}',digest) and 0<=layer['size']<=65536
    raw=(models/'blobs'/digest.replace(':','-')).read_bytes()
    assert len(raw)==layer['size'] and hashlib.sha256(raw).hexdigest()==digest.split(':')[1]
    options.update(json.loads(raw))
window=re.compile(rb'2026[-/]11[-/]19(?:T| - )(?:14|06):46:(?:1[3-9]|2[0-8])')
records=[]
with log.open('rb') as stream:
    while line:=stream.readline():
        match=window.search(line)
        if not match:
            continue
        events=[label for prefix,label in [(b'starting runner','runner-launch'),
                 (b'llama runner started in','ready'),(b'loaded runners','runner-admitted')] if prefix in line]
        route=re.search(rb'\|\s*(\d+)\s*\|\s*([^|]+)\|.*?\bPOST\s+"(/[^"]+)"\s*$',line)
        if route and route[3] in (b'/api/chat',b'/v1/chat/completions'):
            events.append({'status':int(route[1]),'elapsed':route[2].decode().strip(),'route':route[3].decode()})
        if events:
            records.append({'time_prefix':match[0].decode(),'offset':stream.tell()-len(line),
                            'bytes':len(line),'sha256':hashlib.sha256(line).hexdigest(),'events':events})
print(json.dumps({'manifest_sha256':pin,'model_defined_num_thread':options.get('num_thread'),
                  'model_defines_num_thread':'num_thread' in options,'model_defined_num_ctx':options.get('num_ctx'),
                  'service_log':str(log),'records':records,'additional_http_operations':0}))
