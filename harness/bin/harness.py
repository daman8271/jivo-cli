#!/usr/bin/env python3
"""JIVO harness — the self-learning layer for the read-only data toolkit.

This tool NEVER touches SAP or any business system. It only reads and writes
files under `harness/`. RULE 0 (read-only) is untouched by design: the only
thing that learns here is the harness itself.

Subcommands
-----------
  record    Record a correction (the AI got something wrong; here's the truth)
  build     Rebuild the bounded digest injected into every session
  ask       Append a question to the question log (called by a hook)
  mint      Find recurring question shapes and propose skills for them
  status    Show what the harness currently knows

Design notes (ported from NousResearch/hermes-agent — see harness/research/):
  * The always-injected tier is BOUNDED. Scarcity is the curation mechanism.
    Full correction records live on disk; only their one-line `## Rule` is
    injected. See research/00-existing-harness-audit.md §4.1.
  * The digest is rebuilt at commit/session time, never mid-turn, so the
    system prompt stays byte-stable and the prefix cache stays warm.
    See research/00-existing-harness-audit.md §4.2.
  * Corrections are filtered by persona, so an Accounts operator does not pay
    tokens for Sales rules.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
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



HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
CORRECTIONS = HARNESS / "corrections"
QUESTIONS = HARNESS / "questions"
# Minted skills land in the repo's Claude Code skills dir so they are live the
# moment someone clones — no install step for non-technical operators.
SKILLS = REPO / ".claude" / "skills"
PERSONAS = HARNESS / "personas"
INDEX = CORRECTIONS / "INDEX.md"
QLOG = QUESTIONS / "log.jsonl"

# Bounded injection budget, in characters. Hermes ships 2200 for its always-on
# memory tier; we allow more because ours is persona-filtered, but it is still
# a hard ceiling — past it, corrections must be consolidated, not appended.
DIGEST_CHAR_BUDGET = int(os.environ.get("JIVO_DIGEST_BUDGET", "6000"))

# How many times a question shape must recur before we propose a skill.
MINT_THRESHOLD = int(os.environ.get("JIVO_MINT_THRESHOLD", "5"))

VALID_AREAS = ["all", "accounts", "sales", "factory", "ecom", "ops", "hr"]
VALID_SEVERITY = ["high", "medium", "low"]


# ── helpers ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return _dt.date.today().isoformat()


def _slug(text: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:maxlen].strip("-") or "untitled"


def _parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter dict, body). Tolerates missing/!malformed frontmatter."""
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    meta: dict = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k.strip()] = v
    return meta, parts[2]


def _extract_rule(body: str) -> str:
    """Pull the one-line `## Rule` block — this is what gets injected."""
    m = re.search(r"^##\s+Rule\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    if not m:
        return ""
    # Strip HTML comments wholesale — they span multiple lines, so a
    # per-line startswith("<!--") filter leaks the body and closing tag.
    section = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S)
    lines = [ln.strip() for ln in section.splitlines() if ln.strip()]
    return " ".join(lines).strip()


def _load_corrections() -> list[dict]:
    """Read every correction record. Newest id last."""
    out = []
    if not CORRECTIONS.exists():
        return out
    for p in sorted(CORRECTIONS.glob("C-*.md")):
        meta, body = _parse_frontmatter(p)
        rule = _extract_rule(body)
        out.append({
            "path": p,
            "id": meta.get("id", p.stem),
            "date": meta.get("date", ""),
            "author": meta.get("author", "unknown"),
            "area": meta.get("area", "all"),
            "severity": meta.get("severity", "medium"),
            "status": meta.get("status", "active"),
            "supersedes": meta.get("supersedes", ""),
            "rule": rule,
        })
    return out


def _next_id(existing: list[dict]) -> str:
    n = 0
    for c in existing:
        m = re.match(r"C-(\d+)", str(c["id"]))
        if m:
            n = max(n, int(m.group(1)))
    return f"C-{n + 1:04d}"


def _active_persona() -> str:
    env = os.environ.get("JIVO_PERSONA", "").strip()
    if env:
        return env.lower()
    marker = HARNESS / ".persona"
    if marker.exists():
        return marker.read_text(encoding="utf-8").strip().lower() or "all"
    return "all"


# ── record ───────────────────────────────────────────────────────────────────

