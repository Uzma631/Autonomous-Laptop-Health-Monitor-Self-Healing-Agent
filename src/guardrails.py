import re
from typing import Dict, Any, List, Optional, Tuple, Callable
from src.config import StateManager

class EmergencyStopException(Exception):
    """Raised when an emergency stop condition is triggered and execution must halt immediately."""
    pass

class GuardrailsManager:
    """Enforces safety rules, checks command risk levels, prompts for user approvals, and checks for emergency stops."""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        
        # Risk classifications
        self.risk_levels = {
            "LOW": "Low Risk",
            "MEDIUM": "Medium Risk",
            "HIGH": "High Risk",
            "CRITICAL": "Critical Risk"
        }

        # Patterns that indicate forbidden actions
        self.forbidden_patterns = [
            # User Data deletions
            r"remove-item\s+.*\\(documents|downloads|desktop|pictures|videos|source|repos)",
            r"del\s+.*\\(documents|downloads|desktop|pictures|videos|source|repos)",
            # Security disabling
            r"set-mppreference\s+-disablerealtimemonitoring\s+\$true",
            r"set-netfirewallprofile\s+.*-enabled\s+false",
            r"disable-netfirewallrule",
            # System Integrity / BIOS / Bootloader
            r"bootsect",
            r"bcdedit",
            r"firmware",
            r"flash-bios",
            # Disk formatting / Partition changes
            r"format-volume",
            r"clear-disk",
            r"remove-partition"
        ]

    def check_for_forbidden_actions(self, command: str) -> Tuple[bool, Optional[str]]:
        """Scans a proposed command string for forbidden actions.

        Returns:
            A tuple of (is_forbidden, reason_string).
        """
        cmd_lower = command.lower().strip()
        for pattern in self.forbidden_patterns:
            if re.search(pattern, cmd_lower):
                return True, f"Command matches forbidden pattern: '{pattern}'"
        return False, None

    def assess_risk(self, command_type: str) -> str:
        """Determines the risk classification of a command type or category.

        Categories can be: 'temp_cleanup', 'service_restart', 'sfc_scan', 'dism_repair',
        'driver_update', 'driver_rollback', 'startup_disable', 'uninstall_software',
        'process_kill', 'chkdsk_repair', 'registry_write', 'bios_update', etc.
        """
        cmd_type = command_type.upper()
        
        low_risk = ["TEMP_CLEANUP", "CACHE_CLEANUP", "SERVICE_RESTART", "SFC_SCAN", "DISM_REPAIR", "RECYCLE_BIN_CLEANUP", "UPDATE_CHECK", "DIAGNOSTICS"]
        medium_risk = ["DRIVER_INSTALL", "DRIVER_UPDATE", "DRIVER_ROLLBACK", "STARTUP_DISABLE", "UNINSTALL_SOFTWARE", "PROCESS_KILL", "CHKDSK_REPAIR", "NETWORK_RESET"]
        high_risk = ["REGISTRY_WRITE", "DRIVER_REPLACEMENT", "SYSTEM_RESTORE", "PARTITION_CHANGE", "SERVICE_STARTUP_CHANGE"]
        critical_risk = ["BIOS_UPDATE", "FIRMWARE_FLASH", "DISK_FORMAT", "OS_RESET", "FACTORY_RESET", "BOOTLOADER_MODIFY", "ENCRYPTION_CHANGE"]

        if cmd_type in low_risk:
            return "LOW"
        elif cmd_type in medium_risk:
            return "MEDIUM"
        elif cmd_type in high_risk:
            return "HIGH"
        elif cmd_type in critical_risk:
            return "CRITICAL"
        else:
            # Default to High if unrecognized command type for safety
            return "HIGH"

    def request_approval(self, issue: str, proposed_fix: str, expected_benefit: str, risk_level: str) -> bool:
        """Prompts the user for approval before performing Medium or High-risk actions.

        Args:
            issue: The issue being addressed.
            proposed_fix: The proposed fix/action.
            expected_benefit: The expected outcome/benefit.
            risk_level: The evaluated risk level (e.g. 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL').
        """
        if risk_level == "LOW":
            # Low risk can run automatically
            return True

        if risk_level == "CRITICAL":
            print(f"\n[X] BLOCKED: Action is classified as CRITICAL risk and cannot be performed autonomously.")
            print(f"Issue: {issue}")
            print(f"Proposed Fix: {proposed_fix}")
            return False

        # Medium or High risk require user approval
        risk_str = self.risk_levels.get(risk_level, risk_level)
        print(f"\n==========================================")
        print(f"   USER APPROVAL REQUEST - {risk_str.upper()}")
        print(f"==========================================")
        print(f"Issue:           {issue}")
        print(f"Proposed Fix:    {proposed_fix}")
        print(f"Expected Outcome:{expected_benefit}")
        print(f"Risk Level:      {risk_str}")
        print(f"==========================================")
        
        if risk_level == "HIGH":
            print("[!] WARNING: This is a HIGH risk action. Please review carefully.")
            prompt = "Do you explicitly confirm and approve this action? (yes/no): "
            confirm_val = "yes"
        else:
            prompt = "Approve this action? (y/n): "
            confirm_val = "y"

        try:
            choice = input(prompt).strip().lower()
            if choice == confirm_val or (confirm_val == "y" and choice == "yes"):
                print("[+] Action approved by user.")
                return True
            else:
                print("[-] Action declined by user.")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\n[-] Action declined due to input interruption.")
            return False

    def verify_emergency_stop_conditions(self, system_status: Dict[str, Any]) -> None:
        """Checks if any emergency stop condition is triggered, raising EmergencyStopException if true.

        Conditions:
        - BSOD logs detected recently.
        - SMART failure detected on disk drives.
        - Repeated repair failures on the same action (>= 2).
        - Disk corruption suspected.
        """
        # 1. SMART Failure Check
        if system_status.get("smart_status", "").upper() == "FAILING":
            raise EmergencyStopException("SMART disk failure detected. Immediately stopping all automation.")

        # 2. Repeated Repair Failure Check
        repeated_failures = self.state_manager.state_data.get("repeated_failures", {})
        for action_id, count in repeated_failures.items():
            if count >= 2:
                raise EmergencyStopException(
                    f"Action '{action_id}' failed repeatedly ({count} times). "
                    "Aborting automation to prevent further system issues."
                )

        # 3. BSOD Detection Check
        if system_status.get("bsod_detected", False):
            raise EmergencyStopException("Blue Screen of Death (BSOD) event detected in event log. Aborting execution.")
        
        # 4. Disk corruption Check
        if system_status.get("disk_corruption_suspected", False):
            raise EmergencyStopException("Disk corruption is suspected. Aborting automation immediately.")
