"""Centralized SQL statements and data access helpers."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from .models import Company, Contact, RawCandidate, RunStatus, RunSummary, Signal, User

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        full_name TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        status TEXT NOT NULL DEFAULT 'queued',
        started_at TEXT,
        completed_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        name TEXT NOT NULL,
        domain TEXT,
        industry TEXT,
        employee_count INTEGER,
        location TEXT,
        score REAL NOT NULL DEFAULT 0,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES runs(id),
        UNIQUE(run_id, name, domain)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        source_type TEXT NOT NULL,
        source_url TEXT,
        payload_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id),
        UNIQUE(company_id, source_type, source_url)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        source_id INTEGER,
        signal_type TEXT NOT NULL,
        value TEXT NOT NULL,
        confidence REAL NOT NULL DEFAULT 0,
        observed_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id),
        FOREIGN KEY (source_id) REFERENCES sources(id),
        UNIQUE(company_id, signal_type, value)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        title TEXT,
        contact_type TEXT NOT NULL,
        contact_value TEXT NOT NULL,
        is_primary INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id),
        UNIQUE(company_id, contact_type, contact_value)
    )
    """,
)

INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS idx_runs_user_id ON runs(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_companies_run_id ON companies(run_id)",
    "CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain)",
    "CREATE INDEX IF NOT EXISTS idx_sources_company_id ON sources(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_signals_company_id ON signals(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id)",
)


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)
    for statement in INDEX_STATEMENTS:
        conn.execute(statement)
    conn.commit()


def _row_to_user(row: sqlite3.Row) -> User:
    return User.model_validate(dict(row))


def _row_to_company(row: sqlite3.Row) -> Company:
    payload = dict(row)
    payload["metadata"] = json.loads(payload.pop("metadata_json") or "{}")
    return Company.model_validate(payload)


def _row_to_signal(row: sqlite3.Row) -> Signal:
    return Signal.model_validate(dict(row))


def _row_to_contact(row: sqlite3.Row) -> Contact:
    payload = dict(row)
    payload["is_primary"] = bool(payload["is_primary"])
    return Contact.model_validate(payload)


