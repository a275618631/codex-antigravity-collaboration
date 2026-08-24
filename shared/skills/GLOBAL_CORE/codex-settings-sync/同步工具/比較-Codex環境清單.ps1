param(
    [Parameter(Mandatory = $true)][string]$ReferenceManifest,
    [Parameter(Mandatory = $true)][string]$TargetManifest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

foreach ($path in @($ReferenceManifest, $TargetManifest)) { if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "找不到 Manifest：$path" } }
$reference = Get-Content -LiteralPath $ReferenceManifest -Raw -Encoding UTF8 | ConvertFrom-Json
$target = Get-Content -LiteralPath $TargetManifest -Raw -Encoding UTF8 | ConvertFrom-Json
$referenceMap = @{}; $targetMap = @{}
foreach ($item in @($reference.items)) { $referenceMap[$item.id] = $item }
foreach ($item in @($target.items)) { $targetMap[$item.id] = $item }

function Get-VersionKind([string]$ReferenceVersion, [string]$TargetVersion) {
    if ([string]::IsNullOrWhiteSpace($ReferenceVersion) -or [string]::IsNullOrWhiteSpace($TargetVersion)) { return 'unknown' }
    if ($ReferenceVersion -eq $TargetVersion) { return 'exact_match' }
    $r = [regex]::Match($ReferenceVersion, '(\d+)(?:\.(\d+))?'); $t = [regex]::Match($TargetVersion, '(\d+)(?:\.(\d+))?')
    if ($r.Success -and $t.Success -and $r.Groups[1].Value -eq $t.Groups[1].Value) { return 'compatible' }
    return 'different'
}

Write-Output '# Codex 環境清單比較'
Write-Output "來源：$ReferenceManifest"
Write-Output "目標：$TargetManifest"
Write-Output ''
$allIds = @($referenceMap.Keys + $targetMap.Keys | Sort-Object -Unique)
foreach ($id in $allIds) {
    $r = $referenceMap[$id]; $t = $targetMap[$id]
    if (-not $r) { Write-Output "$($t.name)`n  分類：僅目標電腦存在`n  建議動作：保留或人工確認是否納入同步`n"; continue }
    if (-not $t) { Write-Output "$($r.name)`n  分類：缺少工具／設定`n  建議動作：依來源電腦重建清單安裝、設定或登入`n"; continue }
    $version = Get-VersionKind ([string]$r.installation.version) ([string]$t.installation.version)
    $categories = [System.Collections.Generic.List[string]]::new()
    if ($r.installation.status -eq 'installed' -and $t.installation.status -ne 'installed') { $categories.Add('缺少工具') }
    if ($r.configuration.present -and -not $t.configuration.present) { $categories.Add('缺少設定') }
    if ($r.authentication.status -in @('logged_in', 'not_required') -and $t.authentication.status -notin @('logged_in', 'not_required')) { $categories.Add('需要登入') }
    if ($version -eq 'different') { $categories.Add('版本不一致') }
    if ($t.verification.connection -eq 'failed' -or $t.verification.tools_list -eq 'failed') { $categories.Add('連線驗證失敗') }
    if ($categories.Count -eq 0) { $categories.Add('已完成') }
    Write-Output "$($r.name)`n  分類：$($categories -join '、')`n  版本判定：$version`n  來源狀態：$($r.current_status)`n  目標狀態：$($t.current_status)`n  建議動作：$(if ($categories -contains '已完成') { '無；維持目前設定' } else { '依來源 restore.steps 逐項處理後重新匯出比較' })`n"
}
