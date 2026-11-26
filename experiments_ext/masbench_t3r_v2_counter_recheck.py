"""One explicitly approved vocabulary-only retry of immutable invented inputs."""
import hashlib
import gzip
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

from experiments_ext.masbench_t3r_v2_pressure import HELPER, HELPER_SHA, TEMPLATE_SHA, MANIFEST_SHA, WEIGHT


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()


def main():
    from scripts.hpc_runs import require_hpc, ROOT
    require_hpc()
    auth = json.loads((ROOT/'research/protocols/masbench_t3rv2i_counter_authorization_2026-11-26.json').read_bytes())
    assert auth['approved'] and auth['additional_helper_attempts']==1
    assert Path(os.environ['GOSC_RUN_DIR']).name==auth['run_id']
    cap = auth['per_process_hard_AS_bytes']
    resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
    resource.setrlimit(resource.RLIMIT_CPU,(20,20))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024**2,8*1024**2))
    src = ROOT/'research/sync/runs'/auth['source_pressure_run']/'outputs'
    body = (src/'counter-input.json').read_bytes()
    req_raw = (src/'synthetic-requests.json').read_bytes()
    assert sha(body)==auth['input_sha256'] and sha(req_raw)==auth['synthetic_requests_sha256']
    requests = json.loads(req_raw)
    payload = json.loads(body)
    assert [r['messages'] for r in payload['requests']]==requests
    assert sha(HELPER.read_bytes())==HELPER_SHA==auth['helper_sha256']
    models = ROOT.parents[1]/'models/ollama-gosc'
    manifest = models/'manifests/registry.ollama.ai/library/qwen2.5/7b'
    template = models/'blobs'/('sha256-'+TEMPLATE_SHA)
    assert sha(manifest.read_bytes())==MANIFEST_SHA and sha(template.read_bytes())==TEMPLATE_SHA
    assert payload['model_path']==str(models/'blobs'/WEIGHT) and payload['template_path']==str(template)
    assert payload['template_sha256']==TEMPLATE_SHA and payload['texts']==[]
    layer, = [x for x in json.loads(manifest.read_bytes())['layers'] if x['mediaType']=='application/vnd.ollama.image.model']
    assert layer['digest'].replace(':','-')==WEIGHT and (models/'blobs'/WEIGHT).stat().st_size==layer['size']
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    # Exclusive durable single-attempt marker BEFORE subprocess creation.
    marker = out/'dispatch.json'
    with marker.open('xb') as stream:
        stream.write(canonical(dict(input_sha256=sha(body),helper_sha256=HELPER_SHA,attempt=1,real_model=False))+b'\n')
        stream.flush();os.fsync(stream.fileno())
    def no_sockets(event, unused):
        if event.startswith('socket.'):
            raise PermissionError('counter-no-network')
    import sys
    sys.addaudithook(no_sockets)
    raw_path=Path('/tmp/gosc-t3rv2i-counter-v2-20261126-stdout.json')
    stdout = raw_path.open('xb')
    stderr = (out/'counter-stderr.log').open('xb')
    start = time.monotonic()
    def child_limits():
        resource.setrlimit(resource.RLIMIT_FSIZE,(6*1024**2,6*1024**2))
    process = subprocess.Popen([str(HELPER)],stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,
        env={**os.environ,'GOMAXPROCS':'2','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'},
        start_new_session=True,preexec_fn=child_limits)
    peak = 0
    failure = None
    try:
        os.set_blocking(process.stdin.fileno(),False)
        offset=0
        while process.poll() is None:
            if time.monotonic()-start>20:
                raise RuntimeError('helper_timeout')
            if process.stdin is not None:
                try:
                    offset += os.write(process.stdin.fileno(),body[offset:offset+65536])
                except BlockingIOError:
                    pass
                if offset==len(body):
                    process.stdin.close();process.stdin=None
            p = Path('/proc')/str(process.pid)/'status'
            if p.exists():
                fields = dict((line.split(':',1)[0],line.split(':',1)[1].strip()) for line in p.read_text().splitlines() if ':' in line)
                peak=max(peak,int(fields.get('VmRSS','0 kB').split()[0])*1024)
                if peak>auth['RSS_observation_stop_bytes']:
                    raise RuntimeError('helper_RSS_observation_stop')
            if raw_path.stat().st_size>6*1024**2:
                raise RuntimeError('helper_stdout_cap')
            time.sleep(.05)
    except BaseException as exc:
        failure=type(exc).__name__+':'+str(exc)
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        raise
    finally:
        process.wait()
        stdout.close();stderr.close()
        raw=raw_path.read_bytes()
        (out/'counter-raw.json.gz').write_bytes(gzip.compress(raw,compresslevel=1,mtime=0))
        (out/'process.json').write_text(json.dumps(dict(pid=process.pid,returncode=process.returncode,
            elapsed_seconds=time.monotonic()-start,peak_RSS_observed_bytes=peak,
            hard_AS_bytes=cap,failure=failure,model_inference=False,
            raw_stdout_sha256=sha(raw),raw_stdout_bytes=len(raw)),indent=2)+'\n')
    if process.returncode:
        raise RuntimeError('helper_exit:'+str(process.returncode))
    reply = json.loads(raw)
    assert reply['vocab_only'] is True and reply['tensor_context_created'] is False
    assert reply['input_sha256']==sha(body) and reply['template_sha256']==TEMPLATE_SHA
    assert reply['add_special'] is False and reply['parse_special'] is True
    assert len(reply['requests'])==len(requests)
    rows=[]
    for req,row in zip(requests,reply['requests']):
        assert sha(row['rendered'].encode())==row['rendered_sha256']
        assert len(row['rendered'].encode())==row['utf8_bytes']
        assert len(row['token_ids'])==row['token_count'] and sha(canonical(row['token_ids']))==row['token_ids_json_sha256']
        rows.append(dict(request_sha256=sha(canonical(req)),tokens=row['token_count'],
            rendered_sha256=row['rendered_sha256'],rendered_bytes=row['utf8_bytes'],fits_16384_with_512=row['token_count']+512<=16384))
    report=dict(acceptance_passed=True,rows=rows,source_run=auth['source_pressure_run'],
        input_sha256=sha(body),helper_sha256=HELPER_SHA,hard_AS_bytes=cap,
        real_model_calls=0,additional_fake_generations=0,vocab_only=True,tensor_context_created=False,
        raw_stdout_sha256=sha(raw),raw_stdout_bytes=len(raw),raw_stdout_storage='lossless counter-raw.json.gz; original also in tmpfs',
        total_helper_attempts_this_task=2,first_failed_attempt_preserved=True,
        limitation='offline synthetic vocabulary counts only, no live render/runtime/usage validation')
    (out/'counter_recheck.json').write_text(json.dumps(report,indent=2)+'\n')
    assert sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<=8*1024**2
    print(json.dumps(dict(acceptance_passed=True,requests=len(rows),max_input_tokens=max(r['tokens'] for r in rows),real_model_calls=0)))


if __name__=='__main__':
    main()
