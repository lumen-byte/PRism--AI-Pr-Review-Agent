from app.db.models import Severity
from app.services.review.review_models import MergedIssue


class CommentFormatter:
    def __init__(self):
        pass

    def format_inline_comment(self, issue: MergedIssue) -> str:
        """
        Formats a single issue into a professional GitHub markdown comment.
        """
        icon = (
            "🚨"
            if issue.severity == Severity.CRITICAL
            else "🛑"
            if issue.severity == Severity.ERROR
            else "⚠️"
            if issue.severity == Severity.WARNING
            else "💡"
        )

        lines = [
            f"**{icon} [{issue.severity.name}] {issue.title}**",
            "",
            f"**Issue:** {issue.description}",
        ]

        if getattr(issue, "why_it_matters", ""):
            lines.append(f"**Impact:** {issue.why_it_matters}")

        if getattr(issue, "recommendation", ""):
            lines.append(f"**Fix:** {issue.recommendation}")

        if getattr(issue, "improved_code", None):
            lines.append("")
            lines.append("```")
            lines.append(issue.improved_code)
            lines.append("```")

        return "\\n".join(lines)


comment_formatter = CommentFormatter()
