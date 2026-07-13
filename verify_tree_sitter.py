import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.graph import run_review_graph
from app.agents.state import ReviewState

async def verify():
    print("Testing Tree-sitter AST Extraction Pipeline...")
    
    # Mock source contents to parse
    mock_file_contents = {
        "src/main.py": """def hello_world():
    print('hello')

class MyClass:
    def method(self):
        pass""",
        "src/app.js": """function test() { console.log('test'); }
const arrow = () => {};""",
        "data.json": """{
  "key": "value"
}""",
        "config.yaml": """version: '3'
services:
  app:
    image: node:14""",
    }
    
    mock_state: ReviewState = {
        "owner": "testowner",
        "repo": "testrepo",
        "pr_number": 42,
        "title": "Mock AST PR",
        "description": "This is a mock PR.",
        "author": "mockuser",
        "changed_files": [
            {"filename": "src/main.py", "status": "modified", "additions": 10, "deletions": 2, "changes": 12, "patch": mock_file_contents["src/main.py"]},
            {"filename": "src/app.js", "status": "added", "additions": 5, "deletions": 0, "changes": 5, "patch": mock_file_contents["src/app.js"]},
            {"filename": "data.json", "status": "modified", "additions": 2, "deletions": 1, "changes": 3, "patch": mock_file_contents["data.json"]},
            {"filename": "config.yaml", "status": "modified", "additions": 4, "deletions": 0, "changes": 4, "patch": mock_file_contents["config.yaml"]},
        ],
        "raw_diff": "mock diff",
        "parsed_files": [],
        "reviewable_files": [],
        "ignored_files": [],
        "diff_statistics": {},
        "language_breakdown": {},
        "ast_summaries": {},
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
        
        ast_summaries = final_state.get('ast_summaries', {})
        print(f"\\nAST Summaries Generated: {len(ast_summaries)}")
        
        # Verify Python
        py_ast = ast_summaries.get("src/main.py")
        assert py_ast is not None, "Failed to parse Python file"
        print(f"Python metrics: {py_ast['summary']}")
        assert py_ast['summary']['function_count'] >= 1, "Failed to extract Python functions"
        assert py_ast['summary']['class_count'] >= 1, "Failed to extract Python classes"
        
        # Verify JS
        js_ast = ast_summaries.get("src/app.js")
        assert js_ast is not None, "Failed to parse JS file"
        print(f"JS metrics: {js_ast['summary']}")
        assert js_ast['summary']['function_count'] >= 1, "Failed to extract JS functions"
        
        # Verify JSON
        json_ast = ast_summaries.get("data.json")
        assert json_ast is not None, "Failed to parse JSON file"
        print(f"JSON metrics: {json_ast['summary']}")
        
        print("\\n✓ Every parser loads correctly")
        print("✓ AST generation works")
        print("✓ Metrics are generated")
        print("✓ ReviewState receives AST information")
        
    except Exception as e:
        print(f"Tree-sitter execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
