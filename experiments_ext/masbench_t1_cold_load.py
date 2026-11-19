"""Bounded, one-shot Ollama cold-render diagnosis on the existing HPC service."""
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from hpc_runs import require_hpc, resource_limits, write_json
from experiments_ext.masbench_t1b_live import HELPER, Monitor, own_listener
from experiments_ext.masbench_t1_runner_evidence_audit import verify_artifacts
from experiments_ext.masbench_t1a_evidence_audit import read_chain, require
from extensions.masbench_reasoning import live_driver as live
from extensions.masbench_reasoning.execution_safety import canonical, digest, SafetyError

RUN = 'hpc-masbench-t1-cold-load-v2-20261119'
FIXTURE = 'hpc-masbench-t1-cold-load-fixture-v2-20261119'
FIRST = 'hpc-masbench-t1-cold-load-20261119'
OLD = 'hpc-masbench-t1b-post-storage-20261119'
RUNS = ROOT/'research/sync/runs'
AUTH = ROOT/'research/protocols/masbench_t1_cold_load_authorization_v2_2026-11-19.json'
PLAN = ROOT/'research/protocols/masbench_t1b_post_storage_plan.json'
BUDGET = ROOT/'research/protocols/masbench_t1_cold_load_diagnostic_budget_2026-11-19.md'
LEASE = ROOT/'.local/t1-service.lock'
LOG = ROOT/'.local/ollama/service.log'
ARCHIVE = Path('/hdd/u202520081000097/gosc-archive/2026-11-18-ssd-relief-v1')
OLD_SHA = 'f10f3609467d2f78b21f78f2abd01ee3fbc14b230ab041f0400f2b97d5878bbd'
SERVICE = live.Runtime(str(ROOT),HELPER,37483,'4897373256',
    'e014750cd656db3a77f3bf6b45903f646c76075e58b835cc9787fb5fc8a8a600')
CAPS = {'old_get':2,'get':4,'cleanup_get':8,'debug':1,'unload':1}
RESOURCES = {'driver_rss':2*1024**3,'service_rss':16*1024**3,'gpu_bytes':16*1024**3}
MAX_RESPONSE = 64*1024


def clock():
    return {'utc':datetime.now(timezone.utc).isoformat(),'mono':time.monotonic()}


def request_spec(kind):
    if kind in ('ps','version'):
        return 'GET', {'ps':'/api/ps','version':'/api/version'}[kind], None
    if kind=='render':
        messages = json.loads(PLAN.read_bytes())['cases'][0]['messages']
        return 'POST','/api/chat',{'model':SERVICE.model,'messages':messages,'stream':False,
            '_debug_render_only':True,'options':{'num_thread':2}}
    if kind=='unload':
        return 'POST','/api/chat',{'model':SERVICE.model,'messages':[],'keep_alive':0,'stream':False}
    raise SafetyError('HTTP operation is outside the cold-load contract')


def authorization():
    require(Path(os.environ['GOSC_RUN_DIR'])==RUNS/RUN,'cold-load run identity changed')
    approval = json.loads(live.reject_links(AUTH).read_bytes())
    require(approval['scope']=='one cold render only' and approval['exclusive_service'] is True
            and approval['authorize_old_marker_handling'] is True, 'authorization incomplete')
    for path,field in ((PLAN,'input_plan_sha256'),(BUDGET,'budget_sha256'),(Path(__file__),'source_sha256')):
        require(live.file_sha(path)==approval[field],f'frozen material changed: {field}')
    return approval


def endpoint_worker(parent, deadline):
    live.stop_with_parent(parent)
    authorization()
    kind = sys.stdin.read(24).strip()
    method,path,body = request_spec(kind)
    remaining = min(120, deadline-time.monotonic())
    if remaining<=0:
        raise TimeoutError('worker deadline')
    connection = http.client.HTTPConnection('127.0.0.1',11434,timeout=remaining)
    try:
        connection.request(method,path,canonical(body) if body is not None else None,{'Content-Type':'application/json'})
        print(json.dumps(dict(clock(),phase='sent')),flush=True)
        response = connection.getresponse()
        raw = response.read(MAX_RESPONSE+1)
        if len(raw)>MAX_RESPONSE:
            raise SafetyError('response byte cap')
        print(json.dumps(dict(clock(),phase='response',status=response.status,body=json.loads(raw))),flush=True)
    finally:
        connection.close()


