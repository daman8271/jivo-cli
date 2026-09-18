#!/usr/bin/env python3
"""
build.py — one pass of the JIVO approval board.

Reads the three SAP company books for A/P drafts BHAWANI (USER03) rejected and
that are still sitting open, and writes state/board.json for the page to read.

It also writes state/history.jsonl. That file is the whole reason this runs every
minute: SAP keeps approvals as CURRENT STATE ONLY — OWDD_LOG and WDD1_LOG are
empty — so SAP itself can never say when a rejection turned up or when somebody
dealt with it. If we do not write it down as we watch, nobody can.

Read-only. hana-sql refuses anything that is not a SELECT.
"""
import argparse, csv, io, json, os, subprocess, sys, tempfile
from datetime import datetime, timezone, timedelta

IST  = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE = os.path.join(ROOT, "state")

# ---- what the board watches ------------------------------------------------
# Daman, 2026-09-18: the Accounts entry team's own documents. The login list is
# the same DESK_LOGINS already used by .claude/skills/ap-rm-pm/bin/daily_sort.py.
BOOKS = {"OIL": "JIVO_OIL_HANADB", "MART": "JIVO_MART_HANADB", "BEV": "JIVO_BEVERAGES_HANADB"}
OBJTYPES = {"18": "A/P Invoice", "19": "A/P Credit Memo", "20": "GRPO"}
LOGINS = {
    "USER07": "Harsh",
    "USER08": "Divjot",
    "USER09": "Satnam",
    "USER19": "Mahak / Priya",
    "USER39": "Muqeem",
}
LATE_AFTER_HOURS = 48          # the 2-day rule

# ---- how we reach HANA -----------------------------------------------------
# The env file's own HANA_PORT points at 47301, which is a DEAD tunnel to the old
# SAP box. The live reverse tunnel is 127.0.0.1:43015, so host/port are forced
# here and must stay forced.
HANA_BIN = os.environ.get("HANA_SQL_BIN", "/opt/jivo-mcp/bin/hana-sql")
HANA_ENV = os.environ.get("HANA_ENV_FILE", "/opt/jivo-mcp/env/hana/hana.env")
HANA_HOST = os.environ.get("HANA_HOST", "127.0.0.1")
HANA_PORT = os.environ.get("HANA_PORT", "43015")


def now_ist():
    return datetime.now(IST)


def sql_for(schema):
    with open(os.path.join(HERE, "sql", "rejected.sql"), encoding="utf-8") as fh:
        q = fh.read()
    return (q.replace("{{SCHEMA}}", schema)
             .replace("{{OBJTYPES}}", ",".join("'%s'" % t for t in OBJTYPES))
             .replace("{{LOGINS}}",   ",".join("'%s'" % u for u in LOGINS)))


def run_query(schema):
    """Return list of dicts for one book. Raises on failure — a book that fails
    must NOT silently render as zero rejections."""
    env = dict(os.environ, HANA_HOST=HANA_HOST, HANA_PORT=HANA_PORT)
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as tf:
        tf.write(sql_for(schema))
        path = tf.name
    try:
        p = subprocess.run([HANA_BIN, "-env", HANA_ENV, "-csv", "-f", path],
                           capture_output=True, text=True, timeout=120, env=env)
        if p.returncode != 0:
            raise RuntimeError("hana-sql exit %d: %s" % (p.returncode, (p.stderr or p.stdout).strip()[:300]))
        return list(csv.DictReader(io.StringIO(p.stdout)))
    finally:
        os.unlink(path)


def clean(v):
    """hana-sql writes a SQL NULL into CSV as the literal text "NULL", so an
    empty remark arrives as four characters and would render as the reason.
    Seen live on MART draft 34935."""
    v = (v or "").strip()
    return "" if v.upper() == "NULL" else v


def age_hours(rejected_at, ref):
    try:
        t = datetime.strptime(rejected_at, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=IST)
    except (ValueError, TypeError):
        return None
    return (ref - t).total_seconds() / 3600.0


