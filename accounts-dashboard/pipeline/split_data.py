#!/usr/bin/env python3
"""split_data.py — data.json (10.7 MB) -> site-v2/data/ (a manifest + per-page slices).

v1 refetches the whole 10.7 MB document every two minutes, in every open tab, to
render one page. A 20-page board cannot work that way: the reader would pay for
all thirteen sections to look at one.

So the monolith is cut into a ~20 KB manifest that every page polls, and one
slice per section per company that only the page needing it ever loads.

Section-AGNOSTIC on purpose: it splits whatever data.json contains. A new
section (the budget register arrived on 2026-08-22) appears in the manifest and
gets its slice without this file being touched.

  python3 pipeline/split_data.py [--in site/data.json] [--out site-v2/data]
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# C-0005: intercompany is 23 group CardCodes, not just CUSTA000606.
INTERCO = {
    "oil":  {"CUSTA000001","CUSTA000002","CUSTA000003","CUSTA000004","CUSTA000606",
             "CUSTA000827","CUSTA000906","CUSTA001099","CUSTA001113"},
    "mart": {"CUSTA000001","CUSTA000827","CUSTA000874","CUSTA000875","CUSTA000876",
             "CUSTA000877","CUSTA000878","CUSTA000926"},
    "bev":  {"CUSTA000001","CUSTA000002","CUSTA000003","CUSTA000004","CUSTA000606",
             "CUSTA000827"},
}
# C-0020: intercompany VENDORS hide outside the BRANCH groups — Mart VENDA000001
# 'JIVO WELLNESS' sits in group PURCHASE, Oil VENDA000483 in E-COMMERCE. Group
# alone misses them, so the card name is matched too.
INTERCO_NAME = re.compile(r"\b(JIVO|AKAL)\b", re.I)


def atomic_write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, sort_keys=True, separators=(",", ":"))
    os.replace(tmp, path)     # a half-written slice must never be served
    return os.path.getsize(path)


def kind_of(row, company):
    """TRADE / BRANCH / INTERCO / STAFF, preferring what the query already decided."""
    for key in ("ACCT_KIND", "KIND", "PARTY_CLASS"):
        v = row.get(key)
        if isinstance(v, str) and v.upper() in ("TRADE", "BRANCH", "INTERCO", "STAFF"):
            return v.upper()
    card = str(row.get("CARD_CODE") or row.get("CardCode") or "")
    name = str(row.get("CARD_NAME") or "")
    if card in INTERCO.get(company, set()):
        return "INTERCO"
    if INTERCO_NAME.search(name):
        return "INTERCO"
    if card.startswith("ORGV"):
        return "STAFF"          # employee imprest cards, filed as vendors
    return "TRADE"


def build_parties(sections, company):
    """One row per distinct card across every section that names one."""
    out = {}
    # Order matters and is not arbitrary. Both the ageing sections AND
    # open-item-list carry an explicit ACCT_KIND, and they DISAGREE: 18 employee
    # imprest vendors (ORGV*) read TRADE in vendor-ageing and STAFF in
    # open-item-list. The ageing sections are what actually compute the trade
    # headline, so their word is the one the directory must carry — otherwise a
    # party page contradicts the figure the reader just clicked through from.
    for sec in ("vendor-ageing", "customer-ageing", "open-item-list"):
        blob = sections.get(sec) or {}
        for kind in ("summary", "detail"):
            for r in (blob.get(kind) or {}).get(company) or []:
                card = r.get("CARD_CODE")
                if not card or not isinstance(card, str):
                    continue
                side = "V" if (sec == "vendor-ageing"
                               or str(r.get("CARD_TYPE") or "").upper().startswith("S")
                               or card.startswith(("VENDA", "ORGV"))) else "C"
                bal = r.get("OCRD_BALANCE", r.get("CARD_BALANCE"))
                prev = out.get((card, side))
                # A card appears in several sections. Only the ageing sections
                # carry an explicit ACCT_KIND/KIND, and that is what actually
                # decides whether the card sits inside a trade headline. Rows
                # from open-item-list have no such column, so the heuristic below
                # fires and can contradict it — it did, on 18 staff imprest
                # vendors and CUSTA000242, which the directory called STAFF/INTERCO
                # while vendor-ageing had them as TRADE and inside the headline.
                # An explicit classification always wins over an inferred one.
                explicit = any(isinstance(r.get(c), str) and
                               r.get(c, "").upper() in ("TRADE", "BRANCH", "INTERCO", "STAFF")
                               for c in ("ACCT_KIND", "KIND"))
                rec = {
                    "card": card, "side": side,
                    "name": r.get("CARD_NAME") or (prev or {}).get("name") or "",
                    "group": r.get("VENDOR_GROUP") or r.get("CUSTOMER_GROUP")
                             or r.get("BP_GROUP") or (prev or {}).get("group") or "",
                    "kind": kind_of(r, company),
                    "kind_explicit": explicit,
                    "balance": (float(bal) if bal not in (None, "") else
                                (prev or {}).get("balance")),
                }
                # Prefer the row that actually carries a balance and a name.
                # First explicit wins, and the loop visits the ageing sections first.
                if prev and prev.get("kind_explicit"):
                    rec["kind"] = prev["kind"]          # keep the section's word
                    rec["kind_explicit"] = True
                if prev and prev.get("balance") is not None and rec["balance"] is None:
                    rec["balance"] = prev["balance"]
                if prev and not rec["name"]:
                    rec["name"] = prev.get("name", "")
                out[(card, side)] = rec
    return sorted(out.values(), key=lambda p: (p["side"], p["card"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=os.path.join(ROOT, "site", "data.json"))
    ap.add_argument("--out", dest="dst", default=os.path.join(ROOT, "site-v2", "data"))
    a = ap.parse_args()

    if not os.path.exists(a.src):
        print("split_data: no input at %s" % a.src, file=sys.stderr)
        return 1
    with open(a.src, encoding="utf-8") as fh:
        d = json.load(fh)

    os.makedirs(a.dst, exist_ok=True)
    companies = d.get("companies") or []
    keys = [c["key"] for c in companies] or ["oil", "mart", "bev"]
    sections = d.get("sections") or {}

    manifest = {
        "generated_at": d.get("generated_at"),
        "as_of": d.get("as_of"),
        "build_seconds": d.get("build_seconds"),
        "companies": companies,
        "sections": {},
        "kpis": {k: {} for k in keys},     # derive.py fills these
        "audit": {},                       # verify.py fills this
        "stale": False,
        "stale_reason": None,
        "history_points": 0,
        "alerts": [],
    }

    # Surface any operational alert the refresh loop raised, so health.html can
    # show WHY a build is missing rather than only that it is old.
    alert_path = os.path.join(HERE, "alert-state.json")
    if os.path.exists(alert_path):
        try:
            manifest["alerts"] = json.loads(open(alert_path).read()).get("alerts", [])[:5]
        except Exception:
            pass

    total = 0
    for sec, blob in sorted(sections.items()):
        errors = blob.get("errors") or {}
        timing = blob.get("timing") or {}
        # build_data.py files these under a COMPOUND key — "summary.oil",
        # "detail.oil" — not under the bare company. Reading timing.get("oil")
        # therefore returned None for every section (all timings published null),
        # and errors.get("oil") returned None for every FAILED query, which meant
        # a section could never reach status "error" at all. That is a hole in
        # exactly the alarm health.html exists to display: a query could fail on
        # every book and the board would call the section merely "empty".
        def _for(d, co):
            return {k: v for k, v in (d or {}).items()
                    if k == co or k.endswith("." + co)}

        rows, secs = {}, {}
        for co in keys:
            summ = (blob.get("summary") or {}).get(co) or []
            det = (blob.get("detail") or {}).get(co) or []
            rows[co] = len(summ)
            t = [v for v in _for(timing, co).values() if isinstance(v, (int, float))]
            secs[co] = round(sum(t), 1) if t else None
            errs_co = _for(errors, co)
            n = atomic_write(os.path.join(a.dst, "%s.%s.json" % (sec, co)), {
                "section": sec, "company": co, "as_of": d.get("as_of"),
                "summary": summ, "detail": det,
                "error": "; ".join(str(v) for v in errs_co.values()) or None,
            })
            total += n
        # never silently zero: an errored or empty section says so, with the message
        any_err = {co: _for(errors, co) for co in keys}
        if any(any_err[co] for co in keys):
            first = next(co for co in keys if any_err[co])
            status = "error"
            err = "; ".join("%s: %s" % (k, v) for k, v in any_err[first].items())
        elif not any(rows.values()):
            status, err = "empty", "returned no rows in any book"
        else:
            status, err = "ok", None
        manifest["sections"][sec] = {"status": status, "error": err,
                                     "rows": rows, "seconds": secs}

    for co in keys:
        p = build_parties(sections, co)
        total += atomic_write(os.path.join(a.dst, "parties.%s.json" % co), p)
        n_ic = sum(1 for x in p if x["kind"] == "INTERCO")
        print("  parties.%-5s %5d cards (%d intercompany, %d branch, %d staff)"
              % (co, len(p), n_ic,
                 sum(1 for x in p if x["kind"] == "BRANCH"),
                 sum(1 for x in p if x["kind"] == "STAFF")))

    # Ship the section notes INTO the deploy root. ui.js renders them inline on
    # each section page ("the trap that makes a naive reading wrong belongs on
    # the page, not in a repo nobody opens") — but site-v2/ IS the Vercel root,
    # so pipeline/notes/ is never deployed and every one of those fetches 404s
    # in production while working locally from the repo. Copy, don't symlink.
    notes_src = os.path.join(HERE, "notes")
    notes_dst = os.path.join(os.path.dirname(a.dst), "notes")
    if os.path.isdir(notes_src):
        os.makedirs(notes_dst, exist_ok=True)
        n_notes = 0
        for fn in sorted(os.listdir(notes_src)):
            if fn.endswith(".md"):
                with open(os.path.join(notes_src, fn), encoding="utf-8") as fh:
                    body = fh.read()
                with open(os.path.join(notes_dst, fn), "w", encoding="utf-8") as fh:
                    fh.write(body)
                n_notes += 1
        # An index of what exists. Without it note() must fetch-and-fail to find
        # out, and the browser logs a 404 for every section that has no note —
        # which makes the console-error count in browser-check.sh meaningless,
        # so a real error would hide among the benign ones.
        have = sorted(fn[:-3] for fn in os.listdir(notes_dst) if fn.endswith(".md"))
        with open(os.path.join(notes_dst, "_index.json"), "w", encoding="utf-8") as fh:
            json.dump(have, fh)
        print("  notes         %d markdown files + an index copied into the deploy root"
              % n_notes)

    # Ship the QUERIES into the deploy root too, for the same reason as the notes:
    # section pages show the SQL that produced their figures, and pipeline/ is not
    # deployed beside site-v2/. Read-only SELECT text, already public in the repo.
    sql_src = os.path.join(HERE, "sql")
    sql_dst = os.path.join(os.path.dirname(a.dst), "sql")
    if os.path.isdir(sql_src):
        os.makedirs(sql_dst, exist_ok=True)
        n_sql = 0
        for fn in sorted(os.listdir(sql_src)):
            if fn.endswith(".sql"):
                with open(os.path.join(sql_src, fn), encoding="utf-8") as fh:
                    body = fh.read()
                with open(os.path.join(sql_dst, fn), "w", encoding="utf-8") as fh:
                    fh.write(body)
                n_sql += 1
        with open(os.path.join(sql_dst, "_index.json"), "w", encoding="utf-8") as fh:
            json.dump(sorted(f[:-4] for f in os.listdir(sql_dst) if f.endswith(".sql")), fh)
        print("  sql           %d queries + an index copied into the deploy root" % n_sql)

    mp = os.path.join(a.dst, "manifest.json")
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)

    print("  manifest      %.1f KB   %d sections   generated_at %s"
          % (os.path.getsize(mp) / 1024, len(manifest["sections"]),
             manifest["generated_at"]))
    print("  slices        %.1f MB total" % (total / 1024 / 1024))
    # This rewrites manifest.json WHOLE, so kpis/audit_summary come back empty.
    # Running it on its own silently strips every KPI from the board and the
    # pages render with no headline figures and no error. Always follow it with
    # derive.py and verify.py — build-v2.sh does; a bare invocation does not.
    print("  NOTE          manifest kpis/audit are now EMPTY — run derive.py then "
          "verify.py (or just pipeline/build-v2.sh) before serving this build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
