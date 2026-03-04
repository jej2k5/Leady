"""Company CRUD/list routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from ...db.models import Company
from ...db.queries import create_company, get_company, list_companies, search_companies
from ...db.session import get_connection

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[Company])
def get_companies(
    run_id: int | None = Query(default=None),
    q: str | None = Query(default=None, min_length=1),
) -> list[Company]:
    with get_connection() as conn:
        if q:
            return search_companies(conn, q)
        return list_companies(conn, run_id=run_id)


@router.get("/{company_id}", response_model=Company)
def get_company_by_id(company_id: int) -> Company:
    with get_connection() as conn:
        try:
            return get_company(conn, company_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=Company, status_code=status.HTTP_201_CREATED)
def create_company_route(company: Company) -> Company:
    with get_connection() as conn:
        return create_company(conn, company)