def cmd_record(args: argparse.Namespace) -> int:
    CORRECTIONS.mkdir(parents=True, exist_ok=True)
    existing = _load_corrections()
    cid = _next_id(existing)

    if args.area not in VALID_AREAS:
        print(f"error: --area must be one of {VALID_AREAS}", file=sys.stderr)
        return 2
    if args.severity not in VALID_SEVERITY:
        print(f"error: --severity must be one of {VALID_SEVERITY}", file=sys.stderr)
        return 2

    # Fail closed on a bad --supersedes. If the target does not exist, the old
    # rule stays active AND the new one lands, so the digest carries two
    # contradictory rules and the model picks one at random. Hermes hit the
    # same class of bug in its consolidation pass (issue #29912) and now
    # refuses any retirement that cannot name a live target.
    if args.supersedes:
        known = {str(c["id"]) for c in existing}
        if args.supersedes not in known:
            print(f"error: --supersedes {args.supersedes} does not exist.", file=sys.stderr)
            print(f"  known corrections: {', '.join(sorted(known)) or '(none)'}", file=sys.stderr)
            print("  Nothing was recorded. Fix the id and re-run.", file=sys.stderr)
            return 2

    # A high-severity correction is, by definition, one where getting it wrong
    # produces a financial number someone acts on. Those may not enter the
    # digest on somebody's say-so. Learned the hard way: a seeded test record
    # with no evidence, marked high, superseded a CORRECT rule and shipped —
    # its replacement text would have inverted a cancelled-document filter.
    if args.severity == "high" and not args.evidence.strip():
        print("error: --severity high requires --evidence.", file=sys.stderr)
        print("  A high-severity rule overrides CLAUDE.md for every operator.", file=sys.stderr)
        print("  Give the query or source that proves it, or file it as medium.", file=sys.stderr)
        return 2

    author = args.author or os.environ.get("JIVO_USER") or os.environ.get("USER") or "unknown"
    fname = f"{cid}-{_slug(args.title)}.md"
    path = CORRECTIONS / fname

    doc = f"""---
id: {cid}
date: {_now()}
author: {author}
area: {args.area}
severity: {args.severity}
status: active
supersedes: {args.supersedes or ""}
tags: [{", ".join(args.tag or [])}]
---

# {args.title}

## Wrong
{args.wrong}

## Right
{args.right}

## Evidence
{args.evidence or "_not recorded — add the query or source that proves this_"}

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
{args.rule}
"""
    path.write_text(doc, encoding="utf-8")

    # Mark the superseded record so the digest drops it.
    if args.supersedes:
        for c in existing:
            if str(c["id"]) == args.supersedes:
                txt = c["path"].read_text(encoding="utf-8")
                txt = re.sub(r"(?m)^status:.*$", "status: superseded", txt, count=1)
                c["path"].write_text(txt, encoding="utf-8")
                print(f"  superseded {c['id']} ({c['path'].name})")

    print(f"recorded {cid} -> {path.relative_to(HARNESS.parent)}")
    cmd_build(argparse.Namespace(quiet=True))

    # Send it. A correction that stays on one laptop helps nobody, and the
    # operators this is built for do not use git — telling them to run three
    # commands is the same as not sharing it at all. --no-sync exists for
    # rehearsing the command without publishing.
    if args.no_sync:
        print("\nNot sent (--no-sync). To share it later:")
        print("  python3 harness/bin/sync.py push")
        return 0

    sync = HARNESS / "bin" / "sync.py"
    if not sync.exists():
        print("\nharness/bin/sync.py is missing — this correction is saved but "
              "NOT shared. Run: git add harness/corrections && git commit && git push")
        return 0

    import subprocess
    try:
        r = subprocess.run([sys.executable, str(sync), "push"],
                           capture_output=True, text=True, timeout=90,
                           errors="replace")
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        if out:
            print("\n" + out)
        if err:
            print("\n" + err, file=sys.stderr)
        if r.returncode != 0 or err:
            print("\nThe correction is SAVED on this machine either way. "
                  "It just is not shared yet.")
    except subprocess.TimeoutExpired:
        print("\nSaved, but sharing timed out. It will go out on the next "
              "correction or session — nothing is lost.")
    return 0


# ── build ────────────────────────────────────────────────────────────────────

