# Architecture Overview

PRism follows an event-driven architecture using a modern data stack.

1. **Webhook Receiver (FastAPI)**: Listens for GitHub PR events.
2. **Background Queue (Redis)**: Validates and pushes the event into a Redis-backed queue.
3. **Graph Orchestration (LangGraph)**:
   - **Diff Analyzer**: Parses the PR diff and creates abstract syntax trees (Tree-sitter).
   - **Parallel Agents**: Three parallel agents (Security, Quality, Logic) analyze the diff.
   - **Review Orchestrator**: Consolidates findings and scores the PR.
4. **GitHub Publisher**: Publishes comments back to GitHub via their API.
5. **Storage (PostgreSQL)**: Stores review metrics, findings, and metadata.
