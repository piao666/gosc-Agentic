"""HPC synthetic-only contract acceptance; no LLM or actual dataset episodes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from hpc_runs import require_hpc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    require_hpc()
    signal.alarm(120)
    out = Path(os.environ["GOSC_OUTPUT_DIR"])
    frozen = json.loads((ROOT/"research/sync/runs/hpc-native-information-freeze-20261030/outputs/frozen.json").read_text())

    def check_frozen():
        for name, digest in frozen["source_sha256"].items():
            body = (ROOT/name).read_bytes().replace(b"\r\n", b"\n")
            if hashlib.sha256(body).hexdigest() != digest:
                raise RuntimeError("Protected scientific source changed: "+name)

    check_frozen()
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    command = [sys.executable, "-m", "pytest", "-q", "tests_ext/test_masbench_reasoning_adapter.py",
               "-p", "no:cacheprovider", "--basetemp", str(Path(os.environ["GOSC_RUN_DIR"])/"pytest-tmp"),
               "--junitxml", str(out/"contracts.xml")]
    completed = subprocess.run(command, cwd=ROOT, env=env, timeout=100)
    check_frozen()
    sys.path.insert(0, str(ROOT))
    from extensions.masbench_reasoning.wire import ContractTransport, DL_ACK
    transport = ContractTransport(faults={(DL_ACK, 0, 0): "drop"})
    result = transport.transfer(0, 0, "SYNTHETIC跨片🙂".encode())
    trace = {"result": {k:v.hex() if isinstance(v, bytes) else v for k,v in result.items()},
             "events": transport.events, "cpu": transport.cpu, "totals": transport.totals()}
    (out/"wire_trace.json").write_text(json.dumps(trace, indent=2)+"\n")
    summary = {"execution_host": "hpc", "model_calls": 0, "task_episodes": 0,
               "fixture_source": "synthetic fixed strings only", "pytest_exit": completed.returncode,
               "protected_sources_unchanged": len(frozen["source_sha256"]),
               "actual_radio_deployment": False,
               "pending": ["GOSC stochastic Channel integration", "deployment CPU coefficient/time calibration",
                           "model chat/context/timeout capability", "actual task scientific efficacy"],
               "command": command}
    (out/"contract_acceptance.json").write_text(json.dumps(summary, indent=2)+"\n")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
