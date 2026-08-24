Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-CodexHomePath {
    if ($env:CODEX_HOME) { return [IO.Path]::GetFullPath($env:CODEX_HOME) }
    return [IO.Path]::GetFullPath((Join-Path $HOME '.codex'))
}

function ConvertTo-PortablePath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return [PSCustomObject]@{ Value = ''; MachineSpecific = $false } }
    $value = $Path.Trim().Trim('"', "'")
    $replacements = @(
        @{ Root = $env:USERPROFILE; Token = '%USERPROFILE%' },
        @{ Root = $env:LOCALAPPDATA; Token = '%LOCALAPPDATA%' },
        @{ Root = $env:APPDATA; Token = '%APPDATA%' },
        @{ Root = $env:PROGRAMFILES; Token = '%PROGRAMFILES%' },
        @{ Root = ${env:ProgramFiles(x86)}; Token = '%PROGRAMFILES(X86)%' },
        @{ Root = $env:TEMP; Token = '%TEMP%' }
    )
    foreach ($replacement in $replacements) {
        if ($replacement.Root -and $value.StartsWith($replacement.Root, [StringComparison]::OrdinalIgnoreCase)) {
            return [PSCustomObject]@{ Value = $replacement.Token + $value.Substring($replacement.Root.Length); MachineSpecific = $true }
        }
    }
    if ($value -match '^[A-Za-z]:[\\/]') {
        return [PSCustomObject]@{ Value = '<machine-path-omitted>'; MachineSpecific = $true }
    }
    return [PSCustomObject]@{ Value = $value.Replace('/', '\'); MachineSpecific = $false }
}

function Get-CommandInfo([string]$Name) {
    $command = Get-Command -Name $Name -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) {
        return [PSCustomObject]@{ Name = $Name; Installed = $false; Path = ''; PortablePath = ''; MachineSpecific = $false; Version = '' }
    }
    $path = if ($command.Source) { [string]$command.Source } else { [string]$command.Path }
    $portable = ConvertTo-PortablePath $path
    $version = ''
    try {
        $result = Invoke-ReadOnlyCommand -FilePath $path -Arguments @('--version') -TimeoutSeconds 8
        if ($result.ExitCode -eq 0 -and $result.StdOut) { $version = (($result.StdOut -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1).Trim()) }
    } catch { $version = '' }
    return [PSCustomObject]@{ Name = $Name; Installed = $true; Path = $path; PortablePath = $portable.Value; MachineSpecific = $portable.MachineSpecific; Version = $version }
}

