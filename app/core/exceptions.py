import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from github import GithubException
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("prism.exceptions")


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "ValidationError",
                "detail": exc.errors(),
                "message": "The payload contains invalid parameters.",
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "DatabaseError",
                "message": "A database operation encountered a critical failure.",
            },
        )

    @app.exception_handler(GithubException)
    async def github_exception_handler(request: Request, exc: GithubException):
        logger.error(f"GitHub client exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "type": "GitHubAPIError",
                "message": f"Unable to reach or validate GitHub API. Details: {exc.message}",
            },
        )

    @app.exception_handler(RedisError)
    async def redis_exception_handler(request: Request, exc: RedisError):
        logger.error(f"Redis cache exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "CacheError",
                "message": "Redis connection pools encountered a connection drop.",
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected system error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "InternalServerError",
                "message": "An unexpected error occurred in our system pipeline.",
            },
        )
