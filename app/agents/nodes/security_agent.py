import time
import asyncio
from typing import Dict, Any, List
from app.agents.state import ReviewState
from app.core.logger import logger
from app.services.security.rule_engine import rule_engine
from app.core.github_client import github_client

async def security_agent(state: ReviewState) -> ReviewState:
    logger.info(f"[Node: Security Agent] Started for PR {state['pr_number']}")
    start_time = time.time()
    
    reviewable_files = state.get("reviewable_files", [])
    ast_summaries = state.get("ast_summaries", {})
    
    all_findings = []
    
    owner = state["owner"]
    repo = state["repo"]
    
    # We could parallelize across files, but for clarity we'll iterate
    for f_data in reviewable_files:
        file_path = f_data["file_path"]
        patch = f_data.get("patch", "")
        
        # Try to get raw file content for secret detection
        content = await github_client.get_file_content(owner, repo, file_path, ref="")
        if not content:
            mock_contents = state.get("mock_file_contents", {})
            content = mock_contents.get(file_path, patch)
            
        ast_data = ast_summaries.get(file_path, {})
        
        # Run Rule Engine
        issues = await rule_engine.run_all_checks(file_path, content, patch, ast_data)
        
        for issue in issues:
            all_findings.append(issue.model_dump())
    
    # Sort findings by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_findings.sort(key=lambda x: severity_order.get(x["severity"], 4))
    
    critical_count = sum(1 for f in all_findings if f["severity"] == "critical")
    high_count = sum(1 for f in all_findings if f["severity"] == "high")
    medium_count = sum(1 for f in all_findings if f["severity"] == "medium")
    low_count = sum(1 for f in all_findings if f["severity"] == "low")
    
    total_issues = len(all_findings)
    security_score = max(0, 100 - (critical_count * 20) - (high_count * 10) - (medium_count * 5) - (low_count * 1))
    
    summary = f"Found {total_issues} security issues ({critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low)."
    
    execution_time = time.time() - start_time
    logger.info(f"[Node: Security Agent] {summary}")
    logger.info(f"[Node: Security Agent] Finished in {execution_time:.2f} seconds")
    
    return {
        "security_findings": all_findings,
        "security_summary": summary,
        "security_score": security_score,
        "critical_issue_count": critical_count,
        "current_nodes": ["security_agent"],
        "timing_info": [{"node": "security_agent", "execution_time": execution_time}]
    }
