# Receiver-CF v1 evidence index / rebuild

## Evidence and provenance

|Claim/material|Evidence|Scope|
|---|---|---|
|Approval and bounded split|approval.json; execution_protocol.md; preceding mechanism/counterfactual_protocol_v1.md SHA|8 development missions; <=128 continuations; no new policy|
|Actual runtime|experiment_manifest.json; configs.json; execution_completion.json; pilot-execution.log|commit48404fd5e68c2f7671845ed10ccd2868423edfbe;112 branches|
|Executed tests|implementation_gate.json; full-tests.log|126 passed57.39s, including13 new contracts; pre-execution source snapshot|
|Native hook/clone/current tape|extensions/counterfactual.py:19–60,135–210|no scheduling/ACK/fusion replacement; native decode always consumes draw|
|Observed timing / diagnostic context|extensions/counterfactual.py:76–132|planner_context reconstructs score formula from original MIT Agent.plan; shadow is separate from actual next decision|
|Outcome-blind sampling / features / streams|extensions/counterfactual.py:213–261|stable packet ID hash; sender/shared whitelist; five future streams|
|Bounded execution and raw recording|experiments_ext/run_receiver_cf.py:88–193,195–274|per-seed JSONL/snapshot;2workers;900s cap;exceptions retained|
|Paired labels and cluster inference|experiments_ext/analyze_receiver_cf.py:20–117|mean by point then mission;bootstrap multiplicity;average ties;4000seed0|
|Integrity and actual budgets|preanalysis_audit.json; raw_artifact_index.json|76 original inputs,23 prior receiver artifacts and prior raw unchanged;16 checkpoints match|
|All14 point outcomes and costs|per_point.csv|all positive/zero/negative points;R4 per point, not independent112missions|
|Means/CI/rank undefined counts|statistics.json|exploratory mission-cluster inference;not confirmatory/policy comparison|
|Independent numeric check|independent_numeric_review.json|14raw labels/MC SE rebuilt; independent scalar bootstrap matches all3mean CIs|
|Postrun precision/behavior check|outcome_review.json; experiments_ext/review_receiver_cf.py|descriptive, not additional preregistered inference; recomputed identical|
|All-point figure|point_effects.png/.svg; figure_manifest.json; experiments_ext/plot_receiver_cf.py|all14;bars1MC SE, not populationCI;PNG visually checked|
|Original GOSC/adjacent prior art|../2026-10-16-mechanism/prior_art.md and code_map.csv|local directed PDF review from prior stage, no fresh external verification|

All root-relative source paths above resolve under `E:\gosc-agentic-teams`. Raw states/outcomes remain at `E:\gosc-agentic-teams\.local\reproduction\2026-10-16-cf-pilot-v1`; hashes and sizes are indexed. Pickles are trusted local self-generated checkpoints, never accept unknown files. No PDF/private contents or raw checkpoints were uploaded; Git has only local commits.

## Rebuild saved-data analysis (no new simulations)

Completed output directories are immutable/exclusive. Copy the local raw run to a **new analysis workspace with no analysis subdirectory**, preserving manifest/config/seed-* raw files and hashes. Then invoke the unchanged analysis:

```powershell
.\.venv\Scripts\python.exe -m experiments_ext.analyze_receiver_cf --run-dir <new-raw-copy>
.\.venv\Scripts\python.exe -m experiments_ext.plot_receiver_cf --run-dir <new-raw-copy>
.\.venv\Scripts\python.exe -m experiments_ext.review_receiver_cf --run-dir <new-raw-copy>
```

These are rebuild instructions, not extra executions claimed here. Original raw branches are required for reanalysis; index hashes alone are not data. For the current run the first postrun review was an inline Python check; the permanent review script recomputed into `outcome_review_recomputed.json` and matched exactly. Plot/review helpers were added after the frozen run and are listed separately from the126-test gate.

To reproduce full simulations later, use frozen implementation commit, matching lock/protocol/approval/source hashes, and a new output directory. A repeat would be a **new experiment** with a separate budget; no repeat was performed in this task. Current clone state/tape and full future trajectories/RNG keys suffice for auditing. The proposed R32 precision extension is explicitly unapproved and unexecuted.
