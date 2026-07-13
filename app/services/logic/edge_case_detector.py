class EdgeCaseDetector:
    def __init__(self):
        pass

    def build_context(self, repo: str, pr_title: str, pr_desc: str, function_name: str, function_body: str, patch: str) -> str:
        """
        Builds a lean context string to feed to the LLM to minimize token usage.
        """
        context_parts = [
            f"Repository: {repo}",
            f"PR Title: {pr_title}",
            f"PR Description: {pr_desc}",
            "---",
            f"Target Function: {function_name}",
            f"Changed lines (Diff/Patch):\\n{patch}",
            "---",
            f"Function Source:\\n{function_body}"
        ]
        
        return "\\n".join(context_parts)

edge_case_detector = EdgeCaseDetector()
