# Research Task Report - HPC policy and project sync (2026-10-19)

- **Research Question / Hypothesis**: [HYPOTHESIS] Can the current local research worktree be transported to the school HPC with its original baseline, uncommitted documentation and original result/cache files intact?
- **已核验前人工作**: [CODE] GOSC working HEAD `876fc523b113b3b65e19f0b730f1573ccc2ee17f`, upstream baseline `387b49389385b51c275dc5a22ec1672087edda1d`; no new paper or novelty claim.
- **实际阅读源码**: [CODE] AGENTS, README, .gitignore, workspace_paths; prior task brief and Git status. The new sync helper is source-transfer administration, not a GOSC algorithm.
- **本轮新增或修改**: AGENTS HPC connection/execution/sync rules; README HPC notice; workspace_paths HPC endpoints and paths; research/reproduction/hpc_environment.md; scripts/sync_hpc.py; this task brief/report and initial sync receipt.
- **实际运行**: [RUN] SSH directory/readlink inspection confirmed `/home/u202520081000097/jupyterlab/Paper` exists and was empty. HPC AST validation of the sync helper passed under Python 3.6.9. Local `python scripts/sync_hpc.py` creates a Git bundle and non-ignored worktree snapshot, uploads it by SCP and verifies every payload on HPC. Local lightweight hashing/packaging is administration, not a project compute test.
- **测试与结果**: [RUN] First snapshot: 108 files, zero SHA-256 mismatches, restored original HEAD/history and active research branch; see initial_sync_receipt.json. A final source synchronization includes this report and the default-Python note; authoritative latest file manifest/receipt are local `.local/hpc-sync/latest_manifest.json`, `latest_receipt.json` and remote `.local/hpc-sync/latest_manifest.json`. No pytest, simulation, model inference, calibration, benchmark or training was run.
- **失败/负面证据**: `.bashrc` line 13 still emits an independent directory-as-command warning; no shell startup file changed. Default python3=3.6.9 does not meet README Python 3.9+; choosing/creating a Linux experiment environment is pending, not silently replaced by local execution.
- **与原 GOSC 的差异**: No algorithm, tests, LICENSE or original result/cache modifications. Linux payload text uses LF; original local bytes remain untouched, with both local and remote hashes recorded.
- **公平性与泄露检查**: No training/eval or seed selection. No .ssh/private keys/.env/venv or private E:\Papers PDFs in the project upload. Git history travels as a bundle rather than local credentials/hooks/config. Remote-only files are preserved; no project deletions.
- **成本**: Source/archive/Git transport and lightweight HPC syntax/hash verification only; no models, paid API or high-load job. Peak resource use/network bytes not measured.
- **可否进入下一阶段**: Go for HPC environment inspection and reproduction protocol preparation. Project execution remains gated on an appropriate Linux Python/dependency environment and user-authorized experiment scope.
- **用户需要批准的下一步**: No further approval needed for this requested documentation/sync. This instruction chooses HPC as the execution venue, not an instruction to immediately install dependencies or start training.

## Connection and workspace

- Alias: `hpc`; endpoint: `172.18.101.241:22610`; user: `u202520081000097`; UID: `8301880`.
- Local source: `E:\gosc`.
- Remote source: `/home/u202520081000097/jupyterlab/Paper/gosc` (JupyterLab: `Paper/gosc`).
- Current resource allocation from the preceding read-only inspection: 2 CPU cores, 24 GiB RAM, L40 34304 MiB visible memory, CUDA_DEVICE_SM_LIMIT=75; recheck before experiments.
- User-requested rule: all subsequent CPU/GPU/RAM project tests, simulations, analysis/inference and training run on HPC. Local editing/Git/lightweight sync management remain allowed.

## Commands and evidence

- `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, `git remote -v`, `git ls-files --others --exclude-standard`, `git diff --check`.
- SSH read-only directory and interpreter checks; remote `ast.parse` of the helper.
- `python scripts/sync_hpc.py` (initial snapshot, followed by final documentation snapshot).
- Sync helper uses `git bundle create --all`, SCP, remote Git clone and SHA-256 verification; no remote Git reset/clean or file deletion.
- Source policy: AGENTS section E1. Path contract: research/workspace_paths.json. Setup instructions: research/reproduction/hpc_environment.md.
