param(
    [string]$RepoPath = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }),
    [string]$ProjectsRoot = (Resolve-Path "$PSScriptRoot\..\..").Path,
    [string]$ComputerName = $(if ($env:COMPUTERNAME) { $env:COMPUTERNAME } else { [System.Net.Dns]::GetHostName() })
)

$ErrorActionPreference = "Stop"
$baseScript = Join-Path $PSScriptRoot "匯出目前設定到同步包.ps1"
& $baseScript -RepoPath $RepoPath -CodexHome $CodexHome -ProjectsRoot $ProjectsRoot -ComputerName $ComputerName

$backupRoot = Join-Path (Join-Path $RepoPath "backups") $ComputerName
$legacyCodexRoot = Join-Path (Join-Path $RepoPath "要同步的Codex設定") ".codex"

function Copy-PortableDirectory([string]$Source, [string]$BackupDestination, [string]$SyncDestination, [string[]]$ExcludedNames = @()) {
    if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
        return
    }
    foreach ($destination in @($BackupDestination, $SyncDestination)) {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        Get-ChildItem -LiteralPath $destination -Force | Remove-Item -Recurse -Force
        Get-ChildItem -LiteralPath $Source -Force | Where-Object { $ExcludedNames -notcontains $_.Name } | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $destination $_.Name) -Recurse -Force
        }
    }
}

Copy-PortableDirectory (Join-Path $CodexHome "agents") (Join-Path $backupRoot "agents") (Join-Path $legacyCodexRoot "agents")
Copy-PortableDirectory (Join-Path $CodexHome "workflows") (Join-Path $backupRoot "workflow-definitions") (Join-Path $legacyCodexRoot "workflows")
Copy-PortableDirectory (Join-Path $CodexHome "skills") (Join-Path $backupRoot "skills") (Join-Path $legacyCodexRoot "skills") @(".system")

$safeConfig = Join-Path $backupRoot "config\config.toml"
if (Test-Path -LiteralPath $safeConfig -PathType Leaf) {
    Copy-Item -LiteralPath $safeConfig -Destination (Join-Path $legacyCodexRoot "config.toml") -Force
}

$snapshotRoot = Join-Path $backupRoot "snapshots"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$snapshot = Join-Path $snapshotRoot $stamp
New-Item -ItemType Directory -Path $snapshot -Force | Out-Null

Get-ChildItem -LiteralPath $backupRoot -Force |
    Where-Object { $_.Name -ne "snapshots" } |
    ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $snapshot $_.Name) -Recurse -Force
    }

@(
    "snapshot_at=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
    "source_backup_root=$backupRoot"
) | Set-Content -LiteralPath (Join-Path $snapshot "snapshot-info.txt") -Encoding UTF8

Write-Output "Created immutable timestamp snapshot: $snapshot"
