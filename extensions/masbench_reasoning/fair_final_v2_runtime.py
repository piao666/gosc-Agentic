"""Independent six-slot application; probe approval cannot authorize tasks.

The frozen fixture entry remains unchanged. New fake integration compares
every request, history, final and frame against that entry.
"""
import json
from .fair_final_v2 import Agent, VERSION, SCHEDULE, canonical, sha, parse_output
from .client import ClientFailure
from .execution_safety import SafetyError

def run_episode(views, driver, condition, episode_id):
    """Six opportunities through the independent v2 live application entry.

    No record/gold, controller dictionary, callback or global board argument.
    Infrastructure failure stops the campaign via its persistent ledger.
    """
    if condition not in {"Full", "No-A2A"} or len(views) != 2:
        raise SafetyError("episode_configuration")
    from .fair_final_v2_guard import FixtureDriver
    from .fair_final_v2_live import LiveDriver
    from .fair_final_v2_task import TaskDriver, TaskFixtureDriver
    if type(driver) not in (FixtureDriver, LiveDriver, TaskDriver, TaskFixtureDriver):
        raise SafetyError("independent_v2_driver_required")
    if type(driver) is LiveDriver and driver.approval["scope"] != "T3-R-v2 full task campaign":
        raise SafetyError("six_slot_real_tasks_not_authorized_by_probe_approval")
    if (episode_id not in driver.ledger.plan or
            driver.ledger.plan[episode_id]["condition"] != condition):
        raise SafetyError("condition_plan_binding")
    if [v.name for v in views] != ["Alice", "Bob"] or views[0].question != views[1].question:
        raise SafetyError("view_pair")
    agents = [Agent(v) for v in views]
    result = dict(version=VERSION, id=episode_id, condition=condition, started=False,
                  completed=False, slots=[dict(turn=t, speaker=SCHEDULE[t][0],
                  stage=SCHEDULE[t][1], status="not_dispatched") for t in range(6)],
                  finals={}, messages=[], error=None)
    driver.begin(episode_id)
    result["started"] = True
    try:
        for turn, slot in enumerate(result["slots"]):
            if driver.transport.expired():
                raise SafetyError("wire_deadline")
            speaker, listener = agents[turn % 2], agents[1 - turn % 2]
            slot["status"] = "preparing"
            request = speaker.request(turn)
            slot["request"] = request
            slot["request_sha256"] = sha(canonical(request))
            raw, audit = driver.generate(request, episode_id, turn)
            slot.update(raw=raw, client_audit=audit, status="returned")
            parsed = parse_output(raw, speaker.view.name, slot["stage"], speaker._received)
            slot["parsed"] = parsed
            speaker.remember(raw)
            if turn < 4 and parsed["valid_format"]:
                body = parsed["text"].encode("utf-8")
                ready = driver.transport.application_cpu("v2_payload_ready")
                if not ready:
                    raise SafetyError("wire_deadline")
                delivery = driver.transport.transfer(turn, turn % 2, body, condition == "Full")
                source = dict(turn=turn, sender=speaker.view.name,
                              request_sha256=slot["request_sha256"],
                              response_sha256=audit["response_sha256"], payload_sha256=sha(parsed["text"]))
                delivery["source"] = source
                delivery["reason"] = "offered" if condition == "Full" else "blocked_by_condition"
                result["messages"].append(delivery)
                ready = driver.transport.application_cpu("v2_receive_ready")
                if ready and delivery["delivered"]:
                    if delivery["body"] != body:
                        raise SafetyError("wire_payload_mismatch")
                    listener.receive(turn, speaker.view.name, parsed["text"], source)
            elif turn >= 4:
                result["finals"][speaker.view.name] = parsed
        driver.end(episode_id)
        result["completed"] = True
    except (ClientFailure, SafetyError, UnicodeError, TimeoutError, OSError) as exc:
        if isinstance(exc,(TimeoutError,OSError)) and type(driver) not in (TaskDriver,TaskFixtureDriver):raise
        result["error"] = getattr(exc, "reason", str(exc))
        active = next((s for s in result["slots"] if s["status"] == "preparing"), None)
        if active:
            active["status"] = "failed"
        if type(driver) in (TaskDriver,TaskFixtureDriver):
            try:driver.abort(episode_id,result['error'])
            except (ClientFailure,SafetyError,OSError) as cleanup_error:
                result['cleanup_error']=str(cleanup_error)
        else:driver.abort(episode_id, result["error"])
    result["memory"] = [json.loads(canonical(a._history)) for a in agents]
    result["received_sources"] = [dict(a._received) for a in agents]
    result["wire_totals"] = driver.transport.totals()
    requests = [v for v in driver.ledger.state["requests"].values() if v["episode"] == episode_id]
    result["accounting"] = dict(reserved_requests=len(requests),
        reserved_input=sum(r["input"] for r in requests), reserved_output=sum(r["output"] for r in requests),
        unknown_usage=sum(r.get("observed_usage") is None for r in requests),
        observed_input=sum((r.get("observed_usage") or {}).get("prompt_tokens", 0) for r in requests),
        observed_output=sum((r.get("observed_usage") or {}).get("completion_tokens", 0) for r in requests),
        http={k: v - driver.epoch_http[k] for k, v in driver.ledger.state["http"].items()},
        scope=getattr(driver,'accounting_scope',"synthetic backend and fixture-counter units; no real inference"))
    driver.packets.result(result)
    return result
