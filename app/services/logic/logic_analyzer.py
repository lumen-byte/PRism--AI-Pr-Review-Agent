import json
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from app.services.logic.logic_models import LogicIssue, LogicResponse
from app.services.logic.reasoning_prompt import LOGIC_REASONING_PROMPT
from app.config.settings import settings
from app.core.logger import logger
from app.core.llm_utils import groq_rate_limiter, retry_llm_call

class LogicAnalyzer:
    def __init__(self):
        try:
            self.llm = ChatGroq(
                temperature=0, 
                model_name="llama3-70b-8192", 
                api_key=settings.GROQ_API_KEY
            ).with_structured_output(LogicResponse)
            
            self.chain = LOGIC_REASONING_PROMPT | self.llm
        except Exception as e:
            logger.error(f"Failed to initialize Logic Analyzer: {e}")
            self.llm = None
            self.chain = None

    async def analyze(self, file_path: str, context: str, start_line_offset: int) -> List[LogicIssue]:
        if not self.chain or not context:
            return []
            
        try:
            @retry_llm_call
            async def _invoke():
                async with groq_rate_limiter:
                    return await self.chain.ainvoke({
                        "context": context
                    })
            result: LogicResponse = await _invoke()
            
            issues = []
            for issue in result.issues:
                # Adjust line number if it's relative
                # For safety, we just cap it or trust the LLM, but usually it might return 0 if it doesn't know
                actual_line = issue.line if issue.line > 0 else start_line_offset
                
                issues.append(
                    LogicIssue(
                        file=file_path,
                        line=actual_line,
                        severity=issue.severity.lower(),
                        title=issue.title,
                        description=issue.description,
                        recommendation=issue.recommendation,
                        confidence=issue.confidence.lower(),
                        reasoning=issue.reasoning
                    )
                )
            return issues
        except Exception as e:
            logger.error(f"Logic Analyzer Scan failed for {file_path}: {e}")
            return []

logic_analyzer = LogicAnalyzer()
