import asyncio
import time
from datetime import datetime, timezone

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import review_graph
from app.config.settings import settings
from app.core.github_client import github_client
from app.core.parser.tree_sitter_service import tree_sitter_service
from app.db.database import get_db

START_TIME = time.time()

router = APIRouter()

def get_now_iso():
    return datetime.now(timezone.utc).isoformat()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    services = {}

    # FastAPI
    services["fastapi"] = {
        "status": "healthy",
        "latency_ms": 1,
        "last_checked": get_now_iso()
    }

    # Database
    t0 = time.time()
    database_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception:
        pass
    services["database"] = {
        "status": database_status,
        "latency_ms": int((time.time() - t0) * 1000),
        "last_checked": get_now_iso()
    }

    # Redis
    t0 = time.time()
    redis_status = "unhealthy"
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        redis_status = "healthy"
        await r.aclose()
    except Exception:
        pass
    services["redis"] = {
        "status": redis_status,
        "latency_ms": int((time.time() - t0) * 1000),
        "last_checked": get_now_iso()
    }

    # GitHub API
    t0 = time.time()
    github_status = "unhealthy"
    try:
        if settings.GITHUB_TOKEN:
            await asyncio.to_thread(github_client.g.get_rate_limit)
            github_status = "healthy"
    except Exception:
        pass
    services["github"] = {
        "status": github_status,
        "latency_ms": int((time.time() - t0) * 1000),
        "last_checked": get_now_iso()
    }

    # Groq API
    t0 = time.time()
    groq_status = "unhealthy"
    if settings.GROQ_API_KEY:
        groq_status = "healthy"
    services["groq"] = {
        "status": groq_status,
        "latency_ms": int((time.time() - t0) * 1000),  # In real app, we might ping Groq API
        "last_checked": get_now_iso()
    }

    # LangGraph
    t0 = time.time()
    langgraph_status = "unhealthy"
    try:
        if review_graph is not None:
            langgraph_status = "healthy"
    except Exception:
        pass
    services["langgraph"] = {
        "status": langgraph_status,
        "latency_ms": int((time.time() - t0) * 1000),
        "last_checked": get_now_iso()
    }

    # Tree Sitter
    t0 = time.time()
    tree_sitter_status = "unhealthy"
    try:
        if tree_sitter_service.parse_file("dummy.py", "def foo(): pass"):
            tree_sitter_status = "healthy"
    except Exception:
        pass
    services["tree-sitter"] = {
        "status": tree_sitter_status,
        "latency_ms": int((time.time() - t0) * 1000),
        "last_checked": get_now_iso()
    }

    overall_status = "healthy" if all(s["status"] == "healthy" for s in services.values()) else "unhealthy"

    return {
        # Legacy flat structure for backwards compatibility
        "fastapi": "healthy",
        "database": database_status,
        "redis": redis_status,
        "github": github_status,
        "groq": groq_status,
        "langgraph": langgraph_status,
        "tree-sitter": tree_sitter_status,
        
        # New Detailed Structure
        "services": services,
        "version": "1.1.0",
        "build_time": "2026-07-13T18:00:00Z",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "status": overall_status,
    }
