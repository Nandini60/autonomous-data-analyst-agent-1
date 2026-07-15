"""
Chat History Manager
=====================
SQLite-backed persistent chat sessions and messages per user.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


class ChatHistoryManager:
    """Persistent chat-session storage backed by SQLite."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            self.db_path = Path(__file__).resolve().parent / "chat_history.db"
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── Schema ────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id            TEXT PRIMARY KEY,
                    username      TEXT NOT NULL,
                    title         TEXT DEFAULT 'New Chat',
                    document_name TEXT,
                    created_at    TEXT NOT NULL,
                    updated_at    TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id   TEXT    NOT NULL,
                    role         TEXT    NOT NULL,
                    content      TEXT    NOT NULL,
                    metadata_json TEXT   DEFAULT '{}',
                    timestamp    TEXT    NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sess_user ON sessions(username)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_msg_sess ON messages(session_id)"
            )

    # ── Sessions ──────────────────────────────────────────────

    def create_session(
        self,
        username: str,
        title: str = "New Chat",
        document_name: str | None = None,
    ) -> str:
        """Create a new chat session and return its id."""
        sid = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions VALUES (?,?,?,?,?,?)",
                (sid, username.lower(), title, document_name, now, now),
            )
        return sid

    def get_sessions(self, username: str) -> list[dict]:
        """Return all sessions for *username*, newest first."""
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT s.*, COUNT(m.id) AS message_count
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                WHERE s.username = ?
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                """,
                (username.lower(),),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, session_id: str) -> dict | None:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return dict(row) if row else None

    def delete_session(self, session_id: str):
        with self._conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def rename_session(self, session_id: str, new_title: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id)
            )

    # ── Messages ──────────────────────────────────────────────

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ):
        """Append a message to a session."""
        now = datetime.now().isoformat()
        meta_json = json.dumps(metadata or {}, default=str)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO messages (session_id,role,content,metadata_json,timestamp) VALUES (?,?,?,?,?)",
                (session_id, role, content, meta_json, now),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
            )
            # Auto-title from first user message
            row = conn.execute(
                "SELECT title FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row and row[0] == "New Chat" and role == "user":
                title = content[:50] + ("…" if len(content) > 50 else "")
                conn.execute(
                    "UPDATE sessions SET title = ? WHERE id = ?", (title, session_id)
                )

    def get_messages(self, session_id: str) -> list[dict]:
        """Return all messages in a session, chronologically."""
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,),
            ).fetchall()
        return [
            {
                "role": r["role"],
                "content": r["content"],
                "metadata": json.loads(r["metadata_json"]),
                "timestamp": r["timestamp"],
            }
            for r in rows
        ]
