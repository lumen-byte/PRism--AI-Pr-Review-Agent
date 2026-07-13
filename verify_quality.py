import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.graph import run_review_graph
from app.agents.state import ReviewState

async def verify():
    print("Testing Quality Agent Pipeline...")
    
    # Mock source contents to parse
    mock_file_contents = {
        "src/main.py": """
# TODO: fix this

def a(x):
    # This is a very complex function
    if x > 10:
        for i in range(10):
            if i % 2 == 0:
                print(i)
            else:
                if x == 15:
                    return 1
                elif x == 16:
                    return 2
                elif x == 17:
                    return 3
                elif x == 18:
                    return 4
                elif x == 19:
                    return 5
                elif x == 20:
                    return 6
                elif x == 21:
                    return 7
                elif x == 22:
                    return 8
                elif x == 23:
                    return 9
                elif x == 24:
                    return 10
                elif x == 25:
                    return 11
    
    timeout = 3600
    return 0
    
def a(x):
    # This is a very complex function
    if x > 10:
        for i in range(10):
            if i % 2 == 0:
                print(i)
            else:
                if x == 15:
                    return 1
                elif x == 16:
                    return 2
                elif x == 17:
                    return 3
                elif x == 18:
                    return 4
                elif x == 19:
                    return 5
                elif x == 20:
                    return 6
                elif x == 21:
                    return 7
                elif x == 22:
                    return 8
                elif x == 23:
                    return 9
                elif x == 24:
                    return 10
                elif x == 25:
                    return 11
    
    timeout = 3600
    return 0

class myClass:
    def method(self):
        pass
""",
    }
    
    # MOCK LLMRefactorChecker
    from app.services.quality.llm_refactor import LLMRefactorChecker
    from app.services.quality.quality_models import QualityIssue
    
    original_scan = LLMRefactorChecker.scan
    async def mock_llm_scan(self, file_path, function_name, code_block, start_line):
        return [
            QualityIssue(
                file=file_path,
                line=start_line,
                rule="refactor_suggestion",
                severity="medium",
                title="Refactor via LLM",
                description="Mock LLM refactor suggestion.",
                recommendation="Extract logic.",
                confidence="high"
            )
        ]
    LLMRefactorChecker.scan = mock_llm_scan
    
    mock_state: ReviewState = {
        "owner": "testowner",
        "repo": "testrepo",
        "pr_number": 42,
        "title": "Mock Quality PR",
        "description": "This is a mock PR.",
        "author": "mockuser",
        "changed_files": [
            {"filename": "src/main.py", "status": "modified", "additions": 100, "deletions": 0, "changes": 100, "patch": mock_file_contents["src/main.py"]},
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
        "review_summary": "",
        "review_decision": "",
        "health_score": 100,
        "current_nodes": ["START"],
        "errors": [],
        "timing_info": []
    }
    
    try:
        final_state = await run_review_graph(mock_state)
        
        findings = final_state.get('quality_findings', [])
        print(f"\\nQuality Findings Generated: {len(findings)}")
        for f in findings:
            print(f"- [{f['severity'].upper()}] {f['rule']}: {f['title']} (Line {f['line']})")
        
        # Verify specific findings
        assert any(f['rule'] == 'short_function_name' for f in findings), "Failed to detect short function name"
        assert any(f['rule'] == 'class_naming_convention' for f in findings), "Failed to detect invalid class naming"
        assert any(f['rule'] == 'todo_comment' for f in findings), "Failed to detect TODO comment"
        assert any(f['rule'] == 'missing_docstring_func' for f in findings), "Failed to detect missing docstring"
        assert any(f['rule'] == 'high_cyclomatic_complexity' for f in findings), "Failed to detect high complexity"
        assert any(f['rule'] == 'duplicate_code' for f in findings), "Failed to detect duplicate code"
        assert any(f['rule'] == 'refactor_suggestion' for f in findings), "Failed to trigger LLM refactor"
        
        print(f"\\nSummary: {final_state.get('quality_summary')}")
        print(f"Metrics: Maintainability {final_state.get('maintainability_metrics')}, Complexity {final_state.get('complexity_metrics')}")
        
        print("\\n✓ Naming convention checks work")
        print("✓ Code smell detection works (TODOs, docstrings)")
        print("✓ Cyclomatic complexity metrics work")
        print("✓ Structural AST duplication detection works")
        print("✓ LLM selectively hooked for complex functions")
        print("✓ ReviewState receives complete quality state")
        
    except Exception as e:
        print(f"Quality Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
