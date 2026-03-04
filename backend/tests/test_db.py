from __future__ import annotations

from leadbot.db.models import Company, Contact, ContactType, RunStatus, Signal, SignalType
from leadbot.db.queries import (
    create_company,
    create_contact,
    create_run,
    create_signal,
    list_companies,
    list_contacts_for_company,
    list_runs,
    search_companies,
    update_run_status,
    upsert_company,
)
from leadbot.db.session import get_connection


def test_db_schema_and_query_flows() -> None:
    with get_connection() as conn:
        run_id = create_run(conn, user_id=None, status=RunStatus.running)
        company = create_company(conn, Company(run_id=run_id, name="Acme", domain="acme.io", score=12.5, metadata={"tier": "a"}))
        create_signal(conn, Signal(company_id=int(company.id), signal_type=SignalType.intent, value="pricing_page", confidence=0.7))
        create_contact(
            conn,
            Contact(company_id=int(company.id), full_name="Alex", contact_type=ContactType.email, contact_value="alex@acme.io"),
        )
        updated = upsert_company(conn, Company(run_id=run_id, name="Acme", domain="acme.io", score=90, metadata={"tier": "b"}))
        update_run_status(conn, run_id, RunStatus.completed)

        runs = list_runs(conn)
        companies = list_companies(conn, run_id=run_id)
        searched = search_companies(conn, "acme")
        contacts = list_contacts_for_company(conn, int(company.id))

    assert updated.score == 90
    assert runs[0].status == RunStatus.completed
    assert companies[0].metadata["tier"] == "b"
    assert searched[0].id == company.id
    assert contacts[0].contact_value == "alex@acme.io"
