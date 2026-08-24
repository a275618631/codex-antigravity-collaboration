param(
    [string]$ManifestPath = (Join-Path (Resolve-Path "$PSScriptRoot\..\環境清單\current").Path 'codex-environment-manifest.json'),
    [string]$OutputPath = (Join-Path (Resolve-Path "$PSScriptRoot\..\環境清單\current").Path 'codex-restore-checklist.md')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Codex環境清單共用.ps1')
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw "找不到 Manifest：$ManifestPath" }
$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-RestoreChecklist -Manifest $manifest -Path $OutputPath
Write-Output "重建清單已產生：$OutputPath"
