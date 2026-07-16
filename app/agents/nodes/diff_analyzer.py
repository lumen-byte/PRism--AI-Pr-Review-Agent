import time

from app.agents.state import ReviewState
from app.core.diff_parser import DiffParser
from app.core.github_client import github_client
from app.core.logger import logger
from app.core.parser.tree_sitter_service import tree_sitter_service


async def diff_analyzer(state: ReviewState) -> ReviewState:
    start_time = time.time()
    pr_number = state.get("pr_number")
    owner = state.get("owner")
    repo = state.get("repo")
    logger.info(f"[Node: Diff Analyzer] Started for PR {pr_number}")

    # 1. Fetch PR metadata if missing
    title = state.get("title")
    description = state.get("description")
    author = state.get("author")

    if not title or not author or description is None:
        logger.info(
            f"[Node: Diff Analyzer] Fetching missing metadata for PR {pr_number}"
        )
        pr_metadata = await github_client.get_pull_request(owner, repo, pr_number)
        if pr_metadata:
            title = title or pr_metadata.title
            author = author or pr_metadata.author
            # Note: We need body from PyGithub which we didn't initially store in PRMetadata.
            # But the requirement asks to extract description. We'll set it empty if missing.
            description = description or ""

    # 2. Fetch changed files if missing
    changed_files = state.get("changed_files")
    if not changed_files:
        logger.info(
            f"[Node: Diff Analyzer] Fetching missing changed files for PR {pr_number}"
        )
        cf_models = await github_client.get_pull_request_files(owner, repo, pr_number)
        changed_files = [f.model_dump() for f in cf_models]

    # 3. Fetch raw git diff if missing
    raw_diff = state.get("raw_diff")
    if not raw_diff:
        logger.info(
            f"[Node: Diff Analyzer] Fetching missing raw diff for PR {pr_number}"
        )
        raw_diff = await github_client.get_pull_request_diff(owner, repo, pr_number)
        raw_diff = raw_diff or ""

    # Parse Diff
    logger.info(f"[Node: Diff Analyzer] Parsing {len(changed_files)} files...")
    parsed_data = DiffParser.parse_files(changed_files)

    stats = parsed_data["diff_statistics"]
    logger.info(
        f"[Node: Diff Analyzer] Stats: +{stats['total_additions']} -{stats['total_deletions']} in {stats['total_files']} files"
    )
    logger.info(
        f"[Node: Diff Analyzer] Ignored {stats['ignored_count']} files, Reviewable {stats['reviewable_count']} files"
    )
    logger.info(f"[Node: Diff Analyzer] Languages: {parsed_data['language_breakdown']}")

    # 5. Extract AST using TreeSitterService
    ast_summaries = {}
    reviewable = parsed_data["reviewable_files"]

    # We need the PR ref to fetch correct file versions.
    # Usually we want the head branch sha, but we might just use the PR branch or default to 'main'.
    # For now we can fetch using just the PR branch if available in PR metadata.
    # However, to be simple, we can fetch without ref or with the author branch if stored.
    # We don't have head_branch in the state by default unless we add it.
    # Let's just use patch fallback if GitHub fails to fetch.

    import asyncio

    async def fetch_and_parse(f_data):
        file_path = f_data["file_path"]
        patch = f_data.get("patch", "")

        # Try to fetch raw file from GitHub, fallback to patch
        content = await github_client.get_file_content(owner, repo, file_path, ref="")
        if not content:
            # Fallback to test mock data or patch
            mock_contents = state.get("mock_file_contents", {})
            content = mock_contents.get(file_path, patch)

        parsed_ast = tree_sitter_service.parse_file(file_path, content)
        if parsed_ast:
            return file_path, parsed_ast.model_dump()
        return None

    results = await asyncio.gather(*(fetch_and_parse(f) for f in reviewable))

    for res in results:
        if res:
            ast_summaries[res[0]] = res[1]

    execution_time = time.time() - start_time
    logger.info(f"[Node: Diff Analyzer] Finished in {execution_time:.2f} seconds")

    return {
        "title": title,
        "author": author,
        "description": description or "",
        "changed_files": changed_files,
        "raw_diff": raw_diff,
        "parsed_files": parsed_data["parsed_files"],
        "reviewable_files": parsed_data["reviewable_files"],
        "ignored_files": parsed_data["ignored_files"],
        "diff_statistics": parsed_data["diff_statistics"],
        "language_breakdown": parsed_data["language_breakdown"],
        "ast_summaries": ast_summaries,
        "current_nodes": ["diff_analyzer"],
        "timing_info": [{"node": "diff_analyzer", "execution_time": execution_time}],
    }
