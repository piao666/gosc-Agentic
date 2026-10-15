# Reproduction evidence index

## Approved R4-S1 statistical reproduction

Raw root: `.local/reproduction/2026-10-15-statistical-v1/`.
Compact directory: `research/reproduction/2026-10-15-statistical/`.

| Claim / limitation | Evidence |
|---|---|
| 5200 fresh, zero reused; 1455.827s, four workers | `execution_manifest.json`, raw `execution.log` |
| 100/104 equivalent, four inconclusive, no incompatible endpoints | `gate.json`, `agreement.csv/json` |
| 200 exact-discrepancy records, 800 scalar differences | `discrepancy_groups.csv`, raw `exact_discrepancies.csv` |
| Private600 and headline1200 saved fields match | raw per-record `reference_differences`; `report.md` states saved-field boundary |
| Three joint-oracle task CIs cross zero; no stable benefit established | `supplemental_contrasts.json:private` |
| All seeds retained, illustrative large positive/negative tails | raw `raw.jsonl`, compact `tail_examples.csv` |
| No extrapolation; invalid frontier resamples counted | `frontier_statistics.json` |
| Full99 tests + final statistics7 + gate2 (separate invocations) | raw `preflight.json` and linked logs |
| New receiver factorization not run; scoped proposal unapproved | `experiment_manifest.json`, `receiver_scope_proposal.md` |

This is a disclosed amendment after prior data exposure, not a blind preregistration.
Original strict R4 remains failed; R4-S1 remains inconclusive. Historical calibration,
live/cached LLM reproduction and new estimator contributions are not claimed.

## Approved mismatch follow-up

[RUN] Raw root: `.local/reproduction/2026-10-15-mismatch-v2/` (local only).
Compact evidence: [diagnosis report](2026-10-15-mismatch/diagnosis_report.md).

| Claim / boundary | Evidence |
|---|---|
| 14 seed-0 probes; none matches the saved reference | `2026-10-15-mismatch/compatibility_matrix.csv`, `experiment_manifest.json` |
| One-ULP value-only replay changes selected message | `2026-10-15-mismatch/first_scheduler_divergence.json`, `selection_audit.json` |
| Dual stage selects empty; greedy group order changes | `selection_audit.json:dual_and_greedy_left/right` |
| 80-combination offline objective audit, not task quality | `selection_audit.json:exact_small_state_left/right` |
| All mission argv, failed image probe and pip invocation retained | `2026-10-15-mismatch/command_ledger.json` |
| Existing tests: 93 passed in 45.32s | raw root `tests.log` |
| Original 76 inputs unchanged, Linux 14 source hashes match | raw root `protected-and-linux-source-check.json` |
| Historical 83-slot provenance unresolved; R4/receiver not resumed | `2026-10-15-mismatch/experiment_manifest.json`, `diagnosis_report.md` |

These observations establish local numerical sensitivity. They do not identify the
author's original generation environment, validate a new estimator or establish a
representative receiver-model defect.

Run root (local, not uploaded):
`E:\gosc-agentic-teams\.local\reproduction\2026-10-15-baseline-v1`.
Original baseline: `387b49389385b51c275dc5a22ec1672087edda1d`.
Working base: `876fc523b113b3b65e19f0b730f1573ccc2ee17f`.

