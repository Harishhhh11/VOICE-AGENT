from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import get_settings


def _db_path() -> str:
    url = get_settings().database_url
    if url.startswith("sqlite:///"):
        return url.removeprefix("sqlite:///")
    raise RuntimeError("Initial database adapter supports SQLite; configure PostgreSQL in the production adapter.")


def init_db() -> None:
    path = Path(_db_path())
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                course_interest TEXT,
                qualification TEXT,
                preferred_mode TEXT,
                notes TEXT
            )
            """
        )
        conn.commit()


def save_lead(payload) -> int:
    path = Path(_db_path())
    created_at = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO leads (
                created_at, session_id, name, phone, email,
                course_interest, qualification, preferred_mode, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                payload.session_id,
                payload.name,
                payload.phone,
                payload.email,
                payload.course_interest,
                payload.qualification,
                payload.preferred_mode,
                payload.notes,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)
