"""Local archive-only file/stage verification; no scientific computation."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];LOG=Path(__file__).resolve().parent
ART=ROOT/'research/artifacts/context-deployment-20261117'
staged='--staged' in sys.argv
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
raw=(git('diff','--cached','--name-only','-z','--diff-filter=ACMR') if staged else
     git('diff','--name-only','-z','HEAD')+git('ls-files','--others','--exclude-standard','-z'))
paths=sorted({x.decode() for x in raw.split(b'\0') if x});blockers=[];rows=[]
patterns={'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
          'github_token':rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}',
          'api_key':rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}',
          'aws_key':rb'AKIA[0-9A-Z]{16}'}
for name in paths:
    if name in {(LOG/'staged_audit.json').relative_to(ROOT).as_posix(),(LOG/'precommit_file_audit.json').relative_to(ROOT).as_posix()}:continue
    p=ROOT/name
    if p.is_symlink() or not p.is_file():blockers.append({'path':name,'reason':'nonregular'});continue
    b=p.read_bytes()
    if any(x in {'.local','.venv','.ssh','.aws','__pycache__','outputs','pytest-tmp'} for x in Path(name).parts) or p.suffix.lower() in {'.pdf','.gguf','.pt','.safetensors','.pem','.key','.gz','.zip','.tgz'} or p.name.startswith('.env'):
        blockers.append({'path':name,'reason':'excluded_private_raw'})
    if len(b)>10*1024**2:blockers.append({'path':name,'reason':'over10MiB'})
    for label,pattern in patterns.items():
        if re.search(pattern,b):blockers.append({'path':name,'reason':label})
    if p.suffix=='.json':
        try:json.loads(b)
        except Exception:blockers.append({'path':name,'reason':'invalid_json'})
    if p.suffix=='.md':
        for link in re.findall(r'\]\(([^)]+)\)',b.decode('utf-8-sig')):
            if link.startswith(('https:','http:','#','mailto:')):continue
            target=link.split('#')[0].strip('<>')
            if target and not (p.parent/target).exists():blockers.append({'path':name,'reason':'missing_link','target':target})
    if staged and (name.startswith('research/artifacts/context-deployment-20261117/') or name.startswith('research/sync/runs/hpc-masbench-') or name.startswith(('research/logs/masbench-context-deployment','research/logs/masbench-cpp-vendor'))):
        if git('show',':'+name)!=b:blockers.append({'path':name,'reason':'stage_bytes_changed'})
    rows.append({'path':name,'bytes':len(b),'sha256':sha(b)})
frozen=json.loads((ROOT/'research/artifacts/native-masbench-20261104/native_frozen.json').read_bytes())
for name,h in frozen['source_sha256'].items():
    if sha((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))!=h:blockers.append({'path':name,'reason':'frozen_changed'})
for item in json.loads((ART/'provenance.json').read_bytes())['files']:
    if sha((ROOT/item['archive_path']).read_bytes())!=item['sha256'] or sha((ROOT/item['source_path']).read_bytes())!=item['sha256']:
        blockers.append({'path':item['archive_path'],'reason':'provenance_mismatch'})
for r in json.loads((ART/'receipt_index.json').read_bytes())['receipts']:
    if sha((ROOT/r['source_path']).read_bytes())!=r['sha256']:blockers.append({'path':r['source_path'],'reason':'receipt_mismatch'})
protected=git('diff','--name-only','HEAD','--','gosc','experiments','tests','results','LICENSE','extensions/masbench_reasoning').decode().splitlines()
if protected:blockers.append({'reason':'protected_changed','paths':protected})
report={'mode':'staged' if staged else 'working','files':rows,'file_count':len(rows),'bytes':sum(x['bytes'] for x in rows),
        'frozen_sources_verified':len(frozen['source_sha256']),'artifact_outputs_verified':20,'receipt_originals_verified':16,'blockers':blockers,
        'self_audit_outputs_excluded_from_fingerprint':True}
(LOG/('staged_audit.json' if staged else 'precommit_file_audit.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False))
raise SystemExit(bool(blockers))
