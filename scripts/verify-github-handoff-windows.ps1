$ErrorActionPreference = 'Stop'
$Config = if ($args.Count) { $args[0] } else { "$env:USERPROFILE\.config\github-handoff\config.json" }
$PythonPath = $env:CODEX_PYTHON
$PythonArgs = @()

if (-not $PythonPath) {
    $BundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $BundledPython) {
        $PythonPath = $BundledPython
    }
}

if (-not $PythonPath) {
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        try {
            & $PyLauncher.Source -3 -c 'import sys' *> $null
            if ($LASTEXITCODE -eq 0) {
                $PythonPath = $PyLauncher.Source
                $PythonArgs = @('-3')
            }
        } catch {
            $PythonPath = $null
        }
    }
}

if (-not $PythonPath) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $PythonPath = $PythonCommand.Source
    }
}

if (-not $PythonPath -or (-not (Test-Path -LiteralPath $PythonPath))) {
    throw 'No usable Python runtime found. Set CODEX_PYTHON to an existing python.exe.'
}

& $PythonPath @PythonArgs -m github_handoff --config $Config doctor
Write-Output 'Verified only. No Scheduled Task or Windows service was installed.'
