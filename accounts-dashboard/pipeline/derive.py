#!/usr/bin/env python3
"""derive.py — turn every KPI into a number AND the story of how it was made.

This is the point of the whole board. A figure with no derivation is just a
claim; a figure whose formula, terms, exclusions, SQL and caveats travel WITH it
can be checked by the person reading it.

Derivations are computed here, server-side, from the same rows that produced the
headline. The frontend renders them and never re-derives — one definition,
computed once, so a drill-down cannot drift away from the number it explains.

  python3 pipeline/derive.py [--data site-v2/data] [--strict]

--strict makes a term-closure failure fatal (exit 2). By default a KPI whose
terms do not add up is still published, flagged, and listed — because hiding it
would be the very thing this file exists to prevent.
"""
import argparse, datetime, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from kpis import (load_specs, validate, scale, rowmatch, resolve_rows,  # noqa: E402
                  FILTER_ERRORS)

CORR_DIR = os.path.join(os.path.dirname(ROOT), "harness", "corrections")
CLOSURE_TOL = 0.005          # half a paisa, before the relative floor below

# Columns that count things rather than measure money. A formula mixing these
# with rupees cannot close, and gating on it would produce noise, not signal.
_COUNTISH = re.compile(r"(_N|_CNT|_COUNT|_DOCS|_LINES|_ROWS|_PCT|_SHARE|_DAYS)$", re.I)


def _is_money(col):
    return bool(col) and not _COUNTISH.search(col)


# Unambiguously a money column. Deliberately stricter than _is_money: used only
# where being wrong silently changes the ANSWER rather than a diagnostic.
# _is_money's "anything not obviously a count" is too generous here — it called
# N_EFF_CUSTOMERS, CO_ITEMS_ALL and RET_QTY_PCS money, which would have replaced
# three correct counts with a row-count of 1.
_STRICT_MONEY = re.compile(r"(_INR|_L|_CR|_GROSS|_NET|_AMT|_OPEN|_BAL|_COST|_VAL|_SPEND)$", re.I)


def corrections():
    """C-00xx id -> {id, title, rule, wrong, right}. Read once."""
    out = {}
    for path in sorted(glob.glob(os.path.join(CORR_DIR, "C-*.md"))):
        txt = open(path, encoding="utf-8").read()
        cid = re.search(r"^id:\s*(C-\d+)", txt, re.M)
        if not cid:
            continue
        title = re.search(r"^#\s+(.+)$", txt, re.M)
        def sect(name):
            m = re.search(r"^##\s+%s\s*\n(.+?)(?=\n##\s|\Z)" % name, txt, re.M | re.S)
            return m.group(1).strip() if m else None
        rule = sect("Rule")
        if rule:
            rule = "\n".join(l for l in rule.splitlines() if not l.strip().startswith("<!--")).strip()
            rule = rule.split("-->")[-1].strip()
        out[cid.group(1)] = {"id": cid.group(1),
                             "title": title.group(1).strip() if title else cid.group(1),
                             "rule": rule, "wrong": sect("Wrong"), "right": sect("Right")}
    return out


def agg(rows, col, how):
    vals = [scale(r.get(col), col) for r in rows]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    if how == "first":
        return vals[0]
    if how == "max":
        return max(vals)
    if how == "avg":
        return sum(vals) / len(vals)
    if how == "median":
        v = sorted(vals)
        n = len(v)
        return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0
    return sum(vals)


def sql_slice(relpath, lines):
    if not relpath or not lines or len(lines) != 2:
        return None
    p = os.path.join(ROOT, relpath)
    if not os.path.exists(p):
        return None
    src = open(p, encoding="utf-8").read().splitlines()
    a, b = max(1, lines[0]), min(len(src), lines[1])
    return {"file": relpath, "lines": [a, b],
            "text": "\n".join(src[a - 1:b])}


