from __future__ import annotations

from leadbot.enrichment.email_extractor import extract_emails


def test_extract_emails_deduplicates_case_insensitively() -> None:
    text = "Reach us: Team@Example.com, team@example.com, sales@example.com"
    assert extract_emails(text) == ["team@example.com", "sales@example.com"]
