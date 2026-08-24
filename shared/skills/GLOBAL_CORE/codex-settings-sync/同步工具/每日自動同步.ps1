$ErrorActionPreference = "Stop"

Write-Output "This script no longer pulls settings automatically."
Write-Output "Use 手動拉取分類設定.ps1 with explicit -Category choices instead."
Write-Output "Example:"
Write-Output "  .\同步工具\手動拉取分類設定.ps1 -Pull -SourceComputer YOUR-PC -Category agents-root,skills -Union"
