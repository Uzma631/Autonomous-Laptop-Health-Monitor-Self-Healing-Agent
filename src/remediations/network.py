from src.powershell import PowerShellRunner
from typing import Dict, Any

class NetworkRemediation:
    """Performs network adapter resets, DNS flushes, and IP configuration renewal."""

    def __init__(self, ps_runner: PowerShellRunner):
        self.ps_runner = ps_runner

    def flush_dns(self) -> Dict[str, Any]:
        """Flushes the Windows DNS resolver cache."""
        cmd = "ipconfig /flushdns"
        res = self.ps_runner.run(cmd)
        return {
            "success": res.success,
            "details": res.stdout if res.success else res.stderr
        }

    def renew_ip(self) -> Dict[str, Any]:
        """Releases and renews the IP configuration for all adapters."""
        # Run release and renew in sequence
        release_res = self.ps_runner.run("ipconfig /release")
        renew_res = self.ps_runner.run("ipconfig /renew")
        
        success = release_res.success and renew_res.success
        details = (
            f"Release: {release_res.stdout.strip() if release_res.success else release_res.stderr}\n"
            f"Renew: {renew_res.stdout.strip() if renew_res.success else renew_res.stderr}"
        )
        return {
            "success": success,
            "details": details
        }

    def reset_winsock(self) -> Dict[str, Any]:
        """Performs a Winsock reset (requires reboot to complete fully)."""
        cmd = "netsh winsock reset"
        res = self.ps_runner.run(cmd)
        return {
            "success": res.success,
            "details": res.stdout if res.success else res.stderr
        }
