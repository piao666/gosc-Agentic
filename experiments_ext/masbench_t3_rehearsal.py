"""No-network sizing of T3 application packets on the frozen four-item matrix."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import resource
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from experiments_ext import masbench_t2_window_demand as t2
from experiments_ext.masbench_t1a_contract import deny_network
from extensions.masbench_reasoning.application import LocalAgent, private_view
from extensions.masbench_reasoning.client import ClientConfig, ContextBinding, ControlledClient, run_controlled
from extensions.masbench_reasoning.evaluation import summarize
from extensions.masbench_reasoning.execution_safety import canonical, digest
from extensions.masbench_reasoning.fixture_driver import _jsonable
from extensions.masbench_reasoning.wire import ContractTransport
from hpc_runs import require_hpc, write_json


def packet_size(packet):
    return len(canonical(_jsonable(packet))) + 1


class Replay:
    is_live = False
    model = 't3-fixture'
    manifest = '0' * 64

    def __init__(self, responses, input_tokens, output_tokens):
        self.responses, self.input_tokens, self.output_tokens = responses, input_tokens, output_tokens
        self.requests = []

    def identity(self, timeout):
        return {'model': self.model, 'manifest_sha256': self.manifest}

    def create(self, payload, timeout):
        i = len(self.requests)
        self.requests.append(payload['messages'])
        p, c = self.input_tokens[t2.digest(payload['messages'])], self.output_tokens[i]
        return {'model': self.model, 'choices': [{'finish_reason': 'stop',
                          'message': {'content': self.responses[i]}}],
                'usage': {'prompt_tokens': p, 'completion_tokens': c, 'total_tokens': p+c}}


def run_matrix():
    t2.check_pins()
    selected, items, templates = t2.development_inputs()
    responses, response_tokens = t2.long_responses()
    raw = ROOT / 'research/sync/runs/hpc-masbench-t2-window-demand-20261125/outputs/window_demand.json'
    counts = json.loads(raw.read_bytes())
    assert counts['registry_sha256'] == t2.REGISTRY_SHA and counts['synthetic_response_tokens'] == response_tokens
    assert counts['smallest_test_candidate'] == 16384
    input_tokens = {row['request_sha256']: row['prompt_tokens'] for row in counts['rows']}
    episodes = []
    for number, entry in enumerate(selected, 1):
        for style in t2.FAMILIES:
            views = [private_view(items[entry['row']], name) for name in t2.NAMES]
            # Balance which condition goes first across the two prompts and four items.
            conditions = ('Full', 'No-A2A') if (number + t2.FAMILIES.index(style)) % 2 else ('No-A2A', 'Full')
            pair = []
            for condition in conditions:
                agents = [LocalAgent(view, templates[style]) for view in views]
                initial = [t2.digest(agent.request()) for agent in agents]
                pair.append(initial)
                backend = Replay(responses,input_tokens,response_tokens)
                config = ClientConfig(backend.model,backend.manifest,16384,max_output_tokens=512,max_calls=6)
                binding = ContextBinding(backend.manifest,16384,'offline-count-fixture','0'*64,True)
                audit_sizes = []
                client = ControlledClient(config,backend,lambda m:input_tokens[t2.digest(m)],binding,
                                          audit_sink=lambda entry: audit_sizes.append(len(canonical(entry))))
                transport = ContractTransport(episode_id=len(episodes)+1)
                outcome = run_controlled(agents,client,transport,style,max_turns=6,
                                         admit=lambda *_:condition=='Full')
                assert outcome['end_reason']=='turn_limit' and len(backend.requests)==6
                assert not outcome['error_flags'] and not outcome['usage_missing']
                next_proofs = []
                for index, (delivery, messages) in enumerate(zip(outcome['messages'][:-1],backend.requests[1:],strict=True)):
                    visible = delivery['body'].decode()
                    in_receiver = bool(visible) and any(item['content'].startswith(visible) for item in messages[1:])
                    assert in_receiver == (condition=='Full') == delivery['delivered']
                    next_proofs.append({'turn':index+1,'payload_sha256':delivery['payload_sha256'],
                                        'next_request_sha256':t2.digest(messages),'verified':in_receiver})
                wire = {'events':transport.events,'cpu':transport.cpu,'offers':transport.offers}
                sizes = [packet_size({'kind':'generate','messages':m}) for m in backend.requests]
                replies = [packet_size({'text':text,'audit':row}) for text,row in zip(responses,client.audit,strict=True)]
                terminal = packet_size({'kind':'result','value':outcome,'wire':wire})
                episodes.append({'case':number,'level':entry['level'],'style':style,'condition':condition,
                                 'id':f'{number:02d}-{style}-{condition}',
                                 'family_sha256':entry['family_sha256'],'private_view_sha256':digest([asdict(v) for v in views]),
                                 'initial_request_sha256':initial,'calls':len(sizes),'input_tokens':sum(
                                     input_tokens[t2.digest(m)] for m in backend.requests),
                                 'output_reserved_tokens':512*len(sizes),'max_request_packet_bytes':max(sizes),
                                 'max_broker_reply_bytes':max(replies),'completed_packet_bytes':terminal,
                                 'application_to_broker_bytes':sum(sizes)+terminal,'client_audit_bytes':sum(audit_sizes),
                                 'wire_frames':sum(e['event']=='frame' for e in transport.events),
                                 'receiver_next_request':next_proofs})
            assert pair[0] == pair[1]
    return episodes,hashlib.sha256(raw.read_bytes()).hexdigest()


def main():
    require_hpc()
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.environ['CUDA_VISIBLE_DEVICES']=''
    deny_network()
    episodes,demand_sha = run_matrix()
    assert len(episodes)==16 and len({row['family_sha256'] for row in episodes})==4
    assert sum(row['calls'] for row in episodes)==96
    score=summarize(['answer','failed','unstarted'],[
        {'id':'answer','gold':'blue','answer':'blue','end_reason':'answer'},
        {'id':'failed','gold':'blue','answer':None,'end_reason':'timeout'}])
    assert score['mean_F1_all']==score['EM_all_added']==.5 and score['N_not_started']==1
    value={'t2_demand_sha256':demand_sha,'episodes':episodes,'fixture_scoring_contract':True,
           'model_calls':0,'live_http':0,'real_prompt_exposed_to_model':0,
           'legacy_ipc':{'packet_limit':65536,'episode_limit':512*1024,
               'terminal_packets_over_limit':sum(r['completed_packet_bytes']>65536 for r in episodes),
               'episodes_over_cumulative_limit':sum(r['application_to_broker_bytes']>512*1024 for r in episodes)}}
    write_json(Path(os.environ['GOSC_OUTPUT_DIR'])/'t3_rehearsal.json',value)
    print(json.dumps({'episodes':len(episodes),'fixture_calls':96,'legacy_ipc':value['legacy_ipc'],
                      'maxima':{k:max(r[k] for r in episodes) for k in ('max_request_packet_bytes',
                          'max_broker_reply_bytes','completed_packet_bytes','application_to_broker_bytes')},
                      'real_generation':0}))


if __name__=='__main__':
    main()
