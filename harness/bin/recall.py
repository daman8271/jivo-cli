#!/usr/bin/env python3
"""JIVO harness — `recall`: searchable memory over the team's written record.

Why this exists
---------------
The harness has two memory tiers, both borrowed from NousResearch/hermes-agent
(see harness/research/01-hermes-learning.md):

  1. An always-injected digest — tiny, bounded, in every prompt. Built.
  2. Search over everything ever written down — called on demand, costing
     nothing until it is used. This file.

Hermes' second tier is `session_search`: SQLite FTS5 over every past message,
with a parallel trigram index for substring/misspelling recovery
(`~/.hermes/hermes-agent/hermes_state_search.py`, and the schema in
`hermes_state_common.py:331` / `:391`). JIVO's corpus is not a message table —
it is dated markdown that people (and Claude) actually wrote: work logs, audit
findings, corrections, runbooks. Same problem, different substrate.

Today, answering *"what did we work out about the oil returns escalation last
month?"* means guessing which file to grep. The answer is 324 lines inside
`savings-audit/findings/finding-oil-returns-escalation.md`, mentioned in one
line of `chats/2026-07-28.md`. Nobody finds that by guessing.

RULE 0 is untouched. This module reads local markdown and writes exactly one
file — its own index at `harness/.state/recall.db` (gitignored, derived, never
committed). It issues no business-system call of any kind.

Subcommands
-----------
  index     build/refresh the FTS index over the corpus (incremental)
  search    ranked search; returns heading + snippet + file:line
  stats     what is indexed, how big, how fresh, which search path is live

Design notes
------------
  * CHUNKS ARE HEADING SECTIONS. A whole 800-line work log is a useless search
    result and a single line has no context. Measured over the real corpus,
    H1-H3 sections have a median of 14 lines and a p99 of 67 — already the
    right grain. Only the 16 sections (of 1,127) that run long get split.
  * TWO INDEXES, LIKE HERMES. `porter unicode61` for ranked word search,
    `trigram` for substring/partial/misspelled terms the tokenizer can never
    match. Standard runs first; trigram tops up when it comes back thin.
  * PROBE, NEVER ASSUME. FTS5 and the trigram tokenizer are both optional in a
    SQLite build. Each is probed at open time and the tool degrades one step at
    a time — fts5+trigram -> fts5 -> LIKE over the same chunks -> file scan —
    rather than failing. `stats` always names the live path.
  * ORDINARY FTS5 TABLES, NOT external-content. External-content halves storage
    but makes every delete carry the old column values. At ~1 MB of corpus the
    duplication is free and the sync bug it removes is not. Revisit past ~100 MB.
  * FAIL QUIET, EXIT 0. Anything a hook can call must never block an operator.
    Set JIVO_RECALL_DEBUG=1 to get the traceback instead.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
STATE = HARNESS / ".state"

# Overridable so a test, a hook, or an experiment with a different --corpus can
# use its own index instead of clobbering the operator's. Without this, running
# `index --corpus /some/other/dir` silently replaces the real index with a
# narrower one — a footgun worth one environment variable to remove.
DB_PATH = Path(os.environ["JIVO_RECALL_DB"]) if os.environ.get("JIVO_RECALL_DB") \
    else STATE / "recall.db"

SCHEMA_VERSION = 1

# ── what gets indexed, and why ───────────────────────────────────────────────
#
# The rule: index what a human wrote about a DECISION; do not index what a
# generator wrote about an API.
#
#   chats/              the point of the exercise — dated session work logs
#   savings-audit/      the audit vault. The motivating query ("oil returns
#                       escalation") resolves HERE, not in chats/ — the chat
#                       log only wikilinks to it. Excluding it would return the
#                       one-line mention instead of the 324-line answer.
#   harness/            corrections (the digest injects only the `## Rule` line;
#                       the wrong/right/evidence record stays on disk and is
#                       exactly what you want to search), plus the research and
#                       design notes that explain why the harness behaves as it
#                       does.
#   connections/        system runbooks + inter-system lineage. This is what a
#                       chat log points AT ("documented in SAP-HOME-ACCESS.md").
#   vision/             intent and direction — the "why are we building this".
#   *.md at repo root   README / CLI-HUB-README / CLAUDE.md — the toolkit map.
#
# Deliberately OUT: sap-b1/ (548 files), portals/ (194), exim/ (156),
# control-panel/, factory-cli/, dsr-cli/, tankhapay/, ecom-cli/, oms-cli/.
# Those are generated study vaults and API reference — ~80k lines of material
# that already has a purpose-built lookup path (`sapb1 entities|fields`, the
# MCP catalog tools, each CLI's own --help). Indexing them would bury every
# work-log hit under API stubs, which is the one failure mode that makes a
# search tool stop being used.
#
# This is a default, not a cage: --corpus (repeatable) or JIVO_RECALL_CORPUS
# (os.pathsep- or comma-separated) replaces it entirely.
DEFAULT_CORPUS = [
    "chats",
    "savings-audit",
    "harness",
    "connections",
    "vision",
    ".",  # repo-root *.md only — see _iter_corpus_files
]

# Directory names never walked into, anywhere.
SKIP_DIRS = {
    ".git", ".claude", ".obsidian", ".state", "node_modules", "__pycache__",
    ".venv", "venv", ".mypy_cache", ".pytest_cache", "dist", "build",
}

# A markdown file bigger than this is almost certainly a dump, not a document.
# Skipped with a note rather than silently, so nobody wonders why it never hits.
MAX_FILE_BYTES = 2 * 1024 * 1024

# Chunks longer than this are split at paragraph boundaries. 4,000 chars is
# roughly 60 lines of prose — past the measured p99 section length, so in
# practice this only fires on the handful of genuinely long audit sections.
MAX_CHUNK_CHARS = 4000

# Hermes caps FTS input at 2,048 chars (hermes_state_common.py:122). Same
# reasoning: a search query never needs to be arbitrarily large, and bounding
# it keeps sanitiser behaviour predictable under adversarial input.
MAX_QUERY_CHARS = 2048

# bm25 column weights, in table order (title, heading, tags, body). A hit in a
# document's title is a much stronger signal than the same word buried in a
# paragraph — "oil returns escalation" should surface the finding note whose
# TITLE says that, above the chat log that mentions it in passing.
BM25_WEIGHTS = (4.0, 3.0, 2.0, 1.0)

FTS_STD_SQL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5("
    "title, heading, tags, body, "
    "tokenize='porter unicode61 remove_diacritics 2')"
)
# Stemming ("returns" finds "return") is worth it for prose work logs. It is
# mildly wrong for code identifiers (DocTotal, CardCode) — which is precisely
# what the trigram index below is for.

FTS_TRI_SQL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_tri USING fts5("
    "title, heading, tags, body, tokenize='trigram')"
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _rel(path: Path) -> str:
    """Repo-relative path with POSIX separators.

    Stored and printed this way on every platform: office machines may be
    Windows under git-bash, and an index built there must stay comparable with
    one built on macOS. Backslashes in a stored key would break incrementality
    across machines and make `file:line` pointers unclickable.
    """
    try:
        return path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _corpus_roots(cli_roots: list[str] | None) -> list[str]:
    if cli_roots:
        return list(cli_roots)
    env = os.environ.get("JIVO_RECALL_CORPUS", "").strip()
    if env:
        parts = re.split(r"[,%s]" % re.escape(os.pathsep), env)
        return [p.strip() for p in parts if p.strip()]
    return list(DEFAULT_CORPUS)


def _peek_meta(db_path: Path, key: str) -> str | None:
    """Read one meta value without going through Index.open().

    Needed because the corpus-mismatch guard below has to fire BEFORE
    `_ensure_schema` runs — that is where `--no-trigram` drops a table, and a
    guard that trips after a destructive step is not a guard.
    """
    if not db_path.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        try:
            row = con.execute(
                "SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
            return row[0] if row else None
        finally:
            con.close()
    except sqlite3.Error:
        return None


def _iter_corpus_files(roots: list[str]):
    """Yield (abs_path, rel_posix) for every markdown file in the corpus.

    The literal root "." means *repo-root markdown only* — walking the whole
    repo from "." would pull in every excluded vault by the back door.
    """
    seen: set[str] = set()
    for root in roots:
        base = (REPO / root).resolve() if not os.path.isabs(root) else Path(root).resolve()
        if not base.exists():
            continue
        if root == ".":
            candidates = sorted(base.glob("*.md"))
        elif base.is_file():
            candidates = [base]
        else:
            candidates = []
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [
                    d for d in sorted(dirnames)
                    if d not in SKIP_DIRS and not d.startswith(".")
                ]
                for fn in sorted(filenames):
                    if fn.lower().endswith(".md"):
                        candidates.append(Path(dirpath) / fn)
        for path in candidates:
            rel = _rel(path)
            if rel in seen:
                continue
            seen.add(rel)
            yield path, rel


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


_DATE_IN_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _parse_frontmatter(raw: str) -> tuple[dict, int]:
    """Return (frontmatter dict, line offset of the body).

    Same tolerant hand-parse as harness.py `_parse_frontmatter` — deliberately
    not a YAML dependency (stdlib only) and deliberately forgiving, because a
    malformed header in one note must not cost us the other 95.
    """
    if not raw.startswith("---"):
        return {}, 0
    lines = raw.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, 0
    meta: dict = {}
    for line in lines[1:end]:
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip().strip('"').strip("'")
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k.strip()] = v
    return meta, end + 1


def _doc_meta(rel: str, raw: str, path: Path) -> tuple[dict, int]:
    """Document-level metadata: title, date, persona, tags — plus body offset."""
    meta, offset = _parse_frontmatter(raw)

    title = str(meta.get("title") or "").strip()
    if not title:
        m = re.search(r"^#\s+(.+)$", raw, re.M)
        title = m.group(1).strip() if m else Path(rel).stem

    # Date precedence: explicit frontmatter > a date in the filename (the chats
    # convention is YYYY-MM-DD.md) > file mtime. Filename beats mtime because a
    # git clone rewrites every mtime to checkout time.
    date = str(meta.get("created") or meta.get("date") or "").strip()
    if not _DATE_IN_NAME.fullmatch(date or ""):
        m = _DATE_IN_NAME.search(Path(rel).name)
        if m:
            date = m.group(1)
        elif not date:
            date = _dt.date.fromtimestamp(path.stat().st_mtime).isoformat()

    # Persona = ROLE, not identity. `area:` is the harness's own role field
    # (harness.py VALID_AREAS) and is deliberately preferred over `author:`:
    # a correction written by daman FOR Accounts must answer to
    # `--persona accounts`, not to `--persona daman`. `area: all` means
    # universal, which is stored as "" — the same value an untagged file gets,
    # so both behave identically in the filter.
    #
    # chats/ carries no role tag YET; every operator's chats are being
    # committed to the shared repo with them, so the path convention below is
    # here for when they land.
    persona = str(
        meta.get("persona") or meta.get("operator") or meta.get("area") or ""
    ).strip().lower()
    if persona == "all":
        persona = ""
    if not persona:
        # Path convention, for when the shared repo lands: chats/<persona>/....
        parts = rel.split("/")
        if len(parts) > 2 and parts[0] == "chats":
            persona = parts[1].lower()

    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]
    tag_str = " ".join(str(t) for t in tags)

    return {
        "title": title, "date": date, "persona": persona, "tags": tag_str,
    }, offset


_HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*#*\s*$")


def _chunk_document(raw: str, offset: int) -> list[dict]:
    """Split a markdown body into heading-scoped chunks.

    Returns dicts of {line, end_line, depth, heading, body} with 1-based line
    numbers *in the original file*, so the printed `file:line` lands on the
    heading the operator wants to read.

    Splitting at H1-H3 and leaving H4+ inside the parent is a measurement, not
    a guess: across the real corpus (1,127 sections) the median H1-H3 section
    is 14 lines and the p99 is 67. That is already a good search result. Going
    deeper would shred arguments that span sub-points; going shallower would
    return whole 300-line audit notes.
    """
    lines = raw.splitlines()
    body_lines = lines[offset:]

    # (start_index_within_body, depth, heading_trail)
    marks: list[tuple[int, int, str]] = []
    trail: list[str] = []
    for i, line in enumerate(body_lines):
        m = _HEADING.match(line)
        if not m:
            continue
        depth = len(m.group(1))
        text = m.group(2).strip()
        trail = trail[: depth - 1]
        while len(trail) < depth - 1:
            trail.append("")
        trail.append(text)
        heading = " › ".join(t for t in trail if t)
        marks.append((i, depth, heading))

    spans: list[tuple[int, int, int, str]] = []  # start, end, depth, heading
    if not marks or marks[0][0] > 0:
        # Preamble: prose before the first heading. Worth keeping — it is often
        # the one-line "what this note is" summary.
        first = marks[0][0] if marks else len(body_lines)
        if any(l.strip() for l in body_lines[:first]):
            spans.append((0, first, 0, ""))
    for idx, (start, depth, heading) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(body_lines)
        spans.append((start, end, depth, heading))

    chunks: list[dict] = []
    for start, end, depth, heading in spans:
        text = "\n".join(body_lines[start:end]).strip("\n")
        if not text.strip():
            continue
        for part_no, (abs_start, sub_text) in enumerate(
            _split_long(body_lines[start:end], start), start=1
        ):
            if not sub_text.strip():
                continue
            label = heading
            if part_no > 1 or _needs_split(body_lines[start:end]):
                label = f"{heading} (part {part_no})" if heading else f"(part {part_no})"
            chunks.append({
                "line": offset + abs_start + 1,           # 1-based, original file
                "end_line": offset + abs_start + len(sub_text.splitlines()),
                "depth": depth,
                "heading": label,
                "body": sub_text,
            })
    return chunks


def _needs_split(section_lines: list[str]) -> bool:
    return len("\n".join(section_lines)) > MAX_CHUNK_CHARS


def _split_long(section_lines: list[str], base: int):
    """Yield (absolute_start_line, text) parts of at most MAX_CHUNK_CHARS.

    ``base`` is the section's own offset within the document body, so the
    yielded index is directly usable as a line pointer. Getting this wrong
    silently produces `file:line` numbers that land in the wrong section —
    worse than shipping no pointer at all, because it looks right.

    Splits on blank lines so a part never starts mid-sentence or mid-table.
    A single paragraph longer than the budget is emitted whole rather than cut:
    a chunk that lies about its own boundaries is worse than an oversized one.
    """
    text = "\n".join(section_lines)
    if len(text) <= MAX_CHUNK_CHARS:
        yield base, text.strip("\n")
        return
    buf: list[str] = []
    buf_start = 0
    size = 0
    for i, line in enumerate(section_lines):
        if size + len(line) + 1 > MAX_CHUNK_CHARS and buf and not line.strip():
            yield base + buf_start, "\n".join(buf).strip("\n")
            buf, size, buf_start = [], 0, i + 1
            continue
        buf.append(line)
        size += len(line) + 1
    if buf:
        yield base + buf_start, "\n".join(buf).strip("\n")


# ── database ─────────────────────────────────────────────────────────────────

class Index:
    """The recall index, plus an honest account of what it can actually do.

    `fts` / `trigram` are set by probing this SQLite build, never assumed.
    Every caller must be able to work when both are False.
    """

    def __init__(self, db_path: Path | None = None, want_trigram: bool | None = None):
        # Resolved HERE, not as a default argument: `db_path: Path = DB_PATH`
        # binds the module global once at class-definition time, so a later
        # `--db` rebind never reached it and writes still landed on the real
        # index. Found by testing --db and watching the shared index change.
        self.db_path = db_path if db_path is not None else DB_PATH
        # None = inherit whatever this index was built with. Only `index`
        # passes an explicit value, so `search`/`stats` can never silently
        # create a second index shape behind the operator's back.
        self.want_trigram = want_trigram
        self.con: sqlite3.Connection | None = None
        self.fts = False
        self.trigram = False
        self.trigram_off_by_choice = False
        self.error = ""

    # -- open / schema --

    def open(self, create: bool = True) -> bool:
        if not create and not self.db_path.exists():
            self.error = "index not built"
            return False
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.con = sqlite3.connect(str(self.db_path))
            self.con.row_factory = sqlite3.Row
            self.con.execute("PRAGMA journal_mode=WAL")
            self.con.execute("PRAGMA synchronous=NORMAL")
            self._ensure_schema()
            return True
        except sqlite3.Error as exc:
            self.error = f"cannot open {self.db_path.name}: {exc}"
            self.con = None
            return False

    def _ensure_schema(self) -> None:
        con = self.con
        assert con is not None
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS files (
                path        TEXT PRIMARY KEY,
                mtime_ns    INTEGER NOT NULL,
                size        INTEGER NOT NULL,
                sha256      TEXT NOT NULL,
                title       TEXT NOT NULL DEFAULT '',
                doc_date    TEXT NOT NULL DEFAULT '',
                persona     TEXT NOT NULL DEFAULT '',
                tags        TEXT NOT NULL DEFAULT '',
                chunk_count INTEGER NOT NULL DEFAULT 0,
                indexed_at  TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS chunks (
                id       INTEGER PRIMARY KEY,
                path     TEXT NOT NULL,
                line     INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                depth    INTEGER NOT NULL DEFAULT 0,
                heading  TEXT NOT NULL DEFAULT '',
                title    TEXT NOT NULL DEFAULT '',
                doc_date TEXT NOT NULL DEFAULT '',
                persona  TEXT NOT NULL DEFAULT '',
                tags     TEXT NOT NULL DEFAULT '',
                body     TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
            CREATE INDEX IF NOT EXISTS idx_chunks_date ON chunks(doc_date);
            """
        )
        con.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        # FTS5 and the trigram tokenizer are independent capabilities: a build
        # can have the module without the tokenizer (trigram needs SQLite
        # >= 3.34). Probe each, and lose only what is actually missing —
        # Hermes' rule at hermes_state_schema.py:713.
        self.fts = self._try(FTS_STD_SQL)

        # Trigram is also opt-OUT-able, because it is the single biggest thing
        # in the file (measured: 61% of a 15 MB index over 1.5 MB of text).
        # A team whose corpus has grown past comfort can trade substring
        # recall for disk. The choice is persisted, so `search` and `stats`
        # inherit it without needing the flag repeated.
        if self.want_trigram is None:
            row = con.execute(
                "SELECT value FROM meta WHERE key = 'trigram_enabled'").fetchone()
            want = (row[0] if row else "1") == "1"
        else:
            want = self.want_trigram
            con.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES"
                " ('trigram_enabled', ?)", ("1" if want else "0"))
            if not want:
                had = con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table'"
                    " AND name='chunks_tri'").fetchone() is not None
                con.executescript("DROP TABLE IF EXISTS chunks_tri")
                if had:
                    # DROP frees pages INSIDE the file; it does not shrink the
                    # file. Without the VACUUM the operator runs --no-trigram,
                    # sees the same 15 MB, and reasonably concludes the flag
                    # did nothing. Only run it when there was something to
                    # drop, since VACUUM rewrites the whole database.
                    con.commit()
                    con.execute("VACUUM")

        self.trigram = self._try(FTS_TRI_SQL) if (self.fts and want) else False
        self.trigram_off_by_choice = self.fts and not want
        con.commit()

    def _try(self, sql: str) -> bool:
        try:
            self.con.execute(sql)  # type: ignore[union-attr]
            return True
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if "no such module" in msg or "no such tokenizer" in msg:
                return False
            raise

    def close(self) -> None:
        if self.con is not None:
            try:
                self.con.commit()
                self.con.close()
            except sqlite3.Error:
                pass
            self.con = None

    @property
    def path_label(self) -> str:
        if self.fts and self.trigram:
            return "fts5+trigram"
        if self.fts and self.trigram_off_by_choice:
            return "fts5 (trigram off by --no-trigram)"
        if self.fts:
            return "fts5 (this SQLite build has no trigram tokenizer)"
        return "LIKE scan (no FTS5 in this SQLite build)"

    # -- write --

    def forget_file(self, rel: str) -> None:
        con = self.con
        assert con is not None
        ids = [r[0] for r in con.execute("SELECT id FROM chunks WHERE path = ?", (rel,))]
        for cid in ids:
            if self.fts:
                con.execute("DELETE FROM chunks_fts WHERE rowid = ?", (cid,))
            if self.trigram:
                con.execute("DELETE FROM chunks_tri WHERE rowid = ?", (cid,))
        con.execute("DELETE FROM chunks WHERE path = ?", (rel,))
        con.execute("DELETE FROM files WHERE path = ?", (rel,))

    def add_file(self, rel: str, st: os.stat_result, digest: str,
                 doc: dict, chunks: list[dict]) -> int:
        con = self.con
        assert con is not None
        con.execute(
            "INSERT OR REPLACE INTO files"
            "(path, mtime_ns, size, sha256, title, doc_date, persona, tags,"
            " chunk_count, indexed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (rel, st.st_mtime_ns, st.st_size, digest, doc["title"], doc["date"],
             doc["persona"], doc["tags"], len(chunks), _now_iso()),
        )
        for ch in chunks:
            cur = con.execute(
                "INSERT INTO chunks"
                "(path, line, end_line, depth, heading, title, doc_date,"
                " persona, tags, body) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (rel, ch["line"], ch["end_line"], ch["depth"], ch["heading"],
                 doc["title"], doc["date"], doc["persona"], doc["tags"],
                 ch["body"]),
            )
            cid = cur.lastrowid
            row = (cid, doc["title"], ch["heading"], doc["tags"], ch["body"])
            if self.fts:
                con.execute(
                    "INSERT INTO chunks_fts(rowid, title, heading, tags, body)"
                    " VALUES (?,?,?,?,?)", row)
            if self.trigram:
                con.execute(
                    "INSERT INTO chunks_tri(rowid, title, heading, tags, body)"
                    " VALUES (?,?,?,?,?)", row)
        return len(chunks)

    def touch_file(self, rel: str, st: os.stat_result) -> None:
        """Content unchanged, only mtime moved — refresh the stat gate, keep chunks."""
        self.con.execute(  # type: ignore[union-attr]
            "UPDATE files SET mtime_ns = ?, size = ? WHERE path = ?",
            (st.st_mtime_ns, st.st_size, rel),
        )


