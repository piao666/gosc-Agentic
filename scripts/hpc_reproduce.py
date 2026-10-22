"""Bounded HPC-only environment, upstream tests, stored-data replot and one mission."""
from pathlib import Path
import argparse
import dataclasses
import gzip
import hashlib
import json
import os
import platform
import shutil
import subprocess
import time

from hpc_runs import ROOT, require_hpc, write_json


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def snapshot():
    return {p.relative_to(ROOT).as_posix(): sha(p)
            for folder in ['gosc', 'experiments', 'tests', 'results']
            for p in sorted((ROOT/folder).rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'} | {'LICENSE': sha(ROOT/'LICENSE')}


def command(argv, out, label, timeout, cwd=ROOT):
    started = time.monotonic()
    env = os.environ.copy()
    env['MPLCONFIGDIR'] = str(out/'mplconfig')
    env['PYTHONPATH'] = str(cwd)
    with (out/(label+'.stdout.log')).open('wb') as stdout, (out/(label+'.stderr.log')).open('wb') as stderr:
        try:
            result = subprocess.run([str(x) for x in argv], cwd=cwd, env=env,
                                    stdout=stdout, stderr=stderr, timeout=timeout)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    steps = out/'commands.json'
    rows = json.loads(steps.read_text()) if steps.exists() else []
    rows.append({'argv': [str(x) for x in argv], 'cwd': str(cwd), 'exit_code': code,
                 'elapsed_seconds': time.monotonic()-started, 'timeout_seconds': timeout})
    write_json(steps, rows)
    print(label, 'exit', code, flush=True)
    if code:
        raise RuntimeError(label+' failed; inspect preserved stdout/stderr; exit '+str(code))
    return (out/(label+'.stdout.log')).read_text(errors='replace')


def environment(c, out):
    uv = Path.home()/'.local/bin/uv'
    runtime = c['runtime_python']
    venv = ROOT/'.venv'
    lock = out/'requirements-linux.lock.txt'
    command([uv, 'pip', 'compile', ROOT/'requirements.txt', '--python', runtime,
             '--only-binary', ':all:', '--generate-hashes', '--output-file', lock], out, 'resolve', 240)
    if venv.exists():
        raise RuntimeError('Existing .venv must be inspected; refusing to replace or mutate it automatically')
    command([uv, 'venv', '--python', runtime, venv], out, 'create-venv', 60)
    python = venv/'bin/python'
    command([uv, 'pip', 'sync', '--python', python, '--require-hashes', '--only-binary', ':all:', lock], out, 'install', 300)
    command([uv, 'pip', 'check', '--python', python], out, 'dependency-check', 60)
    frozen = command([uv, 'pip', 'freeze', '--python', python], out, 'freeze', 60)
    (out/'requirements-linux.freeze.txt').write_text(frozen)
    probe = "import sys,platform,json;from importlib.metadata import distributions;import numpy,matplotlib,pytest; print(json.dumps({'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':{p.metadata['Name']:p.version for p in distributions()}}))"
    details = json.loads(command([python, '-c', probe], out, 'environment-probe', 60))
    details.update(status='ready', lock_path=str(lock.relative_to(ROOT)), lock_sha256=sha(lock),
                   uv_version=subprocess.check_output([str(uv), '--version']).decode().strip(),
                   note='No model downloads, global Python changes or GPU workloads.')
    write_json(out/'environment.json', details)
    write_json(ROOT/'.local/reproduction-environment.json', details)


def copy_environment(out):
    src = ROOT/'.local/reproduction-environment.json'
    details = json.loads(src.read_text())
    python = Path(details['executable'])
    lock = ROOT/details['lock_path']
    if not python.is_file() or sha(lock) != details['lock_sha256']:
        raise RuntimeError('Verified project environment is missing or lock has changed')
    shutil.copyfile(src, out/'environment.json')
    shutil.copyfile(lock, out/'requirements-linux.lock.txt')
    return python


def tests(python, out, run_dir):
    command([python, '-m', 'pytest', '--collect-only', '-q', 'tests', '-p', 'no:cacheprovider'], out, 'collect', 180)
    command([python, '-m', 'pytest', '-q', 'tests', '-p', 'no:cacheprovider',
             '--basetemp', run_dir/'pytest-tmp', '--junitxml', out/'pytest.xml'], out, 'pytest', 600)
    import xml.etree.ElementTree as ET
    suites = ET.parse(out/'pytest.xml').getroot()
    leaves = [s for s in suites.iter('testsuite')]
    result = {k: sum(int(s.attrib.get(k, 0)) for s in leaves) for k in ['tests', 'failures', 'errors', 'skipped']}
    result['status'] = 'passed' if not result['failures'] and not result['errors'] else 'failed'
    write_json(out/'test_summary.json', result)
    print(json.dumps(result), flush=True)


def replot(python, out, run_dir):
    work = ROOT/'.local/reproduction-workspaces'/run_dir.name
    work.mkdir(parents=True, exist_ok=False)
    for name in ['gosc', 'experiments', 'results']:
        shutil.copytree(ROOT/name, work/name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    decompressed = []
    for p in sorted((work/'results').glob('*.jsonl.gz')):
        dest = p.with_suffix('')
        if dest.exists():
            raise RuntimeError('Unexpected pre-existing decompressed input: '+str(dest))
        with gzip.open(p, 'rb') as src, dest.open('wb') as dst:
            shutil.copyfileobj(src, dst)
        decompressed.append({'path': dest.name, 'size': dest.stat().st_size, 'sha256': sha(dest)})
    steps = ['plot', 'plot_revision', 'plot_realistic']
    for module in steps:
        text = command([python, '-m', 'experiments.'+module], out, module, 600, cwd=work)
        if 'skipping ' in text or '\nskip ' in '\n'+text:
            raise RuntimeError('Replot skipped a section; inspect '+module+' logs')
    command([python, '-m', 'experiments.run_belief_divergence', '--table'],
            out, 'fill-table-vi', 600, cwd=work)
    shutil.copytree(work/'figures', out/'figures')
    summaries = out/'summaries'
    summaries.mkdir()
    comparisons = {}
    def equal(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            return set(a)==set(b) and all(equal(a[k], b[k]) for k in a)
        if isinstance(a, list) and isinstance(b, list):
            return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
        if isinstance(a, (int,float)) and isinstance(b, (int,float)):
            import math
            return (math.isnan(a) and math.isnan(b)) or math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
        return a==b
    for name in ['summary.json', 'summary_revision.json', 'summary_realistic.json']:
        p = work/'results'/name
        shutil.copyfile(p, summaries/name)
        baseline = ROOT/'results'/name
        reference = baseline.read_bytes() if baseline.is_file() else None
        provenance = 'current tracked input'
        if reference is None:
            result = subprocess.run(['git', '-C', str(ROOT), 'show', 'upstream-gosc-387b493:results/'+name], capture_output=True)
            if result.returncode == 0:
                reference = result.stdout
                provenance = 'upstream-gosc-387b493 Git object (read only)'
        comparisons[name] = {'reference': provenance if reference else 'not available',
                             'numerically_equal_at_1e-10': equal(json.loads(reference), json.loads(p.read_bytes())) if reference else None}
    figures = list((out/'figures').glob('*.pdf'))
    tables = list((out/'figures').glob('*.tex'))
    assert figures and tables
    write_json(out/'replot_summary.json', {'status': 'completed', 'modules': steps,
               'pdf_count': len(figures), 'tex_count': len(tables), 'table_completion_module': 'experiments.run_belief_divergence --table', 'decompressed_inputs': decompressed,
               'summary_comparisons': comparisons, 'workspace': str(work),
               'scope': 'Stored upstream results reanalysis only; no new simulations, model calls or paper-PDF visual/numerical verification.'})
    print(json.dumps({'pdf_count': len(figures), 'tex_count': len(tables), 'summary_comparisons': comparisons}), flush=True)


def mission(python, out, seed):
    code = '''from pathlib import Path
import dataclasses,json,sys,time
from gosc import Config,run_episode
out=Path(sys.argv[1]);seed=int(sys.argv[2]);cfg=Config()
assert not cfg.llm_agents
t=time.monotonic();result=run_episode(cfg,'gosc',seed,record_traj=True)
assert len(result['curve'])==cfg.max_steps
assert 0<result['completion_time']<=cfg.max_steps
assert 0<=result['found']<=cfg.n_victims
assert result['symbols']>=0 and result['bits']>=0
(out/'mission.json').write_text(json.dumps({'scheme':'gosc','seed':seed,'config':dataclasses.asdict(cfg),'elapsed_seconds':time.monotonic()-t,'result':result},indent=2))
print(json.dumps({k:result[k] for k in ['completed','completion_time','found','symbols','bits','false_declarations']}))
'''
    command([python, '-c', code, out, seed], out, 'single-mission', 180)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['environment', 'r1', 'r2', 'r3'])
    p.add_argument('--seed', type=int, default=3000)
    args = p.parse_args()
    c = require_hpc()
    out = Path(os.environ['GOSC_OUTPUT_DIR']).resolve()
    run_dir = Path(os.environ['GOSC_RUN_DIR']).resolve()
    assert run_dir.parent == ROOT/'research/sync/runs' and out == run_dir/'outputs'
    before = snapshot()
    write_json(out/'input_integrity.json', {'before': before})
    try:
        if args.stage == 'environment':
            environment(c, out)
        else:
            python = copy_environment(out)
            if args.stage == 'r1': tests(python, out, run_dir)
            elif args.stage == 'r2': replot(python, out, run_dir)
            else: mission(python, out, args.seed)
    finally:
        after = snapshot()
        write_json(out/'input_integrity.json', {'before': before, 'after': after, 'unchanged': before==after})
        if before != after:
            raise RuntimeError('Protected source/results integrity changed')


if __name__ == '__main__':
    main()
