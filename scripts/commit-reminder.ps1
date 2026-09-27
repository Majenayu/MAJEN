<#
  Daily commit reminder. It NEVER commits or pushes anything.
  If you have not committed to this repo today, it shows a popup nudging you to
  commit real work. Kiro University disqualifies entries with commits after
  submission, so set $StopAfter to your submission date.

  Register once (runs daily at 20:00):
    powershell -ExecutionPolicy Bypass -File scripts\commit-reminder.ps1 -Register
  Remove:
    Unregister-ScheduledTask -TaskName StudyStreakCommitReminder -Confirm:$false
#>
param(
  [switch]$Register,
  [string]$StopAfter = '2026-10-05'
)

$repo = Split-Path -Parent $PSScriptRoot

if ($Register) {
  $action  = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`""
  $trigger = New-ScheduledTaskTrigger -Daily -At '20:00'
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
  Register-ScheduledTask -TaskName 'StudyStreakCommitReminder' -Action $action `
    -Trigger $trigger -Settings $settings -Force | Out-Null
  Write-Host 'Registered daily reminder at 20:00 (StudyStreakCommitReminder).'
  exit 0
}

if ((Get-Date).Date -gt [datetime]$StopAfter) { exit 0 }

$today = (Get-Date).ToString('yyyy-MM-dd')
$commits = git -C "$repo" log --since="$today 00:00" --oneline 2>$null
if ($commits) { exit 0 }

$shell = New-Object -ComObject WScript.Shell
$null = $shell.Popup(
  "No commit in MAJEN today.`n`nBuild something small and real, then commit and push it.",
  0, 'StudyStreak reminder', 64)
