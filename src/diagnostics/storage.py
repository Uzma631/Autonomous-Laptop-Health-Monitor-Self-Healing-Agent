from src.powershell import PowerShellRunner
from typing import Dict, Any, List

class StorageDiagnostics:
    """Queries storage status, free space, and SMART health info from Windows."""

    def __init__(self, ps_runner: PowerShellRunner):
        self.ps_runner = ps_runner

    def check_disk_space(self, drive_letter: str = "C") -> Dict[str, float]:
        """Returns size, free space, and free percent for the specified drive."""
        cmd = f"Get-CimInstance Win32_LogicalDisk -Filter \"DeviceID='{drive_letter}:'\" | Select-Object Size, FreeSpace"
        data, res = self.ps_runner.run_json(cmd)

        metrics = {"size_gb": 0.0, "free_gb": 0.0, "free_percent": 100.0}

        if res.success and data:
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            try:
                size_bytes = float(data.get("Size", 0))
                free_bytes = float(data.get("FreeSpace", 0))
                if size_bytes > 0:
                    free_percent = (free_bytes / size_bytes) * 100.0
                    metrics = {
                        "size_gb": round(size_bytes / (1024**3), 1),
                        "free_gb": round(free_bytes / (1024**3), 1),
                        "free_percent": round(free_percent, 1)
                    }
            except (ValueError, TypeError, KeyError):
                pass
        return metrics

    def check_smart_status(self) -> Dict[str, Any]:
        """Queries physical drives to detect SMART status or failing disks.

        Returns:
            A dict containing overall status ("Healthy", "Warning", "Failing") and details.
        """
        # Get-PhysicalDisk queries hardware health
        cmd = "Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, OperationalStatus, HealthStatus"
        data, res = self.ps_runner.run_json(cmd)

        status_report = {
            "overall_status": "Healthy",
            "failing_drives": []
        }

        if res.success and data:
            # Wrap in list if single object returned
            drives = data if isinstance(data, list) else [data]
            
            for drive in drives:
                if not drive:
                    continue
                health = drive.get("HealthStatus", "Healthy")
                name = drive.get("FriendlyName", "Unknown Disk")
                op_status = drive.get("OperationalStatus", "OK")
                
                # HealthStatus values: Healthy, Warning, Unhealthy
                if health == "Unhealthy" or "Failing" in str(op_status) or "Error" in str(op_status):
                    status_report["overall_status"] = "Failing"
                    status_report["failing_drives"].append({
                        "name": name,
                        "health": health,
                        "status": op_status
                    })
                elif health == "Warning" and status_report["overall_status"] == "Healthy":
                    status_report["overall_status"] = "Warning"

        return status_report
