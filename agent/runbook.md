# Runbook: Laptop Health Monitor

## Purpose

This runbook defines the diagnostic and remediation procedures the Laptop Health Monitor agent must follow when investigating system health issues.

The agent must follow:

1. Detect
2. Diagnose
3. Repair
4. Verify
5. Report
6. Escalate if necessary

The procedures in this document are subordinate to guardrails.md.

---

# Universal Troubleshooting Workflow

For every issue:

## Step 1: Collect Evidence

Gather:

* OS version
* CPU usage
* RAM usage
* Disk usage
* Running processes
* Startup programs
* Event logs
* Windows Update status
* Driver status

---

## Step 2: Determine Severity

### Critical

System instability or boot issues.

### High

Major user-facing performance degradation.

### Medium

Noticeable issue with workaround available.

### Low

Optimization opportunity.

---

## Step 3: Attempt Repair

Follow the issue-specific procedure.

---

## Step 4: Verify

Confirm:

* Error no longer exists.
* Performance improved.
* System remains stable.

---

## Step 5: Report

Generate:

Issue:
Root Cause:
Actions Taken:
Result:
Next Recommendation:

---

# Runbook: Slow Laptop Performance

## Symptoms

* System feels sluggish
* Delayed application launches
* Input lag
* General slowdown

## Diagnostics

Check:

* CPU utilization
* Memory utilization
* Disk utilization
* Startup applications
* Background services

## Root Cause Indicators

### CPU > 90%

Likely excessive process activity.

### RAM > 90%

Likely memory pressure.

### Disk > 95%

Storage bottleneck.

---

## Remediation

### CPU Bottleneck

Actions:

* Identify top CPU consumers
* Investigate abnormal processes
* Recommend closure of unnecessary apps

Verification:

CPU returns to normal range.

---

### Memory Bottleneck

Actions:

* Identify memory-heavy applications
* Recommend closing unused apps
* Restart memory-leaking processes

Verification:

Available memory increases.

---

### Storage Bottleneck

Actions:

* Remove temporary files
* Empty recycle bin
* Identify large unused files

Verification:

Free space exceeds 15%.

---

# Runbook: Slow Startup

## Symptoms

* Long boot time
* Long login time

## Diagnostics

Review:

* Startup applications
* Startup impact ratings
* Delayed services

## Remediation

Actions:

* Disable unnecessary startup applications
* Remove broken startup entries
* Optimize startup sequence

Verification:

Boot duration reduced.

---

# Runbook: Driver Problems

## Symptoms

* Device not working
* Missing hardware
* Blue screens
* Audio issues
* Network issues

## Diagnostics

Check:

* Device Manager
* Driver versions
* Driver status

## Remediation

Actions:

* Scan for hardware changes
* Update drivers from trusted source
* Roll back recently installed drivers if necessary

Verification:

Device functions correctly.

---

# Runbook: Windows Update Failure

## Symptoms

* Update installation errors
* Repeated update failures

## Diagnostics

Check:

* Windows Update service
* Update logs
* Error codes

## Remediation

Actions:

* Restart update services
* Clear update cache
* Run Windows Update Troubleshooter

Verification:

Updates install successfully.

---

# Runbook: Corrupted System Files

## Symptoms

* Random crashes
* Missing Windows features
* Unexplained errors

## Diagnostics

Run:

SFC Scan

DISM Health Check

## Remediation

Execute:

sfc /scannow

DISM /Online /Cleanup-Image /RestoreHealth

Verification:

No integrity violations remain.

---

# Runbook: Application Crashes

## Symptoms

* Application unexpectedly closes
* Frequent error dialogs

## Diagnostics

Check:

* Event Viewer
* Application logs
* Recent updates

## Remediation

Actions:

* Repair installation
* Reinstall application
* Update application

Verification:

Application runs normally.

---

# Runbook: High Memory Usage

## Symptoms

* Memory constantly near maximum
* System stuttering

## Diagnostics

Identify:

* Top memory consumers
* Memory leaks
* Excessive browser usage

## Remediation

Actions:

* Restart affected process
* Recommend tab reduction
* Close unused applications

Verification:

Memory utilization decreases.

---

# Runbook: High CPU Usage

## Symptoms

* Fan noise
* System lag
* CPU constantly busy

## Diagnostics

Identify:

* Top CPU-consuming processes

## Remediation

Actions:

* Investigate process
* Restart process if appropriate
* Disable unnecessary startup source

Verification:

CPU returns below 50% during idle.

---

# Runbook: Disk Space Shortage

## Symptoms

* Low disk space warnings
* Slow system performance

## Diagnostics

Check:

* Free storage percentage
* Largest folders
* Temporary files

## Remediation

Actions:

* Remove temp files
* Empty recycle bin
* Clear cache

Verification:

Minimum 15–20% free space available.

---

# Runbook: Service Failure

## Symptoms

* Windows feature not functioning

## Diagnostics

Check:

* Service status
* Startup type
* Event logs

## Remediation

Actions:

* Restart service
* Restore recommended startup type

Verification:

Service remains operational.

---

# Runbook: Network Issues

## Symptoms

* Slow internet
* No connectivity
* Intermittent connection

## Diagnostics

Check:

* Network adapter status
* Driver status
* DNS configuration

## Remediation

Actions:

* Reset adapter
* Renew IP configuration
* Update network drivers

Verification:

Stable connectivity restored.

---

# Runbook: Battery Health

## Symptoms

* Rapid battery drain
* Reduced battery capacity

## Diagnostics

Review:

* Battery health report
* Charge cycles
* Power settings

## Remediation

Actions:

* Recommend power plan optimization
* Reduce unnecessary background activity

Verification:

Improved battery runtime.

---

# Escalation Conditions

Escalate immediately if:

* BSOD occurs repeatedly
* System fails to boot
* Hardware failure suspected
* SMART disk errors detected
* Repair fails twice
* Root cause cannot be determined

Report:

Issue:
Evidence:
Actions Attempted:
Reason For Escalation:

---

# Health Score Calculation

The agent should maintain a health score.

Components:

CPU Health: 20%
Memory Health: 20%
Storage Health: 20%
Driver Health: 15%
Windows Health: 15%
Security Health: 10%

Overall Score:

90–100 = Excellent
75–89 = Good
60–74 = Needs Attention
Below 60 = Critical

---

# Completion Criteria

A ticket is considered resolved only when:

* Root cause identified.
* Repair completed or recommended.
* Verification successful.
* User informed of outcome.
* System stability maintained.
