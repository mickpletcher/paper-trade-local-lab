[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$taskName = "TradeForge Canary $([guid]::NewGuid())"
$marker = Join-Path $env:RUNNER_TEMP "tradeforge-scheduled-task-canary.txt"

try {
    $command = "Set-Content -LiteralPath '$($marker.Replace("'", "''"))' -Value 'ok' -Encoding utf8"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -Command `"$command`""
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5)
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    $deadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path -LiteralPath $marker) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 250
    }
    if (-not (Test-Path -LiteralPath $marker)) {
        throw "The disposable scheduled task did not create its verification marker."
    }
    if ((Get-Content -Raw -LiteralPath $marker).Trim() -ne "ok") {
        throw "The disposable scheduled task marker was invalid."
    }
}
finally {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue
}

Write-Output "Real Windows Task Scheduler canary passed."
