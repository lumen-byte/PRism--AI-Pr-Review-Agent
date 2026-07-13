import sys
import os
import json

from app.agents.graph import run_review_graph
from app.agents.state import ReviewState

def verify():
    print("Testing Graph Execution...")
    
    mock_state: ReviewState = {
        "owner": "testowner",
        "repo": "testrepo",
        "pr_number": 42,
        "title": "Mock PR",
        "author": "mockuser",
        "changed_files": [],
        "raw_diff": "mock diff",
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
        final_state = run_review_graph(mock_state)
        
        # Verify node order basically
        timings = final_state.get('timing_info', [])
        nodes_executed = [t['node'] for t in timings]
        
        print(f"Nodes Executed: {nodes_executed}")
        
        assert "diff_analyzer" in nodes_executed, "diff_analyzer didn't run"
        assert "security_agent" in nodes_executed, "security_agent didn't run"
        assert "quality_agent" in nodes_executed, "quality_agent didn't run"
        assert "logic_agent" in nodes_executed, "logic_agent didn't run"
        assert "orchestrator" in nodes_executed, "orchestrator didn't run"
        
        assert final_state["current_node"] == "orchestrator", "Graph did not finish at orchestrator"
        
        print("✓ Graph executed successfully")
        print(f"Final state node: {final_state['current_node']}")
    except Exception as e:
        print(f"Graph execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
