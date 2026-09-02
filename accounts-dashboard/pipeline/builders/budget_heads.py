#!/usr/bin/env python3
"""budget-heads — JIVO's expense budget register, by EFFECTIVE month.

Not SAP. This section's source is JSAP (JIVO's internal ops platform), whose
budget module is the only place that carries three things SAP does not:

  * the EFFECTIVE month an expense belongs to (SAP only knows its posting date),
  * the budget head / sub-head it was approved against,
  * the approval trail (verified / pending / rejected).

Two things about it were verified live on 2026-08-22 and both change the reading:

  1. JSAP's DocEntry points at SAP **DRAFTS** (ODRF), not posted documents.
     ODRF 46357 = FACEBOOK INDIA Rs 3,234 (matches JSAP); OPCH 46357 =
     FRYSTAL PET Rs 4.19 L (a different document entirely). So this register is
     budget-APPROVED spend at draft stage, NOT the posted books. Never join its
     DocEntry to OPCH/ORPC, and never call these figures "booked".
  2. There is NO budget allocation figure for FY 2026-27 anywhere. The V2
     allocation tables (bud.BudgetMonthlyAllocations) stop at Mar-2026 and hold
     test values (Rs 6,000 Cr against NPD1); Current_month_Budget is 0 on 6,224
     of 6,225 Apr-Jul lines; SAP's own OBGT has 4 accounts for FY26-27. So
     budget-vs-actual variance cannot be computed, and this section does not
     pretend to. It reports consumption.

Sign convention, verified against the drafts: ObjType 19 (A/P credit memo)
credits the expense GL, so it is subtracted. ObjType 14 (A/R credit memo) is how
JIVO issues free samples and promotional discount - it DEBITS sampling/discount
expense, so it counts as spend.

Reachability: JSAP moved with the Aug-2026 vendor migration. The old
103.89.45.75:5001 is dead from every path including office PCs; the live host is
138.252.101.118:5001 and its database (jsaplive3) is on the same box, TCP 1433,
open from home and the VPS. Read-only: dsr's SELECT-only guard, rolled back.
"""
import json
import os
import subprocess

SECTION_ID = "budget-heads"
# JSAP is a second system on a second box. If it is unreachable the rest of the
# board (SAP HANA) is still correct and must still publish.
OPTIONAL = True

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(PIPELINE_DIR))
# The repo ships a darwin/arm64 `dsr`; on Linux (the VPS runs the 2-minute
# loop) that dies with "Exec format error", which is exactly how this board
# silently froze for five hours on 2026-08-22. Pick per OS.
_DSR_DEFAULT = os.path.join(REPO, "dsr-cli",
                            "dsr-linux" if os.uname().sysname == "Linux" else "dsr")
DSR = os.environ.get("DSR_BIN", _DSR_DEFAULT)
ARY_ENV = os.environ.get("ARY_ENV_FILE", os.path.join(REPO, "connections", "ary.env"))
JSAP_DB = os.environ.get("JSAP_DB", "jsaplive3")

# JSAP branch -> dashboard company key. Mart never entered the budget process.
BRANCH_TO_CO = {"OIL": "oil", "BEVERAGE": "bev"}

MON = {"01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY", "06": "JUN",
       "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC"}


def _env():
    """ary.env is written for bash and single-quotes its values; strip them or
    the host reads as "'138.252.101.118'" and fails as a DNS lookup."""
    env = dict(os.environ)
    with open(ARY_ENV) as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip().strip("'").strip('"')
    return env


def _query(sql, timeout=120):
    p = subprocess.run([DSR, "query", "--db", JSAP_DB, "--json", "--quiet", sql],
                       capture_output=True, text=True, timeout=timeout, env=_env())
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip().splitlines()[0][:300])
    out = p.stdout.strip()
    return json.loads(out) if out else []


