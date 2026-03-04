from __future__ import annotations

from leadbot.db.models import Contact, ContactType, RawCandidate, Signal, SignalType, SourceType
from leadbot.db.queries import list_contacts_for_company, list_signals_for_company
from leadbot.db.session import get_connection
from leadbot.utils.dedup import normalize_domain, upsert_candidate_company


def test_normalize_domain_handles_urls_and_www() -> None:
    assert normalize_domain("https://www.Example.com/path") == "example.com"
    assert normalize_domain("example.com/") == "example.com"
    assert normalize_domain(None) is None


def test_upsert_candidate_company_persists_and_deduplicates() -> None:
    candidate = RawCandidate(
        company_name=" Acme ",
        domain="WWW.Acme.io/careers",
        source_type=SourceType.website,
        source_url="https://news.example/acme",
        signals=[Signal(company_id=0, signal_type=SignalType.hiring, value="active_hiring", confidence=0.8)],
        contacts=[
            Contact(
                company_id=0,
                full_name="Ava Founder",
                contact_type=ContactType.email,
                contact_value="ava@acme.io",
                is_primary=True,
            )
        ],
    )

    with get_connection() as conn:
        company_first = upsert_candidate_company(conn, run_id=1, candidate=candidate)
        company_second = upsert_candidate_company(conn, run_id=1, candidate=candidate)
        contacts = list_contacts_for_company(conn, int(company_first.id))
        signals = list_signals_for_company(conn, int(company_first.id))

    assert company_first.id == company_second.id
    assert company_first.domain == "acme.io"
    assert len(contacts) == 1
    assert len(signals) == 1
