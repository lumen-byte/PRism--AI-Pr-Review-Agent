from app.demo.sample_logic_cases import LOGIC_CONTENTS, LOGIC_DIFF
from app.demo.sample_quality_cases import QUALITY_CONTENTS, QUALITY_DIFF
from app.demo.sample_security_cases import SECURITY_CONTENTS, SECURITY_DIFF

CLEAN_DIFF = """@@ -1,5 +1,5 @@
-def add(a, b):
-    return a - b
+def add(a, b):
+    return a + b
"""

CLEAN_CONTENTS = {
    "app/clean_code.py": """def add(a, b):
    return a + b
"""
}

# Mixed Contents and Diffs
MIXED_DIFF = SECURITY_DIFF + "\n" + QUALITY_DIFF + "\n" + LOGIC_DIFF
MIXED_CONTENTS = {**SECURITY_CONTENTS, **QUALITY_CONTENTS, **LOGIC_CONTENTS}

SCENARIOS = {
    "clean": {
        "title": "Fix addition helper implementation",
        "description": "Adjust sum logic to add instead of subtract.",
        "author": "john_developer",
        "repo": "math_utils",
        "owner": "lumen-byte",
        "changed_files": [
            {
                "filename": "app/clean_code.py",
                "status": "modified",
                "additions": 1,
                "deletions": 1,
                "changes": 2,
                "patch": CLEAN_DIFF,
            }
        ],
        "raw_diff": CLEAN_DIFF,
        "mock_file_contents": CLEAN_CONTENTS,
    },
    "security": {
        "title": "Add sqlite user endpoints and login authentication",
        "description": "Introducing initial database queries and secure login handlers.",
        "author": "sec_dev",
        "repo": "user_service",
        "owner": "lumen-byte",
        "changed_files": [
            {
                "filename": "app/security_vuln.py",
                "status": "modified",
                "additions": 15,
                "deletions": 2,
                "changes": 17,
                "patch": SECURITY_DIFF,
            }
        ],
        "raw_diff": SECURITY_DIFF,
        "mock_file_contents": SECURITY_CONTENTS,
    },
    "quality": {
        "title": "Refactor cart value calculations",
        "description": "Optimizing discount applications for guests and registered users.",
        "author": "clean_coder",
        "repo": "cart_service",
        "owner": "lumen-byte",
        "changed_files": [
            {
                "filename": "app/quality_smells.py",
                "status": "modified",
                "additions": 30,
                "deletions": 2,
                "changes": 32,
                "patch": QUALITY_DIFF,
            }
        ],
        "raw_diff": QUALITY_DIFF,
        "mock_file_contents": QUALITY_CONTENTS,
    },
    "logic": {
        "title": "Process scores helper and vip discount implementation",
        "description": "Includes calculating score averages and VIP promotions.",
        "author": "algo_expert",
        "repo": "score_engine",
        "owner": "lumen-byte",
        "changed_files": [
            {
                "filename": "app/logic_errors.py",
                "status": "modified",
                "additions": 15,
                "deletions": 2,
                "changes": 17,
                "patch": LOGIC_DIFF,
            }
        ],
        "raw_diff": LOGIC_DIFF,
        "mock_file_contents": LOGIC_CONTENTS,
    },
    "mixed": {
        "title": "Mixed features release: SQL endpoints, Cart helpers, VIP logic",
        "description": "Bundled release package containing database access, cart values, and score logic.",
        "author": "fullstack_john",
        "repo": "core_gateway",
        "owner": "lumen-byte",
        "changed_files": [
            {
                "filename": "app/security_vuln.py",
                "status": "modified",
                "additions": 15,
                "deletions": 2,
                "changes": 17,
                "patch": SECURITY_DIFF,
            },
            {
                "filename": "app/quality_smells.py",
                "status": "modified",
                "additions": 30,
                "deletions": 2,
                "changes": 32,
                "patch": QUALITY_DIFF,
            },
            {
                "filename": "app/logic_errors.py",
                "status": "modified",
                "additions": 15,
                "deletions": 2,
                "changes": 17,
                "patch": LOGIC_DIFF,
            },
        ],
        "raw_diff": MIXED_DIFF,
        "mock_file_contents": MIXED_CONTENTS,
    },
}
