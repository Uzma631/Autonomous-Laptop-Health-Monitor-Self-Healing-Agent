# Laptop Health Monitor Agent

An autonomous diagnostic and repair agent for Windows laptops, written in Python and PowerShell.

## Overview

The Laptop Health Monitor Agent proactively monitors system health (CPU, Memory, Storage, Drivers, Network, Services, Windows Updates, and Security) and autonomously repairs common issues. It incorporates strict safety guardrails to ensure no destructive actions are taken without user approval.

## Requirements

- Windows 10 or 11
- Python 3.12+
- Administrator privileges (for remediation actions and Scheduled Task setup)

## Installation & Deployment

To deploy the agent to run automatically on a **monthly** schedule, run the provided installation script:

1. Open PowerShell as **Administrator**.
2. Run the deployment script:
   ```powershell
   .\install.ps1
   ```
This will create a Windows Scheduled Task named `LaptopHealthMonitor_Monthly` that executes the agent autonomously.

## Manual Usage

You can also run the agent manually from your terminal:

```powershell
# Run a dry-run diagnostic scan and view the health report
python src/main.py --diagnostic

# Run diagnostics and attempt all authorized repairs
python src/main.py --run-all

# Run a quick storage cleanup (Temp files and Recycle Bin)
python src/main.py --cleanup
```

## Logs

All actions taken by the agent are securely logged in markdown format in `audit_log.md` in the project root directory.
