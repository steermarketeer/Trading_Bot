# Fix ETH Shadow HTF Task Scheduler reliability.
# Right-click PowerShell -> Run as administrator, then:
#   Set-Location "D:\Trading Bot"
#   .\fix_shadow_task.ps1

$ErrorActionPreference = "Stop"
$name = "ETH Shadow HTF"

$task = Get-ScheduledTask -TaskName $name
$settings = $task.Settings
$settings.StartWhenAvailable = $true
$settings.WakeToRun = $true
$settings.DisallowStartIfOnBatteries = $false
$settings.StopIfGoingOnBatteries = $false
$settings.ExecutionTimeLimit = "PT2H"
$settings.MultipleInstances = "IgnoreNew"

Set-ScheduledTask -TaskName $name -Settings $settings | Out-Null

$t = Get-ScheduledTask -TaskName $name
$info = Get-ScheduledTaskInfo -TaskName $name
Write-Host "Updated $name"
Write-Host "  StartWhenAvailable = $($t.Settings.StartWhenAvailable)"
Write-Host "  WakeToRun          = $($t.Settings.WakeToRun)"
Write-Host "  DisallowOnBattery  = $($t.Settings.DisallowStartIfOnBatteries)"
Write-Host "  NextRun            = $($info.NextRunTime)"
Write-Host ""
Write-Host "If last result was 0x800710E0, also re-enter the task password:"
Write-Host "  Task Scheduler -> ETH Shadow HTF -> Properties -> Change User or Group / update password"
Write-Host "  Keep: Run whether user is logged on or not"
Write-Host ""
Write-Host "Test:"
Write-Host "  Start-ScheduledTask -TaskName '$name'"
