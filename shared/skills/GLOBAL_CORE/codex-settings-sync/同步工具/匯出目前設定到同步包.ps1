param(
    [string]$RepoPath = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }),
    [string]$ProjectsRoot = (Resolve-Path "$PSScriptRoot\..\..").Path,
    [string]$ComputerName = $(if ($env:COMPUTERNAME) { $env:COMPUTERNAME } else { [System.Net.Dns]::GetHostName() })
)

$ErrorActionPreference = "Stop"

function Ensure-Directory([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Reset-Directory([string]$Path) {
    Ensure-Directory $Path
    Get-ChildItem -LiteralPath $Path -Force | Remove-Item -Recurse -Force
}

function Copy-FileIfExists([string]$Source, [string]$Destination) {
    if (Test-Path -LiteralPath $Source -PathType Leaf) {
        Ensure-Directory (Split-Path -Parent $Destination)
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
    }
}

function Export-SafeConfigToml([string]$Source, [string]$Destination) {
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        return
    }

    $blockedSectionPrefixes = @(
        "[projects.",
        "[marketplaces.",
        "[mcp_servers.",
        "[windows]"
    )
    $blockedSectionExact = @(
        "[mcp_servers.node_repl.env]"
    )
    $blockedTopLevelKeys = @(
        "notify"
    )
    $blockedValuePatterns = @(
        "C:\",
        "c:\",
        "C:/",
        "c:/",
        "\\?\",
        "\\.\pipe\",
        "CODEX_HOME",
        "TRUSTED_CODE_PATHS"
    )

    Ensure-Directory (Split-Path -Parent $Destination)
    $safeLines = [System.Collections.Generic.List[string]]::new()
    $sectionLines = [System.Collections.Generic.List[string]]::new()
    $sectionName = $null

    function Test-BlockedValue([string]$Line, [string[]]$Patterns) {
        foreach ($pattern in $Patterns) {
            if ($Line.Contains($pattern, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
        }
        return $false
    }

    function Add-SafeSection {
        param(
            [string]$Name,
            [System.Collections.Generic.List[string]]$Lines
        )

        if ($Lines.Count -eq 0) {
            return
        }

        if ($null -eq $Name) {
            foreach ($line in $Lines) {
                $trimmed = $line.Trim()
                $key = ($trimmed -split "=", 2)[0].Trim()
                if ($blockedTopLevelKeys -contains $key) {
                    continue
                }
                if (-not (Test-BlockedValue $line $blockedValuePatterns)) {
                    $safeLines.Add($line)
                }
            }
            return
        }

        foreach ($blocked in $blockedSectionExact) {
            if ($Name.Equals($blocked, [System.StringComparison]::OrdinalIgnoreCase)) {
                return
            }
        }

        foreach ($prefix in $blockedSectionPrefixes) {
            if ($Name.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                return
            }
        }

        foreach ($line in $Lines) {
            if (Test-BlockedValue $line $blockedValuePatterns) {
                return
            }
        }

        foreach ($line in $Lines) {
            $safeLines.Add($line)
        }
    }

    foreach ($line in Get-Content -LiteralPath $Source -Encoding UTF8) {
        $trimmed = $line.Trim()
        if ($trimmed.StartsWith("[") -and $trimmed.EndsWith("]")) {
            Add-SafeSection $sectionName $sectionLines
            $sectionLines = [System.Collections.Generic.List[string]]::new()
            $sectionName = $trimmed
        }

        $sectionLines.Add($line)
    }

    Add-SafeSection $sectionName $sectionLines
    $safeLines | Set-Content -LiteralPath $Destination -Encoding UTF8
}

function Copy-DirectoryContentsIfExists([string]$Source, [string]$Destination, [string[]]$ExcludedNames = @()) {
    Reset-Directory $Destination
    if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
        return
    }

    Get-ChildItem -LiteralPath $Source -Force |
        Where-Object { $ExcludedNames -notcontains $_.Name } |
        ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $Destination $_.Name) -Recurse -Force
        }
}

$backupRoot = Join-Path (Join-Path $RepoPath "backups") $ComputerName
$metadataPath = Join-Path $backupRoot "metadata"
$legacySyncRoot = Join-Path $RepoPath "要同步的Codex設定"
$legacyCodexRoot = Join-Path $legacySyncRoot ".codex"

Ensure-Directory $backupRoot
Ensure-Directory $metadataPath
Ensure-Directory $legacySyncRoot
Ensure-Directory $legacyCodexRoot

