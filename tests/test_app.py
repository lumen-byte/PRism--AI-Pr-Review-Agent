import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

from app.agents.graph import run_review_graph
from app.api.health import health_check
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.db.database import AsyncSessionLocal
from app.db.models import User, UserRole


class TestPRismProduction(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Setup session for testing DB operations
        self.session = AsyncSessionLocal()

    async def asyncTearDown(self):
        await self.session.close()

    # 1. Test Authentication Functions
    def test_auth_password_hashing(self):
        password = "PRismTestPassword2026!"
        hashed = get_password_hash(password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_auth_token_generation(self):
        username = "test_user"
        role = "VIEWER"
        token = create_access_token(username, role)
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 0)

        refresh = create_refresh_token(username)
        self.assertIsNotNone(refresh)
        self.assertTrue(len(refresh) > 0)

    # 2. Test Database and Seeding
    async def test_db_seeding_and_users(self):
        # Query the seeded admin user
        result = await self.session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.role, UserRole.ADMIN)

    # 3. Test Health Endpoint Logic
    async def test_health_endpoint(self):
        health_response = await health_check(db=self.session)
        self.assertIn("fastapi", health_response)
        self.assertIn("database", health_response)
        self.assertIn("redis", health_response)
        self.assertIn("langgraph", health_response)
        self.assertIn("tree-sitter", health_response)
        self.assertEqual(health_response["fastapi"], "healthy")

    # 4. Test Webhook Validation and Processing (Mocked)
    @patch("app.api.webhook.validate_signature", return_value=True)
    @patch("app.api.webhook.process_pull_request")
    @patch("app.api.webhook.redis_client")
    async def test_webhook_event_filtering(
        self, mock_redis, mock_process, mock_validate
    ):
        # We mock redis deduplication to false (new delivery)
        mock_redis.is_duplicate_delivery = AsyncMock(return_value=False)
        mock_redis.set_pr_status = AsyncMock()

        # Test direct webhook endpoint route simulation or unit logic if we want.
        # This acts as a unit test for webhook handlers
        from app.api.webhook import github_webhook

        # We can mock the Request object
        mock_request = MagicMock()
        mock_request.headers = {
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "test-delivery-id",
        }
        mock_request.body = AsyncMock(return_value=b"{}")

        # Call webhook with unsupported event 'ping'
        response = await github_webhook(
            request=mock_request,
            background_tasks=MagicMock(),
            x_hub_signature_256="sha256=123",
        )
        self.assertEqual(response["status"], "ignored")
        self.assertEqual(response["reason"], "unsupported event")

    # 5. Test Graph Invocation (Sandbox/Demo Mode)
    async def test_graph_sandbox_execution(self):
        # Build initial state for clean demo scenario
        initial_state = {
            "owner": "lumen-byte",
            "repo": "math_utils",
            "pr_number": 9999,
            "title": "Fix math calculations",
            "description": "Clean demo calculation helper.",
            "author": "john_dev",
            "changed_files": [
                {
                    "filename": "app/math_helper.py",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 1,
                    "changes": 2,
                    "patch": "@@ -1,2 +1,2 @@\n-def add(a, b): return a - b\n+def add(a, b): return a + b",
                }
            ],
            "raw_diff": "@@ -1,2 +1,2 @@\n-def add(a, b): return a - b\n+def add(a, b): return a + b",
            "mock_file_contents": {"app/math_helper.py": "def add(a, b): return a + b"},
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

        final_state = await run_review_graph(initial_state)
        self.assertTrue(final_state.get("review_completed"))
        self.assertEqual(final_state.get("review_decision"), "APPROVED")
        self.assertTrue(final_state.get("health_score") >= 90)


if __name__ == "__main__":
    unittest.main()
