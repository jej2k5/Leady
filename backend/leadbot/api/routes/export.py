"""Export routes."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from ...db.queries import list_companies
from ...db.session import get_connection
from ...exports.csv_export import (
    OUTREACH_QUEUE_HEADERS,
    build_outreach_queue_csv,
    build_raw_candidates_csv,
)
from ...exports.google_sheets import append_rows_to_google_sheets

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/companies.csv")
def export_companies_csv(run_id: int | None = Query(default=None)) -> StreamingResponse:
    with get_connection() as conn:
        companies = list_companies(conn, run_id=run_id)

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["id", "name", "domain", "industry", "employee_count", "location", "score"])
    for company in companies:
        writer.writerow(
            [
                company.id,
                company.name,
                company.domain,
                company.industry,
                company.employee_count,
                company.location,
                company.score,
            ]
        )
    stream.seek(0)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=companies.csv"},
    )


@router.get("/outreach_queue.csv")
def export_outreach_queue_csv(
    run_id: int | None = Query(default=None),
    include_unknown_stage: bool = Query(default=False),
) -> StreamingResponse:
    with get_connection() as conn:
        companies = list_companies(conn, run_id=run_id)
    csv_content = build_outreach_queue_csv(companies, include_unknown_stage=include_unknown_stage)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=outreach_queue.csv"},
    )


@router.get("/raw_candidates.csv")
def export_raw_candidates_csv(run_id: int | None = Query(default=None)) -> StreamingResponse:
    with get_connection() as conn:
        companies = list_companies(conn, run_id=run_id)
    csv_content = build_raw_candidates_csv(companies)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=raw_candidates.csv"},
    )


@router.post("/google-sheets/outreach_queue")
def export_outreach_queue_google_sheets(run_id: int | None = Query(default=None)) -> dict[str, object]:
    with get_connection() as conn:
        companies = list_companies(conn, run_id=run_id)
    csv_content = build_outreach_queue_csv(companies)
    reader = csv.DictReader(io.StringIO(csv_content))
    headers = reader.fieldnames or OUTREACH_QUEUE_HEADERS
    rows = [[row.get(header, "") for header in headers] for row in reader]
    result = append_rows_to_google_sheets(headers, rows)
    return {"filename": "outreach_queue.csv", **result}