# ── FTS5 query sanitising ────────────────────────────────────────────────────
#
# Ported from Hermes' `_sanitize_fts5_query` (hermes_state_search.py:782) with
# the same reasoning: FTS5's MATCH argument is a query LANGUAGE, not a string.
# An operator typing `TODO: fix returns` or `what about "oil` gets an
# OperationalError from raw MATCH — which, unhandled, reads to them as "search
# is broken". This is the single highest-value thing to copy from that file.

def _sanitize_fts5(query: str) -> str:
    query = (query or "")[:MAX_QUERY_CHARS]

    # 1. Protect balanced "quoted phrases" with placeholders. Linear scan, not
    #    a regex, so a pathological run of quotes cannot induce backtracking.
    quoted: list[str] = []
    out: list[str] = []
    i = 0
    while i < len(query):
        ch = query[i]
        if ch != '"':
            out.append(ch)
            i += 1
            continue
        end = query.find('"', i + 1)
        if end == -1:
            out.append(" ")          # unmatched quote — drop it
            i += 1
            continue
        quoted.append(query[i:end + 1])
        out.append(f"\x00Q{len(quoted) - 1}\x00")
        i = end + 1
    s = "".join(out)

    # 2. Strip the remaining FTS5 metacharacters. `:` matters most: with a
    #    multi-column table, `notes: turnover` parses as a column filter and
    #    raises "no such column".
    s = re.sub(r'[+{}():"^,]', " ", s)

    # 3. `*` is prefix-search; collapse runs and drop a leading one (a bare `*`
    #    is a syntax error).
    s = re.sub(r"\*+", "*", s)
    s = re.sub(r"(^|\s)\*", r"\1", s)

    # 4. Dangling booleans ("returns AND") are syntax errors.
    s = re.sub(r"(?i)^(AND|OR|NOT)\b\s*", "", s.strip())
    s = re.sub(r"(?i)\s+(AND|OR|NOT)\s*$", "", s.strip())

    # 5. Quote dotted/hyphenated/underscored terms so they stay phrases.
    #    Unquoted, FTS5 turns `hana-sql` into `hana AND sql` and `C-0001` into
    #    `c AND 0001` — both of which match far too much. One pass, so
    #    `sap-b1.doctor` is not double-quoted.
    s = re.sub(r"\b(\w+(?:[._-]\w+)+)\b", r'"\1"', s)

    for idx, q in enumerate(quoted):
        s = s.replace(f"\x00Q{idx}\x00", q)
    return s.strip()


