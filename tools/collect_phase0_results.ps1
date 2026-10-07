[CmdletBinding()]
param(
    [string]$UserDataDir,
    [string]$PythonExecutable = "python",
    [string]$AnswersJson,
    [string]$Notes,
    [string]$GameVersion
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $UserDataDir) {
    $UserDataDir = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Paradox Interactive\Victoria 3"
}
$Checks = @(
    "journal_integration", "unicode_input", "ascii_punctuation_input", "length_200_input", "empty_input", "newline_input",
    "journal_reopen_text", "save_load_text", "full_restart_text", "slot_isolation", "slot_completion",
    "baseline_persistence", "cosmetic_preserves_baseline", "reconfiguration_once", "selector_ui",
    "tracker_target_config_persistence", "relations_target_binding", "building_net_delta", "progress_update",
    "technology_boolean", "dynamic_status", "pinning", "pin_persistence", "error_log_clean", "gui_log_clean",
    "keyboard_open", "keyboard_hud_button", "keyboard_register"
)
$TemporaryAnswers = $null
try {
    if (-not $AnswersJson) {
        $Answers = [ordered]@{}
        foreach ($Check in $Checks) {
            do {
                $Value = (Read-Host "$Check [PASS/FAIL/NOT_TESTED; blank=NOT_TESTED]").Trim().ToUpperInvariant()
                if (-not $Value) { $Value = "NOT_TESTED" }
            } while ($Value -notin @("PASS", "FAIL", "NOT_TESTED"))
            $Answers[$Check] = $Value
        }
        $TemporaryAnswers = [IO.Path]::GetTempFileName()
        $Answers | ConvertTo-Json | Set-Content -LiteralPath $TemporaryAnswers -Encoding UTF8
        $AnswersJson = $TemporaryAnswers
    }
    if (-not $GameVersion) { $GameVersion = Read-Host "Actual game version displayed in-game (blank=NOT_RECORDED)" }
    if (-not $GameVersion) { $GameVersion = "NOT_RECORDED" }
    if (-not $Notes) { $Notes = Read-Host "Notes: country, start date, baseline/current/goal, reproduction steps, failures" }
    $Arguments = @((Join-Path $PSScriptRoot "collect_results.py"), "--answers", $AnswersJson,
        "--log-dir", (Join-Path $UserDataDir "logs"), "--mod-dir", (Join-Path $UserDataDir "mod\Vic3TODOProbe"),
        "--game-version", $GameVersion)
    if ($Notes) { $Arguments += @("--notes", $Notes) }
    & $PythonExecutable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Result collection failed (exit $LASTEXITCODE)." }
} finally {
    if ($TemporaryAnswers -and (Test-Path -LiteralPath $TemporaryAnswers)) { Remove-Item -LiteralPath $TemporaryAnswers }
}
