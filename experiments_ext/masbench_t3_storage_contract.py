"""Exercise a full control allocation and readback on the project user's HDD."""
import hashlib
import json
import os
from pathlib import Path
import resource
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from experiments_ext.masbench_t1a_contract import deny_network
from experiments_ext.masbench_t1a_evidence_audit import read_chain
from extensions.masbench_reasoning.execution_safety import SafetyError
from extensions.masbench_reasoning.live_driver import ControlJournal
from hpc_runs import require_hpc, write_json

HDD=Path('/hdd/u202520081000097')
CONTROL_CAPS={'debug':98,'get':312,'cleanup_get':108,'unload':18}
CONTROL_BYTES=8*1024**2


def main():
    require_hpc()
    assert os.getuid()==8301880 and HDD.resolve()==HDD and os.path.ismount(HDD.parent)
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    deny_network()
    ssd=Path(os.environ['GOSC_OUTPUT_DIR'])
    assert ssd.is_dir() and ssd.stat().st_dev!=HDD.stat().st_dev
    root=HDD/'gosc-t3-contracts'/ssd.parent.name
    assert root.resolve()==root
    root.mkdir(parents=True,exist_ok=False,mode=0o700)
    path=root/'control.jsonl'
    scope={'run_id':ssd.parent.name,'fixture_only':True}
    journal=ControlJournal(path,scope,CONTROL_CAPS,reserve_bytes=CONTROL_BYTES)
    try:
        for category, cap in CONTROL_CAPS.items():
            for index in range(cap):
                journal.charge(category)
                for part in range(4):
                    journal.append({'kind':'fixture_evidence','category':category,'index':index,'part':part,
                                    'sha256':hashlib.sha256(f'{category}/{index}/{part}'.encode()).hexdigest()})
            try:
                journal.charge(category)
            except SafetyError:
                pass
            else:
                raise AssertionError('global control cap was exceeded')
        expected_tip, records=journal.previous,len(journal.rows)
    finally:
        journal.close()
    body=path.read_bytes()
    rows=read_chain(path)
    assert rows[-1]['hash']==expected_tip and len(rows)==records
    assert len(body)==CONTROL_BYTES
    journal=ControlJournal(path,scope,CONTROL_CAPS,reserve_bytes=CONTROL_BYTES)
    try:
        assert journal.used==CONTROL_CAPS and journal.previous==expected_tip
    finally:
        journal.close()
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    receipt={'hdd_directory':str(root),'ssd_directory':str(ssd),'control_counts':CONTROL_CAPS,
             'hdd_control_bytes':len(body),'control_sha256':hashlib.sha256(body).hexdigest(),
             'control_records':records,'reopened_exact_budget':True,'model_requests':0,'http':0,
             'scope':'synthetic storage contract'}
    write_json(ssd/'t3_storage_receipt.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':
    main()
