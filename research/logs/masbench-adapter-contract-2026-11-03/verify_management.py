"""Local lightweight file/hash/receipt verification; never parse task dataset."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

LOG = Path(__file__).resolve().parent
ROOT = LOG.parents[2]
RUNS = ROOT/"research/sync/runs"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path, lf=False):
    body = path.read_bytes()
    return hashlib.sha256(body.replace(b"\r\n", b"\n") if lf else body).hexdigest()


def main():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip() == "014b85dfc472c45d8ea5f15e83e0c1ed8e938daf"
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", "gosc", "extensions", "tests", "tests_ext", "scripts"], cwd=ROOT, check=True)
    frozen = read(RUNS/"hpc-native-information-freeze-20261030/outputs/frozen.json")
    assert all(sha(ROOT/name, True) == expected for name, expected in frozen["source_sha256"].items())
    prior = read(ROOT/"research/logs/masbench-reasoning-static-2026-10-30/experiment_manifest.json")
    assert all(sha(ROOT/p) == expected for p, expected in prior["protected_previous_report_sha256"].items())
    names = ["hpc-masbench-data-audit-20261103", "hpc-masbench-data-audit-v2-20261103",
             "hpc-masbench-adapter-contract-20261103", "hpc-masbench-data-followup-20261103",
             "hpc-masbench-adapter-contract-v2-20261103", "hpc-masbench-adapter-contract-v3-20261103"]
    records = []
    for name in names:
        directory = RUNS/name
        status, manifest = read(directory/"status.json"), read(directory/"manifest.json")
        assert manifest["execution_host"] == "n1" and not manifest["seeds"] and not manifest["models"]
        assert status["status"] == ("failed" if name == names[0] else "completed")
        assert status["exit_code"] == (1 if name == names[0] else 0)
        for item in read(directory/"artifacts.json")["files"]:
            path = directory/item["path"]
            assert path.stat().st_size == item["size"] and sha(path) == item["sha256"]
        row = {"run_id": name, "status": status["status"], "exit_code": status["exit_code"],
               "elapsed_seconds": status["elapsed_seconds"], "command": manifest["command"],
               "source_sync_id": manifest["source_sync_id"], "manifest_sha256": sha(directory/"manifest.json")}
        xml = directory/"outputs/contracts.xml"
        if xml.exists():
            suite = ET.parse(xml).getroot().find("testsuite")
            row["tests"] = int(suite.attrib["tests"])
            assert int(suite.attrib["errors"]) == int(suite.attrib["failures"]) == 0
        records.append(row)
    assert records[2]["tests"] == 61 and records[4]["tests"] == records[5]["tests"] == 67
    data = RUNS/names[1]/"outputs/reasoning.json"
    assert data.stat().st_size == 11996959
    assert sha(data) == "ce65640b566e70098c540b9c814768c9ff5d8544a4cb25162a3872ac9c3bb331"
    # Check the final test used the exact current implementation, not an earlier
    # file copied after execution. This is source/metadata management only.
    source = read(RUNS/names[-1]/"source_snapshot.json")
    entries = {x["path"]:x for x in source["files"]}
    implementation = sorted((ROOT/"extensions/masbench_reasoning").glob("*.py"))
    implementation += [ROOT/"tests_ext/test_masbench_reasoning_adapter.py", ROOT/"scripts/masbench_reasoning_contract.py"]
    for path in implementation:
        name = path.relative_to(ROOT).as_posix()
        assert sha(path, True) == entries[name]["remote_sha256"], name
    receipts = []
    for path in sorted((ROOT/"research/sync/receipts").glob("20261103*.json")):
        receipt = read(path)
        if receipt.get("all_outputs_mirrored"):
            receipts.append(path.relative_to(ROOT).as_posix())
    assert receipts
    result = {"scope": "local file/hash/receipt metadata only; not project tests or data analysis",
              "frozen_sources_unchanged": len(frozen["source_sha256"]),
              "previous_reports_unchanged": True, "dataset_sha256": sha(data), "records": records,
              "final_test_code_matches_synced_current_code": True, "complete_receipts": receipts,
              "model_calls": 0, "actual_task_episodes": 0, "training": False, "git_commit_or_push": False}
    if (LOG/"final_upload_status.json").exists():
        result["final_documentation_upload"] = read(LOG/"final_upload_status.json")
    (LOG/"experiment_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status": "file_management_passed", "frozen": result["frozen_sources_unchanged"],
                      "final_contract_tests": records[-1]["tests"], "model_calls": 0}))


if __name__ == "__main__":
    main()
