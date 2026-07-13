from app.db.models import Severity

class HealthScoreCalculator:
    def __init__(self):
        self.penalties = {
            Severity.CRITICAL: 30,
            Severity.ERROR: 15,
            Severity.WARNING: 8,
            Severity.INFO: 3,
        }

    def calculate(self, issues: list) -> int:
        score = 100
        for issue in issues:
            penalty = self.penalties.get(issue.severity, 0)
            score -= penalty
        
        # Clamp score between 0 and 100
        return max(0, min(100, score))

health_score_calculator = HealthScoreCalculator()
