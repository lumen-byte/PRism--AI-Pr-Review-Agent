import re
from typing import List, Dict, Any
from app.services.security.security_models import SecurityIssue
from app.core.logger import logger

class SecretDetector:
    def __init__(self):
        self.rules = [
            {
                "id": "hardcoded_aws_key",
                "pattern": re.compile(r"(?i)(?:aws_access_key_id|aws_secret_access_key|aws_session_token).*?['\"]([A-Za-z0-9/+=]{20,40})['\"]"),
                "title": "Hardcoded AWS Credentials",
                "severity": "critical",
                "description": "AWS access keys or secret keys should not be hardcoded in the source code.",
                "recommendation": "Use environment variables or AWS IAM roles instead."
            },
            {
                "id": "hardcoded_github_token",
                "pattern": re.compile(r"(?i)(?:github_token|gh_token|ghp_[a-zA-Z0-9]{36}).*?['\"]([a-zA-Z0-9]{36,40})['\"]"),
                "title": "Hardcoded GitHub Token",
                "severity": "critical",
                "description": "GitHub Personal Access Tokens or OAuth tokens were found.",
                "recommendation": "Use GitHub Actions Secrets or environment variables."
            },
            {
                "id": "hardcoded_jwt",
                "pattern": re.compile(r"eyJ[a-zA-Z0-9_-]{5,}\\.eyJ[a-zA-Z0-9_-]{5,}\\.[a-zA-Z0-9_-]{10,}"),
                "title": "Hardcoded JWT Token",
                "severity": "high",
                "description": "A JSON Web Token (JWT) is hardcoded in the codebase.",
                "recommendation": "Retrieve tokens dynamically. Do not store JWTs in source code."
            },
            {
                "id": "hardcoded_password",
                "pattern": re.compile(r"(?i)(?:password|passwd|pwd|secret|auth_token).*?=\\s*['\"]([^'\"]{6,})['\"]"),
                "title": "Hardcoded Password or Secret",
                "severity": "high",
                "description": "A hardcoded variable that resembles a password or secret was found.",
                "recommendation": "Use a secrets manager or environment variables."
            },
            {
                "id": "private_key",
                "pattern": re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----"),
                "title": "Hardcoded Private Key",
                "severity": "critical",
                "description": "A cryptographic private key was detected in the file.",
                "recommendation": "Remove the private key and manage it via secure key management systems."
            },
            {
                "id": "bearer_token",
                "pattern": re.compile(r"(?i)bearer\\s+[A-Za-z0-9\\-_=]+\\.[A-Za-z0-9\\-_=]+\\.?[A-Za-z0-9\\-_.+/=]*"),
                "title": "Hardcoded Bearer Token",
                "severity": "high",
                "description": "A Bearer token pattern was found.",
                "recommendation": "Do not hardcode Bearer tokens for API authentication."
            },
            {
                "id": "database_url",
                "pattern": re.compile(r"(?i)(?:postgres|mysql|mongodb|redis|sqlite)(?:ql)?://[\w\-]+:[^@\s]+@[\w\-.]+:\d+/[\w\-]+"),
                "title": "Hardcoded Database URL with Credentials",
                "severity": "critical",
                "description": "A database connection string containing a password was found.",
                "recommendation": "Store database URLs in secure environment configuration."
            }
        ]

    def scan(self, file_path: str, content: str) -> List[SecurityIssue]:
        issues = []
        if not content:
            return issues
            
        lines = content.split('\\n')
        for i, line in enumerate(lines):
            line_num = i + 1
            for rule in self.rules:
                if rule["pattern"].search(line):
                    issues.append(
                        SecurityIssue(
                            file=file_path,
                            line=line_num,
                            rule=rule["id"],
                            severity=rule["severity"],
                            title=rule["title"],
                            description=rule["description"],
                            recommendation=rule["recommendation"],
                            confidence="high"
                        )
                    )
        return issues