_BOOLEANS = {"AND", "OR", "NOT"}


def _trigram_eligible(query: str) -> bool:
    """True when every searchable token is >= 3 chars.

    The trigram tokenizer indexes overlapping 3-character runs, so a shorter
    token produces no trigrams at all. Because FTS5 ANDs terms implicitly, one
    2-char token makes the whole trigram MATCH return nothing — so the path is
    only worth taking when every token qualifies. (Hermes, same file, :909.)
    """
    tokens = [t for t in query.strip('"').split() if t.upper() not in _BOOLEANS]
    return bool(tokens) and all(len(t.strip('"')) >= 3 for t in tokens)


def _trigram_query(query: str) -> str:
    """Quote every non-operator token: neutralises metacharacters, keeps booleans."""
    parts = []
    for tok in query.split():
        if tok.upper() in _BOOLEANS:
            parts.append(tok)
        else:
            parts.append('"' + tok.strip('"').replace('"', '""') + '"')
    return " ".join(parts)


# ── index ────────────────────────────────────────────────────────────────────

def cmd_index(args: argparse.Namespace) -> int:
    roots = _corpus_roots(args.corpus)
    started = time.time()

    # Fail closed when the requested corpus is not the one this index was built
    # from. Without this, `index --corpus /somewhere/else` quietly REPLACES the
    # operator's real index with one built from a different tree — verified the
    # hard way: a single stray test run left the shared index at 0 files. An
    # index is cheap to rebuild but expensive to notice is wrong, so a
    # destructive re-point has to be asked for explicitly.
    prior_roots_raw = _peek_meta(DB_PATH, "corpus_roots")
    if prior_roots_raw and not args.rebuild:
        try:
            prior_roots = json.loads(prior_roots_raw)
        except (json.JSONDecodeError, TypeError):
            prior_roots = None
        if prior_roots is not None and prior_roots != roots:
            print(
                f"recall: this index was built from [{', '.join(prior_roots)}] "
                f"but you asked for [{', '.join(roots)}]. Nothing was changed.",
                file=sys.stderr)
            print(
                "  To re-point this index:      add --rebuild\n"
                "  To keep them separate:       JIVO_RECALL_DB=<path> (or --db <path>)",
                file=sys.stderr)
            return 0

    if args.rebuild and DB_PATH.exists():
        try:
            for suffix in ("", "-wal", "-shm"):
                p = Path(str(DB_PATH) + suffix)
                if p.exists():
                    p.unlink()
        except OSError as exc:
            print(f"recall: could not remove old index ({exc})", file=sys.stderr)

    # --no-trigram is a one-way switch for an existing index (it DROPs the
    # table); turning trigram back on needs --rebuild to repopulate it, which
    # `stats` tells you. Absent the flag, inherit the index's own setting.
    idx = Index(want_trigram=False if args.no_trigram else None)
    if not idx.open(create=True):
        print(f"recall: {idx.error}", file=sys.stderr)
        return 0  # fail quiet — a hook must never block the session

    con = idx.con
    assert con is not None

    known = {
        r["path"]: r for r in con.execute(
            "SELECT path, mtime_ns, size, sha256 FROM files")
    }
    seen: set[str] = set()
    new = changed = touched = unchanged = skipped = 0
    chunk_total = 0

    con.execute("BEGIN IMMEDIATE")
    try:
        for path, rel in _iter_corpus_files(roots):
            try:
                st = path.stat()
            except OSError:
                continue
            seen.add(rel)

            if st.st_size > MAX_FILE_BYTES:
                skipped += 1
                if args.verbose:
                    print(f"  skip   {rel} ({st.st_size} bytes > {MAX_FILE_BYTES})")
                continue

            prior = known.get(rel)
            # Cheap gate first: identical (mtime_ns, size) means untouched, and
            # we never pay for a hash. This is what makes re-indexing a
            # 96-file corpus effectively free.
            if prior and prior["mtime_ns"] == st.st_mtime_ns and prior["size"] == st.st_size:
                unchanged += 1
                if args.verbose:
                    print(f"  same   {rel}")
                continue

            try:
                digest = _sha256(path)
            except OSError:
                continue

            # Second gate: mtime moved but content did not (a `touch`, a fresh
            # git clone, a save-with-no-edit). Refresh the stat and keep the
            # chunks — re-chunking identical bytes is pure waste.
            if prior and prior["sha256"] == digest:
                idx.touch_file(rel, st)
                touched += 1
                if args.verbose:
                    print(f"  touch  {rel} (mtime moved, content identical)")
                continue

            try:
                raw = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            doc, offset = _doc_meta(rel, raw, path)
            chunks = _chunk_document(raw, offset)

            if prior:
                idx.forget_file(rel)
                changed += 1
                verb = "update"
            else:
                new += 1
                verb = "add"
            chunk_total += idx.add_file(rel, st, digest, doc, chunks)
            if args.verbose:
                print(f"  {verb:<6} {rel} ({len(chunks)} chunks)")

        removed = 0
        for rel in sorted(set(known) - seen):
            idx.forget_file(rel)
            removed += 1
            if args.verbose:
                print(f"  remove {rel} (gone from corpus)")

        con.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES ('last_index_at', ?)",
            (_now_iso(),))
        con.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES ('corpus_roots', ?)",
            (json.dumps(roots),))
        con.commit()
    except Exception:
        con.rollback()
        idx.close()
        if os.environ.get("JIVO_RECALL_DEBUG"):
            raise
        print("recall: index failed; previous index left intact", file=sys.stderr)
        return 0

    files_now = con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    chunks_now = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    idx.close()

    elapsed = time.time() - started
    if not files_now:
        print(f"recall: no markdown found under {', '.join(roots)} — nothing to index.")
        return 0

    print(
        f"recall: indexed {files_now} files / {chunks_now} chunks "
        f"in {elapsed:.2f}s  [{idx.path_label}]"
    )
    print(
        f"  new {new} · changed {changed} · touched {touched} · "
        f"unchanged {unchanged} · removed {removed}"
        + (f" · skipped {skipped}" if skipped else "")
    )
    if chunk_total:
        print(f"  re-chunked {chunk_total} chunks across {new + changed} file(s)")
    return 0


