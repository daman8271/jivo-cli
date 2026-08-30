#!/usr/bin/env python3
"""
JIVO Oil — THE PROJECTION. Compute next month's demand instead of hand-making it.

Built 2026-08-29 to Daman's spec in reference/PLANNING-MODEL.md §1:

    "built from last month's demand, last month's data, and market demand...
     go to the SAME PERIOD LAST YEAR, measure what was selling normally before
     it, and measure how much it ACTUALLY rose. The uplift is a measured
     multiplier from history, never a guess."

So the method is deliberately three lines:

    base(sku)      = mean litres of the trailing 3 months
    season(group)  = target month LAST YEAR / that year's own trailing-3 baseline
    projection     = base x season

TWO METHODS, because with one September in the data the method choice moves the
answer by ~9%, and pretending otherwise would be false precision:

  A  MOMENTUM   base = trailing 3 months; season = target/trailing-3, same months
                last year. Follows where the business is heading right now.
  B  LEVEL      base = this year's own monthly mean so far; season = target month
                over that whole reference year's mean. Ignores momentum, immune to
                a spiky trailing window.

A is sensitive to what happens to sit in the trailing window (a hot July drags the
baseline up and makes September look weak). B is sensitive to nothing recent. The
honest output is the RANGE they bracket, not either number on its own.

with two guards that matter more than the formula:

  * CREDIBILITY. One September is one observation. A category with 2,000 L of
    history does not get to claim a 3x seasonal swing. Each group's multiplier is
    shrunk toward the all-item multiplier by w = V/(V+K) on its baseline volume,
    so thin categories inherit the market's shape instead of inventing their own.
  * PARTIAL MONTH. The current month is incomplete on the day this runs. It is
    scaled up by days_in_month/days_elapsed before it is used as base, never
    taken raw — an unscaled 29-of-31 August silently forecasts a 6% collapse.

UNITS: litres throughout (C-0050 sale-side, 1 T = 1,000 L). Quantities out of
INV1/RIN1 are PIECES (C-0001) and are converted with the settled name parser.
SCOPE: JIVO_OIL_HANADB finished goods. Intercompany (C-0005) is INCLUDED by
default and reported separately — Oil->Mart is oil the factory still has to make.
Grouping is SAP's own U_Sub_Group (C-0003), never the item name.

Read-only. Writes a CSV.
"""
import argparse, calendar, collections, csv, datetime, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan_units import pack_litres

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
ENV  = os.path.join(REPO, "connections", "hana-office-bridge.env")
CO   = "JIVO_OIL_HANADB"

# C-0005 — the 23 group CardCodes; these nine are Oil's.
INTERCO = ("CUSTA000001","CUSTA000002","CUSTA000003","CUSTA000004","CUSTA000606",
           "CUSTA000827","CUSTA000906","CUSTA001099","CUSTA001113")

CREDIBILITY_K = 50_000.0   # litres of baseline a group needs to own half its multiplier
BASE_MONTHS   = 3

DAILY_SQL = """
SELECT TO_VARCHAR(T0."DocDate",'YYYY-MM-DD') AS "DAY", T1."ItemCode" AS "ItemCode",
       I."ItemName" AS "ItemName", SUM(T1."Quantity") AS PCS
FROM {co}.OINV T0 JOIN {co}.INV1 T1 ON T1."DocEntry"=T0."DocEntry"
JOIN {co}.OITM I ON I."ItemCode"=T1."ItemCode"
JOIN {co}.OITB G ON G."ItmsGrpCod"=I."ItmsGrpCod"
WHERE T0."CANCELED"='N' AND G."ItmsGrpNam"='FINISHED'
  AND T0."DocDate">='{a}' AND T0."DocDate"<='{b}'
  {ic}
GROUP BY TO_VARCHAR(T0."DocDate",'YYYY-MM-DD'), T1."ItemCode", I."ItemName"
"""

