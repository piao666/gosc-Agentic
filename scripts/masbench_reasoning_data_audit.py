"""HPC-only immutable public-data identity/schema/group audit; no task execution."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hpc_runs import require_hpc

COMMIT = "c0301a650db95958924bb080192c09fef39389a5"
BLOB = "9cfc774f5828bb7b811612a16d0f7d209db627d7"
SIZE = 11996959


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def audit(items):
    from extensions.masbench_reasoning.application import private_view
    from extensions.masbench_reasoning.evaluation import normalize
    errors, details, levels = [], [], Counter()
    ids, questions, raw_hashes = defaultdict(list), defaultdict(list), defaultdict(list)
    keys = defaultdict(list)
    fields = Counter()
    for i, item in enumerate(items):
        fields.update(item.keys())
        local_errors = []
        for name in ["id", "question", "answer", "level", "context", "supporting_facts"]:
            if name not in item:
                local_errors.append("missing_"+name)
        for name in ["question", "answer"]:
            if not isinstance(item.get(name), str) or not item.get(name, "").strip():
                local_errors.append("invalid_"+name)
        if isinstance(item.get("answer"), str) and not normalize(item["answer"]):
            local_errors.append("empty_normalized_gold")
        identifier = str(item.get("id", "missing:"+str(i)))
        ids[identifier].append(i)
        q = " ".join(str(item.get("question", "")).lower().split())
        questions[q].append(i)
        keys["id:"+identifier].append(i)
        keys["question:"+q].append(i)
        raw_hashes[hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()].append(i)
        levels[str(item.get("level"))] += 1
        titles, sentences, support = {}, {}, {}
        side = {}
        for agent in ["agent_a", "agent_b"]:
            context = item.get("context", {}).get(agent)
            facts = item.get("supporting_facts", {}).get(agent)
            titles[agent], sentences[agent], support[agent] = set(), set(), set()
            if not isinstance(context, list) or not context:
                local_errors.append("invalid_context_"+agent)
                context = []
            for article in context:
                if (not isinstance(article, list) or len(article) != 2
                        or not isinstance(article[0], str) or not isinstance(article[1], list)
                        or not all(isinstance(s, str) for s in article[1])):
                    local_errors.append("article_schema_"+agent)
                    continue
                title, passages = article
                titles[agent].add(title)
                keys["title:"+title.strip().lower()].append(i)
                sentences[agent].update(p.strip() for p in passages if p.strip())
            if not isinstance(facts, list) or not facts:
                local_errors.append("invalid_support_"+agent)
                facts = []
            for fact in facts:
                if (not isinstance(fact, list) or len(fact) != 3
                        or not isinstance(fact[0], str) or not isinstance(fact[1], int)
                        or not isinstance(fact[2], str)):
                    local_errors.append("support_schema_"+agent)
                    continue
                title, index, sentence = fact
                support[agent].add((title, index, sentence))
                keys["support:"+sentence.strip()].append(i)
                matches = [a for a in context if isinstance(a, list) and len(a) == 2 and a[0] == title]
                if not any(0 <= index < len(a[1]) and a[1][index] == sentence for a in matches):
                    local_errors.append("support_not_exact_context_"+agent)
            try:
                view = private_view(item, "Alice" if agent == "agent_a" else "Bob")
                side[agent] = {"context_utf8_bytes": len(view.information.encode()),
                               "articles": len(context), "sentences": len(sentences[agent]),
                               "support_facts": len(support[agent]),
                               "gold_substring_in_own_context": item.get("answer", "").casefold() in view.information.casefold()}
            except (TypeError, ValueError, KeyError) as e:
                local_errors.append("view_error_"+type(e).__name__)
        details.append({"index": i, "id": identifier, "level": item.get("level"),
                        "sides": side, "shared_titles": sorted(titles["agent_a"] & titles["agent_b"]),
                        "shared_sentence_count": len(sentences["agent_a"] & sentences["agent_b"]),
                        "shared_support_count": len(support["agent_a"] & support["agent_b"]),
                        "errors": local_errors})
        if local_errors:
            errors.append({"index": i, "id": identifier, "errors": local_errors})
    # Conservative connected components: same question/ID/title/exact support text.
    # Answer strings are deliberately not used as grouping keys (e.g. yes/no).
    parent = list(range(len(items)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for members in keys.values():
        for index in members[1:]:
            parent[find(index)] = find(members[0])
    components = defaultdict(list)
    for index in range(len(items)):
        components[find(index)].append(index)
    groups = []
    for members in components.values():
        group_ids = sorted(str(items[i].get("id", i)) for i in members)
        digest = hashlib.sha256(json.dumps(group_ids, ensure_ascii=False).encode()).hexdigest()
        bucket = int(digest[:8], 16) % 100
        split = "development" if bucket < 20 else "calibration" if bucket < 50 else "held_out"
        groups.append({"component_sha256": digest, "indices": members, "ids": group_ids,
                       "proposed_split": split})
    sizes = Counter()
    for group in groups:
        sizes[group["proposed_split"]] += len(group["ids"])
    return {"N": len(items), "levels": dict(levels), "field_counts": dict(fields),
            "unique_ids": len(ids), "duplicate_ids": {k:v for k,v in ids.items() if len(v)>1},
            "duplicate_question_groups": [v for v in questions.values() if len(v)>1],
            "duplicate_record_groups": [v for v in raw_hashes.values() if len(v)>1],
            "schema_errors": errors, "details": details,
            "private_overlap": {"items_shared_titles": sum(bool(d["shared_titles"]) for d in details),
                                "items_shared_sentences": sum(d["shared_sentence_count"]>0 for d in details),
                                "items_shared_support": sum(d["shared_support_count"]>0 for d in details)},
            "split_proposal": {"status": "proposal_only_not_frozen_or_authorized_for_tasks",
                               "rule": "connected id/question/title/exact support; SHA256(group IDs) mod100 20/30/50",
                               "components": len(groups), "largest": max(map(lambda g:len(g["ids"]), groups), default=0),
                               "sizes": dict(sizes), "groups": groups,
                               "all_required_splits_nonempty": all(sizes[s] for s in ["development", "calibration", "held_out"])},
            "leakage_limits": ["All rows inspected offline for schema; no model/task outputs observed",
                               "Cannot detect LLM pretraining contamination or identify every original HotpotQA source without upstream IDs",
                               "Context/gold string overlap is task evidence, not online gold injection",
                               "No diagnostic question selection or model-based split selection"]}


def main():
    require_hpc()
    signal.alarm(120)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Previously hash-checked public data file, HPC only")
    args = parser.parse_args()
    out = Path(os.environ["GOSC_OUTPUT_DIR"])
    url = f"https://raw.githubusercontent.com/BUPT-GAMMA/MASBench/{COMMIT}/Reasoning/reasoning.json"
    if args.input:
        if args.input.is_symlink() or (ROOT/".local").resolve() not in args.input.resolve().parents:
            raise ValueError("Staged input must stay in project .local")
        with args.input.open("rb") as source:
            body = source.read(16*1024*1024+1)
    else:
        with urllib.request.urlopen(url, timeout=30) as response:
            body = response.read(16*1024*1024+1)
    if len(body) != SIZE or hashlib.sha1(b"blob "+str(len(body)).encode()+b"\0"+body).hexdigest() != BLOB:
        write(out/"identity_failure.json", {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        raise RuntimeError("Pinned dataset identity mismatch")
    (out/"reasoning.json").write_bytes(body)
    sys.path.insert(0, str(ROOT))
    items = json.loads(body)
    if not isinstance(items, list) or not all(isinstance(x, dict) for x in items):
        raise RuntimeError("Expected list of records")
    result = audit(items)
    result["identity"] = {"commit": COMMIT, "git_blob_sha1": BLOB, "sha256": hashlib.sha256(body).hexdigest(),
                          "bytes": len(body), "url": url, "execution_host": "hpc"}
    write(out/"data_audit.json", result)
    print(json.dumps({k:result[k] for k in ["N", "levels", "unique_ids", "private_overlap"]}))
    print(json.dumps({"schema_error_records": len(result["schema_errors"]),
                      "split_sizes": result["split_proposal"]["sizes"], "model_calls": 0}))
    # Findings are audit outcomes, not a silently dropped subset or task success.


if __name__ == "__main__":
    main()
