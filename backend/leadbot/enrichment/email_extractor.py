"""Email extraction helpers."""

from __future__ import annotations

import re

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def extract_emails(text: str) -> list[str]:
    """Extract de-duplicated emails preserving first-seen order."""
    seen: set[str] = set()
    emails: list[str] = []
    for match in EMAIL_REGEX.findall(text or ""):
        lowered = match.lower().strip(".")
        if lowered in seen:
            continue
        seen.add(lowered)
        emails.append(lowered)
    return emails
