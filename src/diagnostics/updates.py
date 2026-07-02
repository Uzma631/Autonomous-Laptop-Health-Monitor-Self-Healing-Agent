from src.powershell import PowerShellRunner
from typing import Dict, Any

class UpdateDiagnostics:
    """Checks Windows Update status and reboot requirements using native COM objects."""

    def __init__(self, ps_runner: PowerShellRunner):
        self.ps_runner = ps_runner

    def check_pending_updates(self) -> Dict[str, Any]:
        """Queries the Windows Update Session COM interface for pending software updates."""
        # Querying COM object is native, requiring no external PS modules
        cmd = (
            "$session = New-Object -ComObject Microsoft.Update.Session; "
            "$searcher = $session.CreateUpdateSearcher(); "
            "try { "
            "  $result = $searcher.Search(\"IsInstalled=0 and Type='Software' and IsHidden=0\"); "
            "  $count = $result.Updates.Count; "
            "  $updates = @(); "
            "  for ($i=0; $i -lt $count; $i++) { "
            "    $u = $result.Updates.Item($i); "
            "    $updates += [PSCustomObject]@{ Title = $u.Title; Msi = $u.MsiApplicable }; "
            "  }; "
            "  [PSCustomObject]@{ Count = $count; Updates = $updates } "
            "} catch { "
            "  [PSCustomObject]@{ Count = -1; Error = $_.Exception.Message } "
            "}"
        )
        data, res = self.ps_runner.run_json(cmd)

        report = {
            "pending_count": 0,
            "updates_list": [],
            "error": None
        }

        if res.success and data:
            if isinstance(data, str):
                import json
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    pass
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            try:
                count = data.get("Count", 0)
                if count == -1:
                    report["error"] = data.get("Error", "Unknown COM error")
                else:
                    report["pending_count"] = count
                    raw_updates = data.get("Updates", [])
                    updates = raw_updates if isinstance(raw_updates, list) else [raw_updates]
                    for u in updates:
                        if u:
                            report["updates_list"].append(u.get("Title", "Unnamed Update"))
            except (ValueError, TypeError, KeyError):
                pass
        return report

    def check_pending_reboot(self) -> bool:
        """Checks registry paths to determine if a system reboot is pending due to updates."""
        cmd = (
            "$path1 = 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired'; "
            "$path2 = 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending'; "
            "$path3 = 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager'; "
            "$reboot = $false; "
            "if (Test-Path $path1) { $reboot = $true }; "
            "if (Test-Path $path2) { $reboot = $true }; "
            "if (Get-ItemProperty -Path $path3 -Name 'PendingFileRenameOperations' -ErrorAction SilentlyContinue) { $reboot = $true }; "
            "$reboot"
        )
        res = self.ps_runner.run(cmd)
        return res.success and res.stdout.strip().lower() == "true"
