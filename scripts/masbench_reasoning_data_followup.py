"""HPC-only read-only followup on already audited dataset anomalies/lineage."""
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from hpc_runs import require_hpc


def main():
    require_hpc()
    signal.alarm(120)
    directory = ROOT/"research/sync/runs/hpc-masbench-data-audit-v2-20261103/outputs"
    body = (directory/"reasoning.json").read_bytes()
    assert hashlib.sha256(body).hexdigest() == "ce65640b566e70098c540b9c814768c9ff5d8544a4cb25162a3872ac9c3bb331"
    items = json.loads(body)
    audit = json.loads((directory/"data_audit.json").read_text())
    questions = defaultdict(list)
    for i, item in enumerate(items):
        questions[" ".join(item["question"].lower().split())].append(i)
    repeated, conflicts = [], []
    for members in questions.values():
        if len(members) > 1:
            row = {"indices": members, "ids": [items[i]["id"] for i in members],
                   "levels": [items[i]["level"] for i in members],
                   "answer_identical": len({items[i]["answer"] for i in members}) == 1,
                   "context_identical": len({json.dumps(items[i]["context"], sort_keys=True) for i in members}) == 1}
            repeated.append(row)
            if not row["answer_identical"]:
                conflicts.append(row)
    anomalies = []
    for entry in audit["schema_errors"]:
        item = items[entry["index"]]
        facts = []
        for side in ["agent_a", "agent_b"]:
            for title, index, sentence in item["supporting_facts"][side]:
                article = [a for a in item["context"][side] if a[0] == title]
                passages = [s for a in article for s in a[1]]
                facts.append({"side": side, "title_sha256": hashlib.sha256(title.encode()).hexdigest(),
                              "stated_index": index, "article_present": bool(article),
                              "exact_sentence_elsewhere_in_article": sentence in passages,
                              "whitespace_normalized_sentence_in_article": " ".join(sentence.split()) in [" ".join(s.split()) for s in passages],
                              "sentence_sha256": hashlib.sha256(sentence.encode()).hexdigest()})
        anomalies.append({"id": item["id"], "index": entry["index"], "facts": facts,
                          "context_raw_type": type(item.get("context_raw")).__name__})
    raw_types = Counter(type(x.get("context_raw")).__name__ for x in items)
    split = audit["split_proposal"]
    lengths = {}
    for side in ["agent_a", "agent_b"]:
        lengths[side] = sorted(d["sides"][side]["context_utf8_bytes"] for d in audit["details"])
    result = {"data_sha256": hashlib.sha256(body).hexdigest(), "unique_normalized_questions": len(questions),
              "duplicate_question_groups": len(repeated), "repeated_question_rows": repeated,
              "same_question_different_answers": conflicts,
              "same_question_same_context_groups": sum(r["context_identical"] for r in repeated),
              "context_raw_types": dict(raw_types),
              "source_lineage_fields": {k:sum(k in x for x in items) for k in ["id", "thread_id", "retry_count", "source_id", "_id"]},
              "anomaly_diagnostics": anomalies,
              "context_bytes": {side:{"min": values[0], "median_order_statistic": values[len(values)//2], "max": values[-1]}
                                for side, values in lengths.items()},
              "split_decision": "Pending_not_frozen: conservative evidence components yield 9/17/274 with giant242; no random row split or silent regrouping",
              "schema_decision": "Conditional: context mode is structurally usable; two support/context exact mismatches require explicit research disposition before capability question registry",
              "all_records_preserved": True, "model_calls": 0, "task_episodes": 0,
              "no_pretraining_contamination_claim": True}
    out = Path(os.environ["GOSC_OUTPUT_DIR"])
    (out/"data_followup.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["unique_normalized_questions", "duplicate_question_groups", "same_question_same_context_groups", "context_bytes", "split_decision"]}))


if __name__ == "__main__":
    main()
