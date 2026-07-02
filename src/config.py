import os
import json
from typing import Dict, Any, List, Optional

DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
DEFAULT_STATE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "state.json"))

class ConfigManager:
    """Manages the configuration options and thresholds for the Laptop Health Monitor."""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Loads configuration from config_path, falling back to defaults if not found or corrupted."""
        if not os.path.exists(self.config_path):
            self.config_data = self._get_default_config()
            self.save_config()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            # Fall back to default config if reading fails
            self.config_data = self._get_default_config()
            self.save_config()

    def save_config(self) -> None:
        """Saves current configuration data back to config_path."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2)
        except OSError:
            pass  # Fail silently or log error depending on engine state

    def _get_default_config(self) -> Dict[str, Any]:
        """Returns the default configuration dictionary."""
        return {
            "thresholds": {
                "cpu_warning": 70.0,
                "cpu_critical": 90.0,
                "memory_warning": 85.0,
                "memory_critical": 95.0,
                "storage_free_warning": 20.0,
                "storage_free_critical": 10.0
            },
            "cleanup_targets": [
                "C:\\Windows\\Temp",
                "AppData\\Local\\Temp"
            ],
            "monitored_services": [
                "wuauserv",
                "Spooler",
                "Dhcp",
                "BFE",
                "LanmanWorkstation",
                "EventLog"
            ],
            "log_file_path": "audit_log.md"
        }

    def get_threshold(self, name: str) -> float:
        """Returns a threshold float value. Falls back to defaults if missing."""
        thresholds = self.config_data.get("thresholds", {})
        default_thresholds = self._get_default_config()["thresholds"]
        return float(thresholds.get(name, default_thresholds.get(name)))

    def get_cleanup_targets(self) -> List[str]:
        """Returns a list of temporary cleanup paths."""
        return list(self.config_data.get("cleanup_targets", self._get_default_config()["cleanup_targets"]))

    def get_monitored_services(self) -> List[str]:
        """Returns list of service names to monitor."""
        return list(self.config_data.get("monitored_services", self._get_default_config()["monitored_services"]))

    def get_log_file_path(self) -> str:
        """Returns the log file path, resolving to absolute path if needed."""
        path = self.config_data.get("log_file_path", "audit_log.md")
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(os.path.dirname(self.config_path), path))
        return path


class StateManager:
    """Manages the agent running state, interval checks, and failure records."""

    def __init__(self, state_path: str = DEFAULT_STATE_PATH):
        self.state_path = state_path
        self.state_data: Dict[str, Any] = {}
        self.load_state()

    def load_state(self) -> None:
        """Loads state tracker from state_path, falling back to defaults if not found or corrupted."""
        if not os.path.exists(self.state_path):
            self.state_data = self._get_default_state()
            self.save_state()
            return

        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                self.state_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            self.state_data = self._get_default_state()
            self.save_state()

    def save_state(self) -> None:
        """Saves current state data back to state_path."""
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(self.state_data, f, indent=2)
        except OSError:
            pass

    def _get_default_state(self) -> Dict[str, Any]:
        """Returns default state structure."""
        return {
            "last_run_daily": None,
            "last_run_weekly": None,
            "last_run_monthly": None,
            "repeated_failures": {}
        }

    def get_last_run(self, interval: str) -> Optional[str]:
        """Returns ISO format timestamp of the last run for an interval ('daily', 'weekly', 'monthly')."""
        key = f"last_run_{interval}"
        return self.state_data.get(key)

    def set_last_run(self, interval: str, timestamp: str) -> None:
        """Sets the last run timestamp for an interval."""
        key = f"last_run_{interval}"
        self.state_data[key] = timestamp
        self.save_state()

    def get_failure_count(self, action_id: str) -> int:
        """Gets number of consecutive failures for a specific repair action."""
        failures = self.state_data.get("repeated_failures", {})
        return int(failures.get(action_id, 0))

    def increment_failure(self, action_id: str) -> int:
        """Increments and returns the failure counter for a specific repair action."""
        if "repeated_failures" not in self.state_data:
            self.state_data["repeated_failures"] = {}
        
        current = self.state_data["repeated_failures"].get(action_id, 0)
        new_count = current + 1
        self.state_data["repeated_failures"][action_id] = new_count
        self.save_state()
        return new_count

    def clear_failures(self, action_id: str) -> None:
        """Resets the failure counter for a specific repair action upon success."""
        if "repeated_failures" in self.state_data and action_id in self.state_data["repeated_failures"]:
            del self.state_data["repeated_failures"][action_id]
            self.save_state()