def durable(path, value):
    payload = canonical(value)+b'\n'
    with path.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def runner_sample(identity, model, proc=Path('/proc')):
    base = proc/str(identity['pid'])
    try:
        stat = live.proc_fields(base)
        if stat[19]!=identity['stamp']:
            return dict(identity,status='identity-changed')
        row = dict(identity,status='observed',minflt=int(stat[7]),majflt=int(stat[9]),
                   user_ticks=int(stat[11]),system_ticks=int(stat[12]))
        for field in ('io','maps'):
            try:
                with (base/field).open('rb') as stream:
                    content = stream.read(256*1024+1)
                if len(content)>256*1024:
                    row[field+'_missing']='bounded-read-cap'
                elif field=='maps':
                    row['model_mapped'] = any(line.split(maxsplit=5)[5:]==[os.fsencode(model)]
                                              for line in content.splitlines())
                else:
                    row['io']={name.decode():int(value) for line in content.splitlines()
                               for name,value in [line.split(b':',1)]
                               if name in (b'rchar',b'read_bytes',b'syscr')}
            except (OSError, ValueError) as error:
                row[field+'_missing']=type(error).__name__
        if live.proc_fields(base)[19]!=identity['stamp']:
            return dict(identity,status='identity-changed')
        return row
    except (FileNotFoundError,ProcessLookupError):
        return dict(identity,status='exited-during-sample')


class Campaign:
    def __init__(self, out, control, models):
        self.out,self.control = out,control
        self.monitor = Monitor(SERVICE,RESOURCES,control)
        self.model = models/'blobs'/live.MODEL_BLOB
        self.last_sample = -1.0
        self.seen = {}
        self.samples = 0
        self.sample_bytes = 0

    def sample(self, cleanup=False, force=False):
        now = time.monotonic()
        if not force and self.last_sample>=0 and now-self.last_sample<1:
            return
        self.last_sample = now
        identities = live.runner_identities(SERVICE)
        for identity in identities:
            key=(identity['pid'],identity['stamp'])
            if key not in self.seen:
                self.control.append({'kind':'runner-observed','runner':identity})
                self.seen[key]=identity
        values = self.monitor(cleanup=cleanup,force=True)
        data = canonical(dict(clock(),runners=[runner_sample(row,self.model) for row in identities],
                              resources=values,cleanup=cleanup))+b'\n'
        require(self.sample_bytes+len(data) <= 2*1024**2, 'sample artifact cap')
        with (self.out/'samples.jsonl').open('ab') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        self.sample_bytes+=len(data)
        self.samples+=1

    def request(self, kind, category, deadline, watch=False):
        if deadline<=time.monotonic():
            raise TimeoutError('no dispatch time remains')
        method,path,body = request_spec(kind)
        self.control.charge(category)
        process = subprocess.Popen([sys.executable,str(Path(__file__)), '--worker',str(os.getpid()),str(deadline)],
                                   stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                                   start_new_session=True)
        stamp = live.proc_stamp(process.pid)
        buffer = bytearray()
        sent = None
        try:
            self.control.append({'kind':'worker','operation':kind,'pid':process.pid,'stamp':stamp,
                                 'request_sha256':digest({'method':method,'path':path,'body':body})})
            process.stdin.write((kind+'\n').encode())
            process.stdin.close()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout,selectors.EVENT_READ)
                while time.monotonic()<deadline:
                    if watch:
                        self.sample()
                    if not selector.select(max(0,min(.10,deadline-time.monotonic()))):
                        continue
                    data = os.read(process.stdout.fileno(),65536)
                    if not data:
                        raise SafetyError('HTTP worker exited without a complete result')
                    buffer.extend(data)
                    require(len(buffer)<=2*MAX_RESPONSE,'worker output cap')
                    while b'\n' in buffer:
                        line,_,rest = buffer.partition(b'\n')
                        buffer=bytearray(rest)
                        value=json.loads(line)
                        if value['phase']=='sent':
                            require(sent is None,'duplicate HTTP send receipt')
                            sent=value['mono']
                            deadline=min(deadline,sent+120)
                            self.control.append(dict(value,kind='http-sent',operation=kind,pid=process.pid))
                            continue
                        if value['phase']=='error':
                            self.control.append(dict(value,kind='http-worker-error',operation=kind,pid=process.pid))
                            raise SafetyError(f'{kind} worker: {value["error_type"]}')
                        require(sent is not None and sent<=value['mono']<=deadline,'response outside dispatch window')
                        durable(self.out/f'http-{len(self.control.rows):03d}-{kind}.json',value)
                        self.control.append({'kind':'http-response','operation':kind,'http_status':value['status'],
                                             'response_sha256':digest(value),'mono_observed':value['mono']})
                        return value
            self.control.append({'kind':'http-deadline','operation':kind,'sent_mono':sent,'deadline':deadline})
            raise TimeoutError(f'{kind} reached its bound')
        finally:
            if not process.stdin.closed:
                process.stdin.close()
            try:
                if process.poll() is None and stamp is not None:
                    live.stop_owned(process.pid,stamp,self.control)
            finally:
                process.wait(timeout=2)
                process.stdout.close()

    def value(self, kind, category, deadline, watch=False):
        reply=self.request(kind,category,deadline,watch)
        require(reply['status']==200,f'{kind} HTTP {reply["status"]}')
        return reply['body']