# ── search ───────────────────────────────────────────────────────────────────

def _filters(args: argparse.Namespace) -> tuple[list[str], list]:
    """Shared WHERE fragments for every search path."""
    where: list[str] = []
    params: list = []
    if args.persona:
        # Untagged == universal, mirroring harness.py's `area: all` convention:
        # an Accounts operator sees Accounts notes plus the shared ones.
        where.append("(c.persona = ? OR c.persona = '')")
        params.append(args.persona.lower())
    if args.since:
        where.append("c.doc_date >= ?")
        params.append(args.since)
    if args.until:
        where.append("c.doc_date <= ?")
        params.append(args.until)
    if args.path:
        # Pushed into SQL rather than filtered afterwards: post-filtering would
        # apply --path to an already-LIMITed page and quietly return fewer
        # results than exist.
        where.append("c.path GLOB ?")
        params.append(args.path)
    return where, params


def _rows_to_results(rows, match: str) -> list[dict]:
    out = []
    for r in rows:
        out.append({
            "path": r["path"], "line": r["line"], "end_line": r["end_line"],
            "heading": r["heading"], "title": r["title"], "date": r["doc_date"],
            "persona": r["persona"], "tags": r["tags"],
            "snippet": (r["snippet"] if "snippet" in r.keys() else "") or "",
            "score": round(float(r["score"]), 6) if "score" in r.keys() else 0.0,
            "match": match,
            "body": r["body"] if "body" in r.keys() else "",
        })
    return out


