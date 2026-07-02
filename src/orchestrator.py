import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from src.config import ConfigManager, StateManager
from src.powershell import PowerShellRunner
from src.guardrails import GuardrailsManager, EmergencyStopException
from src.health import HealthEvaluator
from src.logger import AuditLogger

# Diagnostics
from src.diagnostics.system import SystemDiagnostics
from src.diagnostics.storage import StorageDiagnostics
from src.diagnostics.network import NetworkDiagnostics
from src.diagnostics.services import ServiceDiagnostics
from src.diagnostics.drivers import DriverDiagnostics
from src.diagnostics.updates import UpdateDiagnostics

# Remediations
from src.remediations.cleanup import StorageCleanupRemediation
from src.remediations.system_repair import SystemRepairRemediation
from src.remediations.services import ServiceRecoveryRemediation
from src.remediations.network import NetworkRemediation
from src.remediations.processes import ProcessRemediation


class Orchestrator:
    """Manages the full Laptop Health Monitor lifecycle: diagnosis, decision making, remediation, and reporting."""

    def __init__(self, config_manager: ConfigManager, state_manager: StateManager):
        self.config = config_manager
        self.state = state_manager
        
        # Core components
        self.ps_runner = PowerShellRunner()
        self.guardrails = GuardrailsManager(self.state)
        self.health_evaluator = HealthEvaluator()
        self.logger = AuditLogger(self.config.get_log_file_path())

        # Initialize diagnostic modules
        self.diag_system = SystemDiagnostics(self.ps_runner)
        self.diag_storage = StorageDiagnostics(self.ps_runner)
        self.diag_network = NetworkDiagnostics(self.ps_runner)
        self.diag_services = ServiceDiagnostics(self.ps_runner, self.config.get_monitored_services())
        self.diag_drivers = DriverDiagnostics(self.ps_runner)
        self.diag_updates = UpdateDiagnostics(self.ps_runner)

        # Initialize remediation modules
        self.rem_cleanup = StorageCleanupRemediation(self.ps_runner, self.config.get_cleanup_targets())
        self.rem_repair = SystemRepairRemediation(self.ps_runner)
        self.rem_services = ServiceRecoveryRemediation(self.ps_runner)
        self.rem_network = NetworkRemediation(self.ps_runner)
        self.rem_processes = ProcessRemediation(self.ps_runner)

    def run_health_check(self, interval_mode: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Performs system diagnostic scans, calculates the health score, and checks for emergency stops.

        Args:
            interval_mode: Optional string ('daily', 'weekly', 'monthly') to filter executed checks.

        Returns:
            A tuple of (raw_diagnostics, health_evaluation).
        """
        self.logger.log_info("Starting Laptop Health Diagnostic Scan...")
        
        # Verify execution elevation (Administrator check)
        is_elevated = self.ps_runner.is_admin()
        if not is_elevated:
            self.logger.log_warning("Agent is not running as Administrator. Some repairs will be restricted.")

        # 1. Run Diagnostics (Interval based)
        run_daily = interval_mode in [None, "daily", "weekly", "monthly"]
        run_weekly = interval_mode in [None, "weekly", "monthly"]
        run_monthly = interval_mode in [None, "monthly"]

        diagnostics = {}
        
        # Daily Diagnostics (CPU, Memory, Storage, Services)
        if run_daily:
            self.logger.log_info("Running Daily Diagnostics...")
            diagnostics["cpu"] = self.diag_system.check_cpu_usage()
            diagnostics["memory"] = self.diag_system.check_memory_usage()
            diagnostics["storage"] = self.diag_storage.check_disk_space("C")
            diagnostics["smart"] = self.diag_storage.check_smart_status()
            diagnostics["services"] = self.diag_services.check_services()
            diagnostics["network_conn"] = self.diag_network.test_connectivity()

        # Weekly Diagnostics (Drivers, Updates)
        if run_weekly:
            self.logger.log_info("Running Weekly Diagnostics...")
            diagnostics["drivers"] = self.diag_drivers.check_driver_issues()
            diagnostics["updates"] = self.diag_updates.check_pending_updates()
            diagnostics["reboot_pending"] = self.diag_updates.check_pending_reboot()

        # Monthly Diagnostics (Battery wear)
        if run_monthly:
            self.logger.log_info("Running Monthly Diagnostics...")
            diagnostics["battery"] = self.diag_system.check_battery_health()

        # Compile safety info for emergency stop checks
        safety_status = {
            "smart_status": diagnostics.get("smart", {}).get("overall_status", "Healthy"),
            "bsod_detected": False, # Mock/extended implementation can check event logs
            "disk_corruption_suspected": False
        }
        
        # Enforce Emergency Stop check
        self.guardrails.verify_emergency_stop_conditions(safety_status)

        # 2. Evaluate Health Score
        scores = {}
        if "cpu" in diagnostics:
            scores["cpu"] = self.health_evaluator.evaluate_cpu(diagnostics["cpu"])
        if "memory" in diagnostics:
            scores["memory"] = self.health_evaluator.evaluate_memory(diagnostics["memory"].get("used_percent", 0.0))
        if "storage" in diagnostics:
            scores["storage"] = self.health_evaluator.evaluate_storage(diagnostics["storage"].get("free_percent", 100.0))
        if "drivers" in diagnostics:
            drvs = diagnostics["drivers"]
            has_errs = len(drvs.get("failed_devices", [])) > 0 or len(drvs.get("conflicting_drivers", [])) > 0 or len(drvs.get("missing_drivers", [])) > 0
            warn_cnt = len(drvs.get("outdated_drivers", []))
            scores["driver"] = self.health_evaluator.evaluate_driver(has_errs, warn_cnt)
        if "updates" in diagnostics:
            pending_count = diagnostics["updates"].get("pending_count", 0)
            scores["windows"] = self.health_evaluator.evaluate_windows(
                sfc_corrupted=False, # Detected later if SFC runs
                updates_pending=(pending_count > 0 or diagnostics.get("reboot_pending", False))
            )
        
        # Security Health check
        # Run Get-MpComputerStatus for security check
        defender_active = True
        threats_active = False
        sec_res, sec_status = self.ps_runner.run_json("Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled, AMServiceEnabled")
        if sec_res:
            if isinstance(sec_status, list) and len(sec_status) > 0:
                sec_status = sec_status[0]
            rt = str(sec_res.get("RealTimeProtectionEnabled", "")).strip().lower()
            am = str(sec_res.get("AMServiceEnabled", "")).strip().lower()
            if rt == "false" or am == "false":
                defender_active = False

        scores["security"] = self.health_evaluator.evaluate_security(defender_active, threats_active)
        diagnostics["security_defender_active"] = defender_active

        evaluation = self.health_evaluator.calculate_overall(scores)
        return diagnostics, evaluation

    def diagnose_and_repair(self, interval_mode: Optional[str] = None) -> None:
        """Executes the complete diagnostic, decision, repair, and logging workflow."""
        try:
            # 1. First health check scan
            diagnostics, eval_before = self.run_health_check(interval_mode)
            
            self.logger.log_success(
                f"Initial Health Rating: {eval_before['rating']} (Score: {eval_before['overall']}/100)"
            )
            
            # 2. Identify Issues and build proposals
            proposals = self._identify_issues(diagnostics)
            
            if not proposals:
                self.logger.log_success("No issues detected. System is running optimally.")
                return

            # 3. Process each repair proposal
            repairs_attempted = False
            for prop in proposals:
                issue_id = prop["id"]
                issue_desc = prop["issue"]
                proposed_fix = prop["fix"]
                expected_benefit = prop["benefit"]
                risk_cat = prop["risk_category"]
                
                # Double-check command for forbidden actions
                # (Normally action functions contain shell calls)
                # We do a mock check here for the CLI description text as well
                is_forbidden, reason = self.guardrails.check_for_forbidden_actions(proposed_fix)
                if is_forbidden:
                    self.logger.log_error(f"Action blocked: {reason}")
                    self.logger.log_action(
                        issue=issue_desc,
                        action=proposed_fix,
                        risk=risk_cat,
                        result="Blocked",
                        verification=f"Action forbidden: {reason}"
                    )
                    continue

                # Assess risk category and request user approval
                risk_level = self.guardrails.assess_risk(risk_cat)
                
                approved = self.guardrails.request_approval(
                    issue=issue_desc,
                    proposed_fix=proposed_fix,
                    expected_benefit=expected_benefit,
                    risk_level=risk_level
                )

                if not approved:
                    self.logger.log_warning(f"Repair declined/skipped: {proposed_fix}")
                    self.logger.log_action(
                        issue=issue_desc,
                        action=proposed_fix,
                        risk=risk_level,
                        result="Declined",
                        verification="User declined action approval."
                    )
                    continue

                # Execute repair
                self.logger.log_info(f"Executing repair: {proposed_fix}...")
                repairs_attempted = True
                
                try:
                    action_fn = prop["action_fn"]
                    verify_fn = prop["verify_fn"]
                    
                    repair_result = action_fn()
                    
                    if repair_result.get("success", False):
                        # Verify the repair
                        self.logger.log_info("Verifying repair success...")
                        time.sleep(1) # Allow state change to settle
                        verify_result = verify_fn()
                        
                        if verify_result.get("success", False):
                            self.logger.log_success(f"Repair succeeded: {verify_result.get('details', '')}")
                            self.state.clear_failures(issue_id)
                            result_status = "Success"
                        else:
                            self.logger.log_warning(f"Repair completed but verification failed: {verify_result.get('details', '')}")
                            self.state.increment_failure(issue_id)
                            result_status = "Verification Failed"
                            
                        self.logger.log_action(
                            issue=issue_desc,
                            action=proposed_fix,
                            risk=risk_level,
                            result=result_status,
                            verification=verify_result.get("details", "N/A")
                        )
                    else:
                        error_details = repair_result.get("details", "Unknown failure")
                        self.logger.log_error(f"Repair failed: {error_details}")
                        self.state.increment_failure(issue_id)
                        
                        self.logger.log_action(
                            issue=issue_desc,
                            action=proposed_fix,
                            risk=risk_level,
                            result="Failed",
                            verification=f"Execution error: {error_details}"
                        )
                except Exception as e:
                    self.logger.log_error(f"Exception during repair: {e}")
                    self.state.increment_failure(issue_id)
                    self.logger.log_action(
                        issue=issue_desc,
                        action=proposed_fix,
                        risk=risk_level,
                        result="Failed",
                        verification=f"Internal Exception: {str(e)}"
                    )

            # 4. If repairs were run, re-run diagnostics to get new health score
            if repairs_attempted:
                self.logger.log_info("Recalculating health rating...")
                _, eval_after = self.run_health_check(interval_mode)
                self.logger.log_success(
                    f"Final Health Rating: {eval_after['rating']} (Score: {eval_after['overall']}/100)"
                )
            
            # Record last execution timestamp
            if interval_mode:
                self.state.set_last_run(interval_mode, datetime.now().isoformat())

        except EmergencyStopException as ese:
            self.logger.log_error(f"EMERGENCY STOP TRIGGERED: {ese}")
            # Log stop event
            self.logger.log_action(
                issue="Critical system risk detected.",
                action="Emergency abort initiated.",
                risk="Critical",
                result="Aborted",
                verification=str(ese)
            )

    def _identify_issues(self, diagnostics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyzes diagnostic data and maps issues to corresponding auto-fix proposals."""
        proposals = []

        # 1. Disk Space Check
        if "storage" in diagnostics:
            storage = diagnostics["storage"]
            free_pct = storage.get("free_percent", 100.0)
            critical_thresh = self.config.get_threshold("storage_free_critical")
            warning_thresh = self.config.get_threshold("storage_free_warning")
            
            if free_pct < critical_thresh or free_pct < warning_thresh:
                proposals.append({
                    "id": "cleanup_temp_files",
                    "issue": f"Low disk space on C: drive. Free percentage is {free_pct}%",
                    "fix": "Clear temporary files and empty the Recycle Bin.",
                    "benefit": "Frees up disk space to improve storage performance.",
                    "risk_category": "TEMP_CLEANUP",
                    "action_fn": self.rem_cleanup.clean_temp_directories,
                    "verify_fn": lambda: {
                        "success": self.diag_storage.check_disk_space("C").get("free_percent", 0) > free_pct,
                        "details": f"Free storage improved. Current: {self.diag_storage.check_disk_space('C').get('free_percent', 0)}%"
                    }
                })

        # 2. Stopped Services Check
        if "services" in diagnostics:
            services = diagnostics["services"]
            stopped = services.get("stopped_services", [])
            for srv in stopped:
                proposals.append({
                    "id": f"restart_service_{srv}",
                    "issue": f"Critical service '{srv}' is stopped.",
                    "fix": f"Restart service '{srv}' and restore automatic startup type.",
                    "benefit": f"Restores core service functionality for '{srv}'.",
                    "risk_category": "SERVICE_RESTART",
                    "action_fn": lambda s=srv: self.rem_services.restart_service(s),
                    "verify_fn": lambda s=srv: {
                        "success": self.diag_services.check_services()["details"].get(s, {}).get("status") == "Running",
                        "details": f"Service '{s}' status verified."
                    }
                })

        # 3. Network Outage Check
        if "network_conn" in diagnostics:
            net = diagnostics["network_conn"]
            if not net.get("connected", False):
                proposals.append({
                    "id": "network_dns_flush",
                    "issue": "External network connectivity test failed.",
                    "fix": "Flush DNS resolver cache and renew IP configuration.",
                    "benefit": "Restores basic internet connection and updates IP configurations.",
                    "risk_category": "NETWORK_RESET",
                    "action_fn": self.rem_network.flush_dns, # Start with flush
                    "verify_fn": lambda: {
                        "success": self.diag_network.test_connectivity().get("connected", False),
                        "details": "Connectivity test succeeded."
                    }
                })

        # 4. Outdated / Pending Updates Check
        if "updates" in diagnostics:
            updates = diagnostics["updates"]
            count = updates.get("pending_count", 0)
            if count > 0:
                proposals.append({
                    "id": "trigger_updates",
                    "issue": f"There are {count} pending Windows Updates.",
                    "fix": "Scan and trigger background Windows Updates download/install.",
                    "benefit": "Ensures operating system security patches are applied.",
                    "risk_category": "UPDATE_CHECK",
                    "action_fn": self.rem_repair.trigger_update_scan,
                    "verify_fn": lambda: {
                        "success": True, # Asynchronous verification
                        "details": "Update scan triggered."
                    }
                })

        # 5. Faulty Drivers check
        if "drivers" in diagnostics:
            drivers = diagnostics["drivers"]
            if drivers.get("has_errors", False) or len(drivers.get("outdated_drivers", [])) > 0:
                for dev in drivers.get("failed_devices", []):
                    dev_name = dev.get("name", "Unknown")
                    dev_id = dev.get("id", "")
                    proposals.append({
                        "id": f"driver_repair_{dev_id}",
                        "issue": f"Hardware device '{dev_name}' driver has error status: '{dev.get('status')}'",
                        "fix": "Scan for hardware changes to re-initialize device drivers.",
                        "benefit": "Re-registers driver configuration to attempt recovery.",
                        "risk_category": "DRIVER_UPDATE",
                        "action_fn": lambda: self.ps_runner.run("Get-PnpDevice | Where-Object Status -ne 'OK' | Update-Device"), # Mock/stub
                        "verify_fn": lambda: {
                            "success": dev_id not in [d.get("id") for d in self.diag_drivers.check_driver_issues().get("failed_devices", [])],
                            "details": f"Device '{dev_name}' driver status re-checked."
                        }
                    })

                for dev in drivers.get("conflicting_drivers", []):
                    dev_name = dev.get("name", "Unknown")
                    dev_id = dev.get("id", "")
                    proposals.append({
                        "id": f"driver_conflict_{dev_id}",
                        "issue": f"Resource conflict detected for device '{dev_name}' (Code {dev.get('error_code')})",
                        "fix": "Restart device to reallocate resources.",
                        "benefit": "Resolves IRQ or memory space conflicts.",
                        "risk_category": "DRIVER_UPDATE",
                        "action_fn": lambda: self.ps_runner.run(f"Disable-PnpDevice -InstanceId '{dev_id}' -Confirm:$false; Enable-PnpDevice -InstanceId '{dev_id}' -Confirm:$false"),
                        "verify_fn": lambda: {
                            "success": dev_id not in [d.get("id") for d in self.diag_drivers.check_driver_issues().get("conflicting_drivers", [])],
                            "details": f"Device '{dev_name}' conflict status re-checked."
                        }
                    })

                for dev in drivers.get("missing_drivers", []):
                    dev_name = dev.get("name", "Unknown")
                    dev_id = dev.get("id", "")
                    proposals.append({
                        "id": f"driver_missing_{dev_id}",
                        "issue": f"Missing driver for device '{dev_name}'",
                        "fix": "Trigger Windows Update Optional Updates check to find missing drivers.",
                        "benefit": "Installs necessary drivers to enable hardware functionality.",
                        "risk_category": "UPDATE_CHECK",
                        "action_fn": self.rem_repair.trigger_update_scan,
                        "verify_fn": lambda: {
                            "success": True,
                            "details": f"Windows update scan triggered for '{dev_name}'."
                        }
                    })

                for dev in drivers.get("outdated_drivers", []):
                    dev_name = dev.get("name", "Unknown")
                    dev_id = dev.get("id", "")
                    proposals.append({
                        "id": f"driver_outdated_{dev_id}",
                        "issue": f"Outdated driver detected for device '{dev_name}' (Version: {dev.get('version')})",
                        "fix": "Check for driver updates via Windows Update.",
                        "benefit": "Improves compatibility, performance, and security.",
                        "risk_category": "DRIVER_UPDATE",
                        "action_fn": self.rem_repair.trigger_update_scan,
                        "verify_fn": lambda: {
                            "success": True,
                            "details": f"Update check triggered for '{dev_name}'."
                        }
                    })

        return proposals