def create_user(conn: sqlite3.Connection, user: User) -> User:
    now = utcnow()
    cursor = conn.execute(
        """
        INSERT INTO users (email, full_name, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (str(user.email), user.full_name, now, now),
    )
    conn.commit()
    return get_user(conn, int(cursor.lastrowid))


def get_user(conn: sqlite3.Connection, user_id: int) -> User:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise ValueError(f"User {user_id} not found")
    return _row_to_user(row)


def list_users(conn: sqlite3.Connection) -> list[User]:
    rows = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    return [_row_to_user(row) for row in rows]


def upsert_user(conn: sqlite3.Connection, user: User) -> User:
    now = utcnow()
    conn.execute(
        """
        INSERT INTO users (email, full_name, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            full_name = excluded.full_name,
            updated_at = excluded.updated_at
        """,
        (str(user.email), user.full_name, now, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (str(user.email),)).fetchone()
    assert row is not None
    return _row_to_user(row)


def create_run(conn: sqlite3.Connection, user_id: int | None, status: RunStatus = RunStatus.queued) -> int:
    now = utcnow()
    started_at = now if status == RunStatus.running else None
    cursor = conn.execute(
        """
        INSERT INTO runs (user_id, status, started_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, status.value, started_at, now),
    )
    conn.commit()
    return int(cursor.lastrowid)


def update_run_status(conn: sqlite3.Connection, run_id: int, status: RunStatus) -> None:
    completed_at = utcnow() if status in {RunStatus.completed, RunStatus.failed} else None
    conn.execute(
        """
        UPDATE runs
        SET status = ?,
            completed_at = COALESCE(?, completed_at)
        WHERE id = ?
        """,
        (status.value, completed_at, run_id),
    )
    conn.commit()


def list_runs(conn: sqlite3.Connection) -> list[RunSummary]:
    rows = conn.execute(
        """
        SELECT
            r.id AS run_id,
            r.status,
            r.started_at,
            r.completed_at,
            COUNT(DISTINCT c.id) AS companies_discovered,
            COUNT(DISTINCT s.id) AS signals_collected,
            COUNT(DISTINCT ct.id) AS contacts_collected
        FROM runs r
        LEFT JOIN companies c ON c.run_id = r.id
        LEFT JOIN signals s ON s.company_id = c.id
        LEFT JOIN contacts ct ON ct.company_id = c.id
        GROUP BY r.id
        ORDER BY r.id DESC
        """
    ).fetchall()
    return [RunSummary.model_validate(dict(row)) for row in rows]


def create_company(conn: sqlite3.Connection, company: Company) -> Company:
    now = utcnow()
    cursor = conn.execute(
        """
        INSERT INTO companies (
            run_id, name, domain, industry, employee_count, location, score, metadata_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company.run_id,
            company.name,
            company.domain,
            company.industry,
            company.employee_count,
            company.location,
            company.score,
            json.dumps(company.metadata),
            now,
            now,
        ),
    )
    conn.commit()
    return get_company(conn, int(cursor.lastrowid))


def get_company(conn: sqlite3.Connection, company_id: int) -> Company:
    row = conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
    if row is None:
        raise ValueError(f"Company {company_id} not found")
    return _row_to_company(row)


def list_companies(conn: sqlite3.Connection, run_id: int | None = None) -> list[Company]:
    if run_id is None:
        rows = conn.execute("SELECT * FROM companies ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM companies WHERE run_id = ? ORDER BY id DESC", (run_id,)).fetchall()
    return [_row_to_company(row) for row in rows]


def search_companies(conn: sqlite3.Connection, query: str) -> list[Company]:
    like = f"%{query}%"
    rows = conn.execute(
        """
        SELECT * FROM companies
        WHERE name LIKE ? OR domain LIKE ? OR industry LIKE ?
        ORDER BY score DESC, id DESC
        """,
        (like, like, like),
    ).fetchall()
    return [_row_to_company(row) for row in rows]


def upsert_company(conn: sqlite3.Connection, company: Company) -> Company:
    now = utcnow()
    conn.execute(
        """
        INSERT INTO companies (
            run_id, name, domain, industry, employee_count, location, score, metadata_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id, name, domain) DO UPDATE SET
            industry = excluded.industry,
            employee_count = excluded.employee_count,
            location = excluded.location,
            score = excluded.score,
            metadata_json = excluded.metadata_json,
            updated_at = excluded.updated_at
        """,
        (
            company.run_id,
            company.name,
            company.domain,
            company.industry,
            company.employee_count,
            company.location,
            company.score,
            json.dumps(company.metadata),
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM companies WHERE run_id IS ? AND name = ? AND domain IS ?",
        (company.run_id, company.name, company.domain),
    ).fetchone()
    assert row is not None
    return _row_to_company(row)


def create_source(
    conn: sqlite3.Connection,
    company_id: int,
    source_type: str,
    source_url: str | None,
    payload: dict[str, object] | None = None,
) -> int:
    now = utcnow()
    cursor = conn.execute(
        """
        INSERT INTO sources (company_id, source_type, source_url, payload_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (company_id, source_type, source_url, json.dumps(payload or {}), now, now),
    )
    conn.commit()
    return int(cursor.lastrowid)


def upsert_source(
    conn: sqlite3.Connection,
    company_id: int,
    source_type: str,
    source_url: str | None,
    payload: dict[str, object] | None = None,
) -> int:
    now = utcnow()
    conn.execute(
        """
        INSERT INTO sources (company_id, source_type, source_url, payload_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(company_id, source_type, source_url) DO UPDATE SET
            payload_json = excluded.payload_json,
            updated_at = excluded.updated_at
        """,
        (company_id, source_type, source_url, json.dumps(payload or {}), now, now),
    )
    conn.commit()
    row = conn.execute(
        """
        SELECT id FROM sources
        WHERE company_id = ? AND source_type = ? AND source_url IS ?
        """,
        (company_id, source_type, source_url),
    ).fetchone()
    assert row is not None
    return int(row["id"])


def list_sources_for_company(conn: sqlite3.Connection, company_id: int) -> list[dict[str, object]]:
    rows = conn.execute("SELECT * FROM sources WHERE company_id = ? ORDER BY id DESC", (company_id,)).fetchall()
    result: list[dict[str, object]] = []
    for row in rows:
        data = dict(row)
        data["payload"] = json.loads(data.pop("payload_json") or "{}")
        result.append(data)
    return result


def create_signal(conn: sqlite3.Connection, signal: Signal) -> Signal:
    cursor = conn.execute(
        """
        INSERT INTO signals (company_id, source_id, signal_type, value, confidence, observed_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            signal.company_id,
            signal.source_id,
            signal.signal_type.value,
            signal.value,
            signal.confidence,
            signal.observed_at.isoformat() if signal.observed_at else None,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM signals WHERE id = ?", (int(cursor.lastrowid),)).fetchone()
    assert row is not None
    return _row_to_signal(row)


def upsert_signal(conn: sqlite3.Connection, signal: Signal) -> Signal:
    conn.execute(
        """
        INSERT INTO signals (company_id, source_id, signal_type, value, confidence, observed_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(company_id, signal_type, value) DO UPDATE SET
            source_id = excluded.source_id,
            confidence = excluded.confidence,
            observed_at = excluded.observed_at
        """,
        (
            signal.company_id,
            signal.source_id,
            signal.signal_type.value,
            signal.value,
            signal.confidence,
            signal.observed_at.isoformat() if signal.observed_at else None,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM signals WHERE company_id = ? AND signal_type = ? AND value = ?",
        (signal.company_id, signal.signal_type.value, signal.value),
    ).fetchone()
    assert row is not None
    return _row_to_signal(row)


def list_signals_for_company(conn: sqlite3.Connection, company_id: int) -> list[Signal]:
    rows = conn.execute("SELECT * FROM signals WHERE company_id = ? ORDER BY id DESC", (company_id,)).fetchall()
    return [_row_to_signal(row) for row in rows]


def create_contact(conn: sqlite3.Connection, contact: Contact) -> Contact:
    now = utcnow()
    cursor = conn.execute(
        """
        INSERT INTO contacts (
            company_id, full_name, title, contact_type, contact_value, is_primary, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            contact.company_id,
            contact.full_name,
            contact.title,
            contact.contact_type.value,
            contact.contact_value,
            int(contact.is_primary),
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (int(cursor.lastrowid),)).fetchone()
    assert row is not None
    return _row_to_contact(row)


def upsert_contact(conn: sqlite3.Connection, contact: Contact) -> Contact:
    now = utcnow()
    conn.execute(
        """
        INSERT INTO contacts (
            company_id, full_name, title, contact_type, contact_value, is_primary, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(company_id, contact_type, contact_value) DO UPDATE SET
            full_name = excluded.full_name,
            title = excluded.title,
            is_primary = excluded.is_primary,
            updated_at = excluded.updated_at
        """,
        (
            contact.company_id,
            contact.full_name,
            contact.title,
            contact.contact_type.value,
            contact.contact_value,
            int(contact.is_primary),
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM contacts WHERE company_id = ? AND contact_type = ? AND contact_value = ?",
        (contact.company_id, contact.contact_type.value, contact.contact_value),
    ).fetchone()
    assert row is not None
    return _row_to_contact(row)


def list_contacts_for_company(conn: sqlite3.Connection, company_id: int) -> list[Contact]:
    rows = conn.execute("SELECT * FROM contacts WHERE company_id = ? ORDER BY is_primary DESC, id DESC", (company_id,)).fetchall()
    return [_row_to_contact(row) for row in rows]


def search_contacts(conn: sqlite3.Connection, query: str) -> list[Contact]:
    like = f"%{query}%"
    rows = conn.execute(
        """
        SELECT * FROM contacts
        WHERE full_name LIKE ? OR title LIKE ? OR contact_value LIKE ?
        ORDER BY is_primary DESC, id DESC
        """,
        (like, like, like),
    ).fetchall()
    return [_row_to_contact(row) for row in rows]


def persist_raw_candidate(conn: sqlite3.Connection, run_id: int, candidate: RawCandidate) -> Company:
    company = upsert_company(
        conn,
        Company(
            run_id=run_id,
            name=candidate.company_name,
            domain=candidate.domain,
            metadata=candidate.metadata,
        ),
    )
    if company.id is None:
        raise ValueError("Persisted company is missing an id")

    source_id = upsert_source(conn, company.id, candidate.source_type.value, candidate.source_url)
    for signal in candidate.signals:
        upsert_signal(conn, signal.model_copy(update={"company_id": company.id, "source_id": source_id}))
    for contact in candidate.contacts:
        upsert_contact(conn, contact.model_copy(update={"company_id": company.id}))
    return company
