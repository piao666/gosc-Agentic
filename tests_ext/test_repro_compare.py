from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from repro_compare import compare_rows,schema

def test_zero_coverage_not_match():
    r=compare_rows([{'scheme':'a','param':'x','seed':0}],[{'scheme':'b','param':'x','seed':0}],['scheme','param','seed'])
    assert r['status']=='not_compared' and r['compared_common_keys']==0

def test_duplicates_are_invalid_on_both_sides():
    row={'scheme':'a','param':'x','seed':0}
    for a,b in [([row,row],[row]),([row],[row,row])]:assert compare_rows(a,b,['scheme','param','seed'])['status']=='invalid_identity'

def test_missing_keys_not_silent_null():
    assert compare_rows([{'seed':0}],[{'seed':0}],['scheme','seed'])['status']=='invalid_identity'

def test_extra_selection_labels_do_not_destroy_explicit_identity():
    a={'scheme':'gosc','param':'W100/eta0.0','seed':0,'case':2,'setting':'rescue-W100','symbols':12}
    b={'scheme':'gosc','param':'W100/eta0.0','seed':0,'symbols':12}
    assert compare_rows([a],[b],schema('rev_rescue.json'))['status']=='matching_complete_coverage'

def test_partial_coverage_and_missing_metric_explicit():
    a={'scheme':'a','param':'x','seed':0};b=a|{'symbols':12}
    r=compare_rows([a],[b,b|{'seed':1}],['scheme','param','seed'])
    assert r['status']=='scientific_differences_retained' and r['reference_coverage']==0.5
    assert r['mismatches'][0]['fields']==['symbols']

def test_genie_schema_does_not_require_unrecorded_scheme():
    row={'param':'W100','seed':0,'symbols':0}
    assert compare_rows([row|{'scheme':'genie'}],[row],schema('rev_genie_ref.json'))['status']=='matching_complete_coverage'

def test_fidelity_identity_includes_decision_time_agent_kind_and_nested_estimate():
    from repro_compare import compare_rows,schema
    a=[{'seed':2000,'t':4,'agent':0,'kind':'E','est':{'tom':1.0},'dT':2.0}]
    b=[{**a[0],'est':{'tom':2.0}}]
    r=compare_rows(a,b,schema('rev_value_fidelity.json'))
    assert r['status']=='scientific_differences_retained' and r['mismatches'][0]['fields']==['est']

def test_common_identity_without_scientific_metrics_is_not_evidence_of_match():
    from repro_compare import compare_rows
    rows=[{'seed':1,'label':'x'}]
    r=compare_rows(rows,rows,['seed'])
    assert r['compared_common_keys']==1 and r['scientific_metric_comparisons']==0
    assert r['status']=='not_compared'
