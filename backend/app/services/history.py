"""Persistent, local SQLite storage for generated summaries."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "history.sqlite3"


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    path = Path(os.getenv("HISTORY_DB_PATH", str(DEFAULT_DB_PATH))).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                summary TEXT NOT NULL,
                length TEXT NOT NULL,
                provider TEXT NOT NULL,
                original_word_count INTEGER NOT NULL,
                summary_word_count INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )
        with connection:
            yield connection
    finally:
        connection.close()


def save_summary(
    *, text: str, summary: str, length: str, provider: str,
    original_word_count: int, summary_word_count: int,
) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO summaries
                (text, summary, length, provider, original_word_count, summary_word_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (text, summary, length, provider, original_word_count, summary_word_count),
        )


def list_summaries() -> list[dict]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, text AS original_text, summary AS summary_text, "
            "length AS summary_length, provider, original_word_count, "
            "summary_word_count, created_at FROM summaries "
            "ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_summary(summary_id: int) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, text AS original_text, summary AS summary_text, "
            "length AS summary_length, provider, original_word_count, "
            "summary_word_count, created_at FROM summaries WHERE id = ?",
            (summary_id,),
        ).fetchone()
    return dict(row) if row else None


def delete_summary(summary_id: int) -> bool:
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM summaries WHERE id = ?", (summary_id,))
        return cursor.rowcount > 0


def clear_history() -> None:
    with _connect() as connection:
        connection.execute("DELETE FROM summaries")
