import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class ReviewState(TypedDict):
    # Repository & PR Information
    owner: str
    repo: str
    pr_number: int
    title: str
    description: str
    author: str

    # Input Data
    changed_files: List[Dict[str, Any]]
    raw_diff: str

    # Diff Analyzer Outputs
    parsed_files: List[Dict[str, Any]]
    reviewable_files: List[Dict[str, Any]]
    ignored_files: List[Dict[str, Any]]
    diff_statistics: Dict[str, Any]
    language_breakdown: Dict[str, int]
    ast_summaries: Dict[str, Any]

    # Analysis Findings - Using Annotated with operator.add to allow parallel nodes to append
    security_findings: Annotated[List[Dict[str, Any]], operator.add]
    security_summary: str
    security_score: int
    critical_issue_count: int

    quality_findings: Annotated[List[Dict[str, Any]], operator.add]
    quality_summary: str
    quality_score: int
    maintainability_metrics: Dict[str, Any]
    complexity_metrics: Dict[str, Any]

    logic_findings: Annotated[List[Dict[str, Any]], operator.add]
    logic_summary: str
    logic_score: int
    logic_issue_count: int

    # Review Summary & Decision
    review_summary: str
    review_decision: str  # e.g., "APPROVED", "CHANGES_REQUESTED", "NEEDS_DISCUSSION"
    overall_score: int
    health_score: int

    # Execution Metadata
    current_nodes: Annotated[List[str], operator.add]
    execution_time: float
    review_completed: bool
    errors: Annotated[List[str], operator.add]
    timing_info: Annotated[List[Dict[str, Any]], operator.add]

    # Sandbox/Demo settings
    demo_mode: Optional[bool]
    mock_file_contents: Optional[Dict[str, str]]
