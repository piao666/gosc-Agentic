"""Recover the specific, independently audited zero-dispatch T2 attempt."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from hpc_runs import require_hpc
from experiments_ext import masbench_t2_live as deploy
from experiments_ext.masbench_t1_runner_evidence_audit import read_chain, require, verify_artifacts
from extensions.masbench_reasoning import live_driver as live

RUNS=ROOT/'research/sync/runs'
RUN=RUNS/'hpc-masbench-t2-live-20261125'
AUDIT=RUNS/'hpc-masbench-t2-audit-20261125'
ARCHIVE=Path('/hdd/u202520081000097/gosc-archive/2026-11-25-t2-zero-dispatch')
MARKER_SHA='d83a9336806721f726eead7649bd180339fe6ef114eabda3ce20c05168c343b3'
PROFILE_SHA='d7d9d7dc22b8f160d37a87b5aefb4d0c855dffce148992d5e5ba27b24caaccbd'
BINARY_SHA='e014750cd656db3a77f3bf6b45903f646c76075e58b835cc9787fb5fc8a8a600'


def save(path, body):
    with path.open('xb') as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    expected=hashlib.sha256(body).hexdigest()
    require(live.file_sha(path)==expected,'HDD archive readback mismatch')
    return expected


def main():
    require_hpc()
    require(os.getuid()==8301880 and ARCHIVE.resolve()==ARCHIVE and os.path.ismount('/hdd'),'wrong recovery scope')
    require(not any(json.loads(p.read_bytes())['status'] in ('running','planned') for p in RUNS.glob('*/status.json')),
            'active job blocks administrative recovery')
    require(json.loads((RUN/'status.json').read_bytes())['status']=='failed','prior T2 status drift')
    require(json.loads((AUDIT/'status.json').read_bytes())['status']=='completed','failure audit missing')
    verify_artifacts(RUN)
    verify_artifacts(AUDIT)
    result=json.loads((AUDIT/'outputs/audit.json').read_bytes())
    require(result['failed_prefix_verified'] and not result['acceptance_passed']
            and result['reservations']=={'requests':{},'inputs':0,'outputs':0},'prior run dispatched or audit mismatch')
    paths={'control.jsonl':RUN/'outputs/driver/control.jsonl',
           'ledger.jsonl':RUN/'outputs/driver/campaign/ledger.jsonl',
           'summary.json':RUN/'outputs/summary.json','audit.json':AUDIT/'outputs/audit.json',
           'service_transitions.jsonl':RUN/'outputs/service_transitions.jsonl','status.json':RUN/'status.json'}
    ledger=read_chain(paths['ledger.jsonl'])
    control=read_chain(paths['control.jsonl'])
    require(not any(row['event']['kind']=='request' for row in ledger)
            and not any(row['event']['kind']=='runner-dispatch-bound' for row in control),'generation evidence present')
    cleanup,=[row['event']['observation'] for row in control if row['event']['kind']=='unload-unverified']
    require(cleanup['ps']=={'models':[]} and cleanup['remaining_runners']==[]
            and cleanup['response']['done_reason']=='unload','unload evidence drift')
    lease=live.ServiceLease(deploy.LEASE)
    try:
        marker=lease.owner()
        owner=json.loads(marker)
        require(len(marker)==207 and hashlib.sha256(marker).hexdigest()==MARKER_SHA
                and owner['campaign']==str(RUN/'outputs/driver')
                and owner['ledger_binding']==ledger[0]['event']['binding']==control[0]['event']['identity'],
                'active marker does not belong to the audited zero-dispatch run')
        profile=deploy.PROFILE.read_bytes()
        require(live.file_sha(deploy.PROFILE)==PROFILE_SHA and json.loads(profile)=={'context_tokens':16384},
                'candidate profile does not match the failed transition')
        running=deploy.service(16384,BINARY_SHA)
        require(running and (running.service_pid,running.service_stamp)==(34365,'4966254184'),'service changed')
        deploy.assert_idle(running)
        ARCHIVE.mkdir(mode=0o700)
        shas={name:save(ARCHIVE/name,path.read_bytes()) for name,path in paths.items()}
        shas['original_lease']=save(ARCHIVE/'original_lease',marker)
        shas['candidate_profile.json']=save(ARCHIVE/'candidate_profile.json',profile)
        deploy.sync_dir(ARCHIVE)
        deploy.sync_dir(ARCHIVE.parent)
        raw=Path('/proc',str(running.service_pid),'environ').read_bytes()
        env=dict(item.split('=',1) for item in raw.decode().split('\0') if '=' in item)
        journal=ARCHIVE/'rollback.jsonl'
        deploy.stop_idle(running,journal)
        deploy.PROFILE.unlink()
        deploy.sync_dir(deploy.PROFILE.parent)
        baseline=deploy.start_checked(1024,env,BINARY_SHA,journal,'baseline-restart')
        require(lease.owner()==marker and not deploy.PROFILE.exists(),'recovery identity changed')
        lease.clear(marker)
        require(not lease.owner(),'marker did not clear')
        evidence={'archive':str(ARCHIVE),'source_run':RUN.name,'independent_audit':AUDIT.name,
                  'generation_dispatches':0,'reserved_input':0,'reserved_output':0,'gpu_mib':0,
                  'service':deploy.identity(baseline),'archive_sha256':shas,'lease_marker_bytes':0}
        save(ARCHIVE/'recovery.json',json.dumps(evidence,indent=2).encode()+b'\n')
        deploy.sync_dir(ARCHIVE)
        print(json.dumps(evidence))
    finally:
        lease.close()


if __name__=='__main__':
    main()
