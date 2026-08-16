[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$installer = Join-Path $PSScriptRoot "Install-TradeForgeScheduledTask.ps1"
$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile($installer, [ref]$tokens, [ref]$parseErrors) | Out-Null
if ($parseErrors.Count -gt 0) {
    throw "Scheduled task installer has PowerShell parse errors: $($parseErrors -join '; ')"
}

$global:TradeForgeScheduledTaskTestCalls = [ordered]@{
    Action = $null
    Trigger = $null
    Settings = $null
    Registered = $null
    Started = $null
    Queried = $null
}

function New-ScheduledTaskAction {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string]$Execute,
        [Parameter(Mandatory)] [string]$Argument,
        [Parameter(Mandatory)] [string]$WorkingDirectory
    )

    $global:TradeForgeScheduledTaskTestCalls.Action = [pscustomobject]@{
        Execute = $Execute
        Argument = $Argument
        WorkingDirectory = $WorkingDirectory
    }
    return $global:TradeForgeScheduledTaskTestCalls.Action
}

function New-ScheduledTaskTrigger {
    [CmdletBinding()]
    param(
        [switch]$Daily,
        [Parameter(Mandatory)] [datetime]$At
    )

    $global:TradeForgeScheduledTaskTestCalls.Trigger = [pscustomobject]@{ Daily = [bool]$Daily; At = $At }
    return $global:TradeForgeScheduledTaskTestCalls.Trigger
}

function New-ScheduledTaskSettingsSet {
    [CmdletBinding()]
    param(
        [switch]$StartWhenAvailable,
        [Parameter(Mandatory)] [int]$RestartCount,
        [Parameter(Mandatory)] [timespan]$RestartInterval,
        [Parameter(Mandatory)] [timespan]$ExecutionTimeLimit
    )

    $global:TradeForgeScheduledTaskTestCalls.Settings = [pscustomobject]@{
        StartWhenAvailable = [bool]$StartWhenAvailable
        RestartCount = $RestartCount
        RestartInterval = $RestartInterval
        ExecutionTimeLimit = $ExecutionTimeLimit
    }
    return $global:TradeForgeScheduledTaskTestCalls.Settings
}

function Register-ScheduledTask {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string]$TaskName,
        [Parameter(Mandatory)] [object]$Action,
        [Parameter(Mandatory)] [object]$Trigger,
        [Parameter(Mandatory)] [object]$Settings,
        [Parameter(Mandatory)] [string]$Description,
        [switch]$Force
    )

    $global:TradeForgeScheduledTaskTestCalls.Registered = [pscustomobject]@{
        TaskName = $TaskName
        Action = $Action
        Trigger = $Trigger
        Settings = $Settings
        Description = $Description
        Force = [bool]$Force
    }
}

function Start-ScheduledTask {
    [CmdletBinding()]
    param([Parameter(Mandatory)] [string]$TaskName)

    $global:TradeForgeScheduledTaskTestCalls.Started = $TaskName
}

function Get-ScheduledTask {
    [CmdletBinding()]
    param([Parameter(Mandatory)] [string]$TaskName)

    $global:TradeForgeScheduledTaskTestCalls.Queried = $TaskName
    return [pscustomobject]@{ TaskName = $TaskName; State = "Ready" }
}

function Assert-Equal {
    param([object]$Actual, [object]$Expected, [string]$Message)

    if ($Actual -ne $Expected) {
        throw "$Message Expected '$Expected', got '$Actual'."
    }
}

$taskName = "TradeForge CI Validation"
$dailyAt = [datetime]"02:30"
$executable = (Get-Command pwsh -ErrorAction Stop).Source
$workingDirectory = Split-Path -Parent $PSScriptRoot
$result = & $installer `
    -TaskName $taskName `
    -DailyAt $dailyAt `
    -TradeForgeExecutable $executable `
    -WorkingDirectory $workingDirectory `
    -RunNow `
    -Confirm:$false

Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Action.Execute (Resolve-Path -LiteralPath $executable).Path "Executable mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Action.Argument "run-maintenance" "CLI argument mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Action.WorkingDirectory (Resolve-Path -LiteralPath $workingDirectory).Path "Working directory mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Trigger.Daily $true "Daily trigger mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Trigger.At.TimeOfDay $dailyAt.TimeOfDay "Trigger time mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Settings.StartWhenAvailable $true "StartWhenAvailable mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Settings.RestartCount 3 "Restart count mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Settings.RestartInterval (New-TimeSpan -Minutes 5) "Restart interval mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Settings.ExecutionTimeLimit (New-TimeSpan -Hours 1) "Execution time limit mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Registered.TaskName $taskName "Registered task mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Registered.Force $true "Force flag mismatch."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Started $taskName "RunNow did not start the task."
Assert-Equal $global:TradeForgeScheduledTaskTestCalls.Queried $taskName "Registered task was not queried."
Assert-Equal $result.TaskName $taskName "Returned task mismatch."

$global:TradeForgeScheduledTaskTestCalls.Registered = $null
$global:TradeForgeScheduledTaskTestCalls.Started = $null
$global:TradeForgeScheduledTaskTestCalls.Queried = $null
$null = & $installer `
    -TaskName $taskName `
    -DailyAt $dailyAt `
    -TradeForgeExecutable $executable `
    -WorkingDirectory $workingDirectory `
    -RunNow `
    -WhatIf

if (
    $null -ne $global:TradeForgeScheduledTaskTestCalls.Registered -or
    $null -ne $global:TradeForgeScheduledTaskTestCalls.Started -or
    $null -ne $global:TradeForgeScheduledTaskTestCalls.Queried
) {
    throw "WhatIf performed a scheduled task mutation."
}

Remove-Variable -Name TradeForgeScheduledTaskTestCalls -Scope Global
Write-Output "Scheduled task installer validation passed."