SALES_SQL = """
SELECT M."MTH", M."ItemCode", I."ItemName", I."U_TYPE", I."U_Sub_Group", M."INTERCO",
       SUM(M."QTY") AS PCS
FROM (
  SELECT TO_VARCHAR(T0."DocDate",'YYYY-MM') AS "MTH", T1."ItemCode" AS "ItemCode",
         CASE WHEN T0."CardCode" IN ({ic}) THEN 'Y' ELSE 'N' END AS "INTERCO",
         T1."Quantity" AS "QTY"
  FROM {co}.OINV T0 JOIN {co}.INV1 T1 ON T1."DocEntry"=T0."DocEntry"
  WHERE T0."CANCELED"='N' AND T0."DocDate">='{since}' AND T0."DocDate"<='{until}'
  UNION ALL
  SELECT TO_VARCHAR(T0."DocDate",'YYYY-MM'), T1."ItemCode",
         CASE WHEN T0."CardCode" IN ({ic}) THEN 'Y' ELSE 'N' END, -T1."Quantity"
  FROM {co}.ORIN T0 JOIN {co}.RIN1 T1 ON T1."DocEntry"=T0."DocEntry"
  WHERE T0."CANCELED"='N' AND T0."DocDate">='{since}' AND T0."DocDate"<='{until}'
) M
JOIN {co}.OITM I ON I."ItemCode"=M."ItemCode"
JOIN {co}.OITB G ON G."ItmsGrpCod"=I."ItmsGrpCod"
WHERE G."ItmsGrpNam"='FINISHED'
GROUP BY M."MTH", M."ItemCode", I."ItemName", I."U_TYPE", I."U_Sub_Group", M."INTERCO"
"""


def run_sql(sql, env):
    r = subprocess.run([HANA, "-env", env, "-csv", sql],
                       capture_output=True, text=True, timeout=600)
    if r.returncode:
        sys.exit(f"HANA read failed: {r.stderr[:400]}")
    return list(csv.DictReader(r.stdout.splitlines()))


