# Research Task Report — 2026-10-15

**Approved statistical follow-up:** 5200 new Planner missions completed. R4-S1 gives
100 equivalent and 4 inconclusive endpoints out of 104; overall still Pending.
Original private600 and frozen headline1200 saved fields are reproduced. The new
receiver factorial was not run. See [the statistical report](2026-10-15-statistical/report.md)
and [the unapproved scoped diagnostic proposal](2026-10-15-statistical/receiver_scope_proposal.md).
Neither the original strict failure nor the new statistical gate is rewritten as passed.

**Follow-up diagnosis:** [RUN] A same-input one-ULP counterfactual now demonstrates
numerically sensitive message selection. The author's 83-slot trajectory is still
unmatched. R4 remains blocked; receiver diagnostics were not run. See the
[diagnosis report](2026-10-15-mismatch/diagnosis_report.md) and its 14-run matrix.
The original report and v1 failure evidence below remain preserved.

- **Research Question / Hypothesis**: [HYPOTHESIS] Can the original GOSC numbers and missions be reproduced before assessing whether TeamModel receiver assumptions cause a stable task-performance loss?
- **已核验前人工作**: [PAPER] D01, arXiv:2609.39477v1, computational Figures 2–5 and Tables IV–XIII. [RUN] Saved-data regeneration matches 83 displayed numeric rows. This does not establish the validity of all inherited scientific interpretations.
- **实际阅读源码**: [CODE] Baseline `387b49389385b51c275dc5a22ec1672087edda1d`; original plot modules, run_revision, validate_headline, run_belief_divergence, Config, Simulation, GOSC.build_groups/lagrangian_select and TeamModel. The source of the five central files is identical across the available upstream initial/current release history.
- **本轮新增或修改**: Added independent orchestration in `experiments_ext/`, a privileged-state diagnostic adapter in `extensions/`, contract/statistics tests in `tests_ext/`, a frozen protocol, evidence index and this report. No changes to upstream algorithms, original experiment modules/tests/results, LICENSE or Obsidian. Work is on `codex/baseline-reproduction`.
- **实际运行**: [RUN] Four upstream reanalysis commands in an isolated Git archive; default fresh seed 0; a bounded R4 campaign halted at its first discrepancy; small independent environment/numerical probes; a non-intervening scheduling trace; combined original and extension tests. Exact commands, logs, configurations, hashes and raw curves are retained under `.local/reproduction/2026-10-15-baseline-v1/`.
- **测试与结果**: [RUN] Combined suite: **93 passed in 61.35 s** (85 original + 8 extension cases). R2 generated 17 PDFs and 18 TeX files, numeric/visual checks passed within stated scope. R3 reproduced 122 slots, 13304 UL channel uses and 17186 payload bits. R4 retained 1399 records: 1398 match original per-seed records within 1e-9; the first throughput case differs materially. R4 did not pass. New independent-seed receiver diagnostics were not run.
- **失败/负面证据**: [RUN] `gosc_bits`, W100, eta=0, seed 0: author-saved T=83 versus fresh T=76; symbols 31011 versus 29596; payload bits 23468 versus 22109. Failure is retained and not normalized away. Direct execution in the untouched upstream Git archive also gives the local result. The original tests do not cover this saved-frontier consistency condition.
- **与原 GOSC 的差异**: No deployed method changes. The adapter splits receiver private information and true position only for explicitly privileged analysis; it has been contract-tested but its planned 4000–4099 campaign is not executed. Numerical-backend probes are sensitivity interventions, not baseline reproductions.
- **公平性与泄露检查**: No model calls, learning, parameter fitting, calibration changes, favorable-seed selection or original-result rewriting. Oracle access is unpriced and cannot establish a deployable or equal-cost gain. The original fixed-price oracle comparisons are not equal-realized-cost comparisons. No claims of complete calibration, LLM or paper-wide simulation reproduction are made.
- **成本**: [RUN] R2 commands total about 295.75 s; R3 fresh episode about 3.42 s. The failed R4 interval is approximately 396.6 s from stage file timestamps (an estimate, not a measured CPU time). Up to four CPU workers, one numerical-library thread per worker; no GPU/paid API/model download. CPU/RAM peaks and assistant token costs were not measured. Some in-flight tasks were terminated and are not counted as verified records.
- **可否进入下一阶段**: **No-Go for new receiver experiments; R4 blocked.** R2 and R3 passed their defined gates. The replication discrepancy has no established root cause and cannot be attributed to TeamModel: throughput mode does not instantiate TeamModel.
- **用户需要批准的下一步**: Resolve the minimal throughput reproduction discrepancy using the author's generation-time environment/source provenance or a separately scoped compatibility investigation. Do not silently replace saved results, change the algorithm to match them, or continue as if R4 passed. An upstream question is drafted locally; no message or issue has been sent.

## Checkpoint scope

