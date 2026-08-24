param(
    [string]$RepoPath = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Branch = "master",
    [string]$SourceComputer = "",
    [string[]]$Category = @("all"),
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }),
    [string]$TargetWorkflowsPath = (Join-Path $CodexHome "workflows"),
    [switch]$Pull,
    [switch]$Union,
    [switch]$ListSources
)

$ErrorActionPreference = "Stop"

$validCategories = @(
    "agents-root",
    "agents-codex",
    "agents",
    "config",
    "execution-profiles",
    "skills",
    "workflows",
    "workflow-definitions",
    "sync-tools-and-docs",
    "all"
)

function Ensure-Directory([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Test-TextFile([string]$Path) {
    $extensions = @(".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".ps1", ".sh")
    return $extensions -contains ([System.IO.Path]::GetExtension($Path).ToLowerInvariant())
}

function Copy-OrUnionFile([string]$Source, [string]$Destination, [switch]$UseUnion) {
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        Write-Output "Skipped missing source: $Source"
        return
    }

    Ensure-Directory (Split-Path -Parent $Destination)
    if (-not (Test-Path -LiteralPath $Destination -PathType Leaf) -or -not $UseUnion) {
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
        return
    }

    if (-not (Test-TextFile $Source)) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($Destination)
        $ext = [System.IO.Path]::GetExtension($Destination)
        $conflictPath = Join-Path (Split-Path -Parent $Destination) "$name.remote-conflict$ext"
        Copy-Item -LiteralPath $Source -Destination $conflictPath -Force
        return
    }

    $localLines = [System.Collections.Generic.List[string]]::new()
    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        foreach ($line in Get-Content -LiteralPath $Destination -Encoding UTF8) {
            $localLines.Add($line)
        }
    }

    $known = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($line in $localLines) {
        [void]$known.Add($line)
    }

    $missing = [System.Collections.Generic.List[string]]::new()
    foreach ($line in Get-Content -LiteralPath $Source -Encoding UTF8) {
        if (-not $known.Contains($line)) {
            $missing.Add($line)
            [void]$known.Add($line)
        }
    }

    if ($missing.Count -gt 0) {
        $localLines.Add("")
        $localLines.Add("# --- union from remote backup: $(Split-Path -Leaf (Split-Path -Parent $Source)) ---")
        foreach ($line in $missing) {
            $localLines.Add($line)
        }
        $localLines | Set-Content -LiteralPath $Destination -Encoding UTF8
    }
}

function Copy-OrUnionDirectory([string]$SourceDir, [string]$DestinationDir, [switch]$UseUnion) {
    if (-not (Test-Path -LiteralPath $SourceDir -PathType Container)) {
        return
    }

    Get-ChildItem -LiteralPath $SourceDir -Recurse -File -Force | ForEach-Object {
        $relative = [System.IO.Path]::GetRelativePath($SourceDir, $_.FullName)
        Copy-OrUnionFile $_.FullName (Join-Path $DestinationDir $relative) -UseUnion:$UseUnion
    }
}

function Resolve-LatestSourceComputer([string]$BackupsRoot) {
    $candidates = @()
    Get-ChildItem -LiteralPath $BackupsRoot -Directory | ForEach-Object {
        $infoPath = Join-Path $_.FullName "metadata\export-info.txt"
        $exportedAt = $null
        if (Test-Path -LiteralPath $infoPath -PathType Leaf) {
            $line = Get-Content -LiteralPath $infoPath -Encoding UTF8 |
                Where-Object { $_ -like "exported_at=*" } |
                Select-Object -First 1
            if ($line) {
                $exportedAt = $line -replace "^exported_at=", ""
            }
        }
        if (-not $exportedAt) {
            $exportedAt = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss zzz")
        }
        $candidates += [PSCustomObject]@{ Name = $_.Name; ExportedAt = $exportedAt }
    }

    if ($candidates.Count -eq 0) {
        Write-Error "No source computer backup found under $BackupsRoot."
    }

    return ($candidates | Sort-Object ExportedAt -Descending | Select-Object -First 1).Name
}

Push-Location -Path $RepoPath
try {

if ($Pull) {
    $currentBranch = git branch --show-current
    if (-not $currentBranch) {
        Write-Error "Cannot detect the current Git branch. Switch to the target branch before -Pull."
    }
    if ($currentBranch -ne $Branch) {
        Write-Error "Current branch is '$currentBranch', but GitHub source branch is '$Branch'. Switch to '$Branch' before -Pull."
    }
    if (git status --porcelain) {
        Write-Error "Working tree is not clean. Commit or back up local sync-repo changes before -Pull."
    }
    git pull --ff-only origin $Branch
}

$backupsRoot = Join-Path $RepoPath "backups"
if (-not (Test-Path -LiteralPath $backupsRoot -PathType Container)) {
    Write-Error "No backups directory found. Run export on at least one computer first."
}

if ($ListSources) {
    Get-ChildItem -LiteralPath $backupsRoot -Directory | Select-Object -ExpandProperty Name
    return
}

$Category = $Category |
    ForEach-Object { $_ -split "," } |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ }

if (-not $SourceComputer) {
    $SourceComputer = Resolve-LatestSourceComputer $backupsRoot
    Write-Output "Auto-selected latest source computer: $SourceComputer"
}

$invalid = $Category | Where-Object { $validCategories -notcontains $_ }
if ($invalid) {
    Write-Error "Invalid category: $($invalid -join ', '). Valid categories: $($validCategories -join ', ')"
}

if ($Category -contains "all") {
    $Category = $validCategories | Where-Object { $_ -ne "all" }
}

$sourceRoot = Join-Path $backupsRoot $SourceComputer
if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    Write-Error "Backup source not found: $sourceRoot"
}

foreach ($item in $Category) {
    switch ($item) {
        "agents-root" {
            Copy-OrUnionFile (Join-Path $sourceRoot "agents-root\AGENTS.md") (Join-Path $CodexHome "AGENTS.md") -UseUnion:$Union
        }
        "agents-codex" {
            Copy-OrUnionFile (Join-Path $sourceRoot "agents-codex\AGENTS.md") (Join-Path $CodexHome "AGENTS.md") -UseUnion:$Union
        }
        "agents" {
            Copy-OrUnionDirectory (Join-Path $sourceRoot "agents") (Join-Path $CodexHome "agents") -UseUnion:$Union
        }
        "config" {
            Copy-OrUnionFile (Join-Path $sourceRoot "config\config.toml") (Join-Path $CodexHome "config.toml") -UseUnion:$Union
        }
        "execution-profiles" {
            Copy-OrUnionDirectory (Join-Path $sourceRoot "execution-profiles") $CodexHome -UseUnion:$Union
        }
        "skills" {
            Copy-OrUnionDirectory (Join-Path $sourceRoot "skills") (Join-Path $CodexHome "skills") -UseUnion:$Union
        }
        "workflows" {
            Copy-OrUnionDirectory (Join-Path $sourceRoot "workflows") $TargetWorkflowsPath -UseUnion:$Union
        }
        "workflow-definitions" {
            Copy-OrUnionDirectory (Join-Path $sourceRoot "workflow-definitions") $TargetWorkflowsPath -UseUnion:$Union
        }
        "sync-tools-and-docs" {
            Copy-OrUnionDirectory (Join-Path $sourceRoot "sync-tools-and-docs") $RepoPath -UseUnion:$Union
        }
    }
}

Write-Output "Applied selected categories from $SourceComputer."
Write-Output "Categories: $($Category -join ', ')"
Write-Output "Union mode: $Union"
}
finally {
    Pop-Location
}
