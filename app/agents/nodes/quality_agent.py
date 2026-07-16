import time

from app.agents.state import ReviewState
from app.core.github_client import github_client
from app.core.logger import logger
from app.services.quality.code_smell_detector import CodeSmellDetector
from app.services.quality.complexity_analyzer import ComplexityAnalyzer
from app.services.quality.duplication_detector import DuplicationDetector
from app.services.quality.llm_refactor import LLMRefactorChecker
from app.services.quality.metrics import metrics_aggregator
from app.services.quality.naming_checker import NamingChecker

# Initialize once per worker
complexity_analyzer = ComplexityAnalyzer()
naming_checker = NamingChecker()
code_smell_detector = CodeSmellDetector()
duplication_detector = DuplicationDetector()
llm_refactor = LLMRefactorChecker()


async def quality_agent(state: ReviewState) -> ReviewState:
    logger.info(f"[Node: Quality Agent] Started for PR {state['pr_number']}")
    start_time = time.time()

    reviewable_files = state.get("reviewable_files", [])
    ast_summaries = state.get("ast_summaries", {})

    all_findings = []

    owner = state["owner"]
    repo = state["repo"]

    for f_data in reviewable_files:
        file_path = f_data["file_path"]
        patch = f_data.get("patch", "")

        content = await github_client.get_file_content(owner, repo, file_path, ref="")
        if not content:
            mock_contents = state.get("mock_file_contents", {})
            content = mock_contents.get(file_path, patch)

        ast_data = ast_summaries.get(file_path, {})

        # 1. Complexity Analysis
        comp_issues = complexity_analyzer.scan(file_path, ast_data)
        all_findings.extend(comp_issues)

        # 2. Naming Conventions
        name_issues = naming_checker.scan(file_path, ast_data)
        all_findings.extend(name_issues)

        # 3. Code Smells
        smell_issues = code_smell_detector.scan(file_path, content, ast_data)
        all_findings.extend(smell_issues)

        # 4. Duplication Detection
        dup_issues = duplication_detector.scan(file_path, ast_data)
        all_findings.extend(dup_issues)

        # 5. LLM Refactoring (only for highly complex functions)
        for issue in comp_issues:
            if issue.rule in ("high_cyclomatic_complexity", "long_function"):
                # Find the function body
                functions = ast_data.get("functions", [])
                for func in functions:
                    start_line = func.get("start_point", [0])[0] + 1
                    if start_line == issue.line:
                        llm_issues = await llm_refactor.scan(
                            file_path,
                            func.get("name", ""),
                            func.get("body", ""),
                            start_line,
                        )
                        all_findings.extend(llm_issues)
                        break

    # Deduplicate issues
    unique_issues = {}
    for issue in all_findings:
        h = issue.get_hash()
        if h not in unique_issues:
            unique_issues[h] = issue

    final_issues = list(unique_issues.values())

    # Sort findings by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    final_issues.sort(key=lambda x: severity_order.get(x.severity, 4))

    # Calculate Metrics
    aggregated = metrics_aggregator.calculate_scores(final_issues, ast_summaries)

    total_issues = len(final_issues)
    quality_score = aggregated["quality_score"]

    summary = (
        f"Found {total_issues} quality issues. Quality Score: {quality_score}/100."
    )

    execution_time = time.time() - start_time
    logger.info(f"[Node: Quality Agent] {summary}")
    logger.info(f"[Node: Quality Agent] Finished in {execution_time:.2f} seconds")

    return {
        "quality_findings": [f.model_dump() for f in final_issues],
        "quality_summary": summary,
        "quality_score": quality_score,
        "maintainability_metrics": aggregated["maintainability_metrics"],
        "complexity_metrics": aggregated["complexity_metrics"],
        "current_nodes": ["quality_agent"],
        "timing_info": [{"node": "quality_agent", "execution_time": execution_time}],
    }