function Invoke-ReadOnlyCommand {
    param([string]$FilePath, [string[]]$Arguments = @(), [int]$TimeoutSeconds = 10)
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FilePath
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    foreach ($argument in $Arguments) { [void]$startInfo.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    if (-not $process.Start()) { throw "無法啟動唯讀命令：$FilePath" }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $timedOut = -not $process.WaitForExit($TimeoutSeconds * 1000)
    if ($timedOut) { try { $process.Kill($true) } catch { try { $process.Kill() } catch {} }; $process.WaitForExit() }
    return [PSCustomObject]@{
        ExitCode = if ($timedOut) { 124 } else { $process.ExitCode }
        TimedOut = $timedOut
        StdOut = $stdoutTask.Result
        StdErr = $stderrTask.Result
    }
}

function Get-TomlString([string]$Line) {
    if ($Line -notmatch '=') { return '' }
    return (($Line -split '=', 2)[1]).Trim().Trim([char]39, [char]34)
}

function Get-TomlArray([string]$Line) {
    $match = [regex]::Match($Line, '=\s*\[(.*?)\]\s*$')
    if (-not $match.Success) { return @() }
    return @($match.Groups[1].Value -split ',' | ForEach-Object { $_.Trim().Trim([char]39, [char]34) } | Where-Object { $_ })
}

function Get-McpDefinitions([string]$ConfigPath) {
    $items = [System.Collections.Generic.List[object]]::new()
    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) { return @() }
    $lines = Get-Content -LiteralPath $ConfigPath -Encoding UTF8
    $section = ''
    $block = [System.Collections.Generic.List[string]]::new()
    $environmentNames = [System.Collections.Generic.List[string]]::new()
    $inEnvironmentSection = $false
    function Add-McpBlock([string]$Name, [System.Collections.Generic.List[string]]$Lines, [System.Collections.Generic.List[string]]$EnvNames) {
        if ([string]::IsNullOrWhiteSpace($Name)) { return }
        $commandLine = $Lines | Where-Object { $_ -match '^\s*command\s*=' } | Select-Object -First 1
        $argsLine = $Lines | Where-Object { $_ -match '^\s*args\s*=' } | Select-Object -First 1
        $command = if ($commandLine) { Get-TomlString $commandLine } else { '' }
        $args = if ($argsLine) { @(Get-TomlArray $argsLine) } else { @() }
        $envNames = @($EnvNames | Sort-Object -Unique)
        $portable = ConvertTo-PortablePath $command
        $resolved = $null
        if ($command -and (Test-Path -LiteralPath $command -PathType Leaf)) { $resolved = $command }
        elseif ($command) { $resolved = (Get-Command -Name $command -ErrorAction SilentlyContinue | Select-Object -First 1).Source }
        $items.Add([PSCustomObject]@{ Name = $Name; Command = $command; Args = $args; EnvironmentVariables = $envNames; PortableCommand = $portable.Value; MachineSpecific = $portable.MachineSpecific; ExecutableFound = [bool]$resolved })
    }
    foreach ($line in $lines) {
        $header = [regex]::Match($line, '^\s*\[mcp_servers\.([^.\]]+)\]\s*$')
        if ($header.Success) {
            Add-McpBlock $section $block $environmentNames
            $section = $header.Groups[1].Value.Trim('"', "'")
            $block = [System.Collections.Generic.List[string]]::new()
            $environmentNames = [System.Collections.Generic.List[string]]::new()
            $inEnvironmentSection = $false
            continue
        }
        $environmentHeader = [regex]::Match($line, '^\s*\[mcp_servers\.([^.\]]+)\.env\]\s*$')
        if ($environmentHeader.Success -and $environmentHeader.Groups[1].Value -eq $section) {
            $inEnvironmentSection = $true
            continue
        }
        if ($line -match '^\s*\[') {
            Add-McpBlock $section $block $environmentNames
            $section = ''
            $block = [System.Collections.Generic.List[string]]::new()
            $environmentNames = [System.Collections.Generic.List[string]]::new()
            $inEnvironmentSection = $false
            continue
        }
        if ($section) {
            $block.Add($line)
            if ($inEnvironmentSection -and $line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') { $environmentNames.Add($Matches[1]) }
        }
    }
    Add-McpBlock $section $block $environmentNames
    return @($items)
}

function Get-AuthStatus([string]$ToolName) {
    if ($ToolName -eq 'gh') {
        $gh = Get-CommandInfo 'gh'
        if (-not $gh.Installed) { return 'not_logged_in' }
        try { $result = Invoke-ReadOnlyCommand -FilePath $gh.Path -Arguments @('auth', 'status') -TimeoutSeconds 10; if ($result.ExitCode -eq 0) { return 'logged_in' }; return 'expired_or_invalid' } catch { return 'unknown' }
    }
    return 'manual_verification_required'
}

function Test-McpStdio([string]$Command, [string[]]$Arguments) {
    if (-not $Command) { return [PSCustomObject]@{ Startup = 'not_run'; Initialize = 'not_run'; ToolsList = 'not_run' } }
    $process = [Diagnostics.Process]::new()
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Command
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    foreach ($argument in $Arguments) { [void]$info.ArgumentList.Add($argument) }
    $process.StartInfo = $info
    try {
        if (-not $process.Start()) { return [PSCustomObject]@{ Startup = 'failed'; Initialize = 'not_run'; ToolsList = 'not_run' } }
        $process.StandardInput.WriteLine('{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"codex-environment-inventory","version":"1.0"}}}')
        $process.StandardInput.WriteLine('{"jsonrpc":"2.0","method":"notifications/initialized"}')
        $process.StandardInput.WriteLine('{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}')
        $process.StandardInput.Flush()
        $initialize = $false; $tools = $false; $deadline = [DateTime]::UtcNow.AddSeconds(8)
        while ([DateTime]::UtcNow -lt $deadline) {
            $lineTask = $process.StandardOutput.ReadLineAsync()
            if (-not $lineTask.Wait(500)) { continue }
            $line = $lineTask.Result
            if (-not $line) { break }
            try { $message = $line | ConvertFrom-Json; if ($message.id -eq 1) { $initialize = $true }; if ($message.id -eq 2) { $tools = $true } } catch {}
            if ($initialize -and $tools) { break }
        }
        return [PSCustomObject]@{ Startup = 'passed'; Initialize = if ($initialize) { 'passed' } else { 'failed' }; ToolsList = if ($tools) { 'passed' } else { 'failed' } }
    } catch { return [PSCustomObject]@{ Startup = 'failed'; Initialize = 'not_run'; ToolsList = 'not_run' } }
    finally { try { if (-not $process.HasExited) { $process.Kill($true) } } catch { try { $process.Kill() } catch {} }; $process.Dispose() }
}

function ConvertTo-YamlScalar([object]$Value) {
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [bool]) { return $Value.ToString().ToLowerInvariant() }
    if ($Value -is [int] -or $Value -is [long] -or $Value -is [double] -or $Value -is [decimal]) { return [string]$Value }
    $text = [string]$Value
    return "'" + $text.Replace("'", "''") + "'"
}

