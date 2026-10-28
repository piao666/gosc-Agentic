"""BF-selector-v1: legacy feasible returns, bounded budget-only repair.

No upstream modification, price tuning, clipping, RNG, or task outcomes.
"""
import math
from numbers import Real

from gosc.schemes import lagrangian_select as legacy_select

VERSION='BF-selector-v1'
MAX_EXPANSIONS=64
BISECTION_STEPS=40


class SelectorFailure(RuntimeError):
    pass


def _finite(value):
    try:
        return isinstance(value,Real) and not isinstance(value,bool) and math.isfinite(value)
    except (OverflowError,TypeError):
        return False


def validate_inputs(groups,budget,price):
    if not isinstance(groups,(list,tuple)):
        raise TypeError('Reusable ordered group sequence required')
    if type(budget) is not int or budget<0 or not _finite(price) or price<0:
        raise ValueError('Budget/price contract')
    if len({id(g) for g in groups})!=len(groups):
        raise ValueError('Repeated group identity')
    for g in groups:
        if not isinstance(g.options,(list,tuple)):
            raise TypeError('Reusable ordered options required')
        for o in g.options:
            if type(o.symbols) is not int or o.symbols<=0 or not _finite(o.value):
                raise ValueError('Positive integer symbols and finite value required')
            # Finite operands can still overflow in legacy arithmetic. Never
            # disguise an undefined utility as a successful empty selection.
            try:
                if not all(math.isfinite(x) for x in
                    (price*o.symbols,o.value-price*o.symbols,o.value/o.symbols)):
                    raise SelectorFailure('Nonfinite input arithmetic')
            except OverflowError as exc:
                raise SelectorFailure('Input arithmetic overflow') from exc


def selection_indices(groups,chosen):
    index={id(g):i for i,g in enumerate(groups)}
    seen=set();answer=[]
    for g,o in chosen:
        if id(g) not in index or id(g) in seen:
            raise ValueError('Unknown or repeated selected group')
        matches=[i for i,p in enumerate(g.options) if p is o]
        if not matches:
            raise ValueError('Selected option is not an original group member')
        seen.add(id(g))
        answer.append(dict(group_index=index[id(g)],option_index=matches[0]))
    return answer


def validate_selection(groups,chosen,budget):
    selection_indices(groups,chosen)
    if any(type(o.symbols) is not int or o.symbols<=0 for _,o in chosen):
        raise ValueError('Selected symbol type')
    used=sum(o.symbols for _,o in chosen)
    if used>budget:
        raise ValueError('Selected budget')
    return used


def _state(groups):
    return tuple((id(g),g.kind,g.cell,tuple((id(o),o.rate,o.bits,o.symbols,o.value,o.n_records)
                                         for o in g.options)) for g in groups)


def _pick(groups,multiplier):
    if not math.isfinite(multiplier):
        raise SelectorFailure('Nonfinite multiplier')
    chosen=[];used=0
    for g in groups:
        best=None;best_u=0.
        for o in g.options:
            u=o.value-multiplier*o.symbols
            if not math.isfinite(u):
                raise SelectorFailure('Nonfinite repaired utility')
            if u>best_u:
                best,best_u=o,u
        if best is not None:
            chosen.append((g,best));used+=best.symbols
    return chosen,used


def _expand(hi):
    return max(hi*2.,math.nextafter(hi,math.inf))


def select_feasible(groups,budget,price):
    validate_inputs(groups,budget,price)
    before=_state(groups)
    active=[g for g in groups if g.options]
    old=legacy_select(active,budget,price)
    selection_indices(groups,old)  # Structural errors never enter budget repair.
    legacy_used=sum(o.symbols for _,o in old)
    trace=dict(selector_version=VERSION,path='legacy_feasible',legacy_used=legacy_used,
        initial_upper=None,upper_checks=[],expansions=0,bisection_steps=0,
        final_used=legacy_used,max_expansions=MAX_EXPANSIONS)
    if legacy_used<=budget:
        validate_selection(groups,old,budget)
        if before!=_state(groups):raise SelectorFailure('Input mutation')
        return old,trace
    trace['path']='budget_repair'
    hi=max((o.value/o.symbols for g in active for o in g.options),default=1.)
    trace['initial_upper']=hi
    if not math.isfinite(hi) or hi<=0:
        raise SelectorFailure('Invalid repair upper bound')
    for attempt in range(MAX_EXPANSIONS+1):
        chosen,used=_pick(active,price+hi)
        trace['upper_checks'].append(dict(upper=hi,used=used))
        if used<=budget:
            break
        if attempt==MAX_EXPANSIONS:
            raise SelectorFailure('Upper-bound expansion exhausted')
        new_hi=_expand(hi)
        if not math.isfinite(new_hi):raise SelectorFailure('Upper-bound overflow')
        if new_hi<=hi:raise SelectorFailure('Upper-bound progress stalled')
        hi=new_hi;trace['expansions']+=1
    lo=0.
    for _ in range(BISECTION_STEPS):
        mid=lo+.5*(hi-lo)
        if mid==lo or mid==hi:break
        if _pick(active,price+mid)[1]<=budget:
            hi=mid
        else:
            lo=mid
        trace['bisection_steps']+=1
    chosen,used=_pick(active,price+hi)
    if used>budget:raise SelectorFailure('Lost feasible upper endpoint')
    taken={id(g) for g,_ in chosen}
    for g in sorted((g for g in active if id(g) not in taken),
                    key=lambda g:-max(o.value/o.symbols for o in g.options)):
        fits=[o for o in g.options if o.symbols<=budget-used and o.value-price*o.symbols>0]
        if fits:
            o=max(fits,key=lambda o:o.value-price*o.symbols)
            chosen.append((g,o));used+=o.symbols
    trace['final_used']=validate_selection(groups,chosen,budget)
    if before!=_state(groups):raise SelectorFailure('Input mutation')
    return chosen,trace
