from typing import List

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.config.settings import settings
from app.core.llm_utils import groq_rate_limiter, retry_llm_call
from app.core.logger import logger
from app.services.quality.quality_models import QualityIssue


class RefactorSuggestion(BaseModel):
    rule: str = Field(description="A short identifier, e.g. dead_code")
    title: str = Field(description="A short title for the refactor")
    description: str = Field(
        description="Detailed explanation of the complexity or quality issue"
    )
    why_it_matters: str = Field(
        description="Explanation of why this affects maintainability or readability"
    )
    recommendation: str = Field(
        description="Concrete steps or code to refactor the function"
    )
    improved_code: str = Field(
        "", description="Suggested code snippet to fix the issue. Leave empty if N/A."
    )
    confidence: str = Field(description="Confidence: high, medium, or low")


class LLMRefactorResponse(BaseModel):
    issues: List[RefactorSuggestion] = Field(
        description="List of refactoring suggestions"
    )


class LLMRefactorChecker:
    def __init__(self):
        try:
            self.llm = ChatGroq(
                temperature=0.2,
                model_name="llama3-70b-8192",
                api_key=settings.GROQ_API_KEY,
            ).with_structured_output(LLMRefactorResponse)

            self.prompt = PromptTemplate.from_template(
                """You are an elite Software Architect performing a strict code quality review.

CRITICAL RULES:
1. Every finding MUST reference actual changed code. Do NOT comment on lines that were not modified.
2. NEVER invent issues or comment on unchanged files.
3. Ignore security and deep logical errors; focus entirely on Code Quality and Clean Code principles.

Analyze the function and detect:
- Dead Code
- Duplicate Code
- Large Functions
- Naming Problems
- Poor Readability
- Missing Error Handling
- Unused Variables
- Code Smells
- Maintainability Issues

Provide concrete refactoring suggestions.

File: {file_path}
Function: {function_name}
Code:
{code_block}
"""
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM Refactor Checker: {e}")
            self.llm = None

    async def scan(
        self, file_path: str, function_name: str, code_block: str, start_line: int
    ) -> List[QualityIssue]:
        if not self.llm or not code_block:
            return []

        try:

            @retry_llm_call
            async def _invoke():
                async with groq_rate_limiter:
                    return await self.prompt.pipe(self.llm).ainvoke(
                        {
                            "file_path": file_path,
                            "function_name": function_name,
                            "code_block": code_block,
                        }
                    )

            result: LLMRefactorResponse = await _invoke()

            issues = []
            for issue in result.issues:
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=start_line,
                        rule=issue.rule,
                        severity="medium",
                        title=issue.title,
                        description=issue.description,
                        why_it_matters=issue.why_it_matters,
                        recommendation=issue.recommendation,
                        improved_code=issue.improved_code,
                        confidence=issue.confidence.lower(),
                    )
                )
            return issues
        except Exception as e:
            logger.error(
                f"LLM Refactor Scan failed for {function_name} in {file_path}: {e}"
            )
            return []