foreach ($blockedPortablePath in @((Join-Path $backupRoot "rules"), (Join-Path $legacyCodexRoot "rules"))) {
    if (Test-Path -LiteralPath $blockedPortablePath) {
        Remove-Item -LiteralPath $blockedPortablePath -Recurse -Force
    }
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
@(
    "computer=$ComputerName"
    "exported_at=$timestamp"
) | Set-Content -LiteralPath (Join-Path $metadataPath "export-info.txt") -Encoding UTF8

Copy-FileIfExists (Join-Path $CodexHome "AGENTS.md") (Join-Path $backupRoot "agents-root\AGENTS.md")
Copy-FileIfExists (Join-Path $CodexHome "AGENTS.md") (Join-Path $backupRoot "agents-codex\AGENTS.md")
Copy-FileIfExists (Join-Path $CodexHome "AGENTS.md") (Join-Path $legacySyncRoot "AGENTS.md")
Copy-FileIfExists (Join-Path $CodexHome "AGENTS.md") (Join-Path $legacyCodexRoot "AGENTS.md")
Copy-FileIfExists (Join-Path $RepoPath "AGENTS.md") (Join-Path $backupRoot "project-agents\AGENTS.md")
Export-SafeConfigToml (Join-Path $CodexHome "config.toml") (Join-Path $backupRoot "config\config.toml")
Copy-FileIfExists (Join-Path $backupRoot "config\config.toml") (Join-Path $legacyCodexRoot "config.toml")

$executionProfilesDest = Join-Path $backupRoot "execution-profiles"
Reset-Directory $executionProfilesDest
foreach ($profileName in @("sol-auto.config.toml", "luna-manual.config.toml")) {
    Copy-FileIfExists (Join-Path $CodexHome $profileName) (Join-Path $executionProfilesDest $profileName)
    Copy-FileIfExists (Join-Path $CodexHome $profileName) (Join-Path $legacyCodexRoot $profileName)
}

Copy-DirectoryContentsIfExists (Join-Path $CodexHome "skills") (Join-Path $backupRoot "skills") @(".system")

$workflowsDest = Join-Path $backupRoot "workflows"
Reset-Directory $workflowsDest
if (Test-Path -LiteralPath $ProjectsRoot -PathType Container) {
    Get-ChildItem -LiteralPath $ProjectsRoot -Directory -Force |
        Where-Object { $_.FullName -ne $RepoPath } |
        ForEach-Object {
            $workflowDir = Join-Path $_.FullName "workflows"
            if (Test-Path -LiteralPath $workflowDir -PathType Container) {
                $projectName = $_.Name
                Get-ChildItem -LiteralPath $workflowDir -File |
                    Where-Object { @(".yaml", ".yml", ".md") -contains $_.Extension.ToLowerInvariant() } |
                    ForEach-Object {
                        $projectWorkflowDest = Join-Path $workflowsDest $projectName
                        Ensure-Directory $projectWorkflowDest
                        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $projectWorkflowDest $_.Name) -Force
                    }
            }
        }
}

$syncToolsDest = Join-Path $backupRoot "sync-tools-and-docs"
Reset-Directory $syncToolsDest
Copy-Item -LiteralPath (Join-Path $RepoPath "同步工具") -Destination (Join-Path $syncToolsDest "同步工具") -Recurse -Force
Get-ChildItem -LiteralPath $RepoPath -File -Force |
    Where-Object { @(".md", ".txt") -contains $_.Extension.ToLowerInvariant() } |
    ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $syncToolsDest $_.Name) -Force
    }

foreach ($directoryName in @("schemas", "文件")) {
    $sourceDirectory = Join-Path $RepoPath $directoryName
    if (Test-Path -LiteralPath $sourceDirectory -PathType Container) {
        Copy-DirectoryContentsIfExists $sourceDirectory (Join-Path $syncToolsDest $directoryName)
    }
}
$environmentCurrent = Join-Path $RepoPath "環境清單\current"
if (Test-Path -LiteralPath $environmentCurrent -PathType Container) {
    Copy-DirectoryContentsIfExists $environmentCurrent (Join-Path $syncToolsDest "環境清單\current")
}

Write-Output "Exported categorized Codex settings backup."
Write-Output "Backup root: $backupRoot"
Write-Output "Categories: agents-root, agents-codex, project-agents, config, execution-profiles, skills, workflows, sync-tools-and-docs, environment-manifest"
