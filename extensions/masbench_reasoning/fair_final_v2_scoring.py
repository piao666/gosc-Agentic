"""Offline dual-local-final scorer. Never imported by the application driver."""
from .evaluation import normalize, f1


def score_episode(episode, gold):
    if not isinstance(gold, str) or not normalize(gold):
        raise ValueError("invalid_reference")
    if not episode.get("started"):
        return dict(started=False, scores=None, mean_F1=None, mean_EM=None)
    rows = {}
    for role in ("Alice", "Bob"):
        final = episode.get("finals", {}).get(role, {})
        answer = final.get("answer")
        valid = bool(final.get("valid_answer") and isinstance(answer, str) and normalize(answer))
        rows[role] = dict(F1=f1(gold, answer) if valid else 0.,
                          EM=int(valid and normalize(gold) == normalize(answer)),
                          valid_format=bool(final.get("valid_format")), valid_answer=valid,
                          abstain=final.get("reason") == "abstain", normalized=normalize(answer) if valid else None,
                          reason=final.get("reason", "not_dispatched"))
    a, b = rows.values()
    return dict(started=True, completed=bool(episode.get("completed")), scores=rows,
                mean_F1=(a["F1"] + b["F1"]) / 2, mean_EM=(a["EM"] + b["EM"]) / 2,
                joint=f'{a["EM"]}{b["EM"]}', both_correct=a["EM"] == b["EM"] == 1,
                agreement=("at_least_one_unanswered" if not (a["valid_answer"] and b["valid_answer"])
                           else "equal" if a["normalized"] == b["normalized"] else "different"),
                valid_answer_rate=sum(r["valid_answer"] for r in rows.values()) / 2,
                valid_format_rate=sum(r["valid_format"] for r in rows.values()) / 2,
                unanswered_rate=sum(not r["valid_answer"] for r in rows.values()) / 2,
                abstain_rate=sum(r["abstain"] for r in rows.values()) / 2,
                format_failure_rate=sum(not r["valid_format"] for r in rows.values()) / 2)


def paired_summary(planned_families, scored):
    if len(set(planned_families)) != len(planned_families):
        raise ValueError("duplicate_family")
    if set(scored) - set(planned_families):
        raise ValueError("unplanned_family")
    pairs = []
    for family in planned_families:
        pair = scored.get(family, {})
        if set(pair) - {"Full", "No-A2A"}:
            raise ValueError("unknown_condition")
        full, no = pair.get("Full"), pair.get("No-A2A")
        present = all(r and r.get("started") for r in (full, no))
        pairs.append(dict(family=family, delta=(full["mean_F1"] - no["mean_F1"]) if present else None,
                          valid_both_conditions=bool(present and all(
                              r["valid_answer_rate"] == 1 for r in (full, no)))))
    complete = bool(pairs) and all(p["delta"] is not None for p in pairs)
    conditions = {}
    for condition in ("Full", "No-A2A"):
        rows = [scored[f][condition] for f in planned_families if f in scored and
                condition in scored[f] and scored[f][condition].get("started")]
        conditions[condition] = dict(N_started=len(rows), N_not_started=len(planned_families) - len(rows),
            mean_F1=sum(r["mean_F1"] for r in rows) / len(rows) if rows else None,
            mean_EM=sum(r["mean_EM"] for r in rows) / len(rows) if rows else None,
            both_correct_families=sum(r["both_correct"] for r in rows),
            joint={key: sum(r["joint"] == key for r in rows) for key in ("00", "01", "10", "11")},
            valid_answer_rate=sum(r["valid_answer_rate"] for r in rows) / len(rows) if rows else None,
            valid_format_rate=sum(r["valid_format_rate"] for r in rows) / len(rows) if rows else None)
    return dict(N_families=len(planned_families), N_pairs_started=sum(p["delta"] is not None for p in pairs),
                complete_pairs=complete, pairs=pairs,
                conditions=conditions,
                Delta_F1=sum(p["delta"] for p in pairs) / len(pairs) if complete else None,
                independent_problem_unit="family; article-component dependence remains")
