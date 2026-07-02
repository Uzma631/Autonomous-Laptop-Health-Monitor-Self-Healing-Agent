import os
from datetime import datetime

class AuditLogger:
    """Logs system checks, detected issues, repairs, and verification results in markdown format."""

    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path

    def log_action(
        self,
        issue: str,
        action: str,
        risk: str,
        result: str,
        verification: str,
        timestamp: datetime = None
    ) -> None:
        """Appends a structured log entry to the audit log file.

        Args:
            issue: Description of the issue detected.
            action: Repair action executed or proposed.
            risk: Risk level (Low, Medium, High, Critical).
            result: Outcome of the action (e.g. Success, Failed, Declined, Aborted).
            verification: Details of the verification performed.
            timestamp: Optional datetime object. Defaults to current system time.
        """
        if timestamp is None:
            timestamp = datetime.now()

        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        log_entry = (
            f"---\n\n"
            f"Timestamp:\n{formatted_time}\n\n"
            f"Issue:\n{issue}\n\n"
            f"Action:\n{action}\n\n"
            f"Risk:\n{risk}\n\n"
            f"Result:\n{result}\n\n"
            f"Verification:\n{verification}\n\n"
        )

        try:
            # Ensure parent directories of log file exist
            parent_dir = os.path.dirname(self.log_file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except OSError as e:
            # Output warning if logging fails but do not crash the agent
            print(f"[Warning] Failed to write to audit log: {e}")

    def log_info(self, message: str) -> None:
        """Outputs an informative message to the console."""
        print(f"[*] {message}")

    def log_warning(self, message: str) -> None:
        """Outputs a warning message to the console."""
        print(f"[!] Warning: {message}")

    def log_error(self, message: str) -> None:
        """Outputs an error message to the console."""
        print(f"[X] Error: {message}")

    def log_success(self, message: str) -> None:
        """Outputs a success message to the console."""
        print(f"[+] {message}")
