"""Conversation storage via SQLite."""

from __future__ import annotations

import json
import random
import sqlite3
import string
from datetime import UTC, datetime
from pathlib import Path

from orcx.schema import Conversation, Message

DB_PATH = Path.home() / ".config" / "orcx" / "conversations.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    agent TEXT,
    title TEXT,
    messages TEXT NOT NULL,
    total_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_updated ON conversations(updated_at DESC);
"""

_schema_initialized_for: str | None = None


def _connect() -> sqlite3.Connection:
    """Get database connection, creating schema if needed."""
    global _schema_initialized_for
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Re-init schema if DB path changed (e.g., in tests)
    db_path_str = str(DB_PATH)
    if _schema_initialized_for != db_path_str:
        conn.executescript(SCHEMA)
        _schema_initialized_for = db_path_str
    return conn


def _generate_id() -> str:
    """Generate 4-char base36 ID."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(4))


def _now() -> str:
    """ISO timestamp."""
    return datetime.now(UTC).isoformat()


class ConversationCorruptedError(Exception):
    """Raised when conversation data cannot be parsed."""

    def __init__(self, conv_id: str, details: str):
        self.conv_id = conv_id
        super().__init__(f"Corrupted conversation {conv_id}: {details}")


def _row_to_conversation(row: sqlite3.Row) -> Conversation:
    """Convert database row to Conversation object."""
    conv_id = row["id"]
    try:
        messages = [Message(**m) for m in json.loads(row["messages"])]
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        raise ConversationCorruptedError(conv_id, str(e)) from e

    return Conversation(
        id=conv_id,
        model=row["model"],
        agent=row["agent"],
        title=row["title"],
        messages=messages,
        total_tokens=row["total_tokens"],
        total_cost=row["total_cost"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create(model: str, agent: str | None = None) -> Conversation:
    """Create a new conversation."""
    now = _now()
    with _connect() as conn:
        for _ in range(10):  # Retry on ID collision
            conv_id = _generate_id()
            try:
                conn.execute(
                    """
                    INSERT INTO conversations
                        (id, model, agent, title, messages, total_tokens, total_cost,
                         created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (conv_id, model, agent, None, "[]", 0, 0.0, now, now),
                )
                return Conversation(
                    id=conv_id,
                    model=model,
                    agent=agent,
                    messages=[],
                    created_at=now,
                    updated_at=now,
                )
            except sqlite3.IntegrityError:
                continue
        raise RuntimeError("Failed to generate unique conversation ID")


def get(conv_id: str) -> Conversation | None:
    """Get conversation by ID."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    if not row:
        return None
    return _row_to_conversation(row)


def get_last() -> Conversation | None:
    """Get most recently updated conversation."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    return _row_to_conversation(row)


def update(conv: Conversation) -> None:
    """Update conversation in database. Raises ValueError if not found."""
    conv.updated_at = _now()
    with _connect() as conn:
        cursor = conn.execute(
            """
            UPDATE conversations
            SET model = ?, agent = ?, title = ?, messages = ?,
                total_tokens = ?, total_cost = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                conv.model,
                conv.agent,
                conv.title,
                json.dumps([m.model_dump() for m in conv.messages]),
                conv.total_tokens,
                conv.total_cost,
                conv.updated_at,
                conv.id,
            ),
        )
    if cursor.rowcount == 0:
        raise ValueError(f"Conversation {conv.id} not found")


def list_recent(limit: int = 20) -> list[Conversation]:
    """List recent conversations."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_conversation(row) for row in rows]


def delete(conv_id: str) -> bool:
    """Delete conversation by ID. Returns True if deleted."""
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    return cursor.rowcount > 0


def clean(days: int = 30) -> int:
    """Delete conversations older than N days. Returns count deleted."""
    with _connect() as conn:
        # Normalize ISO timestamps (replace T with space, strip tz) for comparison
        # Use datetime('now', 'utc', ...) since updated_at stores UTC timestamps
        cursor = conn.execute(
            """DELETE FROM conversations
               WHERE substr(replace(updated_at, 'T', ' '), 1, 19) < datetime('now', 'utc', ?)""",
            (f"-{days} days",),
        )
    return cursor.rowcount
