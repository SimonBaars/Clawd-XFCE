"""Persistent conversations, summaries, and long-term memories."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from clippy_xfce.paths import db_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    created REAL NOT NULL,
    updated REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created REAL NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    importance INTEGER NOT NULL DEFAULT 1,
    created REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, id);
CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind, created);
"""


@dataclass
class Conversation:
    id: int
    title: str
    summary: str
    created: float
    updated: float


@dataclass
class Memory:
    id: int
    kind: str
    text: str
    importance: int
    created: float


class MemoryStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def create_conversation(self, title: str = "New chat") -> Conversation:
        now = time.time()
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO conversations (title, summary, created, updated) VALUES (?, '', ?, ?)",
                (title, now, now),
            )
            return Conversation(int(cur.lastrowid), title, "", now, now)

    def get_conversation(self, conversation_id: int) -> Conversation | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        return self._conv(row) if row else None

    def list_conversations(self, limit: int = 50) -> list[Conversation]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY updated DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._conv(row) for row in rows]

    def delete_conversation(self, conversation_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

    def rename_conversation(self, conversation_id: int, title: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE conversations SET title = ?, updated = ? WHERE id = ?",
                (title, time.time(), conversation_id),
            )

    def set_summary(self, conversation_id: int, summary: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE conversations SET summary = ?, updated = ? WHERE id = ?",
                (summary, time.time(), conversation_id),
            )

    def add_message(self, conversation_id: int, role: str, content: Any) -> None:
        payload = json.dumps(content, ensure_ascii=False)
        now = time.time()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content, created) VALUES (?, ?, ?, ?)",
                (conversation_id, role, payload, now),
            )
            conn.execute(
                "UPDATE conversations SET updated = ? WHERE id = ?",
                (now, conversation_id),
            )
            row = conn.execute(
                "SELECT title FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if row and row["title"] in ("New chat", "New conversation"):
                title = _title_from_content(content)
                if title:
                    conn.execute(
                        "UPDATE conversations SET title = ? WHERE id = ?",
                        (title, conversation_id),
                    )

    def messages(self, conversation_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id",
                (conversation_id,),
            ).fetchall()
        return [{"role": row["role"], "content": json.loads(row["content"])} for row in rows]

    def recent_summaries(self, limit: int = 8, exclude: int | None = None) -> list[Conversation]:
        sql = "SELECT * FROM conversations WHERE summary != ''"
        args: list[Any] = []
        if exclude is not None:
            sql += " AND id != ?"
            args.append(exclude)
        sql += " ORDER BY updated DESC LIMIT ?"
        args.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, args).fetchall()
        return [self._conv(row) for row in rows]

    def remember(self, text: str, kind: str = "fact", importance: int = 1) -> Memory:
        now = time.time()
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT id FROM memories WHERE text = ?", (text,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE memories SET importance = MAX(importance, ?), kind = ? WHERE id = ?",
                    (importance, kind, existing["id"]),
                )
                return Memory(int(existing["id"]), kind, text, importance, now)
            cur = conn.execute(
                "INSERT INTO memories (kind, text, importance, created) VALUES (?, ?, ?, ?)",
                (kind, text, importance, now),
            )
            return Memory(int(cur.lastrowid), kind, text, importance, now)

    def forget(self, memory_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

    def search_memories(self, query: str, limit: int = 12) -> list[Memory]:
        like = f"%{query}%"
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM memories
                WHERE text LIKE ? OR kind LIKE ?
                ORDER BY importance DESC, created DESC
                LIMIT ?
                """,
                (like, like, limit),
            ).fetchall()
        return [self._mem(row) for row in rows]

    def all_memories(self, limit: int = 40) -> list[Memory]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY importance DESC, created DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._mem(row) for row in rows]

    def context_block(self, conversation_id: int | None = None) -> str:
        memories = self.all_memories()
        summaries = self.recent_summaries(exclude=conversation_id)
        lines = ["Long-term memories:"]
        if memories:
            lines.extend(f"- ({mem.kind}) {mem.text}" for mem in memories)
        else:
            lines.append("- (none yet)")
        lines.append("Recent conversation summaries:")
        if summaries:
            lines.extend(f"- {item.title}: {item.summary}" for item in summaries)
        else:
            lines.append("- (none yet)")
        return "\n".join(lines)

    @staticmethod
    def _conv(row: sqlite3.Row) -> Conversation:
        return Conversation(
            id=int(row["id"]),
            title=row["title"],
            summary=row["summary"],
            created=float(row["created"]),
            updated=float(row["updated"]),
        )

    @staticmethod
    def _mem(row: sqlite3.Row) -> Memory:
        return Memory(
            id=int(row["id"]),
            kind=row["kind"],
            text=row["text"],
            importance=int(row["importance"]),
            created=float(row["created"]),
        )


def _title_from_content(content: Any) -> str:
    text = first_text(content)
    text = " ".join(text.split())
    if not text:
        return ""
    return text[:72] + ("…" if len(text) > 72 else "")


def first_text(content: Any) -> str:
    return primary_text(content)


def primary_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                return str(block.get("text") or "")
            if isinstance(block, str):
                return block
        return ""
    if isinstance(content, dict) and content.get("type") == "text":
        return str(content.get("text") or "")
    return ""


def iter_text_blocks(content: Any) -> Iterable[str]:
    text = first_text(content)
    if text:
        yield text
