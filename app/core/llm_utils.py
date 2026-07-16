import functools
import time

from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.metrics import prism_api_calls_total, prism_groq_api_duration_seconds

# 5 requests per second to avoid Groq rate limits
groq_rate_limiter = AsyncLimiter(5, 1)


def retry_llm_call(func):
    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        prism_api_calls_total.labels(target="groq").inc()
        start_time = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - start_time
            prism_groq_api_duration_seconds.observe(duration)

    return wrapper
