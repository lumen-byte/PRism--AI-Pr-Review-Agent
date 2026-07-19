# Triggering redeployment (2/2)
import os

from fastapi import APIRouter, Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import auth, dashboard, demo, health, webhook, live
from app.config.settings import settings
from app.core import metrics
from app.core.auth import create_access_token
from app.core.exceptions import setup_exception_handlers
from app.db.database import database_lifespan, get_db
from app.db.models import User
from app.middleware.observability import ObservabilityMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=database_lifespan,
)

# Apply global exception handlers
setup_exception_handlers(app)

# Apply observability middleware
app.add_middleware(ObservabilityMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

api_router = APIRouter()
api_router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(demo.router, prefix="/demo", tags=["demo"])
api_router.include_router(live.router, prefix="/live", tags=["live"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Expose Prometheus metrics endpoint at root /metrics
app.include_router(metrics.router, tags=["metrics"])


def _read_dashboard_html() -> str:
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "static", "index.html"
    )
    with open(path, "r") as f:
        return f.read()


@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(
    _demo: str = Query(None, alias="demo"),
    db: AsyncSession = Depends(get_db),
):
    """Serve the dashboard SPA.

    If the ?demo=1 query parameter is present, look up the admin user,
    generate a JWT, and inject it directly into the HTML via an inline
    <script> tag **before** app.js loads. This guarantees localStorage
    is set synchronously with no redirect race-conditions.
    """
    html = _read_dashboard_html()

    if _demo:
        try:
            result = await db.execute(select(User).where(User.username == "admin"))
            admin = result.scalar_one_or_none()
            if admin:
                token = create_access_token(subject=admin.username, role=admin.role.name)
                inject = (
                    f'<script>'
                    f'alert("Token injected successfully! Token starts with: {token[:10]}...");'
                    f'localStorage.setItem("prism_token","{token}");'
                    f'</script>'
                )
                html = html.replace("</head>", inject + "</head>", 1)
            else:
                inject = "<script>alert('Demo user NOT FOUND in database!');</script>"
                html = html.replace("</head>", inject + "</head>", 1)
        except Exception as e:
            import logging
            logging.error(f"Demo injection failed: {e}")
            import traceback
            tb = traceback.format_exc()
            return HTMLResponse(
                content=f"<div style='background:red;color:white;padding:20px;font-family:monospace'><h3>Demo Injection Failed</h3><pre>{tb}</pre></div>",
                status_code=500
            )

    return HTMLResponse(content=html)


app.include_router(api_router, prefix=settings.API_V1_STR)
