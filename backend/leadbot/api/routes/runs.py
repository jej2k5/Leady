"""Run lifecycle routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from ..auth.authy_setup import AuthUser
from ..dependencies import require_auth
from ...db.models import RunStatus, RunSummary
from ...db.queries import create_run, list_runs, update_run_status
from ...db.session import get_connection

router = APIRouter(prefix="/api/runs", tags=["runs"])


class CreateRunRequest(BaseModel):
    status: RunStatus = RunStatus.queued


class UpdateRunStatusRequest(BaseModel):
    status: RunStatus


@router.get("", response_model=list[RunSummary])
def get_runs() -> list[RunSummary]:
    with get_connection() as conn:
        return list_runs(conn)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_run_route(
    payload: CreateRunRequest,
    current_user: AuthUser = Depends(require_auth),
) -> dict[str, int]:
    with get_connection() as conn:
        run_id = create_run(conn, user_id=current_user.id, status=payload.status)
    return {"run_id": run_id}


@router.patch("/{run_id}")
def update_run(run_id: int, payload: UpdateRunStatusRequest) -> dict[str, str]:
    with get_connection() as conn:
        update_run_status(conn, run_id, payload.status)
    return {"detail": "updated"}
