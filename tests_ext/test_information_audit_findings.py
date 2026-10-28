"""Strict rejection stays default; diagnostic collection cannot pass violations."""
import copy

import pytest

from scripts.audit_information_identifiability import decision_audit
from scripts.audit_information_calibration import selection_budget_status


def overbudget_decision():
    option = dict(kind='CONF', cell=1, rate=2., bits=152, symbols=76, n_records=0,
                  value=1., value_hex=(1.).hex())
    return dict(event='decision', t=2, sender=0, arm='public-fixed', age_source='none',
        timestamps=[], summary_cache=[], native_positions={}, valuation_positions={},
        factor=1., effective_price=0., base_price=0., budget=100,
        selected=[option, dict(option, cell=2)],
        groups_before_age=[dict(kind='CONF', cell=cell, options=[option]) for cell in (1, 2)])


def test_default_audit_still_rejects_real_overbudget_selection():
    with pytest.raises(ValueError, match='Selected budget'):
        decision_audit([overbudget_decision()], {'selection_calls': 1})


def test_collection_preserves_actual_excess_and_cannot_mark_passed():
    findings = []
    assert decision_audit([overbudget_decision()], {'selection_calls': 1},
                          selection_budget_findings=findings) == 1
    assert len(findings) == 1
    assert findings[0]['selected_symbols'] == 152
    assert findings[0]['budget'] == 100 and findings[0]['excess'] == 52
    assert selection_budget_status(findings) == 'blocked_selection_budget'
    assert selection_budget_status([]) == 'passed'


def test_collection_does_not_skip_remaining_catalog_checks():
    decision = copy.deepcopy(overbudget_decision())
    decision['groups_before_age'] = []
    with pytest.raises(ValueError, match='absent from catalog'):
        decision_audit([decision], {'selection_calls': 1}, selection_budget_findings=[])
