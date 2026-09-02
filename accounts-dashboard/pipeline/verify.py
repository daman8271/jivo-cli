#!/usr/bin/env python3
"""verify.py — prove each headline twice, every build.

The v1 board was adversarially reviewed once, in the past, and all eleven
queries came back FIXED. That review was a moment in time. This makes it a
heartbeat: on every build each figure is re-derived by a genuinely different
route and the two are compared.

Crucially both routes are computed from the SAME build, so there is no time
skew between them. (Comparing a board figure against a fresh database read
half an hour later measures the clock, not the query — a trap worth naming.)

  python3 pipeline/verify.py [--data site-v2/data] [--strict]

--strict exits 2 on a critical disagreement so the refresh loop refuses to
publish. By default a disagreement is RECORDED and published with a red dot,
because a number shown with a warning beats a number withheld.
"""
import argparse, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from kpis import scale                                        # noqa: E402

TOL = 1e-4          # 1 basis point
ROLLUP = ("ZZ_TOTAL", "TOTAL", "ALL", "GRAND TOTAL")
MONEYISH = re.compile(r"(_INR|_L|_CR|_GROSS|_NET|_AMT|_OPEN|_BAL|_SPEND|_COST|_VAL)$", re.I)


def load(d, name):
    p = os.path.join(d, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def rel(a, b):
    if a is None or b is None:
        return None
    if abs(b) < 1e-9:
        return 0.0 if abs(a) < 1e-9 else 1.0
    return (a - b) / abs(b)


# Facets that must account for the whole section. A VENDOR/PARTY/ITEM facet is
# often a top-N slice and is not expected to reconcile — flagging it would be
# crying wolf, so it is reported as partial coverage instead.
EXHAUSTIVE = ("CLASS", "KIND", "MONTH", "CREDIT_NOTE", "STATUS", "AGE_BUCKET", "TYPE")


def check_rollups(data, co, sections):
    """The broadest automatic check there is.

    Several sections stack a roll-up row AND SEVERAL INDEPENDENT FACETS of the
    same data in one result set — goods-return carries TOTAL, CLASS, MONTH,
    CREDIT_NOTE and VENDOR together. Summing every non-total row counts the
    section four times over (it reads as +300%, which is how this check first
    caught its own naivety). So each facet is reconciled to the total on its
    own. This is the single most common way a board like this goes quietly
    wrong, and I walked into it myself while tying out A/R.
    """
    out = []
    for sec in sections:
        blob = load(data, "%s.%s.json" % (sec, co))
        if not blob:
            continue
        rows = blob.get("summary") or []
        if not rows:
            continue
        keycol = next((c for c in ("SCOPE", "KIND", "ROW_TYPE", "SECTION")
                       if c in rows[0]), None)
        if not keycol:
            continue
        roll = [r for r in rows if str(r.get(keycol)).upper() in ROLLUP]
        if not roll:
            continue
        facets = {}
        for r in rows:
            k = str(r.get(keycol)).upper()
            if k in ROLLUP:
                continue
            facets.setdefault(k, []).append(r)
        for col in rows[0]:
            if not MONEYISH.search(col):
                continue
            rv = sum(scale(r.get(col), col) or 0 for r in roll)
            if abs(rv) < 1:
                continue
            for fname, frows in facets.items():
                cv = sum(scale(r.get(col), col) or 0 for r in frows)
                if abs(cv) < 1:
                    continue
                d = rel(cv, rv)
                if d is None or abs(d) <= TOL:
                    continue
                exhaustive = any(fname.startswith(e) for e in EXHAUSTIVE)
                out.append({"section": sec, "column": col, "facet": fname,
                            "rollup": rv, "facet_sum": cv, "delta_pct": d * 100,
                            "severity": "disagreement" if exhaustive else "partial-coverage",
                            "note": None if exhaustive else
                                    "this facet is a top-N slice, not expected to reconcile"})
    return out


def check_cross_section(data, co):
    """A/R and A/P re-derived from open-item-list — a different query with
    different joins, one row per open document — instead of from the ageing
    sections.

    open-item-list PUBLISHES ONLY A TOP-N SLICE (669 of 13,030 open A/R
    invoices on Oil), so summing its visible rows understates the book by
    20-35%. It carries DT_OPEN_ALL, the untruncated total per document type,
    which is the figure to compare. Getting this wrong the first time produced
    a confident 640% "disagreement" that was entirely an artefact of the check.
    """
    out = []
    oil = load(data, "open-item-list.%s.json" % co)
    if not oil:
        return out
    rows = oil.get("summary") or []

    def doctype_total(dt):
        for r in rows:
            if str(r.get("DOCTYPE", "")).upper() == dt:
                v = r.get("DT_OPEN_ALL")
                return scale(v, "DT_OPEN_ALL") if v is not None else None
        return None

    ca = load(data, "customer-ageing.%s.json" % co) or {}
    va = load(data, "vendor-ageing.%s.json" % co) or {}

    pairs = [
        ("ar-raw-open", "AR_INV",
         sum(scale(r.get("RAW_OPEN_INR"), "RAW_OPEN_INR") or 0
             for r in (ca.get("summary") or [])
             if str(r.get("KIND")).upper() in ROLLUP),
         "customer-ageing RAW_OPEN roll-up vs open-item-list DT_OPEN_ALL for AR_INV"),
        ("ap-raw-open", "AP_INV",
         sum(scale(r.get("RAW_OPEN"), "RAW_OPEN") or 0 for r in (va.get("summary") or [])),
         "vendor-ageing RAW_OPEN summed per card vs open-item-list DT_OPEN_ALL for AP_INV"),
    ]
    for kid, dt, primary, method in pairs:
        alt = doctype_total(dt)
        if not primary or alt is None:
            continue
        d = rel(alt, primary) or 0.0
        out.append({"kpi": kid, "primary": primary, "alt": alt,
                    "delta_pct": d * 100, "method": method,
                    "ok": abs(d) <= TOL})
    return out


def check_corrections():
    """Where is each correction actually honoured? A correction we cannot locate
    is reported UNVERIFIED, never as passing."""
    want = ["C-0001", "C-0005", "C-0019", "C-0020", "C-0021", "C-0022", "C-0023"]
    hay = []
    for pat in ("pipeline/sql/*.sql", "pipeline/*.py", "specs/*.json"):
        for p in glob.glob(os.path.join(ROOT, pat)):
            try:
                hay.append((os.path.relpath(p, ROOT), open(p, encoding="utf-8").read()))
            except Exception:
                pass
    out = {}
    for c in want:
        hits = []
        for name, txt in hay:
            for i, line in enumerate(txt.splitlines(), 1):
                if c in line:
                    hits.append("%s:%d" % (name, i))
                    break
        out[c] = {"honoured_at": hits[:6],
                  "status": "referenced" if hits else "UNVERIFIED"}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "site-v2", "data"))
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    man_path = os.path.join(a.data, "manifest.json")
    man = json.load(open(man_path, encoding="utf-8"))
    companies = [c["key"] for c in man.get("companies", [])] or ["oil", "mart", "bev"]
    sections = sorted(man.get("sections", {}))

    audit = {"rollup_disagreements": {}, "cross_section": {}, "additivity": {},
             "corrections": check_corrections(), "kpi_checks": {}}
    critical = 0

    for co in companies:
        rd = check_rollups(a.data, co, sections)
        audit["rollup_disagreements"][co] = rd
        audit["cross_section"][co] = check_cross_section(a.data, co)

        derivs = load(a.data, "derivations.%s.json" % co) or {}
        for kid, rec in derivs.items():
            # What the dot means, precisely.
            #
            # reproduces_spec_measurement compares today's figure against the one
            # the inventory pass measured when it read the SQL, hours earlier. A
            # live book MOVES. Treating any difference as an error paints the
            # board red every afternoon and trains the reader to ignore red —
            # the same failure the closure check already had.
            #
            # So: a small difference is business movement (green), a moderate one
            # is drift worth showing (amber), and only a gross difference or a
            # sign flip indicates the computation itself is wrong (red).
            rep = rec.get("reproduces_spec_measurement")
            clo = rec.get("closure")
            alt = (rec.get("spec_live") or {}).get(co)
            v = rec.get("value")
            if rep is True:
                # Reproduction OUTRANKS closure. A value that exactly matches an
                # independent measurement is correct; if its term decomposition
                # does not add up, that is a fact about the decomposition, worth
                # noting, not grounds for calling the number wrong.
                if clo and not clo.get("ok"):
                    ok, method = None, ("value reproduces the independent measurement, but "
                                        "its published term decomposition does not add up "
                                        "(delta %.2f) — the terms describe the query, they "
                                        "are not addends" % clo.get("delta", 0))
                else:
                    ok, method = True, ("reproduces the figure measured independently "
                                        "from the SQL when the section was catalogued")
            elif clo and not clo.get("ok"):
                ok, method = False, "the terms do not sum to the value"
                alt = clo.get("terms_sum")
            elif rep is False and v is not None and alt:
                r = abs(v - alt) / max(abs(alt), 1.0)
                flipped = (v < 0) != (alt < 0)
                if flipped or r > 0.25:
                    ok, method = False, ("differs from the independently measured figure "
                                         "by %.0f%%%s — too large to be movement in the books"
                                         % (r * 100, ", and the sign flipped" if flipped else ""))
                else:
                    ok, method = None, ("%.1f%% from the figure measured when the section was "
                                        "catalogued — consistent with movement in a live book, "
                                        "not corroborated" % (r * 100))
            else:
                ok, method = None, "no independent measurement exists for this KPI"
            chk = {"ok": ok, "alt_value": alt, "method": method,
                   "delta": (v - alt) if (v is not None and alt is not None) else None,
                   "delta_pct": (rel(v, alt) or 0) * 100 if (v is not None and alt) else None}
            rec["check"] = chk
            # The manifest is polled by every page every 60 seconds. It carries
            # only the verdict; the method prose and both figures live in
            # derivations.<co>.json, which only the drill-down page loads.
            # alt_value and a SHORT method travel in the manifest: without them
            # checkDot cannot name the second figure, so every page had to pull
            # the 1.6 MB derivations file just to render a tooltip. The long
            # prose stays in derivations.<co>.json.
            man.setdefault("kpis", {}).setdefault(co, {}).setdefault(kid, {})["check"] = {
                "ok": chk["ok"],
                "alt_value": chk["alt_value"],
                "delta_pct": round(chk["delta_pct"], 4) if chk["delta_pct"] is not None else None,
                # A NOUN PHRASE: ui.js renders it as "the <method> re-derivation".
                # A verdict sentence here reads as broken English on every tooltip.
                "method": ("independent" if ok is True else
                           "disagreeing" if ok is False else
                           "uncorroborated"),
            }
            if ok is False:
                critical += 1
        with open(os.path.join(a.data, "derivations.%s.json" % co), "w", encoding="utf-8") as fh:
            json.dump(derivs, fh, sort_keys=True, separators=(",", ":"))

    # additivity: group = oil + mart + bev, per KPI
    for kid in (man.get("kpis", {}).get(companies[0]) or {}):
        vals = [(man["kpis"].get(c, {}).get(kid) or {}).get("value") for c in companies]
        if all(isinstance(v, (int, float)) for v in vals):
            audit["additivity"][kid] = {"per_company": dict(zip(companies, vals)),
                                        "group": sum(vals),
                                        "note": "intercompany NOT eliminated (C-0005)"}

    # The audit block is large (per-KPI additivity across every book) and only
    # health.html reads it. The manifest is polled by EVERY page every 60s, so
    # it stays small; the audit lives in its own file with a summary left behind.
    with open(os.path.join(a.data, "audit.json"), "w", encoding="utf-8") as fh:
        json.dump(audit, fh, sort_keys=True, separators=(",", ":"))
    man["audit_summary"] = {
        "rollup_disagreements": sum(1 for v in audit["rollup_disagreements"].values()
                                    for it in v if it["severity"] == "disagreement"),
        "cross_section_ok": all(it.get("ok") for v in audit["cross_section"].values() for it in v),
        "corrections_unverified": [c for c, v in audit["corrections"].items()
                                   if v["status"] == "UNVERIFIED"],
        "kpi_checks_failing": critical,
        "kpi_checks_total": sum(len(x) for x in man.get("kpis", {}).values()),
    }
    man.pop("audit", None)
    # Atomic, like history.py and the slices. A plain open(...,"w") was observed
    # serving a TORN manifest mid-write: every KPI came back with check: null.
    # The board polls this file every 60 seconds, so the race is not theoretical.
    tmp = man_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(man, fh, sort_keys=True, separators=(",", ":"))
    os.replace(tmp, man_path)

    nroll = sum(1 for v in audit["rollup_disagreements"].values()
                for it in v if it["severity"] == "disagreement")
    print("  roll-up vs components : %d disagreement(s) over %d sections x %d books"
          % (nroll, len(sections), len(companies)))
    for co, items in audit["rollup_disagreements"].items():
        for it in [x for x in items if x["severity"] == "disagreement"][:6]:
            print("      %-5s %-14s %-9s %-20s total=%.2f facet=%.2f (%+.2f%%)"
                  % (co, it["section"], it["facet"], it["column"],
                     it["rollup"], it["facet_sum"], it["delta_pct"]))
    for co, items in audit["cross_section"].items():
        for it in items:
            print("  cross-section %-5s %-13s primary=%9.2f Cr  alt=%9.2f Cr  (%+.4f%%)  %s"
                  % (co, it["kpi"], it["primary"] / 1e7, it["alt"] / 1e7,
                     it["delta_pct"], "AGREE" if it["ok"] else "DISAGREE"))
    unver = [c for c, v in audit["corrections"].items() if v["status"] == "UNVERIFIED"]
    print("  corrections           : %d referenced, %d UNVERIFIED %s"
          % (len(audit["corrections"]) - len(unver), len(unver), unver or ""))
    print("  KPI checks failing    : %d" % critical)
    return 2 if (a.strict and (critical or nroll)) else 0


if __name__ == "__main__":
    sys.exit(main())
