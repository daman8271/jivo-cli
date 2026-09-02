#!/usr/bin/env python3
"""build.py — refresh engine for the JIVO Transporter-wise Details board.

Runs every .sql in pipeline/sql/ against all three SAP company books through
the read-only hana-sql CLI and writes one JSON file per (section, company) into
site/data/, plus a manifest.json describing what was produced.

Each .sql is written ONCE with a placeholder and executed three times:
    {{SCHEMA}}  ->  JIVO_OIL_HANADB | JIVO_MART_HANADB | JIVO_BEVERAGES_HANADB
    {{ASOF}}    ->  the as-of date, YYYY-MM-DD (optional; none of the current
                    templates use it, substituted anyway so a future one can)

Read-only by construction: hana-sql refuses anything but SELECT/WITH, runs in a
HANA read-only transaction, and never commits. This script issues no write of
any kind to SAP. It honours CLAUDE.md RULE 0 and FACTS.md §8.1.

Modelled on accounts-dashboard/pipeline/build_data.py (same hana invocation,
same TSV discipline) with three deliberate differences:
  * SQL goes to hana-sql on STDIN, not argv. Every template here starts with a
    comment block and the Go flag parser eats a leading "--" as a flag. stdin
    and -f were verified byte-identical by the SQL authors on 2026-08-22.
  * One file per (section, company), not one monolithic data.json, so the page
    can load a single book lazily and the three books are never in one object
    (FACTS §8.7: never sum Oil + Mart + Bev).
  * Typing is decided per COLUMN, not per cell. An empty cell in a numeric
    column becomes null, never 0 — that is the "never a confident zero" rule.
    An empty cell in a text column stays '' because the SQL contracts use ''
    to mean "present, blank" (PAY_NUMS, SETTLED_BY, TRSFR_REF) and reserve the
    literal token NULL for SQL NULL.

Outputs (site/data/):
    <section>.<co>.json   {"section","company","as_of","rows":[...],"error":null,...}
    manifest.json         generated_at, as_of, per-section per-company row
                          counts and seconds, every error string, ok flag

Failure policy (safe under cron):
  * A query that fails, times out, or returns ZERO rows does not clobber the
    previous good file for that (section, company). The manifest records the
    error and marks the entry stale_since the previous build. If there is no
    previous file, a file with rows:[] and error:"<reason>" is written so the
    page renders "not computed: <reason>" instead of 404.
  * The other companies and sections are still built and written.
  * Exit codes: 0 all clean · 1 at least one query failed (files for the rest
    were written) · 2 no route to HANA at all · 3 another build holds the lock.

Deterministic: same data -> byte-identical row files (only generated_at and
the timings in the manifest move). stdlib only.

Usage:
    python3 build.py                        # today, all sections, all companies
    python3 build.py --as-of 2026-07-31
    python3 build.py --only invoices,payments
    python3 build.py --company oil
Environment overrides (for the VPS / another box):
    HANA_SQL_BIN, HANA_ENV_FILE, HANA_BRIDGE_CMD, HANA_SQL_TIMEOUT (seconds),
    RAW_TSV_DIR (if set, the raw TSV of every query is also saved there).
"""
import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import date, datetime

# ---------------------------------------------------------------- locations

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PIPELINE_DIR)                 # transporter-dashboard/
REPO = os.path.dirname(ROOT)                         # jivo-cli/
SQL_DIR = os.path.join(PIPELINE_DIR, "sql")
SITE_DIR = os.path.join(ROOT, "site")
DATA_DIR = os.path.join(SITE_DIR, "data")
MANIFEST_PATH = os.path.join(DATA_DIR, "manifest.json")

HANA_SQL = os.environ.get("HANA_SQL_BIN", os.path.join(REPO, "hana-sql", "hana-sql"))
HANA_DIR = os.path.dirname(HANA_SQL)
# FACTS.md names this env file as THE connection. It is the default on purpose;
# the direct office route is not probed because off-office it hangs rather than
# refusing, and the cron tick should not burn that fuse every run.
TUNNEL_ENV = os.environ.get("HANA_ENV_FILE", os.path.join(REPO, "connections", "hana-tunnel.env"))
# Re-raises the home bridge (VPS-parked hanadb ports) when the local port is dead.
BRIDGE_CMD = shlex.split(os.environ.get(
    "HANA_BRIDGE_CMD", "bash " + os.path.join(REPO, "connections", "sap-home-bridge.sh")))
