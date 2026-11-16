"""Local Git/file archival audit, not a project test or scientific analysis."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[3]
LOG=Path(__file__).resolve().parent
ART=ROOT/'research/artifacts/masbench-b1-20261116'


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--staged',action='store_true');a=parser.parse_args()
    raw=(git('diff','--cached','--name-only','-z','--diff-filter=ACMR') if a.staged else
         git('diff','--name-only','-z','HEAD')+git('ls-files','--others','--exclude-standard','-z'))
    paths=sorted({x.decode() for x in raw.split(b'\0') if x})
    result_name='staged_audit.json' if a.staged else 'precommit_file_audit.json'
    self_path=(LOG/result_name).relative_to(ROOT).as_posix()
    inventory=[];blockers=[]
    patterns={'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
              'github_token':rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}',
              'api_key':rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}',
              'aws_access_key':rb'AKIA[0-9A-Z]{16}',
              'bearer_literal':rb'Bearer [A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'}
    added=set(x.decode() for x in git('diff','--cached','--name-only','--diff-filter=A','-z').split(b'\0') if x) if a.staged else set(x.decode() for x in git('ls-files','--others','--exclude-standard','-z').split(b'\0') if x)
    for name in paths:
        if name==self_path:continue
        p=ROOT/name
        if not p.is_file() or p.is_symlink():blockers.append({'path':name,'reason':'missing_or_symlink'});continue
        if (any(x in {'.ssh','.aws','.local','.venv','__pycache__'} for x in p.relative_to(ROOT).parts)
                or p.name=='.env' or (p.name.startswith('.env.') and p.name!='.env.example')
                or p.suffix.lower() in {'.pdf','.gguf','.safetensors','.pt','.pem','.key','.p12','.gz','.tgz','.zip'}
                or '/outputs/' in name or '.partial-' in name or p.name=='source_changes.patch'):
            blockers.append({'path':name,'reason':'excluded_private_or_raw_artifact'})
        data=p.read_bytes()
        if len(data)>10*1024*1024:blockers.append({'path':name,'reason':'file_over_10MiB'})
        for label,pattern in patterns.items():
            if re.search(pattern,data):blockers.append({'path':name,'reason':label})
        if name in added and p.suffix=='.md':
            text=data.decode('utf-8-sig')
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith(('https:','http:','#','mailto:')):continue
                target=link.split('#')[0].strip('<>')
                if target and not (p.parent/target).exists():blockers.append({'path':name,'reason':'missing_markdown_target','target':target})
        inventory.append({'path':name,'bytes':len(data),'sha256':sha(data)})
    protected=git('diff','--name-only','HEAD','--','gosc','experiments','tests','results','LICENSE').decode().splitlines()
    if protected:blockers.append({'reason':'protected_upstream_changed','paths':protected})
    frozen=json.loads((ROOT/'research/artifacts/native-masbench-20261104/native_frozen.json').read_bytes())
    for name,h in frozen['source_sha256'].items():
        if sha((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))!=h:blockers.append({'path':name,'reason':'frozen_source_changed'})
    snap=json.loads((ROOT/'research/sync/runs/hpc-masbench-b1-integration-v4-20261110/source_snapshot.json').read_bytes())
    rows={x['path']:x for x in snap['files']}
    tested=['extensions/masbench_reasoning/fixture_driver.py','tests_ext/test_masbench_fixture_driver.py','experiments_ext/masbench_b1_integration_contract.py']
    for name in tested:
        if sha((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))!=rows[name]['remote_sha256']:blockers.append({'path':name,'reason':'final_test_snapshot_mismatch'})
    provenance=json.loads((ART/'provenance.json').read_bytes())
    for e in provenance['files']:
        if sha((ROOT/e['archive_path']).read_bytes())!=e['sha256'] or sha((ROOT/e['source_path']).read_bytes())!=e['sha256']:
            blockers.append({'path':e['archive_path'],'reason':'whitelist_source_mismatch'})
    receipt_index=json.loads((ART/'receipt_index.json').read_bytes())
    for r in receipt_index['receipts']:
        if sha((ROOT/r['source_path']).read_bytes())!=r['sha256']:
            blockers.append({'path':r['source_path'],'reason':'full_receipt_fingerprint_mismatch'})
    note=ROOT/'commit/2026-11-16-01-masbench-b1-safety-and-delivery.md'
    content=note.read_text(encoding='utf-8');positions=[]
    for title in ['## 1. 提交内容','## 2. 主要尝试','## 3. 结果','## 4. 当前进展','## 5. 下一步安排']:
        positions.append(content.find(title))
    if min(positions)<0 or positions!=sorted(positions):blockers.append({'reason':'commit_note_format'})
    exact=[]
    if a.staged:
        staged={}
        for row in git('ls-files','--stage','-z').split(b'\0'):
            if not row:continue
            meta,name=row.split(b'\t',1);staged[name.decode()]=meta.split()[1].decode()
        evidence=[p for p in paths if p in added and p!=self_path]
        hashes=[] if not evidence else subprocess.check_output(
            ['git','hash-object','--no-filters','--stdin-paths'],cwd=ROOT,input=('\n'.join(evidence)+'\n').encode()).decode().splitlines()
        assert len(hashes)==len(evidence)
        for name,h in zip(evidence,hashes):
            if staged[name]!=h:blockers.append({'path':name,'reason':'stage_raw_bytes_differ'})
            exact.append(name)
        deleted=git('diff','--cached','--name-only','--diff-filter=D').decode().splitlines()
        if deleted:blockers.append({'reason':'unexpected_deletions','paths':deleted})
    result={'scope':'Git and lightweight file/hash management only; no tests or models',
            'base_head':git('rev-parse','HEAD').decode().strip(),'staged':a.staged,
            'file_count':len(inventory),'bytes':sum(x['bytes'] for x in inventory),
            'largest_file_bytes':max((x['bytes'] for x in inventory),default=0),
            'blockers':blockers,'frozen_sources_checked':len(frozen['source_sha256']),
            'new_driver_source_vs_final_HPC_snapshot':tested,'whitelist_outputs_checked':len(provenance['files']),
            'compact_receipt_sources_checked':len(receipt_index['receipts']),
            'new_raw_stage_blobs_checked':len(exact),'sensitive_scan':'high-confidence path/key patterns, not an absolute absence guarantee',
            'self_result_excluded':True,'inventory':inventory}
    (LOG/result_name).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='inventory'},ensure_ascii=False))
    if blockers:raise SystemExit(1)


if __name__=='__main__':main()
