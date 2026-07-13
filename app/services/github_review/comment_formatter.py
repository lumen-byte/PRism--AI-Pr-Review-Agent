from typing import List
from app.services.review.review_models import MergedIssue
from app.db.models import Severity

class CommentFormatter:
    def __init__(self):
        pass

    def format_inline_comment(self, issue: MergedIssue) -> str:
        """
        Formats a single issue into a professional GitHub markdown comment.
        """
        icon = "🚨" if issue.severity == Severity.CRITICAL else "🛑" if issue.severity == Severity.ERROR else "⚠️" if issue.severity == Severity.WARNING else "💡"
        
        return (
            f"**{icon} [{issue.severity.name}] {issue.title}**\\n\\n"
            f"{issue.description}"
        )

comment_formatter = CommentFormatter()
