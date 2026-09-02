#!/usr/bin/env python3
"""build_data.py — refresh engine for the JIVO Accounts dashboard.

Runs every .sql in pipeline/sql/ against all three SAP company books through the
read-only hana-sql CLI, and emits site/data.json.

Each .sql is written ONCE with two placeholders and executed three times:
    {{SCHEMA}}  ->  JIVO_OIL_HANADB | JIVO_MART_HANADB | JIVO_BEVERAGES_HANADB
    {{ASOF}}    ->  the as-of date, YYYY-MM-DD (default: today)

Read-only by construction: hana-sql refuses anything but SELECT/WITH, runs inside
a HANA read-only transaction, and never commits. This script issues no write of
any kind to SAP. It honours CLAUDE.md RULE 0.

Deterministic, stdlib-only, safe to run unattended (cron).

Exit codes: 0 ok, 1 no route to HANA / SQL failure, 2 sanity guard refused to
write (previous data.json is left untouched and still serving).

Usage:
    python3 build_data.py                    # today, all sections, all companies
    python3 build_data.py --as-of 2026-07-31 # a month-end position
    python3 build_data.py --only vendor-ageing,bank-reco
    python3 build_data.py --company oil
    python3 build_data.py --no-guard         # write even if the guards complain
"""
import argparse
import hashlib
import importlib
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
ROOT = os.path.dirname(PIPELINE_DIR)                 # accounts-dashboard/
REPO = os.path.dirname(ROOT)                         # jivo-cli/
SQL_DIR = os.path.join(PIPELINE_DIR, "sql")
BUILDERS_DIR = os.path.join(PIPELINE_DIR, "builders")
RAW_DIR = os.path.join(PIPELINE_DIR, "raw")
SITE_DIR = os.path.join(ROOT, "site")
OUT_PATH = os.path.join(SITE_DIR, "data.json")

# Overridable so this runs on the VPS / another box unchanged.
HANA_SQL = os.environ.get("HANA_SQL_BIN", os.path.join(REPO, "hana-sql", "hana-sql"))
HANA_DIR = os.path.dirname(HANA_SQL)
TUNNEL_ENV = os.environ.get("HANA_ENV_FILE", os.path.join(REPO, "connections", "hana-tunnel.env"))
# Re-raises the home bridge (VPS-parked hanadb ports) when the local port is dead.
BRIDGE_CMD = shlex.split(os.environ.get(
    "HANA_BRIDGE_CMD", "bash " + os.path.join(REPO, "connections", "sap-home-bridge.sh")))

COMPANIES = [
    ("oil",  "JIVO Wellness (Oil)", "JIVO_OIL_HANADB"),
    ("mart", "JIVO Mart",           "JIVO_MART_HANADB"),
    ("bev",  "JIVO Beverages",      "JIVO_BEVERAGES_HANADB"),
]

# A query that legitimately returns nothing for a company (tiny/absent activity).
# Guards downgrade "zero rows" from an error to a note for these.
MAY_BE_EMPTY = {"goods-return", "bank-reco", "provisions", "cash-sale"}

# Per-statement ceiling. The daily refresh must not sit on production HANA.
SQL_TIMEOUT = int(os.environ.get("HANA_SQL_TIMEOUT", "300"))

# Keep the raw TSV of every query for debugging. On by default for a hand-run
# build; the live 2-minute loop sets SAVE_RAW=0 so it is not rewriting ~10 MB
# of files nobody reads, 720 times a day.
SAVE_RAW = os.environ.get("SAVE_RAW", "1") not in ("0", "false", "no")

_ENV_ARGS = None  # set by connect(): [] = direct office route, or ["-env", ...]


# -------------------------------------------------------------- hana access

def _run_hana(sql, env_args, timeout=SQL_TIMEOUT):
    """Run one SQL statement through the read-only hana-sql CLI; return stdout."""
    p = subprocess.run([HANA_SQL] + env_args + [sql],
                       cwd=HANA_DIR, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "hana-sql exited %d" % p.returncode)
    return p.stdout


