# Collects the Victoria 3 logs needed to diagnose Vic3 TODO into one ZIP.
# Run after exiting the game: powershell -ExecutionPolicy Bypass -File .\tools\collect_logs.ps1
[CmdletBinding()]
param([string]$UserDataDir)
$ErrorActionPreference = "Stop"
if (-not $UserDataDir) {
    $UserDataDir = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Paradox Interactive\Victoria 3"
}
$Logs = Join-Path $UserDataDir "logs"
$Stage = Join-Path ([IO.Path]::GetTempPath()) ("vic3_todo_logs_" + [DateTime]::UtcNow.ToString("yyyyMMddHHmmss"))
New-Item -ItemType Directory -Path $Stage | Out-Null
foreach ($Name in @("error.log", "game.log", "gui.log", "debug.log")) {
    $Path = Join-Path $Logs $Name
    if (Test-Path -LiteralPath $Path) { Copy-Item -LiteralPath $Path -Destination $Stage }
}
$ErrorLog = Join-Path $Logs "error.log"
if (Test-Path -LiteralPath $ErrorLog) {
    Select-String -LiteralPath $ErrorLog -Pattern "vic3_todo" | ForEach-Object { $_.Line } |
        Set-Content -LiteralPath (Join-Path $Stage "vic3_todo_errors.txt") -Encoding UTF8
}
$Meta = Join-Path $UserDataDir "mod\Vic3TODO\.metadata\metadata.json"
if (Test-Path -LiteralPath $Meta) { Copy-Item -LiteralPath $Meta -Destination (Join-Path $Stage "installed_metadata.json") }
$RepoRoot = Split-Path -Parent $PSScriptRoot
$OutDir = Join-Path $RepoRoot "research\runtime"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Zip = Join-Path $OutDir ((Split-Path -Leaf $Stage) + ".zip")
Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $Zip
Remove-Item -Recurse -Force $Stage
Write-Host "Logs collected: $Zip"
