from typing import List

from pydantic import BaseModel

from app.db.models import ReviewDecision, Severity


class MergedIssue(BaseModel):
    file: str
    line: int
    severity: Severity
    title: str
    description: str
    why_it_matters: str = ""
    recommendation: str = ""
    improved_code: str = ""
    category: str  # security, quality, logic

    def get_hash(self) -> str:
        return f"{self.file}:{self.line}:{self.title}"


class OrchestratorResult(BaseModel):
    merged_issues: List[MergedIssue]
    health_score: int
    decision: ReviewDecision
    summary: str
    security_score: int
    quality_score: int
    logic_score: int
