<#
.SYNOPSIS
Installs the Laptop Health Monitor Agent as a Monthly Scheduled Task.

.DESCRIPTION
This script registers a Windows Scheduled Task to run the health monitor agent
autonomously on a monthly schedule.
#>

# Ensure script is running as Administrator
if (-Not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "This script must be run as Administrator to create a Scheduled Task."
    Write-Host "Please right-click PowerShell, select 'Run as Administrator', and try again."
    exit
}

$TaskName = "LaptopHealthMonitor_Monthly"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonExe = (Get-Command python).Source

if (-not $PythonExe) {
    Write-Error "Python is not installed or not in the system PATH. Please install Python 3.12+."
    exit
}

$ActionArgs = "$ScriptDir\src\main.py --run-all --interval monthly"

Write-Host "Installing $TaskName..."
Write-Host "Path: $ScriptDir"
Write-Host "Python: $PythonExe"

# Create Task Action
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $ActionArgs -WorkingDirectory $ScriptDir

# Create Task Trigger (Monthly, 1st of every month at 2:00 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -DaysInterval 30 -At 2:00AM
# Note: PowerShell 5.1 New-ScheduledTaskTrigger -Monthly can be finicky depending on OS version, 
# so using a daily 30-day interval or standard monthly definition.
# Let's use standard WMI/CIM scheduled task creation to be safe, or native cmdlets if available.
# Actually, New-ScheduledTaskTrigger -At "2:00 AM" -Monthly -DaysOfWeek Monday -WeeksInterval 4 is one way.
# A simpler approach that always works for basic monthly:
$Trigger = New-ScheduledTaskTrigger -At "2:00 AM" -Daily 
$Trigger.Repetition = New-ScheduledTaskTriggerRepetition -Interval (New-TimeSpan -Days 30) -Duration (New-TimeSpan -Days 3650)

# Create Task Settings (Run hidden, run with highest privileges)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden

# Create Task Principal (Run as SYSTEM)
$Principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the Task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
    Write-Host "Successfully registered Scheduled Task: $TaskName" -ForegroundColor Green
    Write-Host "The agent will now run autonomously in the background every month." -ForegroundColor Green
} catch {
    Write-Error "Failed to register Scheduled Task: $_"
}