| Evidence | Anchor | Meaning / boundary |
|---|---|---|
| [RUN] Original tests | `../logs/environment-2026-10-12/pytest.log` | 85 passed in the validated environment; not full paper reproduction |
| [RUN] Current dependency check | run root `runtime_manifest.json` | Actual package versions match the pinned environment |
| [RUN] R2 execution | run root `r2_manifest.json`, `r2_logs/` | Four original analysis commands, executed in the isolated archive |
| [RUN] R2 numeric checks | run root `r2_numeric_audit_v2.json`, `r2_audit.json` | 83 generated rows match displayed PDF numeric sequences, Tables IV–XIII |
| [RUN] R2 first audit | run root `r2_numeric_audit.json` | Retained audit-parser issue: TeX multirow count initially treated as data; corrected in v2 |
| [RUN] Visual review | run root `visual_review/all_figures.png` and original page renders | 17 generated PDFs; main Figures 2–5 compared to original pages |
| [RUN] R3 | run root `r3_output.json`, `r3_manifest.json` | Fresh seed 0: 122 slots, 13304 UL uses, 17186 payload bits; full curve retained |
| [RUN] Diagnostic contracts | run root `diagnostic_contract_tests.json`, `contract-tests.log` | Both code paths and original shared/joint endpoints, six tests passed |
| [RUN] Extended statistics checks | run root `extended-tests.log` | Eight tests including seed ordering and paired common-effect cancellation passed |
| [RUN] Final combined tests | run root `final-tests.log` | 93 passed in 61.35 seconds; saved-benchmark consistency is a separate check |
| [RUN] R4 first discrepancy | run root `r4/failure.json`, `r4/raw.jsonl` | 1399 retained records; 1398 match, first throughput record differs; R4 blocked |
| [RUN] Independent probes | run root `mismatch-probes/` | Direct original archive and existing environments reproduce the local discrepancy; root cause unresolved |
| [RUN] Scheduling trace | run root `mismatch-trace/scheduling.jsonl` | 456 non-intervening original decisions; trace reproduces the local outcome |
| [CODE] Theory-of-mind inputs | `gosc/voi.py`, TeamModel.__init__, _belief_mass, _expected_utility | Default shared knowledge versus privileged private evidence and position; softmax surrogate |
| [CODE] Actual Planner | `gosc/agent.py`, Agent.plan | Argmax with target hysteresis; not identical to TeamModel's softmax distribution |
| [CODE] Existing oracle campaign | `experiments/run_revision.py`, experiments()['private'] | Three original settings, two modes; both receiver evidence and position change together |
| [CODE] Split intervention | `extensions/receiver_oracle.py` | Process-local diagnostic view only, both parallel paths restored; no deployed estimator |
| [HYPOTHESIS] Model-error relevance | protocol's independent factorial design | A model mismatch must affect task outcomes and withstand resource accounting; no defect presumed |

## Paper mapping

Source PDF: local D01, `Resource-Efficient Semantic Communication for Heterogeneous
Agentic Teams`, arXiv:2609.39477v1; the original PDF SHA-256 is recorded in the numeric
audit. Source PDF remains in Obsidian and is never uploaded by this workflow.

| Paper item [PAPER] | Upstream generation [CODE] | Generated isolated artifact [RUN] |
|---|---|---|
| Figure 2, p.7 | plot_revision.rescue | figures/fig_rescue.pdf |
| Figure 3, p.9 | plot_realistic.noise | figures/fig_noise.pdf |
| Figure 4, p.9 | plot.sweep_pair_plot | figures/fig_snr_pair.pdf |
| Figure 5, p.11 | plot_realistic.shared_column | figures/fig_shared_col.pdf |
| Table IV, p.8 | plot_revision.validation_table | figures/table_validation.tex |
| Table V, p.8 | plot.default_table | figures/table_default.tex |
| Table VI, p.8 | plot_revision + run_belief_divergence --table | figures/table_values.tex |
| Table VII, p.9 | plot_realistic.noise | figures/table_noise.tex |
| Table VIII, p.10 | plot_revision.ablation | figures/table_ablation.tex |
| Table IX, p.10 | plot_realistic.overhead | figures/table_overhead.tex |
| Table X, p.10 | plot_realistic.overhead | figures/table_cost.tex |
| Table XI, p.12 | plot_realistic.shared | figures/table_shared.tex |
| Table XII, p.12 | plot_realistic.llm | figures/table_llm_extended.tex; author-stored values only |
| Table XIII, p.12 | plot_revision.validation_table | figures/table_frozen.tex |

## Interpretation safeguards

- R2 regenerates statistics from saved results. It does not simulate the world or call an LLM.
- Original Figures 1 and Tables I–III are conceptual/configuration items, not outputs of the plot scripts.
- Regenerating the same published numbers does not validate every methodological interpretation.
- The inherited counterfactual target-change proxy, tied-rank calculation, incomplete historical
  noise groups, and shared-radio cost-selection boundary remain documented limitations.
- The baseline's calibration-seed selection history has not been reconstructed.
- Fixed-price shared/oracle comparisons are not cost-matched. Oracle information is privileged,
  and a null result is not an equivalence proof.
- R4 did not pass and has a failure record instead of a completed success manifest. The
  independent receiver campaign was not run. An in-progress log, prepared adapter or
  planned command is never evidence of stage completion.
