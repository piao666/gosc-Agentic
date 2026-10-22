"""HPC-only audit of transcribed paper tables against immutable R2 outputs."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

from hpc_runs import ROOT, require_hpc, write_json
from hpc_reproduce import snapshot, command


def cells(text):
    text = re.sub(r'\\multi(?:row|column)\{[^}]*\}\{[^}]*\}\{([^}]*)\}', r'\1', text)
    text = text.replace(r'$^\dagger$', '†').replace(r'$^\ddagger$', '‡')
    marks = ''.join(x for x in text if x in '†‡')
    text = re.sub(r'\\[A-Za-z]+', '', text).replace('$', '').replace('{', '').replace('}', '')
    nums = [float(x) for x in re.findall(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?', text)]
    words = re.sub(r'[^A-Za-z ]', '', text)
    words = ' '.join(words.split()).lower()
    return {'numbers': nums, 'markers': marks, 'words': words if not nums else ''}


def compare(reference, source):
    result = []
    for table in reference['tables']:
        file = source/table['file']
        rows = [line.split('&') for line in file.read_text().splitlines()
                if '&' in line and not line.lstrip().startswith('\\multicolumn')]
        differences, checks = [], 0
        if len(rows) != len(table['rows']):
            differences.append({'row_count_actual': len(rows), 'row_count_paper': len(table['rows'])})
        for i, (actual, expected) in enumerate(zip(rows, table['rows'])):
            expected = expected.split('|')
            selected = [actual[n] for n in table['columns'] if n < len(actual)]
            if len(selected) != len(expected):
                differences.append({'row': i+1, 'column_count_actual': len(selected), 'column_count_paper': len(expected)})
            for j, (a, e) in enumerate(zip(selected, expected)):
                av, ev = cells(a), cells(e)
                checks += 1
                ok = len(av['numbers']) == len(ev['numbers']) and all(abs(x-y)<1e-8 for x,y in zip(av['numbers'], ev['numbers']))
                ok = ok and av['markers']==ev['markers'] and av['words']==ev['words']
                if not ok:
                    differences.append({'row': i+1, 'column': table['columns'][j], 'paper': e, 'actual': a.strip()})
        result.append({'table': table['id'], 'pdf_page': table['page'], 'file': table['file'],
                       'rows_checked': len(table['rows']), 'cells_checked': checks,
                       'status': 'match' if not differences else 'difference', 'differences': differences})
    return result


def main():
    require_hpc()
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    run_dir = Path(os.environ['GOSC_RUN_DIR'])
    src = ROOT/'research/sync/runs/hpc-r2-20261019/outputs/figures'
    references = ROOT/'research/reproduction/paper_table_references.json'
    reference = json.loads(references.read_text())
    before = snapshot()
    write_json(out/'input_integrity.json', {'before': before})
    try:
        original = compare(reference, src)
        write_json(out/'original_table_comparison.json', original)
        work = ROOT/'.local/paper-audit-workspaces'/run_dir.name
        work.mkdir(parents=True, exist_ok=False)
        for folder in ['gosc', 'experiments']:
            shutil.copytree(ROOT/folder, work/folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (work/'results').mkdir()
        for name in ['rev_where_tom.json', 'belief_divergence.jsonl']:
            shutil.copyfile(ROOT/'results'/name, work/'results'/name)
        (work/'figures').mkdir()
        shutil.copyfile(src/'table_values.tex', work/'figures/table_values.tex')
        command([sys.executable, '-m', 'experiments.run_belief_divergence', '--table'],
                out, 'fill-table-vi', 600, cwd=work)
        supplement = out/'supplements'
        supplement.mkdir()
        shutil.copyfile(work/'figures/table_values.tex', supplement/'table_values.tex')
        table_vi = {'tables': [t for t in reference['tables'] if t['id']=='VI']}
        completed = compare(table_vi, supplement)
        write_json(out/'completed_table_vi_comparison.json', completed)

        sys.path.insert(0, str(work))
        from gosc import Config
        from gosc.messages import raw_bits, confirm_bits, intent_bits, sem_step_bits, evidence_bits
        cfg = Config()
        payload = {'raw_bits': raw_bits(cfg), 'confirm_bits': confirm_bits(cfg),
                   'intent_bits': intent_bits(cfg), 'sem_base_bits': sem_step_bits(0, cfg),
                   'sem_detection_increment_bits': sem_step_bits(1,cfg)-sem_step_bits(0,cfg),
                   'evidence_n1_p0_bits': evidence_bits(1,0,cfg), 'evidence_n1_p1_bits': evidence_bits(1,1,cfg)}
        assert payload == {'raw_bits':218,'confirm_bits':18,'intent_bits':18,'sem_base_bits':33,
                           'sem_detection_increment_bits':5,'evidence_n1_p0_bits':34,'evidence_n1_p1_bits':39}
        configs = []
        for name, expected in reference['config_defaults'].items():
            actual = getattr(cfg, name)
            if isinstance(actual, tuple): actual = list(actual)
            configs.append({'field':name,'paper':expected,'code':actual,'match':actual==expected})
        assert all(x['match'] for x in configs)
        points = json.loads((ROOT/'results/rev_validation.json').read_text())
        frozen = []
        for row in reference['frozen_points']:
            source = points[row['setting']]
            eta = float(source['gosc']['point'].split('eta')[1])
            point = source['periodic']['point']
            k = int(re.search(r'/k(\d+)', point).group(1))
            th = float(point.split('/th')[1]) if '/th' in point else None
            actual = {'eta':eta,'scheme':source['periodic']['scheme'],'interval':k,'threshold':th}
            expected = {k:v for k,v in row.items() if k!='setting'}
            frozen.append({'setting':row['setting'],'paper':expected,'stored_point':actual,'match':actual==expected})
        assert all(x['match'] for x in frozen)
        write_json(out/'static_and_frozen_checks.json', {'table_II_payload':payload,'table_III_defaults':configs,
                   'table_XIII_frozen_points':frozen,'qualifiers':[
                   'Natural-language message length is variable, not a 1480-bit constant.',
                   '34-bit evidence base assumes n=1 and P=0; detections add bits.',
                   'Rescue deadlines 60..180 are explicitly set in experiment scripts, not Config generic defaults 100..300.']})
        known = [x for x in original if x['status']!='match']
        assert len(known)==1 and known[0]['table']=='VI' and len(known[0]['differences'])==5, known
        assert completed[0]['status']=='match', completed
        report = {'status':'verified_with_documented_upstream_gap','paper_sha256':reference['paper_sha256'],
                  'reference_sha256':hashlib.sha256(references.read_bytes()).hexdigest(),
                  'original_tables_matching':sum(x['status']=='match' for x in original),
                  'original_tables_checked':len(original),'original_cells_checked':sum(x['cells_checked'] for x in original),
                  'original_differing_cells':5,'table_vi_supplement_matches_paper':True,
                  'static_default_checks':len(configs),'frozen_points_checked':len(frozen),
                  'scope':'Paper printed values and footnote markers vs regenerated tables, plus payload/default/frozen checks. No new simulations, calibration, training or LLM calls. Table I is a literature-positioning table, reviewed semantically rather than numerically.',
                  'figure_2_layout_issue':'Overlapping minor log tick labels in regenerated rescue subplot 3; report as display issue, not a data discrepancy.'}
        write_json(out/'audit_summary.json', report)
        print(json.dumps(report), flush=True)
    finally:
        after = snapshot()
        write_json(out/'input_integrity.json', {'before':before,'after':after,'unchanged':before==after})
        if before!=after: raise RuntimeError('Protected input files changed')


if __name__=='__main__':main()
