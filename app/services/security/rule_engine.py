from typing import Any, Dict, List

from app.services.security.llm_checker import LLMSecurityChecker
from app.services.security.secret_detector import SecretDetector
from app.services.security.security_models import SecurityIssue
from app.services.security.vulnerability_checker import VulnerabilityChecker


class RuleEngine:
    def __init__(self):
        self.secret_detector = SecretDetector()
        self.vuln_checker = VulnerabilityChecker()
        self.llm_checker = LLMSecurityChecker()

    async def run_all_checks(
        self, file_path: str, content: str, patch: str, ast_data: Dict[str, Any]
    ) -> List[SecurityIssue]:
        """Runs all security layers in parallel where possible and returns deduplicated issues."""

        # Static checks are fast, run synchronously
        secret_issues = self.secret_detector.scan(file_path, content)
        ast_issues = self.vuln_checker.scan(file_path, ast_data)

        # LLM checks are async
        llm_issues = await self.llm_checker.scan(file_path, patch)

        all_issues = secret_issues + ast_issues + llm_issues

        # Deduplicate using hash
        unique_issues = {}
        for issue in all_issues:
            h = issue.get_hash()
            if h not in unique_issues:
                unique_issues[h] = issue
            else:
                # If duplicate exists, keep the one with higher severity or just skip
                pass

        return list(unique_issues.values())


rule_engine = RuleEngine()
