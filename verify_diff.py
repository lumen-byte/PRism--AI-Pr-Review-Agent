import sys
import os
import json
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.graph import run_review_graph
from app.agents.state import ReviewState

async def verify():
    print("Testing Diff Analyzer via Graph Execution...")
    
    mock_state: ReviewState = {
        "owner": "testowner",
        "repo": "testrepo",
        "pr_number": 42,
        "title": "Mock PR",
        "description": "This is a mock PR.",
        "author": "mockuser",
        "changed_files": [
            {
                "filename": "src/main.py",
                "status": "modified",
                "additions": 10,
                "deletions": 2,
                "changes": 12,
                "patch": "@@ -1,2 +1,12 @@\\n+new code\\n-old code"
            },
            {
                "filename": "package-lock.json",
                "status": "modified",
                "additions": 1000,
                "deletions": 500,
                "changes": 1500,
                "patch": "@@ -1,2 +1,12 @@..."
            },
            {
                "filename": "logo.png",
                "status": "added",
                "additions": 0,
                "deletions": 0,
                "changes": 0,
                "patch": ""
            }
        ],
        "raw_diff": "mock diff",
        "parsed_files": [],
        "reviewable_files": [],
        "ignored_files": [],
        "diff_statistics": {},
        "language_breakdown": {},
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
    
    try:
        final_state = await run_review_graph(mock_state)
        
        # Verify node order basically
        timings = final_state.get('timing_info', [])
        nodes_executed = [t['node'] for t in timings]
        
        print(f"Nodes Executed: {nodes_executed}")
        assert "diff_analyzer" in nodes_executed, "diff_analyzer didn't run"
        
        print(f"Total Parsed Files: {len(final_state['parsed_files'])}")
        print(f"Reviewable Files: {len(final_state['reviewable_files'])}")
        print(f"Ignored Files: {len(final_state['ignored_files'])}")
        print(f"Stats: {final_state['diff_statistics']}")
        print(f"Languages: {final_state['language_breakdown']}")
        
        assert len(final_state['parsed_files']) == 3
        assert len(final_state['reviewable_files']) == 1  # main.py
        assert len(final_state['ignored_files']) == 2  # package-lock.json, logo.png
        
        print("✓ Diff parsing works")
        print("✓ File classification (ignored files) works")
        print("✓ ReviewState populated properly")
        print("✓ Graph executed successfully")
        
    except Exception as e:
        print(f"Graph execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
