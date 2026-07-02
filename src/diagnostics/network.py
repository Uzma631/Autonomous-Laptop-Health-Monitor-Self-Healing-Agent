from src.powershell import PowerShellRunner
from typing import Dict, Any, List

class NetworkDiagnostics:
    """Checks network adapters, IP settings, and runs connectivity tests."""

    def __init__(self, ps_runner: PowerShellRunner):
        self.ps_runner = ps_runner

    def check_adapters(self) -> List[Dict[str, Any]]:
        """Returns the status and speed of available network adapters."""
        cmd = "Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, LinkSpeed"
        data, res = self.ps_runner.run_json(cmd)
        
        adapters = []
        if res.success and data:
            raw_adapters = data if isinstance(data, list) else [data]
            for adapter in raw_adapters:
                if not adapter:
                    continue
                adapters.append({
                    "name": adapter.get("Name", "Unknown"),
                    "desc": adapter.get("InterfaceDescription", "Unknown"),
                    "status": adapter.get("Status", "Disconnected"),
                    "speed": adapter.get("LinkSpeed", "N/A")
                })
        return adapters

    def test_connectivity(self, target: str = "8.8.8.8") -> Dict[str, Any]:
        """Tests network connectivity by pinging an external target."""
        # Test-Connection command is built into PowerShell and parses easily
        cmd = f"Test-Connection -ComputerName {target} -Count 2 -Quiet"
        res = self.ps_runner.run(cmd)

        connected = False
        if res.success and res.stdout.strip().lower() == "true":
            connected = True

        return {
            "target": target,
            "connected": connected
        }
