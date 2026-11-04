"""HPC-only P2 pure fake-client acceptance. Does not contact any model service."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import hashlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from hpc_runs import require_hpc


def main():
    require_hpc()
    signal.alarm(120)
    output = Path(os.environ["GOSC_OUTPUT_DIR"])
    frozen = json.loads((ROOT/"research/sync/runs/hpc-native-information-freeze-20261030/outputs/frozen.json").read_text())
    for path, digest in frozen["source_sha256"].items():
        assert hashlib.sha256((ROOT/path).read_bytes().replace(b"\r\n",b"\n")).hexdigest() == digest
    command = [sys.executable, "-m", "pytest", "-q", "tests_ext/test_masbench_reasoning_adapter.py",
               "tests_ext/test_masbench_reasoning_preparation.py", "-p", "no:cacheprovider",
               "--basetemp", str(Path(os.environ["GOSC_RUN_DIR"])/"pytest-tmp"),
               "--junitxml", str(output/"contracts.xml")]
    completed = subprocess.run(command, env=dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"),
                               cwd=ROOT, timeout=100)
    summary = {"execution_host":"hpc", "pytest_exit":completed.returncode, "command":command,
               "model_calls":0, "actual_task_episodes":0, "new_network_calls":0,
               "backend":"fixed synthetic response objects and fake HTTP; socket connections forbidden",
               "source_guard_count":len(frozen["source_sha256"]),
               "live_chat_context_capability":"Pending_not_tested", "training":False,
               "independent_reasoning_environment_not_modified":True}
    (output/"client_contract_acceptance.json").write_text(json.dumps(summary,indent=2)+"\n")
    # A small inspectable binding/usage audit, also a pure in-process backend.
    sys.path.insert(0,str(ROOT))
    from extensions.masbench_reasoning.client import ClientConfig, ContextBinding, ControlledClient
    class Backend:
        is_live=False
        def identity(self, timeout):
            return {"model":"fixture-only", "manifest_sha256":"a"*64}
        def create(self, payload, timeout):
            return {"model":"fixture-only", "choices":[{"finish_reason":"stop", "message":{"content":"SYNTHETIC <A>ok</A>"}}],
                    "usage":{"prompt_tokens":10,"completion_tokens":2,"total_tokens":12}}
    client = ControlledClient(ClientConfig("fixture-only","a"*64,32768), Backend(), lambda _:10,
                              ContextBinding("a"*64,32768,"fixture-counter","b"*64,True))
    client.generate([{"role":"system","content":"SYNTHETIC private view only"}])
    (output/"synthetic_client_audit.json").write_text(json.dumps(client.audit,indent=2)+"\n")
    if sum(p.stat().st_size for p in output.iterdir()) > 16*1024*1024:
        raise RuntimeError("Contract artifact cap exceeded")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
