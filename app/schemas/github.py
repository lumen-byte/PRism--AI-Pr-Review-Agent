from pydantic import BaseModel, Field
from typing import Optional, List

class GitHubUser(BaseModel):
    login: str
    id: int
    avatar_url: str

class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    owner: GitHubUser
    html_url: str

class GitHubPullRequest(BaseModel):
    url: str
    id: int
    number: int
    state: str
    title: str
    user: GitHubUser
    html_url: str
    body: Optional[str] = None
    created_at: str
    updated_at: str
    base: dict
    head: dict

class GitHubWebhookPayload(BaseModel):
    action: str
    number: Optional[int] = None
    pull_request: Optional[GitHubPullRequest] = None
    repository: GitHubRepository
    sender: GitHubUser

class ChangedFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    blob_url: str
    raw_url: str
    contents_url: str
    patch: Optional[str] = None

class PRMetadata(BaseModel):
    pr_number: int
    owner: str
    repo: str
    title: str
    author: str
    base_branch: str
    head_branch: str
    pr_url: str
    status: str