def _route_label():
    """Describe the route actually in use, read from the env file rather than
    assumed. The old hardcoded 'home bridge (13015)' caption was wrong on the VPS,
    which reaches HANA directly on its own parked port — a log that misreports
    where production data came from is worse than no log."""
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
            or "connection reset" in m or "no route to host" in m)


def connect():
    """Probe the direct office route, then the home bridge, raising it if down."""
    global _ENV_ARGS
    probe = 'SELECT 1 AS "OK" FROM DUMMY'
    # Short fuse: off the office network the direct route does not refuse, it
    # hangs. 8s is plenty for a LAN answer and keeps the daily refresh honest.
    try:
        _run_hana(probe, [], timeout=8)
        _ENV_ARGS = []
        print("connection: direct (office route)")
        return
    except Exception as e:
        print("direct route unavailable (%s)" % str(e).splitlines()[0][:120])

    try:
        _run_hana(probe, ["-env", TUNNEL_ENV], timeout=30)
        _ENV_ARGS = ["-env", TUNNEL_ENV]
        print("connection: %s" % _route_label())
        return
    except Exception as e:
        print("route %s dead (%s); re-raising the bridge..."
              % (_route_label(), str(e).splitlines()[0][:120]))

    try:
        subprocess.run(BRIDGE_CMD, capture_output=True, text=True, timeout=90)
        time.sleep(2)
        _run_hana(probe, ["-env", TUNNEL_ENV], timeout=30)
        _ENV_ARGS = ["-env", TUNNEL_ENV]
        print("connection: home bridge (re-raised)")
        return
    except Exception as e:
        sys.exit("FATAL: no route to SAP HANA. Direct probe failed, the bridge was "
                 "down, and re-raising it failed too (%s).\n"
                 "  Try:  bash %s" % (e, os.path.join(REPO, "connections", "sap-home-bridge.sh")))


# ------------------------------------------------------------------ parsing

def read_sql(path):
    """Read SQL, dropping leading comment/blank lines.

    hana-sql takes the statement as argv; a leading '--' would be misparsed as a
    CLI flag, so the comment header every .sql carries has to come off the front.
    Comments *after* the first SQL token are fine — the guard's lexer strips them.
    """
    with open(path) as f:
        lines = f.read().splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("--")):
        lines.pop(0)
    return "\n".join(lines).strip().rstrip(";").strip()


def parse_tsv(out, where):
    """TSV -> list of dicts. A row whose field count disagrees with the header is
    dropped and counted, never silently reshaped."""
    lines = out.splitlines()
    if not lines:
        return [], 0
    hdr = lines[0].split("\t")
    rows, bad = [], 0
    for ln in lines[1:]:
        if not ln:
            continue
        parts = ln.split("\t")
        if len(parts) != len(hdr):
            bad += 1
            continue
        rows.append(dict(zip(hdr, parts)))
    if bad:
        print("    ! %s: %d malformed row(s) dropped" % (where, bad))
    return rows, bad