function ConvertTo-Yaml([object]$Value, [int]$Indent = 0) {
    $pad = ' ' * $Indent
    if ($null -eq $Value) { return @($pad + 'null') }
    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string] -and $Value -isnot [System.Collections.IDictionary]) {
        $lines = [System.Collections.Generic.List[string]]::new()
        foreach ($item in $Value) {
            if ($item -is [PSCustomObject] -or $item -is [System.Collections.IDictionary]) { $lines.Add($pad + '-'); $lines.AddRange([string[]](ConvertTo-Yaml $item ($Indent + 2))) }
            else { $lines.Add($pad + '- ' + (ConvertTo-YamlScalar $item)) }
        }
        return @($lines)
    }
    if ($Value -is [PSCustomObject] -or $Value -is [System.Collections.IDictionary]) {
        $lines = [System.Collections.Generic.List[string]]::new()
        $properties = if ($Value -is [System.Collections.IDictionary]) { $Value.Keys | ForEach-Object { [PSCustomObject]@{ Name = $_; Value = $Value[$_] } } } else { $Value.PSObject.Properties }
        foreach ($property in $properties) {
            $propertyValue = if ($property.PSObject.Properties['Value']) { $property.Value } else { $property.Value }
            if ($null -eq $propertyValue -or $propertyValue -is [string] -or $propertyValue -is [bool] -or $propertyValue -is [ValueType]) { $lines.Add($pad + [string]$property.Name + ': ' + (ConvertTo-YamlScalar $propertyValue)) }
            else { $lines.Add($pad + [string]$property.Name + ':'); $lines.AddRange([string[]](ConvertTo-Yaml $propertyValue ($Indent + 2))) }
        }
        return @($lines)
    }
    return @($pad + (ConvertTo-YamlScalar $Value))
}

