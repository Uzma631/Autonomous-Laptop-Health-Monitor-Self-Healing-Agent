import unittest
from unittest.mock import MagicMock
from src.diagnostics.drivers import DriverDiagnostics

class TestDriverDiagnostics(unittest.TestCase):
    def setUp(self):
        self.ps_runner_mock = MagicMock()
        self.diag = DriverDiagnostics(self.ps_runner_mock)

    def test_no_issues(self):
        # Mock PowerShell response: 1 good device
        self.ps_runner_mock.run_json.side_effect = [
            (
                [
                    {
                        "InstanceId": "DEV1",
                        "FriendlyName": "Good Device",
                        "Class": "System",
                        "Status": "OK",
                        "ConfigManagerErrorCode": 0,
                        "DriverDate": "2023-01-01",
                        "DriverVersion": "1.0.0.0",
                        "SignerProvider": "Intel",
                        "Manufacturer": "Intel"
                    }
                ],
                MagicMock(success=True)
            ),
            (
                [], # No events
                MagicMock(success=True)
            )
        ]
        
        report = self.diag.check_driver_issues()
        self.assertFalse(report["has_errors"])
        self.assertEqual(len(report["failed_devices"]), 0)
        self.assertEqual(len(report["missing_drivers"]), 0)
        self.assertEqual(len(report["conflicting_drivers"]), 0)
        self.assertEqual(len(report["outdated_drivers"]), 0)

    def test_failed_device(self):
        self.ps_runner_mock.run_json.side_effect = [
            (
                [
                    {
                        "InstanceId": "DEV2",
                        "FriendlyName": "Bad Device",
                        "Class": "System",
                        "Status": "Error",
                        "ConfigManagerErrorCode": 43, # Generic failure
                        "DriverDate": "2023-01-01",
                        "DriverVersion": "1.0",
                        "SignerProvider": "Test",
                        "Manufacturer": "Test"
                    }
                ],
                MagicMock(success=True)
            ),
            (
                [],
                MagicMock(success=True)
            )
        ]
        
        report = self.diag.check_driver_issues()
        self.assertTrue(report["has_errors"])
        self.assertEqual(len(report["failed_devices"]), 1)
        self.assertEqual(report["failed_devices"][0]["error_code"], 43)

    def test_missing_driver(self):
        self.ps_runner_mock.run_json.side_effect = [
            (
                [
                    {
                        "InstanceId": "DEV3",
                        "FriendlyName": "Unknown Device",
                        "Class": "Unknown",
                        "Status": "Error",
                        "ConfigManagerErrorCode": 28, # Missing
                        "DriverDate": None,
                        "DriverVersion": None,
                        "SignerProvider": None,
                        "Manufacturer": None
                    }
                ],
                MagicMock(success=True)
            ),
            (
                [],
                MagicMock(success=True)
            )
        ]
        
        report = self.diag.check_driver_issues()
        self.assertTrue(report["has_errors"])
        self.assertEqual(len(report["missing_drivers"]), 1)

    def test_conflicting_driver(self):
        self.ps_runner_mock.run_json.side_effect = [
            (
                [
                    {
                        "InstanceId": "DEV4",
                        "FriendlyName": "Conflict Device",
                        "Class": "System",
                        "Status": "Error",
                        "ConfigManagerErrorCode": 12, # Conflict
                        "DriverDate": "2023-01-01",
                        "DriverVersion": "1.0",
                        "SignerProvider": "Test",
                        "Manufacturer": "Test"
                    }
                ],
                MagicMock(success=True)
            ),
            (
                [],
                MagicMock(success=True)
            )
        ]
        
        report = self.diag.check_driver_issues()
        self.assertTrue(report["has_errors"])
        self.assertEqual(len(report["conflicting_drivers"]), 1)

    def test_outdated_driver(self):
        self.ps_runner_mock.run_json.side_effect = [
            (
                [
                    {
                        "InstanceId": "DEV5",
                        "FriendlyName": "Old Device",
                        "Class": "System",
                        "Status": "OK",
                        "ConfigManagerErrorCode": 0,
                        "DriverDate": "2018-01-01", # Outdated (>5 yrs)
                        "DriverVersion": "1.0",
                        "SignerProvider": "Test",
                        "Manufacturer": "Test"
                    }
                ],
                MagicMock(success=True)
            ),
            (
                [],
                MagicMock(success=True)
            )
        ]
        
        report = self.diag.check_driver_issues()
        self.assertFalse(report["has_errors"]) # Outdated is warning, not error
        self.assertEqual(len(report["outdated_drivers"]), 1)

if __name__ == '__main__':
    unittest.main()
