import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("prism.structured")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Extract or generate Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # 2. Track timing
        start_time = time.time()

        # 3. Client IP
        client_ip = request.client.host if request.client else "unknown"

        # Process request
        try:
            response: Response = await call_next(request)
        except Exception as e:
            # Timing for failed requests
            duration = time.time() - start_time
            logger.error(
                {
                    "message": "Request failed",
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url.path),
                    "client_ip": client_ip,
                    "duration_seconds": round(duration, 4),
                    "error": str(e),
                }
            )
            raise e

        duration = time.time() - start_time

        # 4. Inject Response Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.4f}s"

        # Log structured information
        logger.info(
            {
                "message": "Request processed",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url.path),
                "status_code": response.status_code,
                "client_ip": client_ip,
                "duration_seconds": round(duration, 4),
            }
        )

        return response
