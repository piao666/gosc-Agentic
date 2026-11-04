"""HPC read-only byte/context preflight inventory; no token approximation or LLM."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts"))
from hpc_runs import require_hpc
from extensions.masbench_reasoning.application import LocalAgent, private_view
from extensions.masbench_reasoning.registry import digest


def main():
    require_hpc()
    signal.alarm(120)
    registry_path = ROOT/"research/sync/runs/hpc-masbench-registry-v2-20261103/outputs/development_registry_v1.json"
    registry = json.loads(registry_path.read_text())
    expected = registry.pop("registry_content_sha256")
    assert digest(registry) == expected
    body = (ROOT/"research/sync/runs/hpc-masbench-data-audit-v2-20261103/outputs/reasoning.json").read_bytes()
    assert hashlib.sha256(body).hexdigest() == registry["data_sha256"]
    items = json.loads(body)
    prompts_path = ROOT/"research/logs/masbench-adapter-contract-2026-11-03/reference/Reasoning/src/prompts.py"
    raw = prompts_path.read_bytes()
    assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest() == "4a39061fe2840f177f4169223d188448469e2ada"
    templates = runpy.run_path(str(prompts_path))
    rows = []
    for selected in registry["selected"]:
        item = items[selected["row"]]
        for style in ["base", "protocol"]:
            template = templates["QA_INFO_EXCHANGE_PROMPT"+("_PROTOCOL" if style == "protocol" else "")]
            for name in ["Alice", "Bob"]:
                agent = LocalAgent(private_view(item, name), template)
                request = agent.request()
                rows.append({"record_id": selected["record_id"], "style": style, "agent": name,
                             "system_content_utf8_bytes": len(agent.system.encode()),
                             "request_json_utf8_bytes": len(json.dumps(request, ensure_ascii=False).encode()),
                             "request_content_sha256": digest(request), "exact_model_tokens": None,
                             "token_count_status": "Pending_exact_deployed_template_tokenizer"})
    independent = ROOT/".local/envs/masbench-reasoning-v1/bin/python"
    code = "import importlib.util,json,sys;print(json.dumps({'python':sys.version,'available':{n:importlib.util.find_spec(n) is not None for n in ['openai','httpx','transformers','tokenizers','sentencepiece','tiktoken','llama_cpp','gguf']}}))"
    env = subprocess.run([str(independent),"-c",code],capture_output=True,text=True,timeout=15,check=True)
    summary = {"registry_content_sha256": expected, "model_calls":0, "model_loaded":False,
               "initial_requests": rows, "independent_environment":json.loads(env.stdout),
               "candidate_context_tokens":32768, "effective_context_verified":False,
               "tokenizer_binding_verified":False,
               "context_formula":"exact_tokens(deployed_chat_template(system + own_full_history + delivered_peer_visible_and_local_board_history)) + max_output_tokens <= effective_num_ctx; check each call, never trim",
               "candidate_calls":{"synthetic_preflight":2,"tasks":96,"total":98},
               "candidate_max_output_tokens_per_call":512,"candidate_total_output_tokens_cap":50176,
               "candidate_total_prompt_tokens_cap":3161088,
               "prompt_cap_scope":"98*(32768-512), ceiling only, not measured tokens or runtime projection",
               "candidate_wall_seconds":6000,"candidate_operation_timeout_seconds":60,
               "candidate_storage_bytes":256*1024*1024,"actual_model_diagnostic_authorized":False,
               "budget_status":"conditional_proposal_not_executable_context_and_runtime_preflight_pending"}
    out = Path(os.environ["GOSC_OUTPUT_DIR"])
    (out/"context_budget_preflight.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({"initial_requests":len(rows),"max_initial_system_bytes":max(r["system_content_utf8_bytes"] for r in rows),
                      "exact_model_tokens":None,"independent_environment":summary["independent_environment"],
                      "model_calls":0,"budget_status":summary["budget_status"]}))


if __name__ == "__main__":
    main()
