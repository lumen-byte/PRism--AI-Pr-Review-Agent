import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, update
from app.agents.state import ReviewState
from app.core.logger import logger
from app.core.github_client import github_client
from app.db.database import AsyncSessionLocal
from app.db.models import Review, ReviewDecision
from app.services.review.review_models import MergedIssue
from app.services.github_review.github_mapper import github_mapper
from app.services.github_review.comment_formatter import comment_formatter

class ReviewPublisher:
    def __init__(self):
        pass

    async def publish(self, state: ReviewState, issues: List[MergedIssue]) -> bool:
        owner = state.get("owner")
        repo = state.get("repo")
        pr_number = state.get("pr_number")
        
        if not owner or not repo or not pr_number:
            logger.error("[Review Publisher] Missing PR details.")
            return False

        summary = state.get("review_summary", "Review complete.")
        decision_str = state.get("review_decision", "COMMENTED")
        
        event_map = {
            "APPROVED": "APPROVE",
            "CHANGES_REQUESTED": "REQUEST_CHANGES",
            "COMMENTED": "COMMENT",
            "NEEDS_DISCUSSION": "COMMENT"
        }
        event = event_map.get(decision_str, "COMMENT")
        
        # Build comments payload
        comments_payload = []
        changed_files = {f["filename"]: f for f in state.get("changed_files", [])}
        
        for issue in issues:
            file_data = changed_files.get(issue.file)
            if not file_data or "patch" not in file_data:
                continue
                
            position = github_mapper.map_line_to_position(file_data["patch"], issue.line)
            if position is None:
                logger.warning(f"[Review Publisher] Could not map line {issue.line} in {issue.file} to diff position.")
                continue
                
            body = comment_formatter.format_inline_comment(issue)
            comments_payload.append({
                "path": issue.file,
                "position": position,
                "body": body
            })
            
        logger.info(f"[Review Publisher] Submitting review with {len(comments_payload)} inline comments...")
        
        # We retry transient failures up to 3 times
        max_retries = 3
        review_id = None
        
        for attempt in range(max_retries):
            review_id = await github_client.create_review(
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                body=summary,
                event=event,
                comments=comments_payload
            )
            if review_id:
                break
            logger.warning(f"[Review Publisher] Attempt {attempt + 1} failed. Retrying...")
            await asyncio.sleep(2 ** attempt)
            
        # Update Database
        async with AsyncSessionLocal() as session:
            try:
                # Find the most recent review for this PR summary
                result = await session.execute(
                    select(Review).where(Review.summary == summary).order_by(Review.reviewed_at.desc()).limit(1)
                )
                review = result.scalar_one_or_none()
                if review:
                    review.github_review_id = str(review_id) if review_id else None
                    review.publishing_status = "PUBLISHED" if review_id else "FAILED"
                    review.publishing_timestamp = datetime.utcnow()
                    review.retry_count = attempt + 1 if not review_id else attempt
                    await session.commit()
            except Exception as e:
                logger.error(f"[Review Publisher] DB update failed: {e}")
                
        return review_id is not None

review_publisher = ReviewPublisher()
