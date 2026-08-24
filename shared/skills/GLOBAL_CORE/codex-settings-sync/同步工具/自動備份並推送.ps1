param(
    [string]$RepoPath = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Branch = "",
    [switch]$ConfirmPush
)

$ErrorActionPreference = "Stop"

Push-Location -Path $RepoPath
try {

& (Join-Path $PSScriptRoot "匯出目前設定到同步包.ps1") -RepoPath $RepoPath

if (-not $ConfirmPush) {
    Write-Output "Codex settings exported locally. Commit/Push skipped; rerun with -ConfirmPush only after an explicit GitHub upload request."
    return
}

if (-not (git remote)) {
    Write-Error "No GitHub remote configured. Add a private repo as origin first."
}

if (-not $Branch) {
    $Branch = git branch --show-current
}

if (-not $Branch) {
    Write-Error "Cannot detect current branch. Pass -Branch explicitly."
}

if ($Branch -in @("main", "master")) {
    Write-Error "Refusing to commit or push directly to default branch '$Branch'. Create a non-protected feature branch first."
}

git add backups 要同步的Codex設定 使用說明.md 同步規劃.md 同步工具

$hasStagedChanges = git diff --cached --quiet; if ($LASTEXITCODE -eq 1) { $true } else { $false }
if ($hasStagedChanges) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    git commit -m "Auto sync Codex settings $timestamp"
} else {
    Write-Output "No local Codex settings changes to commit."
}

git push -u origin $Branch

Write-Output "Codex settings exported, committed if needed, and pushed to origin/$Branch. Merge was not performed."
}
finally {
    Pop-Location
}
