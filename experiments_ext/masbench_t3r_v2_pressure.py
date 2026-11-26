"""Invented full-history byte pressure, optional pinned vocabulary-only counts.

Never imports T2 demand/development_inputs, a dataset loader or live driver.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

from extensions.masbench_reasoning.application import PrivateView
from extensions.masbench_reasoning.fair_final_v2 import canonical, run_episode, sha
from extensions.masbench_reasoning.fair_final_v2_guard import FairLedger, FixtureDriver, FixtureCounter, jsonable

HELPER = Path("/tmp/gosc-hpc-masbench-context-build-v3-20261116/context-counter")
HELPER_SHA = "e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5"
TEMPLATE_SHA = "eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175"
MANIFEST_SHA = "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"
WEIGHT = "sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vocab_count(root, requests, out):
    """Explicit vocabulary-only executable, one batch <=20s; zero inference."""
    models = root.parents[1] / "models/ollama-gosc"
    template = models / "blobs" / ("sha256-" + TEMPLATE_SHA)
    manifest = models / "manifests/registry.ollama.ai/library/qwen2.5/7b"
    if digest(HELPER) != HELPER_SHA or digest(template) != TEMPLATE_SHA or digest(manifest) != MANIFEST_SHA:
        raise RuntimeError("offline_counter_pin")
    layer, = [x for x in json.loads(manifest.read_bytes())["layers"]
              if x["mediaType"] == "application/vnd.ollama.image.model"]
    if layer["digest"].replace(":", "-") != WEIGHT or (models / "blobs" / WEIGHT).stat().st_size != layer["size"]:
        raise RuntimeError("vocabulary_blob_manifest_binding")
    payload = canonical(dict(model_path=str(models / "blobs" / WEIGHT), template_path=str(template),
                             template_sha256=TEMPLATE_SHA,
                             requests=[dict(messages=r) for r in requests], texts=[])).encode("utf-8")
    (out / "counter-input.json").write_bytes(payload)
    start = time.monotonic()
    proc = subprocess.run([str(HELPER)], input=payload, capture_output=True, timeout=20,
                          env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    (out / "counter-stderr.log").write_bytes(proc.stderr)
    if proc.returncode or len(proc.stdout) > 6 * 1024**2:
        raise RuntimeError("vocabulary_counter_exit_or_output")
    (out / "counter-raw.json").write_bytes(proc.stdout)
    reply = json.loads(proc.stdout)
    if (reply["vocab_only"] is not True or reply["tensor_context_created"] is not False
            or reply["template_sha256"] != TEMPLATE_SHA or reply["input_sha256"] != hashlib.sha256(payload).hexdigest()
            or reply["add_special"] is not False or reply["parse_special"] is not True
            or len(reply["requests"]) != len(requests)):
        raise RuntimeError("offline_counter_contract")
    rows = []
    for messages, row in zip(requests, reply["requests"]):
        if (sha(row["rendered"]) != row["rendered_sha256"]
                or len(row["rendered"].encode("utf-8")) != row["utf8_bytes"]
                or len(row["token_ids"]) != row["token_count"]
                or sha(canonical(row["token_ids"])) != row["token_ids_json_sha256"]):
            raise RuntimeError("complete_render_token_binding")
        rows.append(dict(request_sha256=sha(canonical(messages)), tokens=row["token_count"],
                         rendered_sha256=row["rendered_sha256"], rendered_bytes=row["utf8_bytes"],
                         fits_16384_with_512=row["token_count"] + 512 <= 16384))
    return dict(rows=rows, elapsed_seconds=time.monotonic() - start, helper_sha256=HELPER_SHA,
                model_inference=False, tensor_context_created=False,
                limitation="GGUF size+manifest binding; full weight blob not rehashed; no service comparison/deployment validation")


def main():
    from scripts.hpc_runs import require_hpc, ROOT
    require_hpc()
    parser = argparse.ArgumentParser()
    parser.add_argument("--vocab-only", action="store_true")
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    out = Path(os.environ["GOSC_OUTPUT_DIR"])
    # Python denies sockets; the optional executable is pinned and vocab-only.
    def deny_socket(event, unused):
        if event.startswith("socket."):
            raise PermissionError("no_network_pressure")
    import sys
    sys.addaudithook(deny_socket)
    requests, rows = [], []
    start = time.monotonic()
    for name, char in (("ascii", "x"), ("multibyte", "彩"), ("json_escape", '"')):
        for condition in ("Full", "No-A2A"):
            body = char * ((4096 - 24) // len(char.encode("utf-8")))
            outputs = [f'{"Alice" if t % 2 == 0 else "Bob"}: MESSAGE\n<R>{body}</R>' for t in range(4)]
            outputs += ["Alice: FINAL\n<E>LOCAL</E>\n<A>red blue</A>", "Bob: FINAL\n<E>LOCAL</E>\n<A>red blue</A>"]
            plan = [dict(id="invented-pressure", family="synthetic-only", condition=condition, partition="task")]
            with FairLedger(out / (name + "-" + condition), plan) as ledger:
                # Isolate byte/IPC pressure from invented token units. The
                # default bytes/4 fixture estimator is NOT a qwen tokenizer
                # and must not decide real-window feasibility. Exact tokens
                # are obtained for these immutable requests below, offline.
                driver = FixtureDriver(ledger, outputs, counter=FixtureCounter(tokens=1))
                private = "synthetic " * 2048
                v = [PrivateView("Alice", "Bob", "Invented pressure question.", private),
                     PrivateView("Bob", "Alice", "Invented pressure question.", private)]
                result = run_episode(v, driver, condition, "invented-pressure")
                for slot in result["slots"]:
                    if "request" in slot:
                        req = slot["request"]
                        requests.append(req)
                        rows.append(dict(case=name, condition=condition, turn=slot["turn"],
                                         serialized_bytes=len(canonical(req).encode("utf-8")),
                                         sha256=sha(canonical(req)), status=slot["status"]))
                if not result["completed"] and result["error"] != "IPC_packet_or_cumulative_cap":
                    raise RuntimeError("unexpected_pressure_failure:" + str(result["error"]))
    (out / "synthetic-requests.json").write_text(canonical(requests) + "\n", encoding="utf-8")
    counts = vocab_count(ROOT, requests, out) if args.vocab_only else dict(status="not_run", scope="fixture counts only")
    summary = dict(schema="t3rv2i-synthetic-pressure-v1", rows=rows, exact_counter=counts,
                   fixture_counter_scope="constant 1 synthetic unit for byte-path replay; real window judgments use offline vocab-only counts only",
                   elapsed_seconds=time.monotonic() - start, model_calls=0, real_task_bodies=False,
                   max_serialized_bytes=max(r["serialized_bytes"] for r in rows),
                   self_max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   hard_deployment_resources="Pending; synthetic observations do not establish service/GPU ceilings")
    (out / "pressure.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if sum(p.stat().st_size for p in out.rglob("*") if p.is_file()) > 8 * 1024**2:
        raise RuntimeError("frozen_output_cap")
    print(json.dumps({k: summary[k] for k in ("elapsed_seconds", "max_serialized_bytes", "model_calls")}))


if __name__ == "__main__":
    main()
