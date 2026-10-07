param(
  [string]$TaskName = "HomeGymPT-Claude-AutoResume",
  [string]$DailyStart = "12:50"
)

$ErrorActionPreference = "Stop"
$watcher = Join-Path $PSScriptRoot "claude_auto_resume.ps1"
if (-not (Test-Path $watcher)) {
  throw "Watcher not found: $watcher"
}

$time = [datetime]::ParseExact($DailyStart, "HH:mm", $null)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$watcher`""
$trigger = New-ScheduledTaskTrigger -Daily -At $time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Queue the Home Gym PT continuation prompt when Claude usage becomes available." -Force | Out-Null

Write-Host "Installed $TaskName for $DailyStart local time."
Write-Host "The watcher retries every 5 minutes for up to 3 hours and exits after the first successful queue."
