"""Extract bounded, provenance-linked historical Ollama log observations."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
LOG = ROOT/'.local/ollama/service.log'
ARCHIVE = Path('/hdd/u202520081000097/gosc-archive/2026-11-18-ssd-relief-v1')
RUN = ROOT/'research/sync/runs/hpc-masbench-t1b-runner-recheck-20261118'
assert os.getuid()==8301880 and LOG.resolve()==LOG and ARCHIVE.resolve()==ARCHIVE
patterns = {
    'failed_recheck':re.compile(rb'2026[-/]11[-/]18(?:T| - )(?:15|07):(43:4[5-9]|43:5[0-9]|44:[01][0-9]|44:2[0-4])'),
    'previous_successful_debug':re.compile(rb'2026[-/]11[-/]18(?:T| - )(?:14|06):(06:5[6-9]|07:0[0-9])'),
}
msg = re.compile(rb'msg="((?:[^"\\]|\\.)*)"')
source = re.compile(rb'source=([^ \r\n]+)')
tags = (b'error', b'reason', b'status', b'progress', b'duration')
sensitive = re.compile(rb'authorization|api[_ -]?key|password|secret|bearer|proxy=|environment=|config=|env=', re.I)
entries = {}
for title, pattern in patterns.items():
    selected = []
    with LOG.open('rb') as stream:
        while line := stream.readline():
            match = pattern.search(line)
            if not match:
                continue
            m = msg.search(line)
            origin = source.search(line)
            if m and not sensitive.search(m[1]):
                message = m[1].decode(errors='replace')[:330]
            elif b'[GIN]' in line:
                route = re.search(rb'\|\s*(\d+)\s*\|\s*([^|]+)\|.*?\b(GET|POST)\s+"(/[^"]+)"\s*$',line)
                if not route:
                    continue
                message = f'{route[1].decode()} {route[2].decode().strip()} {route[3].decode()} {route[4].decode()}'
            else:
                continue
            row = {'timestamp':match[0].decode(), 'offset':stream.tell()-len(line),
                   'size':len(line),'sha256':hashlib.sha256(line).hexdigest(),'message':message}
            if origin:
                row['code_source']=Path(origin[1].decode()).name
            for tag in tags:
                field = re.search(rb'(?:^| )'+tag+rb'=(?:"([^"]*)"|([^\s]+))',line)
                if field:
                    value = field[1] or field[2] or b''
                    if not sensitive.search(value):
                        row[tag.decode()]=value.decode(errors='replace')[:190]
            selected.append(row)
    entries[title]=selected

raw_status = (RUN/'status.json').read_bytes()
receipt = {'host':os.uname().nodename,'observed_utc':datetime.now(timezone.utc).isoformat(),
           'source':str(LOG),'source_inode':LOG.stat().st_ino,'source_bytes_at_read':LOG.stat().st_size,
           'source_preserved_in_place':True,'entries':entries,
           'failed_run_status_sha256':hashlib.sha256(raw_status).hexdigest(),
           'failed_run_status':json.loads(raw_status),'additional_service_calls':0}
with (ARCHIVE/'t1_499_review_2026-11-19.json').open('x',encoding='utf-8') as out:
    json.dump(receipt,out,indent=2)
    out.write('\n')
    out.flush()
    os.fsync(out.fileno())
print(json.dumps(receipt))
