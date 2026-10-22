# Research Task Report - research/sync and Python 3.11 (2026-10-19)

- **Research Question / Hypothesis**: [HYPOTHESIS] Can every authorized HPC test/train/simulation retain truthful completion state and verifiable outputs, with local mirrors unable to overwrite remote execution history?
- **已核验前人工作**: [CODE] GOSC HEAD 876fc52 and original requirements numpy>=1.24, matplotlib>=3.7, pytest>=7; historical Windows 85/85 is not an HPC result.
- **实际阅读源码**: AGENTS, current sync helper, workspace paths, HPC environment note, prior progress report and HPC task report.
- **本轮新增或修改**: research/sync protocol/config/environment/project_status/plans/templates; scripts/hpc_runs.py; source helper --pull-runs and HPC-owned record exclusions; AGENTS, .gitignore, paths/environment notes.
- **实际运行**: [RUN] Offline uv lookup and actual Python version/package metadata on HPC. uv=0.11.19; managed CPython=3.11.15. Bare interpreter has pip 26.1.2 but lacks numpy/matplotlib/pytest; project .venv absent. No packages installed.
- **测试与结果**: [RUN] Infrastructure-only success fixture exit 0 => completed; intentional negative fixture exit 3 => failed. Both preserve logs, source manifest and one output with verified SHA-256. First pull retrieved 16 files (82703 bytes), all_outputs_mirrored=true; receipt mirrored back to HPC. Further launch-path validation is separately recorded in runs/ and receipts/. No GOSC pytest/R1, training or simulation executed.
- **失败/负面证据**: Intentional failure fixture is expected protocol validation, not an algorithm failure. Initial metadata probe had a quoting syntax error; corrected probe returned actual package absence. Login still emits unrelated .bashrc directory warning. Python availability alone does not imply dependency readiness.
- **与原 GOSC 的差异**: No changes to original gosc/experiments/tests/results/LICENSE. This is execution/synchronization administration, not an algorithm contribution.
- **公平性与泄露检查**: No research seeds, training labels, model changes or resource comparisons. Private keys/.env/private PDF files are excluded. Remote-only run records remain authoritative; no reset/clean or record deletion.
- **成本**: File transport and metadata checks plus sub-second fixture commands, no GPU/model/paid API. Runner child CPU/RSS includes metadata child processes and is not an exclusive model benchmark; GPU peak remains unmeasured/null.
- **可否进入下一阶段**: Go for HPC project environment readiness and then R1 after dependency/environment preparation. Local can concurrently complete P0 mapping/protocol and P2 reading/RQ documents. No basis to start training a new method yet.
- **用户需要批准的下一步**: No extra approval needed for requested sync infrastructure. This task plans rather than starts dependency installation, official tests, full campaigns or training.

## Completion evidence

- Interpreter: research/sync/environment/hpc_python.json.
- Real infrastructure cases: research/sync/environment/registry_validation.json and runs/infra-ledger-*.
- HPC task completion: research/sync/dashboard.json and STATUS.md.
- Local/remote output mirror completion: research/sync/receipts/*.json (separate from run status).
- Exact next execution locations/gates: research/sync/plans/next_steps.md.
- Latest code upload evidence: .local/hpc-sync/latest_manifest.json and latest_receipt.json on the local checkout, manifest also on HPC.

## Remaining scope

Default system python3 stays 3.6.9; the existing uv-managed 3.11.15 is selected by absolute path without changing global Python. Source push never uploads local runs/receipts/dashboard/STATUS onto HPC. HPC output pulls use SHA-256 and an explicit 100 MiB default incremental download cap; larger outputs remain indexed on HPC with skipped_size_limit in receipts until deliberately pulled.

- 回执一致性修复：Windows 换行转换曾导致本地与 HPC 回执字节哈希不同；统一 UTF-8/LF，并将回执按原始字节写回及校验。旧回执的本地原始字节备份在 `.local/hpc-runs/receipt-line-ending-backups/`。
