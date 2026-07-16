# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-16

### Added
- **LangGraph Multi-Agent Architecture**: Introduced orchestration of specialized AI agents (Security, Quality, Logic) for intelligent Pull Request reviews.
- **GitHub Webhook Integration**: Fully implemented secure, payload-validated webhook listener for `pull_request` events (`opened`, `synchronize`).
- **AST Parsing**: Integrated `tree-sitter` for deep semantic codebase understanding across Python, JavaScript, TypeScript, JSON, and YAML.
- **Diff Analyzer Engine**: Parses raw Git diffs to extract additions, deletions, reviewable files, and patches.
- **PostgreSQL Database**: Configured via SQLAlchemy and Alembic for robust data persistence.
- **Redis Caching & Locking**: Added Redis for duplicate webhook deduplication, caching rate limits, and asynchronous task queues.
- **Authentication**: Built JWT Bearer authentication system with Bcrypt password hashing.
- **Dashboard Interface**: Created a fully responsive metrics and review browsing UI utilizing Chart.js.
- **Demo Mode**: Allows recruiters and developers to test the full LangGraph pipeline via dummy data without requiring a live GitHub App setup.
- **Prometheus Metrics**: Integrated `prometheus-client` at `/metrics` for system observability.
- **Structured Logging**: Built a custom JSON logger for easy Datadog/ELK integration.

### Changed
- Refactored `diff_analyzer` to utilize `asyncio.gather` for significantly improved parallel network I/O.
- Overhauled project file structure to decouple webhook reception from AI review processing.

### Fixed
- Fixed sequential API blockages by adopting `FastAPI` BackgroundTasks for webhooks.
- Resolved database connection leaks and optimized connection pooling via `asyncpg`.
- Addressed security vulnerabilities by strictly avoiding `shell=True` and securing webhook secrets.
