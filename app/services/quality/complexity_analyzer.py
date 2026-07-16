import re
from typing import Any, Dict, List

from app.services.quality.quality_models import QualityIssue


class ComplexityAnalyzer:
    def __init__(self):
        self.max_function_length = 40
        self.max_class_length = 200
        self.max_cyclomatic_complexity = 10
        self.max_return_count = 3
        self.max_parameters = 5
        self.max_branches = 8

    def scan(self, file_path: str, ast_data: Dict[str, Any]) -> List[QualityIssue]:
        issues = []
        if not ast_data:
            return issues

        functions = ast_data.get("functions", [])
        classes = ast_data.get("classes", [])

        # Analyze Functions
        for func in functions:
            name = func.get("name", "anonymous")
            start_line = func.get("start_point", [0])[0] + 1
            body = func.get("body", "")
            lines = body.split("\\n")
            length = len(lines)

            # Function Length
            if length > self.max_function_length:
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=start_line,
                        rule="long_function",
                        severity="high",
                        title="Function is too long",
                        description=f"Function '{name}' is {length} lines long, exceeding the limit of {self.max_function_length}.",
                        recommendation="Break the function down into smaller, focused helper methods.",
                        confidence="high",
                    )
                )

            # Return Count
            return_count = len(re.findall(r"\breturn\b", body))
            if return_count > self.max_return_count:
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=start_line,
                        rule="high_return_count",
                        severity="medium",
                        title="Too many return statements",
                        description=f"Function '{name}' has {return_count} return statements.",
                        recommendation="Refactor the logic to have a more unified exit path or extract early returns into separate functions.",
                        confidence="high",
                    )
                )

            # Cyclomatic Complexity Approximation
            branches = len(re.findall(r"\b(if|elif|else|for|while|case|catch)\b", body))
            complexity = 1 + branches
            if complexity > self.max_cyclomatic_complexity:
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=start_line,
                        rule="high_cyclomatic_complexity",
                        severity="high",
                        title="High Cyclomatic Complexity",
                        description=f"Function '{name}' has an estimated cyclomatic complexity of {complexity}.",
                        recommendation="Simplify the logic, avoid deep nesting, and extract complex conditional blocks.",
                        confidence="medium",
                    )
                )

            # Parameters Check (approximate by searching first line)
            if lines:
                first_line = lines[0]
                if "(" in first_line and ")" in first_line:
                    params_str = first_line[
                        first_line.find("(") + 1 : first_line.find(")")
                    ]
                    params = [
                        p
                        for p in params_str.split(",")
                        if p.strip() and p.strip() != "self"
                    ]
                    if len(params) > self.max_parameters:
                        issues.append(
                            QualityIssue(
                                file=file_path,
                                line=start_line,
                                rule="too_many_parameters",
                                severity="medium",
                                title="Too many function parameters",
                                description=f"Function '{name}' has {len(params)} parameters.",
                                recommendation="Consider grouping related parameters into a configuration object or dataclass.",
                                confidence="low",
                            )
                        )

        # Analyze Classes
        for cls in classes:
            name = cls.get("name", "anonymous")
            start_line = cls.get("start_point", [0])[0] + 1
            body = cls.get("body", "")
            length = len(body.split("\\n"))

            if length > self.max_class_length:
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=start_line,
                        rule="long_class",
                        severity="high",
                        title="Class is too long",
                        description=f"Class '{name}' is {length} lines long.",
                        recommendation="Refactor into smaller classes with single responsibilities.",
                        confidence="high",
                    )
                )

        return issues
