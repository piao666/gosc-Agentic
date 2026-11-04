"""Local precommit/staged file, provenance and sensitive-path management audit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[3]
LOG=Path(__file__).resolve().parent


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--staged',action='store_true');args=parser.parse_args()
    if args.staged:
        raw=git('diff','--cached','--name-only','-z','--diff-filter=ACMR')
    else:
        raw=git('diff','--name-only','-z','HEAD')+git('ls-files','--others','--exclude-standard','-z')
    paths=sorted(set(x.decode('utf-8') for x in raw.split(b'\0') if x))
    blockers=[];inventory=[]
    patterns={
      'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
      'github_token':rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}',
      'openai_key':rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}',
      'aws_access_key':rb'AKIA[0-9A-Z]{16}',
      'bearer_token_literal':rb'Bearer [A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'}
    for name in paths:
        if name=='research/logs/git-publish-2026-11-04/staged_audit.json':
            continue  # Generated audit result does not hash or scan itself.
        p=ROOT/name
        if not p.exists() or p.is_symlink():
            blockers.append({'path':name,'reason':'deletion_or_symlink'});continue
        parts=Path(name).parts
        if (any(s in {'.ssh','.local','.venv','__pycache__'} for s in parts)
                or p.name=='.env' or (p.name.startswith('.env.') and p.name!='.env.example')
                or p.suffix.lower() in {'.pdf','.gguf','.safetensors','.pt','.pem','.p12','.tgz','.gz','.zip'}
                or '/outputs/' in name or '.partial-' in name or p.name=='source_changes.patch'):
            blockers.append({'path':name,'reason':'excluded_artifact_or_private_path'})
        data=p.read_bytes()
        if len(data)>=50*1024*1024:blockers.append({'path':name,'reason':'file_at_least_50MiB'})
        for label,pattern in patterns.items():
            if re.search(pattern,data):blockers.append({'path':name,'reason':label})
        inventory.append({'path':name,'bytes':len(data),'sha256':sha(data)})
    protected=git('diff','--name-only','HEAD','--','gosc','experiments','tests','results','LICENSE').strip()
    if protected:blockers.append({'reason':'protected_upstream_changed','paths':protected.decode().splitlines()})
    frozen=json.loads((ROOT/'research/sync/runs/hpc-native-information-freeze-20261030/outputs/frozen.json').read_text())
    assert all(sha((ROOT/p).read_bytes().replace(b'\r\n',b'\n'))==h for p,h in frozen['source_sha256'].items())
    provenance=json.loads((ROOT/'research/artifacts/native-masbench-20261104/provenance.json').read_text())
    for entry in provenance['files']:
        assert sha((ROOT/entry['archive_path']).read_bytes())==entry['sha256']
        assert sha((ROOT/entry['source_path']).read_bytes())==entry['sha256']
    exact=[]
    if args.staged:
        staged={}
        for record in git('ls-files','--stage','-z').split(b'\0'):
            if not record:continue
            metadata,name=record.split(b'\t',1)
            mode,obj,stage=metadata.split()
            staged[name.decode()]=obj.decode()
        added=set(x.decode() for x in git('diff','--cached','--name-only','--diff-filter=A','-z').split(b'\0') if x)
        evidence=[p for p in paths if
                  (p in added or p.startswith(('research/sync/runs/','research/sync/receipts/','research/artifacts/native-masbench-20261104/')))
                  and p!='research/logs/git-publish-2026-11-04/staged_audit.json']
        r=subprocess.run(['git','hash-object','--no-filters','--stdin-paths'],cwd=ROOT,
                         input=('\n'.join(evidence)+'\n').encode(),capture_output=True,check=True)
        hashes=r.stdout.decode().splitlines()
        assert len(hashes)==len(evidence)
        for name,digest in zip(evidence,hashes):
            if staged[name]!=digest:blockers.append({'path':name,'reason':'staged_evidence_bytes_differ'})
            exact.append(name)
        deletions=git('diff','--cached','--name-only','--diff-filter=D').decode().splitlines()
        if deletions:blockers.append({'reason':'unexpected_deletions','paths':deletions})
    value={'scope':'Git/file management only; no scientific computation',
           'baseline':git('rev-parse','HEAD').decode().strip(),'staged':args.staged,
           'files':len(inventory),'bytes':sum(x['bytes'] for x in inventory),
           'largest_file_bytes':max((x['bytes'] for x in inventory),default=0),
           'blockers':blockers,'immutable_staged_evidence_files_checked':len(exact),
           'frozen_sources_unchanged':len(frozen['source_sha256']),
           'whitelist_artifacts_checked':len(provenance['files']),
           'sensitive_scan_scope':'high-confidence token/key patterns and private/large paths; not an absolute absence guarantee',
           'self_audit_result_excluded':True,
           'inventory':inventory}
    target=LOG/('staged_audit.json' if args.staged else 'precommit_file_audit.json')
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in value.items() if k not in {'inventory'}}))
    if blockers:raise SystemExit(1)


if __name__=='__main__':main()
