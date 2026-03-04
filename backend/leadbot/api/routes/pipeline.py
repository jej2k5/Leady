"""Pipeline ingestion routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...db.models import Company, RawCandidate
from ...db.queries import persist_raw_candidate
from ...db.session import get_connection

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class IngestCandidateRequest(BaseModel):
    run_id: int
    candidate: RawCandidate


@router.post("/ingest", response_model=Company, status_code=status.HTTP_201_CREATED)
def ingest_candidate(payload: IngestCandidateRequest) -> Company:
    with get_connection() as conn:
        try:
            return persist_raw_candidate(conn, payload.run_id, payload.candidate)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
