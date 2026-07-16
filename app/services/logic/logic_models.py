from typing import List

from pydantic import BaseModel, Field


class LogicIssue(BaseModel):
    file: str = Field(description="The file path where the logic issue was found")
    line: int = Field(description="The approximate line number of the issue")
    severity: str = Field(description="Severity: critical, high, medium, or low")
    title: str = Field(description="A short, descriptive title for the issue")
    description: str = Field(
        description="Detailed explanation of the logical vulnerability, edge case, or bug"
    )
    why_it_matters: str = Field(
        description="Explanation of why this issue is problematic"
    )
    recommendation: str = Field(description="Concrete steps or code to fix the issue")
    improved_code: str = Field(
        "", description="Suggested code snippet to fix the issue. Leave empty if N/A."
    )
    confidence: str = Field(description="Confidence level: high, medium, low")
    reasoning: str = Field(
        description="Step-by-step reasoning explaining why this is a logical error"
    )
    category: str = Field("logic", description="Category of the finding")

    def get_hash(self) -> str:
        """Returns a unique hash to prevent duplicate findings on the same line."""
        return f"{self.file}:{self.line}:{self.title}"


class LogicResponse(BaseModel):
    issues: List[LogicIssue] = Field(description="List of detected logical issues")
