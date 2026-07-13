import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.services.quality.quality_models import QualityIssue
from app.config.settings import settings
from app.core.logger import logger
from app.core.llm_utils import groq_rate_limiter, retry_llm_call

class RefactorSuggestion(BaseModel):
    rule: str = Field(description="A short identifier, e.g. refactor_suggestion")
    title: str = Field(description="A short title for the refactor")
    description: str = Field(description="Detailed explanation of the complexity issue")
    recommendation: str = Field(description="Concrete steps or code to refactor the function")
    confidence: str = Field(description="Confidence: high, medium, or low")

class LLMRefactorResponse(BaseModel):
    issues: List[RefactorSuggestion] = Field(description="List of refactoring suggestions")

class LLMRefactorChecker:
    def __init__(self):
        try:
            self.llm = ChatGroq(
                temperature=0.2, 
                model_name="llama3-70b-8192", 
                api_key=settings.GROQ_API_KEY
            ).with_structured_output(LLMRefactorResponse)
            
            self.prompt = PromptTemplate.from_template(
                """You are an elite Software Architect. 
The following function has been flagged for high cyclomatic complexity or excessive length.
Analyze the function and provide concrete refactoring suggestions to improve readability, maintainability, and reduce complexity.

File: {file_path}
Function: {function_name}
Code:
{code_block}
"""
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM Refactor Checker: {e}")
            self.llm = None

    async def scan(self, file_path: str, function_name: str, code_block: str, start_line: int) -> List[QualityIssue]:
        if not self.llm or not code_block:
            return []
            
        try:
            @retry_llm_call
            async def _invoke():
                async with groq_rate_limiter:
                    return await self.prompt.pipe(self.llm).ainvoke({
                        "file_path": file_path,
                        "function_name": function_name,
                        "code_block": code_block
                    })
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
                        recommendation=issue.recommendation,
                        confidence=issue.confidence.lower()
                    )
                )
            return issues
        except Exception as e:
            logger.error(f"LLM Refactor Scan failed for {function_name} in {file_path}: {e}")
            return []
