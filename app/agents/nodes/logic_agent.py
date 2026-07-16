import asyncio
import time

from app.agents.state import ReviewState
from app.core.logger import logger
from app.services.logic.edge_case_detector import edge_case_detector
from app.services.logic.logic_analyzer import logic_analyzer


async def logic_agent(state: ReviewState) -> ReviewState:
    logger.info(f"[Node: Logic Agent] Started for PR {state['pr_number']}")
    start_time = time.time()

    reviewable_files = state.get("reviewable_files", [])
    ast_summaries = state.get("ast_summaries", {})

    state.get("owner", "")
    repo = state.get("repo", "")
    pr_title = state.get("title", "")
    pr_desc = state.get("description", "")

    all_findings = []

    # We execute requests asynchronously, let's collect tasks
    tasks = []

    for f_data in reviewable_files:
        file_path = f_data["file_path"]
        patch = f_data.get("patch", "")

        # Skip files with no patch (not changed)
        if not patch or patch == "dummy":
            continue

        ast_data = ast_summaries.get(file_path, {})
        functions = ast_data.get("functions", [])

        # If no AST functions (e.g. non-code file), we might scan the whole patch
        if not functions:
            context = edge_case_detector.build_context(
                repo=repo,
                pr_title=pr_title,
                pr_desc=pr_desc,
                function_name="Global File Context",
                function_body="",
                patch=patch,
            )
            tasks.append(logic_analyzer.analyze(file_path, context, 1))
        else:
            # Only build context for functions touched by the patch
            # (In a real scenario, we'd check if the function overlaps with the patch line numbers)
            # For simplicity, we'll scan all parsed functions in the changed file
            for func in functions:
                func_name = func.get("name", "anonymous")
                func_body = func.get("body", "")
                start_line = func.get("start_point", [0])[0] + 1

                context = edge_case_detector.build_context(
                    repo=repo,
                    pr_title=pr_title,
                    pr_desc=pr_desc,
                    function_name=func_name,
                    function_body=func_body,
                    patch=patch,
                )
                tasks.append(logic_analyzer.analyze(file_path, context, start_line))

    # Wait for all LLM calls
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Logic Agent async task failed: {res}")
            elif isinstance(res, list):
                all_findings.extend(res)

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

    total_issues = len(final_issues)

    # Simple score calculation
    critical = sum(1 for i in final_issues if i.severity == "critical")
    high = sum(1 for i in final_issues if i.severity == "high")
    medium = sum(1 for i in final_issues if i.severity == "medium")
    low = sum(1 for i in final_issues if i.severity == "low")

    penalty = (critical * 25) + (high * 15) + (medium * 5) + (low * 2)
    logic_score = max(0, 100 - penalty)

    summary = f"Found {total_issues} logic issues. Logic Score: {logic_score}/100."

    execution_time = time.time() - start_time
    logger.info(f"[Node: Logic Agent] {summary}")
    logger.info(f"[Node: Logic Agent] Finished in {execution_time:.2f} seconds")

    return {
        "logic_findings": [f.model_dump() for f in final_issues],
        "logic_summary": summary,
        "logic_score": logic_score,
        "logic_issue_count": total_issues,
        "current_nodes": ["logic_agent"],
        "timing_info": [{"node": "logic_agent", "execution_time": execution_time}],
    }
