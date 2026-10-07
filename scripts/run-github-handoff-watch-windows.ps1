param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigPath,
    [string]$PythonPath = "python"
)

$ErrorActionPreference = "Stop"

if (-not $env:GH_TOKEN) {
    throw "GH_TOKEN must be injected into this foreground process before starting the receiver."
}
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "Receiver config file was not found."
}
if (-not (Get-Command -Name $PythonPath -ErrorAction SilentlyContinue)) {
    throw "Python executable was not found. Pass -PythonPath with an explicit Python 3.11+ executable."
}

try {
    & $PythonPath -m github_handoff --config $ConfigPath doctor
    if ($LASTEXITCODE -ne 0) { throw "Receiver doctor failed with exit $LASTEXITCODE." }
    & $PythonPath -m github_handoff --config $ConfigPath watch
    exit $LASTEXITCODE
}
finally {
    Remove-Item Env:GH_TOKEN -ErrorAction SilentlyContinue
}

