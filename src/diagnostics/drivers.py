from src.powershell import PowerShellRunner
from typing import Dict, Any, List
from datetime import datetime

class DriverDiagnostics:
    """Scans and analyzes system device drivers for errors, missing drivers, age, and conflicts."""

    def __init__(self, ps_runner: PowerShellRunner):
        self.ps_runner = ps_runner
        
        # Generic Microsoft fallback keywords on third-party hardware
        self.oem_keywords = ["nvidia", "intel", "amd", "radeon", "realtek", "atheros", "broadcom", "synaptics", "elan", "mediatek"]

    def check_driver_issues(self) -> Dict[str, Any]:
        """Scans for present hardware devices and maps failed, missing, outdated, or conflicting drivers.

        Returns:
            A detailed report containing categorized driver issues, confidence levels, and remediation steps.
        """
        # 1. Fetch present devices and signed driver information from PowerShell
        cmd = (
            "$devices = Get-PnpDevice | Where-Object { $_.Present -eq $true }; "
            "$drivers = Get-CimInstance Win32_PnPSignedDriver | Select-Object PNPDeviceID, DriverVersion, "
            "  @{Name='DriverDate'; Expression={if ($_.DriverDate) { $_.DriverDate.ToString('yyyy-MM-dd') } else { $null }}}, "
            "  SignerProvider, Manufacturer; "
            "$driverMap = @{}; "
            "foreach ($d in $drivers) { if ($d.PNPDeviceID) { $driverMap[$d.PNPDeviceID] = $d } }; "
            "$result = @(); "
            "foreach ($dev in $devices) { "
            "  $drv = $driverMap[$dev.InstanceId]; "
            "  $drvDate = $null; $drvVersion = $null; $drvProvider = $null; $drvMfg = $null; "
            "  if ($drv) { "
            "    $drvDate = $drv.DriverDate; $drvVersion = $drv.DriverVersion; "
            "    $drvProvider = $drv.SignerProvider; $drvMfg = $drv.Manufacturer; "
            "  }; "
            "  $result += [PSCustomObject]@{ "
            "    InstanceId = $dev.InstanceId; "
            "    FriendlyName = $dev.FriendlyName; "
            "    Class = $dev.Class; "
            "    Status = $dev.Status; "
            "    ConfigManagerErrorCode = $dev.ConfigManagerErrorCode; "
            "    ProblemDescription = $dev.ProblemDescription; "
            "    DriverDate = $drvDate; "
            "    DriverVersion = $drvVersion; "
            "    SignerProvider = $drvProvider; "
            "    Manufacturer = $drvMfg "
            "  } "
            "}; "
            "$result"
        )
        data, res = self.ps_runner.run_json(cmd)

        report = {
            "has_errors": False,
            "failed_devices": [],
            "missing_drivers": [],
            "outdated_drivers": [],
            "conflicting_drivers": [],
            "total_checked": 0
        }

        if not res.success or not data:
            return report

        devices = data if isinstance(data, list) else [data]
        report["total_checked"] = len(devices)

        # 2. Fetch recent Kernel-PnP events (last 48 hours) to find driver load errors/conflicts
        events_cmd = (
            "Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-Kernel-PnP'; "
            "  Level=@(2,3); StartTime=(Get-Date).AddDays(-2)} -ErrorAction SilentlyContinue | "
            "Select-Object Id, Message"
        )
        events_data, events_res = self.ps_runner.run_json(events_cmd)
        recent_events = events_data if isinstance(events_data, list) else ([events_data] if events_data else [])

        # Process each device
        for dev in devices:
            if not dev:
                continue

            inst_id = dev.get("InstanceId", "")
            name = dev.get("FriendlyName", "Unknown Device")
            dev_class = dev.get("Class", "Unknown")
            status = dev.get("Status", "Unknown")
            err_code = dev.get("ConfigManagerErrorCode", 0)
            drv_date = dev.get("DriverDate")
            drv_version = dev.get("DriverVersion")
            provider = dev.get("SignerProvider", "")
            manufacturer = dev.get("Manufacturer", "")

            # Check if there's a recent event log failure matching this device
            has_pnp_event_failure = False
            for ev in recent_events:
                if ev and inst_id in ev.get("Message", ""):
                    has_pnp_event_failure = True
                    break

            # Categorize issues:
            
            # Category A: CONFLICTING DRIVER
            # Code 12: Resource conflict, Code 16: Resource allocation failed
            if err_code in [12, 16]:
                report["has_errors"] = True
                report["conflicting_drivers"].append({
                    "id": inst_id,
                    "name": name,
                    "class": dev_class,
                    "status": status,
                    "error_code": err_code,
                    "confidence": "High",
                    "remediation": [
                        f"Reboot system to allow Windows to reallocate device resources.",
                        f"Uninstall the device using Device Manager or pnputil and let Windows rediscover it."
                    ]
                })

            # Category B: FAILED DRIVER
            # Status not OK and not 0 error code (excluding phantom/known codes like 28 which is missing)
            elif (status != "OK" and err_code != 0 and err_code != 28) or has_pnp_event_failure:
                report["has_errors"] = True
                confidence = "High" if err_code != 0 else "Medium"
                
                # Check for standard error codes
                err_desc = dev.get("ProblemDescription")
                if not err_desc:
                    err_desc = f"Code {err_code}"
                if has_pnp_event_failure:
                    err_desc += " (Driver failed to load in recent event logs)"

                report["failed_devices"].append({
                    "id": inst_id,
                    "name": name,
                    "class": dev_class,
                    "status": status,
                    "error_code": err_code,
                    "error_description": err_desc,
                    "confidence": confidence,
                    "remediation": [
                        f"Run hardware diagnostic scan: pnputil /scan-devices",
                        f"Reinstall or roll back the driver in Device Manager.",
                        f"Check system manufacturer support page for certified updates."
                    ]
                })

            # Category C: MISSING DRIVER
            # Code 28: "The drivers for this device are not installed" or class is Unknown
            elif err_code == 28 or dev_class in ["Unknown", None, ""]:
                report["has_errors"] = True
                report["missing_drivers"].append({
                    "id": inst_id,
                    "name": name,
                    "class": dev_class,
                    "status": status,
                    "confidence": "High",
                    "remediation": [
                        f"Trigger Windows Update Optional Updates check: UsoClient StartScan",
                        f"Manual install: Download the latest driver package from manufacturer portal."
                    ]
                })

            # Category D: OUTDATED DRIVER
            # Check driver date (> 5 years old) or Microsoft generic provider fallback
            else:
                is_outdated = False
                reasons = []

                # Age check: older than 5 years (prior to 2021)
                if drv_date:
                    try:
                        year = int(drv_date.split("-")[0])
                        if year < 2021:
                            is_outdated = True
                            reasons.append(f"Driver date is {drv_date} (older than 5 years)")
                    except (ValueError, IndexError):
                        pass

                # Generic provider fallback check
                # If provider is Microsoft but hardware name contains OEM keywords
                name_lower = name.lower()
                has_oem_keyword = any(k in name_lower for k in self.oem_keywords)
                is_generic_ms = provider and provider.strip().lower() == "microsoft"
                
                if has_oem_keyword and is_generic_ms and "microsoft" not in name_lower:
                    is_outdated = True
                    reasons.append(f"Using generic Microsoft driver instead of manufacturer driver ({manufacturer})")

                if is_outdated:
                    report["outdated_drivers"].append({
                        "id": inst_id,
                        "name": name,
                        "class": dev_class,
                        "version": drv_version,
                        "date": drv_date,
                        "provider": provider,
                        "reasons": reasons,
                        "confidence": "Medium",
                        "remediation": [
                            f"Run 'winget upgrade' to check for third-party application driver bundles.",
                            f"Visit OEM manufacturer portal ({manufacturer if manufacturer else 'System Vendor'}) to obtain the latest certified driver."
                        ]
                    })

        return report
