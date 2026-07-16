from typing import List

from app.db.models import ReviewDecision
from app.services.review.review_models import MergedIssue


class SummaryGenerator:
    def __init__(self):
        pass

    def generate(
        self, decision: ReviewDecision, score: int, issues: List[MergedIssue]
    ) -> str:
        decision_str = (
            "Approve"
            if decision == ReviewDecision.APPROVED
            else "Request Changes"
            if decision == ReviewDecision.CHANGES_REQUESTED
            else "Comment"
        )
        risk_level = "Low" if score >= 85 else "Medium" if score >= 70 else "High"
        confidence = "High (95%)" if score >= 80 else "Medium (85%)"

        lines = [
            "### PRism Executive Summary",
            f"**Overall Health Score:** {score}/100",
            f"**Overall Risk Level:** {risk_level}",
            f"**Merge Recommendation:** {decision_str}",
            f"**Estimated Review Confidence:** {confidence}",
            "",
        ]

        if score >= 90:
            lines.append(
                "Excellent work! The code looks solid and has passed security, logic, and quality checks."
            )
        elif score >= 70:
            lines.append(
                "The code is mostly good, but there are some areas that need improvement."
            )
        else:
            lines.append(
                "Several issues were detected. Please address the critical and high severity findings below."
            )

        lines.append("")

        if issues:
            lines.append("### Top Findings")
            # Sort issues by severity (Critical > Error > Warning > Info)
            severity_order = {"CRITICAL": 0, "ERROR": 1, "WARNING": 2, "INFO": 3}
            sorted_issues = sorted(
                issues, key=lambda x: severity_order.get(x.severity.name, 4)
            )
            top_issues = sorted_issues[:5]

            for idx, i in enumerate(top_issues, 1):
                icon = (
                    "🚨"
                    if i.severity.name == "CRITICAL"
                    else "🛑"
                    if i.severity.name == "ERROR"
                    else "⚠️"
                    if i.severity.name == "WARNING"
                    else "💡"
                )
                lines.append(
                    f"{idx}. {icon} **[{i.severity.name}] {i.title}** (`{i.file}:{i.line}`) - {i.description}"
                )

        return "\\n".join(lines)


summary_generator = SummaryGenerator()
