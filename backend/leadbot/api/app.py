"""FastAPI application wiring for the backend API."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import router as auth_router
from .dependencies import require_auth
from .routes.companies import router as companies_router
from .routes.contacts import router as contacts_router
from .routes.export import router as export_router
from .routes.pipeline import router as pipeline_router
from .routes.runs import router as runs_router
from .routes.signals import router as signals_router
from .routes.stats import router as stats_router
from ..mcp.server import mcp_app

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


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
