from fastapi import APIRouter, BackgroundTasks, HTTPException
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

    # Generate a unique PR number to avoid conflicts
    # Let's generate a random integer or use timestamp
    import random

    pr_number = random.randint(1000, 9999)

    # We run the pipeline in a background task so the API returns immediately
    background_tasks.add_task(execute_demo_pipeline, scenario_name, pr_number)

    return {
        "status": "queued",
        "scenario": scenario_name,
        "pr_number": pr_number,
        "message": f"Demo run queued successfully for PR #{pr_number}.",
    }
