#!/usr/bin/env python3
"""JIVO harness — query-pattern capture and skill proposal.

The second, independent learning signal. `harness.py` clusters what operators
*typed*; this clusters what actually *got run*.

Why a second signal
-------------------
Question shapes are a weak signal on their own. Three operators asking
"ledger balance for X", "how much does X owe us", and "statement for X"
produce three shapes and one underlying need — so `harness.py mint` never
sees five of anything. But all three sessions end up issuing the same
`sapb1 query BusinessPartners --filter "CardCode eq …"`. The command is the
need, stated unambiguously, in the vocabulary a skill has to be written in.

This tool NEVER touches SAP, Postgres, HANA, or any business system. It reads
a PostToolUse payload describing a call that already happened and writes a
line to `harness/questions/queries.jsonl`. It issues no business-system call
of any kind, read or write. It never reads `tool_response` — see REDACTION.

Subcommands
-----------
  record     Normalise one PostToolUse payload from stdin into queries.jsonl
  propose    Rank captured query shapes and report which deserve a skill
  draft      Print a complete draft SKILL.md for one shape id (stdout only)
  status     Show what the query log currently holds
  selftest   Run the built-in verification battery (no network, no business calls)

Design notes
------------
  * CLI and MCP collapse to ONE shape. `sapb1 query BusinessPartners --filter
    "CardCode eq 'V1'"` and `mcp__sapb1__sapb1_query{entity:…, filter:…}` are
    the same act by the same operator; the transport is not the pattern. Both
    normalise into the same canonical dict before hashing.
  * Two identifiers per record. `shape_id` is strict (entity + filter fields +
    selected columns + scope). `family_id` is coarse (tool + verb + entity +
    filter fields) and ignores the selected columns. Strict ids are what a
    skill is minted against; families answer the owner's actual question —
    "someone keeps selecting from one table" — without fragmenting on whether
    this run happened to add CardCode to --select.
  * Pagination and presentation are NOT the pattern. --top/--skip/--page-size/
    --json/--csv/--orderby are dropped from the shape; --count and --all are
    kept, because "just the number" and "every matching row" are different
    needs. The dropped values are still recorded in `parsed` so a draft can
    reuse the most common one.
  * Writes are not captured. `sapb1 draft/post/patch` are skipped: a write is
    not a query pattern, and nothing minted from this log may authorise one.
  * `propose` gates before it ranks. Volume alone cannot promote a shape — see
    RANKING below and harness/PATTERNS.md for the full argument.

REDACTION
---------
`tool_response` is never read. Not stdout, not stderr, not a single row of
business data — there is no field in the record that could hold it, so a leak
is structurally impossible rather than merely unlikely.

The command string itself IS recorded (truncated), because the flags are the
pattern. It is scrubbed first, then re-inspected: if any secret pattern still
matches after scrubbing, the whole record is dropped rather than logged
half-clean. Commands that touch a credential file (.env, .pgpass, id_rsa, …)
are dropped outright — they are never query patterns anyway.

RANKING
-------
Runs are cheap; distinct days are not. One operator can produce twenty runs in
an afternoon chasing a single number, and that is a one-off investigation, not
a standing need. So volume enters the score logarithmically and cannot carry a
shape on its own, while spread across days, weeks, sessions and people carries
most of the weight. A hard gate (min runs AND min days AND min sessions) runs
before scoring, so a burst is excluded rather than merely out-ranked.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

# Windows consoles default to cp1252, which cannot encode the characters that
# actually occur in JIVO's data — the rupee sign, en dashes, the arrows in the
# persona profiles. Verified live on an Accounts-class Windows box: a profile
# containing "\u2192" raised UnicodeEncodeError inside print(), and because the
# hook redirects stderr the operator silently received NO corrections at all.
# Force UTF-8 on the streams we own before anything prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass



# ── harness.py reuse (defensive) ─────────────────────────────────────────────
# Reuse the persona resolution, frontmatter parser and question loader rather
# than duplicating them, so the two signals always agree on who the operator is
# and where things live. If harness.py moves or changes shape, fall back to
# local minimal equivalents — a hook must never break because a sibling did.

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:  # pragma: no cover - exercised implicitly by every run
    import harness as _h
    # Running from a directory that merely CONTAINS a `harness/` folder makes
    # Python synthesise an implicit namespace package: the import succeeds, _h
    # is not None, and every attribute access fails. Require a real function.
    if not hasattr(_h, "_active_persona"):
        _h = None
except Exception:  # pragma: no cover - fallback path
    _h = None

HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
QUESTIONS = HARNESS / "questions"
QLOG = QUESTIONS / "log.jsonl"          # question shapes (harness.py ask)
QUERYLOG = QUESTIONS / "queries.jsonl"  # query shapes (this tool)
SKILLS = REPO / ".claude" / "skills"


def _active_persona() -> str:
    if _h is not None:
        try:
            return _h._active_persona()
        except Exception:
            pass
    env = os.environ.get("JIVO_PERSONA", "").strip()
    if env:
        return env.lower()
    marker = HARNESS / ".persona"
    try:
        return marker.read_text(encoding="utf-8").strip().lower() or "all"
    except OSError:
        return "all"


def _parse_frontmatter(path: Path) -> tuple[dict, str]:
    if _h is not None:
        try:
            return _h._parse_frontmatter(path)
        except Exception:
            pass
    return {}, ""


def _slug(text: str, maxlen: int = 40) -> str:
    if _h is not None:
        try:
            return _h._slug(text, maxlen)
        except Exception:
            pass
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:maxlen].strip("-") or "untitled"


# ── tunables ─────────────────────────────────────────────────────────────────

# Gate: a shape must clear ALL THREE before it is even scored. This is what
# implements "20 runs in one afternoon is an investigation, not a need".
MIN_RUNS = int(os.environ.get("JIVO_QMINT_MIN_RUNS", "4"))
MIN_DAYS = int(os.environ.get("JIVO_QMINT_MIN_DAYS", "3"))
MIN_SESSIONS = int(os.environ.get("JIVO_QMINT_MIN_SESSIONS", "2"))

# Score weights. Spread is deliberately the largest term and volume the
# smallest-growing one; see RANKING in the module docstring.
W_DAY = 3.0          # per distinct calendar day, capped
W_DAY_CAP = 8
W_WEEK = 2.0         # per extra distinct ISO week, capped
W_WEEK_CAP = 3
W_VOLUME = 2.0       # multiplies log2(runs + 1) — saturating on purpose
W_PERSONA = 3.0      # per additional distinct persona: the strongest evidence
W_SESSION = 0.5      # per distinct session, capped
W_SESSION_CAP = 8
W_PHRASING = 1.5     # per additional distinct question phrasing, capped
W_PHRASING_CAP = 4

# Recency decay. A query pattern is more perishable than a correction: the
# report it served may have shipped. Hermes ages skills at 30d stale / 90d
# archived (tools/skill_usage.py); a *proposal* deserves tighter windows.
RECENCY_FRESH_DAYS = 14
RECENCY_WARM_DAYS = 45
RECENCY_WARM_FACTOR = 0.6
RECENCY_COLD_FACTOR = 0.3

RAW_MAX = 300        # chars of scrubbed command kept as evidence
SHAPE_MAX = 400      # chars of shape string hashed (deterministic cap)
ATTRIB_WINDOW_S = int(os.environ.get("JIVO_QMINT_ATTRIB_WINDOW", "3600"))


# ── redaction ────────────────────────────────────────────────────────────────
#
# Two layers. SCRUB rewrites the value of anything that names a credential.
# DETECT then re-reads the scrubbed text; a hit means the scrubber did not
# fully understand the form, so the record is dropped instead of logged.
# Over-redaction costs nothing here — a redacted token is never part of a
# query pattern.

_SCRUB_RULES: list[tuple[re.Pattern[str], str]] = [
    # --password X / --token=X / -pass X ... (value replaced, flag kept)
    (re.compile(
        r"(--?(?:password|passwd|pass|pwd|token|secret|api[-_]?key|apikey"
        r"|access[-_]?key|auth|bearer|credential|creds|user|username|login)"
        r"[= ])\S+", re.I), r"\1<redacted>"),
    # ENV_VAR=value where the name smells like a credential
    (re.compile(
        r"\b([A-Za-z_][A-Za-z0-9_]*"
        r"(?:PASSWORD|PASSWD|PASS|PWD|TOKEN|SECRET|APIKEY|API_KEY|KEY"
        r"|CREDENTIAL|CREDS|PAT|AUTH|BEARER)[A-Za-z0-9_]*)=\S+", re.I),
     r"\1=<redacted>"),
    # scheme://user:pass@host
    (re.compile(r"([a-zA-Z][a-zA-Z0-9+.\-]*://)[^/\s:@]+:[^/\s@]+@"),
     r"\1<redacted>@"),
    # JSON-ish "password": "x"
    (re.compile(
        r'("(?:password|passwd|token|secret|api_?key|auth|bearer)"\s*:\s*)'
        r'"[^"]*"', re.I), r'\1"<redacted>"'),
    # Known vendor token literals
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"), "<redacted>"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "<redacted>"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}"), "<redacted>"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "<redacted>"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}"), "<redacted>"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<redacted>"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"), "<redacted>"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "<redacted>"),
    # JWT
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
     "<redacted>"),
    # Long hex blobs (hashes, session keys). Never pattern-relevant.
    (re.compile(r"\b[A-Fa-f0-9]{40,}\b"), "<redacted>"),
]

# If any of these still match AFTER scrubbing, drop the record.
_DETECT_RULES: list[re.Pattern[str]] = [
    re.compile(r"--?(?:password|passwd|pwd|token|secret|api[-_]?key|apikey|bearer)"
               r"[= ](?!<redacted>)\S", re.I),
    re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://[^/\s:@]+:[^/\s@]+@"),
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
]

# Commands touching these are dropped wholesale: they can never be a query
# pattern, and a partial scrub of a credential file read is not worth the risk.
_CREDENTIAL_PATHS = re.compile(
    r"(?:^|[\s/=\"'])(?:\.env(?:\.[\w.-]+)?|\.pgpass|\.netrc|\.npmrc|\.pypirc"
    r"|id_rsa|id_ed25519|\.ssh/|credentials(?:\.json)?|auth\.json"
    r"|hana\.env|service-account[\w.-]*\.json)\b", re.I)


def scrub(text: str) -> str:
    """Replace credential values in *text*. Never raises."""
    if not text:
        return ""
    out = text
    for pat, repl in _SCRUB_RULES:
        try:
            out = pat.sub(repl, out)
        except re.error:  # pragma: no cover - defensive
            continue
    return out


def secret_residue(text: str) -> str:
    """Return the first still-matching secret pattern, or "" if clean."""
    for pat in _DETECT_RULES:
        m = pat.search(text or "")
        if m:
            return pat.pattern
    return ""


def touches_credential_file(text: str) -> bool:
    return bool(_CREDENTIAL_PATHS.search(text or ""))


# ── shell tokenising ─────────────────────────────────────────────────────────

_SEGMENT_OPS = ("&&", "||", ";", "|", "\n")

# Prefixes to walk past when looking for the real binary in a segment.
_PREFIX_WORDS = {
    "env", "sudo", "time", "nohup", "command", "exec", "nice", "stdbuf",
    "timeout", "then", "do", "else", "fi", "done",
}


def split_segments(command: str) -> list[str]:
    """Split a shell command on &&, ||, ;, | and newlines, honouring quotes.

    A naive ``str.split`` breaks ``--filter "a | b"``; a full shell parser is
    overkill. This scanner tracks single/double quotes and backslash escapes,
    which covers every form these CLIs are invoked in.
    """
    segs: list[str] = []
    buf: list[str] = []
    i = 0
    quote = ""
    n = len(command)
    while i < n:
        ch = command[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < n:
                buf.append(command[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == "\\" and i + 1 < n:
            buf.append(ch)
            buf.append(command[i + 1])
            i += 2
            continue
        # An unquoted '#' at the start of a word begins a shell comment. Without
        # this, a commented-out or documentation line mentioning a CLI name gets
        # tokenised as if it were a call.
        if ch == "#" and (not buf or buf[-1].isspace()):
            while i < n and command[i] != "\n":
                i += 1
            continue
        matched = ""
        for op in _SEGMENT_OPS:
            if command.startswith(op, i):
                matched = op
                break
        if matched:
            segs.append("".join(buf))
            buf = []
            i += len(matched)
            continue
        buf.append(ch)
        i += 1
    segs.append("".join(buf))
    return [s.strip() for s in segs if s.strip()]


def tokenise(segment: str) -> list[str]:
    """shlex.split with a regex fallback for unbalanced quotes."""
    import shlex
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return re.findall(r"'[^']*'|\"[^\"]*\"|\S+", segment)


# ── tool identification ──────────────────────────────────────────────────────

# Binary basename (or MCP server name) -> canonical tool family. Extend here;
# nothing else needs to change.
TOOL_ALIASES: dict[str, str] = {
    "sapb1": "sapb1",
    "postsql": "postsql",
    "hana-sql": "hana-sql",
    "hanasql": "hana-sql",
    "dsr": "dsr",
    "dsr-cli": "dsr",
    "ecom": "ecom",
    "ecom-cli": "ecom",
    "oms": "oms",
    "oms-cli": "oms",
    "oms-pp-cli": "oms",
    "factory": "factory",
    "factory-cli": "factory",
    "exim": "exim",
    "exim-cli": "exim",
}

# Verbs that write. Never captured — a write is not a query pattern, and
# nothing minted from this log may authorise one (see CLAUDE.md RULE 0).
WRITE_VERBS = {"draft", "post", "patch", "insert", "update", "delete", "create"}

# Verbs with nothing to pattern-match on.
BORING_VERBS = {"help", "completion", "version", "mcp", "--help", "-h"}


def _basename(token: str) -> str:
    t = token.replace("\\", "/")
    t = t.rsplit("/", 1)[-1]
    if t.lower().endswith(".exe"):
        t = t[:-4]
    return t


_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# Real sub-command vocabularies, so a bare tool name appearing in prose cannot
# invent one. Taken from `sapb1 --help` / `postsql --help`.
_KNOWN_SUBCOMMANDS: dict[str, set[str]] = {
    "sapb1": {"auth", "catalog", "doctor", "draft", "entities", "fields", "help",
              "invoices", "items", "mcp", "ops", "orders", "partners", "patch",
              "post", "query"},
    "postsql": {"cols", "completion", "context", "count", "dbs", "describe",
                "doctor", "export", "functions", "help", "indexes", "mcp",
                "peek", "query", "relationships", "roles", "schema-dump",
                "schemas", "search", "sequences", "stats", "tables", "views"},
}


def find_invocation(tokens: list[str]) -> tuple[str, list[str]] | None:
    """Return (tool_family, argv_after_binary) for a JIVO CLI at COMMAND POSITION.

    Command position matters. An earlier version scanned every token, so a bare
    ``sapb1`` inside a shell comment or a Python string literal was read as an
    invocation — this hook was live while the module was being developed and
    duly recorded ``sapb1 pattern, three`` and ``postsql via MCP:`` from the
    author's own heredocs. A real invocation is the first word of a segment,
    after any ``env`` / ``sudo`` / ``VAR=value`` / loop-keyword prefixes.
    """
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        base = _basename(tok)
        if base in _PREFIX_WORDS or _ASSIGNMENT.match(tok):
            i += 1
            continue
        break
    if i >= len(tokens):
        return None
    fam = TOOL_ALIASES.get(_basename(tokens[i]).lower())
    if not fam:
        return None
    argv = tokens[i + 1:]
    # A tool name followed by something that cannot be a sub-command is prose,
    # not a call ("...the sapb1 pattern, three different values...").
    known = _KNOWN_SUBCOMMANDS.get(fam)
    first = next((a for a in argv if not a.startswith("-")), "")
    if known is not None:
        if first.lower() not in known:
            return None
    elif fam != "hana-sql" and not _SUBCOMMANDISH.match(first):
        return None
    return fam, argv


# ── OData filter normalisation ───────────────────────────────────────────────

_ODATA_OPS = {
    "eq", "ne", "gt", "ge", "lt", "le", "and", "or", "not", "has", "in",
    "add", "sub", "mul", "div", "mod", "true", "false", "null", "asc", "desc",
}
_ODATA_FUNCS = {
    "startswith", "endswith", "contains", "substringof", "tolower", "toupper",
    "trim", "concat", "length", "indexof", "substring", "replace", "year",
    "month", "day", "hour", "minute", "second", "round", "floor", "ceiling",
    "cast", "isof", "date", "time",
}
_DATE_LITERAL = re.compile(r"^\d{4}-\d{2}-\d{2}([T ].*)?$")


def normalise_odata(expr: str) -> tuple[str, list[str]]:
    """Return (skeleton, filter_fields) for an OData $filter expression.

    Values become <date>/<num>/<val>; field names, operators and functions are
    preserved. Two filters over the same fields with different values collapse;
    two filters over different fields do not.
    """
    if not expr:
        return "", []
    s = expr.strip()

    # Pull quoted literals out first so field extraction can't see inside them.
    lits: list[str] = []

    def _take(m: re.Match[str]) -> str:
        lits.append(m.group(0))
        return f"\x00{len(lits) - 1}\x00"

    s = re.sub(r"'(?:[^']|'')*'", _take, s)

    # Numbers (after literals are hidden, so '2026-04-01' is untouched).
    # The \x00 in the lookarounds is load-bearing: without it this regex eats
    # the digits of the literal placeholders themselves, and every quoted value
    # renders as "\x00<num>\x00" instead of <val>/<date>.
    s = re.sub(r"(?<![\w.\x00])-?\d+(?:\.\d+)?(?![\w.\x00])", "<num>", s)

    fields: list[str] = []
    for m in re.finditer(r"\b[A-Za-z_][A-Za-z0-9_]*\b", s):
        word = m.group(0)
        low = word.lower()
        if low in _ODATA_OPS or low in _ODATA_FUNCS:
            continue
        if word in ("num", "val", "date", "list"):
            continue
        fields.append(word)

    # Restore literals as generic placeholders.
    def _put(m: re.Match[str]) -> str:
        inner = lits[int(m.group(1))][1:-1]
        return "<date>" if _DATE_LITERAL.match(inner) else "<val>"

    s = re.sub(r"\x00(\d+)\x00", _put, s)

    # Lowercase operators/keywords only; field names keep SAP's CamelCase.
    def _lower_kw(m: re.Match[str]) -> str:
        w = m.group(0)
        return w.lower() if w.lower() in _ODATA_OPS else w

    s = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\b", _lower_kw, s)
    s = re.sub(r"\s+", " ", s).strip()
    return s, sorted(set(fields), key=str.lower)


# ── SQL normalisation ────────────────────────────────────────────────────────

_SQL_KEYWORDS = {
    "select", "from", "where", "group", "by", "order", "having", "limit",
    "offset", "join", "left", "right", "inner", "outer", "full", "cross", "on",
    "and", "or", "not", "in", "is", "null", "as", "distinct", "union", "all",
    "with", "case", "when", "then", "else", "end", "between", "like", "ilike",
    "exists", "asc", "desc", "count", "sum", "avg", "min", "max", "coalesce",
    "cast", "extract", "interval", "date", "current_date", "now", "true",
    "false", "over", "partition", "using", "into", "values", "table", "explain",
    "show", "top", "any", "some", "nulls", "first", "last", "filter", "within",
    "lateral", "return", "returns", "recursive", "except", "intersect", "at",
    "time", "zone", "to_char", "to_date", "round", "abs", "substring", "trim",
    "upper", "lower", "length", "row_number", "rank", "dense_rank", "lag",
    "lead", "string_agg", "array_agg", "json_agg", "unnest", "generate_series",
}


def normalise_sql(sql: str) -> tuple[str, list[str], list[str]]:
    """Return (skeleton, tables, where_fields) for a SQL statement.

    Literals, IN-lists and LIMIT/OFFSET values are genericised; table and
    column names are preserved, because those are the pattern. "Continuously
    selecting from one table" is exactly what `tables` captures.
    """
    if not sql:
        return "", [], []
    s = sql

    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    s = re.sub(r"--[^\n]*", " ", s)

    s = re.sub(r"\$\$.*?\$\$", "<val>", s, flags=re.S)

    lits: list[str] = []

    def _take(m: re.Match[str]) -> str:
        lits.append(m.group(0))
        return f"\x00{len(lits) - 1}\x00"

    s = re.sub(r"'(?:[^']|'')*'", _take, s)

    # See normalise_odata: the \x00 guards stop this eating the placeholders.
    s = re.sub(r"(?<![\w.$\x00])-?\d+(?:\.\d+)?(?![\w.\x00])", "<num>", s)

    # Tables: the identifier following FROM / JOIN, alias stripped.
    ident = r'(?:"[^"]+"|[A-Za-z_][\w$]*)'
    qualified = rf"{ident}(?:\.{ident})*"
    tables: list[str] = []
    for m in re.finditer(rf"\b(?:from|join)\s+({qualified})", s, re.I):
        name = m.group(1)
        if name.lower() in _SQL_KEYWORDS:
            continue
        tables.append(name)

    where_fields: list[str] = []
    wm = re.search(r"\bwhere\b(.*?)(?:\bgroup\b|\border\b|\bhaving\b|\blimit\b|$)",
                   s, re.I | re.S)
    if wm:
        for m in re.finditer(rf"({qualified})\s*(?:=|!=|<>|<=|>=|<|>|\bin\b|"
                             r"\blike\b|\bilike\b|\bis\b|\bbetween\b)",
                             wm.group(1), re.I):
            name = m.group(1)
            if name.lower() in _SQL_KEYWORDS:
                continue
            where_fields.append(name)

    def _put(m: re.Match[str]) -> str:
        inner = lits[int(m.group(1))][1:-1]
        return "<date>" if _DATE_LITERAL.match(inner) else "<val>"

    s = re.sub(r"\x00(\d+)\x00", _put, s)

    # A varying-length IN list is one pattern, not N. This must accept a
    # SINGLE-element list too: `IN (9)` and `IN (1,2,3)` are the same need, and
    # requiring 2+ elements silently split one pattern into two.
    s = re.sub(r"\bin\s*\(\s*<(?:val|num|date)>(?:\s*,\s*<(?:val|num|date)>)*\s*\)",
               "in (<list>)", s, flags=re.I)
    # Pagination is not the need.
    s = re.sub(r"\b(limit|offset)\s+<num>", r"\1 <n>", s, flags=re.I)

    def _upper_kw(m: re.Match[str]) -> str:
        w = m.group(0)
        return w.upper() if w.lower() in _SQL_KEYWORDS else w

    s = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\b", _upper_kw, s)
    # `date`, `filter` and `all` are SQL keywords, so the pass above uppercases
    # the placeholders too. Put them back: a placeholder must read identically
    # in a SQL shape and an OData shape or the two are needlessly distinct.
    s = re.sub(r"<(DATE|VAL|NUM|LIST|N|ARG)>",
               lambda m: "<" + m.group(1).lower() + ">", s)
    s = re.sub(r"\s+", " ", s).strip().rstrip(";")

    def _dedupe(seq: list[str]) -> list[str]:
        """Normalise identifiers and drop repeats.

        Quotes are stripped everywhere, not just at the ends, so HANA's
        `"JIVO_OIL"."OINV"` becomes `JIVO_OIL.OINV` rather than the unreadable
        `JIVO_OIL"."OINV`.
        """
        seen: set[str] = set()
        out: list[str] = []
        for x in seq:
            clean = x.replace('"', "")
            k = clean.lower()
            if k and k not in seen:
                seen.add(k)
                out.append(clean)
        return out

    return s, _dedupe(tables), _dedupe(where_fields)


# ── flag classification ──────────────────────────────────────────────────────

# Flags whose VALUE is part of the pattern.
_VALUE_FLAGS_PATTERN = {
    "filter", "select", "entity", "where", "company", "db", "d", "database",
    "schema", "table", "sql", "q", "query",
}
# Flags whose value is pagination/presentation noise. Recorded, not hashed.
_VALUE_FLAGS_NOISE = {
    "top", "skip", "page-size", "limit", "offset", "orderby", "order-by",
    "sort", "host", "port", "timeout", "user", "password", "env", "f", "file",
    "out", "output", "format",
}
# Boolean flags that change WHAT is asked for.
_BOOL_FLAGS_PATTERN = {"count", "all", "customers", "suppliers", "open", "deep"}
# Boolean flags that change only HOW it is printed.
_BOOL_FLAGS_NOISE = {
    "json", "csv", "compact", "insecure", "quiet", "verbose", "no-color",
    "help", "h", "pretty", "table",
}


def _split_flags(argv: list[str],
                 greedy: bool = False) -> tuple[list[str], dict[str, str], list[str]]:
    """Split argv into (positionals, valued flags, boolean flags).

    ``greedy`` is for CLIs whose flag vocabulary we do not enumerate (dsr, ecom,
    oms, factory, exim): an unknown flag followed by a non-flag token is assumed
    to take that token as its value. Without it, ``dsr retailers list --beat
    4471`` loses ``--beat`` from the shape and mistakes ``4471`` for a
    positional. Known boolean flags are still never allowed to swallow a value.
    """
    pos: list[str] = []
    vals: dict[str, str] = {}
    bools: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("-") and tok != "-" and not re.match(r"^-\d", tok):
            name = tok.lstrip("-")
            if "=" in name:
                name, v = name.split("=", 1)
                vals[name.lower()] = v
                i += 1
                continue
            low = name.lower()
            nxt = argv[i + 1] if i + 1 < len(argv) else None
            known_bool = low in _BOOL_FLAGS_PATTERN or low in _BOOL_FLAGS_NOISE
            known_valued = low in _VALUE_FLAGS_PATTERN or low in _VALUE_FLAGS_NOISE
            takes_value = (
                nxt is not None
                and not nxt.startswith("-")
                and not known_bool
                and (known_valued or greedy)
            )
            if takes_value:
                vals[low] = nxt  # type: ignore[assignment]
                i += 2
                continue
            bools.append(low)
            i += 1
            continue
        pos.append(tok)
        i += 1
    return pos, vals, bools


def _clean_bools(bools: list[str]) -> list[str]:
    return sorted({b for b in bools if b in _BOOL_FLAGS_PATTERN})


def _split_select(value: str) -> list[str]:
    """Selected columns as a sorted set — column ORDER is not the pattern."""
    if not value:
        return []
    cols = [c.strip().strip('"') for c in value.split(",")]
    return sorted({c for c in cols if c}, key=str.lower)


# ── per-tool parsers ─────────────────────────────────────────────────────────
#
# Every parser returns the same canonical dict, so a CLI call and the
# equivalent MCP call produce the same shape.

def _blank(tool: str) -> dict:
    return {
        "tool": tool, "verb": "", "entity": "", "filter": "",
        "filter_fields": [], "select": [], "company": "", "tables": [],
        "flags": [], "orderby": "", "noise": {},
    }


def parse_sapb1(argv: list[str]) -> dict | None:
    pos, vals, bools = _split_flags(argv)
    if not pos:
        return None
    verb = pos[0].lower()
    if verb in WRITE_VERBS or verb in BORING_VERBS:
        return None
    p = _blank("sapb1")
    p["verb"] = verb
    if verb == "query":
        p["entity"] = pos[1] if len(pos) > 1 else ""
    else:
        # Dedicated read subcommands map onto their entity set, so
        # `sapb1 partners` and `sapb1 query BusinessPartners` are comparable.
        p["entity"] = {
            "partners": "BusinessPartners", "invoices": "Invoices",
            "orders": "Orders", "items": "Items", "fields": "",
            "entities": "", "ops": "", "catalog": "", "doctor": "", "auth": "",
        }.get(verb, "")
        if not p["entity"] and len(pos) > 1:
            p["entity"] = pos[1]
    skel, fields = normalise_odata(vals.get("filter", ""))
    p["filter"] = skel
    p["filter_fields"] = fields
    # `--customers` / `--suppliers` are CardType filters wearing a flag costume;
    # normalise them so the flag and the explicit filter agree.
    for flag, field in (("customers", "CardType"), ("suppliers", "CardType")):
        if flag in bools and field not in p["filter_fields"]:
            p["filter_fields"] = sorted(set(p["filter_fields"] + [field]),
                                        key=str.lower)
    p["select"] = _split_select(vals.get("select", ""))
    p["company"] = vals.get("company", "")
    p["flags"] = _clean_bools(bools)
    p["orderby"] = vals.get("orderby", "")
    p["noise"] = {k: v for k, v in vals.items() if k in _VALUE_FLAGS_NOISE}
    return p


def parse_postsql(argv: list[str]) -> dict | None:
    pos, vals, bools = _split_flags(argv)
    if not pos:
        return None
    verb = pos[0].lower()
    if verb in WRITE_VERBS or verb in BORING_VERBS:
        return None
    p = _blank("postsql")
    p["verb"] = verb
    p["company"] = vals.get("db") or vals.get("d") or vals.get("database", "")
    if verb in ("query", "export"):
        sql = vals.get("sql") or (pos[1] if len(pos) > 1 else "")
        skel, tables, wfields = normalise_sql(sql)
        p["filter"] = skel[:SHAPE_MAX]
        p["tables"] = tables
        p["entity"] = tables[0] if tables else ""
        p["filter_fields"] = wfields
    else:
        target = pos[1] if len(pos) > 1 else vals.get("table", "")
        p["entity"] = target
        if target:
            p["tables"] = [target]
        if "where" in vals:
            skel, tables, wfields = normalise_sql(f"select * from t where {vals['where']}")
            p["filter"] = re.sub(r"^SELECT \* FROM t WHERE ", "", skel)
            p["filter_fields"] = wfields
    p["flags"] = _clean_bools(bools)
    p["noise"] = {k: v for k, v in vals.items() if k in _VALUE_FLAGS_NOISE}
    return p


def parse_hana(argv: list[str]) -> dict | None:
    pos, vals, bools = _split_flags(argv)
    sql = vals.get("sql") or (pos[0] if pos else "")
    if not sql and "f" in vals:
        # `-f query.sql` — the file path is the only stable identifier we have.
        p = _blank("hana-sql")
        p["verb"] = "file"
        p["entity"] = _basename(vals["f"])
        p["noise"] = {"f": vals["f"]}
        return p
    if not sql:
        return None
    p = _blank("hana-sql")
    p["verb"] = "query"
    skel, tables, wfields = normalise_sql(sql)
    p["filter"] = skel[:SHAPE_MAX]
    p["tables"] = tables
    p["entity"] = tables[0] if tables else ""
    p["filter_fields"] = wfields
    p["flags"] = _clean_bools(bools)
    return p


_SUBCOMMANDISH = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def parse_generic(tool: str, argv: list[str]) -> dict | None:
    """Cobra-style CLIs (dsr, ecom, oms, factory, exim).

    Keeps the leading run of sub-command words and the SET of flag names;
    genericises every value. A positional that looks like a sub-noun
    (lowercase, hyphenated, no digits) is structure; anything else is a value.
    """
    pos, vals, bools = _split_flags(argv, greedy=True)
    if not pos:
        return None
    path: list[str] = []
    args: list[str] = []
    for tok in pos:
        if not args and _SUBCOMMANDISH.match(tok):
            path.append(tok)
            continue
        args.append(tok)
    if not path:
        return None
    if path[0] in WRITE_VERBS or path[0] in BORING_VERBS:
        return None
    p = _blank(tool)
    p["verb"] = " ".join(path)
    # The noun (cobra puts it first: `dsr retailers list`) is the family key.
    p["entity"] = path[0] if len(path) > 1 else ""
    # For these CLIs the flag NAMES are the pattern; their values are not.
    p["filter_fields"] = sorted(
        {k for k in vals if k not in _VALUE_FLAGS_NOISE}
        | {b for b in bools if b not in _BOOL_FLAGS_NOISE})
    parts = [f"--{k} <val>" if k in vals else f"--{k}"
             for k in p["filter_fields"]]
    if args:
        parts.append(" ".join("<arg>" for _ in args))
    p["filter"] = " ".join(parts).strip()
    p["company"] = vals.get("company") or vals.get("db") or vals.get("d", "")
    p["flags"] = _clean_bools(bools)
    p["noise"] = {k: v for k, v in vals.items() if k in _VALUE_FLAGS_NOISE}
    return p


_CLI_PARSERS = {
    "sapb1": parse_sapb1,
    "postsql": parse_postsql,
    "hana-sql": parse_hana,
}


def parse_cli(tool: str, argv: list[str]) -> dict | None:
    fn = _CLI_PARSERS.get(tool)
    if fn is not None:
        return fn(argv)
    return parse_generic(tool, argv)


# ── MCP parsing ──────────────────────────────────────────────────────────────
#
# tool_name is `mcp__<server>__<tool>`; tool_input is the raw arguments object.
# Both verified against a real PostToolUse payload — see harness/PATTERNS.md.

_MCP_SERVER_TO_TOOL = {"sapb1": "sapb1", "postsql": "postsql", "hana": "hana-sql"}

# MCP tool name -> the entity it always reads, so an MCP convenience tool and
# the CLI subcommand it mirrors land on the same shape.
_MCP_ENTITY = {
    "sapb1_partners": "BusinessPartners",
    "sapb1_invoices": "Invoices",
    "sapb1_orders": "Orders",
    "sapb1_items": "Items",
}


def parse_mcp(tool_name: str, args: dict) -> dict | None:
    parts = tool_name.split("__")
    if len(parts) < 3:
        return None
    server, sub = parts[1], "__".join(parts[2:])
    fam = _MCP_SERVER_TO_TOOL.get(server.lower())
    if not fam:
        return None
    verb = sub[len(server) + 1:] if sub.lower().startswith(server.lower() + "_") else sub
    verb = verb.lower() or sub.lower()
    if verb in WRITE_VERBS:
        return None

    p = _blank(fam)
    p["verb"] = verb
    p["company"] = str(args.get("company") or args.get("database") or "")

    if fam == "sapb1":
        p["entity"] = str(args.get("entity") or _MCP_ENTITY.get(sub, "") or "")
        skel, fields = normalise_odata(str(args.get("filter") or ""))
        p["filter"] = skel
        p["filter_fields"] = fields
        for flag in ("customers", "suppliers"):
            if args.get(flag) and "CardType" not in p["filter_fields"]:
                p["filter_fields"] = sorted(set(p["filter_fields"] + ["CardType"]),
                                            key=str.lower)
        if args.get("open") and "DocStatus" not in p["filter_fields"]:
            p["filter_fields"] = sorted(set(p["filter_fields"] + ["DocStatus"]),
                                        key=str.lower)
        p["select"] = _split_select(str(args.get("select") or ""))
        p["orderby"] = str(args.get("orderby") or "")
        p["noise"] = {"top": str(args["top"])} if "top" in args else {}
        return p

    # postsql / hana
    sql = str(args.get("sql") or args.get("query") or "")
    if sql:
        skel, tables, wfields = normalise_sql(sql)
        p["verb"] = "query"
        p["filter"] = skel[:SHAPE_MAX]
        p["tables"] = tables
        p["entity"] = tables[0] if tables else ""
        p["filter_fields"] = wfields
        return p
    target = str(args.get("table") or args.get("term") or args.get("schema") or "")
    p["entity"] = target
    if target:
        p["tables"] = [target]
    return p


# ── canonical shape ──────────────────────────────────────────────────────────

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def sanitise(text: str) -> str:
    """Strip control characters from anything about to be persisted or hashed.

    The literal-hiding sentinel used by normalise_odata / normalise_sql is
    \\x00-delimited. A regex bug once let those sentinels survive into the
    shape string, which put raw NUL bytes into queries.jsonl — breaking grep,
    terminal display and any downstream SQLite TEXT column. The lookaround
    guards in the normalisers are the root-cause fix; this is the backstop at
    the boundary, so no future normaliser change can leak one again.
    """
    if not text:
        return ""
    return _CONTROL_CHARS.sub("", text)


def render_shape(p: dict) -> str:
    """The strict shape string. This is what gets hashed into shape_id.

    Transport-agnostic on purpose: a CLI call and the equivalent MCP call
    render identically, so they cluster as one pattern.
    """
    bits = [p["tool"], p["verb"]]
    # Generic CLIs carry the noun inside the verb path ("retailers list"), so
    # appending entity again would read "dsr retailers list retailers".
    if p["entity"] and p["entity"] not in str(p["verb"]).split():
        bits.append(p["entity"])
    if p["filter"]:
        bits.append(f'--filter "{p["filter"]}"')
    if p["select"]:
        bits.append(f'--select "{",".join(p["select"])}"')
    if p["company"]:
        # `company` is the SAP CompanyDB; for postsql/hana the same slot holds
        # the database. Render it with the flag the operator actually typed.
        flag = "--company" if p["tool"] == "sapb1" else "--db"
        bits.append(f'{flag} {p["company"]}')
    for f in p["flags"]:
        bits.append(f"--{f}")
    return sanitise(" ".join(b for b in bits if b))[:SHAPE_MAX]


def render_family(p: dict) -> str:
    """The coarse shape: same table, same filter fields, any columns.

    This is the owner's question — "someone keeps selecting from one place,
    one table" — and it survives a colleague adding a column to --select.
    """
    bits = [p["tool"], p["verb"], p["entity"] or "-"]
    if p["filter_fields"]:
        bits.append("by:" + ",".join(p["filter_fields"]))
    if p["company"]:
        bits.append("@" + p["company"])
    return sanitise(" ".join(bits))[:SHAPE_MAX]


def _sid(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


# ── question attribution ─────────────────────────────────────────────────────

def _recent_question_shape() -> str:
    """shape_id of the most recent logged question, if it is recent enough.

    Reads only the tail of log.jsonl, so cost stays flat as the log grows.
    Lets `propose` answer "is this table being reached from several different
    phrasings?" — the exact blind spot the question-shape signal has.
    """
    try:
        size = QLOG.stat().st_size
    except OSError:
        return ""
    try:
        with QLOG.open("rb") as fh:
            fh.seek(max(0, size - 8192))
            chunk = fh.read().decode("utf-8", "replace")
    except OSError:
        return ""
    lines = [ln for ln in chunk.splitlines() if ln.strip()]
    if size > 8192 and lines:
        lines = lines[1:]  # first line is probably partial
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = str(rec.get("ts", ""))
        try:
            age = (_dt.datetime.now() - _dt.datetime.fromisoformat(ts)).total_seconds()
        except ValueError:
            return ""
        if 0 <= age <= ATTRIB_WINDOW_S:
            return str(rec.get("shape_id", ""))
        return ""
    return ""


# ── record ───────────────────────────────────────────────────────────────────

def _extract_from_payload(payload: dict) -> list[tuple[dict, str]]:
    """Return [(parsed, raw_command)] for the JIVO calls in this payload.

    Only ``tool_name`` and ``tool_input`` are read. ``tool_response`` is never
    touched — see REDACTION in the module docstring.
    """
    tool_name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []

    if tool_name.startswith("mcp__"):
        # Scrub BEFORE parsing so every derived field (entity, filter, scope,
        # shape) inherits the redaction. Scrubbing only the raw string left a
        # connection-string password in the `company` field, which the
        # fail-closed sweep then had to throw the whole record away over.
        clean_input = {k: (scrub(v) if isinstance(v, str) else v)
                       for k, v in tool_input.items()}
        p = parse_mcp(tool_name, clean_input)
        if not p:
            return []
        raw = f"{tool_name} " + json.dumps(
            {k: v for k, v in sorted(clean_input.items())}, ensure_ascii=False)
        return [(p, raw)]

    if tool_name != "Bash":
        return []
    command = str(tool_input.get("command") or "")
    if not command:
        return []

    # If ANY part of the command touches a credential file, drop the whole
    # payload. A per-segment check would keep the harmless half of
    # `cat .env && sapb1 doctor`, which is defensible but harder to state as a
    # guarantee. Whole-payload is the rule we can actually promise.
    if touches_credential_file(command):
        return []

    out: list[tuple[dict, str]] = []
    seen: set[str] = set()
    for seg_raw in split_segments(command):
        seg = scrub(seg_raw)
        toks = tokenise(seg)
        if not toks:
            continue
        hit = find_invocation(toks)
        if not hit:
            continue
        tool, argv = hit
        p = parse_cli(tool, argv)
        if not p:
            continue
        key = render_shape(p)
        # Dedupe within ONE tool call: a `for` loop over 50 card codes, or a
        # query piped into jq, is one act — not 50 or 2.
        if key in seen:
            continue
        seen.add(key)
        out.append((p, seg))
    return out


STDIN_WAIT_S = float(os.environ.get("JIVO_QMINT_STDIN_WAIT", "2"))


def _read_stdin() -> str:
    """Read the payload from stdin without ever blocking indefinitely.

    ``isatty()`` is not a sufficient guard: an OPEN PIPE that never delivers
    data is not a tty, so a plain ``read()`` blocks forever. A PostToolUse hook
    runs after every single tool call, so a blocking read is a latency landmine
    — measured at a hard hang until the harness timeout killed it. Wait briefly
    for readiness, then give up quietly.

    ``select`` on stdin works on POSIX and under git-bash's MSYS python; if it
    raises anywhere, fall back to the plain read rather than losing the payload.
    """
    if sys.stdin.isatty():
        return ""
    try:
        import select
        ready, _, _ = select.select([sys.stdin], [], [], STDIN_WAIT_S)
        if not ready:
            return ""
    except Exception:
        pass  # no select on this platform/stream — accept the plain read
    try:
        return sys.stdin.read()
    except (OSError, ValueError):
        return ""


def cmd_record(args: argparse.Namespace) -> int:
    """Normalise a PostToolUse payload from stdin. Always silent, always 0."""
    blob = _read_stdin()
    if not blob.strip():
        return 0
    try:
        payload = json.loads(blob)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    try:
        found = _extract_from_payload(payload)
    except Exception:  # pragma: no cover - a hook must never break a turn
        return 0
    if not found:
        return 0

    persona = _active_persona()
    session = str(payload.get("session_id") or "")[:8]
    tool_name = str(payload.get("tool_name") or "")
    q_shape = _recent_question_shape()
    now = _dt.datetime.now().isoformat(timespec="seconds")

    lines: list[str] = []
    for p, raw in found:
        # `raw` was already scrubbed at the input boundary; re-running scrub is
        # idempotent and cheap, and keeps this correct if a future caller
        # bypasses _extract_from_payload.
        raw_clean = sanitise(scrub(raw))
        if secret_residue(raw_clean):
            # Fail closed: the scrubber did not fully understand this form.
            continue
        shape = render_shape(p)
        family = render_family(p)
        rec = {
            "ts": now,
            "persona": persona,
            "session": session,
            "tool": sanitise(tool_name),
            "family": p["tool"],
            "raw": raw_clean[:RAW_MAX],
            "shape": shape,
            "shape_id": _sid(shape),
            "family_id": _sid(family),
            "q_shape_id": q_shape or None,
            "parsed": {
                "tool": p["tool"], "verb": sanitise(p["verb"]),
                "entity": sanitise(p["entity"]),
                "filter": sanitise(p["filter"]),
                "filter_fields": [sanitise(x) for x in p["filter_fields"]],
                "select": [sanitise(x) for x in p["select"]],
                "company": sanitise(p["company"]),
                "tables": [sanitise(x) for x in p["tables"]],
                "flags": p["flags"],
                "orderby": sanitise(p["orderby"]),
            },
        }
        line = json.dumps(rec, ensure_ascii=False)
        # Paranoid final sweep on the assembled line, not just the command.
        if secret_residue(line):
            continue
        lines.append(line)

    if not lines:
        return 0
    try:
        QUESTIONS.mkdir(parents=True, exist_ok=True)
        with QUERYLOG.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except OSError:
        return 0
    if getattr(args, "verbose", False):
        for line in lines:
            print(line)
    return 0


# ── load + metrics ───────────────────────────────────────────────────────────

def _load_queries() -> list[dict]:
    if not QUERYLOG.exists():
        return []
    out: list[dict] = []
    for line in QUERYLOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _minted_ids() -> tuple[set[str], set[str]]:
    """(query_shape_ids, query_family_ids) already covered by a skill."""
    shapes: set[str] = set()
    fams: set[str] = set()
    if not SKILLS.exists():
        return shapes, fams
    for p in sorted(SKILLS.rglob("SKILL.md")):
        meta, _ = _parse_frontmatter(p)
        for key, sink in (("query_shape_id", shapes), ("query_family_id", fams)):
            v = meta.get(key)
            if not v:
                continue
            if isinstance(v, list):
                sink.update(str(x) for x in v)
            else:
                sink.add(str(v))
    return shapes, fams


def _day(ts: str) -> str:
    return str(ts)[:10]


def _week(ts: str) -> str:
    try:
        y, w, _ = _dt.date.fromisoformat(_day(ts)).isocalendar()
        return f"{y}-W{w:02d}"
    except ValueError:
        return ""


def _cluster(records: list[dict], key: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in records:
        k = str(r.get(key) or "")
        if not k:
            continue
        c = out.setdefault(k, {
            "runs": 0, "days": set(), "weeks": set(), "personas": set(),
            "sessions": set(), "q_shapes": set(), "shapes": set(),
            "first": "", "last": "", "examples": [], "parsed": None,
            "shape": r.get("shape", ""),
        })
        ts = str(r.get("ts") or "")
        c["runs"] += 1
        c["days"].add(_day(ts))
        w = _week(ts)
        if w:
            c["weeks"].add(w)
        c["personas"].add(str(r.get("persona") or "all"))
        if r.get("session"):
            c["sessions"].add(str(r["session"]))
        if r.get("q_shape_id"):
            c["q_shapes"].add(str(r["q_shape_id"]))
        c["shapes"].add(str(r.get("shape_id") or ""))
        if not c["first"] or ts < c["first"]:
            c["first"] = ts
        if ts > c["last"]:
            c["last"] = ts
        if len(c["examples"]) < 5 and r.get("raw"):
            c["examples"].append(str(r["raw"]))
        if c["parsed"] is None and isinstance(r.get("parsed"), dict):
            c["parsed"] = r["parsed"]
    return out


def _recency_factor(last: str, today: _dt.date | None = None) -> float:
    today = today or _dt.date.today()
    try:
        age = (today - _dt.date.fromisoformat(_day(last))).days
    except ValueError:
        return RECENCY_COLD_FACTOR
    if age <= RECENCY_FRESH_DAYS:
        return 1.0
    if age <= RECENCY_WARM_DAYS:
        return RECENCY_WARM_FACTOR
    return RECENCY_COLD_FACTOR


def _metrics(c: dict, today: _dt.date | None = None) -> dict:
    runs = c["runs"]
    days = len(c["days"])
    weeks = len(c["weeks"])
    personas = len(c["personas"])
    sessions = len(c["sessions"])
    qshapes = len(c["q_shapes"])

    spread = W_DAY * min(days, W_DAY_CAP)
    persist = W_WEEK * min(max(weeks - 1, 0), W_WEEK_CAP)
    volume = W_VOLUME * math.log2(runs + 1)
    breadth = W_PERSONA * max(personas - 1, 0) + W_SESSION * min(sessions, W_SESSION_CAP)
    phrasing = W_PHRASING * min(max(qshapes - 1, 0), W_PHRASING_CAP)
    recency = _recency_factor(c["last"], today)
    score = (spread + persist + volume + breadth + phrasing) * recency

    return {
        "runs": runs, "days": days, "weeks": weeks, "personas": personas,
        "sessions": sessions, "q_shapes": qshapes,
        "first": c["first"], "last": c["last"],
        "spread": round(spread, 2), "persist": round(persist, 2),
        "volume": round(volume, 2), "breadth": round(breadth, 2),
        "phrasing": round(phrasing, 2), "recency": recency,
        "score": round(score, 2),
    }


def _gate(m: dict, min_runs: int, min_days: int, min_sessions: int) -> list[str]:
    """Return the list of unmet gate conditions ([] means the shape passes)."""
    fails = []
    if m["runs"] < min_runs:
        fails.append(f"runs {m['runs']}<{min_runs}")
    if m["days"] < min_days:
        fails.append(f"days {m['days']}<{min_days}")
    if m["sessions"] < min_sessions:
        fails.append(f"sessions {m['sessions']}<{min_sessions}")
    return fails


# ── propose ──────────────────────────────────────────────────────────────────

def cmd_propose(args: argparse.Namespace) -> int:
    records = _load_queries()
    if not records:
        print("query log is empty — nothing to propose yet.")
        print(f"  (expected at {QUERYLOG.relative_to(REPO)})")
        print("  the PostToolUse hook fills it as operators run JIVO CLIs.")
        return 0

    min_runs = args.min_runs if args.min_runs is not None else MIN_RUNS
    min_days = args.min_days if args.min_days is not None else MIN_DAYS
    min_sess = args.min_sessions if args.min_sessions is not None else MIN_SESSIONS

    shapes = _cluster(records, "shape_id")
    fams = _cluster(records, "family_id")
    minted_shapes, minted_fams = _minted_ids()

    rows = []
    for sid, c in shapes.items():
        m = _metrics(c)
        fam_id = ""
        for r in records:
            if r.get("shape_id") == sid:
                fam_id = str(r.get("family_id") or "")
                break
        skipped = ""
        if sid in minted_shapes:
            skipped = "already minted"
        elif fam_id in minted_fams:
            skipped = "family already minted"
        rows.append({
            "shape_id": sid, "family_id": fam_id, "shape": c["shape"],
            "metrics": m, "gate": _gate(m, min_runs, min_days, min_sess),
            "skipped": skipped, "examples": c["examples"],
            "parsed": c["parsed"] or {},
        })
    rows.sort(key=lambda r: -r["metrics"]["score"])

    candidates = [r for r in rows if not r["gate"] and not r["skipped"]]

    if args.json:
        print(json.dumps({
            "records": len(records),
            "distinct_shapes": len(shapes),
            "distinct_families": len(fams),
            "gate": {"min_runs": min_runs, "min_days": min_days,
                     "min_sessions": min_sess},
            "candidates": candidates,
            "all": rows if args.explain else [],
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"{len(records)} query call(s) logged, {len(shapes)} distinct shape(s), "
          f"{len(fams)} distinct family(ies)")
    print(f"gate: >={min_runs} runs AND >={min_days} distinct days AND "
          f">={min_sess} distinct sessions\n")

    if candidates:
        print(f"{len(candidates)} shape(s) ready to become skills:\n")
        for r in candidates:
            m = r["metrics"]
            print(f"  score {m['score']:>6}  shape_id={r['shape_id']}  "
                  f"family_id={r['family_id']}")
            print(f"      {m['runs']}x over {m['days']}d / {m['weeks']}w · "
                  f"{m['personas']} persona(s) · {m['sessions']} session(s) · "
                  f"{m['q_shapes']} phrasing(s) · last {m['last'][:10]}")
            print(f"      {r['shape'][:150]}")
            if args.explain:
                print(f"      spread {m['spread']} + persist {m['persist']} "
                      f"+ volume {m['volume']} + breadth {m['breadth']} "
                      f"+ phrasing {m['phrasing']}  x recency {m['recency']}")
            for ex in r["examples"][:2]:
                print(f"      e.g. {ex[:110]}")
            print()
    else:
        print("No query shape has earned a skill yet.\n")

    near = [r for r in rows if (r["gate"] or r["skipped"])][:args.top]
    if near:
        print("Not (yet) candidates:")
        for r in near:
            m = r["metrics"]
            why = r["skipped"] or ", ".join(r["gate"])
            print(f"  {m['runs']:>3}x/{m['days']}d  {r['shape_id']}  "
                  f"[{why}]  {r['shape'][:70]}")
        print()

    # The family view is the owner's question: is one table being hit over and
    # over through several different strict shapes?
    multi = [(fid, c) for fid, c in fams.items() if len(c["shapes"]) > 1]
    multi.sort(key=lambda kv: -_metrics(kv[1])["score"])
    if multi:
        print("Families spanning several strict shapes "
              "(one skill may cover all of them):")
        for fid, c in multi[:args.top]:
            m = _metrics(c)
            p = c["parsed"] or {}
            label = f"{p.get('tool','?')} {p.get('verb','')} {p.get('entity','')}".strip()
            print(f"  score {m['score']:>6}  family_id={fid}  "
                  f"{len(c['shapes'])} shapes · {m['runs']}x over {m['days']}d · "
                  f"{m['personas']} persona(s)")
            print(f"      {label}"
                  + (f"  by {','.join(p.get('filter_fields') or [])}"
                     if p.get("filter_fields") else ""))
        print()

    if candidates:
        print("These are CANDIDATES, not skills. To turn one into a skill:")
        print("  python3 harness/bin/patterns.py draft <shape_id>")
        print("Then VERIFY the query against live SAP before saving the file.")
        print("An unverified minted skill produces a wrong financial number")
        print("that someone acts on — that is why draft only prints.")
    return 0


# ── draft ────────────────────────────────────────────────────────────────────

def _question_examples(q_shape_ids: set[str], limit: int = 6) -> list[str]:
    """Real operator phrasings that led to this query shape.

    The trigger line of a skill has to be written in the words operators
    actually use, and those words are in the question log, not the command.
    """
    if not q_shape_ids or not QLOG.exists():
        return []
    seen: set[str] = set()
    out: list[str] = []
    for line in QLOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = str(rec.get("shape_id") or "")
        if sid not in q_shape_ids or sid in seen:
            continue
        q = str(rec.get("question") or "").strip()
        if q:
            seen.add(sid)
            out.append(q)
        if len(out) >= limit:
            break
    return out


def _placeholderise(p: dict, shape: str) -> str:
    """Turn generic <val>/<date> markers into named parameters."""
    out = shape
    fields = list(p.get("filter_fields") or [])
    for f in fields:
        token = f"<{re.sub(r'[^A-Za-z0-9]', '_', f).upper()}>"
        out = re.sub(rf"(\b{re.escape(f)}\s+(?:eq|ne|gt|ge|lt|le)\s+)<(?:val|num)>",
                     lambda m, t=token: m.group(1) + f"'{t}'", out, count=1)
    out = out.replace("<date>", "<YYYY-MM-DD>")
    out = out.replace("<val>", "<VALUE>").replace("<num>", "<NUMBER>")
    return out


def cmd_draft(args: argparse.Namespace) -> int:
    records = _load_queries()
    mine = [r for r in records if str(r.get("shape_id")) == args.shape_id]
    if not mine:
        fam = [r for r in records if str(r.get("family_id")) == args.shape_id]
        if not fam:
            print(f"error: no logged query has shape_id or family_id "
                  f"'{args.shape_id}'.", file=sys.stderr)
            print("  run: python3 harness/bin/patterns.py propose",
                  file=sys.stderr)
            return 2
        mine = fam

    cluster = _cluster(mine, "shape_id" if mine[0].get("shape_id") == args.shape_id
                       else "family_id")
    c = cluster.get(args.shape_id) or next(iter(cluster.values()))
    m = _metrics(c)
    p = c["parsed"] or {}
    shape = c["shape"] or ""
    minted_shapes, minted_fams = _minted_ids()

    entity = p.get("entity") or "data"
    fields = p.get("filter_fields") or []
    tool = p.get("tool") or "sapb1"
    verb = p.get("verb") or "query"
    by = " and ".join(fields[:3]) if fields else "no filter"

    name = _slug(f"jivo-{tool}-{entity}-by-{'-'.join(f.lower() for f in fields[:2])}"
                 if fields else f"jivo-{tool}-{entity}", 48)
    questions = _question_examples(c["q_shapes"])
    trigger = questions[0] if questions else f"a {entity} lookup by {by}"

    example = _placeholderise(p, shape)
    real = c["examples"][0] if c["examples"] else shape

    fm = [
        "---",
        f"name: {name}",
        f"description: Use when an operator asks about {entity} filtered by "
        f"{by} — e.g. \"{trigger[:80]}\". Runs the verified read-only "
        f"{tool} query and reports the number with its source.",
        f"query_shape_id: {args.shape_id}",
        f"query_family_id: {str(mine[0].get('family_id') or '')}",
        f"persona: {','.join(sorted(c['personas']))}",
        f"minted: {_dt.date.today().isoformat()}",
        f"evidence_runs: {m['runs']}",
        f"evidence_days: {m['days']}",
        f"evidence_weeks: {m['weeks']}",
        f"evidence_personas: {m['personas']}",
        f"evidence_sessions: {m['sessions']}",
        f"evidence_phrasings: {m['q_shapes']}",
        f"evidence_first_seen: {m['first'][:10]}",
        f"evidence_last_seen: {m['last'][:10]}",
        f"evidence_score: {m['score']}",
        "status: draft-unverified",
        "---",
        "",
    ]

    body = [
        "> **DRAFT — UNVERIFIED. Do not save this file yet.**",
        ">",
        "> This was written by `harness/bin/patterns.py draft` from "
        f"{m['runs']} real logged runs. Nothing here has been executed. Before "
        "saving:",
        ">",
        "> 1. Run the command below against live SAP and confirm it returns "
        "what this skill claims.",
        "> 2. Check the definitions against `harness/corrections/INDEX.md` — a "
        "correction may already govern this metric.",
        "> 3. Delete this banner and set `status: verified` in the frontmatter.",
        ">",
        "> A wrong skill here produces a wrong financial number someone acts "
        "on. That is why this tool prints and never writes.",
        "",
        f"# {entity} by {by}",
        "",
        "## When to use",
        "",
    ]
    if questions:
        body.append("Real operator phrasings that led to this query:")
        body.append("")
        for q in questions:
            body.append(f"- \"{q[:160]}\"")
        if len(questions) > 1:
            body.append("")
            body.append(
                f"Note: {len(questions)} distinct phrasings, one query. That is "
                "why this skill is keyed on the query, not the wording.")
    else:
        body.append(
            f"When an operator needs {entity} filtered by {by}. "
            "(No question phrasings were captured for this shape — the runs "
            "came from a hook, a script, or a session that predates question "
            "logging. Write the trigger from the evidence below.)")
    body += [
        "",
        "## The query",
        "",
        "```bash",
        f"# parameters are marked <LIKE_THIS> — substitute before running",
        example,
        "```",
        "",
        "Verified-shape source: one of the real logged runs was",
        "",
        "```bash",
        real,
        "```",
        "",
        "## Parameters",
        "",
    ]
    if fields:
        for f in fields:
            body.append(f"- `{f}` — varies per call; every logged run filtered on it.")
    else:
        body.append("- none — this shape takes no filter.")
    if p.get("select"):
        body += ["", "Columns this shape reads: "
                 + ", ".join(f"`{c2}`" for c2 in p["select"]) + "."]
    if p.get("company"):
        body += ["", f"Company / database: `{p['company']}`. Name it in the "
                 "answer whenever it is not Oil."]
    if p.get("tables"):
        body += ["", "Tables touched: " + ", ".join(f"`{t}`" for t in p["tables"]) + "."]

    body += [
        "",
        "## Verify before you trust it",
        "",
        "- Re-run the command and eyeball one row against the SAP UI.",
        "- Confirm the sign convention: `CurrentAccountBalance` positive = "
        "DEBIT (party owes JIVO), negative = CREDIT (JIVO owes them).",
        "- For turnover, net GST out (`DocTotal - VatSum`) and subtract "
        "`CreditNotes`; exclude `Cancelled eq 'tNO'`.",
        "- Money is INR: present with Indian grouping, crores for big numbers.",
        "",
        "## Evidence",
        "",
        f"- {m['runs']} runs across {m['days']} distinct day(s) / "
        f"{m['weeks']} week(s)",
        f"- {m['personas']} persona(s): {', '.join(sorted(c['personas']))}",
        f"- {m['sessions']} distinct session(s)",
        f"- {m['q_shapes']} distinct question phrasing(s)",
        f"- first seen {m['first'][:10]}, last seen {m['last'][:10]}",
        f"- ranking score {m['score']} "
        f"(spread {m['spread']} + persist {m['persist']} + volume {m['volume']} "
        f"+ breadth {m['breadth']} + phrasing {m['phrasing']}, "
        f"x recency {m['recency']})",
        "",
        f"Read-only: this skill issues `{tool} {verb}` only. It must never be "
        "edited to write. See RULE 0 in `CLAUDE.md`.",
        "",
    ]

    if args.shape_id in minted_shapes:
        print(f"# NOTE: shape_id {args.shape_id} is already declared by an "
              f"existing skill.", file=sys.stderr)
    if str(mine[0].get("family_id") or "") in minted_fams:
        print(f"# NOTE: this family is already covered by an existing skill.",
              file=sys.stderr)

    sys.stdout.write("\n".join(fm + body))
    return 0


# ── status ───────────────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> int:
    records = _load_queries()
    shapes = _cluster(records, "shape_id")
    fams = _cluster(records, "family_id")
    minted_shapes, minted_fams = _minted_ids()

    print("JIVO query-pattern status")
    print(f"  persona (this machine) : {_active_persona()}")
    print(f"  log                    : "
          f"{QUERYLOG.relative_to(REPO) if QUERYLOG.exists() else 'MISSING (no calls captured yet)'}")
    print(f"  calls captured         : {len(records)}")
    print(f"  distinct shapes        : {len(shapes)}")
    print(f"  distinct families      : {len(fams)}")
    print(f"  skills declaring shapes: {len(minted_shapes)} shape(s), "
          f"{len(minted_fams)} family(ies)")
    print(f"  gate                   : >={MIN_RUNS} runs, >={MIN_DAYS} days, "
          f">={MIN_SESSIONS} sessions")
    by_tool: dict[str, int] = {}
    for r in records:
        by_tool[str(r.get("family") or "?")] = by_tool.get(str(r.get("family") or "?"), 0) + 1
    if by_tool:
        print("  by tool                : "
              + ", ".join(f"{k}={v}" for k, v in sorted(by_tool.items())))
    return 0


# ── selftest ─────────────────────────────────────────────────────────────────

def _payload(tool_name: str, tool_input: dict, session: str = "sess0001") -> dict:
    """A PostToolUse payload in the REAL shape.

    Field set verified by capturing live hook invocations — see
    harness/PATTERNS.md "Payload schema". `tool_response` is included here on
    purpose: the test proves we ignore it.
    """
    return {
        "session_id": session,
        "transcript_path": "/tmp/t.jsonl",
        "cwd": "/Users/x/jivo-cli",
        "prompt_id": "p-0001",
        "permission_mode": "dontAsk",
        "hook_event_name": "PostToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_response": {"stdout": "SECRET_ROW_DATA_MUST_NOT_APPEAR",
                          "stderr": "", "interrupted": False},
        "tool_use_id": "toolu_x",
        "duration_ms": 42,
    }


def _bash(cmd: str, session: str = "sess0001") -> dict:
    return _payload("Bash", {"command": cmd, "description": "d"}, session)


def cmd_selftest(args: argparse.Namespace) -> int:
    """Verification battery. Writes only to a temp dir; runs no business query."""
    import tempfile

    global QUESTIONS, QUERYLOG, QLOG, SKILLS
    tmp = Path(tempfile.mkdtemp(prefix="jivo-patterns-selftest-"))
    QUESTIONS = tmp / "questions"
    QUERYLOG = QUESTIONS / "queries.jsonl"
    QLOG = QUESTIONS / "log.jsonl"
    SKILLS = tmp / "skills"
    QUESTIONS.mkdir(parents=True, exist_ok=True)

    passed: list[str] = []
    failed: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        (passed if ok else failed).append(label + (f"  [{detail}]" if detail else ""))

    def shape_of(payload: dict) -> str:
        got = _extract_from_payload(payload)
        return _sid(render_shape(got[0][0])) if got else ""

    def shapestr(payload: dict) -> str:
        got = _extract_from_payload(payload)
        return render_shape(got[0][0]) if got else ""

    # 1. Same pattern, different values -> one shape.
    a = _bash("./sap-b1/cli/sapb1 query BusinessPartners "
              "--filter \"CardCode eq 'V0001'\" "
              "--select \"CardName,CurrentAccountBalance\"")
    b = _bash("sapb1 query BusinessPartners --filter \"CardCode eq 'C0457'\" "
              "--select \"CardName,CurrentAccountBalance\" --top 5 --json")
    check("values vary -> same shape", shape_of(a) == shape_of(b),
          f"{shape_of(a)} vs {shape_of(b)}")

    # 1b. Placeholder sentinels must never survive into a shape. A regex bug
    # once let \x00-delimited literal placeholders through, which put raw NUL
    # bytes into queries.jsonl and silently broke <val>/<date> rendering.
    check("string literal renders as <val>",
          'CardCode eq <val>' in shapestr(a), shapestr(a))
    check("no control chars in shape string",
          not re.search(r"[\x00-\x1f\x7f]", shapestr(a)), repr(shapestr(a)))

    # 1c. <date> and <val> are genuinely distinguished, not collapsed.
    dt1 = _bash("sapb1 query Invoices --filter \"DocDate ge '2026-04-01'\" "
                "--select \"DocTotal\"")
    vv1 = _bash("sapb1 query Invoices --filter \"DocDate ge 'notadate'\" "
                "--select \"DocTotal\"")
    check("date literal renders as <date>", "<date>" in shapestr(dt1), shapestr(dt1))
    check("NEG <date> and <val> are distinct", shape_of(dt1) != shape_of(vv1))

    # 2. Column order and pagination are not the pattern.
    c = _bash("sapb1 query BusinessPartners --filter \"CardCode eq 'X1'\" "
              "--select \"CurrentAccountBalance,CardName\" --page-size 200")
    check("select order + page-size ignored", shape_of(a) == shape_of(c))

    # 3. CLI and MCP collapse.
    d = _payload("mcp__sapb1__sapb1_query",
                 {"entity": "BusinessPartners", "filter": "CardCode eq 'V0009'",
                  "select": "CardName,CurrentAccountBalance", "top": 20})
    check("CLI and MCP collapse", shape_of(a) == shape_of(d),
          f"{shape_of(a)} vs {shape_of(d)}")

    # 4. NEGATIVE: different filter field must NOT collapse.
    e = _bash("sapb1 query BusinessPartners --filter \"CardType eq 'cSupplier'\" "
              "--select \"CardName,CurrentAccountBalance\"")
    check("NEG different filter field -> different shape", shape_of(a) != shape_of(e))

    # 5. NEGATIVE: different entity must NOT collapse.
    f = _bash("sapb1 query Invoices --filter \"CardCode eq 'V0001'\" "
              "--select \"CardName,CurrentAccountBalance\"")
    check("NEG different entity -> different shape", shape_of(a) != shape_of(f))

    # 6. NEGATIVE: --count changes the need.
    g = _bash("sapb1 query BusinessPartners --filter \"CardCode eq 'V0001'\" "
              "--select \"CardName,CurrentAccountBalance\" --count")
    check("NEG --count -> different shape", shape_of(a) != shape_of(g))

    # 7. NEGATIVE: different company is a different pattern.
    h = _bash("sapb1 query BusinessPartners --filter \"CardCode eq 'V1'\" "
              "--select \"CardName,CurrentAccountBalance\" --company JIVO_MART_HANADB")
    check("NEG different company -> different shape", shape_of(a) != shape_of(h))

    # 8. Dates genericise; two date-range queries collapse.
    i1 = _bash("sapb1 query Invoices --filter \"DocDate ge '2026-04-01' and "
               "DocDate lt '2026-07-01' and Cancelled eq 'tNO'\" "
               "--select \"DocTotal,VatSum\" --all")
    i2 = _bash("sapb1 query Invoices --filter \"DocDate ge '2025-04-01' and "
               "DocDate lt '2026-04-01' and Cancelled eq 'tNO'\" "
               "--select \"VatSum,DocTotal\" --all")
    check("date ranges collapse", shape_of(i1) == shape_of(i2))
    check("NEG date-range shape != cardcode shape", shape_of(i1) != shape_of(a))

    # 9. SQL: literals + IN list + LIMIT collapse; table is preserved.
    s1 = _bash("postsql query \"SELECT id, name FROM orders WHERE status = 'open' "
               "AND id IN (1,2,3) LIMIT 10\" --db jivo_oms")
    s2 = _bash("postsql query \"SELECT id, name FROM orders WHERE status = 'shipped' "
               "AND id IN (9,8) LIMIT 500\" --db jivo_oms")
    check("SQL literals/IN/LIMIT collapse", shape_of(s1) == shape_of(s2),
          shapestr(s1))
    s3 = _bash("postsql query \"SELECT id, name FROM shipments WHERE status = 'open' "
               "LIMIT 10\" --db jivo_oms")
    check("NEG different SQL table -> different shape", shape_of(s1) != shape_of(s3))

    # 10. postsql MCP collapses with the postsql CLI.
    s4 = _payload("mcp__postsql__postgres_query",
                  {"sql": "SELECT id, name FROM orders WHERE status = 'x' "
                          "AND id IN (4,5,6) LIMIT 20", "database": "jivo_oms"})
    check("postsql CLI and MCP collapse", shape_of(s1) == shape_of(s4),
          f"{shapestr(s1)} vs {shapestr(s4)}")

    # 11. hana-sql parses and preserves the schema-qualified table.
    hq = _bash("./hana-sql/hana-sql \"SELECT DocNum FROM \\\"JIVO_OIL\\\".\\\"OINV\\\" "
               "WHERE DocDate >= '2026-04-01'\"")
    got = _extract_from_payload(hq)
    check("hana-sql parsed", bool(got) and got[0][0]["tool"] == "hana-sql",
          shapestr(hq))
    check("hana-sql strips quotes from the qualified table",
          bool(got) and got[0][0]["tables"] == ["JIVO_OIL.OINV"],
          str(got[0][0]["tables"]) if got else "")
    check("placeholders render lowercase in SQL too",
          "<date>" in shapestr(hq) and "<DATE>" not in shapestr(hq),
          shapestr(hq))

    # 12. Generic cobra CLI.
    dq = _bash("./dsr-cli/dsr retailers list --beat 4471 --limit 50")
    got = _extract_from_payload(dq)
    check("generic CLI parsed", bool(got) and got[0][0]["tool"] == "dsr",
          shapestr(dq))
    dq2 = _bash("dsr retailers list --beat 9902 --limit 10")
    check("generic CLI values genericised", shape_of(dq) == shape_of(dq2))
    dq3 = _bash("dsr sales list --beat 4471")
    check("NEG different subcommand -> different shape", shape_of(dq) != shape_of(dq3))

    # 12b. Prose, comments and source code that merely MENTION a CLI name must
    # not be read as invocations. Found by dogfooding: this hook was live during
    # development and logged `sapb1 pattern, three` from the author's heredocs.
    for label, cmd in (
        ("shell comment", "# --- same sapb1 pattern, three different values ---"),
        ("trailing comment", "ls -la   # then run postsql query later"),
        ("python string literal",
         "BP = ('sapb1 query BusinessPartners --filter \"x\"')"),
        ("prose mention", "echo 'postsql via MCP: must collapse'"),
        ("unknown subcommand", "sapb1 wibble --filter \"a eq 'b'\""),
        ("bare tool name", "which sapb1"),
    ):
        check(f"NEG not an invocation: {label}",
              not _extract_from_payload(_bash(cmd)),
              str([render_shape(x[0]) for x in _extract_from_payload(_bash(cmd))]))
    # ...but the real forms still work, including the ones that look similar.
    for label, cmd in (
        ("env-assignment prefix",
         "PGPASSWORD=x postsql query \"SELECT a FROM t\" --db d"),
        ("loop body", "for c in V1 V2; do sapb1 query Items --select \"ItemCode\"; done"),
        ("cd-then-run", "cd sap-b1/cli && ./sapb1 query Items --select \"ItemCode\""),
        ("hana bare sql", "hana-sql \"SELECT a FROM t\""),
    ):
        check(f"POS still captured: {label}", bool(_extract_from_payload(_bash(cmd))))

    # 13. Non-JIVO tools are ignored entirely.
    check("non-JIVO bash ignored", not _extract_from_payload(_bash("ls -la /tmp")))
    check("non-JIVO MCP ignored",
          not _extract_from_payload(_payload("mcp__github__list_prs", {"repo": "x"})))
    check("Read tool ignored",
          not _extract_from_payload(_payload("Read", {"file_path": "/etc/hosts"})))

    # 14. Writes are never captured.
    check("sapb1 draft not captured",
          not _extract_from_payload(_bash("sapb1 draft Invoices --file x.json")))

    # 15. Pipelines and loops dedupe to one record.
    pipe = _bash("sapb1 query Items --select \"ItemCode,ItemName\" --json | jq '.value|length'")
    check("pipeline yields one record", len(_extract_from_payload(pipe)) == 1)
    loop = _bash("for c in V1 V2 V3; do sapb1 query BusinessPartners "
                 "--filter \"CardCode eq '$c'\" --select \"CardName\"; done")
    check("loop dedupes to one record", len(_extract_from_payload(loop)) <= 1,
          str(len(_extract_from_payload(loop))))

    # 16. REDACTION.
    pw = _bash("sapb1 doctor --user testuser --password 'Hunt3r$ecret!' "
               "--host 10.0.0.5")
    got = _extract_from_payload(pw)
    raws = [scrub(r) for _, r in got]
    check("password value scrubbed",
          bool(raws) and "Hunt3r" not in raws[0] and "<redacted>" in raws[0],
          raws[0] if raws else "no parse")
    check("username scrubbed", bool(raws) and "testuser" not in raws[0])

    env = "PGPASSWORD=sup3rs3cret postsql query \"SELECT 1 FROM orders\" --db d"
    check("env PGPASSWORD scrubbed", "sup3rs3cret" not in scrub(env))
    uri = "postsql query \"SELECT 1 FROM t\" --db postgres://jivo:p4ss@10.0.0.1:5432/db"
    check("URI userinfo scrubbed", "p4ss" not in scrub(uri))
    for label, blob in (
        ("anthropic key", "sapb1 query X --filter \"a eq 'sk-ant-" + "A" * 95 + "'\""),
        ("github pat", "sapb1 query X --filter \"a eq 'ghp_" + "b" * 36 + "'\""),
        ("aws key", "sapb1 query X --filter \"a eq 'AKIAIOSFODNN7EXAMPLE'\""),
        ("jwt", "sapb1 query X --filter \"a eq 'eyJhbGciOiJIUzI1NiJ9."
                "eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U'\""),
    ):
        check(f"secret literal scrubbed: {label}",
              not secret_residue(scrub(blob)), scrub(blob)[:60])

    # 17. tool_response is structurally never read.
    got = _extract_from_payload(_bash("sapb1 query Items --select \"ItemCode\""))
    blob = json.dumps(got)
    check("tool_response never reaches the record",
          "SECRET_ROW_DATA_MUST_NOT_APPEAR" not in blob)

    # 18. Credential-file commands drop the WHOLE payload, not just the segment
    # that names the file — otherwise `cat .env && sapb1 doctor` still logs the
    # second half and the guarantee gets hard to state.
    check("credential-file payload dropped whole",
          not _extract_from_payload(_bash("cat sap-b1/cli/.env && sapb1 doctor")))
    check("normal command not dropped",
          bool(_extract_from_payload(_bash("sapb1 query Items --select \"ItemCode\""))))

    # 18b. Scrub runs at the INPUT boundary, so DERIVED fields inherit it. A
    # connection string in --db used to reach the `company` field unscrubbed;
    # the fail-closed sweep then discarded an otherwise valid pattern.
    uri_p = _extract_from_payload(_bash(
        'postsql query "SELECT 1 FROM orders" '
        '--db postgres://jivo:p4ssw0rd@10.0.0.1:5432/db'))
    check("URI record survives instead of being dropped", bool(uri_p))
    if uri_p:
        scope = uri_p[0][0]["company"]
        check("derived scope field is scrubbed",
              "p4ssw0rd" not in scope and "<redacted>" in scope, repr(scope))
        check("derived shape is clean",
              not secret_residue(render_shape(uri_p[0][0])),
              render_shape(uri_p[0][0]))
    mcp_secret = _extract_from_payload(_payload(
        "mcp__postsql__postgres_query",
        {"sql": "SELECT 1 FROM orders", "database": "postgres://u:s3cr3t@h/db"}))
    check("MCP arg values scrubbed before parsing",
          bool(mcp_secret) and "s3cr3t" not in json.dumps(mcp_secret[0][0]),
          json.dumps(mcp_secret[0][0].get("company")) if mcp_secret else "")

    # 18c. A single-element IN list is the same pattern as a multi-element one.
    in1 = _bash("postsql query \"SELECT a FROM t WHERE id IN (9)\" --db d")
    in3 = _bash("postsql query \"SELECT a FROM t WHERE id IN (1,2,3)\" --db d")
    check("single-element IN collapses with multi-element",
          shape_of(in1) == shape_of(in3), f"{shapestr(in1)} vs {shapestr(in3)}")

    # 19. End-to-end: write a realistic log, then propose + draft.
    QLOG.write_text("", encoding="utf-8")
    today = _dt.date.today()
    lines: list[str] = []

    def emit(day_offset: int, session: str, persona: str, shape_payload: dict,
             q_shape: str | None) -> None:
        got2 = _extract_from_payload(shape_payload)
        if not got2:
            return
        p2, raw2 = got2[0]
        ts = (_dt.datetime.combine(today - _dt.timedelta(days=day_offset),
                                   _dt.time(10, 0))).isoformat(timespec="seconds")
        sh = render_shape(p2)
        lines.append(json.dumps({
            "ts": ts, "persona": persona, "session": session, "tool": "Bash",
            "family": p2["tool"], "raw": scrub(raw2)[:RAW_MAX], "shape": sh,
            "shape_id": _sid(sh), "family_id": _sid(render_family(p2)),
            "q_shape_id": q_shape,
            "parsed": {k: p2[k] for k in ("tool", "verb", "entity", "filter",
                                          "filter_fields", "select", "company",
                                          "tables", "flags", "orderby")},
        }, ensure_ascii=False))

    # Standing need: same shape, 3 personas, 9 days, 3 weeks, 3 phrasings.
    for n, (off, sess, per, q) in enumerate([
        (0, "s1", "accounts", "qa1"), (1, "s2", "accounts", "qa1"),
        (3, "s3", "sales", "qa2"), (8, "s4", "accounts", "qa1"),
        (9, "s5", "accounts", "qa3"), (11, "s6", "sales", "qa2"),
        (13, "s7", "ops", "qa3"), (15, "s8", "accounts", "qa1"),
        (16, "s9", "accounts", "qa2"),
    ]):
        emit(off, sess, per, _bash(
            "sapb1 query BusinessPartners "
            f"--filter \"CardCode eq 'V{1000 + n}'\" "
            "--select \"CardName,CurrentAccountBalance\""), q)
    # Burst: 20 runs, one day, one session, one person. Must NOT be a candidate.
    for n in range(20):
        emit(2, "burst1", "accounts", _bash(
            "sapb1 query JournalEntries "
            f"--filter \"TransId eq {5000 + n}\" --select \"Memo\""), "qb1")
    QUERYLOG.write_text("\n".join(lines) + "\n", encoding="utf-8")

    QLOG.write_text("\n".join(json.dumps(r) for r in [
        {"ts": _dt.datetime.now().isoformat(timespec="seconds"),
         "persona": "accounts", "question": "what's the ledger balance for V1001",
         "shape": "x", "shape_id": "qa1"},
        {"ts": _dt.datetime.now().isoformat(timespec="seconds"),
         "persona": "sales", "question": "how much does this party owe us",
         "shape": "y", "shape_id": "qa2"},
        {"ts": _dt.datetime.now().isoformat(timespec="seconds"),
         "persona": "ops", "question": "give me the statement for that vendor",
         "shape": "z", "shape_id": "qa3"},
        {"ts": _dt.datetime.now().isoformat(timespec="seconds"),
         "persona": "accounts", "question": "check journal entry 5001",
         "shape": "w", "shape_id": "qb1"},
    ]) + "\n", encoding="utf-8")

    # 19a. cmd_record end-to-end, with stdin substituted so it is deterministic
    # and — critically — cannot block. An earlier version read stdin whenever it
    # was not a tty, so an open pipe with no data hung until the hook timeout.
    import io
    _real_stdin = sys.stdin
    QUERYLOG.unlink(missing_ok=True)
    try:
        for label, blob in (
            ("empty stdin", ""),
            ("whitespace only", "   \n"),
            ("not json", "this is not json at all"),
            ("json but not an object", "[1,2,3]"),
            ("empty object", "{}"),
            ("no tool_input", '{"tool_name":"Bash"}'),
        ):
            sys.stdin = io.StringIO(blob)
            rc_r = cmd_record(argparse.Namespace(verbose=False))
            check(f"cmd_record survives {label} (rc=0, no write)",
                  rc_r == 0 and not QUERYLOG.exists(), f"rc={rc_r}")
        sys.stdin = io.StringIO(json.dumps(_bash(
            "sapb1 query Items --filter \"ItemCode eq 'A1'\" --select \"ItemName\"")))
        rc_r = cmd_record(argparse.Namespace(verbose=False))
        wrote = QUERYLOG.exists() and QUERYLOG.read_text(encoding="utf-8").strip()
        check("cmd_record writes one record for a real payload",
              rc_r == 0 and bool(wrote) and len(str(wrote).splitlines()) == 1)
        check("that record round-trips as JSON with a shape_id",
              bool(wrote) and "shape_id" in json.loads(str(wrote)))
    finally:
        sys.stdin = _real_stdin
    QUERYLOG.unlink(missing_ok=True)

    # 19b. Nothing persisted may carry a control character, in ANY field.
    # This is the assertion that would have caught the NUL leak at the boundary
    # rather than three tests downstream of it.
    bad_fields: list[str] = []
    for raw_line in QUERYLOG.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        if re.search(r"[\x00-\x1f\x7f]", raw_line):
            bad_fields.append("raw line")
        rec_j = json.loads(raw_line)

        def _walk(node: object, path: str) -> None:
            if isinstance(node, str):
                if re.search(r"[\x00-\x1f\x7f]", node):
                    bad_fields.append(f"{path}={node!r}")
            elif isinstance(node, dict):
                for k, v in node.items():
                    _walk(v, f"{path}.{k}")
            elif isinstance(node, list):
                for n, v in enumerate(node):
                    _walk(v, f"{path}[{n}]")

        _walk(rec_j, "rec")
    check("no control chars in ANY persisted field", not bad_fields,
          "; ".join(bad_fields[:3]))

    recs = _load_queries()
    shapes = _cluster(recs, "shape_id")
    std = burst = None
    for sid, cl in shapes.items():
        if "BusinessPartners" in cl["shape"]:
            std = (sid, _metrics(cl))
        if "JournalEntries" in cl["shape"]:
            burst = (sid, _metrics(cl))
    check("standing need clustered", std is not None and std[1]["runs"] == 9,
          str(std[1] if std else None))
    check("burst clustered", burst is not None and burst[1]["runs"] == 20)
    check("burst FAILS the gate (days/sessions), despite 20 runs",
          burst is not None and bool(_gate(burst[1], MIN_RUNS, MIN_DAYS, MIN_SESSIONS)),
          ", ".join(_gate(burst[1], MIN_RUNS, MIN_DAYS, MIN_SESSIONS)) if burst else "")
    check("standing need PASSES the gate on 9 runs",
          std is not None and not _gate(std[1], MIN_RUNS, MIN_DAYS, MIN_SESSIONS))
    check("standing need out-scores the 20-run burst",
          std is not None and burst is not None and std[1]["score"] > burst[1]["score"],
          f"{std[1]['score']} vs {burst[1]['score']}" if std and burst else "")

    # 20. Minted skills are skipped.
    if std:
        sk = SKILLS / "jivo-test-skill"
        sk.mkdir(parents=True, exist_ok=True)
        (sk / "SKILL.md").write_text(
            f"---\nname: t\ndescription: d\nquery_shape_id: {std[0]}\n---\n\nbody\n",
            encoding="utf-8")
        ms, mf = _minted_ids()
        check("minted shape_id detected", std[0] in ms, str(ms))
        import shutil
        shutil.rmtree(sk, ignore_errors=True)

    # 21. draft prints to stdout and writes nothing.
    if std:
        before = {p.name for p in QUESTIONS.iterdir()}
        import io
        buf = io.StringIO()
        real_stdout = sys.stdout
        sys.stdout = buf
        try:
            rc = cmd_draft(argparse.Namespace(shape_id=std[0]))
        finally:
            sys.stdout = real_stdout
        out = buf.getvalue()
        after = {p.name for p in QUESTIONS.iterdir()}
        check("draft returns 0", rc == 0)
        check("draft emits frontmatter with query_shape_id",
              out.startswith("---\n") and f"query_shape_id: {std[0]}" in out)
        check("draft carries the DRAFT-UNVERIFIED banner",
              "DRAFT — UNVERIFIED" in out and "status: draft-unverified" in out)
        check("draft includes real question phrasings",
              "ledger balance" in out and "owe us" in out)
        check("draft marks parameters", "<CARDCODE>" in out)
        check("draft wrote no file", before == after)
        check("draft on unknown id fails loudly",
              cmd_draft(argparse.Namespace(shape_id="deadbeefdead")) == 2)

    print("query-pattern selftest")
    print(f"  temp dir: {tmp}")
    print(f"  {len(passed)} passed, {len(failed)} failed\n")
    for label in passed:
        print(f"  PASS  {label}")
    for label in failed:
        print(f"  FAIL  {label}")
    if args.keep:
        print(f"\n  kept: {tmp}")
    else:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if failed else 0


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="patterns",
        description="JIVO query-pattern capture and skill proposal "
                    "(read-only w.r.t. all business systems)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("record", help="normalise a PostToolUse payload from stdin")
    p.add_argument("--verbose", action="store_true",
                   help="echo the records written (debugging only; the hook never does)")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("propose", help="rank query shapes worth a skill")
    p.add_argument("--min-runs", type=int, default=None)
    p.add_argument("--min-days", type=int, default=None)
    p.add_argument("--min-sessions", type=int, default=None)
    p.add_argument("--top", type=int, default=8, help="rows in the runner-up lists")
    p.add_argument("--explain", action="store_true", help="show the score breakdown")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_propose)

    p = sub.add_parser("draft", help="print a draft SKILL.md for a shape id (stdout only)")
    p.add_argument("shape_id")
    p.set_defaults(func=cmd_draft)

    p = sub.add_parser("status", help="show what the query log holds")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("selftest", help="run the verification battery")
    p.add_argument("--keep", action="store_true", help="keep the temp dir")
    p.set_defaults(func=cmd_selftest)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
