"""Local Git/file management only: sizes, credential patterns, archive members."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[3]
LOG=Path(__file__).resolve().parent
PATTERNS={
    'private_key':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'github_token':re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    'openai_token':re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{30,}'),
    'aws_access_id':re.compile(rb'\bAKIA[A-Z0-9]{16}\b'),
}


def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def names(raw):return [x.decode('utf-8') for x in raw.split(b'\0') if x]
def digest(data):return hashlib.sha256(data).hexdigest()
def unsafe(name):
    p=PurePosixPath(name)
    return (p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name
        or any(x in {'.ssh','.aws','.venv','.env','models','node_modules'} for x in p.parts)
        or p.name.startswith('.env.') and p.name!='.env.example'
        or p.suffix.lower() in {'.pem','.key','.p12','.pfx','.pdf'})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--staged',action='store_true');a=parser.parse_args()
    if a.staged:
        paths=names(git('diff','--cached','--name-only','-z'))
    else:
        paths=sorted(set(names(git('diff','--name-only','-z','HEAD'))+names(git('ls-files','--others','--exclude-standard','-z'))))
    findings=[];rows=[];archives=[];scanned=set();total=0;byte_checks=0
    for name in paths:
        path=ROOT/name
        if unsafe(name) or '/outputs/' in name or '/pytest-tmp/' in name:
            findings.append(dict(path=name,reason='Sensitive/ignored/unsafe candidate path'));continue
        if name.split('/')[0] in {'gosc','experiments','tests','results'} or name=='LICENSE':
            findings.append(dict(path=name,reason='Protected upstream path'));continue
        if not path.is_file():findings.append(dict(path=name,reason='Deletion/non-file'));continue
        data=path.read_bytes();sha=digest(data);total+=len(data)
        if len(data)>=50*1024*1024:findings.append(dict(path=name,reason='At least50MiB'))
        row=dict(path=name,bytes=len(data),sha256=sha);rows.append(row)
        if sha not in scanned:
            scanned.add(sha)
            for label,pattern in PATTERNS.items():
                if pattern.search(data):findings.append(dict(path=name,reason=label))
            if name.endswith('.tar.gz'):
                members=[]
                with tarfile.open(path,'r:gz') as archive:
                    for member in archive.getmembers():
                        if unsafe(member.name) or not member.isfile():
                            findings.append(dict(path=name,member=member.name,reason='Unsafe archive member'));continue
                        raw=archive.extractfile(member).read()
                        for label,pattern in PATTERNS.items():
                            if pattern.search(raw):findings.append(dict(path=name,member=member.name,reason=label))
                        members.append(dict(path=member.name,bytes=len(raw),sha256=digest(raw)))
                archives.append(dict(path=name,members=members))
        evidence=name.startswith(('research/sync/runs/','research/sync/receipts/','research/artifacts/gp-id-bf-20261027/'))
        if a.staged and evidence:
            staged=git('show',':'+name)
            if digest(staged)!=sha:findings.append(dict(path=name,reason='Evidence staged bytes differ'))
            byte_checks+=1
    report=dict(status='passed' if not findings else 'blocked',mode='staged' if a.staged else 'candidate',
        file_count=len(rows),total_bytes=total,largest=sorted(rows,key=lambda x:x['bytes'],reverse=True)[:5],
        unique_contents_scanned=len(scanned),evidence_byte_checks=byte_checks,findings=findings,files=rows,
        archives=archives,scope='Git/file management, high-confidence patterns and paths only; not an absolute confidentiality guarantee; self audit written after snapshot')
    output=LOG/('staged_audit.json' if a.staged else 'precommit_file_audit.json')
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','mode','file_count','total_bytes','unique_contents_scanned','evidence_byte_checks','findings')}))
    if findings:raise SystemExit(1)


if __name__=='__main__':main()