function New-EnvironmentManifest {
    param([string]$RepoPath = (Resolve-Path "$PSScriptRoot\..").Path, [string]$CodexHome = (Get-CodexHomePath))
    $configPath = Join-Path $CodexHome 'config.toml'
    $items = [System.Collections.Generic.List[object]]::new()
    $mcpDefinitions = @(Get-McpDefinitions $configPath)
    $codexInfo = Get-CommandInfo 'codex'
    foreach ($mcp in $mcpDefinitions) {
        $verification = [PSCustomObject]@{ Startup = 'not_run'; McpInitialize = 'not_run'; ToolsList = 'not_run'; VerifiedAt = $null }
        if ($mcp.ExecutableFound -and $mcp.Name -eq 'officecli') {
            $actualCommand = $mcp.Command
            if (-not (Test-Path -LiteralPath $actualCommand -PathType Leaf)) { $actualCommand = (Get-Command -Name $actualCommand -ErrorAction SilentlyContinue | Select-Object -First 1).Source }
            $test = Test-McpStdio $actualCommand $mcp.Args
            $verification = [PSCustomObject]@{ Startup = $test.Startup; McpInitialize = $test.Initialize; ToolsList = $test.ToolsList; VerifiedAt = (Get-Date).ToUniversalTime().ToString('o') }
        }
        $status = if (-not $mcp.ExecutableFound) { 'configured_not_installed' } elseif ($verification.McpInitialize -eq 'failed' -or $verification.ToolsList -eq 'failed') { 'verification_failed' } else { 'ready' }
        $items.Add([PSCustomObject]@{
            id = 'mcp:' + $mcp.Name; name = $mcp.Name; category = 'mcp_server'; current_status = $status
            discovery = [PSCustomObject]@{ source = 'codex_config'; historical = $false; confidence = 'confirmed' }
            installation = [PSCustomObject]@{ status = if ($mcp.ExecutableFound) { 'installed' } else { 'not_installed' }; executable_found = $mcp.ExecutableFound; version = '' }
            configuration = [PSCustomObject]@{ present = $true; enabled = $true; transport = 'stdio'; command_template = $mcp.PortableCommand; args = $mcp.Args; contains_machine_specific_path = $mcp.MachineSpecific; environment_variables = @($mcp.EnvironmentVariables | ForEach-Object { [PSCustomObject]@{ name = $_; configured = $true; value_exported = $false } }) }
            authentication = [PSCustomObject]@{ required = ($mcp.EnvironmentVariables.Count -gt 0); status = if ($mcp.EnvironmentVariables.Count -gt 0) { 'manual_verification_required' } else { 'not_required' }; secret_exported = $false }
            verification = $verification; restore = [PSCustomObject]@{ automatic_safe = $false; steps = @('在目標電腦安裝或確認 MCP 執行檔', '依 command_template 重新建立 Codex MCP 設定', '重新啟動 Codex', '執行 codex mcp get ' + $mcp.Name, '依 verification 欄位重新驗證 initialize 與 tools/list') }; notes = @('不會同步 env 值、登入狀態或本機絕對路徑。')
        })
    }
    $toolNames = @('codex', 'gh', 'git', 'python', 'py', 'pwsh', 'node', 'npm')
    foreach ($name in $toolNames) {
        $tool = Get-CommandInfo $name
        $status = if ($tool.Installed) { 'ready' } else { 'unknown' }
        $items.Add([PSCustomObject]@{ id = 'cli:' + $name; name = $name; category = 'cli_tool'; current_status = $status; discovery = [PSCustomObject]@{ source = 'workflow_allowlist'; historical = $false; confidence = 'confirmed' }; installation = [PSCustomObject]@{ status = if ($tool.Installed) { 'installed' } else { 'not_installed' }; resolved_command = $name; path_template = $tool.PortablePath; version = $tool.Version; architecture = 'unknown'; install_method = 'unknown' }; usage = [PSCustomObject]@{ referenced_by = @('Codex sync workflow') }; authentication = [PSCustomObject]@{ required = ($name -eq 'gh'); status = if ($name -eq 'gh') { Get-AuthStatus 'gh' } else { 'not_required' }; secret_exported = $false }; restore = [PSCustomObject]@{ preferred_install_method = 'manual'; steps = @('確認或安裝 ' + $name, '執行 ' + $name + ' --version'); verify_commands = @($name + ' --version') }; notes = @() })
    }
    $services = @([PSCustomObject]@{ Name = 'GitHub'; Tool = 'gh'; Required = $true }, [PSCustomObject]@{ Name = 'OpenAI Codex'; Tool = 'codex'; Required = $true })
    foreach ($service in $services) {
        $tool = Get-CommandInfo $service.Tool
        $auth = if ($service.Tool -eq 'gh') { Get-AuthStatus 'gh' } else { 'manual_verification_required' }
        $items.Add([PSCustomObject]@{ id = 'service:' + ($service.Name -replace '[^A-Za-z0-9]+', '-').Trim('-').ToLowerInvariant(); name = $service.Name; category = 'external_service'; current_status = if (-not $tool.Installed) { 'configured_not_installed' } elseif ($auth -eq 'logged_in') { 'ready' } else { 'login_required' }; discovery = [PSCustomObject]@{ source = 'codex_workflow'; historical = $false; confidence = 'confirmed' }; installation = [PSCustomObject]@{ status = if ($tool.Installed) { 'installed' } else { 'not_installed' } }; configuration = [PSCustomObject]@{ present = $tool.Installed }; authentication = [PSCustomObject]@{ required = $service.Required; status = $auth; account_identifier_exported = $false; secret_exported = $false; verification_method = if ($service.Tool -eq 'gh') { 'gh auth status' } else { '未讀取登入狀態，需在目標電腦由 Codex UI／CLI 驗證' } }; verification = [PSCustomObject]@{ startup = if ($tool.Installed) { 'passed' } else { 'not_run' }; connection = if ($auth -eq 'logged_in') { 'passed' } else { 'manual_verification_required' }; verified_at = $null }; restore = [PSCustomObject]@{ steps = if ($service.Tool -eq 'gh') { @('安裝 GitHub CLI', '執行 gh auth login', '執行 gh auth status') } else { @('安裝 Codex', '在 Codex UI／CLI 重新登入', '執行 Codex 的唯讀狀態檢查') } }; notes = @('不同步 token、cookie、OAuth 憑證或登入 session。') })
    }
    $skillsPath = Join-Path $CodexHome 'skills'
    if (Test-Path -LiteralPath $skillsPath -PathType Container) {
        Get-ChildItem -LiteralPath $skillsPath -Directory -Force | Where-Object { $_.Name -ne '.system' } | Sort-Object Name | ForEach-Object {
            $items.Add([PSCustomObject]@{ id = 'skill:' + $_.Name; name = $_.Name; category = 'codex_skill'; current_status = 'ready'; discovery = [PSCustomObject]@{ source = 'codex_home_skills'; historical = $false; confidence = 'confirmed' }; installation = [PSCustomObject]@{ status = 'installed'; source = 'local_custom'; path_template = '%USERPROFILE%\\.codex\\skills\\' + $_.Name }; authentication = [PSCustomObject]@{ required = $false; status = 'not_required'; secret_exported = $false }; restore = [PSCustomObject]@{ method = 'copy_or_reinstall'; source_available = $true; steps = @('從同步 repo 的 skills 分類套用或重新安裝此自訂 skill') }; notes = @('內建 .system 與 plugin cache 不列入。') })
        }
    }
    $itemsArray = @($items)
    return [PSCustomObject]@{ schema_version = '1.0'; generated_at = (Get-Date).ToUniversalTime().ToString('o'); machine = [PSCustomObject]@{ machine_identifier_exported = $false; username_exported = $false; os = 'Windows'; architecture = if ([Environment]::Is64BitOperatingSystem) { 'x64' } else { 'x86' } }; security = [PSCustomObject]@{ secrets_exported = $false; credential_stores_scanned = $false; browser_sessions_scanned = $false; environment_values_exported = $false }; summary = [PSCustomObject]@{ mcp_servers = @($itemsArray | Where-Object category -eq 'mcp_server').Count; cli_tools = @($itemsArray | Where-Object category -eq 'cli_tool').Count; external_services = @($itemsArray | Where-Object category -eq 'external_service').Count; codex_skills = @($itemsArray | Where-Object category -eq 'codex_skill').Count; login_required = @($itemsArray | Where-Object { $_.authentication.status -in @('login_required', 'manual_verification_required') }).Count; manual_restore_required = @($itemsArray | Where-Object { ($_.restore.PSObject.Properties['automatic_safe'] -and $_.restore.automatic_safe -eq $false) -or ($_.restore.PSObject.Properties['steps'] -and $_.restore.steps.Count -gt 0) }).Count }; items = $itemsArray }
}

