# Baseline reproduction and receiver-assumption diagnostic protocol

Protocol date: 2026-10-15. Evidence tags: PAPER=original PDF, CODE=specific baseline
source, RUN=actual local output, HYPOTHESIS=unverified interpretation.

## Frozen baseline and environment

Original code commit: `387b49389385b51c275dc5a22ec1672087edda1d`.
Working base: `876fc523b113b3b65e19f0b730f1573ccc2ee17f`.
Use the existing CPython 3.12.10 environment and `requirements-windows.lock.txt`.
Set UTF-8, Agg, and one numerical-library thread per worker. Do not alter dependencies
to force a match. Preserve original files; use a new isolated Git archive for each run.
Completed manifests are write-once. Full configurations, seeds, raw curves, timing,
exceptions and output hashes are retained per mission.

## R2: saved-result analysis reproduction

Run original analysis scripts unchanged in the archived workspace. Original summaries
inside this disposable archive may be regenerated; the user's checkout is protected.
Decompress only archive copies using exclusive-create output files. Invoke, in order,
`experiments.plot`, `experiments.plot_revision`,
`experiments.run_belief_divergence --table`, and `experiments.plot_realistic`.
Check for skipped analysis branches, missing figures/tables and incomplete sample groups.
Main paper targets: computational Figures 2–5 and Tables IV–XIII. Figure 1 and Tables
I–III require conceptual/configuration mapping, not a false claim of generated results.
LLM tables here analyze author-saved values; they are neither cache replay nor live LLM
evaluation. Preserve original statistical definitions before independent sensitivity checks.

## R3: fresh single mission

Default Config, scheme gosc, seed 0, empty llm_agents. Save the entire output including
curve. Compare exact integer fields and floating quantities with absolute tolerance
1e-9 to the matching saved author record. This is a new simulation, unlike R2.

## R4: bounded paired campaigns

1. Original default W100 frontier: all 34 configured operating points, seeds 0–99.
2. Six original frozen headline settings, GOSC and periodic, seeds 3000–3099; recover
   configurations through the author's frozen selection function and check its selected
   labels against stored validation labels before running. Do not retune.
3. Original private-information comparison: default/W50/SNR -5, shared versus joint
   oracle, seeds 0–99. Fixed original price does not mean matched realized cost.

Full original seed arrays and original per-mission records are compared to fresh records.
The matched-budget value comparison retains the original lower-envelope interpolation,
10000 bootstrap resamples and original multiple-comparison correction. It must be
described as frontier interpolation, not an equal-cost intervention on every mission.
Search primary endpoint is capped completion_time with completion rate; rescue primary
endpoint is saved_fraction. Report UL payload bits, UL data channel uses, recorded DL
channel uses and their boundaries. Do not fabricate absent tokens, real serialized bytes,
compute breakdowns or packet-success measurements.

## Receiver assumption experiment: privileged analysis only

Freeze independent seeds 4000–4099, N=100 per setting and mode, before examining outcomes.
Use the original three search settings, original eta, channel, planner and scheduler.
Modes form a 2x2 design: shared, private evidence only, true receiver position only,
and both. The diagnostic adapter changes only TeamModel's view of receiver evidence/
position; no core source is changed. Endpoint equivalence to original shared and
tom_oracle is tested before this campaign.

These are privileged-state interventions with uncharged access; they are neither a
deployable estimator nor a task-optimal oracle. Future deployable methods must pay
state synchronization costs. Lower model error does not guarantee lower task cost.

Primary comparisons: each single-factor mode versus shared, across three settings
(six comparisons); paired bootstrap 4000 resamples, 95% unadjusted and Bonferroni family
intervals. Report joint-oracle contrasts and factorial interaction as secondary. Keep
per-seed data, quartiles, completion failures and resource deltas. Practical-effect
threshold: at least 5% of shared mean completion time; statistical and practical
thresholds are both reported, without claiming equivalence when an interval crosses zero.
No tuning, outcome-based seed selection, new tasks, or learner training is permitted.
If this gives no consistent benefit, report the limitation of this research direction.
Further matched-cost diagnostic campaigns require a separate frozen protocol; a fixed
eta comparison alone cannot establish an equal-cost performance defect.

## Stage boundaries

R2 must be assessed before R3; R3 before R4; baseline R4 before new oracle interventions.
R1 evidence already exists for the unchanged source. Missing historical calibration
records remain a provenance gap; rerunning evaluation does not reconstruct calibration.
Real LLM/cached replay (R5), complete paper-wide resimulation (R6), and estimator
development are outside this execution. No model/server downloads, paid APIs or private
PDF uploads. Record every failure and numerical disagreement without rewriting originals.
