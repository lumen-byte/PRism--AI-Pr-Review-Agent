import time
from typing import Any, Dict, List, Optional

import httpx
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import settings
from app.core.logger import logger
from app.core.metrics import prism_api_calls_total, prism_github_api_duration_seconds
from app.schemas.github import ChangedFile, PRMetadata


class GitHubClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        # Connection pooling and optimization for enterprise traffic
        self.client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers=self.headers,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=10.0,
        )
        self.rate_limiter = AsyncLimiter(10, 1)

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        prism_api_calls_total.labels(target="github").inc()
        start_time = time.perf_counter()

        try:
            async with self.rate_limiter:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
        finally:
            duration = time.perf_counter() - start_time
            # Strip query params or IDs to prevent high cardinality in Prometheus if needed
            base_url_path = url.split("?")[0]
            if "pulls/" in base_url_path:
                parts = base_url_path.split("/")
                if len(parts) >= 6:
                    parts[5] = "{pr_number}"
                base_url_path = "/".join(parts)
            prism_github_api_duration_seconds.labels(
                method=method, endpoint=base_url_path
            ).observe(duration)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_pull_request(
        self, owner: str, repo: str, pr_number: int
    ) -> Optional[PRMetadata]:
        try:
            res = await self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}")
            data = res.json()
            return PRMetadata(
                pr_number=data["number"],
                owner=owner,
                repo=repo,
                title=data["title"],
                author=data["user"]["login"],
                base_branch=data["base"]["ref"],
                head_branch=data["head"]["ref"],
                pr_url=data["html_url"],
                status=data["state"],
            )
        except Exception as e:
            logger.error(f"Failed to fetch PR {pr_number}: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_latest_pull_request(self, owner: str, repo: str) -> Optional[int]:
        try:
            res = await self._request("GET", f"/repos/{owner}/{repo}/pulls?state=open&sort=created&direction=desc&per_page=1")
            data = res.json()
            if data and len(data) > 0:
                return data[0]["number"]
            return None
        except Exception as e:
            logger.error(f"Failed to fetch latest open PR for {owner}/{repo}: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_pull_request_files(
        self, owner: str, repo: str, pr_number: int
    ) -> List[ChangedFile]:
        try:
            res = await self._request(
                "GET", f"/repos/{owner}/{repo}/pulls/{pr_number}/files"
            )
            data = res.json()
            return [
                ChangedFile(
                    filename=f["filename"],
                    status=f["status"],
                    additions=f["additions"],
                    deletions=f["deletions"],
                    changes=f["changes"],
                    blob_url=f.get("blob_url", ""),
                    raw_url=f.get("raw_url", ""),
                    contents_url=f.get("contents_url", ""),
                    patch=f.get("patch", ""),
                )
                for f in data
            ]
        except Exception as e:
            logger.error(f"Failed to fetch PR files {pr_number}: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_pull_request_diff(
        self, owner: str, repo: str, pr_number: int
    ) -> Optional[str]:
        try:
            res = await self._request(
                "GET",
                f"/repos/{owner}/{repo}/pulls/{pr_number}",
                headers={**self.headers, "Accept": "application/vnd.github.v3.diff"},
            )
            return res.text
        except Exception as e:
            logger.error(f"Failed to fetch PR diff {pr_number}: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        event: str = "COMMENT",
        comments: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[int]:
        try:
            commits_res = await self._request(
                "GET", f"/repos/{owner}/{repo}/pulls/{pr_number}/commits"
            )
            commits_data = commits_res.json()
            latest_commit_id = commits_data[-1]["sha"] if commits_data else None

            payload = {"body": body, "event": event}
            if comments:
                payload["comments"] = comments
            if latest_commit_id:
                payload["commit_id"] = latest_commit_id

            res = await self._request(
                "POST", f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews", json=payload
            )
            return res.json()["id"]
        except Exception as e:
            logger.error(f"Failed to create review {pr_number}: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def submit_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        review_id: int,
        event: str = "COMMENT",
        body: str = "",
    ) -> bool:
        try:
            payload = {"event": event}
            if body:
                payload["body"] = body
            await self._request(
                "POST",
                f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews/{review_id}/events",
                json=payload,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to submit review {review_id}: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: str
    ) -> Optional[str]:
        try:
            res = await self._request(
                "GET",
                f"/repos/{owner}/{repo}/contents/{path}?ref={ref}",
                headers={**self.headers, "Accept": "application/vnd.github.v3.raw"},
            )
            return res.text
        except Exception as e:
            logger.warning(f"Failed to fetch file {path}: {e}")
            return None

    async def close(self):
        await self.client.aclose()


github_client = GitHubClient()