def validate_old_marker(owner):
    require(len(owner)==216 and hashlib.sha256(owner).hexdigest()==OLD_SHA,'stale marker changed')
    prior=RUNS/OLD
    value=json.loads(owner)
    require(value['campaign']==str(prior/'outputs/driver'),'stale marker owner changed')
    evidence=verify_artifacts(prior)
    require(len(evidence)==11,'source artifact count')
    status=json.loads((prior/'status.json').read_bytes())
    require(status['status']=='failed' and live.proc_stamp(status['pid']) is None,'older driver may still be active')
    control=read_chain(prior/'outputs/driver/control.jsonl')
    ledger=read_chain(prior/'outputs/driver/campaign/ledger.jsonl')
    require(control[0]['event']['identity']==ledger[0]['event']['binding']==value['ledger_binding'],'stale journal binding')
    require(not any(row['event']['kind'] in ('request','finish','barrier') for row in ledger),'older generation not excluded')
    for row in control:
        event=row['event']
        if event['kind']=='rpc-spawn':
            require(event['stamp'] is not None and live.proc_stamp(event['pid'])!=event['stamp'],'older HTTP worker still active')
    report=json.loads((prior/'outputs/summary.json').read_bytes())
    require(report['reservations']=={'requests':{},'inputs':0,'outputs':0} and report['service_marker_retained'],
            'older reservation or marker mismatch')
    sends=[row['event']['request_sha256'] for row in control if row['event']['kind']=='http-sent']
    def old_hash(kind):
        method,path,body=request_spec(kind)
        return digest({'kind':'http','method':method,'path':path,'body':body,
                       'authorization':str(ROOT/live.RECHECK_AUTH)})
    require(sends==[old_hash(k) for k in ('ps','render','ps','unload','ps')],'older wire identity mismatch')
    return {'control_tip':control[-1]['hash'],'ledger_tip':ledger[-1]['hash'],'source_run':OLD}


def idle(campaign):
    own_listener(SERVICE)
    require(not live.runner_identities(SERVICE),'runner is still active')
    values=campaign.monitor(force=True)
    require(values['gpu_bytes']==0,'GPU is not idle')
    for path in RUNS.glob('*/status.json'):
        if path.parent.name!=RUN:
            require(json.loads(path.read_bytes())['status'] not in ('running','planned'),'another run is active')


def retire(campaign, lease, deadline):
    old=lease.owner()
    proof=validate_old_marker(old)
    idle(campaign)
    require(campaign.value('version','old_get',min(deadline,time.monotonic()+3))=={'version':'0.11.11'},'wrong server')
    require(campaign.value('ps','old_get',min(deadline,time.monotonic()+3))=={'models':[]},'resident model')
    idle(campaign)
    proof.update(marker=json.loads(old),marker_hex=old.hex(),marker_sha256=OLD_SHA,
                 proved_zero_generation=True,observed=clock())
    durable(ARCHIVE/'t1_cold_diagnostic_old_marker_20261119.json',proof)
    campaign.control.append({'kind':'old-marker-preserved','proof_sha256':digest(proof)})
    require(time.monotonic()<deadline and lease.owner()==old,'old recovery deadline or marker drift')
    lease.clear(old)
    campaign.control.append({'kind':'old-marker-retired'})


def clean(campaign, lease, marker, deadline):
    live.runtime_files(SERVICE)
    own_listener(SERVICE)
    active=campaign.value('ps','cleanup_get',min(deadline,time.monotonic()+4))['models']
    require(all(m.get('name')==SERVICE.model and m.get('digest')==live.MANIFEST for m in active),'foreign resident model')
    campaign.sample(cleanup=True,force=True)
    campaign.control.append({'kind':'unload-start','runner_witnesses':list(campaign.seen.values())})
    reply=campaign.value('unload','unload',min(deadline,time.monotonic()+10))
    require(reply.get('done') is True and reply.get('done_reason')=='unload','unload acknowledgment')
    while time.monotonic()<deadline and campaign.control.used['cleanup_get']<CAPS['cleanup_get']:
        empty=campaign.value('ps','cleanup_get',min(deadline,time.monotonic()+4))=={'models':[]}
        campaign.sample(cleanup=True,force=True)
        exited=[dict(row,current_stamp=live.proc_stamp(row['pid'])) for row in campaign.seen.values()]
        if (empty and exited and all(row['stamp']!=row['current_stamp'] for row in exited)
                and not live.runner_identities(SERVICE)):
            idle(campaign)
            campaign.control.append({'kind':'unload-and-identity-proved','exited':exited,'response':reply})
            lease.clear(marker)
            campaign.control.append({'kind':'diagnostic-marker-retired'})
            return
        time.sleep(.35)
    raise SafetyError('unload returned, runner-exit or idle evidence incomplete')


