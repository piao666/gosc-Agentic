"""HPC-only versioned grouping review and development reservation, no models."""
import hashlib
import json
import os
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/"scripts"))
from hpc_runs import require_hpc
from extensions.masbench_reasoning.registry import build_registry, digest


def main():
    require_hpc()
    signal.alarm(120)
    source = ROOT/"research/sync/runs/hpc-masbench-data-audit-v2-20261103/outputs"
    body = (source/"reasoning.json").read_bytes()
    sha = hashlib.sha256(body).hexdigest()
    assert sha == "ce65640b566e70098c540b9c814768c9ff5d8544a4cb25162a3872ac9c3bb331"
    old = json.loads((source/"data_audit.json").read_text())
    items = json.loads(body)
    result = build_registry(items, sha, {row["index"] for row in old["schema_errors"]})
    assert len(result["legacy"]["components"]) == old["split_proposal"]["components"]
    assert max(map(len, result["legacy"]["components"])) == old["split_proposal"]["largest"]
    groups = result["corrected"]["components"]
    out = Path(os.environ["GOSC_OUTPUT_DIR"])
    # P0 artifact is written before the P1 reservation. No source data rewrites.
    audit = {k:v for k,v in result.items() if k in {"version", "data_sha256", "legacy", "corrected", "structural_graphs", "membership_changed_pairs", "families", "anomaly_rows"}}
    (out/"grouping_review_v2.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    registry = {k:v for k,v in result.items() if k not in {"legacy", "corrected", "membership_changed_pairs"}}
    registry["grouping_artifact_sha256"] = hashlib.sha256((out/"grouping_review_v2.json").read_bytes()).hexdigest()
    registry["component_rows"] = groups
    registry["selected_public_initial_view_bytes"] = []
    from extensions.masbench_reasoning.application import private_view
    for entry in result["selected"]:
        item = items[entry["row"]]
        registry["selected_public_initial_view_bytes"].append({"record_id": entry["record_id"],
                    "question_utf8_bytes": len(item["question"].encode()),
                    "Alice_context_utf8_bytes": len(private_view(item, "Alice").information.encode()),
                    "Bob_context_utf8_bytes": len(private_view(item, "Bob").information.encode())})
    # Registry SHA binds all content, not just the compact selection payload.
    registry["registry_content_sha256"] = digest(registry)
    (out/"development_registry_v1.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    summary = {"version": result["version"], "data_sha256": sha, "rows": len(items),
               "question_families": len(result["families"]),
               "legacy_components": len(result["legacy"]["components"]),
               "legacy_largest": max(map(len, result["legacy"]["components"])),
               "corrected_components": len(groups), "corrected_largest": max(map(len, groups)),
               "changed_membership_pairs": len(result["membership_changed_pairs"]),
               "rejected_empty_keys": len(result["corrected"]["rejected_keys"]),
               "structural_graphs": result["structural_graphs"],
               "status": result["status"], "selected": result["selected"],
               "development_reserved_rows": len(result["development_reserved_rows"]),
               "not_reserved_rows": len(result["not_reserved_rows"]),
               "reserved_components": len(result["reserved_components"]),
               "registry_content_sha256": registry["registry_content_sha256"],
               "model_calls": 0, "actual_model_exposure": False,
               "formal_split_frozen": False, "pilot_model_execution_authorized": False}
    (out/"preparation_summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    if sum(p.stat().st_size for p in out.iterdir()) > 16*1024*1024:
        raise RuntimeError("Preparation artifact budget exceeded")
    print(json.dumps(summary))
    if len(result["selected"]) != 4:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