# Per-statement ceiling. The refresh must not sit on production HANA.
SQL_TIMEOUT = int(os.environ.get("HANA_SQL_TIMEOUT", "300"))
# Optional raw-TSV dump for debugging. Off unless pointed somewhere explicitly,
# so the build never creates files outside site/data/.
RAW_TSV_DIR = os.environ.get("RAW_TSV_DIR", "")

COMPANIES = [
    ("oil",  "JIVO Wellness (Oil)", "JIVO_OIL_HANADB"),
    ("mart", "JIVO Mart",           "JIVO_MART_HANADB"),
    ("bev",  "JIVO Beverages",      "JIVO_BEVERAGES_HANADB"),
]
COMPANY_KEYS = [k for k, _, _ in COMPANIES]

# Files are named transporter-<section>.sql; the section id is what is left
# after the prefix. A file without the prefix still runs under its own stem.
SECTION_PREFIX = "transporter-"

# The literal token hana-sql prints for SQL NULL (verified live 2026-08-22:
# `SELECT NULL FROM DUMMY` -> the four characters N U L L). Nothing else is a
# null: '' is a real empty string and is kept as such in text columns.
NULL_TOKEN = "NULL"

# Columns that are identifiers / codes / labels and must stay TEXT even when
# every value happens to look like a number. Matched case-insensitively on the
# column name, anchored to the END of the name (or the whole name). float()
# would round a long DocNum, strip a leading zero from a vendor bill number,
# and turn INV_TYPE '18' into 18 — all of which break lookups the renderer
# does with ===. Date columns are NOT listed: 'YYYY-MM-DD' never parses as a
# number, and a suffix like _date would wrongly catch the money column
# PAID_TO_DATE (it did, on the first run).
TEXT_COLUMN_RE = re.compile(
    r"(_code|_num|_nums|_no|_entry|_id|_ref|_key|_type|_flag|_status|_bill|"
    r"_by|_label|_name|_window)$|^(remarks|branch|comments)$",
    re.I)


# -------------------------------------------------------------- hana access

def _run_hana(sql, timeout=SQL_TIMEOUT):
    """Run one SQL statement through the read-only hana-sql CLI; return stdout.

    The statement is passed on stdin. Every template starts with a '--' comment
    block and hana-sql's flag parser would read that as a flag if it came in
    argv. The binary's guard lexes comments out before it checks the verb.
    """
    p = subprocess.run([HANA_SQL, "-env", TUNNEL_ENV], input=sql,
                       cwd=HANA_DIR, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "hana-sql exited %d" % p.returncode)
    return p.stdout


def _route_label():
    """Describe the route actually in use, read from the env file, not assumed."""
    host, port = "?", "?"
    try:
        with open(TUNNEL_ENV) as f:
            for ln in f:
                if ln.startswith("HANA_HOST="):
                    host = ln.split("=", 1)[1].strip()
                elif ln.startswith("HANA_PORT="):
                    port = ln.split("=", 1)[1].strip()
    except Exception:
        return os.path.basename(TUNNEL_ENV)
    return "%s:%s (%s)" % (host, port, os.path.basename(TUNNEL_ENV))


def _is_conn_error(msg):
    """Does this hana-sql failure mean the tunnel died, rather than bad SQL?"""
    m = msg.lower()
    return ("connection refused" in m or "conn read error" in m or "eof" in m
            or "could not connect" in m or "broken pipe" in m
            or "connection reset" in m or "no route to host" in m
            or "i/o timeout" in m)


def connect():
    """Probe the FACTS.md route; if it is dead, re-raise the bridge once.

    Returns the route label. Exits 2 when nothing answers — there is no point
    running twelve queries against a dead tunnel.
    """
    probe = 'SELECT 1 AS "OK" FROM DUMMY'
    if not os.path.isfile(HANA_SQL) or not os.access(HANA_SQL, os.X_OK):
        sys.exit("FATAL: hana-sql binary not found or not executable at %s" % HANA_SQL)
    if not os.path.isfile(TUNNEL_ENV):
        sys.exit("FATAL: HANA env file not found at %s" % TUNNEL_ENV)
    try:
        _run_hana(probe, timeout=30)
        label = _route_label()
        print("connection: %s" % label)
        return label
    except Exception as e:
        print("route %s dead (%s); re-raising the bridge..."
              % (_route_label(), str(e).splitlines()[0][:120] if str(e) else type(e).__name__))
    try:
        subprocess.run(BRIDGE_CMD, capture_output=True, text=True, timeout=90)
        time.sleep(2)
        _run_hana(probe, timeout=30)
        label = _route_label() + " [bridge re-raised]"
        print("connection: %s" % label)
        return label
    except Exception as e:
        print("FATAL: no route to SAP HANA via %s, and re-raising the bridge failed "
              "too (%s).\n  Try:  bash %s"
              % (_route_label(), e, os.path.join(REPO, "connections", "sap-home-bridge.sh")),
              file=sys.stderr)
        sys.exit(2)


