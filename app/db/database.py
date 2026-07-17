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


# Normalize DATABASE_URL for async driver compatibility
# Render/Neon supply postgres:// or postgresql:// URLs with query params like
# sslmode=require and channel_binding=require that asyncpg does not accept.
# We use urllib.parse to safely strip those params without corrupting the URL.
import ssl as _ssl_module
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

_db_url = settings.DATABASE_URL

# 1. Fix the scheme for asyncpg
if _db_url.startswith("postgres://"):
    _db_url = "postgresql+asyncpg://" + _db_url[len("postgres://"):]
elif _db_url.startswith("postgresql://"):
    _db_url = "postgresql+asyncpg://" + _db_url[len("postgresql://"):]
elif not _db_url.startswith("postgresql+asyncpg://"):
    _db_url = "postgresql+asyncpg://" + _db_url

# 2. Parse the URL and strip asyncpg-incompatible query parameters
_parsed = urlparse(_db_url)
_params = parse_qs(_parsed.query)

# Detect SSL requirement before stripping
_use_ssl = "sslmode" in _params and _params["sslmode"][0] in (
    "require", "prefer", "verify-ca", "verify-full"
)

# Remove parameters that asyncpg does not understand
_asyncpg_incompatible = {"sslmode", "channel_binding"}
_clean_params = {k: v for k, v in _params.items() if k not in _asyncpg_incompatible}

# 3. Reconstruct the URL with cleaned query string
_clean_query = urlencode(_clean_params, doseq=True)
_db_url = urlunparse((
    _parsed.scheme,
    _parsed.netloc,
    _parsed.path,
    _parsed.params,
    _clean_query,
    _parsed.fragment,
))

# 4. Build connect_args for SSL if needed
_connect_args = {}
if _use_ssl:
    _ssl_ctx = _ssl_module.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = _ssl_module.CERT_NONE
    _connect_args["ssl"] = _ssl_ctx

# Create async engine with pre-ping to verify connection health
# Optimize pool sizes for production load
engine = create_async_engine(
    _db_url,
    pool_pre_ping=True,
    pool_size=50,
    max_overflow=20,
    pool_timeout=30,
    echo=False,
    connect_args=_connect_args,
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

    # Auto-create tables if they don't exist (first deploy to a fresh database)
    try:
        import app.db.models  # noqa: F401 — ensure all models are registered with Base.metadata
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise e

    # Seed default admin user
    try:
        from app.core.auth import get_password_hash
        from app.db.models import User, UserRole

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.username == "admin"))
            admin = result.scalar_one_or_none()
            if not admin:
                admin = User(
                    username="admin",
                    role=UserRole.ADMIN,
                )
                session.add(admin)
            admin.hashed_password = get_password_hash("PRismAdmin2026!")
            await session.commit()
            logger.info("Default admin user seeded/verified successfully.")
    except Exception as e:
        logger.error(f"Failed to seed default admin user: {e}")

    yield

    # Shutdown actions
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed.")
