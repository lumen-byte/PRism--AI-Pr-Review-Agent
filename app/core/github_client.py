import asyncio
from typing import List, Dict, Any, Optional
from github import Github, Auth, GithubException
from app.config.settings import settings
from app.core.logger import logger
from app.schemas.github import ChangedFile, PRMetadata
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from aiolimiter import AsyncLimiter

class GitHubClient:
    def __init__(self):
        auth = Auth.Token(settings.GITHUB_TOKEN)
        self.g = Github(auth=auth)
        # 10 requests per second to avoid abuse rate limits
        self.rate_limiter = AsyncLimiter(10, 1)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(GithubException))
    async def get_repository(self, owner: str, repo: str) -> Optional[Any]:
        try:
            async with self.rate_limiter:
                return await asyncio.to_thread(self.g.get_repo, f"{owner}/{repo}")
        except GithubException as e:
            logger.error(f"Failed to fetch repository {owner}/{repo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Network/Unexpected error fetching repository {owner}/{repo}: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(GithubException))
    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Optional[PRMetadata]:
        try:
            repository = await self.get_repository(owner, repo)
            if not repository:
                return None
            async with self.rate_limiter:
                pr = await asyncio.to_thread(repository.get_pull, pr_number)
            return PRMetadata(
                pr_number=pr.number,
                owner=owner,
                repo=repo,
                title=pr.title,
                author=pr.user.login,
                base_branch=pr.base.ref,
                head_branch=pr.head.ref,
                pr_url=pr.html_url,
                status=pr.state
            )
        except GithubException as e:
            logger.error(f"Failed to fetch PR {pr_number} in {owner}/{repo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Network/Unexpected error fetching PR {pr_number}: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(GithubException))
    async def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[ChangedFile]:
        try:
            repository = await self.get_repository(owner, repo)
            if not repository:
                return []
            async with self.rate_limiter:
                pr = await asyncio.to_thread(repository.get_pull, pr_number)
                files = await asyncio.to_thread(pr.get_files)
            changed_files = []
            for f in files:
                changed_files.append(ChangedFile(
                    filename=f.filename,
                    status=f.status,
                    additions=f.additions,
                    deletions=f.deletions,
                    changes=f.changes,
                    blob_url=f.blob_url,
                    raw_url=f.raw_url,
                    contents_url=f.contents_url,
                    patch=f.patch
                ))
            return changed_files
        except GithubException as e:
            logger.error(f"Failed to fetch files for PR {pr_number} in {owner}/{repo}: {e}")
            return []
        except Exception as e:
            logger.error(f"Network/Unexpected error fetching PR files {pr_number}: {e}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(GithubException))
    async def get_pull_request_diff(self, owner: str, repo: str, pr_number: int) -> Optional[str]:
        try:
            # We can get diff by calling GitHub API directly using PyGithub's internal requester
            repository = await self.get_repository(owner, repo)
            if not repository:
                return None
            
            # The proper way to get a raw diff via PyGithub is to use headers 
            # application/vnd.github.v3.diff on the PR endpoint.
            # PyGithub doesn't have a direct helper for this, so we use requester:
            async with self.rate_limiter:
                status, headers, data = await asyncio.to_thread(
                self.g._Github__requester.requestBlobAndCheck,
                "GET",
                f"/repos/{owner}/{repo}/pulls/{pr_number}",
                headers={"Accept": "application/vnd.github.v3.diff"}
            )
            return data
        except GithubException as e:
            logger.error(f"Failed to fetch diff for PR {pr_number} in {owner}/{repo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Network/Unexpected error fetching PR diff {pr_number}: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(GithubException))
    async def create_review(self, owner: str, repo: str, pr_number: int, body: str, event: str = "COMMENT", comments: Optional[List[Dict[str, Any]]] = None) -> Optional[int]:
        try:
            repository = await self.get_repository(owner, repo)
            if not repository:
                return None
            
            async with self.rate_limiter:
                pr = await asyncio.to_thread(repository.get_pull, pr_number)
                kwargs = {"body": body, "event": event}
                if comments:
                    kwargs["comments"] = comments
                    
                # Need the head commit for inline comments
                commits = await asyncio.to_thread(pr.get_commits)
                if commits.totalCount > 0:
                    kwargs["commit"] = commits[commits.totalCount - 1]
                    
                review = await asyncio.to_thread(pr.create_review, **kwargs)
                return review.id
        except GithubException as e:
            logger.error(f"Failed to create review for PR {pr_number} in {owner}/{repo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Network/Unexpected error creating review {pr_number}: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(GithubException))
    async def create_inline_comment(self, owner: str, repo: str, pr_number: int, body: str, commit_id: str, path: str, position: int) -> bool:
        try:
            repository = await self.get_repository(owner, repo)
            if not repository:
                return False
            async with self.rate_limiter:
                pr = await asyncio.to_thread(repository.get_pull, pr_number)
                await asyncio.to_thread(pr.create_review_comment, body=body, commit_id=commit_id, path=path, position=position)
                return True
        except GithubException as e:
            logger.error(f"Failed to create inline comment for PR {pr_number} in {owner}/{repo}: {e}")
            return False
        except Exception as e:
            logger.error(f"Network/Unexpected error creating inline comment {pr_number}: {e}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(GithubException))
    async def submit_review(self, owner: str, repo: str, pr_number: int, review_id: int, event: str = "COMMENT", body: str = "") -> bool:
        try:
            repository = await self.get_repository(owner, repo)
            if not repository:
                return False
            async with self.rate_limiter:
                pr = await asyncio.to_thread(repository.get_pull, pr_number)
                review = await asyncio.to_thread(pr.get_review, review_id)
                await asyncio.to_thread(review.submit, event=event, body=body)
                return True
        except GithubException as e:
            logger.error(f"Failed to submit review {review_id} for PR {pr_number} in {owner}/{repo}: {e}")
            return False
        except Exception as e:
            logger.error(f"Network/Unexpected error submitting review {review_id} for PR {pr_number}: {e}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(GithubException))
    async def get_file_content(self, owner: str, repo: str, path: str, ref: str) -> Optional[str]:
        try:
            repository = await self.get_repository(owner, repo)
            if not repository:
                return None
            async with self.rate_limiter:
                # get_contents can return a single ContentFile or a list of ContentFiles.
                # Assuming path is a file, it returns a single ContentFile.
                content_file = await asyncio.to_thread(repository.get_contents, path, ref=ref)
                if isinstance(content_file, list):
                    return None
                return content_file.decoded_content.decode("utf-8")
        except GithubException as e:
            logger.warning(f"Failed to fetch file {path} for {owner}/{repo} at {ref}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching file {path}: {e}")
            return None

github_client = GitHubClient()
