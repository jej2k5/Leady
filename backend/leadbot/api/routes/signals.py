"""Signal routes."""

from __future__ import annotations

from fastapi import APIRouter, status

from ...db.models import Signal
from ...db.queries import create_signal, list_signals_for_company
from ...db.session import get_connection

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/company/{company_id}", response_model=list[Signal])
def get_company_signals(company_id: int) -> list[Signal]:
    with get_connection() as conn:
        return list_signals_for_company(conn, company_id)


@router.post("", response_model=Signal, status_code=status.HTTP_201_CREATED)
def create_signal_route(signal: Signal) -> Signal:
    with get_connection() as conn:
        return create_signal(conn, signal)
