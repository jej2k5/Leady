"""Export routes."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from ...db.queries import list_companies
from ...db.session import get_connection

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
