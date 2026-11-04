"""Lightweight local hashes/receipts/source metadata only. No dataset analysis."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

LOG=Path(__file__).resolve().parent
ROOT=LOG.parents[2]
RUNS=ROOT/"research/sync/runs"


def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p,lf=False):
    b=p.read_bytes()
    return hashlib.sha256(b.replace(b"\r\n",b"\n") if lf else b).hexdigest()


def main():
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT).decode().strip()=="014b85dfc472c45d8ea5f15e83e0c1ed8e938daf"
    subprocess.run(["git","diff","--exit-code","HEAD","--","gosc","extensions","tests","tests_ext","scripts"],cwd=ROOT,check=True)
    frozen=read(RUNS/"hpc-native-information-freeze-20261030/outputs/frozen.json")
    assert all(sha(ROOT/p,True)==h for p,h in frozen["source_sha256"].items())
    prior=read(ROOT/"research/logs/masbench-data-review-2026-11-03/experiment_manifest.json")
    assert all(sha(ROOT/p)==h for p,h in prior["source_sha256"].items())
    names=["hpc-masbench-registry-v2-20261103","hpc-masbench-client-contract-20261103",
           "hpc-masbench-context-budget-20261103","hpc-masbench-client-contract-v2-20261103",
           "hpc-masbench-httpx-mock-20261103","hpc-masbench-client-contract-v3-20261103",
           "hpc-masbench-httpx-mock-v2-20261103"]
    rows=[]
    for name in names:
        p=RUNS/name;s=read(p/"status.json");m=read(p/"manifest.json")
        assert s["status"]=="completed" and s["exit_code"]==0
        assert not m["models"] and not m["seeds"]
        for a in read(p/"artifacts.json")["files"]:
            f=p/a["path"]
            assert f.stat().st_size==a["size"] and sha(f)==a["sha256"]
        row={"run_id":name,"status":s["status"],"seconds":s["elapsed_seconds"],"command":m["command"],
             "source_sync_id":m["source_sync_id"],"manifest_sha256":sha(p/"manifest.json")}
        if (p/"outputs/contracts.xml").exists():
            x=ET.parse(p/"outputs/contracts.xml").getroot().find("testsuite")
            assert int(x.attrib["errors"])==int(x.attrib["failures"])==0
            row["tests"]=int(x.attrib["tests"])
        rows.append(row)
    assert rows[1]["tests"]==119 and rows[3]["tests"]==123 and rows[5]["tests"]==147
    h=read(RUNS/names[6]/"outputs/httpx_mock_contract.json")
    assert h["tests"]==5 and h["failures"]==h["errors"]==h["actual_network_calls"]==h["actual_model_calls"]==0
    registry=RUNS/names[0]/"outputs/development_registry_v1.json"
    assert sha(registry)=="6d14229ae0dd85a5b3c88b9309fcf86e54fab2523a3701914a7f7ebc06500a86"
    assert read(registry)["registry_content_sha256"]=="94b20ff4e199f8e6dc9eeeae8b0a8f91767c00576906f5589387a1266f4a4f1a"
    source=read(RUNS/names[5]/"source_snapshot.json")
    entries={x["path"]:x for x in source["files"]}
    code=["extensions/masbench_reasoning/registry.py","extensions/masbench_reasoning/client.py",
          "tests_ext/test_masbench_reasoning_preparation.py","scripts/masbench_reasoning_client_contract.py",
          "scripts/masbench_reasoning_prepare_registry.py","scripts/masbench_reasoning_context_budget.py",
          "scripts/masbench_reasoning_http_mock.py"]
    for name in code:assert sha(ROOT/name,True)==entries[name]["remote_sha256"],name
    receipt=ROOT/"research/sync/receipts/20261103T072351Z-cbea65.json"
    assert read(receipt)["all_outputs_mirrored"]
    meta={"scope":"local file/hash/receipt management; not tests or data analysis",
          "baseline":"014b85dfc472c45d8ea5f15e83e0c1ed8e938daf","working_tree_dirty":True,
          "source_guard":len(frozen["source_sha256"]),"protected_review_sources_unchanged":True,
          "runs":rows,"final_pytest_tests":147,"separate_httpx_mock_tests":5,
          "current_code_matches_hpc_execution":True,"registry_file_sha256":sha(registry),
          "receipt":receipt.relative_to(ROOT).as_posix(),"all_outputs_mirrored":True,
          "model_calls":0,"actual_task_episodes":0,"training":False,"git_commit_or_push":False,
          "budget_proposal_execution_authorized":False,"effective_context_and_tokenizer_verified":False}
    (LOG/"experiment_manifest.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"file_management_passed","source_guard":meta["source_guard"],"pytest":147,"httpx_mock":5,"model_calls":0}))


if __name__=="__main__":main()
