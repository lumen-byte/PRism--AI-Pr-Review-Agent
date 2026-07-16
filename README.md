<div align="center">
  <img src="https://via.placeholder.com/150x150.png?text=PRism+Logo" alt="PRism Logo" width="120" height="120">
  <h1>PRism — Intelligent Pull Request Review Agent</h1>
  <p><strong>Production-Grade AI Code Review System powered by LangGraph</strong></p>

  [![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
  [![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF9900.svg)](https://langchain.com)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Release](https://img.shields.io/badge/Release-v1.0.0-purple.svg)](RELEASE_NOTES.md)
</div>

<br />

PRism is a production-ready, asynchronous Backend AI system that automatically reviews GitHub Pull Requests. It orchestrates multiple specialized AI agents (Security, Quality, and Logic) in parallel to analyze your code, generate context-aware critiques, and natively publish actionable comments directly to your GitHub Pull Requests.

Built for scale, PRism leverages a highly optimized technology stack typically found at enterprise tech companies.

---

## 📸 Dashboard Showcase

> *Interactive Metrics, Agent Diagnostics, and Review Drill-downs.*

![Dashboard Placeholder](https://via.placeholder.com/800x400.png?text=Interactive+Dashboard+Screenshot)

---

## ⚡ Core Features

- **Multi-Agent Orchestration**: LangGraph coordinates Security, Quality, and Logic agents.
- **AST Code Parsing**: Deep semantic understanding via `tree-sitter` (Python, TS, JS).
- **Enterprise Architecture**: FastAPI (async), PostgreSQL (asyncpg), Redis caching.
- **GitHub Native**: Secure Webhooks (`X-Hub-Signature-256`) and inline review publishing.
- **Demo Mode**: One-click local testing without requiring a live GitHub App setup.
- **Observability**: Prometheus metrics, JSON structured logging, and robust CI/CD.

---

## 🗺️ System Architecture

<details>
<summary><b>1. High-Level Architecture Diagram</b></summary>

```mermaid
graph TD
    A[GitHub Pull Request] -->|Webhook| B(FastAPI Gateway)
    B -->|Enqueues Task| C{Redis Cache}
    C -->|Background Worker| D[Diff Analyzer Node]
    
    D -->|Parallel Execution| E[Security Agent]
    D -->|Parallel Execution| F[Quality Agent]
    D -->|Parallel Execution| G[Logic Agent]
    
    E --> H[Review Orchestrator]
    F --> H
    G --> H
    
    H -->|Saves to DB| I[(PostgreSQL)]
    H -->|Publishes Inline Comments| J[GitHub API]
```

</details>

<details>
<summary><b>2. Sequence Diagram (E2E Flow)</b></summary>

```mermaid
sequenceDiagram
    actor Developer
    participant GitHub
    participant FastAPI
    participant LangGraph
    participant GroqLLM
    participant PostgreSQL

    Developer->>GitHub: Opens PR
    GitHub->>FastAPI: POST /api/v1/webhook (HMAC verified)
    FastAPI->>LangGraph: Initialize ReviewState
    LangGraph->>GitHub: Fetch Diff & AST Source
    LangGraph->>GroqLLM: Parallel execution (Quality, Logic, Security)
    GroqLLM-->>LangGraph: Structured JSON Findings
    LangGraph->>PostgreSQL: Save Merged Review & Scores
    LangGraph->>GitHub: Publish Inline Review
    GitHub-->>Developer: Notifies Developer
```

</details>

<details>
<summary><b>3. LangGraph Agent Flow</b></summary>

```mermaid
stateDiagram-v2
    [*] --> DiffAnalyzer
    DiffAnalyzer --> SecurityAgent
    DiffAnalyzer --> QualityAgent
    DiffAnalyzer --> LogicAgent
    SecurityAgent --> Orchestrator
    QualityAgent --> Orchestrator
    LogicAgent --> Orchestrator
    Orchestrator --> GitHubPublisher
    GitHubPublisher --> [*]
```

</details>

<details>
<summary><b>4. Database ER Diagram</b></summary>

```mermaid
erDiagram
    USERS ||--o{ REVIEWS : "owns"
    REVIEWS ||--o{ ISSUES : "contains"
    
    USERS {
        int id PK
        string email
        string hashed_password
    }
    
    REVIEWS {
        int id PK
        int user_id FK
        int pr_number
        string repo
        string decision
        int health_score
    }
    
    ISSUES {
        int id PK
        int review_id FK
        string category
        string severity
        string description
    }
```

</details>

<details>
<summary><b>5. Folder Structure</b></summary>

```mermaid
graph LR
    Root[PRism Repository] --> App[app/]
    App --> Agents[agents/ (LangGraph)]
    App --> API[api/ (FastAPI Routers)]
    App --> Core[core/ (GitHub & Parsers)]
    App --> DB[db/ (SQLAlchemy)]
    App --> Services[services/ (Review & AI)]
    
    Root --> Docs[docs/]
    Root --> Tests[tests/]
    Root --> Scripts[scripts/]
```

</details>

---

## 🚀 Quickstart (Recruiter Guide)

We value your time! PRism can be booted locally in **Demo Mode** under 2 minutes. No GitHub setup is required to see the AI in action.

### 1. Clone & Build
```bash
git clone https://github.com/prism-ai/prism.git
cd prism
cp .env.example .env
docker-compose up --build -d
```

### 2. View the Dashboard
Navigate to [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html).

### 3. Trigger an AI Review (Demo Mode)
To simulate a Pull Request without connecting GitHub, simply hit the demo endpoint. The backend will parse mock Python files, spin up the AI agents in parallel, and store the results.

```bash
curl -X POST http://localhost:8000/api/v1/demo/trigger
```

Refresh your dashboard to see the real-time AI critique!

![Demo GIF Placeholder](https://via.placeholder.com/800x400.png?text=Demo+CLI+GIF)

---

## 📖 Deep-Dive Documentation

For engineers looking to contribute or understand the internals:

- [Architecture Overview](docs/architecture.md)
- [Database & Migrations](docs/database.md)
- [LangGraph Orchestration](docs/langgraph.md)
- [Security Guidelines](docs/security.md)
- [GitHub Webhooks Setup](docs/github-webhook.md)
- [Production Deployment](docs/deployment.md)

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.
