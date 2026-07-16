from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

router = APIRouter()

# Define Prometheus metrics
prism_reviews_total = Counter(
    "prism_reviews_total", "Total count of PR reviews executed", ["repo", "decision"]
)

prism_review_duration_seconds = Histogram(
    "prism_review_duration_seconds",
    "Time taken to run the PR review LangGraph graph",
    buckets=[1, 2.5, 5, 10, 30, 60],
)

prism_webhook_calls_total = Counter(
    "prism_webhook_calls_total",
    "Total count of GitHub webhooks received",
    ["event", "action", "status"],
)

prism_api_calls_total = Counter(
    "prism_api_calls_total",
    "Outbound external API calls made by PRism",
    ["target"],  # e.g., "github", "groq"
)

prism_redis_hits_total = Counter(
    "prism_redis_hits_total",
    "Total cache checks against Redis",
    ["type", "hit"],  # type="dedup" or "lock", hit="true" or "false"
)

prism_db_queries_total = Counter(
    "prism_db_queries_total",
    "Total database queries executed by ORM layer",
    ["operation"],  # e.g., "select", "insert", "update"
)

prism_github_api_duration_seconds = Histogram(
    "prism_github_api_duration_seconds",
    "Time taken for GitHub API outbound requests",
    ["method", "endpoint"],
    buckets=[0.1, 0.5, 1, 2.5, 5, 10],
)

prism_groq_api_duration_seconds = Histogram(
    "prism_groq_api_duration_seconds",
    "Time taken for Groq API outbound requests",
    buckets=[0.5, 1, 2.5, 5, 10, 30],
)

prism_webhook_duration_seconds = Histogram(
    "prism_webhook_duration_seconds",
    "Time taken to process incoming GitHub webhooks",
    ["event", "action"],
    buckets=[0.1, 0.5, 1, 2.5, 5, 10],
)


@router.get("/metrics")
def get_prometheus_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
