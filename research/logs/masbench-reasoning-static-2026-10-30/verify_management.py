"""File/Git/JSON/link verification only. Does not import a benchmark or compute task statistics."""
import datetime
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
LOG=Path(__file__).resolve().parent


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def sha(path,lf=False):
    data=(ROOT/path).read_bytes()
    if lf:data=data.replace(b'\r\n',b'\n')
    return hashlib.sha256(data).hexdigest()


def git(*args):
    p=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    if p.returncode:raise RuntimeError((args,p.returncode,p.stderr))
    return p.stdout.strip()


def write(name,data):
    (LOG/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


head=git('rev-parse','HEAD')
if head!='014b85dfc472c45d8ea5f15e83e0c1ed8e938daf':raise RuntimeError('HEAD changed')
frozen=read('research/sync/runs/hpc-native-information-freeze-20261030/outputs/frozen.json')
source_changes=[p for p,v in frozen['source_sha256'].items() if sha(p,True)!=v]
if source_changes:raise RuntimeError(('Frozen scientific source changed',source_changes))
accepted={
    'research/protocols/native_information_value_spec_v1.md':'4e961bd8b3f7ac41064c796d70f719fec39e0ad8145db93e80afda1a5d4db125',
    'research/reports/native_information_feasibility_review_2026-10-30.md':'7d2eee3d88faefa1d40ac930ffa01c673febfadce55006359b00fe16e4c8131b'}
prior=read('research/logs/candidate-task-review-2026-10-30/experiment_manifest.json')
protected={**accepted,**{p:v for p,v in prior['inputs_sha256'].items() if p.startswith('research/reports/')},
    **{p:v for p,v in prior['outputs_sha256'].items() if p.startswith('research/reports/')}}
changed=[p for p,v in protected.items() if sha(p)!=v]
if changed:raise RuntimeError(('Previous evidence changed',changed))
git('diff','--exit-code','HEAD','--','gosc','extensions','tests','tests_ext','scripts')
git('diff','--check')
reports=[ROOT/'research/benchmarks'/n for n in [
    'masbench_reasoning_adapter_spec_v1.md','masbench_reasoning_feasibility_review.md','masbench_reasoning_gate_matrix.md']]
docs=reports+sorted(LOG.glob('*.md'))
missing=[];whitespace=[]
for path in docs:
    body=path.read_text(encoding='utf-8')
    for link in re.findall(r'\]\(([^)]+)\)',body):
        if '://' not in link and not (path.parent/link.split('#')[0]).exists():
            missing.append(dict(path=str(path.relative_to(ROOT)),link=link))
    for i,line in enumerate(body.splitlines(),1):
        if line!=line.rstrip():whitespace.append(dict(path=str(path.relative_to(ROOT)),line=i))
if missing or whitespace:raise RuntimeError(('Document checks',missing,whitespace))
for path in LOG.glob('*.json'):json.loads(path.read_text(encoding='utf-8'))
source_index=read('research/logs/masbench-reasoning-static-2026-10-30/source_index_supplement.json')
if not all(r['metadata_sha_matches'] and r['content_observed'] for r in source_index['source_file_metadata']):
    raise RuntimeError('Third-party file metadata verification incomplete')
inventory=read('research/logs/masbench-reasoning-static-2026-10-30/environment_inventory.json')
remote=inventory['hpc'].get('inventory')
if remote and (remote['uid']!=8301880 or remote['git_head']['stdout']!=head or remote['inference_requested']):
    raise RuntimeError('Read-only inventory identity/scope')
write('experiment_manifest.json',dict(
    date='2026-10-30',task='MASBench Reasoning static adapter specification and feasibility',
    baseline_commit=head,branch=git('branch','--show-current'),remote=git('remote','-v'),
    working_tree_status=git('status','--short'),
    third_party_commit=source_index['commit'],third_party_source_index='source_index.json',
    local_python=dict(executable=sys.executable,version=platform.python_version(),purpose='documentation management only'),
    hpc_activity='Read-only Python package/resource/HTTP inventory only; no scientific run',
    scientific_runs=[],tests_run=False,llm_calls=0,training=False,new_samples=0,
    paid_api=False,dependencies_installed=False,models_downloaded=False,benchmark_integrated=False,
    algorithms_modified=False,hpc_source_sync=False,git_commit_or_push=False,
    old_scientific_status='G1 and GP-ID No-Go retained',current_execution_status='Blocked/No-Go; model and dependencies not ready, data and contracts Pending',
    protected_previous_report_sha256=protected,
    output_document_sha256={p.relative_to(ROOT).as_posix():sha(p.relative_to(ROOT)) for p in docs},
    environment_inventory_sha256=sha(LOG.relative_to(ROOT)/'environment_inventory.json'),
    model_storage_inventory_sha256=sha(LOG.relative_to(ROOT)/'model_storage_stdout.json'),
    finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
write('verification.json',dict(
    scope='Local file/Git/JSON/link management, not project tests or scientific data analysis',
    baseline_head=head,frozen_scientific_file_count=len(frozen['source_sha256']),
    frozen_source_mismatches=source_changes,protected_previous_evidence_changes=changed,
    external_source_files_metadata_matched=len(source_index['source_file_metadata']),
    data_body_or_record_count_verified=False,model_capability_verified=False,
    missing_local_links=missing,trailing_whitespace=whitespace,git_diff_check_exit_code=0,
    protected_tracked_source_diff_exit_code=0,new_tests_run=False,new_scientific_runs=[],
    reports=[p.relative_to(ROOT).as_posix() for p in reports]))
write('actual_commands.json',dict(
    local_read_management=['git status --short','git rev-parse HEAD','git remote -v',
        'Get-Content AGENTS.md / README.md / research workspace and prior task/reproduction records',
        'Get-Content 硕士论文研究与实施说明书.md (research-question section; full manual inherited from preceding review)',
        'python research/logs/masbench-reasoning-static-2026-10-30/readonly_environment.py',
        'python research/logs/masbench-reasoning-static-2026-10-30/readonly_model_storage.py',
        'python research/logs/masbench-reasoning-static-2026-10-30/verify_management.py',
        'git diff --exit-code HEAD -- gosc extensions tests tests_ext scripts','git diff --check'],
    ssh_readonly=inventory['command'],ssh_payload_sources=['readonly_environment.py','readonly_model_storage.py'],
    external_reads=['GitHub connector GET branch/tree and pinned Reasoning files listed in source_index*.json',
        'web open/find pinned arXiv Reasoning sections; dataset GitHub web request failed cache miss'],
    scientific_commands=[],model_generation_requests=[],hpc_registered_runs=[],
    file_edits='apply_patch: new three benchmark documents, management logs and research/README entry only'))
print(json.dumps(dict(status='management_checks_passed',frozen_sources_unchanged=True,
    previous_reports_unchanged=True,local_links_ok=True,project_tests_run=False,llm_calls=0)))
