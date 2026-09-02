"""SQLite store: users, roles, conversations, per-user memory, audit, spend.

One file, no server, fine well past 50 users. The important part is not the
storage engine — it is that *every* answer is reconstructable afterwards: who
asked, what tools ran with what arguments, what came back, and what it cost.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import time
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email         TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'accounts',
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    REAL NOT NULL
);

-- A role is a whitelist of tool-name prefixes. Deny by default: a tool whose
-- name matches no prefix is never shown to the model, so it cannot be called.
CREATE TABLE IF NOT EXISTS roles (
    name           TEXT PRIMARY KEY,
    description    TEXT NOT NULL DEFAULT '',
    tool_prefixes  TEXT NOT NULL      -- JSON list, e.g. ["sap_", "hana_"]
);

CREATE TABLE IF NOT EXISTS conversations (
    id         TEXT PRIMARY KEY,
    user_email TEXT NOT NULL,
    title      TEXT NOT NULL DEFAULT 'New chat',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    archived   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_email, updated_at DESC);

-- content is the raw Anthropic content-block list, stored verbatim. Thinking
-- blocks included: they must be replayed unchanged on the same model.
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    created_at      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, id);

-- Per-user long-term memory, written by Claude through the memory tool.
-- Scoped per user by construction: user_email is part of the key, so one
-- person's memory can never surface in another person's chat.
CREATE TABLE IF NOT EXISTS memories (
    user_email TEXT NOT NULL,
    path       TEXT NOT NULL,
    content    TEXT NOT NULL,
    updated_at REAL NOT NULL,
    PRIMARY KEY (user_email, path)
);

CREATE TABLE IF NOT EXISTS audit (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              REAL NOT NULL,
    user_email      TEXT NOT NULL,
    conversation_id TEXT,
    kind            TEXT NOT NULL,   -- question | tool_call | answer | denied | error
    detail          TEXT NOT NULL    -- JSON
);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit(user_email, ts DESC);

CREATE TABLE IF NOT EXISTS spend (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            REAL NOT NULL,
    user_email    TEXT NOT NULL,
    model         TEXT NOT NULL,
    input_tokens  INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_read    INTEGER NOT NULL DEFAULT 0,
    cache_write   INTEGER NOT NULL DEFAULT 0,
    cost_inr      REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_spend_user ON spend(user_email, ts DESC);
"""

DEFAULT_ROLES = {
    "owner": ("Everything.", ["sap_", "hana_", "pg_", "ecom_", "oms_", "fct_", "exim_", "jsap_", "gateway_"]),
    "accounts": ("SAP books: ledgers, invoices, turnover, payments.", ["sap_", "hana_", "gateway_"]),
    "sales": ("Sales and orders only. No cash position, no vendor ledgers.", ["oms_", "ecom_", "gateway_"]),
    "factory": ("Production and stock.", ["fct_", "exim_", "gateway_"]),
}


