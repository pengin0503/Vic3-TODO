[CmdletBinding()]
param(
    [string]$GameDir,
    [string]$SourceArchive,
    [string]$UserDataDir,
    [string]$PythonExecutable = "python"
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (Get-Process -Name victoria3 -ErrorAction SilentlyContinue) {
    throw "Exit Victoria 3 completely before installing or replacing the probe."
}
if (-not $GameDir) {
    $Candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} "Steam\steamapps\common\Victoria 3"),
        (Join-Path $env:ProgramFiles "Steam\steamapps\common\Victoria 3")
    )
    $GameDir = $Candidates | Where-Object { Test-Path -LiteralPath (Join-Path $_ "binaries\victoria3.exe") } | Select-Object -First 1
    if (-not $GameDir) { throw "Supply -GameDir with the full Victoria 3 installation root." }
}
if (-not $UserDataDir) {
    $UserDataDir = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Paradox Interactive\Victoria 3"
}
$GameDir = (Resolve-Path -LiteralPath $GameDir).Path
$Arguments = @((Join-Path $PSScriptRoot "install_probe.py"), "--game-dir", $GameDir, "--user-data-dir", $UserDataDir)
if ($SourceArchive) { $Arguments += @("--source-archive", (Resolve-Path -LiteralPath $SourceArchive).Path) }
& $PythonExecutable @Arguments
if ($LASTEXITCODE -ne 0) { throw "Probe audit/build/install failed (exit $LASTEXITCODE). No runtime PASS recorded." }
Write-Host "Next: enable the probe in a launcher playset and follow docs/runtime-verification-phase0.md."
