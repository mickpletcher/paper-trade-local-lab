[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$TaskName = "TradeForge Daily Maintenance",
    [datetime]$DailyAt = "02:00",
    [string]$TradeForgeExecutable = (Get-Command tradeforge -ErrorAction Stop).Source,
    [string]$WorkingDirectory = (Split-Path -Parent $PSScriptRoot),
    [switch]$RunNow
)

$resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path
$resolvedExecutable = (Resolve-Path -LiteralPath $TradeForgeExecutable -ErrorAction Stop).Path
$action = New-ScheduledTaskAction `
    -Execute $resolvedExecutable `
    -Argument "run-maintenance" `
    -WorkingDirectory $resolvedWorkingDirectory
$trigger = New-ScheduledTaskTrigger -Daily -At $DailyAt
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

if ($PSCmdlet.ShouldProcess($TaskName, "Register daily TradeForge maintenance task")) {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Imports OHLCV data, refreshes quotes, verifies a SQLite backup, and writes a maintenance report." `
        -Force | Out-Null

    if ($RunNow) {
        Start-ScheduledTask -TaskName $TaskName
    }

    Get-ScheduledTask -TaskName $TaskName
}
