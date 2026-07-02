# Tools: Laptop Health Monitor

## Purpose

This document defines the tools available to the Laptop Health Monitor agent and the approved procedures for using them.

The agent must:

1. Use the least invasive tool first.
2. Gather evidence before remediation.
3. Follow guardrails.md.
4. Verify results after execution.

---

# Tool Categories

## Read-Only Tools

Safe tools used for diagnostics.

### Priority

Use read-only tools before making changes.

Examples:

* Process inspection
* Event log analysis
* Driver inspection
* Storage inspection
* Update inspection

---

## Remediation Tools

Tools that modify system state.

Examples:

* Service restart
* Driver update
* Windows repair
* Cleanup actions

Require adherence to risk policies.

---

# PowerShell Tool

## Purpose

Primary diagnostic and remediation interface.

---

## System Information

### OS Information

Get-ComputerInfo

Use For:

* Windows version
* Build number
* System details

Risk:
Low

---

### Hardware Information

Get-CimInstance Win32_ComputerSystem

Get-CimInstance Win32_Processor

Get-CimInstance Win32_PhysicalMemory

Use For:

* CPU
* RAM
* Device identification

Risk:
Low

---

# Process Analysis

## Top CPU Consumers

Get-Process | Sort CPU -Descending | Select -First 20

Purpose:

Identify excessive CPU usage.

Risk:
Low

---

## Top Memory Consumers

Get-Process | Sort WS -Descending | Select -First 20

Purpose:

Identify memory bottlenecks.

Risk:
Low

---

## Process Termination

Stop-Process -Id <PID>

Allowed:

Only after approval.

Risk:
Medium

---

# Service Management

## List Services

Get-Service

Risk:
Low

---

## Check Failed Services

Get-Service | Where Status -ne Running

Risk:
Low

---

## Restart Service

Restart-Service -Name <Service>

Risk:
Low

Verification Required:
Yes

---

# Startup Analysis

## Startup Applications

Get-CimInstance Win32_StartupCommand

Purpose:

Detect startup delays.

Risk:
Low

---

## Disable Startup Item

Requires approval.

Risk:
Medium

---

# Event Log Analysis

## Recent Errors

Get-WinEvent -LogName System -MaxEvents 200

Get-WinEvent -LogName Application -MaxEvents 200

Purpose:

Root cause investigation.

Risk:
Low

---

## Critical Errors

Get-WinEvent -FilterHashtable @{
Level=1
}

Purpose:

Find critical failures.

Risk:
Low

---

# Driver Management

## Device Inventory

Get-PnpDevice

Purpose:

Driver diagnostics.

Risk:
Low

---

## Driver Information

Get-CimInstance Win32_PnPSignedDriver

Purpose:

Version comparison.

Risk:
Low

---

## Driver Update

Preferred Sources:

* Windows Update
* OEM Vendor
* Device Manufacturer

Requires Approval:
Yes

Risk:
Medium

---

# Windows Update Tools

## Update Status

Get-WindowsUpdate

or

UsoClient ScanInstallWait

Purpose:

Check update health.

Risk:
Low

---

## Trigger Update Scan

UsoClient StartScan

Risk:
Low

---

## Trigger Update Install

UsoClient StartInstall

Requires Approval:
Recommended

Risk:
Medium

---

# Windows Repair Tools

## System File Checker

sfc /scannow

Purpose:

Repair corrupted system files.

Risk:
Low

Verification:
Required

---

## DISM Repair

DISM /Online /Cleanup-Image /RestoreHealth

Purpose:

Repair Windows component store.

Risk:
Low

Verification:
Required

---

# Storage Diagnostics

## Disk Space

Get-PSDrive

Risk:
Low

---

## Largest Directories

Get-ChildItem

Purpose:

Locate storage consumers.

Risk:
Low

---

## Temporary File Cleanup

cleanmgr

or

Remove-Item Temp Files

Allowed:
Automatic

Risk:
Low

---

# Disk Health

## SMART Information

Get-PhysicalDisk

Get-StorageReliabilityCounter

Purpose:

Detect failing drives.

Risk:
Low

---

## Disk Check

chkdsk

Purpose:

File system repair.

Requires Approval:
Yes

Risk:
Medium

---

# Network Diagnostics

## Network Adapter Status

Get-NetAdapter

Risk:
Low

---

## IP Configuration

ipconfig /all

Risk:
Low

---

## Connectivity Test

Test-NetConnection

ping

Risk:
Low

---

## DNS Flush

ipconfig /flushdns

Risk:
Low

---

## Network Reset

netsh winsock reset

Requires Approval:
Yes

Risk:
Medium

---

# Battery Diagnostics

## Battery Report

powercfg /batteryreport

Purpose:

Battery health assessment.

Risk:
Low

---

## Energy Report

powercfg /energy

Purpose:

Power optimization.

Risk:
Low

---

# Security Diagnostics

## Defender Status

Get-MpComputerStatus

Purpose:

Verify protection.

Risk:
Low

---

## Threat History

Get-MpThreat

Purpose:

Review threats.

Risk:
Low

---

# Winget Package Management

## Installed Applications

winget list

Risk:
Low

---

## Upgrade Applications

winget upgrade

Requires Approval:
Recommended

Risk:
Medium

---

## Upgrade All

winget upgrade --all

Requires Approval:
Yes

Risk:
Medium

---

# Registry Tools

## Registry Read

Get-ItemProperty

Allowed:
Yes

Risk:
Low

---

## Registry Write

Set-ItemProperty

Approval Required:
Always

Risk:
High

---

# Health Score Data Sources

## CPU Health

Source:

Get-Counter

Thresholds:

<40% Excellent

40-70% Good

70-90% Warning

> 90% Critical

---

## Memory Health

Source:

Win32_OperatingSystem

Thresholds:

<70% Excellent

70-85% Good

85-95% Warning

> 95% Critical

---

## Storage Health

Source:

Get-PSDrive

Thresholds:

> 20% Free Excellent

10-20% Warning

<10% Critical

---

# Approved Repair Workflow

When a problem is detected:

Step 1:
Collect evidence.

Step 2:
Determine severity.

Step 3:
Choose least invasive tool.

Step 4:
Execute repair.

Step 5:
Verify repair.

Step 6:
Log results.

Step 7:
Update health score.

---

# Emergency Stop Conditions

Immediately stop automation if:

* BSOD detected
* SMART failure detected
* Repeated repair failure
* Disk corruption suspected
* System instability increases
* User cancels operation

Escalate to user immediately.

---

# Tool Usage Priority

1. Read diagnostics
2. Event logs
3. Service recovery
4. Cleanup actions
5. Windows repair
6. Driver actions
7. Registry actions

Always choose the lowest-risk option capable of resolving the issue.
