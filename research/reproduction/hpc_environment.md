# HPC execution and workspace synchronization

## Connection and paths

- SSH alias on Windows: `hpc`; `ssh hpc`.
- Endpoint: `172.18.101.241:22610`; user `u202520081000097`; UID `8301880`.
- VPN: connect the school EasyConnect VPN before SSH.
- SSH config: `C:\Users\34904\.ssh\config`; dedicated identity `~/.ssh/id_ed25519_hpc`. Never upload the identity/private SSH configuration into the repository or HPC project.
- Local source: `E:\gosc`; reference PDFs remain in `E:\Papers`.
- JupyterLab file-browser root: `/home/u202520081000097/jupyterlab`.
- JupyterLab `Paper` folder: `/home/u202520081000097/jupyterlab/Paper`.
- Remote project: `/home/u202520081000097/jupyterlab/Paper/gosc`.

JupyterLab's `/` in its file browser represents the configured file-browser root. The screenshot's terminal was at the operating-system `/`, so `cd Paper` failed there. Use the absolute remote project path above in SSH/Jupyter terminals.

## Mandatory execution location

User instruction on 2026-10-19: all subsequent project tests, simulations, result analysis/replotting, benchmarks, inference, calibration and training that consume CPU/GPU/RAM must execute on HPC. This includes CPU-only pytest and smoke tests. Do not fall back to local computation when VPN/HPC is unavailable.

Local Windows is for source/document editing, Git inspection, lightweight file/hash checks, synchronization and report viewing. These operations do not authorize local model execution or project tests. Resource-heavy file analysis also belongs on HPC.

This chooses the execution location; it does not start or blanket-authorize long campaigns, environment installs, model downloads or paid APIs. Preserve the research stage gates and each user-authorized experiment's scope.

## Measured allocation on 2026-10-19

[RUN] Read-only SSH hardware inspection: container host `n1`, Ubuntu 18.04.6 / Linux 5.4.0-100-generic.

| Resource | Current allocation |
|---|---|
| CPU | AMD EPYC 9354; host reports 64 cores, container cpuset 0-1; cgroup quota 200000/100000 = 2 CPU cores |
| RAM | cgroup limit 25769803776 bytes = 24 GiB |
| GPU | NVIDIA L40; visible memory 34304 MiB = 33.5 GiB |
| GPU sharing | `/usr/local/vgpu/libvgpu.so` preload; `CUDA_DEVICE_MEMORY_LIMIT=34304m`, `CUDA_DEVICE_SM_LIMIT=75`; no throughput benchmark performed |
| Driver | 545.29.06; driver reports CUDA capability 12.3, not proof of an installed CUDA Toolkit |

Recheck allocation before each experiment; do not assume the whole host's CPU/RAM or exclusive whole-GPU access. Default CPU parallelism must not exceed 2 unless a new allocation is verified. Record actual peak memory, GPU memory, wall time, model/cache mode and seeds in the run manifest.

## Sync procedure (run on local Windows)

```powershell
Set-Location E:\gosc
python scripts/sync_hpc.py
```

The helper uses only the Python standard library, Git and OpenSSH. It ships a Git bundle plus the current tracked/untracked, non-ignored worktree files. It preserves history, current uncommitted edits and upstream original result/cache files. Linux copies use LF text line endings; manifest records both original local bytes and remote normalized SHA-256.

Excluded: `.git` working metadata/credentials, `.ssh`, private keys, `.env`, `.venv`, `.local`, caches and all Git-ignored files. Git history is transported through a bundle, not by copying local `.git/config` or hooks. Reference PDF files outside `E:\gosc` are not uploaded by this project sync.

The remote receiver verifies every payload hash, preserves remote-only files, and backs up changed non-result files in `.local/sync-backups/<sync-id>/`. It refuses changed remote original `results/` or `LICENSE`, an unrelated destination, or a different Git HEAD/origin. It never automatically deletes project files. Reconcile divergent Git state or source deletions explicitly before continuing.

Evidence: local and remote `.local/hpc-sync/latest_manifest.json`; local `.local/hpc-sync/latest_receipt.json`. Subsequent HPC jobs must use a successfully verified snapshot. New experiment outputs belong in `research/sync/runs/<run-id>/outputs/` with independent manifests; do not overwrite upstream `results/`.

## Remote checks and subsequent runs

```powershell
ssh hpc 'cd /home/u202520081000097/jupyterlab/Paper/gosc && git status --short && git rev-parse HEAD'
```

[RUN] The default `/usr/bin/python3` observed in this task is Python 3.6.9. The upstream README requires Python 3.9+, so that default interpreter is not a validated GOSC runtime. Before choosing a Python environment, inspect existing HPC interpreters and installed dependencies. The Windows dependency snapshot is historical and cannot be treated as a validated Linux environment. Tests/training have not been run merely by syncing the project.

For multiline remote scripts use UTF-8/LF bytes over SSH stdin; Windows text-mode pipes can convert newlines to CRLF. Never include passwords/tokens/private keys in commands or logs. Keep strict SSH host-key checking enabled.

Known independent startup issue: `.bashrc` line 13 attempts to execute the `jupyterlab/RAG` directory. It emits stderr on login; this sync does not modify that file.

## Verified uv Python and execution ledger (2026-10-19)

[RUN] The HPC also has uv 0.11.19 and managed CPython 3.11.15 at `/home/u202520081000097/.local/share/uv/python/cpython-3.11-linux-x86_64-gnu/bin/python3.11`, confirmed offline by `uv python find` and the actual interpreter. The earlier 3.6.9 observation only described the system default. The bare 3.11 currently lacks numpy/matplotlib/pytest; no project venv or dependencies were installed by this task.

New run records/outputs use `research/sync/runs/<run-id>/`, not upstream results. See `research/sync/README.md`. Source upload excludes HPC-owned runtime records. Use `python scripts/sync_hpc.py --pull-runs` to mirror status/logs/outputs back locally, with per-file receipt and size-limit reporting. The next compute task is project environment readiness and then R1 on HPC; local work is documentation and sync.

## Later execution update — HPC environment and R1–R3

The preceding bare-interpreter paragraph is the earlier read-only snapshot. The project now has `.venv/bin/python` (CPython 3.11.15), 15 pinned dependencies, and passed uv pip check/imports. Use research/sync/environment/project_environment.json and requirements-linux.lock.txt, not the old missing-package snapshot, for current readiness.

Actual HPC results on 2026-10-19: R1 85 passed (33.64s, no skips); R2 three original plot modules produced 17 PDFs and 18 TeX files, all three summary JSONs match historical baseline within 1e-10; R3 default GOSC seed3000 completed in 113 slots, 8 found, 0 false declarations. Full evidence: research/reproduction/repro_report.md and research/sync/runs/hpc-{env,r1,r2,r3}-20261019. These do not complete the full multi-seed/live-LLM/paper-by-paper reproduction stage.
