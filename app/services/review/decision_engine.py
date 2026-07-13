from app.db.models import ReviewDecision, Severity
from app.services.review.review_models import MergedIssue
from typing import List

class DecisionEngine:
    def __init__(self):
        pass

    def decide(self, health_score: int, issues: List[MergedIssue]) -> ReviewDecision:
        critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL)
        
        if critical_count > 0 or health_score < 70:
            return ReviewDecision.CHANGES_REQUESTED
            
        if health_score >= 85 and critical_count == 0:
            return ReviewDecision.APPROVED
            
        # Fallback or edge cases (e.g., conflicting findings, lots of warnings but no critical)
        return ReviewDecision.COMMENTED

decision_engine = DecisionEngine()
