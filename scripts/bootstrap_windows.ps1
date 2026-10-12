param(
    [string]$Python = 'python',
    [switch]$RunTests
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvRoot = Join-Path $repoRoot '.venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
$lockFile = Join-Path $repoRoot 'requirements-windows.lock.txt'

# Process-local settings: UTF-8 avoids dependence on the Windows system code page.
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:MPLBACKEND = 'Agg'

Push-Location $repoRoot
try {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        & $Python -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)'
        if ($LASTEXITCODE -ne 0) { throw 'Use CPython 3.12; the recorded environment uses 3.12.10.' }
        & $Python -m venv $venvRoot
        if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
    }

    & $venvPython -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)'
    if ($LASTEXITCODE -ne 0) { throw 'The existing .venv must use CPython 3.12.' }

    & $venvPython -B -X utf8 -m pip install --disable-pip-version-check -r $lockFile
    if ($LASTEXITCODE -ne 0) { throw 'Installing locked dependencies failed.' }
    & $venvPython -B -X utf8 -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency validation failed.' }
    & $venvPython -B -X utf8 -c 'import numpy, matplotlib, pytest; from gosc import Config, Simulation; print("GOSC environment imports OK")'
    if ($LASTEXITCODE -ne 0) { throw 'Import validation failed.' }

    if ($RunTests) {
        $localRoot = Join-Path $repoRoot '.local'
        New-Item -ItemType Directory -Path $localRoot -Force | Out-Null
        $testTempRoot = Join-Path $localRoot ('pytest-' + [guid]::NewGuid().ToString('N'))
        & $venvPython -B -X utf8 -m pytest -q tests -p no:cacheprovider --basetemp $testTempRoot
        if ($LASTEXITCODE -ne 0) { throw 'Upstream tests failed; retain the output and investigate before experiments.' }
    }
} finally {
    Pop-Location
}
