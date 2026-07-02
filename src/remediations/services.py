from src.powershell import PowerShellRunner
from typing import Dict, Any

class ServiceRecoveryRemediation:
    """Restarts stopped critical services."""

    def __init__(self, ps_runner: PowerShellRunner):
        self.ps_runner = ps_runner

    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restarts a stopped or failing service."""
        cmd = f"Restart-Service -Name '{service_name}' -Force -ErrorAction SilentlyContinue"
        res = self.ps_runner.run(cmd)

        # Verify service state
        verify_cmd = f"(Get-Service -Name '{service_name}').Status"
        verify_res = self.ps_runner.run(verify_cmd)
        
        status = verify_res.stdout.strip() if verify_res.success else "Unknown"
        success = res.success and (status.lower() in ["4", "running"])

        return {
            "success": success,
            "status": status,
            "details": res.stderr if not success else f"Service '{service_name}' restarted successfully."
        }

    def set_startup_type(self, service_name: str, startup_type: str = "Automatic") -> Dict[str, Any]:
        """Configures service startup type (e.g. Automatic, Manual, Disabled)."""
        cmd = f"Set-Service -Name '{service_name}' -StartupType {startup_type} -ErrorAction SilentlyContinue"
        res = self.ps_runner.run(cmd)
        return {
            "success": res.success,
            "details": res.stdout if res.success else res.stderr
        }
