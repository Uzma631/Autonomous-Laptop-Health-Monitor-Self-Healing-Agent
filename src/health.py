from typing import Dict, Any

class HealthEvaluator:
    """Calculates component health scores and aggregates them into a weighted overall score."""

    def __init__(self):
        # Weights defined in runbook.md
        self.weights = {
            "cpu": 0.20,
            "memory": 0.20,
            "storage": 0.20,
            "driver": 0.15,
            "windows": 0.15,
            "security": 0.10
        }

    def evaluate_cpu(self, idle_or_usage: float) -> float:
        """Calculates CPU health score based on utilization.

        Thresholds (tools.md):
        <40% Excellent (100 pts)
        40-70% Good (85 pts)
        70-90% Warning (60 pts)
        >90% Critical (30 pts)
        """
        usage = float(idle_or_usage)
        if usage < 40.0:
            return 100.0
        elif usage <= 70.0:
            return 85.0
        elif usage <= 90.0:
            return 60.0
        else:
            return 30.0

    def evaluate_memory(self, used_percent: float) -> float:
        """Calculates Memory health score based on used memory percentage.

        Thresholds (tools.md):
        <70% Excellent (100 pts)
        70-85% Good (85 pts)
        85-95% Warning (60 pts)
        >95% Critical (30 pts)
        """
        used = float(used_percent)
        if used < 70.0:
            return 100.0
        elif used <= 85.0:
            return 85.0
        elif used <= 95.0:
            return 60.0
        else:
            return 30.0

    def evaluate_storage(self, free_percent: float) -> float:
        """Calculates Storage health score based on free disk percentage.

        Thresholds (tools.md):
        >20% Free Excellent (100 pts)
        10-20% Warning (60 pts)
        <10% Critical (30 pts)
        """
        free = float(free_percent)
        if free > 20.0:
            return 100.0
        elif free >= 10.0:
            return 60.0
        else:
            return 30.0

    def evaluate_driver(self, has_errors: bool, warning_count: int = 0) -> float:
        """Calculates Driver health score."""
        if has_errors:
            return 50.0  # Critical hardware/driver failure
        elif warning_count > 0:
            return 80.0  # Outdated or warning driver
        return 100.0

    def evaluate_windows(self, sfc_corrupted: bool, updates_pending: bool) -> float:
        """Calculates Windows Update / System Files health score."""
        if sfc_corrupted:
            return 50.0
        elif updates_pending:
            return 80.0
        return 100.0

    def evaluate_security(self, defender_active: bool, threats_active: bool) -> float:
        """Calculates Security health score."""
        if threats_active:
            return 0.0
        elif not defender_active:
            return 40.0
        return 100.0

    def calculate_overall(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """Calculates the weighted health score.

        Args:
            scores: Dict mapping component names to their raw scores (0-100).
        
        Returns:
            A dict with individual scores, the weighted overall score, and the text rating.
        """
        # Ensure all components have a default score if missing
        filled_scores = {}
        for key in self.weights.keys():
            filled_scores[key] = scores.get(key, 100.0)

        overall_score = sum(filled_scores[k] * self.weights[k] for k in self.weights.keys())

        # Overall health classification (runbook.md)
        if overall_score >= 90.0:
            rating = "Excellent"
        elif overall_score >= 75.0:
            rating = "Good"
        elif overall_score >= 60.0:
            rating = "Needs Attention"
        else:
            rating = "Critical"

        return {
            "components": filled_scores,
            "overall": round(overall_score, 1),
            "rating": rating
        }
