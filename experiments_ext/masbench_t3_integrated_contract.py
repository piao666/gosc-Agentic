"""No-network T3 gate through the real driver and HDD/SSD registration path."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import resource
import socket
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from hpc_runs import require_hpc, write_json
from experiments_ext import masbench_t3_live as campaign
from experiments_ext.masbench_t1a_contract import deny_network
from experiments_ext.masbench_t1a_evidence_audit import read_chain
from extensions.masbench_reasoning import live_driver as live
from extensions.masbench_reasoning.application import LocalAgent, PrivateView
from extensions.masbench_reasoning.execution_safety import SafetyError, digest
from extensions.masbench_reasoning.registry import digest as registry_digest
from tests_ext.test_masbench_t1_live_driver import FakeIO, RUNNER


def refused(action):
    try:
        action()
    except SafetyError:
        return
    raise AssertionError('expected closed dispatch gate')


def fixture_agents(case, style):
    names = ('Alice','Bob')
    return [LocalAgent(PrivateView(name,names[1-index],f'Fictional question {case}',
                         f'Fictional evidence for {name}.'),style+' ${name} ${question} ${information}')
            for index,name in enumerate(names)]


def fixture_plan():
    rows = []
    for case in range(1,5):
        for style in ('base','protocol'):
            agents = fixture_agents(case,style)
            for condition in ('Full','No-A2A'):
                rows.append({'id':f'{case:02d}-{style}-{condition}','case':case,
                    'family_sha256':digest(case),'style':style,'condition':condition,
                    'private_view_sha256':digest([asdict(a.view) for a in agents]),
                    'initial_request_sha256':[registry_digest(a.request()) for a in agents]})
    return {'episodes':rows}


class FixtureIO(FakeIO):
    def __init__(self):
        super().__init__()
        self.n = 1200
        self.episode_requests = 0
        self.generation_count = 0

    def call(self,spec,timeout,crash=False):
        path = spec.get('path')
        if path=='/v1/chat/completions':
            self.episode_requests += 1
            self.generation_count += 1
            partition = self.driver.ledger.partitions[self.driver.current_episode]
            expected = f'{partition}/{self.generation_count-1}'
            assert self.driver.ledger.state['requests'][expected]['episode']==self.driver.current_episode
            key = self.driver.current_episode
            if key=='01-base-Full' and self.episode_requests==6:
                self.mode='timeout'
            if key=='01-base-No-A2A' and self.episode_requests==6:
                self.mode='length'
        result = super().call(spec,timeout,crash)
        if path=='/api/ps':
            for model in result['models']:
                model.update(name='qwen2.5:7b',digest=live.MANIFEST,context_length=16384)
        if path=='/v1/chat/completions':
            result['model']='qwen2.5:7b'
            if partition=='synthetic':
                result['choices'][0]['message']['content']='OK'
        return result


def main():
    require_hpc()
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    deny_network()
    try:
        socket.socket()
    except PermissionError:
        pass
    else:
        raise AssertionError('kernel network denial missing')
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    raw = campaign.open_hdd(out.parent,'gosc-t3-contracts')
    project = raw/'fixture-project'
    candidate = project/live.T3_PLAN
    plan_input = fixture_plan()
    write_json(candidate,plan_input)
    approval_path = raw/'fixture-authorization.json'
    write_json(approval_path,{'fixture_only':True})
    approval = {'run_id':out.parent.name,'scope':live.T3_SCOPE,'context':16384,
                'plan_path':live.T3_PLAN,'protocol_sha256':'1'*64,'registry_sha256':'2'*64,
                'generation_seconds':180}
    plan = live.t3_plan(plan_input)
    runtime = live.Runtime(str(project),'/not-executed',10000003,'fixture','0'*64,16384)
    io = FixtureIO()
    actual_stamp = live.proc_stamp
    with patch.object(live,'require_authorization',return_value=approval), \
         patch.object(live,'T3_EVIDENCE_ROOT',raw.parent), \
         patch.object(live,'runtime_files',return_value=project), \
         patch.object(live,'RPC',return_value=io), \
         patch.object(live,'runner_identities',side_effect=lambda r:[RUNNER] if io.runner_stamp else []), \
         patch.object(live,'proc_stamp',side_effect=lambda p:io.runner_stamp if p==RUNNER['pid'] else actual_stamp(p)):
        driver = live.LiveDriver(raw/'live',runtime,campaign.limits(240),authorization=approval_path,plan=plan)
        io.driver = driver
        try:
            case = plan[2]
            refused(lambda:driver.run_episode(plan[3]['id'],fixture_agents(1,'base'),max_turns=6))
            refused(lambda:driver.run_episode(case['id'],fixture_agents(2,'base'),max_turns=6))
            refused(lambda:driver.ledger.reserve_partition('task/blocked',plan[0]['id'],8,512,'task'))
            refused(lambda:driver.ledger.reserve_partition('synthetic/blocked',case['id'],8,512,'synthetic'))
            driver.current_episode=case['id']
            refused(lambda:driver.generate(fixture_agents(1,'base')[0].request()))
            assert not io.requests
            for synthetic in live.t3_cases():
                campaign.run_synthetic(driver,synthetic)
            for row in plan[2:]:
                io.mode = 'ok'
                io.episode_requests = 0
                driver.run_episode(row['id'],fixture_agents(row['case'],row['style']),max_turns=6)
                if driver.service_touched:
                    driver.recover()
            assert io.generation_count==98
            assert driver.control.used=={'debug':98,'get':312,'cleanup_get':36,'unload':18}
            assert not driver.service_lease.owner()
            assert driver.ledger.state['outputs']==50176
            assert driver.ledger.state['requests']['task/7']['observed_usage'] is None
            assert driver.ledger.state['requests']['task/13']['observed_usage']=={'prompt_tokens':1200,'completion_tokens':1}
            assert driver.ledger.state['episodes'][plan[4]['id']]=='completed'
            control_tip, ledger_tip = driver.control.previous, driver.ledger.previous
        finally:
            driver.close()
    ledger = read_chain(raw/'live/campaign/ledger.jsonl')
    control = read_chain(raw/'live/control.jsonl')
    assert ledger[-1]['hash']==ledger_tip and control[-1]['hash']==control_tip
    assert sum(r['event']['kind']=='barrier' for r in ledger)==18
    index = campaign.inventory(raw)
    write_json(out/'hdd_manifest.json',index)
    write_json(out/'integration.json',{
        'model_requests':0,'network_denied':True,'task_reservations':96,'synthetic_reservations':2,
        'hdd_readback_verified':index['readback_verified'],'hdd_root':index['hdd_root'],
        'live_source_sha256':live.file_sha(live.__file__),'launcher_sha256':live.file_sha(campaign.__file__),
        'ledger_tip':ledger_tip,'control_tip':control_tip,'old_runner_barriers':18,
        'unknown_timeout_retained':True,'reported_length_usage_retained':True,
        'wrong_partition_and_unfrozen_task_rejected':True,'later_episode_completed_after_fence':True})
    print('98 fabricated reservations, 18 recovery barriers, HDD readback verified, no model or network')


if __name__=='__main__':
    main()
