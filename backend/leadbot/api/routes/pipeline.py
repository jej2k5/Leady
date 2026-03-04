"""Pipeline ingestion routes."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...db.models import Company, RawCandidate, RunStatus
from ...db.queries import list_companies, persist_raw_candidate, update_run_status
from ...db.session import get_connection
from ...exports.csv_export import OUTREACH_QUEUE_HEADERS, build_outreach_queue_csv
from ...exports.google_sheets import append_rows_to_google_sheets

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class IngestCandidateRequest(BaseModel):
    run_id: int
    candidate: RawCandidate


class CompletePipelineRequest(BaseModel):
    run_id: int


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
