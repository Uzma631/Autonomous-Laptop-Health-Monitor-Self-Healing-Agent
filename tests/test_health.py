import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.health import HealthEvaluator

class TestHealthEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = HealthEvaluator()

    def test_cpu_scoring(self):
        # <40% Excellent (100 pts)
        self.assertEqual(self.evaluator.evaluate_cpu(10.0), 100.0)
        self.assertEqual(self.evaluator.evaluate_cpu(39.9), 100.0)
        # 40-70% Good (85 pts)
        self.assertEqual(self.evaluator.evaluate_cpu(40.0), 85.0)
        self.assertEqual(self.evaluator.evaluate_cpu(70.0), 85.0)
        # 70-90% Warning (60 pts)
        self.assertEqual(self.evaluator.evaluate_cpu(70.1), 60.0)
        self.assertEqual(self.evaluator.evaluate_cpu(90.0), 60.0)
        # >90% Critical (30 pts)
        self.assertEqual(self.evaluator.evaluate_cpu(90.1), 30.0)

    def test_memory_scoring(self):
        # <70% Excellent (100 pts)
        self.assertEqual(self.evaluator.evaluate_memory(50.0), 100.0)
        # 70-85% Good (85 pts)
        self.assertEqual(self.evaluator.evaluate_memory(80.0), 85.0)
        # 85-95% Warning (60 pts)
        self.assertEqual(self.evaluator.evaluate_memory(90.0), 60.0)
        # >95% Critical (30 pts)
        self.assertEqual(self.evaluator.evaluate_memory(96.0), 30.0)

    def test_storage_scoring(self):
        # >20% Free Excellent (100 pts)
        self.assertEqual(self.evaluator.evaluate_storage(25.0), 100.0)
        # 10-20% Warning (60 pts)
        self.assertEqual(self.evaluator.evaluate_storage(15.0), 60.0)
        # <10% Critical (30 pts)
        self.assertEqual(self.evaluator.evaluate_storage(5.0), 30.0)

    def test_overall_calculation(self):
        # Perfect scores
        scores = {
            "cpu": 100.0,
            "memory": 100.0,
            "storage": 100.0,
            "driver": 100.0,
            "windows": 100.0,
            "security": 100.0
        }
        res = self.evaluator.calculate_overall(scores)
        self.assertEqual(res["overall"], 100.0)
        self.assertEqual(res["rating"], "Excellent")

        # Lower scores
        scores = {
            "cpu": 30.0,      # weight 0.20 -> 6.0
            "memory": 30.0,   # weight 0.20 -> 6.0
            "storage": 30.0,  # weight 0.20 -> 6.0
            "driver": 50.0,   # weight 0.15 -> 7.5
            "windows": 50.0,  # weight 0.15 -> 7.5
            "security": 40.0   # weight 0.10 -> 4.0
        }                     # Total = 37.0
        res = self.evaluator.calculate_overall(scores)
        self.assertEqual(res["overall"], 37.0)
        self.assertEqual(res["rating"], "Critical")

if __name__ == "__main__":
    unittest.main()
