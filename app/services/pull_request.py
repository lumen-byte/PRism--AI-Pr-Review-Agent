from app.core.github_client import github_client
from app.core.logger import logger
from app.agents.graph import run_review_graph
from app.agents.state import ReviewState
from app.cache.redis_client import redis_client

async def process_pull_request(owner: str, repo: str, pr_number: int) -> None:
    """
    Background task to process a Pull Request.
    Currently fetches metadata, changed files, and diff.
    """
    logger.info(f"Starting background processing for PR {pr_number} in {owner}/{repo}")
    # 1. Acquire Lock
    has_lock = await redis_client.acquire_pr_lock(repo, pr_number)
    if not has_lock:
        logger.info(f"Skipping PR {pr_number} in {owner}/{repo}: already being processed")
        return
        
    await redis_client.set_pr_status(repo, pr_number, "RUNNING")
    
    try:
        # 2. Fetch PR Metadata
        pr_metadata = await github_client.get_pull_request(owner, repo, pr_number)
        if not pr_metadata:
            logger.error(f"Failed to fetch PR metadata for {owner}/{repo}#{pr_number}")
            return
            
        logger.info(f"Successfully fetched PR {pr_metadata.pr_number} - {pr_metadata.title} by {pr_metadata.author}")
        
        # 2. Fetch Changed Files
        changed_files = await github_client.get_pull_request_files(owner, repo, pr_number)
        logger.info(f"Fetched {len(changed_files)} changed files for PR {pr_number}")
        for file in changed_files:
            logger.info(f"File changed: {file.filename} ({file.status}) - +{file.additions} -{file.deletions}")
            
        # 3. Fetch Diff
        diff = await github_client.get_pull_request_diff(owner, repo, pr_number)
        if diff:
            logger.info(f"Successfully fetched diff for PR {pr_number}, size: {len(diff)} bytes")
        else:
            logger.warning(f"No diff found or failed to fetch diff for PR {pr_number}")
            
        # 4. Construct Initial State and Run Graph
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
            "current_node": "START",
            "errors": [],
            "timing_info": []
        }
    
        logger.info(f"Triggering Review Graph for PR {pr_number}")
        final_state = await run_review_graph(initial_state)
        logger.info(f"Graph Execution Final State Node: {final_state.get('current_nodes')}")
        
        await redis_client.set_pr_status(repo, pr_number, "COMPLETED")
        logger.info(f"Finished background processing for PR {pr_number} in {owner}/{repo}")
        
    except Exception as e:
        logger.error(f"Failed processing PR {pr_number} in {owner}/{repo}: {e}")
        await redis_client.set_pr_status(repo, pr_number, "FAILED")
    finally:
        await redis_client.release_pr_lock(repo, pr_number)
