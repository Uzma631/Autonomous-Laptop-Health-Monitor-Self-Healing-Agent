from src.powershell import PowerShellRunner
from typing import Dict, Any

class ProcessRemediation:
    """Manages system processes and terminates runaway applications."""

    def __init__(self, ps_runner: PowerShellRunner):
        self.ps_runner = ps_runner
        
        # Protected core system processes that must never be terminated
        self.protected_processes = [
            "system", "idle", "csrss", "lsass", "smss", "wininit", 
            "services", "svchost", "winlogon", "spoolsv", "explorer",
            "msmpeng", "nissrv"
        ]

    def terminate_process(self, pid: int) -> Dict[str, Any]:
        """Terminates a process by its Process ID (PID)."""
        # Get process name first to verify it's not protected
        name_cmd = f"(Get-Process -Id {pid}).ProcessName"
        name_res = self.ps_runner.run(name_cmd)
        
        if not name_res.success or not name_res.stdout:
            return {
                "success": False,
                "details": f"Could not identify process with PID {pid}. It may have already exited."
            }

        proc_name = name_res.stdout.strip().lower()
        if proc_name in self.protected_processes:
            return {
                "success": False,
                "details": f"Termination blocked: Process '{proc_name}' (PID {pid}) is a protected system process."
            }

        # Attempt to stop the process
        cmd = f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue"
        res = self.ps_runner.run(cmd)

        # Verification check
        verify_cmd = f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"
        verify_res = self.ps_runner.run(verify_cmd)
        
        # If verify_res fails to find the PID, it was successfully stopped
        success = not verify_res.success
        
        return {
            "success": success,
            "details": f"Terminated process '{proc_name}' (PID {pid})." if success else f"Failed to terminate '{proc_name}': {res.stderr}"
        }
