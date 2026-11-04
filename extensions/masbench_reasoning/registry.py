"""Versioned offline grouping/eligibility. Never used by online value functions."""
from collections import defaultdict
import hashlib
import itertools
import json

VERSION = "masbench-registry-v2"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def normalized(text):
    return " ".join(text.strip().lower().split())


def graph(items, legacy=False, kinds=None):
    keys = defaultdict(set)
    rejected = []
    for i, item in enumerate(items):
        keys[("record_id", str(item["id"]))].add(i)
        keys[("question", normalized(item["question"]))].add(i)
        for side in ["agent_a", "agent_b"]:
            for title, _ in item["context"][side]:
                title = title.strip().lower()  # Preserve the original title normalization.
                if legacy or title:
                    keys[("context_title", title)].add(i)
                else:
                    rejected.append({"row": i, "side": side, "reason": "empty_title"})
            for title, index, sentence in item["supporting_facts"][side]:
                text, title = sentence.strip(), title.strip().lower()
                if legacy:
                    keys[("support_text_only", text)].add(i)
                elif not title or not text:
                    rejected.append({"row": i, "side": side, "reason": "empty_support_key"})
                else:
                    keys[("support_article_text", title, text)].add(i)
    parent = list(range(len(items)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    ledger = []
    for key, members in sorted(keys.items()):
        if kinds is not None and key[0] not in kinds:
            continue
        rows = sorted(members)
        if len(rows) > 1:
            ledger.append({"kind": key[0], "key_sha256": digest(key), "rows": rows})
            for row in rows[1:]:
                parent[find(row)] = find(rows[0])
    grouped = defaultdict(list)
    for i in range(len(items)):
        grouped[find(i)].append(i)
    groups = sorted(grouped.values(), key=lambda rows: rows[0])
    component_of = {row: n for n, rows in enumerate(groups) for row in rows}
    return {"components": groups, "component_of": component_of,
            "edges": ledger, "rejected_keys": rejected}


def build_registry(items, data_sha256, anomaly_indices):
    """Four distinct question families, 2 easy/2 hard, no gold-based choices.

    Freeze a development reservation, not actual model exposure or a held-out
    partition. A whole component is reserved when one member is selected.
    """
    fixed = graph(items)
    legacy = graph(items, legacy=True)
    families = defaultdict(list)
    for i, item in enumerate(items):
        families[normalized(item["question"])].append(i)
    blocked_families = {normalized(items[i]["question"]) for i in anomaly_indices}
    blocked_rows = {i for q, rows in families.items() if q in blocked_families for i in rows}
    family_rows = [{"family_sha256": digest(q), "rows": rows,
                    "record_ids": [str(items[i]["id"]) for i in rows],
                    "record_levels": [items[i]["level"] for i in rows],
                    "pilot_eligible": q not in blocked_families,
                    "source_id_status": "unknown_original_source_not_recovered"}
                   for q, rows in sorted(families.items())]
    choices = {"easy": {}, "hard": {}}
    for i, item in enumerate(items):
        if i in blocked_rows or item["level"] not in choices:
            continue
        comp = fixed["component_of"][i]
        rank = digest([VERSION, data_sha256, normalized(item["question"]), str(item["id"])])
        option = {"row": i, "record_id": str(item["id"]), "level": item["level"],
                  "family_sha256": digest(normalized(item["question"])),
                  "component": comp, "selection_rank_sha256": rank}
        family = option["family_sha256"]
        if family not in choices[item["level"]] or rank < choices[item["level"]][family]["selection_rank_sha256"]:
            choices[item["level"]][family] = option
    # Per component/stratum keep four distinct families. At most two families
    # can be consumed by the other stratum, leaving the two required here.
    def candidates(level):
        grouped = defaultdict(list)
        for choice in choices[level].values():
            grouped[choice["component"]].append(choice)
        return sorted([c for group in grouped.values()
                       for c in sorted(group, key=lambda x:x["selection_rank_sha256"])[:4]],
                      key=lambda x:x["selection_rank_sha256"])
    easy, hard = candidates("easy"), candidates("hard")
    selected = []
    # Component diversity is a predeclared soft preference, as in the review.
    # Family uniqueness and 2/2 record strata are hard constraints.
    upper = min(4, min(2, len({x["component"] for x in easy})) +
                min(2, len({x["component"] for x in hard})))
    for target in range(upper, 0, -1):
        for pair in itertools.combinations(easy, 2):
            if len({x["component"] for x in pair})+2 < target:
                continue
            remaining = [x for x in hard if x["family_sha256"] not in {p["family_sha256"] for p in pair}]
            for other in itertools.combinations(remaining, 2):
                combo = [*pair, *other]
                if len({x["component"] for x in combo}) == target:
                    selected = combo
                    break
            if selected:
                break
        if selected:
            break
    reserved_components = sorted({x["component"] for x in selected})
    reserved = sorted(i for n in reserved_components for i in fixed["components"][n])
    # Pairwise membership difference is exact for this finite existing dataset.
    changed_pairs = [[i,j] for i in range(len(items)) for j in range(i+1,len(items))
                     if (legacy["component_of"][i] == legacy["component_of"][j]) !=
                        (fixed["component_of"][i] == fixed["component_of"][j])]
    structural = {}
    for name, kinds in [("question_only", {"record_id", "question"}),
                        ("context_only", {"context_title"}),
                        ("question_and_context", {"record_id", "question", "context_title"}),
                        ("support_only", {"support_article_text"})]:
        sub = graph(items, kinds=kinds)
        structural[name] = {"count": len(sub["components"]),
                            "largest": max(map(len, sub["components"]), default=0)}
    return {"version": VERSION, "data_sha256": data_sha256,
            "selection_uses_gold_or_outputs": False,
            "legacy": legacy, "corrected": fixed, "structural_graphs": structural,
            "membership_changed_pairs": changed_pairs, "families": family_rows,
            "anomaly_rows": sorted(anomaly_indices), "pilot_ineligible_family_rows": sorted(blocked_rows),
            "selection_rule": "Four distinct question families, 2 easy/2 hard; maximize distinct corrected conservative components then first feasible SHA256-ranked representatives; no outcome/answer/length features",
            "component_diversity_constraint": "predeclared_soft_preference_not_statistical_independence_claim",
            "selected": selected, "reserved_components": reserved_components,
            "development_reserved_rows": reserved,
            "not_reserved_rows": [i for i in range(len(items)) if i not in set(reserved)],
            "status": "development_registry_frozen_model_unexposed" if len(selected) == 4 else "blocked_strata_component_coverage",
            "actual_model_exposure": False, "calibration_eval_split_frozen": False,
            "future_independent_pool_sufficiency": "Pending_power_and_study_design",
            "registry_payload_sha256": digest([selected, reserved, sorted(blocked_rows), data_sha256, VERSION])}