| Checkpoint | Actual outcome | Boundary |
|---|---|---|
| R1 | 85 original + 8 new tests passed | Tests alone do not prove saved benchmark reproducibility |
| R2 | 17 PDF figures, 18 TeX files; 83 table rows match PDF display precision | Saved-data analysis; LLM tables use existing values only |
| R3 | Default GOSC, seed 0 matches saved reference; full curve saved | One fresh episode, not a full campaign |
| R4 | Halted at first mismatch; 1399/5200 records retained | 700 ToM and 698 belief-divergence records match; one throughput record differs; remaining records unverified |
| Original shared/oracle reruns | Not reached | Their saved-data table was regenerated in R2, but that is not fresh simulation |
| Split receiver diagnostic | Not run | Independent seeds/protocol frozen; only adapter contract tests executed |

## R2 audit details

Four unchanged original entry points were executed in this order in an isolated archive:

1. `python -m experiments.plot`
2. `python -m experiments.plot_revision`
3. `python -m experiments.run_belief_divergence --table`
4. `python -m experiments.plot_realistic`

Copies of the three gzip inputs were exclusively decompressed in the archive. No missing
or skipped analysis branches remained. Tables IV–XIII were checked against local PDF
pages 8–10 and 12, with scenario labels reviewed separately. Table XI's B150
"target not reached" is preserved. Figure 1 and Tables I–III are conceptual/configuration
items and were not claimed as generated outputs. No pixel-identical PDF claim is made.

The first numeric audit mistakenly interpreted TeX `multirow{2}` layout metadata as
observations in four LLM rows. That attempt is retained; corrected parsing matches all
83 rows. The first attempt is an auditor issue, not a changed paper/result value.

Inherited limitations remain: target-change proxy versus actual action count, tied-rank
handling, partial historical noise groups, shared-radio operating-point cost boundary,
and missing generation-time calibration records. Numeric agreement does not remove them.

## R4 failure and bounded diagnosis

The R4 plan is unchanged: 3400 W100-frontier executions, 600 original shared/oracle
executions, and 1200 frozen headline executions. The workflow stopped before the latter
two components were reached. `r4/failure.json` and `r4/raw.jsonl` are preserved. Of the
3801 unretained planned records, some could have been in flight at termination; no
claim is made that every unretained record was never started.

The local direct result and the saved author record differ as follows:

| Field | Saved author | Fresh original API |
|---|---:|---:|
| completion_time | 83 | 76 |
| symbols | 31011 | 29596 |
| bits | 23468 | 22109 |
| delivered_bits | 12426 | 11849 |
| dl_symbols | 6253 | 5965 |
| confirm_latency | 0.125 | 0.0 |

Checks performed without editing core source:

- Repeated serial executions reproduce the local result.
- Existing NumPy 2.5.3 and 2.3.5 environments give the same local result.
- The bundled existing Python runtime also gives the local result (details in its probe JSON).
- Disabling AVX2/FMA3/AVX512F and replacing only the success-probability exponential
  with `math.exp` do not restore the saved result. These limited checks do not rule out
  all possible numerical/platform causes.
- At eta=0.3, the same completion time is reproduced but payload bits and channel uses
  still differ. This is not merely a comparison of rounded means.
- Direct API execution inside the untouched original Git archive excludes the new
  campaign wrapper as the cause of this observed discrepancy.
- Current upstream HEAD was read-only checked and is still `387b493...`; no available
  newer upstream snapshot resolves it. No remote source was modified.
- A non-intervening trace retained 456 scheduling decisions including options, chosen
  rates, channel state and exact float representations; the instrumented run reproduces
  the same local outcome. This is ready for comparison with generation-time provenance.

[HYPOTHESIS] A generation-time source/configuration difference or an untested numerical
environment may explain the mismatch. Neither is established. It would be scientifically
incorrect to label this a stable TeamModel performance defect or to relax the comparison
tolerance by seven slots.

## Minimal PowerShell reproducer

```powershell
@'
from gosc import Config, run_episode
o = run_episode(Config().with_(energy_price=0.0), 'gosc_bits', 0)
print({k: o[k] for k in ('completion_time', 'symbols', 'bits')})
'@ | .\.venv\Scripts\python.exe -B -X utf8 -
```

Recorded local output: `{'completion_time': 76, 'symbols': 29596, 'bits': 22109}`.
Saved reference: `results/rev_frontier.json`, scheme `gosc_bits`, param `W100/eta0.0`, seed 0.
This reproducer does not write to the original results directory.

## Evidence locations

- `research/reproduction/2026-10-15/`: compact checkpoint, mismatch and retained-group tables.
- `.local/reproduction/2026-10-15-baseline-v1/`: complete isolated outputs, logs,
  original failure, probes, scheduling trace, configurations and hashes.
- `research/reproduction/evidence_index.md`: paper-code-output mapping and interpretation boundaries.
- `research/reproduction/repro_protocol.md`: frozen protocol; no outcome-driven changes.
- `research/reproduction/upstream_reproduction_question_draft.md`: unsent provenance question.
