"""Database session utilities for SQLite-backed API operations."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .queries import ensure_schema


def get_database_path() -> Path:
    """Resolve sqlite path from env with a sensible local default."""
    raw = os.getenv("LEADBOT_DB_PATH", "backend/.data/leadbot.db")
    path = Path(raw)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a sqlite connection configured with row mapping and ensured schema."""
    conn = sqlite3.connect(str(get_database_path()))
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    try:
        yield conn
    finally:
        conn.close()
