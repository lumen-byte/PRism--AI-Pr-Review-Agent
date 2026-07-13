import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Create async engine with pre-ping to verify connection health
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency to get db session in FastAPI routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Database Lifespan management for Startup/Shutdown
@asynccontextmanager
async def database_lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing database connection...")
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to database during startup: {e}")
        raise e
    
    yield
    
    # Shutdown actions
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed.")
