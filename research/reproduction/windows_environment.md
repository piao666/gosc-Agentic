# Windows reproduction environment

## Scope and provenance

[CODE] The upstream baseline is `387b49389385b51c275dc5a22ec1672087edda1d` from
<https://github.com/frezazadeh/gosc-agentic-teams>. Its source, tests, MIT LICENSE,
original per-mission results, and public LLM caches are retained without algorithm changes.
The requested working repository is <https://github.com/piao666/gosc-Agentic>.
The original README and citation remain authoritative for attribution.

The two regenerated summary JSON files were removed at the user's request. Local copies
are under ignored `.local/`; original upstream versions remain in Git history. This does
not delete raw experiment records. Those summaries are generated outputs, not fresh
simulation evidence.

## Recorded configuration

[RUN] CPython 3.12.10 (64-bit), Windows 11 build 26200. Application/test dependencies
are snapshotted in `requirements-windows.lock.txt`; this is a version-pinned Windows
snapshot, not the author's historical environment and not a wheel-hash lock.
The detailed manifest and actual validation logs are under
`research/logs/environment-2026-10-12/`.

Python settings used for validation: `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`,
`MPLBACKEND=Agg`. UTF-8 is an environment setting; no source or test encoding
assumptions are patched. Agg permits plotting without a desktop window.

## Current workspace location

[CODE] On 2026-10-19 the user relocated the working checkout to `E:\gosc` and confirmed the paper library is `E:\Papers`. Commands below use the current checkout path. The recorded 2026-10-12 environment/test evidence is historical; the new checkout has no `.venv` yet and has not rerun those checks.

## Setup from PowerShell

Install/use CPython 3.12 (the recorded patch version is 3.12.10), then run:

```powershell
Set-Location 'E:\gosc'
& .\scripts\bootstrap_windows.ps1
```

The helper creates `.venv` only if missing, uses its interpreter explicitly, installs
the pinned small Python dependencies, and checks imports and dependency consistency.
It does not install Ollama, download models, unpack results, or run experiments.
An existing virtual environment with another Python minor version is rejected rather
than deleted or overwritten. Shell activation is unnecessary.

To request the upstream tests as well:

```powershell
& .\scripts\bootstrap_windows.ps1 -RunTests
```

Or, in a new shell after dependencies are installed:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:MPLBACKEND = 'Agg'
.\.venv\Scripts\python.exe -B -X utf8 -m pytest -q tests -p no:cacheprovider
```

If PowerShell execution policy blocks the helper, execute the equivalent individual
commands; do not change the machine-wide execution policy automatically.

## Stage boundaries

- R1 is determined by actual collection and test logs, not README's expected count.
- R2 (all paper figures/tables from stored data) has not been performed in this task.
- R3/R4 fresh missions and paired campaigns have not been performed in this task.
- The tests contain simulation regression checks, which do not constitute complete paper reproduction.
- Fake-transport LLM tests do not assess a real language model.
- Cached replay and live Ollama runs remain separate future checkpoints. No model has
  been installed or queried by this task. A cache miss can cause the original client
  to issue a live request; do not start an LLM campaign merely because cache files exist.

## Protecting original results

Do not execute the upstream plotting/campaign modules in the original result directory
until their write paths are redirected or an isolated copy is prepared. Plotting writes
summaries and figures; the Bash decompression helper uses overwriting flags. In Windows,
use a separately reviewed Python gzip workflow with exclusive output creation in an
isolated analysis directory. `.gz` result files already present in Git are sufficient
for transport; unpacking is not required to validate this environment.

Keep `.venv/`, `.local/`, credentials, private PDFs, and machine-specific temporary files
out of Git. New experiment inputs/configurations, seeds, model/cache mode, output hashes,
and negative results must be captured in their own manifests.