function Write-EnvironmentManifestFiles {
    param([object]$Manifest, [string]$RepoPath)
    $current = Join-Path $RepoPath '環境清單\current'
    $history = Join-Path $RepoPath ('環境清單\history\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $current,$history -Force | Out-Null
    $jsonPath = Join-Path $current 'codex-environment-manifest.json'
    $yamlPath = Join-Path $current 'codex-environment-manifest.yaml'
    $json = $Manifest | ConvertTo-Json -Depth 30
    Set-Content -LiteralPath $jsonPath -Value $json -Encoding UTF8
    Set-Content -LiteralPath $yamlPath -Value ((ConvertTo-Yaml $Manifest) -join [Environment]::NewLine) -Encoding UTF8
    Copy-Item -LiteralPath $jsonPath -Destination $history -Force
    Copy-Item -LiteralPath $yamlPath -Destination $history -Force
    return [PSCustomObject]@{ Json = $jsonPath; Yaml = $yamlPath; History = $history }
}

function Write-RestoreChecklist([object]$Manifest, [string]$Path) {
    $lines = [System.Collections.Generic.List[string]]::new(); $lines.Add('# Codex 環境重建清單'); $lines.Add(''); $lines.Add('此清單只記錄安裝、設定、登入與驗證步驟；不包含秘密值、登入 session 或本機絕對路徑。'); $lines.Add('')
    foreach ($item in @($Manifest.items)) { $lines.Add('## ' + $item.name); $lines.Add(''); $lines.Add('- 類別：' + $item.category); $lines.Add('- 目前狀態：' + $item.current_status); $lines.Add('- 登入需求：' + $item.authentication.status); if ($item.restore.PSObject.Properties['steps']) { foreach ($step in @($item.restore.steps)) { $lines.Add('- [ ] ' + $step) } }; $lines.Add('') }
    Set-Content -LiteralPath $Path -Value ($lines -join [Environment]::NewLine) -Encoding UTF8
}
