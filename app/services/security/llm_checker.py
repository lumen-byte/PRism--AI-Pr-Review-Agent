from typing import List

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.config.settings import settings
from app.core.llm_utils import groq_rate_limiter, retry_llm_call
from app.core.logger import logger
from app.services.security.security_models import SecurityIssue


class SecurityIssueSchema(BaseModel):
    file: str = Field(description="The file path where the issue was found")
    line: int = Field(description="The approximate line number of the issue")
    rule: str = Field(description="A short identifier for the rule, e.g. sql_injection")
    severity: str = Field(description="Severity: critical, high, medium, or low")
    title: str = Field(description="A short title for the issue")
    description: str = Field(description="Detailed explanation of the vulnerability")
    why_it_matters: str = Field(
        description="Explanation of why this issue is problematic and the risk it poses"
    )
    recommendation: str = Field(description="How to fix the vulnerability")
    improved_code: str = Field(
        "", description="Suggested code snippet to fix the issue. Leave empty if N/A."
    )
    confidence: str = Field(description="Confidence: high, medium, or low")


class LLMSecurityResponse(BaseModel):
    issues: List[SecurityIssueSchema] = Field(
        description="List of security issues found"
    )


class LLMSecurityChecker:
    def __init__(self):
        try:
            # Initialize ChatGroq using the LLaMA 3 model
            self.llm = ChatGroq(
                temperature=0,
                model_name="llama3-70b-8192",
                api_key=settings.GROQ_API_KEY,
            ).with_structured_output(LLMSecurityResponse)

            self.prompt = PromptTemplate.from_template(
                """You are an elite Application Security Engineer performing a code review.
Review the following code diff for security vulnerabilities.

CRITICAL RULES:
1. Every finding MUST reference actual changed code. Do NOT comment on lines that were not modified in this PR.
2. NEVER invent or hallucinate vulnerabilities. Ignore unchanged files.
3. Only report actual security vulnerabilities. Do NOT report stylistic issues or basic bugs.

Focus ONLY on detecting:
- Hardcoded Secrets
- SQL Injection
- Command Injection
- Path Traversal
- Unsafe File Access
- Weak Authentication
- Unsafe Deserialization
- Insecure Random Usage
- Missing Input Validation
- Sensitive Information Exposure

Provide proper severity (critical, high, medium, low) for each finding.

File: {file_path}
Diff / Code:
{code_diff}
"""
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM Checker: {e}")
            self.llm = None

    async def scan(self, file_path: str, patch: str) -> List[SecurityIssue]:
        if not self.llm or not patch:
            return []

        try:

            @retry_llm_call
            async def _invoke():
                async with groq_rate_limiter:
                    return await self.prompt.pipe(self.llm).ainvoke(
                        {"file_path": file_path, "code_diff": patch}
                    )

            result: LLMSecurityResponse = await _invoke()

            issues = []
            for issue in result.issues:
                issues.append(
                    SecurityIssue(
                        file=issue.file,
                        line=issue.line,
                        rule=issue.rule,
                        severity=issue.severity.lower(),
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
            logger.error(f"LLM Security Scan failed for {file_path}: {e}")
            return []
