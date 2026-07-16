from typing import Any, Dict, List

from app.services.quality.quality_models import QualityIssue


class NamingChecker:
    def __init__(self):
        pass

    def scan(self, file_path: str, ast_data: Dict[str, Any]) -> List[QualityIssue]:
        issues = []
        if not ast_data:
            return issues

        functions = ast_data.get("functions", [])
        classes = ast_data.get("classes", [])

        for func in functions:
            name = func.get("name", "")
            start_line = func.get("start_point", [0])[0] + 1
            if name and len(name) <= 2 and name not in ("id", "db", "op", "io"):
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=start_line,
                        rule="short_function_name",
                        severity="low",
                        title="Function name is too short",
                        description=f"The function name '{name}' is non-descriptive.",
                        recommendation="Use a descriptive, action-oriented name.",
                        confidence="high",
                    )
                )

        for cls in classes:
            name = cls.get("name", "")
            start_line = cls.get("start_point", [0])[0] + 1
            if name and len(name) <= 2:
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=start_line,
                        rule="short_class_name",
                        severity="medium",
                        title="Class name is too short",
                        description=f"The class name '{name}' is non-descriptive.",
                        recommendation="Use a descriptive noun phrase for class names.",
                        confidence="high",
                    )
                )

            # Check class name capitalization
            if name and not name[0].isupper():
                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=start_line,
                        rule="class_naming_convention",
                        severity="low",
                        title="Invalid Class Naming Convention",
                        description=f"Class '{name}' should use PascalCase/CamelCase.",
                        recommendation="Capitalize the first letter of the class name.",
                        confidence="medium",
                    )
                )

        return issues
