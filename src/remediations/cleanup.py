from src.powershell import PowerShellRunner
from typing import Dict, Any, List

class StorageCleanupRemediation:
    """Performs cleanup of temp files, caches, and empties the Recycle Bin."""

    def __init__(self, ps_runner: PowerShellRunner, extra_cleanup_targets: List[str]):
        self.ps_runner = ps_runner
        self.extra_cleanup_targets = extra_cleanup_targets

    def empty_recycle_bin(self) -> Dict[str, Any]:
        """Empties the Windows Recycle Bin."""
        cmd = "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
        res = self.ps_runner.run(cmd)
        
        # Clear-RecycleBin returns nothing on success
        return {
            "success": res.success,
            "details": res.stdout if res.stdout else (res.stderr if res.stderr else "Recycle Bin cleared.")
        }

    def clean_temp_directories(self) -> Dict[str, Any]:
        """Deletes files and subdirectories from Windows Temp folders."""
        # PowerShell script to clean Temp paths safely (skipping files in use)
        cmd = (
            "$paths = @('$env:TEMP', 'C:\\Windows\\Temp'); "
            "foreach ($path in $paths) { "
            "  $resolved = Get-Item -Path $path -ErrorAction SilentlyContinue; "
            "  if ($resolved) { "
            "    Get-ChildItem -Path $resolved.FullName -Force -ErrorAction SilentlyContinue | "
            "    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; "
            "  } "
            "}; "
            "Write-Output 'Temp files cleared.'"
        )
        res = self.ps_runner.run(cmd)

        return {
            "success": res.success,
            "details": res.stdout if res.success else res.stderr
        }
