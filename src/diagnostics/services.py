from src.powershell import PowerShellRunner
from typing import Dict, Any, List

class ServiceDiagnostics:
    """Monitors critical Windows services."""

    def __init__(self, ps_runner: PowerShellRunner, monitored_services: List[str]):
        self.ps_runner = ps_runner
        self.monitored_services = monitored_services

    def check_services(self) -> Dict[str, Any]:
        """Checks the status of all configured monitored services.

        Returns:
            A dict containing service status details, count of stopped services, and lists.
        """
        # Formulate query for specific service names
        names_str = ",".join([f"'{s}'" for s in self.monitored_services])
        cmd = f"Get-Service -Name {names_str} | Select-Object Name, DisplayName, Status, StartType"
        data, res = self.ps_runner.run_json(cmd)

        report = {
            "all_healthy": True,
            "stopped_services": [],
            "running_services": [],
            "details": {}
        }

        if res.success and data:
            services = data if isinstance(data, list) else [data]
            for service in services:
                if not service:
                    continue
                name = service.get("Name", "")
                display = service.get("DisplayName", "")
                status = service.get("Status", "Stopped")
                start_type = service.get("StartType", "Unknown")

                status_str = "Running" if str(status).strip().lower() in ["4", "running"] else "Stopped"
                
                info = {
                    "display_name": display,
                    "status": status_str,
                    "start_type": start_type
                }
                report["details"][name] = info

                if status_str == "Stopped":
                    report["stopped_services"].append(name)
                    report["all_healthy"] = False
                else:
                    report["running_services"].append(name)

        return report