def months_back(ym, n):
    y, m = int(ym[:4]), int(ym[5:7])
    out = []
    for _ in range(n):
        m -= 1
        if m == 0: y, m = y - 1, 12
        out.append(f"{y:04d}-{m:02d}")
    return list(reversed(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default="2026-09", help="month to project, YYYY-MM")
    ap.add_argument("--asof", default=None, help="today (YYYY-MM-DD); default real today")
    ap.add_argument("--env", default=ENV)
    ap.add_argument("--csv", default="out/forecast-sep.csv")
    ap.add_argument("--external-only", action="store_true",
                    help="exclude intercompany (market demand rather than factory load)")
    ap.add_argument("--event-days", default=None,
                    help="date ranges in the REFERENCE month that were a demand event "
                         "(festival / platform sale), e.g. 2025-09-22:2025-09-30. The "
                         "seasonal multiplier is then measured on event-free days only, "
                         "so a festival that has moved is not imported into the target "
                         "month. See reference/EVENT-CALENDAR.md.")
    ap.add_argument("--compare", default="out/plan-sep-FINAL2.csv",
                    help="the human plan to check against; '' to skip")
    a = ap.parse_args()

    today = (datetime.date.fromisoformat(a.asof) if a.asof else datetime.date.today())
    target = a.target
    ty, tm = int(target[:4]), int(target[5:7])
    last_year_target = f"{ty-1:04d}-{tm:02d}"

    base_months = months_back(target, BASE_MONTHS)            # e.g. 2026-06..08
    ly_base     = months_back(last_year_target, BASE_MONTHS)  # e.g. 2025-06..08
    ref_year    = [f"{ty-1:04d}-{i:02d}" for i in range(1, 13)]   # method B reference
    cur_year    = [f"{ty:04d}-{i:02d}" for i in range(1, tm)]     # method B base
    since = f"{ty-1:04d}-01-01"

    rows = run_sql(SALES_SQL.format(co=CO, since=since, until=today.isoformat(),
                                    ic=",".join(f"'{c}'" for c in INTERCO)), a.env)

    # ---- partial-month scale: the month we are standing in is not over yet
    cur = f"{today.year:04d}-{today.month:02d}"
    dim = calendar.monthrange(today.year, today.month)[1]
    part = dim / today.day if cur in base_months and today.day < dim else 1.0

    litres = {}
    def L(code, name):
        if code not in litres:
            litres[code] = pack_litres(name)[0]
        return litres[code]

    sku  = collections.defaultdict(lambda: collections.defaultdict(float))
    meta, unparsed = {}, collections.Counter()
    for r in rows:
        if a.external_only and r['INTERCO'] == 'Y':
            continue
        v = L(r['ItemCode'], r['ItemName'])
        if v is None:
            unparsed[r['ItemName']] += float(r['PCS']); continue
        q = float(r['PCS']) * v
        if r['MTH'] == cur: q *= part
        sku[r['ItemCode']][r['MTH']] += q
        meta[r['ItemCode']] = (r['ItemName'], r['U_TYPE'] or 'UNSET',
                               r['U_Sub_Group'] or 'UNSET')

    def total(months, pred=lambda c: True):
        t = 0.0
        for c, m in sku.items():
            if not pred(c): continue
            for k, v in m.items():
                if k not in months: continue
                t += ev_clean.get(c, v) if (k == last_year_target and ev_clean) else v
        return t

    # ---- strip a demand event out of the reference month, if one sat in it
    #      Festivals move ~3 weeks a year. Measuring "September" without asking WHERE
    #      the festival was imports last year's Navratri into a month that will not
    #      have it. This rebuilds the reference month as if every day ran at its own
    #      event-free rate, per SKU.
    ev_clean, ev_note = {}, ""
    if a.event_days:
        wins = []
        for win in a.event_days.split(","):
            x, y = win.split(":"); wins.append((x.strip(), y.strip()))
        ldim = calendar.monthrange(int(last_year_target[:4]), int(last_year_target[5:7]))[1]
        ma, mb = f"{last_year_target}-01", f"{last_year_target}-{ldim:02d}"
        drows = run_sql(DAILY_SQL.format(co=CO, a=ma, b=mb,
                        ic=("AND T0.\"CardCode\" NOT IN (" + ",".join(f"'{c}'" for c in INTERCO) + ")")
                           if a.external_only else ""), a.env)
        on, off, offd = collections.defaultdict(float), collections.defaultdict(float), set()
        for r in drows:
            v = L(r['ItemCode'], r['ItemName'])
            if v is None: continue
            q = float(r['PCS']) * v
            if any(x <= r['DAY'] <= y for x, y in wins): on[r['ItemCode']] += q
            else: off[r['ItemCode']] += q; offd.add(r['DAY'])
        nd = max(len(offd), 1)
        for c in set(on) | set(off):
            ev_clean[c] = off[c] / nd * ldim          # the month at its event-free rate
        tot_on = sum(on.values()); tot_off = sum(off.values())
        ev_note = (f"  event stripped from {last_year_target}: {a.event_days}\n"
                   f"    event days carried {tot_on:,.0f} L; event-free rate "
                   f"{tot_off/nd:,.0f} L/day over {nd} days\n"
                   f"    reference month rebuilt {sum(ev_clean.values()):,.0f} L "
                   f"(was {tot_on+tot_off:,.0f} L)\n")

    grp_of = {c: meta[c][2] for c in sku}
    all_base_ly = total(ly_base) / BASE_MONTHS
    all_ly_tgt  = total([last_year_target])
    all_mult    = (all_ly_tgt / all_base_ly) if all_base_ly else 1.0

    groups = sorted({grp_of[c] for c in sku})
    gm = {}
    for g in groups:
        p = lambda c, g=g: grp_of[c] == g
        b = total(ly_base, p) / BASE_MONTHS
        t = total([last_year_target], p)
        raw = (t / b) if b else all_mult
        w = b / (b + CREDIBILITY_K)                 # credibility on baseline volume
        gm[g] = (w * raw + (1 - w) * all_mult, raw, b, t, w)

    # ---- METHOD B: level-based. Reference year's own mean, not a trailing window.
    have_ref = all(any(k == mm for c in sku for k in sku[c]) for mm in ref_year)
    ref_n    = len([mm for mm in ref_year if any(mm in sku[c] for c in sku)])
    all_ref_avg = total(ref_year) / max(ref_n, 1)
    all_idx_b   = (all_ly_tgt / all_ref_avg) if all_ref_avg else 1.0
    gb_mult = {}
    for g in groups:
        p = lambda c, g=g: grp_of[c] == g
        b = total(ref_year, p) / max(ref_n, 1)
        t = total([last_year_target], p)
        raw = (t / b) if b else all_idx_b
        w = b / (b + CREDIBILITY_K)
        gb_mult[g] = (w * raw + (1 - w) * all_idx_b, raw, b, w)

    # ---- project
    out, tot_base, tot_proj, tot_b_base, tot_projb = [], 0.0, 0.0, 0.0, 0.0
    for c, m in sku.items():
        b = sum(m.get(k, 0.0) for k in base_months) / BASE_MONTHS
        if b <= 0: continue
        g = grp_of[c]
        mult = gm[g][0]
        proj = b * mult
        tot_base += b; tot_proj += proj
        cy = [m.get(k, 0.0) for k in cur_year]
        bb = (sum(cy) / len(cy)) if cy else 0.0
        pb = bb * gb_mult[g][0]
        tot_b_base += bb; tot_projb += pb
        name, typ, _ = meta[c]
        out.append(dict(code=c, name=name, head=typ, group=g,
                        base_l=round(b), mult=round(mult, 4), proj_l=round(proj),
                        proj_t=round(proj / 1000, 2),
                        baseB_l=round(bb), multB=round(gb_mult[g][0], 4),
                        projB_l=round(pb), projB_t=round(pb / 1000, 2),
                        low_l=round(min(proj, pb)), high_l=round(max(proj, pb)),
                        mid_l=round((proj + pb) / 2),
                        **{k.replace('-', '_'): round(m.get(k, 0.0)) for k in base_months}))
    out.sort(key=lambda r: -r['mid_l'])

    # ---- report
    w = "EXTERNAL ONLY" if a.external_only else "EXTERNAL + INTERCOMPANY"
    print(f"\nJIVO Oil — projection for {target}   ({w})")
    print(f"  base months {', '.join(base_months)}"
          + (f"   [{cur} scaled x{part:.3f} for {today.day}/{dim} days]" if part != 1 else ""))
    print(f"  season measured {last_year_target} vs {', '.join(ly_base)}")
    if ev_note: print(ev_note, end="")
    print(f"  all-item multiplier {all_mult:.3f}"
          f"   ({all_ly_tgt:,.0f} L vs {all_base_ly:,.0f} L/mth baseline)\n")

    print(f"  {'GROUP':<20}{'BASE L/mth':>13}{'MULT':>8}{'raw':>8}{'cred':>7}{'PROJ L':>13}")
    gb = collections.defaultdict(float); gp = collections.defaultdict(float)
    for r in out:
        gb[r['group']] += r['base_l']; gp[r['group']] += r['proj_l']
    for g in sorted(gp, key=lambda x: -gp[x]):
        mult, raw, b, t, cw = gm[g]
        print(f"  {g[:19]:<20}{gb[g]:>13,.0f}{mult:>8.3f}{raw:>8.3f}{cw:>7.2f}{gp[g]:>13,.0f}")
    print(f"  {'TOTAL':<20}{tot_base:>13,.0f}{'':>8}{'':>8}{'':>7}{tot_proj:>13,.0f}")
    lo, hi = min(tot_proj, tot_projb), max(tot_proj, tot_projb)
    mid = (tot_proj + tot_projb) / 2
    print(f"\n  METHOD A  momentum   base {tot_base:,.0f} L/mth x season -> "
          f"{tot_proj:,.0f} L  ({tot_proj/1000:,.1f} T)")
    print(f"  METHOD B  level      base {tot_b_base:,.0f} L/mth x index  -> "
          f"{tot_projb:,.0f} L  ({tot_projb/1000:,.1f} T)")
    print(f"      reference year {ref_year[0][:4]}: {ref_n} months, mean "
          f"{all_ref_avg:,.0f} L/mth; {last_year_target} index {all_idx_b:.3f}")
    print(f"\n  >>> PROJECTION {target}:  {lo:,.0f} - {hi:,.0f} L"
          f"   (midpoint {mid:,.0f} L = {mid/1000:,.1f} sale-T)   over {len(out)} SKUs")
    print(f"      spread {(hi-lo)/mid*100:.0f}% of midpoint — one {last_year_target[5:]} "
          f"in the data is the reason; it narrows with every month that passes.")

    if unparsed:
        print(f"\n  unparsed (excluded): {len(unparsed)} SKUs, {sum(unparsed.values()):,.0f} pcs")

    if a.compare and os.path.exists(a.compare):
        pl = list(csv.DictReader(open(a.compare)))
        pt = sum(float(r['total_t'] or 0) for r in pl)
        print(f"\n  human plan  {a.compare}:  {pt*1000:,.0f} L  =  {pt:,.1f} T"
              f"   over {len(pl)} SKUs")
        print(f"  projection midpoint is {mid/(pt*1000)*100:.0f}% of the plan"
              f"   (plan is {pt*1000/mid:.2f}x the projection)")

    os.makedirs(os.path.dirname(a.csv) or ".", exist_ok=True)
    with open(a.csv, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        wr.writeheader(); wr.writerows(out)
    print(f"\n  wrote {a.csv}  ({len(out)} rows)\n")


if __name__ == "__main__":
    main()
