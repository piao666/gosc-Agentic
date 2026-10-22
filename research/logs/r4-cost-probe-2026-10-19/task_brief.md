# Research Task Brief - R4 bounded cost probes

- Authorization: user requested execution of the four remaining scene cost probes, then full multi-seed budget estimation. Full A1, training and LLM are outside this task.
- [CODE] Baseline HEAD876fc523b113b3b65e19f0b730f1573ccc2ee17f; original validate_headline.SETTINGS and results/rev_validation.json frozen points, previously paper-audited. Existing dirty files are prior authorized research/sync work; preserved. No algorithm/result/cache/PDF changes.
- Question: what are wall/CPU/RSS/output costs for K10, clustered, W50, SNR-5; can all six scene costs support a concrete 1200-job A1 budget?
- Preregistration: research/protocols/r4_cost_probe_v1.json. Four settings x two frozen arms x three seeds9010-9012 = 24 missions. Seeds are management only, never used for selection/training. Original A0/full plan remains unchanged.
- Resource check: HPC uid8301880, n1 project .venv Python3.11.15; cpuset0-1, quota200000/100000, RAM25769803776 bytes. No running jobs or registered new seeds. Two workers, one numeric thread per worker; per-job120s, batch600s; no GPU/model/API/dependency installs.
- Expected cost [HYPOTHESIS]: 24 workers at previous pilot mean0.61s plus K10/long-horizon variance, likely under2min; hard batch cap10min; outputs below10MiB, default100MiB pull cap. Partial/failure records retained with fail-fast; no silent retries.
- Implementation: new bounded orchestration scripts/r4_cost_probe.py, reusing unchanged verified run_jobs/worker; tests_ext/test_r4_cost_probe.py. Tests and independent read-only result audit run on HPC through hpc_runs.
- Acceptance: new scope tests plus executor regressions pass;24 terminal records,12 paired initial worlds, exact frozen Config,<=2 concurrent, full raw curves/trajectories/logs retained; all protected input hashes stable; budget weights12 groups equally at100 jobs each despite unequal sample sizes; runtime outputs and receipts verified both sides.
- Counterexamples/limits: N3 cost variance and shared-host contention can defeat linear projection; RSS is per worker, not container peak. Partial rescue/search outcomes are normal scientific records and not discarded. Do not infer performance superiority from probes.
- Evidence: run manifests/status/source snapshot/episodes/events/worker logs, cost summary, budget, audit, final receipt.
