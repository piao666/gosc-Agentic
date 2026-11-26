"""HPC-only C01-C32 entry; no model, service or task data entry point."""
import argparse
import json
import os
from pathlib import Path
import resource
import sys
import tarfile
import time


def deny_external(event, args):
    if event in {"socket.__new__", "socket.connect", "socket.getaddrinfo"}:
        raise PermissionError("v2-contract-network-denied")
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = os.fsdecode(args[0])
        if (Path(path).name in {"reasoning.json", "controlled_read_aid.private.json"}
                or any(p in Path(path).parts for p in (".ssh", ".workbuddy"))
                or Path(path).name.startswith(".env")):
            raise PermissionError("v2-contract-data-denied")


class EvidencePlugin:
    def __init__(self, out):
        self.out, self.rows = out, []

    def pytest_runtest_logreport(self, report):
        self.rows.append(dict(nodeid=report.nodeid, phase=report.when,
                              outcome=report.outcome, duration=report.duration))
        files = list(self.out.rglob("*"))
        if len(files) > 512 or sum(p.stat().st_size for p in files if p.is_file()) > 8 * 1024**2:
            raise RuntimeError("frozen_output_cap")


def main():
    from scripts.hpc_runs import require_hpc
    require_hpc()
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy", action="store_true")
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    cpu_limit = 60 if args.legacy else 120
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**2, 8 * 1024**2))
    out = Path(os.environ["GOSC_OUTPUT_DIR"])
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    sys.addaudithook(deny_external)
    import pytest
    plugin = EvidencePlugin(out)
    start = time.monotonic()
    test_file = "tests_ext/test_masbench_reasoning_adapter.py" if args.legacy else "tests_ext/test_masbench_fair_final_v2.py"
    code = pytest.main(["-q", test_file, "-p", "no:cacheprovider",
                       "--basetemp", str(Path(os.environ["GOSC_RUN_DIR"]) / "pytest-tmp"),
                       "--junitxml", str(out / "pytest.xml")], plugins=[plugin])
    # pytest's convenience symlinks are excluded; preserve every regular fake
    # ledger/artifact in a complete transfer artifact, including failure runs.
    temp = Path(os.environ["GOSC_RUN_DIR"]) / "pytest-tmp"
    with tarfile.open(out / "fixture-journals.tar.gz", "w:gz", compresslevel=1) as archive:
        transient_count = transient_bytes = 0
        for path in sorted(temp.rglob("*")):
            if path.is_file() and not path.is_symlink():
                transient_count += 1
                transient_bytes += path.stat().st_size
                if transient_count > 4096 or transient_bytes > 16 * 1024**2:
                    raise RuntimeError("frozen_transient_cap")
                archive.add(path, arcname=path.relative_to(temp), recursive=False)
    if args.legacy:
        (out / "legacy_results.json").write_text(json.dumps(dict(exit_code=int(code), reports=plugin.rows,
            elapsed_seconds=time.monotonic() - start, real_model_calls=0,
            scope="fresh legacy synthetic regression, not evidence for C01-C32"), indent=2) + "\n")
        return int(code)
    cases = {}
    for i in range(1, 33):
        key = f"C{i:02}"
        matches = [r for r in plugin.rows if ("test_" + key + "_") in r["nodeid"]]
        calls = [r for r in matches if r["phase"] == "call"]
        cases[key] = dict(outcome="passed" if calls and all(r["outcome"] == "passed" for r in matches)
                         else "failed-or-not-run", call_variants=len(calls), reports=matches)
    value = dict(schema="fair-final-v2-contract-evidence-v1", exit_code=int(code), cases=cases,
                 reports=plugin.rows, elapsed_seconds=time.monotonic() - start,
                 self_max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 real_model_calls=0, service_requests=0, data_bodies_used=False,
                 counter_scope="fixture units, not qwen tokens", network_policy="Python audit hook + fixture seccomp",
                 actual_deployment="not_run", scientific_capability="not_evaluated")
    (out / "contract_results.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
