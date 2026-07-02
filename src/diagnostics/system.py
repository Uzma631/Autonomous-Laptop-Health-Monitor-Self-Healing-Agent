from src.powershell import PowerShellRunner
from typing import Dict, Any, Optional

class SystemDiagnostics:
    """Queries CPU, memory, OS, and battery details from Windows."""

    def __init__(self, ps_runner: PowerShellRunner):
        self.ps_runner = ps_runner

    def check_cpu_usage(self) -> float:
        """Returns the current overall CPU usage percentage."""
        # Use CIM to fetch processor time (more reliable than Get-Counter in non-English locales)
        cmd = "Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter \"Name='_Total'\" | Select-Object -ExpandProperty PercentProcessorTime"
        res = self.ps_runner.run(cmd)
        if res.success and res.stdout:
            try:
                return float(res.stdout)
            except ValueError:
                pass
        return 0.0

    def check_memory_usage(self) -> Dict[str, float]:
        """Returns physical memory statistics: total_kb, free_kb, used_percent."""
        cmd = "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory"
        data, res = self.ps_runner.run_json(cmd)
        
        # Default fallback
        metrics = {"total_kb": 1.0, "free_kb": 1.0, "used_percent": 0.0}
        
        if res.success and data:
            try:
                # If there are multiple OS instances (rare), take the first
                if isinstance(data, list):
                    data = data[0]
                total = float(data.get("TotalVisibleMemorySize", 1.0))
                free = float(data.get("FreePhysicalMemory", 1.0))
                used_percent = ((total - free) / total) * 100.0
                
                metrics = {
                    "total_kb": total,
                    "free_kb": free,
                    "used_percent": round(used_percent, 1)
                }
            except (ValueError, KeyError, TypeError):
                pass
        return metrics

    def check_battery_health(self) -> Dict[str, Any]:
        """Returns battery information such as EstimatedChargeRemaining and status."""
        cmd = "Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus, DesignCapacity, FullChargeCapacity"
        data, res = self.ps_runner.run_json(cmd)

        battery_info = {
            "charge_remaining": 100,
            "status": "Unknown",
            "wear_percent": 0.0,
            "present": False
        }

        if res.success and data:
            if isinstance(data, list):
                if len(data) > 0:
                    data = data[0]
                else:
                    return battery_info # No battery (e.g. Desktop PC)
            
            try:
                charge = data.get("EstimatedChargeRemaining", 100)
                status_code = data.get("BatteryStatus", 2)
                design = float(data.get("DesignCapacity", 0))
                full = float(data.get("FullChargeCapacity", 0))

                # Map battery status codes (Win32_Battery BatteryStatus)
                status_map = {
                    1: "Discharging",
                    2: "AC Power",
                    3: "Fully Charged",
                    4: "Low",
                    5: "Critical",
                    6: "Charging",
                    7: "Charging and High",
                    8: "Charging and Low",
                    9: "Charging and Critical",
                    10: "Undefined",
                    11: "Partially Charged"
                }

                status = status_map.get(status_code, "Unknown")
                wear = 0.0
                if design > 0 and full > 0:
                    wear = max(0.0, ((design - full) / design) * 100.0)

                battery_info = {
                    "charge_remaining": charge,
                    "status": status,
                    "wear_percent": round(wear, 1),
                    "present": True
                }
            except (ValueError, TypeError, KeyError):
                pass

        return battery_info