def main():
    begin=time.monotonic()
    require_hpc()
    approval=authorization()
    require(json.loads((RUNS/FIXTURE/'status.json').read_bytes())['status']=='completed',
            'network-denied fixture did not pass')
    first=RUNS/FIRST
    verify_artifacts(first)
    initial=json.loads((first/'outputs/summary.json').read_bytes())
    initial_events=read_chain(first/'outputs/control.jsonl')
    require(initial['render']=='not-dispatched' and initial['charges']==(dict.fromkeys(CAPS,0)|{'old_get':1})
            and all(row['event']['kind'] not in ('http-sent','old-marker-retired') for row in initial_events),
            'uncertain initial dispatch, no continuation')
    resource=resource_limits()
    require(int(resource['cpu_quota'])==2*int(resource['cpu_period']),'CPU allocation changed')
    models=live.runtime_files(SERVICE)
    out=live.reject_links(os.environ['GOSC_OUTPUT_DIR'])
    require(not any(out.iterdir()),'diagnostic cannot replay')
    with (out/'write-preflight.bin').open('xb') as probe:
        probe.write(b'cold-load evidence storage check\n')
        probe.flush()
        os.fsync(probe.fileno())
    control=live.ControlJournal(out/'control.jsonl',digest(approval),CAPS)
    lease=live.ServiceLease(LEASE)
    campaign=Campaign(out,control,models)
    report={'run':RUN,'generation_requests':0,'actual_task_inputs':0,'render':'not-dispatched',
            'cold_runner_before_send':False,'cache_temperature':'unknown','log_begin':None,
            'prior_no_send_run':FIRST,'prior_old_get_charge':1}
    claimed=False
    marker=canonical({'campaign':str(out),'diagnostic_authority':digest(approval)})
    try:
        retire(campaign,lease,begin+29)
        stage=time.monotonic()
        report['diagnostic_started']=clock()
        require(campaign.value('ps','get',min(stage+20,time.monotonic()+4))=={'models':[]},'runner unexpectedly resident')
        idle(campaign)
        campaign.sample(force=True)
        require(time.monotonic()<stage+20,'diagnostic preparation exceeded budget')
        log=LOG.stat()
        report['log_begin']={'inode':log.st_ino,'offset':log.st_size}
        report['cold_runner_before_send']=True
        lease.mark(marker)
        claimed=True
        control.append({'kind':'diagnostic-marker-held'})
        try:
            value=campaign.value('render','debug',min(stage+140,time.monotonic()+120),watch=True)
            require(value.get('model')==SERVICE.model and isinstance(value.get('_debug_info',{}).get('rendered_template'),str),
                    'unexpected debug-render response')
            report['render']='completed'
        except (SafetyError,TimeoutError,OSError) as exc:
            report['render']='incomplete'
            report['render_error']=repr(exc)
        finally:
            report['render_finished']=clock()
            report['cleanup_started']=clock()
            clean(campaign,lease,marker,min(stage+180,time.monotonic()+40))
            report['cleanup_completed']=clock()
    except (SafetyError,TimeoutError,OSError,RuntimeError) as exc:
        report['error']=repr(exc)
    finally:
        log=LOG.stat()
        report.update(log_end={'inode':log.st_ino,'offset':log.st_size},charges=control.used,
                      elapsed_seconds=time.monotonic()-begin,samples=campaign.samples,peaks=campaign.monitor.peaks,
                      service_marker_retained=bool(lease.owner()),diagnostic_claimed=claimed)
        write_json(out/'summary.json',report)
        lease.close()
        control.close()
    return int(report['render']!='completed' or 'error' in report or report['service_marker_retained'])


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--worker':
        try:
            endpoint_worker(int(sys.argv[2]),float(sys.argv[3]))
        except Exception as exc:
            print(json.dumps(dict(clock(),phase='error',error_type=type(exc).__name__)),flush=True)
            raise SystemExit(1) from exc
    elif len(sys.argv)==1:
        raise SystemExit(main())
    else:
        raise SystemExit('invalid cold-load entry')
