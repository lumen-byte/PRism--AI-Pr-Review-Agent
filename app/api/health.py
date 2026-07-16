import asyncio
import time

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


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    database_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception:
        pass

    redis_status = "unhealthy"
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        redis_status = "healthy"
        await r.aclose()
    except Exception:
        pass

    github_status = "unhealthy"
    try:
        if settings.GITHUB_TOKEN:
            await asyncio.to_thread(github_client.g.get_rate_limit)
            github_status = "healthy"
    except Exception:
        pass

    groq_status = "unhealthy"
    if settings.GROQ_API_KEY:
        groq_status = "healthy"

    langgraph_status = "unhealthy"
    try:
        if review_graph is not None:
            langgraph_status = "healthy"
    except Exception:
        pass

    tree_sitter_status = "unhealthy"
    try:
        if tree_sitter_service.parse_file("dummy.py", "def foo(): pass"):
            tree_sitter_status = "healthy"
    except Exception:
        pass

    status = (
        "healthy"
        if all(
            s == "healthy"
            for s in [
                database_status,
                redis_status,
                github_status,
                groq_status,
                langgraph_status,
                tree_sitter_status,
            ]
        )
        else "unhealthy"
    )

    return {
        "fastapi": "healthy",
        "database": database_status,
        "redis": redis_status,
        "github": github_status,
        "groq": groq_status,
        "langgraph": langgraph_status,
        "tree-sitter": tree_sitter_status,
        "version": "1.1.0",
        "build_time": "2026-07-13T18:00:00Z",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "status": status,
    }
