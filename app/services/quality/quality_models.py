from pydantic import BaseModel

class QualityIssue(BaseModel):
    file: str
    line: int
    rule: str
    severity: str  # critical, high, medium, low
    title: str
    description: str
    recommendation: str
    confidence: str  # high, medium, low
    
    def get_hash(self) -> str:
        """Returns a unique hash to prevent duplicate findings on the same line for the same rule."""
        return f"{self.file}:{self.line}:{self.rule}"
