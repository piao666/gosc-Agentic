"""Archive whitespace policy: preserve immutable raw CRLF and upstream bytes."""
from pathlib import Path
import json,subprocess,re,hashlib
ROOT=Path(__file__).resolve().parents[3];LOG=Path(__file__).resolve().parent
cmd=['git','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check']
p=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
lines=p.stdout.decode(errors='replace').splitlines()
locations=[x for x in lines if re.match(r'^.+:\d+: ',x)]
exceptions=[];unexpected=[]
for line in locations:
    path=line.rsplit(':',2)[0]
    if path.startswith(('research/logs/masbench-context-deployment-2026-11-16/source_reference/',
                        'research/logs/masbench-cpp-vendor-2026-11-16/source_reference_',
                        'research/sync/runs/')):exceptions.append(line)
    else:unexpected.append(line)
report={'command':cmd,'exit_code':p.returncode,'raw_crlf_policy':'cr-at-eol; stage bytes unchanged',
        'raw_source_log_exceptions':exceptions,'unexpected':unexpected,
        'full_output_sha256':hashlib.sha256(p.stdout).hexdigest(),'full_output_bytes':len(p.stdout)}
(LOG/'whitespace_check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report));raise SystemExit(bool(unexpected))
