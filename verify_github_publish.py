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
    print("Testing GitHub Review Publishing...")
    
    mock_file_contents = {
        "src/app.py": """
def get_user(user_id):
    # TODO: implement
    if user_id == 0:
        return "admin"
    return "user"
""",
    }
    
    mock_patch = """@@ -1,4 +1,6 @@
 def get_user(user_id):
     # TODO: implement
+    if user_id == 0:
+        return "admin"
     return "user"
"""
    
    # 1. Test the Mapper manually first
    from app.services.github_review.github_mapper import github_mapper
    # line 3 is `if user_id == 0:`
    pos = github_mapper.map_line_to_position(mock_patch, 3)
    print(f"Mapper output for line 3: {pos}")
    assert pos == 4, f"Expected position 4, got {pos}"
    
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
    
    # Mock GitHubClient
    from app.services.github_review.review_publisher import review_publisher
    from app.core.github_client import github_client
    
    publish_payloads = []
    
    async def mock_create_review(owner, repo, pr_number, body, event, comments=None):
        publish_payloads.append({
            "owner": owner, "repo": repo, "pr_number": pr_number,
            "body": body, "event": event, "comments": comments
        })
        return 99999  # Mock review ID
        
    github_client.create_review = mock_create_review
    
    mock_state: ReviewState = {
        "owner": "testowner",
        "repo": "testrepo",
        "pr_number": 100,
        "title": "Orchestrator Test PR",
        "description": "Mock PR for testing full parallel graph.",
        "author": "mockuser",
        "changed_files": [
            {"filename": "src/app.py", "status": "modified", "additions": 5, "deletions": 0, "changes": 5, "patch": mock_patch},
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
        
        print("\\n--- GitHub Publisher Results ---")
        assert len(publish_payloads) == 1, "Expected 1 review submission to GitHub."
        payload = publish_payloads[0]
        
        print(f"Event: {payload['event']}")
        print(f"Comments Sent: {len(payload['comments'])}")
        
        assert payload['event'] == 'APPROVE', "Expected APPROVE based on health score."
        assert len(payload['comments']) == 4, "Expected 4 inline comments."
        
        # Check that the DB was updated with the mock ID 99999
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Review).where(Review.github_review_id == "99999").order_by(Review.reviewed_at.desc()).limit(1)
            )
            review = result.scalar_one_or_none()
            assert review is not None, "Review record was not updated with GitHub Review ID!"
            assert review.publishing_status == "PUBLISHED", "Publishing status not updated."
            
        print("\\n✓ GitHub Publisher Pipeline Verification Successful")
        print("✓ Positions correctly mapped via Hunks")
        print("✓ Markdown comments generated")
        print("✓ Batch payload submitted to GitHub")
        print("✓ Database status fields updated correctly")
        
    except Exception as e:
        print(f"Publisher execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