def fy_months(asof):
    """Every month of the financial year containing `asof`, up to `asof`, as
    JSAP's 'MM-YYYY'. April start - JIVO's books run Apr-Mar."""
    y, m = int(asof[:4]), int(asof[5:7])
    fy = y if m >= 4 else y - 1
    out = []
    for i in range(12):
        mm = 4 + i
        yy = fy + (mm - 1) // 12
        mm = (mm - 1) % 12 + 1
        if (yy, mm) > (y, m):
            break
        out.append("%02d-%d" % (mm, yy))
    return out


# AMOUNT is the line's net-of-GST expense value. Rs -> lakhs here, matching the
# _L column convention the page scales by.
_NET = "SUM(CASE WHEN ObjType = '19' THEN -AMOUNT ELSE AMOUNT END) / 100000.0"
_MONTH_KEY = "RIGHT(EFFECTMONTH, 4) + '-' + LEFT(EFFECTMONTH, 2)"
_MONTH_LABEL = ("CASE LEFT(EFFECTMONTH, 2) "
                + " ".join("WHEN '%s' THEN '%s'" % (k, v) for k, v in sorted(MON.items()))
                + " ELSE LEFT(EFFECTMONTH, 3) END + '-' + RIGHT(EFFECTMONTH, 2)")


def _summary_sql(months):
    inlist = ", ".join("'%s'" % m for m in months)
    return """
SELECT  t.Branch                                          AS BRANCH,
        {mk}                                              AS MONTH_KEY,
        {ml}                                              AS MONTH_LABEL,
        t.BUDGET                                          AS HEAD_CODE,
        COALESCE(NULLIF(b.budgetName, ''), t.BUDGET)      AS HEAD,
        COUNT(*)                                          AS LINES_CNT,
        COUNT(DISTINCT CONCAT(t.ObjType, '-', t.DocEntry)) AS DOCS_CNT,
        COUNT(DISTINCT t.AcctCode)                        AS GLS_CNT,
        CAST({net} AS DECIMAL(18,2))                      AS NET_L,
        CAST(SUM(CASE WHEN t.ObjType = '18' THEN t.AMOUNT ELSE 0 END)/100000.0 AS DECIMAL(18,2)) AS AP_INVOICE_L,
        CAST(SUM(CASE WHEN t.ObjType = '46' THEN t.AMOUNT ELSE 0 END)/100000.0 AS DECIMAL(18,2)) AS PAYMENT_L,
        CAST(SUM(CASE WHEN t.ObjType = '28' THEN t.AMOUNT ELSE 0 END)/100000.0 AS DECIMAL(18,2)) AS JOURNAL_L,
        CAST(SUM(CASE WHEN t.ObjType = '14' THEN t.AMOUNT ELSE 0 END)/100000.0 AS DECIMAL(18,2)) AS SAMPLING_L,
        CAST(SUM(CASE WHEN t.ObjType = '19' THEN t.AMOUNT ELSE 0 END)/100000.0 AS DECIMAL(18,2)) AS CREDITED_L,
        CAST(SUM(CASE WHEN t.ProcesStat = 'P' THEN t.AMOUNT ELSE 0 END)/100000.0 AS DECIMAL(18,2)) AS PENDING_L,
        CAST(SUM(CASE WHEN t.ApprovedStatus = 'R' THEN t.AMOUNT ELSE 0 END)/100000.0 AS DECIMAL(18,2)) AS REJECTED_L
FROM    bud.jsBudgetTable t
LEFT JOIN dbo.jsBudget b
       ON b.budgetId = t.BUDGET
      AND b.company  = CASE t.Branch WHEN 'OIL' THEN 1 WHEN 'BEVERAGE' THEN 2 ELSE 0 END
WHERE   t.EFFECTMONTH IN ({inlist})
GROUP BY t.Branch, {mk}, {ml}, t.BUDGET, COALESCE(NULLIF(b.budgetName, ''), t.BUDGET)
ORDER BY 1, 2, 9 DESC
""".format(mk=_MONTH_KEY, ml=_MONTH_LABEL, net=_NET, inlist=inlist)


