from __future__ import annotations

from leadbot.enrichment.domain import infer_company_domain


def test_infer_company_domain_normalizes_host() -> None:
    assert infer_company_domain("http://www.Example.org/about") == "example.org"
    assert infer_company_domain("EXAMPLE.org") == "example.org"
