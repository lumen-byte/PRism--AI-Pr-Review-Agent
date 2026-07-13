from typing import List, Dict, Any
from app.services.quality.quality_models import QualityIssue

class MetricsAggregator:
    def __init__(self):
        pass

    def calculate_scores(self, issues: List[QualityIssue], ast_summaries: Dict[str, Any]) -> Dict[str, Any]:
        critical = sum(1 for i in issues if i.severity == "critical")
        high = sum(1 for i in issues if i.severity == "high")
        medium = sum(1 for i in issues if i.severity == "medium")
        low = sum(1 for i in issues if i.severity == "low")

        # Baseline score
        base_score = 100
        penalty = (critical * 20) + (high * 10) + (medium * 5) + (low * 1)
        quality_score = max(0, base_score - penalty)

        # Average complexity across all files
        total_complexity = 0
        total_functions = 0
        total_lines = 0

        for file_path, ast_data in ast_summaries.items():
            summary = ast_data.get("summary", {})
            if isinstance(summary, dict):
                total_functions += summary.get("function_count", 0)
                total_lines += summary.get("total_lines", 0)
                # Roughly estimate complexity from AST summary (if we had it, otherwise base it on issues)
                # Here we just use the issues as a proxy for bad complexity
                
        # Maintainability metrics
        maintainability_score = max(0, 100 - (high * 5) - (medium * 2))
        
        # Complexity metrics
        complexity_metrics = {
            "total_functions": total_functions,
            "total_lines": total_lines,
            "complexity_issues": len([i for i in issues if 'complexity' in i.rule or 'length' in i.rule])
        }

        return {
            "quality_score": quality_score,
            "maintainability_metrics": {
                "maintainability_score": maintainability_score,
                "smells_detected": len(issues)
            },
            "complexity_metrics": complexity_metrics
        }

metrics_aggregator = MetricsAggregator()
