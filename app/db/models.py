import enum
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class PRStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MERGED = "MERGED"

class ReviewDecision(str, enum.Enum):
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"

class CommentType(str, enum.Enum):
    BUG = "BUG"
    STYLE = "STYLE"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    DOCUMENTATION = "DOCUMENTATION"

class Severity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Repository(Base):
    __tablename__ = "repository"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_url: Mapped[str] = mapped_column(String(512), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    webhook_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    pull_requests: Mapped[List["PullRequest"]] = relationship(
        "PullRequest", back_populates="repository", cascade="all, delete-orphan"
    )

class PullRequest(Base):
    __tablename__ = "pullrequest"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repository.id", ondelete="CASCADE"), nullable=False)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    head_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    pr_url: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[PRStatus] = mapped_column(Enum(PRStatus, native_enum=False), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    repository: Mapped["Repository"] = relationship("Repository", back_populates="pull_requests")
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="pull_request", cascade="all, delete-orphan"
    )

class Review(Base):
    __tablename__ = "review"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pr_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pullrequest.id", ondelete="CASCADE"), nullable=False)
    health_score: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[ReviewDecision] = mapped_column(Enum(ReviewDecision, native_enum=False), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    security_count: Mapped[int] = mapped_column(Integer, default=0)
    quality_count: Mapped[int] = mapped_column(Integer, default=0)
    logic_count: Mapped[int] = mapped_column(Integer, default=0)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    agent_version: Mapped[str] = mapped_column(String(50), nullable=False)
    human_override: Mapped[bool] = mapped_column(Boolean, default=False)
    override_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_review_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publishing_status: Mapped[str] = mapped_column(String(50), server_default="PENDING", default="PENDING")
    publishing_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, server_default="0", default=0)
    
    pull_request: Mapped["PullRequest"] = relationship("PullRequest", back_populates="reviews")
    comments: Mapped[List["ReviewComment"]] = relationship(
        "ReviewComment", back_populates="review", cascade="all, delete-orphan"
    )

class ReviewComment(Base):
    __tablename__ = "reviewcomment"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("review.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    comment_type: Mapped[CommentType] = mapped_column(Enum(CommentType, native_enum=False), nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity, native_enum=False), nullable=False)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    github_comment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    review: Mapped["Review"] = relationship("Review", back_populates="comments")
