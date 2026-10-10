[CmdletBinding()]
param(
    [string]$GameDir,
    [string]$UserDataDir,
    [string]$PythonExecutable = "python"
)
$ErrorActionPreference = "Stop"
if (Get-Process -Name victoria3 -ErrorAction SilentlyContinue) {
    throw "Exit Victoria 3 completely before installing the mod."
}
if (-not $UserDataDir) {
    $UserDataDir = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Paradox Interactive\Victoria 3"
}
$Arguments = @((Join-Path $PSScriptRoot "install_mod.py"), "--user-data-dir", $UserDataDir)
if ($GameDir) { $Arguments += @("--game-dir", (Resolve-Path -LiteralPath $GameDir).Path) }
& $PythonExecutable @Arguments
if ($LASTEXITCODE -ne 0) { throw "Install failed (exit $LASTEXITCODE)." }
