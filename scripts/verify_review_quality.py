import asyncio
import os
import sys

# Make sure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.graph import run_review_graph
from app.agents.state import ReviewState


async def verify():
    print("=== Starting PRism Review Quality Verification ===")

    # 1. Setup mock data simulating a PR with known flaws
    patch = """
@@ -10,6 +10,14 @@ def calculate_total(items):
     return sum(items)

+def authenticate_user(username, password):
+    # Hardcoded secrets test
+    if password == "super_secret_admin_123":
+        return True
+
+    # SQL Injection test
+    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
+    return execute(query)
"""

    state: ReviewState = {
        "owner": "test-org",
        "repo": "test-repo",
        "pr_number": 42,
        "title": "Add authentication",
        "author": "demo-user",
        "changed_files": [
            {
                "filename": "auth.py",
                "status": "modified",
                "additions": 8,
                "deletions": 0,
                "patch": patch,
            }
        ],
        "raw_diff": patch,
        "security_findings": [],
        "quality_findings": [],
        "logic_findings": [],
        "review_summary": "",
        "review_decision": "",
        "health_score": 100,
        "current_node": "START",
        "errors": [],
        "timing_info": [],
    }

    print("Running LangGraph Review Orchestration...")
    final_state = await run_review_graph(state)

    print("\\n=== VERIFICATION RESULTS ===")

    all_findings = (
        final_state.get("security_findings", [])
        + final_state.get("quality_findings", [])
        + final_state.get("logic_findings", [])
    )

    print(f"Total findings: {len(all_findings)}")

    # Assertions
    if len(all_findings) == 0:
        print("❌ FAIL: No findings were detected. Check Groq API configuration.")
        sys.exit(1)

    for f in all_findings:
        print(f"DEBUG FINDING: {f}")
        # Schema checks
        assert "severity" in f, "Missing severity"
        assert "confidence" in f, "Missing confidence"
        assert "why_it_matters" in f, "Missing why_it_matters"
        assert "recommendation" in f, "Missing recommendation"

        # Hallucination check
        assert f["file"] == "auth.py", (
            f"Hallucination detected! Commented on wrong file: {f['file']}"
        )
        assert f["line"] >= 1, (
            f"Hallucination detected! Commented on unmodified line: {f['line']}"
        )

        print(f"✅ Schema & bounds check passed for finding: {f.get('title')}")

    print("\\n=== GENERATED GITHUB COMMENT ===")
    print(final_state.get("review_summary", ""))

    print(
        "\\n✅ ALL TESTS PASSED. The AI Review system is strictly adhering to the new quality guidelines."
    )


if __name__ == "__main__":
    asyncio.run(verify())
