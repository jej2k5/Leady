"""One-line company blurb generation."""

from __future__ import annotations

from ..utils.text import clean_text, extract_keywords


def generate_one_liner(company_name: str, text: str) -> str:
    """Create a concise summary line for a company."""
    keywords = extract_keywords(text, limit=4)
    if keywords:
        return f"{company_name} appears focused on {', '.join(keywords)}."

    cleaned = clean_text(text)
    if not cleaned:
        return f"{company_name} is a prospective B2B lead."
    return f"{company_name}: {cleaned[:120].rstrip(' ,;:.')}"
