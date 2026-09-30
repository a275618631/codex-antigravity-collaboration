$ErrorActionPreference = 'Stop'
$Config = if ($args.Count) { $args[0] } else { "$env:USERPROFILE\.config\github-handoff\config.json" }
py -3 -m github_handoff --config $Config doctor
Write-Output 'Verified only. No Scheduled Task or Windows service was installed.'