def _fts_search(idx: Index, table: str, query: str, args: argparse.Namespace,
                limit: int) -> list[dict]:
    where, params = _filters(args)
    weights = ", ".join(str(w) for w in BM25_WEIGHTS)
    # Column 3 is `body`, pinned deliberately rather than using snippet()'s
    # auto-select (-1). Auto-select picks whichever column scores best, which
    # for a title-weighted query is the heading — and the heading is already
    # printed on its own line, so the snippet would just echo it and show the
    # operator nothing new. The body snippet is the part they cannot already see.
    sql = f"""
        SELECT c.id, c.path, c.line, c.end_line, c.heading, c.title,
               c.doc_date, c.persona, c.tags, c.body,
               snippet({table}, 3, '»', '«', ' … ', 24) AS snippet,
               bm25({table}, {weights}) AS score
        FROM {table}
        JOIN chunks c ON c.id = {table}.rowid
        WHERE {table} MATCH ?
    """
    sql_params: list = [query] + params
    if where:
        sql += " AND " + " AND ".join(where)
    # bm25() is negative and MORE negative is a better match, so ASC is
    # "best first". Verified against this SQLite build, not assumed.
    sql += " ORDER BY score ASC, c.doc_date DESC LIMIT ?"
    sql_params.append(limit)
    try:
        rows = idx.con.execute(sql, sql_params).fetchall()  # type: ignore[union-attr]
    except sqlite3.OperationalError:
        # A query that survives the sanitiser can still be unrunnable (an
        # exotic operator, a tokenizer that vanished). Let the caller fall
        # through to the next strategy instead of surfacing a stack trace.
        return []
    return _rows_to_results(rows, "trigram" if table == "chunks_tri" else "fts5")


