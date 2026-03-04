"""Simple crawler for fetching text content from a URL."""

from __future__ import annotations

import re

from ..utils.http import ThrottledSession, build_throttled_session
from ..utils.text import clean_text


def fetch_page_text(url: str, session: ThrottledSession | None = None) -> str:
    """Fetch page html and return plain-ish text."""
    active_session = session or build_throttled_session()
    response = active_session.get(url)
    html = response.text
    no_script = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    no_style = re.sub(r"<style[\s\S]*?</style>", " ", no_script, flags=re.IGNORECASE)
    no_noscript = re.sub(r"<noscript[\s\S]*?</noscript>", " ", no_style, flags=re.IGNORECASE)
    return clean_text(no_noscript)
