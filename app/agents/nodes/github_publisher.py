import time
from typing import Dict, Any, List
from app.agents.state import ReviewState
from app.core.logger import logger
from app.services.review.review_models import MergedIssue
from app.services.github_review.review_publisher import review_publisher
from app.db.models import Severity as DBSeverity

async def github_publisher(state: ReviewState) -> ReviewState:
    logger.info(f"[Node: GitHub Publisher] Started for PR {state.get('pr_number')}")
    start_time = time.time()
    
    # 1. Re-construct merged issues from state findings
    sec_findings = state.get("security_findings", [])
    qual_findings = state.get("quality_findings", [])
    log_findings = state.get("logic_findings", [])
    
    merged_map: Dict[str, MergedIssue] = {}
    
    def add_to_merged(findings: List[Dict[str, Any]], category: str):
        for f in findings:
            sev_str = f.get("severity", "info").upper()
            try:
                sev_enum = DBSeverity(sev_str)
            except ValueError:
                sev_enum = DBSeverity.INFO
                
            issue = MergedIssue(
                file=f.get("file", f.get("filename", "unknown")),
                line=f.get("line", 0),
                severity=sev_enum,
                title=f.get("title", f.get("rule", "Issue")),
                description=f.get("description", f.get("message", "No description")),
                category=category
            )
            h = issue.get_hash()
            if h not in merged_map:
                merged_map[h] = issue

    add_to_merged(sec_findings, "security")
    add_to_merged(qual_findings, "quality")
    add_to_merged(log_findings, "logic")
    
    merged_list = list(merged_map.values())
    
    # 2. Publish to GitHub
    success = await review_publisher.publish(state, merged_list)
    
    if not success:
        logger.error(f"[Node: GitHub Publisher] Failed to publish review for PR {state.get('pr_number')}")
        state.setdefault("errors", []).append("Failed to publish to GitHub")
    else:
        logger.info(f"[Node: GitHub Publisher] Successfully published review to GitHub.")
        
    execution_time = time.time() - start_time
    logger.info(f"[Node: GitHub Publisher] Finished in {execution_time:.2f} seconds.")
    
    return {
        "current_nodes": ["github_publisher"],
        "timing_info": [{"node": "github_publisher", "execution_time": execution_time}]
    }
