"""Offline scoring trust domain. Never import into an online value function."""
from collections import Counter
import re
import string


def normalize(text):
    return " ".join(re.sub(r"\b(a|an|the)\b", " ",
                          "".join(c for c in text.lower() if c not in string.punctuation)).split())


def f1(gold, answer):
    a, b = normalize(gold).split(), normalize(answer).split()
    if not a or not b:
        return float(a == b)
    common = sum((Counter(a) & Counter(b)).values())
    return 2*common/(len(a)+len(b))


def legacy_comm_words(transcript, style):
    from .application import ANSWER, BOXED, peer_payload
    total = 0
    for full in transcript:
        name = "Alice" if full.startswith("Alice:") else "Bob" if full.startswith("Bob:") else None
        visible = peer_payload(full, name, style) if style == "protocol" and name else full
        total += len(normalize(BOXED.sub(" ", ANSWER.sub(" ", visible))).split())
    return total


def legacy_summary(episodes, golds, style):
    if len(episodes) != len(golds):
        raise ValueError("one gold per episode")
    scores = [f1(g, e["final_answer"]) if e["final_answer"] is not None else None
              for e, g in zip(episodes, golds)]
    words = [legacy_comm_words(e["transcript"], style) for e in episodes]
    present = [s for s in scores if s is not None]
    mean = sum(present)/len(present) if present else None
    total = sum(words)
    return {"f1_team": scores, "comm_tokens": words,
            "comm_tokens_per_turn": [w/len(e["transcript"]) if e["transcript"] else 0.0 for w,e in zip(words, episodes)],
            "average_f1_team": mean,
            "average_comm_tokens": sum(words)/len(words) if words else None,
            "f1_per_1k_tokens": mean/(total/1000.0) if mean is not None and total > 0 else None}


def summarize(planned, records):
    """One record per planned ID. Only started episodes enter primary mean.

    end_reason is exclusive; errors/unanswered counts overlap by definition.
    """
    if len(planned) != len(set(planned)):
        raise ValueError("planned identities must be unique")
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)) or set(ids)-set(planned):
        raise ValueError("duplicate/unplanned result")
    started = [r for r in records if r.get("started", True)]
    values, legacy, em = [], [], []
    errors = unanswered = completed = 0
    for r in started:
        gold = r["gold"]
        if not isinstance(gold, str) or not normalize(gold):
            raise ValueError("Invalid reference answer must be audited, not silently scored")
        answer = r.get("answer")
        reason = r["end_reason"]
        if reason not in {"answer", "turn_limit", "deadline", "model_error", "parse_error", "timeout"}:
            raise ValueError("unknown end reason")
        valid = reason == "answer" and isinstance(answer, str) and bool(answer)
        value = f1(gold, answer) if valid else 0.0
        values.append(value)
        em.append(float(valid and normalize(gold) == normalize(answer)))
        # Preserve the raw parser answer's native score independently of timeout.
        legacy.append(f1(gold, answer) if isinstance(answer, str) and answer else None)
        errors += reason in {"model_error", "parse_error", "timeout"}
        unanswered += not valid
        completed += reason in {"answer", "turn_limit"}
    present = [v for v in legacy if v is not None]
    n = len(started)
    return {"N_planned": len(planned), "N_started": n, "N_completed": completed,
            "N_error": errors, "N_unanswered": unanswered, "N_not_started": len(planned)-n,
            "not_started_ids": sorted(set(planned)-{r["id"] for r in started}),
            "mean_F1_all": sum(values)/n if n else None,
            "EM_all_added": sum(em)/n if n else None,
            "legacy_mean_F1_nonNone": sum(present)/len(present) if present else None,
            "complete_planned_set": n == len(planned),
            "error_unanswered_overlap": True}
