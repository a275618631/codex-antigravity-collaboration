[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$skillRoot = Join-Path $repoRoot 'shared/skills/GLOBAL_CORE'
$manifestPath = Join-Path $repoRoot 'CANONICAL_MANIFEST.json'
$errors = [System.Collections.Generic.List[string]]::new()

function Get-NormalizedSha256([string] $Path) {
    $text = [IO.File]::ReadAllText($Path).Replace("`r`n", "`n")
    $bytes = [Text.Encoding]::UTF8.GetBytes($text)
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

$skills = Get-ChildItem -LiteralPath $skillRoot -Filter 'SKILL.md' -Recurse
$names = @{}
foreach ($skill in $skills) {
    $content = [IO.File]::ReadAllText($skill.FullName)
    if ($content -notmatch '(?s)\A---\s*\r?\n(.*?)\r?\n---') {
        $errors.Add("Missing or malformed frontmatter: $($skill.FullName)")
        continue
    }

    $frontmatter = $Matches[1]
    $nameMatch = [regex]::Match($frontmatter, '(?m)^name:\s*[''\"]?([^''\"\r\n]+)')
    $descriptionMatch = [regex]::Match($frontmatter, '(?m)^description:\s*(.+)$')
    if (-not $nameMatch.Success) { $errors.Add("Missing name: $($skill.FullName)") }
    if (-not $descriptionMatch.Success) { $errors.Add("Missing description: $($skill.FullName)") }
    if ($descriptionMatch.Success -and $descriptionMatch.Groups[1].Value.Trim(' ', "'", '"').Length -gt 1024) {
        $errors.Add("Description exceeds 1024 characters: $($skill.FullName)")
    }

    if ($nameMatch.Success) {
        $name = $nameMatch.Groups[1].Value.Trim()
        if ($names.ContainsKey($name)) { $errors.Add("Duplicate Skill name '$name': $($skill.FullName)") }
        else { $names[$name] = $skill.FullName }
        if ((Split-Path -Leaf $skill.DirectoryName) -ne $name) {
            $errors.Add("Skill folder/name mismatch '$name': $($skill.FullName)")
        }
    }

    foreach ($match in [regex]::Matches($content, '\[[^\]]+\]\((references/[^)#?]+)\)')) {
        $target = Join-Path $skill.DirectoryName ($match.Groups[1].Value -replace '/', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            $errors.Add("Broken reference '$($match.Groups[1].Value)': $($skill.FullName)")
        }
    }
}

$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$manifestSkillArtifacts = @($manifest.artifacts | Where-Object {
    $_.canonical_repo -eq 'a275618631/codex-antigravity-collaboration' -and
    $_.artifact -like 'skill:*' -and
    $_.artifact -notlike 'skill-reference:*'
})
$discoveredSkillPaths = @{}
foreach ($skill in $skills) {
    $relative = [IO.Path]::GetRelativePath($repoRoot, $skill.FullName).Replace('\', '/')
    $discoveredSkillPaths[$relative] = $skill.FullName
}
if ($manifestSkillArtifacts.Count -ne $discoveredSkillPaths.Count) {
    $errors.Add("Manifest Skill count ($($manifestSkillArtifacts.Count)) does not match discovered Skill count ($($discoveredSkillPaths.Count))")
}
$manifestSkillPaths = @{}
foreach ($artifact in $manifestSkillArtifacts) {
    $manifestSkillPaths[$artifact.canonical_path] = $true
}
foreach ($relative in $discoveredSkillPaths.Keys) {
    if (-not $manifestSkillPaths.ContainsKey($relative)) {
        $errors.Add("Discovered Skill missing from manifest: $relative")
    }
}
foreach ($relative in $manifestSkillPaths.Keys) {
    if (-not $discoveredSkillPaths.ContainsKey($relative)) {
        $errors.Add("Manifest Skill not discovered: $relative")
    }
}
foreach ($artifact in $manifest.artifacts) {
    if ($artifact.canonical_repo -ne 'a275618631/codex-antigravity-collaboration') { continue }
    $path = Join-Path $repoRoot ($artifact.canonical_path -replace '/', [IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $errors.Add("Missing canonical artifact: $($artifact.canonical_path)")
        continue
    }
    if ((Get-NormalizedSha256 $path) -ne $artifact.sha256) {
        $errors.Add("Manifest hash mismatch: $($artifact.canonical_path)")
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "PASS: $($skills.Count) Skills; frontmatter, descriptions, names, references, and manifest hashes validated."
