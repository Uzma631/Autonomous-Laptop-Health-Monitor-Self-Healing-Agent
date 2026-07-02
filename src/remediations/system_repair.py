from src.powershell import PowerShellRunner
from typing import Dict, Any

class SystemRepairRemediation:
    """Executes SFC scannow, DISM component store repairs, and schedules updates."""

    def __init__(self, ps_runner: PowerShellRunner):
        self.ps_runner = ps_runner

    def run_sfc_scan(self) -> Dict[str, Any]:
        """Runs SFC scannow to verify and repair system files."""
        # Create a runner with a high timeout (15 mins) for SFC
        sfc_runner = PowerShellRunner(timeout_seconds=900)
        res = sfc_runner.run("sfc /scannow")
        
        # Parse stdout/stderr to check for typical results
        success = res.success
        details = res.stdout if res.stdout else res.stderr
        
        if "found corrupt files and successfully repaired" in details:
            status = "Repaired"
        elif "did not find any integrity violations" in details:
            status = "No Errors"
        elif "found corrupt files but was unable to fix" in details:
            status = "Failed"
            success = False
        else:
            status = "Executed"

        return {
            "success": success,
            "status": status,
            "details": details
        }

    def run_dism_repair(self) -> Dict[str, Any]:
        """Runs DISM RestoreHealth to clean and repair Windows Component Store."""
        dism_runner = PowerShellRunner(timeout_seconds=1200)
        res = dism_runner.run("DISM /Online /Cleanup-Image /RestoreHealth")
        
        success = res.success
        details = res.stdout if res.stdout else res.stderr

        if "The restore operation completed successfully" in details:
            status = "Success"
        else:
            status = "Executed" if success else "Failed"

        return {
            "success": success,
            "status": status,
            "details": details
        }

    def trigger_update_scan(self) -> Dict[str, Any]:
        """Triggers a background Windows Update scan using UsoClient."""
        # UsoClient doesn't output stdout, it starts asynchronously
        res = self.ps_runner.run("UsoClient StartScan")
        return {
            "success": res.success,
            "details": "Triggered UsoClient update scan." if res.success else res.stderr
        }

    def trigger_update_install(self) -> Dict[str, Any]:
        """Triggers background Windows Update installations using UsoClient."""
        res = self.ps_runner.run("UsoClient StartInstall")
        return {
            "success": res.success,
            "details": "Triggered UsoClient update installation." if res.success else res.stderr
        }
