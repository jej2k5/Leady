"""Database initialization helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .queries import ensure_schema


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Initialize SQLite database and create tables/indexes if missing."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn
