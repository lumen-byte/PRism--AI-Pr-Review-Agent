import asyncio
import json
import time
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.graph import review_graph
from app.agents.state import ReviewState
from app.core.github_client import github_client
from app.core.logger import logger
from app.db.database import get_db
from app.db.models import PullRequest, Review, ReviewDecision, PRStatus, Repository

router = APIRouter()

async def live_review_generator(repo_url: str, pr_number: int | None):
    # Setup state
    owner = ""
    repo = ""
    try:
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1]
        else:
            raise ValueError("Invalid GitHub URL")
    except Exception as e:
        yield f"data: {json.dumps({'agent': 'PR Fetcher', 'status': 'Error', 'message': f'Invalid repository URL.', 'type': 'critical'})}\n\n"
        return

    yield f"data: {json.dumps({'agent': 'PR Fetcher', 'status': 'Running', 'message': f'Analyzing repository {owner}/{repo}...', 'type': 'info'})}\n\n"
    
    # 1. Resolve PR Number
    if not pr_number:
        yield f"data: {json.dumps({'agent': 'PR Fetcher', 'status': 'Running', 'message': 'Finding latest open PR...', 'type': 'info'})}\n\n"
        pr_number = await github_client.get_latest_pull_request(owner, repo)
        if not pr_number:
            yield f"data: {json.dumps({'agent': 'PR Fetcher', 'status': 'Error', 'message': 'No open pull requests found.', 'type': 'critical'})}\n\n"
            return
            
    yield f"data: {json.dumps({'agent': 'PR Fetcher', 'status': 'Running', 'message': f'Found PR #{pr_number}. Fetching metadata...', 'type': 'info'})}\n\n"

    # 2. Fetch Metadata
    pr_metadata = await github_client.get_pull_request(owner, repo, pr_number)
    if not pr_metadata:
        yield f"data: {json.dumps({'agent': 'PR Fetcher', 'status': 'Error', 'message': f'Could not fetch metadata for PR #{pr_number}. Private repo or invalid PR?', 'type': 'critical'})}\n\n"
        return

    # 3. Fetch Files
    yield f"data: {json.dumps({'agent': 'PR Fetcher', 'status': 'Running', 'message': 'Downloading PR diff...', 'type': 'info'})}\n\n"
    changed_files = await github_client.get_pull_request_files(owner, repo, pr_number)
    diff = await github_client.get_pull_request_diff(owner, repo, pr_number)
    
    yield f"data: {json.dumps({'agent': 'PR Fetcher', 'status': 'Running', 'message': f'{len(changed_files)} files changed.', 'type': 'info'})}\n\n"
    yield f"data: {json.dumps({'agent': 'PR Fetcher', 'status': 'Completed', 'message': 'Finished', 'type': 'done'})}\n\n"

    # 4. Construct Initial State
    initial_state: ReviewState = {
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "title": pr_metadata.title,
        "author": pr_metadata.author,
        "changed_files": [f.model_dump() for f in changed_files],
        "raw_diff": diff or "",
        "security_findings": [],
        "quality_findings": [],
        "logic_findings": [],
        "review_summary": "",
        "review_decision": "",
        "health_score": 100,
        "current_nodes": ["START"],
        "errors": [],
        "timing_info": [],
    }

    start_time = time.time()
    
    node_name_mapping = {
        "diff_analyzer": "PR Fetcher",
        "security_agent": "Security Agent",
        "quality_agent": "Code Quality Agent",
        "logic_agent": "Logic Agent",
        "orchestrator": "Review Orchestrator",
        "github_publisher": "GitHub Publisher",
    }
    
    # 5. Run Graph with astream_events
    final_state = None
    try:
        async for event in review_graph.astream_events(initial_state, version="v1"):
            kind = event["event"]
            node_name = event["name"]
            
            if node_name not in node_name_mapping:
                continue
                
            agent_label = node_name_mapping[node_name]
            
            if kind == "on_chain_start":
                yield f"data: {json.dumps({'agent': agent_label, 'status': 'Running', 'message': f'Analyzing...', 'type': 'info'})}\n\n"
            
            elif kind == "on_chain_end":
                data = event.get("data", {})
                output = data.get("output", {})
                if output and isinstance(output, dict) and "current_nodes" in output:
                    final_state = output
                
                findings = []
                if node_name == "security_agent" and isinstance(output, dict) and "security_findings" in output:
                    findings = output["security_findings"]
                elif node_name == "quality_agent" and isinstance(output, dict) and "quality_findings" in output:
                    findings = output["quality_findings"]
                elif node_name == "logic_agent" and isinstance(output, dict) and "logic_findings" in output:
                    findings = output["logic_findings"]
                
                if findings:
                    # In real app we might stream individual findings here. We'll summarize for SSE UI.
                    for finding in findings[:3]: # Stream top 3 findings visually
                        msg = finding.get("description", "Issue detected")
                        severity = finding.get("severity", "WARNING").lower()
                        alert_type = "critical" if severity == "critical" else "warning"
                        yield f"data: {json.dumps({'agent': agent_label, 'status': 'Running', 'message': msg, 'type': alert_type})}\n\n"
                        # Short delay for visual effect
                        await asyncio.sleep(0.3)
                    
                    yield f"data: {json.dumps({'agent': agent_label, 'status': 'Issue Found', 'message': f'Found {len(findings)} issues.', 'type': 'warning', 'html_comment': '<ul>' + ''.join(f'<li>{f.get(\\'description\\')}</li>' for f in findings) + '</ul>'})}\n\n"
                else:
                    if node_name != "github_publisher":
                        yield f"data: {json.dumps({'agent': agent_label, 'status': 'Completed', 'message': 'Clean.', 'type': 'done'})}\n\n"
                
    except Exception as e:
        logger.error(f"Error streaming live review: {e}")
        yield f"data: {json.dumps({'agent': 'Review Orchestrator', 'status': 'Error', 'message': f'Pipeline failed: {str(e)}', 'type': 'critical'})}\n\n"
        return

    duration = time.time() - start_time
    
    if final_state:
        metrics = {
            "critical": sum(1 for f in final_state.get("security_findings", []) if f.get("severity") == "CRITICAL"),
            "warnings": len(final_state.get("quality_findings", [])) + len(final_state.get("logic_findings", [])),
            "files": len(changed_files),
            "languages": "Multiple",
            "time": f"{duration:.1f} sec",
            "health": f"{final_state.get('health_score', 0)}/100",
            "decision": final_state.get("review_decision", "COMMENTED")
        }
        
        yield f"data: {json.dumps({'agent': 'Review Orchestrator', 'status': 'Completed', 'message': 'Finished', 'type': 'done', 'final_summary': True, 'metrics': metrics})}\n\n"

@router.get("/stream")
async def stream_live_review(
    repo_url: str = Query(..., description="GitHub repository URL"),
    pr_number: int | None = Query(None, description="Optional PR number. If omitted, uses latest open PR.")
):
    """
    Streams a live LangGraph review of a public GitHub repository.
    """
    return StreamingResponse(live_review_generator(repo_url, pr_number), media_type="text/event-stream")


@router.get("/history")
async def get_live_history(db: AsyncSession = Depends(get_db)):
    """
    Returns the latest 10 reviews from the database.
    """
    stmt = (
        select(Review, PullRequest, Repository)
        .join(PullRequest, Review.pr_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .order_by(Review.reviewed_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    history = []
    for review, pr, repo in rows:
        history.append({
            "id": str(review.id),
            "repo": f"{repo.owner}/{repo.repo_name}",
            "pr_number": pr.pr_number,
            "decision": review.decision,
            "health_score": review.health_score,
            "timestamp": review.reviewed_at.isoformat()
        })
    return {"history": history}