def cmd_build(args: argparse.Namespace) -> int:
    """Regenerate the bounded digest that gets injected into every session."""
    CORRECTIONS.mkdir(parents=True, exist_ok=True)
    corrections = [c for c in _load_corrections() if c["status"] == "active"]

    sev_rank = {"high": 0, "medium": 1, "low": 2}
    corrections.sort(key=lambda c: (sev_rank.get(c["severity"], 1), c["area"], str(c["id"])))

    by_area: dict[str, list[dict]] = {}
    for c in corrections:
        by_area.setdefault(c["area"], []).append(c)

    lines = [
        "# JIVO corrections — active rule digest",
        "",
        "<!-- GENERATED by harness/bin/harness.py build. Do not hand-edit;",
        "     edit the underlying C-*.md record and rebuild. -->",
        "",
        "These are corrections real JIVO operators made to the AI. They override",
        "any default assumption. If one contradicts your instinct, the correction wins.",
        "",
    ]
    dropped: list[dict] = []
    used = len("\n".join(lines))

    for area in sorted(by_area, key=lambda a: (a != "all", a)):
        header = f"\n## {area}\n"
        block: list[str] = []
        for c in by_area[area]:
            if not c["rule"]:
                continue
            entry = f"- **[{c['id']}]** {c['rule']}"
            if used + len(entry) + len(header) > DIGEST_CHAR_BUDGET:
                dropped.append(c)
                continue
            block.append(entry)
            used += len(entry) + 1
        if block:
            lines.append(header.strip())
            lines.extend(block)
            used += len(header)

    if dropped:
        lines.append("")
        lines.append(
            f"<!-- {len(dropped)} correction(s) omitted: digest hit the "
            f"{DIGEST_CHAR_BUDGET}-char budget. Consolidate overlapping rules "
            f"or raise JIVO_DIGEST_BUDGET. Omitted: "
            f"{', '.join(str(c['id']) for c in dropped)} -->"
        )

    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if not getattr(args, "quiet", False):
        print(f"built {INDEX.relative_to(HARNESS.parent)}")
        print(f"  {len(corrections)} active correction(s), {used}/{DIGEST_CHAR_BUDGET} chars")
        if dropped:
            print(f"  WARNING: {len(dropped)} dropped for budget — consolidate them")
    if dropped:
        return 1
    return 0


# ── ask (question logging) ───────────────────────────────────────────────────

_RE_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_RE_PERIOD = re.compile(
    r"\b(q[1-4]|fy\s?\d{2,4}|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may"
    r"|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?"
    r"|dec(?:ember)?)\b", re.I)
_RE_CODE = re.compile(r"\b[A-Z]{1,4}\d{4,}\b")
_RE_NUM = re.compile(r"\b\d[\d,._]*\b")
_RE_WS = re.compile(r"\s+")

# Runs of Capitalized Words — how we spot party/vendor/customer names without
# needing a lookup against SAP.
_RE_CAP_RUN = re.compile(r"[A-Z][\w&.'-]*(?:\s+[A-Z][\w&.'-]*)*")

# Capitalised tokens that are domain vocabulary, NOT party names. These must
# survive normalisation or distinct question types would collapse together.
_DOMAIN_TERMS = {
    "SAP", "JIVO", "HANA", "GST", "ITC", "TDS", "HSN", "SKU", "UOM", "MRP",
    "PO", "SO", "GRN", "AR", "AP", "B1", "INR", "DSR", "OMS", "MOC", "QTY",
    "YTD", "MTD", "FY", "OIL", "MART", "BEVERAGES", "CLI", "ID", "OK",
}


# Words that introduce a party/entity in the way operators actually phrase these
# questions: "balance for Sharma Traders", "statement of Gupta Oils".
_RE_ENTITY_LEAD = re.compile(r"\b(for|of|to|from|with|against|by)\s+$", re.I)


def _genericise_names(text: str) -> str:
    """Replace proper-noun runs with <name>, so 'Sharma Traders' and
    'Gupta Oils' reduce to the same question shape.

    Deliberately conservative. An earlier version genericised any capitalised
    word not at position 0, which turned "Pretty long I think" into
    "<name> long <name> think" — ordinary words masked as party names, which
    silently destroys the clustering this exists to produce. A single
    capitalised word is only a name if something introduces it as one.
    """
    def repl(m: re.Match) -> str:
        run = m.group(0)
        tokens = run.split()
        # Domain vocabulary is never a party name.
        if all(t.upper().strip(".',&-") in _DOMAIN_TERMS for t in tokens):
            return run
        # Two or more consecutive capitalised words is a strong proper-noun
        # signal on its own ("Sharma Traders", "Blessing Advertising").
        if len(tokens) >= 2:
            return "<name>"
        # A lone capitalised word needs evidence. Sentence-initial words and
        # stray capitals ("Pretty", "I", "Tell") are not names; a word
        # following for/of/to/from usually is.
        return "<name>" if _RE_ENTITY_LEAD.search(text[:m.start()]) else run
    return _RE_CAP_RUN.sub(repl, text)


