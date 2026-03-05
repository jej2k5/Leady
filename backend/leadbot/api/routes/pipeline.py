"""Pipeline ingestion routes."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...db.models import Company, RawCandidate, RunStatus
from ...db.queries import create_run, list_companies, persist_raw_candidate, update_run_status
from ...db.session import get_connection
from ...exports.csv_export import OUTREACH_QUEUE_HEADERS, build_outreach_queue_csv
from ...exports.google_sheets import append_rows_to_google_sheets
from ...jobs.discovery_pipeline_job import DiscoveryPipelineConfig, run_discovery_pipeline_job
from ...pipeline.orchestrator import run_pipeline_for_run
from ..dependencies import require_auth

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class IngestCandidateRequest(BaseModel):
    run_id: int
    candidate: RawCandidate


class CompletePipelineRequest(BaseModel):
    run_id: int


class StartPipelineRequest(BaseModel):
    days: int = 30
    sources: str = "funding,hiring,github"
    include_unknown_stage: bool = False
    source_seed_data: dict[str, list[dict[str, str | int | float | bool | None]]] = Field(default_factory=dict)


class AutoStartPipelineRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=365)
    sources: str = "funding,hiring,github"
    categories: list[str] = Field(default_factory=list)
    max_candidates: int = Field(default=25, ge=1, le=1000)


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
def start_pipeline(
    payload: StartPipelineRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_auth),
) -> dict[str, object]:
    with get_connection() as conn:
        run_id = create_run(conn, user_id=int(current_user.get("sub")) if current_user.get("sub") else None)

    background_tasks.add_task(
        run_pipeline_for_run,
        run_id,
        days=payload.days,
        sources=payload.sources,
        include_unknown_stage=payload.include_unknown_stage,
        source_seed_data=payload.source_seed_data or None,
    )

    return {"run_id": run_id, "status": "queued"}


@router.post("/ingest", response_model=Company, status_code=status.HTTP_201_CREATED)
def ingest_candidate(payload: IngestCandidateRequest) -> Company:
    with get_connection() as conn:
        try:
            return persist_raw_candidate(conn, payload.run_id, payload.candidate)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/complete")
def complete_pipeline(payload: CompletePipelineRequest) -> dict[str, object]:
    with get_connection() as conn:
        update_run_status(conn, payload.run_id, RunStatus.completed)
        companies = list_companies(conn, run_id=payload.run_id)

    csv_content = build_outreach_queue_csv(companies)
    reader = csv.DictReader(io.StringIO(csv_content))
    headers = reader.fieldnames or OUTREACH_QUEUE_HEADERS
    rows = [[row.get(header, "") for header in headers] for row in reader]
    sheets_result = append_rows_to_google_sheets(headers, rows)

    return {
        "detail": "pipeline completed",
        "run_id": payload.run_id,
        "exports": {
            "outreach_queue": f"/api/export/outreach_queue.csv?run_id={payload.run_id}",
            "raw_candidates": f"/api/export/raw_candidates.csv?run_id={payload.run_id}",
            "google_sheets": sheets_result,
        },
    }


@router.post("/auto-start", status_code=status.HTTP_202_ACCEPTED)
def auto_start_pipeline(
    payload: AutoStartPipelineRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_auth),
) -> dict[str, object]:
    config = DiscoveryPipelineConfig.model_validate(payload.model_dump())
    user_id = int(current_user.get("sub")) if current_user.get("sub") else None
    background_tasks.add_task(run_discovery_pipeline_job, config, user_id=user_id)
    return {"status": "queued", "detail": "auto discovery pipeline job scheduled"}
