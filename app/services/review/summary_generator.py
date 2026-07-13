from typing import List
from app.services.review.review_models import MergedIssue
from app.db.models import ReviewDecision

class SummaryGenerator:
    def __init__(self):
        pass

    def generate(self, decision: ReviewDecision, score: int, issues: List[MergedIssue]) -> str:
        decision_str = "Approved" if decision == ReviewDecision.APPROVED else "Changes Requested" if decision == ReviewDecision.CHANGES_REQUESTED else "Needs Discussion"
        
        lines = [
            f"### ReviewSense Summary",
            f"**Recommendation:** {decision_str}",
            f"**Health Score:** {score}/100",
            ""
        ]
        
        if score >= 90:
            lines.append("Excellent work! The code looks solid and has passed security, logic, and quality checks.")
        elif score >= 70:
            lines.append("The code is mostly good, but there are some areas that need improvement.")
        else:
            lines.append("Several issues were detected. Please address the critical and high severity findings below.")
            
        lines.append("")
        
        # Group top issues
        critical = [i for i in issues if i.severity.name == 'CRITICAL']
        high = [i for i in issues if i.severity.name == 'ERROR']
        
        if critical or high:
            lines.append("### Top Issues")
            for i in critical:
                lines.append(f"- **[CRITICAL]** {i.title}: {i.description} (File: `{i.file}`, Line: {i.line})")
            for i in high:
                lines.append(f"- **[HIGH]** {i.title}: {i.description} (File: `{i.file}`, Line: {i.line})")
                
        return "\\n".join(lines)

summary_generator = SummaryGenerator()
