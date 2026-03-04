"""HTTP utilities with throttling, retries, robots checks, and lightweight caching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import threading
import time
from urllib import robotparser
from urllib.parse import urlparse

import requests
from requests import Response, Session

from ..config import get_settings


@dataclass(frozen=True)
class CacheEntry:
    """Small response cache record."""

    response: Response
    expires_at: datetime


class ResponseCache:
    """Thread-safe in-memory response cache."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl = ttl_seconds
        self._entries: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Response | None:
        now = datetime.now(UTC)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                self._entries.pop(key, None)
                return None
            return entry.response

    def set(self, key: str, response: Response) -> None:
        expires = datetime.now(UTC) + timedelta(seconds=self._ttl)
        with self._lock:
            self._entries[key] = CacheEntry(response=response, expires_at=expires)


class RobotsPolicy:
    """Minimal robots.txt policy cache."""

    def __init__(self) -> None:
        self._parsers: dict[str, robotparser.RobotFileParser] = {}
        self._lock = threading.Lock()

    def can_fetch(self, user_agent: str, url: str) -> bool:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        origin = f"{parsed.scheme}://{parsed.netloc}"
        with self._lock:
            parser = self._parsers.get(origin)
            if parser is None:
                parser = robotparser.RobotFileParser()
                parser.set_url(f"{origin}/robots.txt")
                try:
                    parser.read()
                except OSError:
                    return True
                self._parsers[origin] = parser
        return parser.can_fetch(user_agent, url)


class ThrottledSession:
    """Requests wrapper with rate-limiting, retries, robots and cache."""

    def __init__(
        self,
        *,
        min_interval_seconds: float = 0.4,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
        session: Session | None = None,
        cache: ResponseCache | None = None,
        robots: RobotsPolicy | None = None,
    ) -> None:
        settings = get_settings()
        self.user_agent = settings.scraping.user_agent
        self.timeout_seconds = timeout_seconds or settings.scraping.timeout_seconds
        self.max_retries = max_retries if max_retries is not None else settings.scraping.max_retries
        self.min_interval_seconds = min_interval_seconds
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self.cache = cache or ResponseCache()
        self.robots = robots or RobotsPolicy()
        self._last_request_at = 0.0
        self._lock = threading.Lock()

    def get(self, url: str, *, use_cache: bool = True, allow_robots: bool = True) -> Response:
        if allow_robots and not self.robots.can_fetch(self.user_agent, url):
            raise PermissionError(f"Robots policy disallows fetching {url}")

        if use_cache:
            cached = self.cache.get(url)
            if cached is not None:
                return cached

        response = self._retrying_get(url)
        if use_cache and response.ok:
            self.cache.set(url, response)
        return response

    def _retrying_get(self, url: str) -> Response:
        attempts = max(self.max_retries + 1, 1)
        last_exc: Exception | None = None
        for attempt in range(attempts):
            self._throttle()
            try:
                response = self.session.get(url, timeout=self.timeout_seconds)
                if response.status_code >= 500 and attempt < attempts - 1:
                    time.sleep(2**attempt * 0.2)
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_exc = exc
                if attempt == attempts - 1:
                    break
                time.sleep(2**attempt * 0.2)
        assert last_exc is not None
        raise last_exc

    def _throttle(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < self.min_interval_seconds:
                time.sleep(self.min_interval_seconds - elapsed)
            self._last_request_at = time.monotonic()


def build_throttled_session() -> ThrottledSession:
    """Build a session configured from application settings."""
    return ThrottledSession()
