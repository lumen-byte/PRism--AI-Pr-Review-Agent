# PRism AI: Manual Production Deployment Guide

This guide provides step-by-step instructions to manually deploy the **PRism AI Pull Request Reviewer** to [Render.com](https://render.com). We have opted for a manual deployment strategy to bypass Render Blueprint schema validation issues and gain full control over individual service configurations.

---

## 🏗️ Architecture Overview

The production deployment consists of 3 distinct cloud services on Render:
1. **Render PostgreSQL Database** (Managed Relational DB)
2. **Render Redis** (Managed In-Memory Message Broker / Cache)
3. **Render Web Service** (Dockerized FastAPI Application)

All configuration is provided to the Web Service entirely via **Environment Variables**, ensuring a secure, 12-factor app compliant deployment.

---

## Step 1: Create PostgreSQL Database

1. Log into your Render dashboard: [https://dashboard.render.com](https://dashboard.render.com)
2. Click **New +** -> **PostgreSQL**.
3. **Name**: `prism-db`
4. **Database**: `prism`
5. **User**: `prism_user`
6. **Region**: Select the region closest to you (e.g., Ohio).
7. **PostgreSQL Version**: 16 (or latest stable).
8. **Instance Type**: Free or Starter.
9. Click **Create Database**.

Once created, scroll down to the **Connections** section and copy the **Internal Database URL** (if the Web Service is also on Render) or **External Database URL**.
* **Crucial Step**: Since the app uses async database connections, you must modify the prefix from `postgresql://` to `postgresql+asyncpg://` before saving it in your environment variables.

---

## Step 2: Create Redis Instance

1. On the Render dashboard, click **New +** -> **Redis**.
2. **Name**: `prism-redis`
3. **Region**: Select the SAME region as your database.
4. **Instance Type**: Free or Starter.
5. Click **Create Redis**.

Once created, copy the **Internal Redis URL** (e.g., `redis://red-xxxx:6379`).

---

## Step 3: Deploy FastAPI Web Service (Docker)

1. On the Render dashboard, click **New +** -> **Web Service**.
2. Select **Build and deploy from a Git repository**.
3. Connect your GitHub repository: `lumen-byte/PRism--AI-Pr-Review-Agent`.
4. Configure the service:
   - **Name**: `prism-api`
   - **Region**: Select the SAME region as your DB and Redis.
   - **Branch**: `main`
   - **Environment**: `Docker`
5. Render will automatically detect the `Dockerfile` at the root of the repository and use it to build your application container.

---

## Step 4: Configure Environment Variables

Before clicking create, scroll down to the **Environment Variables** section on the Web Service creation page and add the following keys:

| Key | Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://...` | The modified URL from Step 1. |
| `REDIS_URL` | `redis://...` | The Internal Redis URL from Step 2. |
| `GROQ_API_KEY` | `gsk_...` | Your Groq API Key for the LLM agents. |
| `GITHUB_TOKEN` | `ghp_...` | GitHub Personal Access Token for the bot. |
| `GITHUB_WEBHOOK_SECRET` | `your_secret_string` | Secure random string to authenticate GitHub hooks. |
| `ENVIRONMENT` | `production` | Set to `production` to disable debug traces. |
| `PROJECT_NAME` | `PRism AI` | Display name for logs and API documentation. |

Once all environment variables are added, click **Create Web Service**.

---

## Step 5: Verification & Health Checks

Render will now build your Docker container and deploy it. Wait for the deploy logs to state **"Your service is live 🎉"**.

### 1. API Health Verification
Visit your public Render URL at `/api/v1/health`:
```
https://prism-api-xxxx.onrender.com/api/v1/health
```
You should receive a JSON response confirming that `fastapi`, `database`, `redis`, and core services are `"healthy"`.

### 2. Dashboard Verification
Open the Command Center UI:
```
https://prism-api-xxxx.onrender.com/dashboard
```
The Dashboard should load successfully, demonstrating that the application server and static assets are fully functional.

---

## Step 6: GitHub Webhook Configuration

Finally, connect GitHub repository events to your deployed PRism agent:
1. Go to your GitHub Repository -> **Settings** -> **Webhooks** -> **Add webhook**.
2. **Payload URL**: `https://prism-api-xxxx.onrender.com/api/v1/github/webhook`
3. **Content type**: `application/json`
4. **Secret**: Enter the exact string you used for `GITHUB_WEBHOOK_SECRET` in Step 4.
5. **Which events**: Select **Let me select individual events** and check **Pull requests** and **Pull request reviews**.
6. Click **Add webhook**.

Your AI Pull Request Reviewer is now fully deployed and operational!
