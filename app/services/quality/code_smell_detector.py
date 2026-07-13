import re
from typing import List, Dict, Any
from app.services.quality.quality_models import QualityIssue

class CodeSmellDetector:
    def __init__(self):
        self.todo_pattern = re.compile(r"(?i)\b(?:todo|fixme)\b")
        # Matches numbers being assigned directly that aren't 0, 1, or -1 (naive heuristic)
        self.magic_number_pattern = re.compile(r"=\s*(?!0|1|-1)([2-9]|[1-9][0-9]+)\b")
        self.commented_code_pattern = re.compile(r"^\s*(#|//)\s*(if|for|while|def|class|return)\b")

    def scan(self, file_path: str, content: str, ast_data: Dict[str, Any]) -> List[QualityIssue]:
        issues = []
        if not content:
            return issues

        lines = content.split('\\n')
        
        # Line-by-line checks
        for i, line in enumerate(lines):
            line_num = i + 1
            
            if self.todo_pattern.search(line):
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=line_num,
                        rule="todo_comment",
                        severity="low",
                        title="TODO/FIXME Comment found",
                        description="Leftover TODO or FIXME comments indicate incomplete work.",
                        recommendation="Resolve the comment or track it in an issue tracker.",
                        confidence="high"
                    )
                )
                
            if self.commented_code_pattern.search(line):
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=line_num,
                        rule="commented_code",
                        severity="low",
                        title="Commented-out code",
                        description="Code that is commented out clutters the file.",
                        recommendation="Remove commented-out code. Use version control to retain history.",
                        confidence="medium"
                    )
                )

        # AST Missing Docstrings
        language = ast_data.get("language", "unknown").lower()
        if language == "python":
            functions = ast_data.get("functions", [])
            classes = ast_data.get("classes", [])
            
            for func in functions:
                name = func.get("name", "")
                if name.startswith("__") and name != "__init__":
                    continue # Skip private methods
                    
                body = func.get("body", "")
                start_line = func.get("start_point", [0])[0] + 1
                if '"""' not in body and "'''" not in body:
                    issues.append(
                        QualityIssue(
                            file=file_path,
                            line=start_line,
                            rule="missing_docstring_func",
                            severity="low",
                            title="Missing Function Docstring",
                            description=f"Public function '{name}' lacks a docstring.",
                            recommendation="Add a descriptive docstring.",
                            confidence="high"
                        )
                    )
                    
            for cls in classes:
                name = cls.get("name", "")
                body = cls.get("body", "")
                start_line = cls.get("start_point", [0])[0] + 1
                if '"""' not in body and "'''" not in body:
                    issues.append(
                        QualityIssue(
                            file=file_path,
                            line=start_line,
                            rule="missing_docstring_class",
                            severity="low",
                            title="Missing Class Docstring",
                            description=f"Class '{name}' lacks a docstring.",
                            recommendation="Add a descriptive docstring.",
                            confidence="high"
                        )
                    )

        return issues
