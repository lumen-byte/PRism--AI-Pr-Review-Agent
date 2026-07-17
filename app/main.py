import os

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, dashboard, demo, health, webhook, live
from app.config.settings import settings
from app.core import metrics
from app.core.exceptions import setup_exception_handlers
from app.db.database import database_lifespan
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


@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard():
    # Read the dashboard file from static folder
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "static", "index.html"
    )
    with open(path, "r") as f:
        return HTMLResponse(content=f.read())


app.include_router(api_router, prefix=settings.API_V1_STR)
