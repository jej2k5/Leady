"""Statistics routes."""

from __future__ import annotations

from fastapi import APIRouter

from ...db.queries import list_companies, list_runs
from ...db.session import get_connection

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def stats_overview() -> dict[str, int | float]:
    with get_connection() as conn:
        runs = list_runs(conn)
        companies = list_companies(conn)

    average_score = 0.0
    if companies:
        average_score = sum(company.score for company in companies) / len(companies)

    return {
        "runs": len(runs),
        "companies": len(companies),
        "completed_runs": len([item for item in runs if item.status.value == "completed"]),
        "average_company_score": round(average_score, 2),
    }