# ------------------------------------------------------------------ parsing

def read_sql(path):
    """Read a template verbatim. Comments and a trailing ';' are accepted on
    stdin, so nothing is stripped — what runs is exactly what is on disk."""
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def parse_tsv(out):
    """TSV -> (header, list of row lists, malformed count).

    A row whose field count disagrees with the header is dropped and COUNTED,
    never silently reshaped. The count is surfaced as an error because a
    dropped allocation line is exactly how the totals stop tying.
    """
    lines = out.splitlines()
    if not lines:
        return [], [], 0
    hdr = lines[0].split("\t")
    rows, bad = [], 0
    for ln in lines[1:]:
        if ln == "":
            continue
        parts = ln.split("\t")
        if len(parts) != len(hdr):
            bad += 1
            continue
        rows.append(parts)
    return hdr, rows, bad


_NUM_RE = re.compile(r"^-?(\d+)(\.\d+)?$")


def _as_number(s):
    """'12037.50' -> 12037.5 ; '3' -> 3 ; '-1.00' -> -1.0. None if not numeric.
    Integers beyond 2**53 are left alone (they would not survive JSON/JS)."""
    m = _NUM_RE.match(s)
    if not m:
        return None
    if m.group(2) is None:
        v = int(s)
        return v if abs(v) < 2 ** 53 else None
    return float(s)


def coerce(hdr, rows):
    """Decide each column's type ONCE, from its name and all its values, then
    convert every cell accordingly.

      text column    : NULL token -> None ; '' stays '' ; everything else str
      numeric column : NULL token -> None ; ''  -> None ; else int/float
      unknown column : NULL token -> None ; ''  -> None   (every cell blank)

    A column is TEXT when its name is identifier-like (TEXT_COLUMN_RE) or at
    least one non-blank value fails to parse as a number. It is NUMERIC when
    every non-blank value parses. A column with no non-blank value at all
    gives no evidence either way, so its blanks are emitted as null: nothing
    proves it is text, and a '' reaching the page as a value is the confident
    zero the contract forbids (Number('') is 0 in JS).

    hana-sql prints a numeric NULL as the NULL token, never as '', so in
    practice '' only ever comes from a text expression (COALESCE(x, '')); the
    ''-in-a-numeric-column rule is defensive. Returns (rows, numeric flags).
    """
    ncol = len(hdr)
    numeric, blank_is_null = [], []
    for c in range(ncol):
        name = hdr[c]
        if TEXT_COLUMN_RE.search(name):
            numeric.append(False)
            blank_is_null.append(False)
            continue
        seen, ok = False, True
        for r in rows:
            v = r[c]
            if v == "" or v == NULL_TOKEN:
                continue
            seen = True
            if _as_number(v) is None:
                ok = False
                break
        numeric.append(ok and seen)
        blank_is_null.append(ok)          # numeric, or no evidence at all

    out = []
    for r in rows:
        o = {}
        for c in range(ncol):
            v = r[c]
            if v == NULL_TOKEN:
                o[hdr[c]] = None
            elif v == "":
                o[hdr[c]] = None if blank_is_null[c] else ""
            elif numeric[c]:
                o[hdr[c]] = _as_number(v)
            else:
                o[hdr[c]] = v
        out.append(o)
    return out, numeric


# -------------------------------------------------------------------- files

def section_files():
    """Every .sql in sql/ as (section_id, path), sorted by section id."""
    if not os.path.isdir(SQL_DIR):
        sys.exit("FATAL: no sql/ directory at %s" % SQL_DIR)
    out = []
    for fn in sorted(os.listdir(SQL_DIR)):
        if not fn.endswith(".sql"):
            continue
        stem = fn[:-4]
        sid = stem[len(SECTION_PREFIX):] if stem.startswith(SECTION_PREFIX) else stem
        out.append((sid, os.path.join(SQL_DIR, fn)))
    return sorted(out)