def _shape(question: str) -> str:
    """Reduce a question to its reusable shape, so repeats cluster together.

    Order matters: periods and dates are resolved while case is still intact,
    so 'July' becomes <period> rather than being mistaken for a party name.
    """
    s = question.strip()
    s = _RE_DATE.sub("<date>", s)
    s = _RE_PERIOD.sub("<period>", s)
    s = _RE_CODE.sub("<code>", s)
    s = _genericise_names(s)
    s = s.lower()
    s = _RE_NUM.sub("<num>", s)
    return _RE_WS.sub(" ", s).strip()


def cmd_ask(args: argparse.Namespace) -> int:
    q = (args.question or "").strip()
    # Called from a Claude Code UserPromptSubmit hook: the prompt arrives as
    # JSON on stdin rather than as an argument.
    if not q and not sys.stdin.isatty():
        try:
            payload = json.loads(sys.stdin.read() or "{}")
            q = str(payload.get("prompt", "")).strip()
        except (json.JSONDecodeError, ValueError):
            return 0
    if not q or len(q) < 8:
        return 0
    # Never log slash-commands or pasted file blobs — they are not questions.
    if q.startswith("/") or len(q) > 2000:
        return 0
    # Nor machine-generated turns. Background-task notifications, system
    # reminders and tool payloads arrive through the same hook as a human
    # question. They pollute the shape clusters, and — because this log is
    # committed to a shared repo — they leak session ids and absolute local
    # paths to every colleague. Prose from a person never starts with a tag.
    if q.lstrip()[:1] in "<{[":
        return 0
    if any(marker in q for marker in (
            "<task-notification>", "<system-reminder>", "<tool-use-id>",
            "<output-file>", "<command-name>", "SYSTEM NOTIFICATION")):
        return 0
    QUESTIONS.mkdir(parents=True, exist_ok=True)
    shape = _shape(q)
    rec = {
        "ts": _dt.datetime.now().isoformat(timespec="seconds"),
        "persona": _active_persona(),
        "question": q[:500],
        "shape": shape[:500],
        "shape_id": hashlib.sha1(shape.encode("utf-8")).hexdigest()[:12],
    }
    with QLOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return 0


# ── mint ─────────────────────────────────────────────────────────────────────

def _load_questions() -> list[dict]:
    if not QLOG.exists():
        return []
    out = []
    for line in QLOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _minted_shape_ids() -> set[str]:
    ids: set[str] = set()
    if not SKILLS.exists():
        return ids
    for p in SKILLS.rglob("SKILL.md"):
        meta, _ = _parse_frontmatter(p)
        sid = meta.get("shape_id")
        if sid:
            ids.add(str(sid))
    return ids


def cmd_mint(args: argparse.Namespace) -> int:
    """Cluster the question log and report shapes that deserve a skill."""
    questions = _load_questions()
    if not questions:
        print("question log is empty — nothing to mint yet.")
        print(f"  (expected at {QLOG.relative_to(HARNESS.parent)})")
        return 0

    clusters: dict[str, dict] = {}
    for q in questions:
        sid = q.get("shape_id") or hashlib.sha1(
            _shape(q.get("question", "")).encode()).hexdigest()[:12]
        c = clusters.setdefault(sid, {"count": 0, "examples": [], "personas": set()})
        c["count"] += 1
        c["personas"].add(q.get("persona", "all"))
        if len(c["examples"]) < 5:
            c["examples"].append(q.get("question", ""))

    already = _minted_shape_ids()
    ranked = sorted(clusters.items(), key=lambda kv: -kv[1]["count"])
    threshold = args.threshold or MINT_THRESHOLD

    candidates = [
        (sid, c) for sid, c in ranked
        if c["count"] >= threshold and sid not in already
    ]

    print(f"{len(questions)} question(s) logged, {len(clusters)} distinct shape(s)")
    print(f"threshold: {threshold} repeats\n")

    if not candidates:
        print("No shape has recurred enough to justify a skill yet.")
        top = ranked[:5]
        if top:
            print("\nClosest shapes so far:")
            for sid, c in top:
                mark = " (already minted)" if sid in already else ""
                print(f"  {c['count']:>3}x  {sid}{mark}  {c['examples'][0][:70]}")
        return 0

    print(f"{len(candidates)} shape(s) ready to become skills:\n")
    for sid, c in candidates:
        personas = ",".join(sorted(c["personas"]))
        print(f"  {c['count']:>3}x  shape_id={sid}  persona={personas}")
        for ex in c["examples"][:3]:
            print(f"          e.g. {ex[:80]}")
        print()

    print("These are CANDIDATES, not skills. To mint one, ask Claude:")
    print('  "mint a skill for shape <shape_id>"')
    print("It will read the real examples, write the SKILL.md, and verify the")
    print("queries against live SAP before saving.")
    return 0


