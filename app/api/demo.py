import asyncio
import json
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.graph import run_review_graph
from app.agents.state import ReviewState
from app.core.logger import logger
from app.demo.sample_pull_requests import SCENARIOS

router = APIRouter()

class DemoRunRequest(BaseModel):
    scenario: str

async def execute_demo_pipeline(scenario_name: str, pr_number: int):
    scenario = SCENARIOS.get(scenario_name)
    if not scenario:
        logger.error(f"[Demo Run] Invalid scenario: {scenario_name}")
        return

    # Construct the state directly
    initial_state: ReviewState = {
        "owner": scenario["owner"],
        "repo": scenario["repo"],
        "pr_number": pr_number,
        "title": scenario["title"],
        "description": scenario.get("description", ""),
        "author": scenario["author"],
        "changed_files": scenario["changed_files"],
        "raw_diff": scenario["raw_diff"],
        "mock_file_contents": scenario["mock_file_contents"],
        "parsed_files": [],
        "reviewable_files": [],
        "ignored_files": [],
        "diff_statistics": {},
        "language_breakdown": {},
        "ast_summaries": {},
        "security_findings": [],
        "security_summary": "",
        "security_score": 100,
        "critical_issue_count": 0,
        "quality_findings": [],
        "quality_summary": "",
        "quality_score": 100,
        "maintainability_metrics": {},
        "complexity_metrics": {},
        "logic_findings": [],
        "logic_summary": "",
        "logic_score": 100,
        "logic_issue_count": 0,
        "review_summary": "",
        "review_decision": "",
        "health_score": 100,
        "overall_score": 100,
        "current_nodes": ["START"],
        "execution_time": 0,
        "review_completed": False,
        "errors": [],
        "timing_info": [],
        "demo_mode": True,
    }

    logger.info(
        f"[Demo Run] Starting pipeline for scenario {scenario_name} (PR {pr_number})"
    )
    await run_review_graph(initial_state)
    logger.info(
        f"[Demo Run] Completed pipeline for scenario {scenario_name} (PR {pr_number})"
    )

@router.post("/run")
async def run_demo(payload: DemoRunRequest, background_tasks: BackgroundTasks):
    scenario_name = payload.scenario.lower()
    if scenario_name not in SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Choose from: {list(SCENARIOS.keys())}",
        )

    import random
    pr_number = random.randint(1000, 9999)
    background_tasks.add_task(execute_demo_pipeline, scenario_name, pr_number)

    return {
        "status": "queued",
        "scenario": scenario_name,
        "pr_number": pr_number,
        "message": f"Demo run queued successfully for PR #{pr_number}.",
    }

async def demo_event_generator():
    events = [
        # PR Fetcher Agent
        {"agent": "PR Fetcher", "status": "Running", "message": "Analyzing pull request...", "type": "info"},
        {"agent": "PR Fetcher", "status": "Running", "message": "3 files changed", "type": "info"},
        {"agent": "PR Fetcher", "status": "Running", "message": "47 insertions", "type": "info"},
        {"agent": "PR Fetcher", "status": "Running", "message": "Parsing repository...", "type": "info"},
        {"agent": "PR Fetcher", "status": "Running", "message": "Language detected: Python", "type": "info"},
        {"agent": "PR Fetcher", "status": "Running", "message": "Building Tree-sitter AST...", "type": "info"},
        {"agent": "PR Fetcher", "status": "Completed", "message": "Finished", "type": "done"},
        
        # Security Agent
        {"agent": "Security Agent", "status": "Running", "message": "Scanning credentials...", "type": "info"},
        {"agent": "Security Agent", "status": "Running", "message": "Scanning secrets...", "type": "info"},
        {"agent": "Security Agent", "status": "Running", "message": "Hardcoded API key detected", "type": "alert", "highlight": "config.py"},
        {"agent": "Security Agent", "status": "Running", "message": "config.py", "type": "alert"},
        {"agent": "Security Agent", "status": "Running", "message": "Line 23", "type": "alert"},
        {"agent": "Security Agent", "status": "Running", "message": "Severity:", "type": "alert"},
        {"agent": "Security Agent", "status": "Issue Found", "message": "Critical", "type": "critical"},
        
        # Code Quality Agent
        {"agent": "Code Quality Agent", "status": "Running", "message": "Checking complexity...", "type": "info"},
        {"agent": "Code Quality Agent", "status": "Running", "message": "Function process_payment()", "type": "warning", "highlight": "process_payment"},
        {"agent": "Code Quality Agent", "status": "Running", "message": "84 lines detected", "type": "warning"},
        {"agent": "Code Quality Agent", "status": "Running", "message": "Unused import detected", "type": "warning"},
        {"agent": "Code Quality Agent", "status": "Running", "message": "datetime", "type": "warning"},
        {"agent": "Code Quality Agent", "status": "Issue Found", "message": "Line 3", "type": "warning"},
        
        # Logic Agent
        {"agent": "Logic Agent", "status": "Running", "message": "Analyzing control flow...", "type": "info"},
        {"agent": "Logic Agent", "status": "Running", "message": "Potential null reference detected", "type": "warning", "highlight": "account.balance"},
        {"agent": "Logic Agent", "status": "Running", "message": "user.account", "type": "warning"},
        {"agent": "Logic Agent", "status": "Issue Found", "message": "Line 67", "type": "warning"},
        
        # Review Orchestrator
        {"agent": "Review Orchestrator", "status": "Running", "message": "Collecting findings...", "type": "info"},
        {"agent": "Review Orchestrator", "status": "Running", "message": "Ranking issues...", "type": "info"},
        {"agent": "Review Orchestrator", "status": "Running", "message": "Preparing GitHub review...", "type": "info"},
        {"agent": "Review Orchestrator", "status": "Running", "message": "Generating summary...", "type": "info"},
        {"agent": "Review Orchestrator", "status": "Completed", "message": "Finished", "type": "done", "final_summary": True}
    ]
    
    for event in events:
        # Simulate delay 800ms - 1200ms
        import random
        delay = random.uniform(0.8, 1.2)
        await asyncio.sleep(delay)
        yield f"data: {json.dumps(event)}\n\n"

@router.get("/stream")
async def stream_demo():
    return StreamingResponse(demo_event_generator(), media_type="text/event-stream")
