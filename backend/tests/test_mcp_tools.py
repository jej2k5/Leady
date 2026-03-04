from __future__ import annotations

from leadbot.db.models import Company, Contact, ContactType, Signal, SignalType
from leadbot.db.queries import create_company, create_contact, create_run, create_signal
from leadbot.db.session import get_connection
from leadbot.mcp.tools import execute_tool


def test_mcp_tool_handlers_round_trip_data() -> None:
    with get_connection() as conn:
        run_id = create_run(conn, user_id=None)
        company = create_company(conn, Company(run_id=run_id, name="Acme", domain="acme.io", score=77))
        create_signal(
            conn,
            Signal(company_id=int(company.id), source_id=None, signal_type=SignalType.hiring, value="active_hiring", confidence=0.8),
        )
        create_contact(
            conn,
            Contact(
                company_id=int(company.id),
                full_name="Lin",
                contact_type=ContactType.email,
                contact_value="lin@acme.io",
            ),
        )

    search = execute_tool("leady.search_companies", {"query": "acme"})
    assert search["companies"][0]["name"] == "Acme"

    details = execute_tool("get_company", {"company_id": company.id})
    assert details["company"]["domain"] == "acme.io"

    leads = execute_tool("get_top_leads", {"limit": 1})
    assert leads["leads"][0]["score"] == 77.0

    contacts = execute_tool("get_contacts", {"company_id": company.id})
    assert contacts["contacts"][0]["contact_value"] == "lin@acme.io"


def test_mcp_unknown_tool_raises() -> None:
    try:
        execute_tool("missing.tool", {})
    except ValueError as exc:
        assert "Unknown tool" in str(exc)
    else:
        raise AssertionError("expected ValueError")