def _like_search(idx: Index, terms: list[str], args: argparse.Namespace,
                 limit: int) -> list[dict]:
    """Last resort inside the DB: substring AND over the same chunk rows.

    Slow and unranked, but it keeps every other guarantee — chunking, headings,
    `file:line` — intact on a SQLite build with no FTS5 at all.
    """
    if not terms:
        return []  # no term clauses would mean "match everything"
    where, params = _filters(args)
    for t in terms:
        where.append("(c.body LIKE ? OR c.heading LIKE ? OR c.title LIKE ?)")
        params.extend([f"%{t}%"] * 3)
    sql = "SELECT c.id, c.path, c.line, c.end_line, c.heading, c.title, " \
          "c.doc_date, c.persona, c.tags, c.body FROM chunks c"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY c.doc_date DESC LIMIT ?"
    params.append(limit)
    rows = idx.con.execute(sql, params).fetchall()  # type: ignore[union-attr]
    results = _rows_to_results(rows, "like")
    for r in results:
        r["snippet"] = _make_snippet(r["body"], terms)
    return results


def _cap_per_file(results: list[dict], per_file: int, limit: int) -> list[dict]:
    """Keep at most ``per_file`` hits from any one document, preserving rank.

    Without this, a single 324-line audit note wins the whole first page — four
    sections of the same document, all saying much the same thing. The operator
    learns less from four hits in one file than from one hit in each of four,
    and the file is one `--path` away if they want the rest. ``--per-file 0``
    turns the cap off.
    """
    if per_file <= 0:
        return results[:limit]
    kept: list[dict] = []
    seen: dict[str, int] = {}
    overflow: list[dict] = []
    for r in results:
        n = seen.get(r["path"], 0)
        if n < per_file:
            seen[r["path"]] = n + 1
            kept.append(r)
        else:
            overflow.append(r)
        if len(kept) >= limit:
            return kept
    # Under-filled page (a narrow query, or few distinct files): backfill from
    # the capped hits rather than returning less than the operator asked for.
    kept.extend(overflow[: limit - len(kept)])
    return kept


def _make_snippet(body: str, terms: list[str], width: int = 160) -> str:
    """Hand-rolled snippet for the non-FTS paths, shaped like snippet()'s output."""
    low = body.lower()
    pos = min((low.find(t.lower()) for t in terms if t.lower() in low), default=-1)
    if pos < 0:
        return " ".join(body.split())[:width]
    start = max(0, pos - width // 3)
    frag = " ".join(body[start:start + width].split())
    return ("… " if start else "") + frag + " …"


def _file_scan(terms: list[str], roots: list[str], limit: int,
               path_glob: str = "") -> list[dict]:
    """No usable index at all — search the corpus files directly.

    Prefers ripgrep when it is on PATH (fast, and the brief's suggestion), but
    does NOT depend on it. `rg` is missing from plenty of machines, and an
    office box running git-bash on Windows is exactly the kind that won't have
    it — a ripgrep-only fallback would itself be a crash path. The pure-Python
    scan below is the guaranteed floor: stdlib only, identical output shape.

    Both paths are given the SAME file list the index would have used, so a
    degraded search never silently widens the corpus to the whole repo.
    """
    files = [
        (p, rel) for p, rel in _iter_corpus_files(roots)
        if not path_glob or fnmatch.fnmatch(rel, path_glob)
    ]
    if not terms or not files:
        return []

    # ripgrep can only pre-filter on ONE pattern (multiple -e are OR'd, and the
    # Rust regex engine has no lookahead for an unordered AND), so pick the
    # LONGEST term: it is the most selective, which keeps the number of lines
    # the Python side has to re-filter small.
    probe = max(terms, key=len)
    others = [t for t in terms if t is not probe]

    def _hit(rel: str, lineno: int, body: str) -> dict:
        return {
            "path": rel, "line": lineno, "end_line": lineno,
            "heading": "", "title": "", "date": "", "persona": "", "tags": "",
            "snippet": body.strip()[:200], "score": 0.0,
            "match": _hit.label, "body": body,          # type: ignore[attr-defined]
        }

    results: list[dict] = []
    rg = shutil.which("rg")
    if rg:
        try:
            _hit.label = "ripgrep"                      # type: ignore[attr-defined]
            proc = subprocess.run(
                [rg, "--no-heading", "--line-number", "--color", "never",
                 "-i", "-e", probe, "--", *[str(p) for p, _ in files]],
                capture_output=True, text=True, timeout=30)
            # Do NOT truncate rg's output before filtering. An earlier version
            # sliced to limit*4 lines first, so a common probe term ("returns")
            # filled the window with near-misses and the real hit — which
            # needed the OTHER terms too — never appeared. Bound on results
            # produced, not on input consumed.
            for line in proc.stdout.splitlines():
                parts = line.split(":", 2)
                if len(parts) < 3:
                    continue
                body = parts[2]
                if not all(t.lower() in body.lower() for t in others):
                    continue
                try:
                    lineno = int(parts[1])
                except ValueError:
                    continue
                results.append(_hit(_rel(Path(parts[0])), lineno, body))
                if len(results) >= limit:
                    break
            if results:
                return results
        except (OSError, subprocess.SubprocessError, ValueError):
            pass  # fall through to the Python scan

    _hit.label = "scan"                                 # type: ignore[attr-defined]

    for path, rel in files:
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, start=1):
            low = line.lower()
            if all(t.lower() in low for t in terms):
                results.append(_hit(rel, n, line))
                if len(results) >= limit:
                    return results
    return results


