# Receiver-information headroom pilot v1 — frozen design, 2026-10-22

[HYPOTHESIS] This is a user-authorized exploratory diagnostic following P1 acceptance, not exact author reproduction, a learned estimator, or proof of novel contribution. Author calibration/cache gaps remain. No new LLM inference or training. At most30 minutes HPC CPU, workers2/numeric threads1.

## Question and scope
In original search W100/W50 with Planner agents, does receiver private belief or current pose improve over a strong, independently calibrated simple value/periodic family? Separate private/pose/both using the original TeamModel with explicit projections. Free true state is privileged; it is neither deployable nor a mathematical upper bound. Base ideal downlink/outage transport only; no rescue/LLM generalization claim.

## Arms and calibration
Seven families: public ToM, bits, AoI, complete38 periodic configurations, private-only ToM, pose-only ToM, both-state ToM. Keep original GOSC candidate generator, encoder, filter, scheduler and channel for value-rule arms. Periodic is a separately labelled external simple-policy family. Only receiver information available to the original TeamModel is projected; no ground-truth world/future reward is an online feature.

ToM price grid1e-6/3e-6/1e-5/3e-5/1e-4/3e-4; bits0/.003/.01/.03/.1/.3/1/3; AoI0/.0003/.001/.003/.01/.03/.1/.3. Periodic uses public native38 grid. Calibration8 worlds at seeds12000000–12000007, validation20 worlds13000000–13000019. Reserved training11000000–11000099 not used; guard14000000–14000002. Before outcomes, scan all registered input catalogs conservatively for collisions and compare standardized world fingerprints. Collisions stop preparation; no quiet reseeding.

Within family select minimum mean completion time among candidates with meanUL<=10000 (tie meanUL, then catalog id); choose strongest simple family M0star from bits/AoI/periodic on calibration only. Freeze file before validation. If none eligible, mark not comparable; do not adapt grid based on held-out outcomes. This is a calibration mean-budget constraint, not a per-mission hard cap or guaranteed equal resource use.

## Randomness and information checks
Original world initialization retained. Potential sensor noise keyed(seed,201,time,agent,globalcell), block fading(seed,202,time,agent), planner jitter(seed,203,time,agent,cell). Outcomes depend on actions; common exogenous fields remain coupled at overlapping physical events despite different trajectories. Group whole worlds by split; same world across two W settings is not independent replication.

Five HPC checks must pass: denied fields never read; projected-public equals original-public values; projected-both equals original oracle; overlapping sensor cells share noise; identical policy repeat has identical outcomes/event prefix. No modified core source. Endpoint acquisition is not measured by random-seed equality alone.

## Statistics and decision rule
20,000 paired bootstrap resamples, fixed statistics seed15999999. Six primary comparisons(3 oracle masks x2 W), two endpoints(task gain and total logical UL+DL ratio), Bonferroni12 with family alpha.05. Positive task gain=M0starT−oracleT; keep unfinished at originalmax_steps400. Pilot signal requires mean gain>=3slots and corrected lowerCI>0, plus corrected upper total-resource ratio<=1.05. Missing comparability, unmeasured actual state transport or CI crossing0 means not established. No equivalence claim from null significance. No automatic complex-training Go even if a signal occurs.

## Future deployable-feature contract (not implemented in this pilot)
Available baseline features: message kind/size/age, delivered common belief/intent/position and timestamps, observed link/queue metadata. Existing intent/pose is not new information. A proposed paid summary may contain target cell10bits, uncertainty bucket3bits, state-version8bits, slot modulo8bits, valid1bit, padded2bits =32payload bits. Target duplication must be removed/ablated; genuinely incremental uncertainty/version require receiver computation. Prospective summary frame adds16header bits, actual PHY/rate/delivery, ACK1bit/DL, retransmissions, loss/age and waiting costs; compute/tokens and serialization are logged separately. Missing/stale summary uses declared mask, never current private state. Refresh rules/sample grids and learned models require a later frozen implementation protocol; free oracle does not validate these net costs.

Counterfactual labels, if later used, clone pre-decision state and index exogenous events across branch siblings, keep all siblings in same world split. No future truth/test labels/judge accessible online. Equal-capacity no-summary/with-summary/shuffle/age controls required before contribution claims. Existing thirteen notes plus nearest-neighbor review constrain novelty.

## Limits and stop rules
No test-informed hyperparameter or regime changes, seed deletion, paid services, new model download, live inference, full new-method campaign or training. If isolated checks fail, fix diagnostic implementation and retain failed run before data collection. If no evidence of headroom, report negative/uncertain result and do not add complexity to rescue it. Literature and reproducibility documentation can continue.