def _detail_sql(months):
    inlist = ", ".join("'%s'" % m for m in months)
    return """
SELECT  t.Branch                                          AS BRANCH,
        {mk}                                              AS MONTH_KEY,
        {ml}                                              AS MONTH_LABEL,
        COALESCE(NULLIF(b.budgetName, ''), t.BUDGET)      AS HEAD,
        COALESCE(NULLIF(s.sBudgetName, ''), NULLIF(t.SUB_BUDGET, ''), '(no sub-head)') AS SUB_HEAD,
        t.AcctCode                                        AS ACCT_CODE,
        t.AcctName                                        AS ACCT_NAME,
        COUNT(*)                                          AS LINES_CNT,
        COUNT(DISTINCT NULLIF(t.CardCode, ''))            AS PARTIES_CNT,
        CAST({net} AS DECIMAL(18,2))                      AS NET_L,
        CAST(SUM(CASE WHEN t.ProcesStat = 'P' THEN t.AMOUNT ELSE 0 END)/100000.0 AS DECIMAL(18,2)) AS PENDING_L
FROM    bud.jsBudgetTable t
LEFT JOIN dbo.jsBudget b
       ON b.budgetId = t.BUDGET
      AND b.company  = CASE t.Branch WHEN 'OIL' THEN 1 WHEN 'BEVERAGE' THEN 2 ELSE 0 END
LEFT JOIN dbo.jsSubBudget s
       ON s.sBudgetId = t.SUB_BUDGET
      AND s.company   = CASE t.Branch WHEN 'OIL' THEN 1 WHEN 'BEVERAGE' THEN 2 ELSE 0 END
WHERE   t.EFFECTMONTH IN ({inlist})
GROUP BY t.Branch, {mk}, {ml},
         COALESCE(NULLIF(b.budgetName, ''), t.BUDGET),
         COALESCE(NULLIF(s.sBudgetName, ''), NULLIF(t.SUB_BUDGET, ''), '(no sub-head)'),
         t.AcctCode, t.AcctName
ORDER BY 1, 2, 10 DESC
""".format(mk=_MONTH_KEY, ml=_MONTH_LABEL, net=_NET, inlist=inlist)


def _split(rows, coerce):
    """Rows come back branch-tagged; the page asks per company."""
    out = {k: [] for k in ("oil", "mart", "bev")}
    for r in rows:
        co = BRANCH_TO_CO.get((r.get("BRANCH") or "").strip().upper())
        if not co:
            continue
        # coerce() is build_data's TSV normaliser: it expects text and decides
        # per column what is a number and what is an identifier (ACCT_CODE must
        # stay text). MSSQL --json hands back real ints and decimal STRINGS, so
        # everything goes through str() first and one rule set governs both
        # sources.
        out[co].append({k: ("" if v is None else str(v))
                        for k, v in r.items() if k != "BRANCH"})
    return {k: coerce(v) for k, v in out.items()}


def build(asof, only_companies, coerce):
    """Returns the same payload shape run_section() produces for a .sql section."""
    payload = {"summary": {}, "detail": {}, "errors": {}, "timing": {}}
    months = fy_months(asof)
    if not months:
        payload["errors"]["summary.jsap"] = "no months in the financial year up to %s" % asof
        return payload
    for kind, sql in (("summary", _summary_sql(months)), ("detail", _detail_sql(months))):
        try:
            rows = _query(sql)
        except Exception as e:
            msg = str(e).splitlines()[0][:300]
            # NOT the word "FAILED": live-refresh.sh greps for it and refuses to
            # publish the whole board. This section is optional by design.
            print("    %-9s %-6s UNAVAILABLE  %s" % (kind, "jsap", msg))
            payload["errors"]["%s.jsap" % kind] = msg
            continue
        split = _split(rows, coerce)
        if only_companies:
            split = {k: v for k, v in split.items() if k in only_companies}
        payload[kind] = split
        for co, rs in sorted(split.items()):
            print("    %-9s %-6s %6d rows  (jsap)" % (kind, co, len(rs)))
    payload["meta"] = {"months": months, "source": "JSAP %s @ %s" % (JSAP_DB, "138.252.101.118")}
    return payload