def cmd_search(args: argparse.Namespace) -> int:
    raw_query = (args.query or "").strip()
    if not raw_query:
        print("recall: nothing to search for.", file=sys.stderr)
        return 0

    limit = max(1, min(args.limit, 100))
    terms = [t for t in re.split(r"\s+", raw_query) if t and t.upper() not in _BOOLEANS]
    roots = _corpus_roots(args.corpus)

    # A query made only of boolean operators ("NOT", "AND OR") has nothing to
    # match on. Caught here because the LIKE path would otherwise build a
    # WHERE with no term clauses and hand back an arbitrary chunk — an answer
    # that looks like a result and is not one.
    if not terms:
        print(f'recall: "{raw_query}" has no searchable terms — it is only '
              f'operators or punctuation.', file=sys.stderr)
        return 0

    idx = Index()
    if not idx.open(create=False):
        # No index yet. Still answer — degraded, and say so — rather than
        # telling an operator mid-question to go run a build step.
        results = _file_scan(terms, roots, limit, args.path)
        _emit(args, raw_query, results, "file scan (no index — run: recall index)")
        return 0

    # Over-fetch so the per-file cap has something to choose from: capping a
    # page that was already truncated to `limit` would just shrink it.
    fetch = limit if args.per_file <= 0 else min(limit * 6, 200)

    results: list[dict] = []
    path_used = idx.path_label
    try:
        if idx.fts:
            sanitized = _sanitize_fts5(raw_query)
            if sanitized:
                results = _fts_search(idx, "chunks_fts", sanitized, args, fetch)
            # Top up with the trigram index. This is the whole reason for
            # carrying a second index: "escalati", "turnovr", "hana-sql" as one
            # token — things the word tokenizer cannot match but a 3-gram can.
            # Top-up rather than replace, so exact ranked hits always come
            # first and trigram only fills the space they left.
            if idx.trigram and len(results) < fetch and _trigram_eligible(raw_query):
                seen = {(r["path"], r["line"]) for r in results}
                extra = _fts_search(
                    idx, "chunks_tri", _trigram_query(raw_query), args,
                    fetch - len(results))
                results.extend(e for e in extra if (e["path"], e["line"]) not in seen)
        if not results:
            results = _like_search(idx, terms, args, fetch)
            if results:
                path_used = path_used + " → LIKE"
    except sqlite3.Error as exc:
        if os.environ.get("JIVO_RECALL_DEBUG"):
            raise
        print(f"recall: search degraded ({exc})", file=sys.stderr)
        results = _file_scan(terms, roots, limit, args.path)
        path_used = "file scan (index error)"
    finally:
        idx.close()

    _emit(args, raw_query, _cap_per_file(results, args.per_file, limit), path_used)
    return 0


def _emit(args: argparse.Namespace, query: str, results: list[dict], path_label: str) -> None:
    if args.json:
        for r in results:
            if not args.full:
                r.pop("body", None)
        print(json.dumps(
            {"query": query, "path": path_label, "count": len(results),
             "results": results},
            ensure_ascii=False, indent=2))
        return

    if not results:
        print(f'recall: no match for "{query}"  [{path_label}]')
        return

    print(f'recall: {len(results)} result(s) for "{query}"  [{path_label}]\n')
    for i, r in enumerate(results, start=1):
        head = f"{r['path']}:{r['line']}"
        bits = [b for b in (r.get("date"), r.get("persona")) if b]
        # Flag the non-exact paths per row. A trigram hit is a substring match,
        # not a word match — an operator reading a fuzzy result deserves to
        # know it is fuzzy before they act on it.
        if r.get("match") not in ("fts5", None, ""):
            bits.append(r["match"])
        suffix = f"  ({' · '.join(bits)})" if bits else ""
        print(f"{i}. {head}{suffix}")
        if r.get("title"):
            print(f"   {r['title'][:110]}")
        if r.get("heading"):
            print(f"   › {r['heading'][:110]}")
        snip = " ".join((r.get("snippet") or "").split())
        if snip:
            print(f"   {snip[:300]}")
        if args.full and r.get("body"):
            print("   ---")
            for line in r["body"].splitlines():
                print(f"   {line}")
        print()


# ── stats ────────────────────────────────────────────────────────────────────

