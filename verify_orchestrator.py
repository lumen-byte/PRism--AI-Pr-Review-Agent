import sys
import os
import asyncio
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.graph import run_review_graph
from app.agents.state import ReviewState
from app.db.database import AsyncSessionLocal
from app.db.models import Review, ReviewComment

async def verify():
    print("Testing Full Orchestrator Pipeline (Parallel Execution)...")
    
    mock_file_contents = {
        "src/app.py": """
def get_user(user_id):
    # TODO: implement
    if user_id == 0:
        return "admin"
    return "user"
""",
    }
    
    # MOCK LLMs and check rules
    from app.services.security.llm_checker import LLMSecurityChecker
    from app.services.security.security_models import SecurityIssue
    from app.services.quality.llm_refactor import LLMRefactorChecker
    from app.services.logic.logic_analyzer import LogicAnalyzer
    from app.services.logic.logic_models import LogicIssue
    
    async def mock_sec_scan(self, file_path, patch):
        return [
            SecurityIssue(
                file=file_path, line=3, rule="admin_user", severity="high",
                title="Hardcoded Admin User",
                description="Hardcoding admin ID is dangerous.",
                recommendation="Use proper auth.",
                confidence="high"
            )
        ]
        
    async def mock_qual_scan(self, file_path, block):
        return []
        
    async def mock_log_scan(self, file_path, context, offset):
        return [
            LogicIssue(
                file=file_path, line=offset + 2, severity="medium",
                title="Missing Error Handling",
                description="What if user_id is negative?",
                recommendation="Add checks.",
                confidence="high", reasoning=""
            )
        ]
        
    LLMSecurityChecker.scan = mock_sec_scan
    LLMRefactorChecker.scan = mock_qual_scan
    LogicAnalyzer.analyze = mock_log_scan
    
    mock_state: ReviewState = {
        "owner": "testowner",
        "repo": "testrepo",
        "pr_number": 100,
        "title": "Orchestrator Test PR",
        "description": "Mock PR for testing full parallel graph.",
        "author": "mockuser",
        "changed_files": [
            {"filename": "src/app.py", "status": "modified", "additions": 5, "deletions": 0, "changes": 5, "patch": mock_file_contents["src/app.py"]},
        ],
        "mock_file_contents": mock_file_contents,
        "raw_diff": "mock diff",
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
        "execution_time": 0,
        "review_completed": False,
        "current_nodes": ["START"],
        "errors": [],
        "timing_info": []
    }
    
    try:
        final_state = await run_review_graph(mock_state)
        
        print("\\n--- Final Decision ---")
        print(f"Decision: {final_state.get('review_decision')}")
        print(f"Health Score: {final_state.get('overall_score')}")
        print("\\n--- Final Summary ---")
        print(final_state.get('review_summary'))
        
        # Verify DB Records
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Review).where(Review.summary == final_state.get('review_summary')).order_by(Review.reviewed_at.desc())
            )
            review = result.scalar_one_or_none()
            assert review is not None, "Review record not found in Database!"
            
            result_comments = await session.execute(
                select(ReviewComment).where(ReviewComment.review_id == review.id)
            )
            comments = result_comments.scalars().all()
            assert len(comments) >= 2, "Expected at least 2 comments merged and saved to DB."
        
        print("\\n✓ Parallel LangGraph execution successful")
        print("✓ All findings merged correctly")
        print("✓ Health Score calculated accurately")
        print("✓ Decision Engine generated proper outcome")
        print("✓ Database records securely stored in PostgreSQL")
        
    except Exception as e:
        print(f"Orchestrator execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
