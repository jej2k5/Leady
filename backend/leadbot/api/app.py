"""FastAPI application wiring for the backend API."""

from __future__ import annotations

import logging
from asyncio import Task, create_task, sleep
from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from ..config import get_settings
from ..jobs.discovery_pipeline_job import DiscoveryPipelineConfig, run_discovery_pipeline_job
from ..mcp.server import mcp_app
from ..utils.logging import configure_app_logging
from .auth.router import router as auth_router
from .dependencies import require_auth
from .routes.companies import router as companies_router
from .routes.contacts import router as contacts_router
from .routes.export import router as export_router
from .routes.pipeline import router as pipeline_router
from .routes.runs import router as runs_router
from .routes.signals import router as signals_router
from .routes.stats import router as stats_router

settings = get_settings()
configure_app_logging(log_level=settings.core.log_level, log_file=settings.core.log_file)
logger = logging.getLogger(__name__)

app = FastAPI(title="Leady API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(stats_router)
app.include_router(companies_router, dependencies=[Depends(require_auth)])
app.include_router(signals_router, dependencies=[Depends(require_auth)])
app.include_router(contacts_router, dependencies=[Depends(require_auth)])
app.include_router(runs_router, dependencies=[Depends(require_auth)])
app.include_router(pipeline_router, dependencies=[Depends(require_auth)])
app.include_router(export_router, dependencies=[Depends(require_auth)])

app.mount("/mcp", mcp_app)

_auto_start_task: Task[None] | None = None


def _seconds_until_next_hour(hour_utc: int) -> float:
    now = datetime.now(tz=UTC)
    next_run = now.replace(hour=hour_utc, minute=0, second=0, microsecond=0)
    if next_run <= now:
        next_run = next_run + timedelta(days=1)
    return (next_run - now).total_seconds()


async def _auto_discovery_scheduler() -> None:
    while True:
        delay = max(1.0, _seconds_until_next_hour(settings.discovery.auto_start_hour_utc))
        await sleep(delay)
        try:
            run_discovery_pipeline_job(
                DiscoveryPipelineConfig(
                    days=settings.discovery.auto_start_days,
                    sources=settings.discovery.auto_start_sources,
                    categories=settings.discovery.auto_start_categories,
                    max_candidates=settings.discovery.auto_start_max_candidates,
                )
            )
        except Exception:
            logger.exception("Failed to execute scheduled auto discovery pipeline job")


@app.on_event("startup")
async def startup_auto_discovery_scheduler() -> None:
    global _auto_start_task
    if settings.discovery.auto_start_enabled:
        _auto_start_task = create_task(_auto_discovery_scheduler())


@app.on_event("shutdown")
async def shutdown_auto_discovery_scheduler() -> None:
    global _auto_start_task
    if _auto_start_task is not None:
        _auto_start_task.cancel()
        _auto_start_task = None


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
