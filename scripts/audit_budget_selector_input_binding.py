"""Independent original-gzip-line binding, outside the frozen producer."""
import argparse
from collections import Counter,defaultdict,deque
import gzip
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def require(test,message):
    if not test:raise ValueError(message)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def bind_lines(samples,observed):
    """Key is original relative path and original one-based JSONL line."""
    seen=set()
    for sample in samples:
        loc=sample['locator'];key=loc['observation'],loc['line']
        require(key not in seen,'Duplicate sampled line');seen.add(key)
        require(key in observed and observed[key]==sample['decision'],'Detached original decision line')
        require(sample['decision']['event']=='decision' and sample['decision']['t']==loc['t']
                and sample['decision']['sender']==loc['sender'],'Locator time/sender')
        violation=sum(s['symbols'] for s in sample['decision']['selected'])>sample['decision']['budget']
        require(sample['kind']==('violation' if violation else 'feasible'),'Sample kind')


def verify(frozen_path):
    f=read(frozen_path);p=f['plan']
    for name,sha in f['source_sha256'].items():require(digest(ROOT/name)==sha,'Frozen source identity')
    result_path=ROOT/p['input_results'];diagnosis_path=ROOT/p['historical_diagnosis']
    require(digest(result_path)==p['input_results_sha256'] and digest(diagnosis_path)==p['historical_diagnosis_sha256'],'Original input SHA')
    original=read(result_path)
    require(original['frozen']['plan']==f['legacy_plan'],'Legacy plan changed')
    sample_path=frozen_path.parent/f['samples']['path']
    require(digest(sample_path)==f['samples_sha256']==f['samples']['sha256'],'Frozen sample SHA')
    with gzip.open(sample_path,'rt') as stream:samples=[json.loads(line) for line in stream]
    wanted={(s['locator']['observation'],s['locator']['line']) for s in samples}
    observed={};first=defaultdict(list);last=defaultdict(lambda:deque(maxlen=8));bad=[];inputs={}
    for row in original['rows']:
        relative=(result_path.parent/row['observation']['path']).relative_to(ROOT).as_posix()
        file=ROOT/relative;sha=digest(file)
        require(sha==row['observation']['sha256']==f['historical_observation_sha256'][relative],'Original gzip SHA')
        inputs[relative]=sha
        with gzip.open(file,'rt') as stream:
            for number,line in enumerate(stream,1):
                d=json.loads(line);key=relative,number
                if key in wanted:observed[key]=d
                if d['event']!='decision' or d['groups_before_age'] is None:continue
                if sum(x['symbols'] for x in d['selected'])>d['budget']:bad.append(key)
                else:
                    if len(first[row['case_id']])<8:first[row['case_id']].append(key)
                    last[row['case_id']].append(key)
    bind_lines(samples,observed)
    expected=set(bad)
    for case in original['frozen']['cases']:
        if case['mode']!='periodic':expected.update(first[case['id']]+list(last[case['id']]))
    require(wanted==expected and len(samples)==199 and len(bad)==7,'Deterministic first/last sample coverage')
    # Also bind case and seed to the original row owning the gzip, not producer labels.
    owners={(result_path.parent/r['observation']['path']).relative_to(ROOT).as_posix():(r['seed'],r['case_id']) for r in original['rows']}
    for s in samples:
        loc=s['locator'];require((loc['seed'],loc['case_id'])==owners[loc['observation']],'Sample owner')
    return dict(status='passed',scope='Independent immutable original-line and deterministic sample binding only',
        samples=len(samples),historical_violations=len(bad),original_files=len(inputs),
        frozen_sha256=digest(frozen_path),source_sha256=digest(Path(__file__)),sample_sha256=digest(sample_path),
        results_sha256=digest(result_path),efficacy_N=0)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--frozen',type=Path,required=True);a=p.parse_args()
    require(os.name=='posix' and os.getuid()==8301880 and str(ROOT)=='/home/u202520081000097/jupyterlab/Paper/gosc'
            and os.environ.get('GOSC_OUTPUT_DIR'),'Registered HPC only')
    report=verify(a.frozen)
    with (Path(os.environ['GOSC_OUTPUT_DIR'])/'binding.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report))


if __name__=='__main__':main()