# ── review (post-turn learning check) ────────────────────────────────────────
#
# Ported from Hermes' post-turn background review (agent/turn_finalizer.py:634-658,
# see research/01-hermes-learning.md §2a). Hermes forks a whole agent after each
# Nth turn to ask "did anything here deserve to be remembered?".
#
# We do NOT fork a model: office operators share one subscription, and an extra
# inference call every N turns across a dozen people is real money for a check
# that is usually a no-op. Instead the counter raises a flag, and the flag is
# surfaced to the agent already in the room — same trigger, no extra spend.
#
# The anti-thrash rule is Hermes' and is the important part: a session that is
# already recording corrections never gets nagged on top of it.

STATE = HARNESS / ".state"
REVIEW_INTERVAL = int(os.environ.get("JIVO_REVIEW_INTERVAL", "10"))


def _state_read(name: str, default: str = "") -> str:
    p = STATE / name
    try:
        return p.read_text(encoding="utf-8").strip()
    except (OSError, ValueError):
        return default


def _state_write(name: str, value: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / name).write_text(str(value), encoding="utf-8")


def _latest_correction_mtime() -> float:
    if not CORRECTIONS.exists():
        return 0.0
    times = [p.stat().st_mtime for p in CORRECTIONS.glob("C-*.md")]
    return max(times) if times else 0.0


def cmd_review(args: argparse.Namespace) -> int:
    """Count a completed turn; raise the review flag every Nth turn.

    Called from the Stop hook. Always exits 0 and stays silent unless the
    flag fires.
    """
    STATE.mkdir(parents=True, exist_ok=True)

    # Anti-thrash (Hermes agent/tool_executor.py:476-479): if a correction was
    # recorded since we last looked, this session is already learning. Reset
    # and say nothing.
    seeded = (STATE / "last_correction_mtime").exists()
    last_seen = float(_state_read("last_correction_mtime", "0") or 0)
    now_mtime = _latest_correction_mtime()
    if now_mtime > last_seen:
        _state_write("last_correction_mtime", str(now_mtime))
        # On a fresh clone there is no baseline yet; seeding it is bookkeeping,
        # not evidence that this session recorded anything. Only a genuinely
        # new correction resets the counter.
        if seeded:
            _state_write("turns", "0")
            _state_write("review_due", "0")
            return 0

    turns = int(_state_read("turns", "0") or 0) + 1
    interval = args.interval or REVIEW_INTERVAL

    if turns >= interval:
        _state_write("turns", "0")
        _state_write("review_due", "1")
    else:
        _state_write("turns", str(turns))
    return 0


def _review_prompt() -> str:
    return (
        "## Harness check\n\n"
        f"{REVIEW_INTERVAL} turns have passed without a correction being recorded.\n"
        "Before continuing, consider silently: in the recent work, did the operator\n"
        "correct you about how JIVO's data actually works — a metric definition, a\n"
        "field meaning, a relationship, a trap? If yes, use the `jivo-correct` skill\n"
        "to record it so every other operator benefits. If nothing qualifies — which\n"
        "is the common case — say nothing and carry on."
    )


# ── context (SessionStart injection) ─────────────────────────────────────────

