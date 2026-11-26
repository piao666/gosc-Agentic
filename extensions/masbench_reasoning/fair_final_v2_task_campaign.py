"""Task-only campaign orchestration; gold/scoring are offline dependencies."""
import json
from dataclasses import asdict
from pathlib import Path
from .execution_safety import SafetyError,canonical,digest
from .fair_final_v2 import Agent
from .fair_final_v2_runtime import run_episode
from .fair_final_v2_task import validate_plan,TaskDriver,TaskFixtureDriver


def run_campaign(plan,views,driver_factory,artifact):
    validate_plan(plan)
    if set(views)!={r['family'] for r in plan}:raise SafetyError('only_four_predeclared_view_pairs')
    for row in plan:
        if digest([asdict(v) for v in views[row['family']]])!=row['private_view_sha256']:
            raise SafetyError('paired_view_binding')
    results=[]
    for row in plan:
        driver=driver_factory(row)
        if type(driver) not in (TaskDriver,TaskFixtureDriver):raise SafetyError('task_driver_only')
        try:result=run_episode(views[row['family']],driver,row['condition'],row['id'])
        except (SafetyError,OSError,TimeoutError) as exc:
            # Includes admission, serialization and post-result storage faults.
            # No new dispatch; preserve started status from the durable ledger.
            started=driver.ledger.state['episodes'][row['id']]!='unstarted'
            driver.ledger.fence(str(exc))
            if started:
                try:driver.abort(row['id'],str(exc))
                except (SafetyError,OSError):pass
            result=dict(id=row['id'],condition=row['condition'],started=started,
                        completed=False,slots=[],finals={},error=str(exc))
        results.append(result)
        try:artifact(row['id'],result)
        except OSError:
            driver.ledger.fence('episode_return_or_storage_failed')
            raise
        if result.get('error') or not result.get('completed') or driver.ledger.state['fenced']:
            break
    return results


def preflight_initial_inputs(plan,views,counter,write):
    """No generation: full input SHA/count proof on all first-role requests.

    Later requests depend on actual messages; they MUST be re-counted just
    before every dispatch. This routine never asserts their future token size.
    """
    validate_plan(plan);out=[]
    for row in plan[::2]:
        for view in views[row['family']]:
            turn=0 if view.name=='Alice' else 1
            request=Agent(view).request(turn)
            if len(canonical(request))>65536:raise SafetyError('initial_input_serialization_cap')
            proof=counter(request)
            if proof['request_sha256']!=digest(request) or type(proof['tokens']) is not int:
                raise SafetyError('initial_count_binding')
            if proof['tokens']+512>16384 or len(canonical(request))>65536:
                raise SafetyError('initial_input_does_not_fit')
            record=dict(family=row['family'],role=view.name,**proof)
            write(record);out.append(record)
    return out
