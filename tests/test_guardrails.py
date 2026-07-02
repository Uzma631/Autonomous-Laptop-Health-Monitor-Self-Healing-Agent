import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import StateManager
from src.guardrails import GuardrailsManager, EmergencyStopException

class TestGuardrails(unittest.TestCase):

    def setUp(self):
        # Create temp state manager with mock path
        self.state_path = "temp_state_test.json"
        if os.path.exists(self.state_path):
            os.remove(self.state_path)
            
        self.state_manager = StateManager(self.state_path)
        self.guardrails = GuardrailsManager(self.state_manager)

    def tearDown(self):
        if os.path.exists(self.state_path):
            os.remove(self.state_path)

    def test_forbidden_commands(self):
        # User folders deletion check
        is_forbidden, reason = self.guardrails.check_for_forbidden_actions("Remove-Item -Path C:\\Users\\User\\Documents -Recurse")
        self.assertTrue(is_forbidden)
        self.assertIn("forbidden pattern", reason)

        # Non-forbidden check
        is_forbidden, reason = self.guardrails.check_for_forbidden_actions("Get-Process")
        self.assertFalse(is_forbidden)

        # Defender disabling check
        is_forbidden, reason = self.guardrails.check_for_forbidden_actions("Set-MpPreference -DisableRealtimeMonitoring $true")
        self.assertTrue(is_forbidden)

    def test_risk_assessment(self):
        self.assertEqual(self.guardrails.assess_risk("TEMP_CLEANUP"), "LOW")
        self.assertEqual(self.guardrails.assess_risk("SERVICE_RESTART"), "LOW")
        self.assertEqual(self.guardrails.assess_risk("DRIVER_UPDATE"), "MEDIUM")
        self.assertEqual(self.guardrails.assess_risk("REGISTRY_WRITE"), "HIGH")
        self.assertEqual(self.guardrails.assess_risk("BIOS_UPDATE"), "CRITICAL")

    def test_emergency_stop_conditions(self):
        # Healthy status should pass without exception
        status = {"smart_status": "Healthy", "bsod_detected": False, "disk_corruption_suspected": False}
        try:
            self.guardrails.verify_emergency_stop_conditions(status)
        except EmergencyStopException:
            self.fail("verify_emergency_stop_conditions raised EmergencyStopException unexpectedly")

        # SMART failing should trigger stop
        status = {"smart_status": "FAILING", "bsod_detected": False, "disk_corruption_suspected": False}
        with self.assertRaises(EmergencyStopException):
            self.guardrails.verify_emergency_stop_conditions(status)

        # BSOD detected should trigger stop
        status = {"smart_status": "Healthy", "bsod_detected": True, "disk_corruption_suspected": False}
        with self.assertRaises(EmergencyStopException):
            self.guardrails.verify_emergency_stop_conditions(status)

        # Repeated failures check
        self.state_manager.increment_failure("repair_test")
        self.state_manager.increment_failure("repair_test")
        status = {"smart_status": "Healthy", "bsod_detected": False, "disk_corruption_suspected": False}
        with self.assertRaises(EmergencyStopException):
            self.guardrails.verify_emergency_stop_conditions(status)

if __name__ == "__main__":
    unittest.main()