def coerce(rows):
    """Normalise HANA's blank encodings and turn numeric-looking strings into
    numbers, so the browser never has to parse '?' or 'NULL'."""
    out = []
    for r in rows:
        o = {}
        for k, v in r.items():
            if v is None:
                o[k] = None
                continue
            s = v.strip()
            if s in ("", "?") or s.upper() == "NULL":
                o[k] = None
                continue
            try:
                f = float(s)
            except ValueError:
                o[k] = s
                continue
            # Keep identifiers as text. float() would happily eat a long document
            # number and round it, and a grouped doc number cannot be searched for
            # in SAP. Detect by column name as well as by length/leading zero.
            if (re.search(r"(_code|_num|_no|_entry|_id|_ref|_key|_masked)$", k, re.I)
                    and not re.search(r"(_pct|_amt)$", k, re.I)):
                o[k] = s
                continue
            # The long-token guard applies ONLY to integer-looking values. It used
            # to count digits after stripping the decimal point, so an ordinary
            # HANA DOUBLE like 1358792.4106999983 (17 digits) was kept as a STRING
            # — and the page, which switches on `typeof v === 'number'`, printed it
            # raw. That put "1358792.4106999983" and "₹13.59 L" in one column.
            digits = s.lstrip("-").replace(".", "")
            if "." not in s and (len(digits) > 15
                                 or (s.lstrip("-").startswith("0") and s.strip("-") != "0")):
                o[k] = s
            else:
                o[k] = int(f) if f == int(f) and abs(f) < 2**53 and "." not in s else f
        out.append(o)
    return out


# -------------------------------------------------------------------- build

def sections():
    """Every <id>.sql in sql/, with its optional <id>-detail.sql companion."""
    if not os.path.isdir(SQL_DIR):
        sys.exit("FATAL: no sql/ directory at %s" % SQL_DIR)
    ids = sorted({os.path.basename(f)[:-4].replace("-detail", "")
                  for f in os.listdir(SQL_DIR) if f.endswith(".sql")})
    return ids


def builders():
    """Sections whose data does NOT come from SAP HANA.

    The board began as one query engine over three HANA schemas. The budget
    register lives in a different system on a different box (JSAP / MSSQL), and
    forcing it through a .sql template would have meant lying about where it
    came from. A builder module owns its own connection and returns the same
    payload shape run_section() does, so the page cannot tell the difference.

    Each builders/<name>.py exposes SECTION_ID, optional OPTIONAL (True = a
    failure here must not stop the SAP sections publishing), and
    build(asof, only_companies, coerce).
    """
    if not os.path.isdir(BUILDERS_DIR):
        return {}
    if BUILDERS_DIR not in sys.path:
        sys.path.insert(0, BUILDERS_DIR)
    out = {}
    for fn in sorted(os.listdir(BUILDERS_DIR)):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        mod = importlib.import_module(fn[:-3])
        out[getattr(mod, "SECTION_ID", fn[:-3])] = mod
    return out


def run_section(sid, asof, only_companies):
    """Run <sid>.sql (+ -detail) for each company. Returns the section payload."""
    payload = {"summary": {}, "detail": {}, "errors": {}, "timing": {}}
    for kind, suffix in (("summary", ""), ("detail", "-detail")):
        path = os.path.join(SQL_DIR, sid + suffix + ".sql")
        if not os.path.exists(path):
            continue
        template = read_sql(path)
        for key, label, schema in COMPANIES:
            if only_companies and key not in only_companies:
                continue
            sql = template.replace("{{SCHEMA}}", schema).replace("{{ASOF}}", asof)
            t0 = time.time()
            try:
                out = _run_hana(sql, _ENV_ARGS)
            except subprocess.TimeoutExpired:
                msg = "timed out after %ds" % SQL_TIMEOUT
                print("    %-9s %-6s FAILED  %s" % (kind, key, msg))
                payload["errors"]["%s.%s" % (kind, key)] = msg
                continue
            except Exception as e:
                msg = str(e).splitlines()[0][:300]
                # A dropped SSH tunnel poisons every remaining query — connect()
                # runs once, so without this one long query taking the bridge down
                # fails the whole rest of the build. Re-raise it and retry once.
                if _is_conn_error(msg):
                    print("    %-9s %-6s connection lost, re-raising bridge..." % (kind, key))
                    try:
                        connect()
                        out = _run_hana(sql, _ENV_ARGS)
                    except Exception as e2:
                        msg = str(e2).splitlines()[0][:300]
                        print("    %-9s %-6s FAILED  %s" % (kind, key, msg))
                        payload["errors"]["%s.%s" % (kind, key)] = msg
                        continue
                else:
                    print("    %-9s %-6s FAILED  %s" % (kind, key, msg))
                    payload["errors"]["%s.%s" % (kind, key)] = msg
                    continue
            dt = time.time() - t0
            rows, _ = parse_tsv(out, "%s/%s/%s" % (sid, kind, key))
            payload[kind][key] = coerce(rows)
            payload["timing"]["%s.%s" % (kind, key)] = round(dt, 1)
            print("    %-9s %-6s %6d rows  %5.1fs" % (kind, key, len(rows), dt))
            # The raw TSVs are a debugging convenience for a human-run build. On
            # the 2-minute live loop they would rewrite ~10 MB every tick — several
            # GB of disk churn a day to keep a copy nobody reads. SAVE_RAW=0 there.
            if SAVE_RAW:
                os.makedirs(RAW_DIR, exist_ok=True)
                with open(os.path.join(RAW_DIR, "%s%s.%s.tsv" % (sid, suffix, key)), "w") as f:
                    f.write(out)
    return payload


