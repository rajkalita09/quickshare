"""SQLite helpers for share metadata."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS shares (
    token TEXT PRIMARY KEY,
    stored_name TEXT NOT NULL UNIQUE,
    original_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_shares_expires_at ON shares(expires_at);
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(database_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    connection.commit()


def insert_share(
    connection: sqlite3.Connection,
    *,
    token: str,
    stored_name: str,
    original_name: str,
    file_size: int,
    created_at: datetime,
    expires_at: datetime,
) -> None:
    connection.execute(
        """
        INSERT INTO shares (token, stored_name, original_name, file_size, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (token, stored_name, original_name, file_size, to_iso(created_at), to_iso(expires_at)),
    )
    connection.commit()


def get_share(connection: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    cursor = connection.execute("SELECT * FROM shares WHERE token = ?", (token,))
    return cursor.fetchone()


def delete_share(connection: sqlite3.Connection, token: str) -> None:
    connection.execute("DELETE FROM shares WHERE token = ?", (token,))
    connection.commit()


def list_expired(connection: sqlite3.Connection, now: datetime) -> list[sqlite3.Row]:
    cursor = connection.execute(
        "SELECT * FROM shares WHERE expires_at <= ?",
        (to_iso(now),),
    )
    return cursor.fetchall()
