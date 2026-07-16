# Deployment Guide

## Render Deployment (Recommended)
PRism includes a `render.yaml` file for Infrastructure as Code on Render.com.

1. Connect your GitHub repository to Render.
2. Render will automatically detect `render.yaml` and provision:
   - PostgreSQL database
   - Redis instance
   - FastAPI web service (Docker environment)

Ensure you set `GROQ_API_KEY`, `GITHUB_TOKEN`, and `GITHUB_WEBHOOK_SECRET` in your Render dashboard environment variables.

## Docker Deployment
```bash
docker build -t prism-backend .
docker run -p 8000:8000 --env-file .env prism-backend
```
