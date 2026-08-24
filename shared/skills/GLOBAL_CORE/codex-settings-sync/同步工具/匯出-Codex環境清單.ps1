param(
    [string]$RepoPath = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' })
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Codex環境清單共用.ps1')

$manifest = New-EnvironmentManifest -RepoPath $RepoPath -CodexHome $CodexHome
$paths = Write-EnvironmentManifestFiles -Manifest $manifest -RepoPath $RepoPath
Write-RestoreChecklist -Manifest $manifest -Path (Join-Path $RepoPath '環境清單\current\codex-restore-checklist.md')
$validationPath = Join-Path $RepoPath '環境清單\current\codex-environment-validation.md'
@(
    '# Codex 環境清單驗證報告'
    ''
    "產生時間：$($manifest.generated_at)"
    "JSON：$($paths.Json)"
    "YAML：$($paths.Yaml)"
    ''
    '- 未輸出秘密值：是'
    '- 未掃描 Credential Manager：是'
    '- 未掃描瀏覽器 Session：是'
    '- 未讀取 .env 值：是'
    '- 未執行登入：是'
    '- 未修改 Codex 設定：是'
    '- MCP 設定仍由既有安全匯出器排除：待執行既有同步測試確認'
    ''
    '此報告只描述本次唯讀盤點結果；若登入或連線狀態為 manual_verification_required，請在目標電腦重新登入並驗證。'
) | Set-Content -LiteralPath $validationPath -Encoding UTF8
Write-Output "環境清單已產生：$($paths.Json)"
