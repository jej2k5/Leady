"""Contact routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from ...db.models import Contact
from ...db.queries import create_contact, list_contacts_for_company, search_contacts
from ...db.session import get_connection

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=list[Contact])
def get_contacts(
    company_id: int | None = Query(default=None),
    q: str | None = Query(default=None, min_length=1),
) -> list[Contact]:
    with get_connection() as conn:
        if q:
            return search_contacts(conn, q)
        if company_id is None:
            return []
        return list_contacts_for_company(conn, company_id)


@router.post("", response_model=Contact, status_code=status.HTTP_201_CREATED)
def create_contact_route(contact: Contact) -> Contact:
    with get_connection() as conn:
        return create_contact(conn, contact)
