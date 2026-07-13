from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
from app.db.database import get_db
from app.config.settings import settings
import asyncio
from app.core.github_client import github_client

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
    
    status = "healthy" if all(s == "healthy" for s in [database_status, redis_status, github_status, groq_status]) else "unhealthy"
    
    return {
        "fastapi": "healthy",
        "database": database_status,
        "redis": redis_status,
        "github": github_status,
        "groq": groq_status,
        "status": status
    }