def cmd_context(args: argparse.Namespace) -> int:
    """Emit the persona-filtered block injected at the start of every session.

    Deliberately quiet: if the harness is empty or broken this prints nothing
    rather than polluting every operator's session with an error.
    """
    persona = _active_persona()
    corrections = [c for c in _load_corrections() if c["status"] == "active"]

    # An operator tagged `accounts` pays tokens for accounts + universal rules
    # only. `all` sees everything.
    if persona not in ("all", "", "unknown"):
        corrections = [c for c in corrections if c["area"] in ("all", persona)]

    profile = PERSONAS / f"{persona}.md"
    out: list[str] = []

    if profile.exists():
        body = profile.read_text(encoding="utf-8").strip()
        if body:
            out.append(f"## Your operator profile: {persona}\n\n{body}")

    if corrections:
        sev_rank = {"high": 0, "medium": 1, "low": 2}
        corrections.sort(key=lambda c: (sev_rank.get(c["severity"], 1), str(c["id"])))
        rules = []
        used = 0
        for c in corrections:
            if not c["rule"]:
                continue
            entry = f"- **[{c['id']}]** {c['rule']}"
            if used + len(entry) > DIGEST_CHAR_BUDGET:
                break
            rules.append(entry)
            used += len(entry)
        if rules:
            out.append(
                "## JIVO corrections — these override your defaults\n\n"
                "Real JIVO operators corrected the AI on each of these. They are\n"
                "settled fact for this business. If one contradicts your instinct,\n"
                "the correction wins. Full record: `harness/corrections/<id>-*.md`.\n\n"
                + "\n".join(rules)
            )

    # A review fell due since last session — surface it now, in the session
    # that is already running, rather than paying for a separate model call.
    if _state_read("review_due", "0") == "1":
        out.append(_review_prompt())
        _state_write("review_due", "0")

    if out:
        print("\n\n".join(out))
    return 0


# ── status ───────────────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> int:
    corrections = _load_corrections()
    active = [c for c in corrections if c["status"] == "active"]
    questions = _load_questions()
    skills = sorted(SKILLS.rglob("SKILL.md")) if SKILLS.exists() else []
    personas = sorted(PERSONAS.glob("*.md")) if PERSONAS.exists() else []

    print("JIVO harness status")
    print(f"  persona (this machine) : {_active_persona()}")
    print(f"  corrections            : {len(active)} active / {len(corrections)} total")
    print(f"  digest                 : {'built' if INDEX.exists() else 'MISSING — run build'}")
    if INDEX.exists():
        size = len(INDEX.read_text(encoding='utf-8'))
        print(f"                           {size}/{DIGEST_CHAR_BUDGET} chars")
    print(f"  skills                 : {len(skills)}")
    print(f"  personas defined       : {len(personas)} ({', '.join(p.stem for p in personas)})")
    print(f"  questions logged       : {len(questions)}")

    if active:
        print("\n  most recent corrections:")
        for c in active[-5:]:
            print(f"    {c['id']} [{c['area']}/{c['severity']}] {c['rule'][:60]}")

    # The sibling modules own their own state; ask them rather than parsing it
    # here, so their storage can change without breaking this view.
    for label, mod, sub in (("recall", "recall.py", "stats"),
                            ("patterns", "patterns.py", "status")):
        path = HARNESS / "bin" / mod
        if not path.exists():
            continue
        print(f"\n  --- {label} ---")
        try:
            import subprocess
            r = subprocess.run([sys.executable, str(path), sub],
                               capture_output=True, text=True, timeout=30)
            body = (r.stdout or r.stderr).strip().splitlines()
            for line in body[1:9] if len(body) > 1 else body:
                print(f"  {line}")
        except Exception as exc:
            print(f"    unavailable: {exc}")
    return 0


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="harness",
        description="JIVO self-learning harness (read-only w.r.t. all business systems)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("record", help="record a correction")
    p.add_argument("--title", required=True)
    p.add_argument("--wrong", required=True, help="what the AI said/did that was wrong")
    p.add_argument("--right", required=True, help="what is actually true")
    p.add_argument("--rule", required=True, help="ONE imperative line to inject everywhere")
    p.add_argument("--evidence", default="", help="the query/source that proves it")
    p.add_argument("--area", default="all", choices=VALID_AREAS)
    p.add_argument("--severity", default="medium", choices=VALID_SEVERITY)
    p.add_argument("--supersedes", default="", help="id of a correction this replaces")
    p.add_argument("--tag", action="append", default=[])
    p.add_argument("--author", default="")
    p.add_argument("--no-sync", action="store_true",
                   help="record but do not share it yet")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("build", help="rebuild the injected digest")
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("ask", help="log a question (called by hook)")
    p.add_argument("question", nargs="?", default="")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("mint", help="find recurring shapes worth a skill")
    p.add_argument("--threshold", type=int, default=0)
    p.set_defaults(func=cmd_mint)

    p = sub.add_parser("context", help="emit the SessionStart injection block")
    p.set_defaults(func=cmd_context)

    p = sub.add_parser("review", help="count a turn; flag a learning check (Stop hook)")
    p.add_argument("--interval", type=int, default=0)
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("status", help="show what the harness knows")
    p.set_defaults(func=cmd_status)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
