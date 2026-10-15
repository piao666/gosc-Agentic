"""Find and replay the first discrete difference between two scheduling traces."""
import argparse
import copy
import itertools
import json
import math
from pathlib import Path

from experiments_ext.reproduce import save, sha
from gosc.schemes import Group, Option, lagrangian_select


def signature(row):
    return [(x["group"], x["option"]["rate"], x["option"]["bits"],
             x["option"]["symbols"], x["option"]["n_records"]) for x in row["chosen"]]


def reconstruct(row):
    return [Group(g["kind"], [Option(**o) for o in g["options"]], g["cell"]) for g in row["groups"]]


def replay(row):
    gs = reconstruct(row)
    out = lagrangian_select(gs, row["budget"], row["price"])
    return dict(chosen=[dict(group=gs.index(g), kind=g.kind, option=o.__dict__) for g, o in out],
        symbols=sum(o.symbols for _, o in out),
        objective=sum(o.value-row["price"]*o.symbols for _, o in out),
        maximum_densities=[dict(kind=g.kind, density=max(o.value/o.symbols for o in g.options),
            density_hex=float(max(o.value/o.symbols for o in g.options)).hex()) for g in gs])


def exact_small_objective(row):
    """Offline audit only; never used by the simulated scheduler."""
    gs = reconstruct(row)
    count = math.prod(len(g.options)+1 for g in gs)
    if count > 100000:
        raise ValueError("Enumeration audit is restricted to small states")
    best, chosen = 0.0, []
    for options in itertools.product(*[[None, *g.options] for g in gs]):
        if sum(o.symbols for o in options if o is not None) > row["budget"]:
            continue
        value = sum(o.value-row["price"]*o.symbols for o in options if o is not None)
        if value > best:
            best, chosen = value, [dict(group=i, kind=gs[i].kind, option=o.__dict__)
                                    for i, o in enumerate(options) if o is not None]
    return dict(objective=best, chosen=chosen, combinations=count)


def dual_and_greedy(row):
    """Read-only arithmetic replay of the baseline's dual stage for attribution."""
    gs = reconstruct(row)
    def pick(lam):
        chosen, used = [], 0
        for g in gs:
            best, best_u = None, 0.0
            for o in g.options:
                u = o.value-lam*o.symbols
                if u > best_u:
                    best, best_u = o, u
            if best is not None:
                chosen.append((g, best)); used += best.symbols
        return chosen, used
    price, budget = row['price'], row['budget']
    initial = pick(price)
    if initial[1] <= budget:
        return dict(initial_symbols=initial[1], dual_needed=False)
    lo, hi = 0.0, max(o.value/o.symbols for g in gs for o in g.options)
    for _ in range(40):
        mid = 0.5*(lo+hi)
        if pick(price+mid)[1] <= budget:
            hi = mid
        else:
            lo = mid
    chosen, used = pick(price+hi)
    taken = {id(g) for g,o in chosen}
    order = sorted((g for g in gs if id(g) not in taken),
                   key=lambda g: -max(o.value/o.symbols for o in g.options))
    return dict(initial_symbols=initial[1], dual_needed=True, lo=lo, hi=hi, dual_symbols=used,
        greedy_group_order=[g.kind for g in order],
        rate1_utilities_at_hi=[dict(kind=g.kind,utilities=[o.value-(price+hi)*o.symbols
                              for o in g.options if o.rate==1.0]) for g in gs])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("left", type=Path)
    ap.add_argument("right", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    left = [json.loads(x) for x in args.left.read_text().splitlines()]
    right = [json.loads(x) for x in args.right.read_text().splitlines()]
    differing_values = None
    for i, (a, b) in enumerate(zip(left, right)):
        if differing_values is None and a["groups"] != b["groups"]:
            differing_values = i
        if a["pos"] != b["pos"] or signature(a) != signature(b):
            break
    else:
        save(args.output, dict(status="no_discrete_difference_in_common_prefix", left_records=len(left),
             right_records=len(right), first_group_difference=differing_values))
        return
    ra, rb = replay(a), replay(b)
    assert signature(ra) == signature(a) and signature(rb) == signature(b)
    value_changes = []
    same_state = all(a[k] == b[k] for k in ("t", "agent", "pos", "snr_mean", "snr_inst", "budget", "price"))
    changed = copy.deepcopy(a)
    shapes_equal = len(a["groups"]) == len(b["groups"])
    for gi, (ga, gb) in enumerate(zip(a["groups"], b["groups"])):
        shapes_equal &= len(ga["options"]) == len(gb["options"])
        for oi, (oa, ob) in enumerate(zip(ga["options"], gb["options"])):
            shapes_equal &= {k:v for k,v in oa.items() if k != "value"} == {k:v for k,v in ob.items() if k != "value"}
            if oa["value"] != ob["value"]:
                va, vb = oa["value"], ob["value"]
                value_changes.append(dict(group=gi, option=oi, left=va, right=vb,
                    difference=vb-va, ulps=(vb-va)/math.ulp(va)))
                changed["groups"][gi]["options"][oi]["value"] = vb
    causal_replay = replay(changed) if same_state and shapes_equal else None
    if causal_replay is not None:
        assert signature(causal_replay) == signature(rb)
    save(args.output, dict(status="audited", source_sha256=sha(__file__),
        inputs={str(p):sha(p) for p in (args.left,args.right)}, first_group_difference=differing_values,
        first_discrete_difference=i, t=a["t"], agent=a["agent"], same_observed_state=same_state,
        same_candidate_shapes=shapes_equal, value_changes=value_changes,
        left=ra, right=rb, value_only_counterfactual=causal_replay,
        dual_and_greedy_left=dual_and_greedy(a), dual_and_greedy_right=dual_and_greedy(b),
        exact_small_state_left=exact_small_objective(a), exact_small_state_right=exact_small_objective(b),
        note="Offline selection replay isolates numerical sensitivity. Does not identify the author's generation environment or establish a TeamModel defect."))
    print(json.dumps(dict(index=i,t=a['t'],agent=a['agent'],changes=value_changes,
        left_objective=ra['objective'],right_objective=rb['objective']),ensure_ascii=False))


if __name__ == "__main__":
    main()
