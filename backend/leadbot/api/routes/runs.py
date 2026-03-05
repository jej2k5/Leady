"""Run lifecycle routes."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...db.models import RunStatus, RunSummary
from ...db.queries import create_run, list_runs, update_run_status
from ...db.session import get_connection
from ..dependencies import require_auth

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
    current_user: dict = Depends(require_auth),
) -> dict[str, int]:
    with get_connection() as conn:
        run_id = create_run(conn, user_id=int(current_user.get("sub")) if current_user.get("sub") else None, status=payload.status)
    return {"run_id": run_id}


@router.patch("/{run_id}")
def update_run(run_id: int, payload: UpdateRunStatusRequest) -> dict[str, str]:
    with get_connection() as conn:
        update_run_status(conn, run_id, payload.status)
    return {"detail": "updated"}


@router.get("/{run_id}/stream")
async def stream_run(run_id: int) -> StreamingResponse:
    async def event_generator():
        while True:
            with get_connection() as conn:
                runs = list_runs(conn)

            current = next((run for run in runs if run.run_id == run_id), None)
            if current is None:
                yield f"data: Run {run_id} not found\n\n"
                break

            message = (
                f"Status {current.status.value}. Companies {current.companies_discovered}, "
                f"signals {current.signals_collected}, contacts {current.contacts_collected}."
            )
            yield f"data: {message}\n\n"

            if current.status in {RunStatus.completed, RunStatus.failed}:
                break

            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
