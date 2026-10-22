# R4-A0 executor issues and recovery

- First executor test suite passed8 checks, but first scientific-run entry failed before expanding the plan: absolute script invocation had scripts/ on sys.path and could not import gosc. No jobs/mission_status/events/episodes or worker temporary directory were created; no scientific mission started.
- Corrected the controller's source import path and added an integration test invoking the absolute CLI from an unrelated cwd with PYTHONPATH removed. This catches the difference from pytest import behavior.
- Preserve hpc-r4-a0-pilot-20261019 as failed. A new attempt may explicitly reference it only after verifying matching plan/config/seed/HEAD, failed status, original import exception, and no work-start artifacts. This is not a partial-run resume or new seed selection.
