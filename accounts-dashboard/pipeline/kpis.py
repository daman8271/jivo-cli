#!/usr/bin/env python3
"""kpis.py — the KPI registry. Data, not logic.

Loads specs/*.json (one per section, written by the inventory pass), validates
them hard, and exposes them. A bad spec fails loudly and specifically here
rather than producing a quietly wrong number three files later.
"""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPECS = os.path.join(ROOT, "specs")
SQL = os.path.join(HERE, "sql")

_UNIT_L = re.compile(r"_L$", re.I)
_UNIT_CR = re.compile(r"_CR$", re.I)


def scale(v, col):
    """Column NAME carries the unit. Anchored to the end on purpose:
    OUTSTANDING_CR_L contains '_CR' but is LAKHS — a substring test is 100x wrong."""
    if v in (None, ""):
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    if _UNIT_CR.search(col or ""):
        return v * 1e7
    if _UNIT_L.search(col or ""):
        return v * 1e5
    return v


# The specs legitimately write filters like "float(r.get('X') or 0) > 0".
# Evaluating with __builtins__ stripped made every one of those raise NameError,
# which a bare except turned into False — so nine KPIs silently matched ZERO rows
# and published as null with no error anywhere. Whitelist the handful of pure
# builtins a row filter can reasonably need; nothing that can open, import or exec.
_SAFE_BUILTINS = {
    "float": float, "int": int, "str": str, "bool": bool, "abs": abs,
    "len": len, "min": min, "max": max, "round": round, "sum": sum,
    "any": any, "all": all, "sorted": sorted, "True": True, "False": False,
    "None": None,
}

# Filters that failed to evaluate, so the caller can REPORT them instead of
# silently treating "the expression broke" as "the row does not match".
FILTER_ERRORS = {}


def rowmatch(expr, row):
    """Evaluate a spec's row_filter against one row.

    A filter that raises is recorded, not swallowed: silently returning False
    turns a broken expression into an empty result set, which looks exactly like
    a legitimately empty section.
    """
    if not expr or expr is True or expr == "True":
        return True
    try:
        return bool(eval(expr, {"__builtins__": _SAFE_BUILTINS}, {"r": row}))
    except Exception as e:
        FILTER_ERRORS[expr] = "%s: %s" % (type(e).__name__, e)
        return False


def resolve_rows(kpi, blob):
    """Which row set does this KPI read — summary or detail?

    The specs carry no explicit field for it (an omission in the spec template),
    so infer it from the data: whichever set actually carries the KPI's column.
    Preferring summary keeps the roll-up grain where both would work.
    """
    col = kpi.get("column")
    for kind in ("summary", "detail"):
        rows = blob.get(kind) or []
        if rows and col in rows[0]:
            return kind, rows
    return "summary", (blob.get("summary") or [])


def sql_for(section, lines):
    """Main query, or its -detail companion when the line range only fits there."""
    main = os.path.join(SQL, "%s.sql" % section)
    det = os.path.join(SQL, "%s-detail.sql" % section)
    if lines and len(lines) == 2:
        for path in (main, det):
            if os.path.exists(path):
                n = len(open(path, encoding="utf-8").read().splitlines())
                if 1 <= lines[0] <= lines[1] <= n:
                    return path
    return main if os.path.exists(main) else (det if os.path.exists(det) else None)


def load_specs(strict=True):
    """Load every spec, keyed by its declared section.

    Keyed by spec["section"], NOT by filename — so a spec that declares the
    wrong section silently REPLACES another and its KPIs vanish from the board
    with no error anywhere. That happened: bank-reco.json shipped declaring
    section "bank-accounts" and took the real bank-accounts spec's place. A
    board about catching quietly-wrong numbers must not lose a whole section
    quietly, so a collision is now a hard failure.
    """
    out, seen = {}, {}
    for path in sorted(glob.glob(os.path.join(SPECS, "*.json"))):
        base = os.path.basename(path)
        if base.startswith("_"):
            continue
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
        sec = spec.get("section")
        if not sec:
            raise ValueError("%s declares no section" % base)
        if sec in seen:
            msg = ("two specs both declare section %r: %s and %s. One would "
                   "silently replace the other." % (sec, seen[sec], base))
            if strict:
                raise ValueError(msg)
            print("  SPEC COLLISION: %s" % msg)
            continue
        stem = os.path.splitext(base)[0]
        if sec != stem:
            print("  NOTE: %s declares section %r (filename says %r)" % (base, sec, stem))
        seen[sec] = base
        spec["_path"] = path
        out[sec] = spec
    return out


def validate(specs):
    """Returns (kpis, problems). Never raises — the caller decides whether a
    problem is fatal, because a single malformed KPI must not cost the board
    its other ninety."""
    kpis, problems, seen = [], [], {}
    for sec, spec in sorted(specs.items()):
        for k in spec.get("kpis", []):
            kid = k.get("id")
            if not kid:
                problems.append("%s: a KPI has no id" % sec); continue
            if kid in seen:
                problems.append("duplicate KPI id %r in %s and %s" % (kid, seen[kid], sec)); continue
            seen[kid] = sec
            if not k.get("column"):
                problems.append("%s/%s: no column" % (sec, kid))
            rf = k.get("row_filter")
            if rf and rf not in (True, "True"):
                try:
                    compile(rf, "<row_filter>", "eval")
                except SyntaxError:
                    # Some specs describe the row set in prose ("detail row (event
                    # grain)") instead of as an expression. resolve_rows() already
                    # picks summary-vs-detail from which one carries the column, so
                    # the safe reading is "every row of that set". Degrade to that
                    # and SAY SO — losing a whole KPI over one prose field would be
                    # worse, and pretending it filtered would be worse still.
                    problems.append("%s/%s: row_filter is prose, not an expression "
                                    "(%r) - treating as 'every row of the resolved "
                                    "row set'" % (sec, kid, rf))
                    k["row_filter"] = "True"
                    k["row_filter_degraded"] = True
            ln = k.get("sql_lines") or []
            if len(ln) == 2:
                src = sql_for(sec, ln)
                if not src:
                    problems.append("%s/%s: no SQL file for the section" % (sec, kid))
                else:
                    n = len(open(src, encoding="utf-8").read().splitlines())
                    if not (1 <= ln[0] <= ln[1] <= n):
                        problems.append("%s/%s: sql_lines %s fit neither %s.sql nor %s-detail.sql"
                                        % (sec, kid, ln, sec, sec))
                    k["_sql"] = os.path.relpath(src, ROOT)
            k["_section"] = sec
            kpis.append(k)
    return kpis, problems


if __name__ == "__main__":
    s = load_specs()
    k, p = validate(s)
    print("specs: %d   KPIs: %d   problems: %d" % (len(s), len(k), len(p)))
    for x in p[:30]:
        print("  !", x)
