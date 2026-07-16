import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from sqlalchemy import event, select
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings
from app.core.metrics import prism_db_queries_total

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


# Create async engine with pre-ping to verify connection health
# Optimize pool sizes for production load
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=50,
    max_overflow=20,
    pool_timeout=30,
    echo=False,
)


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    stmt = statement.lower().strip()
    if stmt.startswith("select"):
        op = "select"
    elif stmt.startswith("insert"):
        op = "insert"
    elif stmt.startswith("update"):
        op = "update"
    elif stmt.startswith("delete"):
        op = "delete"
    else:
        op = "other"
    prism_db_queries_total.labels(operation=op).inc()


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

    # Seed default admin user
    try:
        from app.core.auth import get_password_hash
        from app.db.models import User, UserRole

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.username == "admin"))
            admin = result.scalar_one_or_none()
            if not admin:
                new_admin = User(
                    username="admin",
                    hashed_password=get_password_hash("PRismAdmin2026!"),
                    role=UserRole.ADMIN,
                )
                session.add(new_admin)
                await session.commit()
                logger.info("Default admin user seeded successfully.")
    except Exception as e:
        logger.error(f"Failed to seed default admin user: {e}")

    yield

    # Shutdown actions
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed.")