def data_path(sid, co):
    return os.path.join(DATA_DIR, "%s.%s.json" % (sid, co))


def write_json(path, obj):
    """Atomic: write a sibling .tmp then rename over the target, so a reader
    (or a deploy) never sees a half-written file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def rows_sha(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


# -------------------------------------------------------------------- build

def run_one(sid, path, template, co, label, schema, asof, generated_at):
    """Run one (section, company). Returns (payload-or-None, manifest entry).

    payload is None when the previous good file must be kept (failure with a
    prior file on disk). The manifest entry always says what happened.
    """
    sql = template.replace("{{SCHEMA}}", schema).replace("{{ASOF}}", asof)
    entry = {"file": os.path.basename(data_path(sid, co)), "rows": None,
             "seconds": None, "error": None}
    t0 = time.time()
    out, err = None, None
    try:
        out = _run_hana(sql)
    except subprocess.TimeoutExpired:
        err = "timed out after %ds" % SQL_TIMEOUT
    except Exception as e:
        err = (str(e).splitlines()[0] if str(e) else type(e).__name__)[:300]
        # A dropped tunnel poisons every remaining query. Re-raise it once and
        # retry this statement before giving up on it.
        if _is_conn_error(err):
            print("    %-12s %-5s connection lost, reconnecting..." % (sid, co))
            try:
                connect()
                out, err = _run_hana(sql), None
            except SystemExit:
                err = "connection lost and could not be re-raised"
            except subprocess.TimeoutExpired:
                err = "timed out after %ds (after reconnect)" % SQL_TIMEOUT
            except Exception as e2:
                err = (str(e2).splitlines()[0] if str(e2) else type(e2).__name__)[:300]
    entry["seconds"] = round(time.time() - t0, 1)

    if err is None:
        if RAW_TSV_DIR:
            os.makedirs(RAW_TSV_DIR, exist_ok=True)
            with open(os.path.join(RAW_TSV_DIR, "%s.%s.tsv" % (sid, co)), "w", encoding="utf-8") as f:
                f.write(out)
        hdr, raw_rows, bad = parse_tsv(out)
        if not hdr:
            err = "hana-sql returned no output at all (not even a header)"
        elif bad:
            err = ("%d of %d row(s) had a field count different from the header "
                   "and were dropped — totals would not tie; not published" % (bad, bad + len(raw_rows)))
        elif not raw_rows:
            # FACTS §1: every book has transporter activity in the window. Zero
            # rows here is a broken substitution or a wrong schema, not a fact,
            # and publishing it would be the confident zero the contract forbids.
            err = "query returned zero rows — refusing to publish a confident zero"

    if err is not None:
        entry["error"] = err
        print("    %-12s %-5s FAILED  %5.1fs  %s" % (sid, co, entry["seconds"], err))
        prev = load_json(data_path(sid, co))
        if prev and prev.get("rows"):
            entry["rows"] = len(prev["rows"])
            entry["stale_since"] = prev.get("generated_at") or prev.get("as_of")
            entry["kept_previous"] = True
            print("    %-12s %-5s keeping previous file (%d rows, built %s)"
                  % (sid, co, entry["rows"], entry["stale_since"]))
            return None, entry
        entry["rows"] = 0
        payload = {
            "section": sid, "company": co, "company_label": label, "schema": schema,
            "as_of": asof, "generated_at": generated_at,
            "sql_file": os.path.basename(path), "columns": [], "rows": [],
            "row_count": 0, "error": err,
        }
        return payload, entry

    rows, numeric = coerce(hdr, raw_rows)
    entry["rows"] = len(rows)
    entry["sha256"] = rows_sha(rows)
    print("    %-12s %-5s %6d rows  %5.1fs" % (sid, co, len(rows), entry["seconds"]))
    payload = {
        "section": sid, "company": co, "company_label": label, "schema": schema,
        "as_of": asof, "generated_at": generated_at,
        "sql_file": os.path.basename(path),
        "columns": hdr,
        "numeric_columns": [h for h, n in zip(hdr, numeric) if n],
        "rows": rows, "row_count": len(rows),
        "error": None,
    }
    return payload, entry


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Refresh the JIVO Transporter board data.")
    ap.add_argument("--as-of", default=date.today().isoformat(),
                    help="position date, YYYY-MM-DD (default: today)")
    ap.add_argument("--only", default="",
                    help="comma-separated section ids (master,invoices,payments,allocations)")
    ap.add_argument("--company", default="", help="comma-separated: oil,mart,bev")
    args = ap.parse_args()

    # Under cron (or `| tee`) stdout is a pipe and Python block-buffers it, so
    # the whole log lands at exit. Line-buffer it: a hung query then shows
    # exactly which statement it hung on.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    try:
        datetime.strptime(args.as_of, "%Y-%m-%d")
    except ValueError:
        sys.exit("FATAL: --as-of must be YYYY-MM-DD, got %r" % args.as_of)
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    only_companies = {s.strip() for s in args.company.split(",") if s.strip()}
    for c in only_companies:
        if c not in COMPANY_KEYS:
            sys.exit("FATAL: unknown company %r (expected oil, mart or bev)" % c)

    # One build at a time. flock on this very file: no lock file to create,
    # works on macOS and Linux, released by the OS if the process dies.
    lock_fh = open(os.path.abspath(__file__), "rb")
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another build is already running (lock held on %s); exiting" % __file__)
        sys.exit(3)

    files = [(sid, p) for sid, p in section_files() if not only or sid in only]
    if not files:
        sys.exit("FATAL: no sections to run (sql/ empty, or --only matched nothing)")
    companies = [c for c in COMPANIES if not only_companies or c[0] in only_companies]

    route = connect()
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print("as-of %s — %d section(s) x %d compan%s: %s"
          % (args.as_of, len(files), len(companies), "y" if len(companies) == 1 else "ies",
             ", ".join(sid for sid, _ in files)))

    t0 = time.time()
    prev_manifest = load_json(MANIFEST_PATH) or {}
    sections = dict(prev_manifest.get("sections", {})) if (only or only_companies) else {}
    errors = []
    for sid, path in files:
        print("  %s  (%s)" % (sid, os.path.basename(path)))
        template = read_sql(path)
        if "{{SCHEMA}}" not in template:
            # A template with no placeholder would run the same book three
            # times and label two of them wrongly. Refuse it for every company.
            msg = "template has no {{SCHEMA}} placeholder — refusing to run it against any book"
            print("    %-12s FAILED  %s" % (sid, msg))
            sec = dict(sections.get(sid, {}))
            for co, _, _ in companies:
                sec[co] = {"file": os.path.basename(data_path(sid, co)), "rows": None,
                           "seconds": 0.0, "error": msg}
                errors.append("%s.%s: %s" % (sid, co, msg))
            sections[sid] = sec
            continue
        sec = dict(sections.get(sid, {}))
        for co, label, schema in companies:
            payload, entry = run_one(sid, path, template, co, label, schema,
                                     args.as_of, generated_at)
            if payload is not None:
                write_json(data_path(sid, co), payload)
            sec[co] = entry
            if entry["error"]:
                errors.append("%s.%s: %s" % (sid, co, entry["error"]))
        sections[sid] = sec

    # Sections in a fixed order, companies in book order, so the manifest is
    # byte-stable apart from generated_at and the timings.
    ordered = {}
    for sid in sorted(sections):
        ordered[sid] = {co: sections[sid][co] for co in COMPANY_KEYS if co in sections[sid]}

    manifest = {
        "board": "transporter",
        "generated_at": generated_at,
        "as_of": args.as_of,
        "connection": route,
        "hana_sql": os.path.basename(HANA_SQL),
        "companies": [{"key": k, "label": l, "schema": s} for k, l, s in COMPANIES],
        "sections": ordered,
        "errors": errors,
        "ok": not errors,
        "build_seconds": round(time.time() - t0, 1),
        "partial_run": bool(only or only_companies),
    }
    write_json(MANIFEST_PATH, manifest)

    total = sum((e.get("rows") or 0) for s in ordered.values() for e in s.values())
    print("\nwrote %d file(s) + manifest to %s  (%d rows, %.1fs)"
          % (sum(1 for s in ordered.values() for _ in s), DATA_DIR, total,
             manifest["build_seconds"]))
    if errors:
        print("\n%d FAILURE(S) — the other files were written; these were not refreshed:" % len(errors))
        for e in errors:
            print("  - %s" % e)
        sys.exit(1)


if __name__ == "__main__":
    main()