# ------------------------------------------------------------------- guards

def guard(data, prev, optional=()):
    """Refuse to publish obviously-broken data. Returns a list of complaints.

    `optional` names sections sourced from a second system. A dead JSAP must not
    hold back a correct SAP board, so their failures are reported and skipped
    rather than counted against the build."""
    bad = []
    for sid, sec in data["sections"].items():
        if sid in optional:
            n = sum(len(v) for v in sec.get("summary", {}).values())
            if not n:
                print("  note: optional section %s has no data — publishing without it" % sid)
            elif sec.get("stale_since"):
                print("  note: optional section %s is serving its last good read (%s)"
                      % (sid, sec["stale_since"]))
            continue
        if sec["errors"]:
            for k, msg in sec["errors"].items():
                bad.append("%s: %s failed — %s" % (sid, k, msg))
        n_now = sum(len(v) for v in sec["summary"].values())
        if n_now == 0 and sid not in MAY_BE_EMPTY:
            bad.append("%s: zero rows across all companies" % sid)
        if prev:
            p = prev.get("sections", {}).get(sid)
            if p:
                n_before = sum(len(v) for v in p.get("summary", {}).values())
                if n_before >= 20 and n_now < n_before * 0.5:
                    bad.append("%s: row count collapsed %d -> %d (>50%% drop)"
                               % (sid, n_before, n_now))
    if not data["sections"]:
        bad.append("no sections produced any data at all")
    return bad


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Refresh the JIVO Accounts dashboard data.")
    ap.add_argument("--as-of", default=date.today().isoformat(),
                    help="position date, YYYY-MM-DD (default: today)")
    ap.add_argument("--only", default="", help="comma-separated section ids")
    ap.add_argument("--company", default="", help="comma-separated: oil,mart,bev")
    ap.add_argument("--no-guard", action="store_true",
                    help="write data.json even if the sanity guards complain")
    args = ap.parse_args()

    try:
        datetime.strptime(args.as_of, "%Y-%m-%d")
    except ValueError:
        sys.exit("FATAL: --as-of must be YYYY-MM-DD, got %r" % args.as_of)

    only = {s.strip() for s in args.only.split(",") if s.strip()}
    only_companies = {s.strip() for s in args.company.split(",") if s.strip()}
    for c in only_companies:
        if c not in {k for k, _, _ in COMPANIES}:
            sys.exit("FATAL: unknown company %r (expected oil, mart or bev)" % c)

    prev = None
    if os.path.exists(OUT_PATH):
        try:
            with open(OUT_PATH) as f:
                prev = json.load(f)
        except Exception:
            pass

    mods = builders()
    bids = [s for s in mods if not only or s in only]
    optional = {sid for sid, m in mods.items() if getattr(m, "OPTIONAL", False)}

    connect()
    ids = [s for s in sections() if not only or s in only]
    if not ids and not bids:
        sys.exit("FATAL: no sections to run (sql/ empty, or --only matched nothing)")
    print("as-of %s — %d section(s): %s"
          % (args.as_of, len(ids) + len(bids), ", ".join(ids + bids)))

    t0 = time.time()
    data = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "as_of": args.as_of,
        "companies": [{"key": k, "label": l, "schema": s} for k, l, s in COMPANIES],
        "sections": {},
    }
    for sid in ids:
        print("  %s" % sid)
        data["sections"][sid] = run_section(sid, args.as_of, only_companies)
    for sid in bids:
        print("  %s  (builder — not SAP)" % sid)
        try:
            sec = mods[sid].build(args.as_of, only_companies, coerce)
        except Exception as e:
            msg = str(e).splitlines()[0][:300]
            print("    builder UNAVAILABLE  %s" % msg)
            sec = {"summary": {}, "detail": {}, "errors": {"builder": msg}, "timing": {}}
        # A second system going dark must not BLANK a section that was correct
        # two minutes ago. Carry the last good payload and stamp it stale, so
        # the page can say "as at ..." instead of "no rows for this company".
        if not sum(len(v) for v in sec.get("summary", {}).values()):
            keep = (prev or {}).get("sections", {}).get(sid)
            if keep and sum(len(v) for v in keep.get("summary", {}).values()):
                print("    keeping the previous payload (source unreachable)")
                sec = dict(keep)
                # stale_since, not errors[] — the page filters errors by company
                # key, so an unkeyed entry would show in the Group tab and hide
                # in every other one. The banner belongs to the section.
                sec["stale_since"] = keep.get("stale_since") or (prev or {}).get("generated_at")
                sec["errors"] = {}
        data["sections"][sid] = sec
    data["build_seconds"] = round(time.time() - t0, 1)

    # A partial run must not clobber the sections it did not rebuild.
    if (only or only_companies) and prev:
        merged = dict(prev.get("sections", {}))
        for sid, sec in data["sections"].items():
            if only_companies and sid in merged:
                for kind in ("summary", "detail", "errors", "timing"):
                    merged[sid].setdefault(kind, {}).update(sec.get(kind, {}))
            else:
                merged[sid] = sec
        data["sections"] = merged

    complaints = guard(data, prev, optional)
    if complaints:
        print("\nSANITY GUARD:")
        for c in complaints:
            print("  - %s" % c)
        if not args.no_guard:
            print("\nREFUSING TO WRITE. The previous data.json is untouched and still "
                  "serving.\nRe-run with --no-guard to publish anyway.")
            sys.exit(2)
        print("\n--no-guard: publishing anyway.")
        data["guard_warnings"] = complaints

    # Fingerprint the business data only — generated_at, build_seconds and the
    # per-query timings change on every run by construction. The live refresh
    # loop compares this to decide whether to deploy, and writing it here means
    # that loop never has to re-parse a 10 MB document just to ask "did anything
    # actually change?" (which cost ~10s of every 2-minute tick).
    fingerprint = {
        "as_of": data["as_of"],
        "sections": {k: {kk: vv for kk, vv in v.items() if kk != "timing"}
                     for k, v in data["sections"].items()},
    }
    data["data_sha256"] = hashlib.sha256(
        json.dumps(fingerprint, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode()).hexdigest()

    os.makedirs(SITE_DIR, exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    os.replace(tmp, OUT_PATH)
    with open(os.path.join(SITE_DIR, ".data.sha256"), "w") as f:
        f.write(data["data_sha256"] + "\n")
    size = os.path.getsize(OUT_PATH)
    total = sum(len(v) for s in data["sections"].values() for v in s["summary"].values())
    print("\nwrote %s  (%.1f KB, %d summary rows, %.1fs)"
          % (OUT_PATH, size / 1024.0, total, data["build_seconds"]))


if __name__ == "__main__":
    main()
