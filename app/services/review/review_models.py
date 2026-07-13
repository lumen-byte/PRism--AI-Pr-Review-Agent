from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.db.models import ReviewDecision, Severity

class MergedIssue(BaseModel):
    file: str
    line: int
    severity: Severity
    title: str
    description: str
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
