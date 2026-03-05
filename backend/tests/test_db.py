from __future__ import annotations

from leadbot.db.models import Company, Contact, ContactType, RunStatus, Signal, SignalType
from leadbot.db.queries import (
    create_company,
    create_contact,
    create_run,
    create_signal,
    list_companies,
    list_contacts_for_company,
    list_discovery_candidates,
    list_runs,
    mark_discovery_candidate_seeded,
    search_companies,
    update_run_status,
    upsert_company,
    upsert_discovery_candidate,
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


def test_discovery_candidate_upsert_and_seed_marking() -> None:
    with get_connection() as conn:
        upsert_discovery_candidate(
            conn,
            company_name="Acme",
            domain="https://acme.io",
            source_type="funding",
            source_url="https://news.example.com/acme",
            evidence={"source_group": "funding", "text": "Acme raised"},
            score=0.7,
        )
        candidate = upsert_discovery_candidate(
            conn,
            company_name="ACME",
            domain="acme.io",
            source_type="hiring",
            source_url="https://jobs.example.com/acme",
            evidence={"source_group": "hiring", "description": "Hiring engineers"},
            score=0.8,
        )
        unseeded = list_discovery_candidates(conn, status="unseeded")

        mark_discovery_candidate_seeded(conn, int(candidate["id"]))
        seeded = list_discovery_candidates(conn, status="seeded")

    assert len(unseeded) == 1
    assert len(unseeded[0]["evidence"]) == 2
    assert unseeded[0]["score"] == 0.8
    assert len(seeded) == 1
