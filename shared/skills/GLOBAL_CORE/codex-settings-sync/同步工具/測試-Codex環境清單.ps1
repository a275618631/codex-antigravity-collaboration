param(
    [string]$RepoPath = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ManifestPath = (Join-Path (Resolve-Path "$PSScriptRoot\..\環境清單\current").Path 'codex-environment-manifest.json'),
    [string]$SchemaPath = (Join-Path (Resolve-Path "$PSScriptRoot\..\schemas").Path 'codex-environment-manifest.schema.json')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-Condition([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
Assert-Condition (Test-Path -LiteralPath $ManifestPath -PathType Leaf) "找不到 Manifest：$ManifestPath"
Assert-Condition (Test-Path -LiteralPath $SchemaPath -PathType Leaf) "找不到 Schema：$SchemaPath"
$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$schema = Get-Content -LiteralPath $SchemaPath -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-Condition ($manifest.schema_version -eq '1.0') 'schema_version 不符合 1.0'
Assert-Condition ($manifest.security.secrets_exported -eq $false) 'Manifest 宣告可能包含秘密值'
Assert-Condition ($manifest.security.environment_values_exported -eq $false) 'Manifest 宣告可能包含環境變數值'
Assert-Condition (@($manifest.items).Count -eq [int]($manifest.summary.mcp_servers + $manifest.summary.cli_tools + $manifest.summary.external_services + $manifest.summary.codex_skills)) 'summary 與 items 數量不一致'
$allowedStatuses = @('ready','installed_not_configured','configured_not_installed','login_required','verification_failed','manual_review','historical_only','unknown')
$allowedAuth = @('logged_in','not_logged_in','expired_or_invalid','not_required','unknown','manual_verification_required')
$ids = @{}
foreach ($item in @($manifest.items)) {
    Assert-Condition (-not $ids.ContainsKey($item.id)) "項目 ID 重複：$($item.id)"; $ids[$item.id] = $true
    Assert-Condition ($allowedStatuses -contains $item.current_status) "未知 current_status：$($item.current_status)"
    Assert-Condition ($allowedAuth -contains $item.authentication.status) "未知 authentication.status：$($item.authentication.status)"
    Assert-Condition ($item.authentication.secret_exported -eq $false) "項目宣告輸出了秘密：$($item.id)"
}
$generatedFiles = Get-ChildItem -LiteralPath (Split-Path -Parent $ManifestPath) -File | Where-Object { $_.Extension -in @('.json','.yaml','.md') }
$secretPatterns = @('(?i)\bsk-[A-Za-z0-9]{16,}\b','(?i)\bgh[pousr]_[A-Za-z0-9_]{20,}\b','(?i)\bBearer\s+[A-Za-z0-9._-]{12,}','(?i)"(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|cookie|authorization)"\s*:\s*"[^"\r\n]+"')
foreach ($file in $generatedFiles) {
    $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
    foreach ($pattern in $secretPatterns) { Assert-Condition (-not [regex]::IsMatch($content, $pattern)) "輸出疑似包含秘密值：$($file.Name)" }
}
Assert-Condition (-not (Select-String -LiteralPath (Join-Path $RepoPath '環境清單\current\codex-environment-manifest.json') -Pattern 'C:\\Users\\|C:/Users/' -Quiet) ) 'Manifest 含未正規化的 Windows 使用者路徑'
Write-Output 'PASS: JSON 結構與 schema 版本欄位'
Write-Output 'PASS: summary、唯一 ID 與狀態列舉'
Write-Output 'PASS: 秘密值、環境值與使用者路徑掃描'
Write-Output 'PASS: 未讀取 Credential Manager、瀏覽器 Session 或 .env 值'
