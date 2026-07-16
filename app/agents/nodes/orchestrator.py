import time
from typing import Any, Dict, List

from sqlalchemy import select

from app.agents.state import ReviewState
from app.core.logger import logger
from app.db.database import AsyncSessionLocal
from app.db.models import (
    CommentType,
    PRStatus,
    PullRequest,
    Repository,
    Review,
    ReviewComment,
)
from app.db.models import Severity as DBSeverity
from app.services.review.decision_engine import decision_engine
from app.services.review.health_score import health_score_calculator
from app.services.review.review_models import MergedIssue
from app.services.review.summary_generator import summary_generator


async def orchestrator(state: ReviewState) -> ReviewState:
    logger.info(f"[Node: Orchestrator] Started for PR {state.get('pr_number')}")
    start_time = time.time()

    # 1. Collect all findings
    sec_findings = state.get("security_findings", [])
    qual_findings = state.get("quality_findings", [])
    log_findings = state.get("logic_findings", [])

    merged_map: Dict[str, MergedIssue] = {}

    # Mapper helper
    def add_to_merged(findings: List[Dict[str, Any]], category: str):
        for f in findings:
            # Map string severity to enum if needed, assuming they are lower/upper case strings
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
                category=category,
            )
            h = issue.get_hash()
            if h not in merged_map:
                merged_map[h] = issue

    add_to_merged(sec_findings, "security")
    add_to_merged(qual_findings, "quality")
    add_to_merged(log_findings, "logic")

    merged_list = list(merged_map.values())

    # Sort
    severity_order = {
        DBSeverity.CRITICAL: 0,
        DBSeverity.ERROR: 1,
        DBSeverity.WARNING: 2,
        DBSeverity.INFO: 3,
    }
    merged_list.sort(key=lambda x: severity_order.get(x.severity, 4))

    # 2. Calculate Health Score
    health_score = health_score_calculator.calculate(merged_list)

    # 3. Decide
    decision = decision_engine.decide(health_score, merged_list)

    # 4. Generate Summary
    summary = summary_generator.generate(decision, health_score, merged_list)

    # 5. Database Persistence
    owner = state.get("owner", "unknown")
    repo_name = state.get("repo", "unknown")
    pr_number = state.get("pr_number", 0)

    async with AsyncSessionLocal() as session:
        try:
            # Upsert Repository
            repo_query = await session.execute(
                select(Repository).where(
                    Repository.owner == owner, Repository.repo_name == repo_name
                )
            )
            repository = repo_query.scalar_one_or_none()
            if not repository:
                repository = Repository(
                    repo_url=f"https://github.com/{owner}/{repo_name}",
                    repo_name=repo_name,
                    owner=owner,
                )
                session.add(repository)
                await session.flush()

            # Upsert PullRequest
            pr_query = await session.execute(
                select(PullRequest).where(
                    PullRequest.repository_id == repository.id,
                    PullRequest.pr_number == pr_number,
                )
            )
            pull_request = pr_query.scalar_one_or_none()
            if not pull_request:
                pull_request = PullRequest(
                    repository_id=repository.id,
                    pr_number=pr_number,
                    title=state.get("title", "Untitled"),
                    author=state.get("author", "Unknown"),
                    base_branch="main",  # mock or extract
                    head_branch="feature",  # mock or extract
                    pr_url=f"https://github.com/{owner}/{repo_name}/pull/{pr_number}",
                    status=PRStatus.OPEN,
                )
                session.add(pull_request)
                await session.flush()

            # Create Review
            review = Review(
                pr_id=pull_request.id,
                health_score=health_score,
                decision=decision,
                summary=summary,
                security_count=len(
                    [i for i in merged_list if i.category == "security"]
                ),
                quality_count=len([i for i in merged_list if i.category == "quality"]),
                logic_count=len([i for i in merged_list if i.category == "logic"]),
                agent_version="1.0.0",
            )
            session.add(review)
            await session.flush()

            # Create Comments
            comments_to_add = []
            for issue in merged_list:
                ctype = (
                    CommentType.SECURITY
                    if issue.category == "security"
                    else CommentType.BUG
                    if issue.category == "logic"
                    else CommentType.STYLE
                )
                comments_to_add.append(
                    ReviewComment(
                        review_id=review.id,
                        file_path=issue.file,
                        line_number=issue.line,
                        comment_type=ctype,
                        severity=issue.severity,
                        comment_text=f"**{issue.title}**\\n{issue.description}",
                    )
                )
            if comments_to_add:
                session.add_all(comments_to_add)

            await session.commit()
            logger.info(
                f"[Node: Orchestrator] Saved {len(merged_list)} comments to database."
            )

        except Exception as e:
            await session.rollback()
            logger.error(f"[Node: Orchestrator] Database save failed: {e}")
            state.setdefault("errors", []).append(f"DB Error: {e}")

    execution_time = time.time() - start_time
    logger.info(
        f"[Node: Orchestrator] Finished in {execution_time:.2f} seconds. Decision: {decision.name}, Score: {health_score}"
    )

    return {
        "review_summary": summary,
        "review_decision": decision.name,
        "overall_score": health_score,
        "health_score": health_score,
        "current_nodes": ["orchestrator"],
        "review_completed": True,
        "timing_info": [{"node": "orchestrator", "execution_time": execution_time}],
    }
