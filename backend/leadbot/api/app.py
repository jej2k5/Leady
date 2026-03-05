"""FastAPI application wiring for the backend API."""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from ..config import get_settings
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
