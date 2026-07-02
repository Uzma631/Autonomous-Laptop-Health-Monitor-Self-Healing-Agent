import subprocess
import json
import os
from typing import Dict, Any, List, Optional, Tuple, Union

class PowerShellResult:
    """Represents the output and execution status of a PowerShell command."""

    def __init__(self, stdout: str, stderr: str, return_code: int):
        self.stdout = stdout.strip()
        self.stderr = stderr.strip()
        self.return_code = return_code

    @property
    def success(self) -> bool:
        """Returns True if the command executed with exit code 0."""
        return self.return_code == 0

    def to_json(self) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """Parses stdout as JSON. Returns None if parsing fails."""
        if not self.stdout:
            return None
        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError:
            return None


class PowerShellRunner:
    """Executes commands and scripts inside the Windows PowerShell environment."""

    def __init__(self, timeout_seconds: int = 120):
        self.timeout_seconds = timeout_seconds

    def run(self, command: str) -> PowerShellResult:
        """Executes a raw PowerShell command string.

        Args:
            command: The PowerShell command or expression to run.
        """
        # Run powershell with flags for scripting safety and speed
        args = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-Command", command
        ]

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                errors="replace"
            )
            return PowerShellResult(result.stdout, result.stderr, result.returncode)
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout if e.stdout else ""
            stderr = f"Command timed out after {self.timeout_seconds} seconds. " + (e.stderr if e.stderr else "")
            return PowerShellResult(stdout, stderr, -1)
        except Exception as e:
            return PowerShellResult("", f"Execution failed: {str(e)}", -1)

    def run_json(self, command: str) -> Tuple[Optional[Union[Dict[str, Any], List[Any]]], PowerShellResult]:
        """Executes a command and forces output to be converted to JSON.

        Args:
            command: The command which should produce output to be converted.
        
        Returns:
            A tuple of (parsed_json, PowerShellResult object).
        """
        # Wrap the command in ConvertTo-Json to make it structured
        # We use -Compress and -Depth 5 to capture nested data structures without truncating
        json_command = f"& {{ {command} }} | ConvertTo-Json -Compress -Depth 5"
        res = self.run(json_command)
        
        if res.success:
            parsed = res.to_json()
            if parsed is not None:
                return parsed, res
            
            # If ConvertTo-Json received nothing or failed to parse, it might return empty or raw string
            # Let's try parsing the original stdout if it is already JSON
            parsed_orig = res.to_json()
            return parsed_orig, res
        
        return None, res

    def is_admin(self) -> bool:
        """Checks if the current process has administrative (elevated) privileges."""
        cmd = "([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)"
        res = self.run(cmd)
        return res.stdout.strip().lower() == "true"