def cmd_stats(args: argparse.Namespace) -> int:
    if not DB_PATH.exists():
        print("recall: no index yet.")
        print(f"  build it with: python3 {_rel(Path(__file__))} index")
        return 0

    idx = Index()
    if not idx.open(create=False):
        print(f"recall: {idx.error}", file=sys.stderr)
        return 0
    con = idx.con
    assert con is not None

    files = con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    chunks = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    body_chars = con.execute(
        "SELECT COALESCE(SUM(LENGTH(body)), 0) FROM chunks").fetchone()[0]
    last = con.execute(
        "SELECT value FROM meta WHERE key = 'last_index_at'").fetchone()
    roots_row = con.execute(
        "SELECT value FROM meta WHERE key = 'corpus_roots'").fetchone()
    roots = json.loads(roots_row[0]) if roots_row else []

    size = sum(
        Path(str(DB_PATH) + s).stat().st_size
        for s in ("", "-wal", "-shm")
        if Path(str(DB_PATH) + s).exists()
    )

    ratio = f", {size / body_chars:.1f}x the indexed text" if body_chars else ""
    print("recall index")
    print(f"  db                : {_rel(DB_PATH)}  ({size / 1048576:.1f} MB{ratio})")
    print(f"  search path       : {idx.path_label}")
    print(f"  files indexed     : {files}")
    print(f"  chunks            : {chunks}")
    print(f"  indexed text      : {body_chars / 1024:.0f} KB")
    if chunks:
        print(f"  mean chunk        : {body_chars // chunks} chars")
    print(f"  last index        : {(last[0] if last else 'never')}")
    print(f"  corpus roots      : {', '.join(roots) or '(unknown)'}")

    rows = con.execute(
        "SELECT CASE WHEN INSTR(path, '/') > 0"
        "  THEN SUBSTR(path, 1, INSTR(path, '/') - 1) ELSE '(root)' END AS root,"
        " COUNT(DISTINCT path) AS files, COUNT(*) AS chunks"
        " FROM chunks GROUP BY root ORDER BY chunks DESC").fetchall()
    if rows:
        print("\n  by corpus root:")
        for r in rows:
            print(f"    {r['root']:<20} {r['files']:>4} files  {r['chunks']:>5} chunks")

    # Where the disk actually goes. Surfaced here rather than buried in a doc
    # because the corpus is about to grow by an order of magnitude when every
    # operator's chats land in the shared repo, and "why is this 15 MB?" should
    # be answerable without reading the source. dbstat is compiled in on most
    # builds but not all — skip quietly when it isn't.
    try:
        rows = con.execute(
            "SELECT name, SUM(pgsize) b FROM dbstat GROUP BY name").fetchall()
        buckets = {"trigram index": 0, "word index": 0, "chunk store": 0, "other": 0}
        for r in rows:
            n, b = r["name"], r["b"]
            if n.startswith("chunks_tri"):
                buckets["trigram index"] += b
            elif n.startswith("chunks_fts"):
                buckets["word index"] += b
            elif n == "chunks" or n.startswith("idx_chunks"):
                buckets["chunk store"] += b
            else:
                buckets["other"] += b
        total = sum(buckets.values()) or 1
        print("\n  disk by component:")
        for k, v in sorted(buckets.items(), key=lambda kv: -kv[1]):
            if v:
                print(f"    {k:<20} {v / 1048576:>6.1f} MB  {100 * v / total:>4.1f}%")
        if idx.trigram:
            print("    (trigram indexes every 3-char window, so it is several"
                  " times the source text by construction —")
            print("     `index --no-trigram` drops it and the substring search"
                  " that depends on it)")
    except sqlite3.OperationalError:
        pass

    personas = con.execute(
        "SELECT persona, COUNT(*) c FROM chunks WHERE persona <> ''"
        " GROUP BY persona ORDER BY c DESC").fetchall()
    if personas:
        print("\n  personas tagged:")
        for p in personas:
            print(f"    {p['persona']:<20} {p['c']:>5} chunks")
    else:
        print("\n  personas tagged   : none yet — --persona matches untagged as shared")

    idx.close()
    return 0


# ── wiring ───────────────────────────────────────────────────────────────────

def register_cli(parent: argparse.ArgumentParser) -> None:
    """Attach recall's subcommands to a parent parser.

    Exists so `harness.py` can mount this as `harness.py recall ...` with a
    three-line change and no edits to this file — the same shape Hermes uses
    for its own optional subcommand modules (hermes_cli/curator.py:680).
    """
    parent.set_defaults(func=lambda a: (parent.print_help(), 0)[1])
    sub = parent.add_subparsers(dest="recall_command")
    _add_subcommands(sub)


def _db_flag(p: argparse.ArgumentParser) -> None:
    p.add_argument("--db", default="", metavar="PATH",
                   help="use a different index file (same as JIVO_RECALL_DB); "
                        "pair with --corpus to keep an experiment off the "
                        "shared index")


def _add_subcommands(sub) -> None:
    p = sub.add_parser("index", help="build/refresh the search index (incremental)")
    p.add_argument("--corpus", action="append",
                   help="corpus root, repeatable; replaces the default set")
    p.add_argument("--rebuild", action="store_true",
                   help="discard the existing index and start clean")
    p.add_argument("--no-trigram", action="store_true",
                   help="drop the substring index (~61%% smaller db, loses "
                        "partial/mid-word matching); --rebuild to restore it")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="print a line per file showing what was done")
    _db_flag(p)
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("search", help="search the indexed corpus")
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--per-file", type=int, default=2, metavar="N",
                   help="max hits from one document (0 = no cap); keeps a long "
                        "note from monopolising the page")
    p.add_argument("--persona", default="",
                   help="restrict to this persona plus untagged (shared) notes")
    p.add_argument("--since", default="", metavar="YYYY-MM-DD")
    p.add_argument("--until", default="", metavar="YYYY-MM-DD")
    p.add_argument("--path", default="", help="glob filter on the file path")
    p.add_argument("--full", action="store_true", help="print whole matching chunks")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--corpus", action="append", help=argparse.SUPPRESS)
    _db_flag(p)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("stats", help="what is indexed, and how fresh")
    _db_flag(p)
    p.set_defaults(func=cmd_stats)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="recall",
        description="Search JIVO's written record (read-only w.r.t. all business systems)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    _add_subcommands(sub)
    args = ap.parse_args(argv)
    # --db is resolved here rather than threaded through every function: the
    # index path is process-global state (Index()'s default, cmd_stats), and
    # rebinding it once at the entry point keeps every call site honest about
    # which file it is touching.
    if getattr(args, "db", ""):
        global DB_PATH
        DB_PATH = Path(args.db)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 0
    except Exception as exc:              # noqa: BLE001 — deliberate catch-all
        # A hook calls this. A traceback in an operator's terminal is worse
        # than a missing search result, and a non-zero exit could stall their
        # session. JIVO_RECALL_DEBUG=1 turns this off while developing.
        if os.environ.get("JIVO_RECALL_DEBUG"):
            raise
        print(f"recall: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
