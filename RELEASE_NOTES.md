# PRism v1.0.0 Release Notes

Welcome to the official **v1.0.0** release of PRism! 🎉

PRism is a production-grade Intelligent Pull Request Review Agent that orchestrates multiple specialized AI agents (Security, Quality, Logic) via LangGraph to automatically review, critique, and approve GitHub Pull Requests.

## Features Included in v1.0.0

- **Multi-Agent Orchestration**: A seamless LangGraph pipeline that divides and conquers the PR diff using specialized context-aware AI agents.
- **Tree-sitter AST Parsing**: Native codebase parsing across 5 different languages (Python, TS, JS, YAML, JSON) for deep semantic understanding.
- **Enterprise Security**: Webhook payloads are secured using `X-Hub-Signature-256`, secrets are filtered out automatically, and the system is fortified against SQL injections via SQLAlchemy ORM.
- **Robust Infrastructure**: Fully dockerized backend powered by FastAPI, PostgreSQL (asyncpg), and Redis.
- **Interactive Dashboard**: A beautiful metrics dashboard mapping the health and quality of all monitored repositories.
- **Demo Mode**: Allows developers to experiment with the LangGraph pipeline locally, without connecting an official GitHub application.
- **Observability**: Prometheus metrics and structured JSON logging are built-in natively.

## Installation and Quickstart

To get started with v1.0.0:

```bash
git clone https://github.com/prism-ai/prism.git
cd prism
docker-compose up --build -d
```

Access the dashboard at: `http://localhost:8000/static/index.html`

## Upgrading

If you were utilizing pre-release versions of PRism, please execute the database migrations after pulling `v1.0.0`:

```bash
docker compose exec api alembic upgrade head
```

Thank you for contributing to the evolution of AI-driven code reviews!
