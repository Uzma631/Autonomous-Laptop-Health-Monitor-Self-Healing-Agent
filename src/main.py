import argparse
import sys
import os
from typing import Dict, Any

# Add parent directory to path so imports resolve correctly when run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import ConfigManager, StateManager
from src.orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(
        description="Laptop Health Monitor Agent - Autonomous repair and optimization utility."
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--run-all", action="store_true",
        help="Run full diagnostics check and attempt authorized auto-fixes."
    )
    group.add_argument(
        "--diagnostic", action="store_true",
        help="Run system diagnostic scan and calculate health rating (dry-run mode)."
    )
    group.add_argument(
        "--cleanup", action="store_true",
        help="Perform temp folder cleanup and empty Recycle Bin immediately."
    )
    
    parser.add_argument(
        "--interval", choices=["daily", "weekly", "monthly"], default=None,
        help="Run checks corresponding to a specific maintenance interval."
    )

    args = parser.parse_args()

    # Load configurations and state
    config = ConfigManager()
    state = StateManager()
    
    orchestrator = Orchestrator(config, state)

    # If no flags are provided, default to --diagnostic
    if not (args.run_all or args.diagnostic or args.cleanup):
        args.diagnostic = True

    try:
        if args.diagnostic:
            print("[*] Launching Laptop Diagnostics Scan (Dry-Run Mode)...")
            diagnostics, evaluation = orchestrator.run_health_check(args.interval)
            print_health_report(diagnostics, evaluation)
            
        elif args.run_all:
            print("[*] Launching Laptop Diagnostics Scan & Autonomous Repairs...")
            orchestrator.diagnose_and_repair(args.interval)
            
        elif args.cleanup:
            print("[*] Launching Storage Cleanup Task...")
            is_admin = orchestrator.ps_runner.is_admin()
            if not is_admin:
                orchestrator.logger.log_warning("Running cleanup without Administrator privileges. Some folders may be skipped.")
            
            # Low risk cleanup can run automatically
            clean_res = orchestrator.rem_cleanup.clean_temp_directories()
            recycle_res = orchestrator.rem_cleanup.empty_recycle_bin()
            
            orchestrator.logger.log_success(f"Temp folders cleanup result: {clean_res.get('details')}")
            orchestrator.logger.log_success(f"Recycle bin empty result: {recycle_res.get('details')}")
            
            orchestrator.logger.log_action(
                issue="User-requested storage cleanup.",
                action="Clear temp folders and empty recycle bin.",
                risk="Low",
                result="Success" if clean_res.get("success") and recycle_res.get("success") else "Partial",
                verification="Temporary files removed."
            )

    except KeyboardInterrupt:
        print("\n[-] Agent execution cancelled by user (CTRL+C).")
        sys.exit(0)
    except Exception as e:
        print(f"\n[X] Critical agent execution failure: {e}", file=sys.stderr)
        sys.exit(1)


def print_health_report(diagnostics: Dict[str, Any], evaluation: Dict[str, Any]):
    """Formats and prints the diagnostic report and health ratings to the console."""
    print("\n" + "="*50)
    print("           SYSTEM HEALTH DIAGNOSTIC REPORT")
    print("="*50)
    
    # 1. Overall Score
    rating = evaluation["rating"]
    score = evaluation["overall"]
    print(f"Overall Rating:    {rating.upper()} ({score}/100)")
    print("-"*50)

    # 2. Individual Component Scores
    print("Component Health Scores:")
    for comp, val in evaluation["components"].items():
        print(f"  - {comp.capitalize():<12}: {val:.0f}/100")
    print("-"*50)

    # 3. Key Metrics
    print("Key System Metrics:")
    if "cpu" in diagnostics:
        print(f"  * CPU Utilization  : {diagnostics['cpu']}%")
    if "memory" in diagnostics:
        mem = diagnostics["memory"]
        print(f"  * Memory Utilization: {mem.get('used_percent')}% (Free: {mem.get('free_kb', 0)/1024/1024:.2f} GB)")
    if "storage" in diagnostics:
        disk = diagnostics["storage"]
        print(f"  * Free Disk Space   : {disk.get('free_percent')}% (Free: {disk.get('free_gb')} GB / {disk.get('size_gb')} GB)")
    if "smart" in diagnostics:
        smart = diagnostics["smart"]
        print(f"  * Disk SMART Health : {smart.get('overall_status')}")
    if "services" in diagnostics:
        srv = diagnostics["services"]
        stopped_cnt = len(srv.get("stopped_services", []))
        print(f"  * Stopped Services  : {stopped_cnt} critical service(s) stopped")
        for s in srv.get("stopped_services", []):
            print(f"      - {s}")
    if "drivers" in diagnostics:
        drv = diagnostics["drivers"]
        print(f"  * Hardware Drivers  : Checked {drv.get('total_checked', 0)} devices")
        failed = len(drv.get("failed_devices", []))
        if failed > 0:
            print(f"      - {failed} failed driver(s)")
        conflict = len(drv.get("conflicting_drivers", []))
        if conflict > 0:
            print(f"      - {conflict} conflicting driver(s)")
        missing = len(drv.get("missing_drivers", []))
        if missing > 0:
            print(f"      - {missing} missing driver(s)")
        outdated = len(drv.get("outdated_drivers", []))
        if outdated > 0:
            print(f"      - {outdated} outdated driver(s)")
    if "updates" in diagnostics:
        updates = diagnostics["updates"]
        print(f"  * Windows Updates   : {updates.get('pending_count')} pending update(s)")
        if diagnostics.get("reboot_pending", False):
            print("  * System Reboot     : Pending reboot required")
    if "battery" in diagnostics:
        battery = diagnostics["battery"]
        if battery.get("present"):
            print(f"  * Battery Charge    : {battery.get('charge_remaining')}% ({battery.get('status')})")
            print(f"  * Battery Wear      : {battery.get('wear_percent')}%")
        else:
            print("  * Battery           : Not present (Desktop PC)")
    
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