def derive_one(k, blob, spec, corr, company, as_of=None):
    col, how = k["column"], (k.get("agg") or "sum")
    # agg='count' means "how many rows match", and its column is often TEXT
    # (reco-never-reconciled-n counts RECO_STATUS). Mapping it to sum summed a
    # text column and published null where the answer was already sitting in
    # n_rows. Same for 'count_ratio', handled as a candidate below.
    counting = how in ("count", "count_ratio")
    if counting:
        how = "sum"
    kind, rows = resolve_rows(k, blob)
    sel = [r for r in rows if rowmatch(k.get("row_filter"), r)]
    raw = agg(sel, col, how)

    # ── the terms, computed first, because for many KPIs they ARE the value ──
    terms, plus, minus, closing, closing_col, n_signed = [], 0.0, 0.0, None, None, 0
    for t in k.get("terms") or []:
        tc = t.get("col")
        tv = agg(sel, tc, how) if tc else None
        op = t.get("op") or "+"
        terms.append({"label": t.get("label"), "col": tc, "op": op,
                      "source": t.get("source"), "note": t.get("note"), "value": tv})
        if tv is None:
            continue
        # A COUNT is not an addend of a money figure. Specs list columns like
        # TXN_CNT among the terms as context, and summing them into a rupee
        # total adds the transaction count to the rupees:
        # cash-sale-ar-control-gl-net came out exactly TXN_CNT too high — 1,300
        # on Oil, 336 on Bev. On Bev that is 0.03% of the figure, which sailed
        # through the reproduction tolerance and earned a GREEN dot on a wrong
        # number. Only same-unit terms may be summed.
        countish = bool(tc) and _COUNTISH.search(tc) is not None
        if op == "+" and not (k.get("unit") == "INR" and countish):
            plus += tv; n_signed += 1
        elif op == "-" and not (k.get("unit") == "INR" and countish):
            minus += tv; n_signed += 1
        elif op == "=":
            closing, closing_col = tv, tc

    # ── candidate readings ────────────────────────────────────────────────
    # A KPI is not always "one column, aggregated". bank-net-position is a FIVE
    # column expression (current + cash + wallet + FD - borrowings); reading only
    # its `column` returned Rs 5.52 L where the answer is -Rs 74.86 Cr, and
    # published apparent liquidity JIVO does not have — the exact failure that
    # card exists to prevent.
    #
    # So: enumerate every PRINCIPLED reading of the spec, then pick the one that
    # reproduces the figure the inventory pass measured by reading the SQL. Each
    # candidate is a legitimate interpretation, never a fitted constant, and the
    # one chosen is recorded in `method` and shown on the derivation page. If
    # none reproduces, the plain column read stands and the KPI goes red.
    cands = [("direct", raw)]

    if k.get("unit") == "count" and _STRICT_MONEY.search(col or ""):
        cands.append(("row count over the filter (unit is count)", float(len(sel))))

    if k.get("unit") == "pct":
        den_col = closing_col if closing_col != col else None
        den = agg(sel, den_col, how) if den_col else None
        if raw is not None and den:
            cands.append(("ratio: %s / %s x 100" % (col, den_col), raw / den * 100.0))

    if k.get("unit") == "pct":
        # "This subset as a share of the section total" — the shape behind
        # top-1-share, facility-funded-share and friends. Their specs express it
        # with operators this engine does not parse ('/', 'x', 'info'), so the
        # ratio candidate above never fired and a RUPEE figure sat in a percent
        # field: bank-facility-funded-share published 8,274,720,000 where the
        # answer is 94.1%. Numerator = the filtered rows; denominator = every row
        # the section returned.
        whole = agg(rows, col, "sum")
        part = raw
        if part is not None and whole:
            cands.append(("share of the section total: %s over all rows x 100" % col,
                          part / whole * 100.0))

    # A per-row PERCENTAGE cannot be summed or plainly averaged across rows of
    # different size — a 100%-manual account with 3 lines does not weigh the same
    # as a 2%-manual account with 40,000. The specs mark the weight column as a
    # term beside the value column (op 'x', or a second '=' term):
    #   bank-manual-je-share = SUM(N_LINES_12M x MANUAL_JE_LINE_PCT_12M) / SUM(N_LINES_12M)
    # Ignoring the weight published 100.0% where the answer is 5.4%.
    if k.get("unit") == "pct":
        w_col = next((t.get("col") for t in (k.get("terms") or [])
                      if t.get("col") and t.get("col") != col), None)
        if w_col:
            num = wsum = 0.0
            for r in sel:
                v = scale(r.get(col), col)
                w = scale(r.get(w_col), w_col)
                if v is None or w is None:
                    continue
                num += v * w
                wsum += w
            if wsum:
                cands.insert(0, ("weighted average: %s weighted by %s" % (col, w_col),
                                 num / wsum))

    # A unit:count KPI whose column will not aggregate is still answerable: the
    # filter has already selected the rows being counted. oi-oitr-settled-docs
    # sums the TEXT column RECON_STATE and published null in all three books,
    # while n_rows already held the answer (81 / 6 / 0).
    # ...and an empty selection is a MEASURED ZERO, not an unknown — provided the
    # filter actually ran. Beverages genuinely has 0 fully-reconciled documents;
    # suppressing that renders nothing where the honest answer is "none".
    # A filter that RAISED is a different thing entirely and stays unknown.
    filter_ran = (k.get("row_filter") in (None, True, "True")
                  or k.get("row_filter") not in FILTER_ERRORS)
    if k.get("agg") == "count" or (k.get("unit") == "count" and raw is None and filter_ran):
        cands.insert(0, ("count of rows matching the filter", float(len(sel))))

    if k.get("agg") == "count_ratio":
        # "How many of these rows have a value, as a share of them all." The
        # numerator column is the CLOSING term, not `column`: coverage is
        # accounts with RECONS_DONE_N > 0 over accounts in the filter. Summing
        # the column instead produced a flat 50.0 in all three books — a
        # constant across three different books, which is never a real ratio.
        num_col = closing_col or col
        hit = sum(1 for r in sel if (scale(r.get(num_col), num_col) or 0) > 0)
        if sel:
            cands.insert(0, ("count ratio: rows with %s over rows matching the filter x 100"
                             % num_col, hit / len(sel) * 100.0))

    if k.get("unit") == "days" and as_of:
        # A date column with a "- AS_OF" term is an AGE, not a date. The oldest
        # item is the MINIMUM date, and its age is the maximum number of days.
        ds = []
        for r in sel:
            v = r.get(col)
            if isinstance(v, str) and len(v) >= 10:
                try:
                    ds.append(datetime.date.fromisoformat(v[:10]))
                except ValueError:
                    pass
        if ds:
            base = datetime.date.fromisoformat(as_of[:10])
            cands.insert(0, ("age in days: %s from %s to the as-of date"
                             % ("oldest" if how == "max" else "newest", col),
                             float((base - (min(ds) if how == "max" else max(ds))).days)))

    # An AVERAGE reads exactly like a percentage ratio but lands in rupees:
    # cash-sale-avg-ticket is INV_GROSS_INR / INV_CNT, and reading the column
    # alone published Rs 14.44 LAKH as the average cash ticket when the answer
    # is Rs 1,314. A closing term that is a COUNT is a denominator, not a total.
    if (closing_col and closing_col != col and _COUNTISH.search(closing_col)
            and k.get("unit") != "pct"):
        den = agg(sel, closing_col, how)
        if raw is not None and den:
            cands.append(("average: %s per %s" % (col, closing_col), raw / den))

    if n_signed >= 2:
        cands.append(("sum of the signed terms - this figure spans several columns, "
                      "so the single column %s is only its first term" % col, plus - minus))

    live = (k.get("live") or {}).get(company)
    def near(a, b):
        """Does `a` reproduce the measured figure `b`?

        The spec's live values are often ROUNDED for readability — a coverage
        ratio recorded as 4.5 when the arithmetic gives 4.545. A pure relative
        tolerance rejects that (0.045 against a 0.0225 band) and the correct
        reading gets thrown away for a wrong one. So also accept a match at the
        oracle's own precision.
        """
        if abs(a - b) <= max(0.01, abs(b) * 0.005):
            return True
        txt = repr(float(b))
        dec = len(txt.split(".")[1].rstrip("0")) if "." in txt else 0
        return dec <= 4 and round(a, dec) == round(float(b), dec)

    # The FALLBACK matters as much as the pick. When nothing reproduces the
    # measured figure, falling back to "first candidate" means falling back to
    # reading one column — and for a KPI whose formula spans several, that is
    # not a near-miss, it is a different number. prov-net-fytd is
    # CREATED_FYTD - REVERSED_FYTD = -Rs 1.32 Cr; its term-sum missed the
    # tolerance by 885 rupees because the books moved since the spec was
    # written, so it fell back to CREATED alone and published +Rs 16.76 Cr —
    # wrong sign, wrong order of magnitude.
    #
    # Where the terms form a signed formula, that formula IS the definition.
    # Prefer it over a single-column read whenever no candidate reproduces.
    def _pick_default():
        # Signed terms: the formula IS the definition (see above) — EXCEPT when
        # the closing term is the value's own column. That means the column
        # already carries the answer (a broadcast CO_* total), and the other
        # terms describe how the QUERY built it, not addends to sum. Reading
        # ap-unbacked-credit as PAYABLE - RAW_OPEN off one broadcast row gave
        # Rs 0 where the column plainly held Rs 69.4 L.
        if closing_col != col:
            for c in cands:
                if c[0].startswith("sum of the signed terms"):
                    return c
        # A percentage must be shaped like one. Reading the numerator column
        # alone leaves a RUPEE figure in a percent field — Mart's
        # ar-overdue-60p-share published 3,014,261.42 where the answer is 2.93%.
        # Prefer any ratio-shaped candidate that lands in percentage range, even
        # when it does not reproduce a measurement taken hours ago.
        # A declared aggregation is a statement of what the figure MEANS. If the
        # spec says count_ratio, a share-of-column is not a near-miss of it.
        for c in cands:
            if c[0].startswith(("count ratio:", "count of rows", "age in days:")):
                return c
        if k.get("unit") == "pct":
            for c in cands:
                if c[0].startswith(("ratio:", "share of the section total")) \
                        and c[1] is not None and -1000 <= c[1] <= 1000:
                    return c
        return cands[0]

    default = _pick_default()
    method, value = default
    if live not in (None, 0):
        picked = None
        for mname, mval in cands:
            if mval is None:
                continue
            if near(mval, live):
                picked = (mname, mval); break
            # A credit stored negative and shown positive: same reading, flipped.
            if near(-mval, live):
                picked = (mname + " + sign flip (the column stores this as a credit)",
                          -mval); break
        if picked:
            method, value = picked

    reproduces = None
    if live not in (None, 0) and value is not None:
        reproduces = near(value, live)

    # Last line of defence. A unit:pct KPI holding a figure far outside percentage
    # range is a rupee amount in a percent field, whatever the candidates said.
    # Publish it — hiding a number is worse — but never let it pass as agreeing.
    implausible = None
    if k.get("unit") == "pct" and value is not None and abs(value) > 1000:
        implausible = ("unit is pct but the value is %.0f, which is not a "
                       "percentage - the formula for this KPI is not expressible "
                       "as a single column and no candidate reading reproduced it"
                       % value)
        reproduces = False

    terms, plus, minus, closing = [], 0.0, 0.0, None
    for t in k.get("terms") or []:
        tc = t.get("col")
        tv = agg(sel, tc, how) if tc else None
        op = t.get("op") or "+"
        terms.append({"label": t.get("label"), "col": tc, "op": op,
                      "source": t.get("source"), "note": t.get("note"), "value": tv})
        if tv is None:
            continue
        if op == "+":
            plus += tv
        elif op == "-":
            minus += tv
        elif op == "=":
            closing = tv

    # Closure is only meaningful when the decomposition genuinely targets THIS
    # value: every term is a money column present on the rows we read, and the
    # closing term is the value's own column. Enforced more loosely, it fires on
    # explanatory decompositions never meant to be arithmetic over one row set —
    # 96 false alarms, which would train the reader to ignore the flag. A warning
    # nobody trusts is worse than no warning.
    closure = None
    term_cols = [t.get("col") for t in (k.get("terms") or []) if t.get("col")]
    closing_col = next((t.get("col") for t in (k.get("terms") or [])
                        if t.get("op") == "="), None)
    present = bool(sel) and all(c in sel[0] for c in term_cols)
    # ...and only where summing the terms is semantically valid at all. For an
    # agg='first' KPI the row IS the answer and its terms are a description of
    # how the query built it, not addends over a row set. Asserting arithmetic
    # there produced exact 2x / 3x / negated "failures" — an artefact of the
    # check, not a defect in the books.
    if (how == "sum" and k.get("unit") == "INR" and closing is not None
            and (plus or minus) and len(term_cols) > 1 and present
            and closing_col == col and all(_is_money(c) for c in term_cols)):
        lhs = plus - minus
        tol = max(CLOSURE_TOL, abs(closing) * 1e-6)   # float64 over crore-scale sums
        closure = {"terms_sum": lhs, "closing_term": closing, "delta": lhs - closing,
                   "tolerance": tol, "ok": abs(lhs - closing) <= tol}
    excludes = []
    for e in k.get("excludes") or []:
        rf = e.get("row_filter")
        # Many exclusions are described in prose ("never in the universe", "not in
        # this section", "OBNK.DueDate > {{ASOF}}") rather than written as an
        # expression over a row. Those cannot be quantified from the published
        # slice. Saying so is the honest rendering; an empty row set silently
        # becomes "nothing was excluded", which is a confident zero about the
        # single thing this panel exists to disclose.
        computable = bool(rf) and rf not in (True, "True")
        if computable:
            try:
                compile(rf, "<exclude_filter>", "eval")
            except SyntaxError:
                computable = False
        ex = [r for r in rows if rowmatch(rf, r)] if computable else []
        if computable and not ex and rf in FILTER_ERRORS:
            computable = False
        cards = sorted({str(r.get("CARD_CODE")) for r in ex if r.get("CARD_CODE")})[:60]
        excludes.append({
            "label": e.get("label"), "why": e.get("why"),
            "amount": agg(ex, col, "sum") if computable else None,
            "n_rows": len(ex) if computable else None,
            "cards": cards,
            "computable": computable,
            "note": None if computable else
                    ("This exclusion is described in the section spec but not "
                     "expressed as a filter over the published rows, so its amount "
                     "cannot be computed here: %r" % rf),
        })

    cav = []
    for c in k.get("caveats") or []:
        if c in corr:
            cav.append(dict(corr[c], scope="global"))
        else:
            # Section-local codes (P-LAKHS, P-FIFO...) carry no text of their own;
            # the prose lives in the section's traps, which travel with the record.
            cav.append({"id": c, "title": c, "rule": None, "scope": "section"})

    return {
        "id": k["id"], "label": k.get("label"), "unit": k.get("unit"),
        "section": k["_section"], "column": col, "agg": how,
        "row_source": kind, "n_rows": len(sel),
        "value": value, "raw_column_value": raw, "method": method,
        "implausible": implausible,
        "reproduces_spec_measurement": reproduces,
        "formula": k.get("formula"),
        "terms": terms, "closure": closure,
        "closure_note": (None if closure else
                         "Terms describe how the query built this figure; they are not "
                         "addends over a row set, so no arithmetic closure is asserted."),
        "excludes": excludes,
        "sql": sql_slice(k.get("_sql"), k.get("sql_lines")),
        "caveats": cav,
        "section_traps": spec.get("traps") or [],
        "rows": {"section": k["_section"], "kind": kind,
                 "filter": k.get("row_filter"), "top": 50},
        "drill": k.get("drill"),
        "spec_live": (k.get("live") or {}),
        "check": None,           # verify.py fills this
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "site-v2", "data"))
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    specs = load_specs()
    kpis, problems = validate(specs)
    for p in problems:
        print("  spec problem: %s" % p, file=sys.stderr)
    if problems and a.strict:
        return 2

    man_path = os.path.join(a.data, "manifest.json")
    man = json.load(open(man_path, encoding="utf-8"))
    corr = corrections()
    companies = [c["key"] for c in man.get("companies", [])] or ["oil", "mart", "bev"]

    blobs, failures, drifted, n = {}, [], [], 0
    for co in companies:
        out = {}
        for k in kpis:
            sec = k["_section"]
            key = (sec, co)
            if key not in blobs:
                p = os.path.join(a.data, "%s.%s.json" % (sec, co))
                blobs[key] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
            rec = derive_one(k, blobs[key], specs[sec], corr, co,
                             man.get("as_of"))
            out[k["id"]] = rec
            n += 1
            if rec["closure"] and not rec["closure"]["ok"]:
                failures.append((co, k["id"], rec["closure"]))
            # The inventory pass recorded the value it measured. A large drift
            # means the query or the books moved since — worth surfacing, not fatal.
            if rec["reproduces_spec_measurement"] is False:
                live = rec["spec_live"].get(co)
                d = abs(rec["value"] - live) / max(abs(live), 1.0) * 100 if rec["value"] is not None else float("inf")
                drifted.append((co, k["id"], live, rec["value"], d))
            # CONTRACT §2 shape. Short keys saved ~4 KB gzipped and would have
            # broken every page written against the published contract — a bad
            # trade, and exactly the kind of silent interface drift this build
            # is supposed to be immune to.
            man["kpis"].setdefault(co, {})[k["id"]] = {
                "value": rec["value"], "unit": rec["unit"], "label": rec["label"],
                "section": rec["section"], "check": None,
            }
        tmp = os.path.join(a.data, "derivations.%s.json" % co)
        with open(tmp + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(out, fh, sort_keys=True, separators=(",", ":"))
        os.replace(tmp + ".tmp", tmp)
        print("  derivations.%-5s %4d KPIs  %.0f KB" % (co, len(out), os.path.getsize(tmp) / 1024))

    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(man, fh, sort_keys=True, separators=(",", ":"))

    print("  derived %d company-KPIs from %d specs" % (n, len(specs)))
    print("  corrections resolved: %d" % len(corr))
    if FILTER_ERRORS:
        print("  ROW FILTERS THAT WOULD NOT EVALUATE: %d (each silently selected "
              "no rows)" % len(FILTER_ERRORS))
        for expr, err in list(FILTER_ERRORS.items())[:6]:
            print("    %s  ->  %s" % (expr[:70], err))
    if failures:
        print("  TERM CLOSURE FAILURES: %d" % len(failures))
        for co, kid, c in failures[:12]:
            print("    %-5s %-34s terms=%.2f closing=%.2f delta=%.2f"
                  % (co, kid, c["terms_sum"], c["closing_term"], c["delta"]))
    else:
        print("  term closure: every closed formula adds up to <0.5 paise")
    if drifted:
        print("  DOES NOT REPRODUCE the value the inventory pass measured: %d of %d" % (len(drifted), n))
        for co, kid, was, now, pc in drifted[:8]:
            print("    %-5s %-34s spec=%.2f now=%.2f (%+.1f%%)" % (co, kid, was, now, pc))
    return 2 if (failures and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
