"""Independent stdlib evidence audit: no production parser/scorer imports."""
import argparse
from collections import Counter
import hashlib
import gzip
import json
import math
import os
from pathlib import Path
import re
import resource
import string
import struct
import tarfile
import xml.etree.ElementTree as ET
import zlib


def canonical(v, ascii=False):
    return json.dumps(v, ensure_ascii=ascii, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(v):
    return hashlib.sha256(v).hexdigest()


def audit_journal(rows):
    tip = "0" * 64
    http = Counter()
    inputs = outputs = 0
    for i, record in enumerate(rows):
        row = {k: v for k, v in record.items() if k != "hash"}
        assert row["seq"] == i and row["previous"] == tip
        assert digest(canonical(row, ascii=True)) == record["hash"]
        tip = record["hash"]
        e = row["event"]
        if e["kind"] == "v2-http":
            http[e["category"]] += 1
        if e["kind"] == "request":
            inputs += e["input"]
            outputs += e["output"]
    return dict(rows=len(rows), tip=tip, http=dict(http), reserved_input=inputs, reserved_output=outputs)


def audit_episode(item, condition):
    r = item["result"]
    assert r["completed"] and len(r["slots"]) == 6 and set(r["finals"]) == {"Alice", "Bob"}
    memory = [[], []]
    delivered = {m["source"]["turn"]: m for m in r["messages"] if m["delivered"]}
    initial = [r["slots"][0]["request"][:2], r["slots"][1]["request"][:2]]
    for t, slot in enumerate(r["slots"]):
        side = t % 2
        clock = dict(kind="PUBLIC_CLOCK", protocol="T3-R-v2-fair-final-candidate-v1",
                     speaker="Bob" if side else "Alice", stage="exchange" if t < 4 else "local_final", turn=f"t{t}")
        memory[side].append(dict(role="user", content=canonical(clock).decode()))
        expected = initial[side] + memory[side]
        assert slot["request"] == expected
        assert slot["request_sha256"] == digest(canonical(expected))
        raw = slot["raw"]
        response = slot["client_audit"]["response"]
        assert raw == response["choices"][0]["message"]["content"]
        assert digest(canonical(response)) == slot["client_audit"]["response_sha256"]
        memory[side].append(dict(role="assistant", content="" if raw is None else raw))
        if t in delivered:
            assert condition == "Full" and t < 4
            msg = delivered[t]
            body = bytes.fromhex(msg["body"]["utf8_or_wire_hex"]).decode()
            assert body == raw.replace("\r\n", "\n").strip(" \t\r\n")
            assert digest(body.encode()) == msg["source"]["payload_sha256"]
            assert msg["source"]["request_sha256"] == slot["request_sha256"]
            memory[1 - side].append(dict(role="user", content=canonical(dict(
                kind="PEER_MESSAGE", sender=clock["speaker"], turn=f"t{t}", text=body)).decode()))
    assert memory == r["memory"]
    assert all(m["source"]["turn"] < 4 for m in r["messages"])
    frames = [e for e in item["wire_events"] if e["event"] == "frame"]
    totals = Counter()
    for frame in frames:
        raw = bytes.fromhex(frame["raw_hex"])
        assert len(raw) == frame["bytes"] and zlib.crc32(raw[:-4]) == struct.unpack("!I", raw[-4:])[0]
        header = struct.unpack("!2sBBIIBBIHHH", raw[:24])
        assert header[0:2] == (b"MR", 1) and header[4] < 4
        assert len(raw) == 28 + header[-1]
        assert frame["uses"] == math.ceil(8 * len(raw) / frame["rate"])
        totals["wire_bytes"] += len(raw)
        totals["ul_uses" if frame["direction"] == "UL" else "dl_uses"] += frame["uses"]
    for key in ("wire_bytes", "ul_uses", "dl_uses"):
        assert r["wire_totals"][key] == totals[key]
    if condition == "No-A2A":
        assert not frames and not delivered and r["received_sources"] == [{}, {}]
    j = audit_journal(item["journal"])
    assert j["reserved_output"] == 3072
    assert dict(item["counters"]) == {k: j["http"].get(k, 0) for k in item["counters"]}
    assert item["counters"]["get"] == 19 and item["counters"]["generation"] == 6
    assert all(t["model_inference"] is False and t["elapsed_seconds"] < 1 for t in item["worker_traces"])
    return dict(journal=j, frames=len(frames), requests=6, local_finals=2, memory_rebuilt=True)


def independent_f1(text):
    if text is None:
        return 0.
    def tokens(value):
        value = "".join(c for c in value.lower() if c not in string.punctuation)
        return re.sub(r"\b(a|an|the)\b", " ", value).split()
    gold, answer = tokens("red blue"), tokens(text)
    if not answer:
        return 0.
    return 2 * sum((Counter(gold) & Counter(answer)).values()) / (len(gold) + len(answer))


def main():
    # This entry itself is invoked through hpc_runs run; no application import.
    if os.name != "posix" or os.getuid() != 8301880:
        raise RuntimeError("HPC-only audit")
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    p = argparse.ArgumentParser()
    p.add_argument("--contract-run", required=True)
    p.add_argument("--pressure-run")
    p.add_argument("--pressure-summary-run")
    p.add_argument("--legacy-run")
    p.add_argument("--counter-recheck-run")
    p.add_argument("--baseline", required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    run = root / "research/sync/runs" / args.contract_run / "outputs"
    results = json.loads((run / "contract_results.json").read_bytes())
    assert results["exit_code"] == 0 and results["real_model_calls"] == results["service_requests"] == 0
    assert set(results["cases"]) == {f"C{i:02}" for i in range(1, 33)}
    assert all(c["outcome"] == "passed" and c["call_variants"] > 0 for c in results["cases"].values())
    xml = ET.parse(run / "pytest.xml")
    assert not xml.findall(".//failure") and not xml.findall(".//error") and not xml.findall(".//skipped")
    for key in results["cases"]:
        assert any(("test_" + key + "_") in e.get("name", "") for e in xml.findall(".//testcase"))
    complete = json.loads((run / "evidence/C01_complete.json").read_bytes())
    rebuilt = {condition: audit_episode(item, condition) for condition, item in complete.items()}
    vectors = []
    for path in sorted((run / "evidence").glob("C14_*.json")):
        v = json.loads(path.read_bytes())
        raw_answers = []
        for text in v["raw_finals"]:
            match = re.fullmatch(r"(?:Alice|Bob): FINAL\n<E>LOCAL</E>\n<A>([^<>\r\n]+)</A>", text)
            raw_answers.append(match[1] if match else None)
        fa, fb, na, nb = map(independent_f1, raw_answers)
        sf, sn = (fa + fb) / 2, (na + nb) / 2
        assert math.isclose(sf, v["Full"]["mean_F1"]) and math.isclose(sn, v["No_A2A"]["mean_F1"])
        assert math.isclose(sf - sn, v["paired"]["Delta_F1"], abs_tol=1e-15)
        vectors.append(path.name)
    assert len(vectors) == 5
    journals = 0
    with tarfile.open(run / "fixture-journals.tar.gz") as archive:
        members = {m.name: m for m in archive.getmembers()}
        assert all(m.isfile() and not Path(m.name).is_absolute() and ".." not in Path(m.name).parts
                   for m in members.values())
        for name, member in members.items():
            if Path(name).name != "ledger.jsonl":
                continue
            rows = [json.loads(x) for x in archive.extractfile(member).read().splitlines()]
            audit_journal(rows)
            journals += 1
            for row in rows:
                e = row["event"]
                if e["kind"] == "bytes":
                    target = (Path(name).parent / "artifacts" / e["path"]).as_posix()
                    if target not in members:
                        # C28's intentionally failed write has a permanent
                        # reservation, fence and no successful artifact.
                        assert any(r["event"]["kind"] == "v2-fence" for r in rows)
                    else:
                        body = archive.extractfile(members[target]).read()
                        assert len(body) == e["count"] and digest(body) == e["sha256"]
    failures = []
    for path in (run / "evidence").glob("C20_*.json"):
        value = json.loads(path.read_bytes())
        assert value["state"]["fenced"] and value["state"]["outputs"] == 512
        assert len(value["trace"]) == 1 and not value["result"]["completed"]
        failures.append(path.name)
    assert len(failures) == 4
    baseline = json.loads((root / args.baseline).read_bytes())
    frozen = []
    for record in baseline["frozen_files"]:
        raw = (root / record["path"]).read_bytes().replace(b"\r\n", b"\n")
        assert digest(raw) == record["LF_sha256"], record["path"]
        frozen.append(record["path"])
    pressure = None
    if args.pressure_run:
        out = root / "research/sync/runs" / args.pressure_run / "outputs"
        pressure = json.loads((out / "pressure.json").read_bytes())
        assert pressure["model_calls"] == 0 and pressure["real_task_bodies"] is False
        reqs = json.loads((out / "synthetic-requests.json").read_bytes())
        assert len(reqs) == len(pressure["rows"])
        for req, row in zip(reqs, pressure["rows"]):
            assert digest(canonical(req)) == row["sha256"] and len(canonical(req)) == row["serialized_bytes"]
        if "rows" in pressure["exact_counter"]:
            reply = json.loads((out / "counter-raw.json").read_bytes())
            assert reply["vocab_only"] and not reply["tensor_context_created"]
            assert digest((out / "counter-input.json").read_bytes()) == reply["input_sha256"]
            for row in reply["requests"]:
                assert digest(row["rendered"].encode()) == row["rendered_sha256"]
                assert row["token_count"] == len(row["token_ids"])
                assert digest(canonical(row["token_ids"])) == row["token_ids_json_sha256"]
    exact_counter_passed = bool(pressure and "rows" in pressure.get("exact_counter", {}))
    retained_pressure = None
    if args.pressure_summary_run:
        summary_dir = root / "research/sync/runs" / args.pressure_summary_run / "outputs"
        retained_pressure = json.loads((summary_dir / "pressure_summary.json").read_bytes())
        src = root / "research/sync/runs" / retained_pressure["source_run"] / "outputs"
        reqs = json.loads((src / "synthetic-requests.json").read_bytes())
        assert retained_pressure["byte_pressure_verified"] and len(reqs) == len(retained_pressure["rows"])
        for req, row in zip(reqs, retained_pressure["rows"]):
            assert digest(canonical(req)) == row["sha256"] and len(canonical(req)) == row["serialized_bytes"]
        for filename, field in [("synthetic-requests.json", "requests_sha256"),
                                ("counter-input.json", "counter_input_sha256"),
                                ("counter-stderr.log", "counter_stderr_sha256")]:
            assert digest((src / filename).read_bytes()) == retained_pressure[field]
        assert retained_pressure["exact_counter"]["status"] == "failed_resource_limit"
        assert b"runtime: out of memory" in (src / "counter-stderr.log").read_bytes()
    counter_recheck = None
    if args.counter_recheck_run:
        counter_dir = root / "research/sync/runs" / args.counter_recheck_run / "outputs"
        counter_recheck = json.loads((counter_dir / "counter_recheck.json").read_bytes())
        process = json.loads((counter_dir / "process.json").read_bytes())
        dispatch = json.loads((counter_dir / "dispatch.json").read_bytes())
        assert counter_recheck["acceptance_passed"] and counter_recheck["real_model_calls"] == 0
        assert counter_recheck["additional_fake_generations"] == 0 and counter_recheck["total_helper_attempts_this_task"] == 2
        assert process["returncode"] == 0 and process["hard_AS_bytes"] == 2 * 1024**3
        assert process["elapsed_seconds"] <= 20 and process["peak_RSS_observed_bytes"] <= 512 * 1024**2
        src = root / "research/sync/runs" / counter_recheck["source_run"] / "outputs"
        input_bytes = (src / "counter-input.json").read_bytes()
        assert digest(input_bytes) == dispatch["input_sha256"] == counter_recheck["input_sha256"]
        assert dispatch["attempt"] == 1 and dispatch["real_model"] is False
        raw = gzip.decompress((counter_dir / "counter-raw.json.gz").read_bytes())
        assert digest(raw) == counter_recheck["raw_stdout_sha256"]
        reply = json.loads(raw)
        assert reply["vocab_only"] is True and reply["tensor_context_created"] is False
        assert reply["input_sha256"] == digest(input_bytes)
        messages = [x["messages"] for x in json.loads(input_bytes)["requests"]]
        assert len(messages) == len(reply["requests"]) == len(counter_recheck["rows"])
        for req, row, summary in zip(messages, reply["requests"], counter_recheck["rows"]):
            assert digest(canonical(req)) == summary["request_sha256"]
            assert len(row["token_ids"]) == row["token_count"] == summary["tokens"]
            assert digest(canonical(row["token_ids"])) == row["token_ids_json_sha256"]
            assert digest(row["rendered"].encode()) == row["rendered_sha256"] == summary["rendered_sha256"]
            assert len(row["rendered"].encode()) == row["utf8_bytes"] == summary["rendered_bytes"]
        exact_counter_passed = True
    legacy_cases = None
    if args.legacy_run:
        legacy_dir = root / "research/sync/runs" / args.legacy_run / "outputs"
        legacy = json.loads((legacy_dir / "legacy_results.json").read_bytes())
        assert legacy["exit_code"] == 0 and legacy["real_model_calls"] == 0
        old_xml = ET.parse(legacy_dir / "pytest.xml")
        assert not old_xml.findall(".//failure") and not old_xml.findall(".//error")
        assert not old_xml.findall(".//skipped")
        legacy_cases = len(old_xml.findall(".//testcase"))
    artifact = dict(acceptance_passed=exact_counter_passed, contract_acceptance_passed=True,
                    exact_counter_acceptance_passed=exact_counter_passed,
                    counter_recheck_run=args.counter_recheck_run,
                    byte_pressure_verified=bool(pressure or retained_pressure),
                    overall_engineering="Go" if exact_counter_passed else "Blocked: exact counter resource validation incomplete",
                    contract_ids=sorted(results["cases"]),
                    pytest_cases=len(xml.findall(".//testcase")), rebuilt=rebuilt,
                    preserved_negative_scenarios=failures, frozen_files_verified=frozen,
                    independent_scoring_vectors=vectors, raw_journals_verified=journals,
                    pressure_included=bool(pressure or retained_pressure), legacy_fresh_cases=legacy_cases, real_model_calls=0,
                    support="new model-free engineering evidence only; no real deployment or capability")
    dest = Path(os.environ["GOSC_OUTPUT_DIR"]) / "independent_audit.json"
    dest.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps({k: artifact[k] for k in ("acceptance_passed", "pytest_cases", "real_model_calls")}))


if __name__ == "__main__":
    main()