def load_json(name, default):
    try:
        with open(os.path.join(STATE, name), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_atomic(name, text):
    os.makedirs(STATE, exist_ok=True)
    path = os.path.join(STATE, name)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def append_history(events):
    if not events:
        return
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, "history.jsonl"), "a", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="single pass (the cron default anyway)")
    ap.add_argument("--dry-run", action="store_true", help="print the board, write nothing")
    args = ap.parse_args()

    ref = now_ist()
    prev = load_json("board.json", {})
    prev_rows = {r["id"]: r for b in prev.get("books", {}).values() for r in b.get("rows", [])}

    # The alarm clock starts the first time this ever runs, so the board does not
    # open by shouting about entries rejected months before it existed.
    launched_at = prev.get("launched_at") or ref.isoformat()

    books, errors = {}, {}
    for book, schema in BOOKS.items():
        try:
            raw = run_query(schema)
        except Exception as exc:                       # noqa: BLE001 - reported, not swallowed
            errors[book] = str(exc)
            continue
        rows = []
        for r in raw:
            ah = age_hours(r.get("REJECTED_AT"), ref)
            rid = "%s-%s" % (book, r["DOCENTRY"])
            rows.append({
                "id": rid,
                "book": book,
                "doc_entry": int(r["DOCENTRY"]),
                "doc_num": clean(r.get("DOCNUM")),
                "doc_type": OBJTYPES.get(r.get("OBJTYPE"), r.get("OBJTYPE") or ""),
                "card_code": clean(r.get("CARDCODE")),
                "vendor": clean(r.get("VENDOR")),
                "bill_no": clean(r.get("BILLNO")),
                "amount": float(r.get("AMOUNT") or 0),
                "doc_date": clean(r.get("DOCDATE")),
                "login": r.get("CREATOR") or "",
                "who": LOGINS.get(r.get("CREATOR"), r.get("CREATOR") or ""),
                "rejected_at": r.get("REJECTED_AT") or "",
                "age_hours": round(ah, 2) if ah is not None else None,
                "reason": clean(r.get("REASON")),
                # Only entries rejected after the board went live can raise the
                # alarm. Older ones stay visible and stay silent.
                "alarmable": bool(r.get("REJECTED_AT") and r["REJECTED_AT"] >= launched_at[:19]),
            })
        rows.sort(key=lambda x: x["rejected_at"], reverse=True)
        live = [r for r in rows if r["alarmable"]]
        books[book] = {
            "rows": rows,
            "open": len(rows),
            "late": sum(1 for r in rows if (r["age_hours"] or 0) >= LATE_AFTER_HOURS),
            "late_alarmable": sum(1 for r in live if (r["age_hours"] or 0) >= LATE_AFTER_HOURS),
            "amount": round(sum(r["amount"] for r in rows), 2),
        }

    # --- the history SAP does not keep --------------------------------------
    seen_now = {r["id"]: r for b in books.values() for r in b["rows"]}
    events = []
    for rid, r in seen_now.items():
        if rid not in prev_rows:
            events.append({"event": "rejected", "at": ref.isoformat(), "id": rid,
                           "book": r["book"], "doc_entry": r["doc_entry"],
                           "vendor": r["vendor"], "bill_no": r["bill_no"],
                           "amount": r["amount"], "login": r["login"], "who": r["who"],
                           "rejected_at": r["rejected_at"], "reason": r["reason"]})
    for rid, r in prev_rows.items():
        if rid not in seen_now and r["book"] not in errors:
            events.append({"event": "cleared", "at": ref.isoformat(), "id": rid,
                           "book": r["book"], "doc_entry": r["doc_entry"],
                           "vendor": r["vendor"], "login": r["login"], "who": r["who"],
                           "rejected_at": r["rejected_at"],
                           "sat_hours": round(r.get("age_hours") or 0, 2)})

    cleared_today = 0
    try:
        today = ref.date().isoformat()
        with open(os.path.join(STATE, "history.jsonl"), encoding="utf-8") as fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("event") == "cleared" and e.get("at", "").startswith(today):
                    cleared_today += 1
    except OSError:
        pass
    cleared_today += sum(1 for e in events if e["event"] == "cleared")

    board = {
        "generated_at": ref.isoformat(),
        "launched_at": launched_at,
        "late_after_hours": LATE_AFTER_HOURS,
        "books": books,
        "errors": errors,
        "totals": {
            "open": sum(b["open"] for b in books.values()),
            "late": sum(b["late"] for b in books.values()),
            "late_alarmable": sum(b["late_alarmable"] for b in books.values()),
            "cleared_today": cleared_today,
        },
        "logins": LOGINS,
    }

    if args.dry_run:
        json.dump(board, sys.stdout, indent=2, ensure_ascii=False)
        print()
        return 0

    append_history(events)
    write_atomic("board.json", json.dumps(board, ensure_ascii=False, indent=1))

    late = board["totals"]["late_alarmable"]
    print("%s  books=%d open=%d late(alarmable)=%d new=%d cleared=%d%s" % (
        ref.strftime("%H:%M:%S"), len(books), board["totals"]["open"], late,
        sum(1 for e in events if e["event"] == "rejected"),
        sum(1 for e in events if e["event"] == "cleared"),
        ("  ERRORS: " + ",".join(errors)) if errors else ""))
    # A book that failed to read is a failure, even if the others worked: the
    # page must never show a confident zero for a book we could not reach.
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
