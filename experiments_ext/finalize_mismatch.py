"""Index immutable local diagnostic outputs; does not run simulations."""
import csv
import importlib.metadata as md
import json
from pathlib import Path
import sys

from experiments_ext.reproduce import ROOT, BASE, check_protected, save, sha, git
from experiments_ext.campaign import differences


def main():
    run = ROOT / ".local/reproduction/2026-10-15-mismatch-v2"
    old = ROOT / ".local/reproduction/2026-10-15-baseline-v1"
    compact = ROOT / "research/reproduction/2026-10-15-mismatch"
    reference = next(r for r in json.loads((old / "upstream_workspace/results/rev_frontier.json").read_text())["rows"]
                     if (r["scheme"], r["param"], r["seed"]) == ("gosc_bits", "W100/eta0.0", 0))
    save(compact / "author_reference.json", dict(reference=reference, baseline_commit=BASE,
        file="results/rev_frontier.json", file_sha256=sha(old / "upstream_workspace/results/rev_frontier.json")))
    paths = [run / "initial", run / "windows246", run / "windows126"]
    paths += [run / "linux" / x for x in ("arithmetic", "python314", "np124", "np126", "np126-noavx")]
    rows, artifacts = [], {}
    for folder in paths:
        manifest = json.loads((folder / "manifest.json").read_text())
        artifacts[str((folder / 'manifest.json').relative_to(ROOT))] = sha(folder / "manifest.json")
        for output_file in sorted(folder.glob("*-output.json")):
            record = json.loads(output_file.read_text())
            output = record["output"]
            row = dict(variant=folder.relative_to(run).as_posix(), mode=record["mode"],
                python=manifest['python'].split()[0], numpy=manifest['numpy'], os=manifest['os'],
                seed=manifest['seed'], completion_time=output['completion_time'], symbols=output['symbols'],
                bits=output['bits'], delivered_bits=output['delivered_bits'], found=output['found'],
                completed=output['completed'], elapsed_seconds=record['elapsed_seconds'],
                differing_reference_fields=len(differences(reference,output)),
                raw_output=str(output_file.relative_to(ROOT)))
            rows.append(row)
            artifacts[row['raw_output']] = sha(output_file)
            trace = folder / (record['mode'] + '-trace.jsonl')
            artifacts[str(trace.relative_to(ROOT))] = sha(trace)
    with (compact / 'compatibility_matrix.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lock={}
    for line in (ROOT/'requirements-windows.lock.txt').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version = line.split('==');lock[name]=dict(expected=version,installed=md.version(name))
    assert all(x['expected']==x['installed'] for x in lock.values())
    audit=run/'platform-selection-audit-v2.json'
    save(compact/'selection_audit.json',json.loads(audit.read_text()))
    wheels={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (run/'wheels').glob('*.whl')}
    summary=dict(experiment_id=run.name,git_commit=git('rev-parse','HEAD'),upstream_commit=BASE,
        working_tree_dirty=bool(git('status','--short')),python_version=sys.version,
        dependencies_lock='requirements-windows.lock.txt',dependencies_lock_sha256=sha(ROOT/'requirements-windows.lock.txt'),
        original_environment_lock_check=lock, protected_inputs=check_protected(old),
        seeds=[0],agent_models=['Planner'],llm_cache_mode='not_used',
        status='diagnosis_completed_historical_provenance_unresolved',
        r4_status='blocked_not_resumed',receiver_diagnostic_status='not_run',
        missions=len(rows),matching_saved_records=sum(r['differing_reference_fields']==0 for r in rows),
        elapsed_mission_seconds_sum=sum(r['elapsed_seconds'] for r in rows),
        independent_mission_seeds=1,confidence_intervals='not_estimated_single_seed_compatibility_probes',
        wheels=wheels,wheel_bytes_total=sum(w['bytes'] for w in wheels.values()),
        observations=rows,artifacts=artifacts,
        notes=['No original algorithm/results/cache changes.','Arithmetic interventions are not original baseline runs.',
            'Linux NumPy wheel installs were isolated and offline inside existing images.',
            'Exact root cause of saved author 83-slot trajectory remains unverified.',
            'No GPU, model download, paid API or messages to authors. CPU peaks/tokens not measured.'])
    save(run/'final_manifest.json',summary)
    save(compact/'experiment_manifest.json',summary)
    print(json.dumps({k:summary[k] for k in ('missions','matching_saved_records','elapsed_mission_seconds_sum','protected_inputs','wheel_bytes_total')}))


if __name__=='__main__':
    main()
