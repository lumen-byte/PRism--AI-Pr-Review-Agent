from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential

# 5 requests per second to avoid Groq rate limits
groq_rate_limiter = AsyncLimiter(5, 1)

# A standard decorator for LLM API retries
retry_llm_call = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