class Store:
    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._seed_roles()
        self._conn.commit()

    def _seed_roles(self) -> None:
        for name, (desc, prefixes) in DEFAULT_ROLES.items():
            self._conn.execute(
                "INSERT OR IGNORE INTO roles (name, description, tool_prefixes) VALUES (?,?,?)",
                (name, desc, json.dumps(prefixes)),
            )

    # -------------------------------------------------------------------- users

    @staticmethod
    def _hash(password: str, salt: str) -> str:
        return hashlib.scrypt(
            password.encode(), salt=salt.encode(), n=2**14, r=8, p=1, dklen=32
        ).hex()

    def create_user(self, email: str, name: str, password: str, role: str = "accounts") -> None:
        salt = secrets.token_hex(16)
        self._conn.execute(
            "INSERT OR REPLACE INTO users (email,name,password_hash,salt,role,active,created_at)"
            " VALUES (?,?,?,?,?,1,?)",
            (email.lower().strip(), name, self._hash(password, salt), salt, role, time.time()),
        )
        self._conn.commit()

    def verify_user(self, email: str, password: str) -> sqlite3.Row | None:
        row = self._conn.execute(
            "SELECT * FROM users WHERE email=? AND active=1", (email.lower().strip(),)
        ).fetchone()
        if not row:
            return None
        expected = self._hash(password, row["salt"])
        # Constant-time: a timing difference here leaks whether the hash matched.
        return row if secrets.compare_digest(expected, row["password_hash"]) else None

    def get_user(self, email: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM users WHERE email=? AND active=1", (email.lower().strip(),)
        ).fetchone()

    def role_prefixes(self, role: str) -> list[str]:
        row = self._conn.execute(
            "SELECT tool_prefixes FROM roles WHERE name=?", (role,)
        ).fetchone()
        # Unknown role => no tools at all. Deny by default, always.
        return json.loads(row["tool_prefixes"]) if row else []

    # ------------------------------------------------------------ conversations

    def new_conversation(self, user_email: str, title: str = "New chat") -> str:
        cid = secrets.token_urlsafe(12)
        now = time.time()
        self._conn.execute(
            "INSERT INTO conversations (id,user_email,title,created_at,updated_at)"
            " VALUES (?,?,?,?,?)",
            (cid, user_email, title, now, now),
        )
        self._conn.commit()
        return cid

    def list_conversations(self, user_email: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id,title,updated_at FROM conversations"
            " WHERE user_email=? AND archived=0 ORDER BY updated_at DESC LIMIT ?",
            (user_email, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def owns_conversation(self, user_email: str, cid: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM conversations WHERE id=? AND user_email=?", (cid, user_email)
        ).fetchone()
        return row is not None

    def set_title(self, cid: str, title: str) -> None:
        self._conn.execute(
            "UPDATE conversations SET title=?, updated_at=? WHERE id=?",
            (title[:80], time.time(), cid),
        )
        self._conn.commit()

    def add_message(self, cid: str, role: str, content: Any) -> None:
        self._conn.execute(
            "INSERT INTO messages (conversation_id,role,content,created_at) VALUES (?,?,?,?)",
            (cid, role, json.dumps(content), time.time()),
        )
        self._conn.execute(
            "UPDATE conversations SET updated_at=? WHERE id=?", (time.time(), cid)
        )
        self._conn.commit()

    def history(self, cid: str) -> list[dict[str, Any]]:
        """The conversation in Anthropic messages= shape, ready to re-send."""
        rows = self._conn.execute(
            "SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id", (cid,)
        ).fetchall()
        return [{"role": r["role"], "content": json.loads(r["content"])} for r in rows]

    # ------------------------------------------------------------------- memory

    def memory_list(self, user_email: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT path,content FROM memories WHERE user_email=? ORDER BY path", (user_email,)
        ).fetchall()
        return [dict(r) for r in rows]

    def memory_get(self, user_email: str, path: str) -> str | None:
        row = self._conn.execute(
            "SELECT content FROM memories WHERE user_email=? AND path=?", (user_email, path)
        ).fetchone()
        return row["content"] if row else None

    def memory_put(self, user_email: str, path: str, content: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO memories (user_email,path,content,updated_at)"
            " VALUES (?,?,?,?)",
            (user_email, path, content, time.time()),
        )
        self._conn.commit()

    def memory_delete(self, user_email: str, path: str) -> None:
        self._conn.execute(
            "DELETE FROM memories WHERE user_email=? AND path=?", (user_email, path)
        )
        self._conn.commit()

    # ------------------------------------------------------------ audit + spend

    def audit(self, user_email: str, cid: str | None, kind: str, detail: Any) -> None:
        self._conn.execute(
            "INSERT INTO audit (ts,user_email,conversation_id,kind,detail) VALUES (?,?,?,?,?)",
            (time.time(), user_email, cid, kind, json.dumps(detail, default=str)[:20000]),
        )
        self._conn.commit()

    def record_spend(self, user_email: str, model: str, usage: dict[str, int], cost_inr: float) -> None:
        self._conn.execute(
            "INSERT INTO spend (ts,user_email,model,input_tokens,output_tokens,"
            "cache_read,cache_write,cost_inr) VALUES (?,?,?,?,?,?,?,?)",
            (
                time.time(),
                user_email,
                model,
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
                usage.get("cache_read_input_tokens", 0),
                usage.get("cache_creation_input_tokens", 0),
                cost_inr,
            ),
        )
        self._conn.commit()

    def spend_today(self, user_email: str) -> float:
        cutoff = time.time() - 86400
        row = self._conn.execute(
            "SELECT COALESCE(SUM(cost_inr),0) AS total FROM spend WHERE user_email=? AND ts>?",
            (user_email, cutoff),
        ).fetchone()
        return float(row["total"])
