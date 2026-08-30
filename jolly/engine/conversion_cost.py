#!/usr/bin/env python3
"""
JIVO Oil — CONVERSION COST. What it costs to turn oil + packaging into a filled bottle.

Built 2026-08-30 on Daman's instruction ("yes do it, build your own"). The Control
Panel refuses COGS (HTTP 403 for `preshit`), so cost is built here from SAP's own
ledger instead of waiting on a permission.

WHY THIS EXISTS. jolly/engine/allocate.py already prices MATERIAL from what we
actually paid, and ranks SKUs by (price - material) / litres of oil. That is a
CONTRIBUTION margin, not profit — it silently assumes filling a 200 ml bottle costs
the same per litre as filling a 15 L tin. It does not, and the difference decides
the ranking:

    conversion Rs/litre = Rs per line-day / litres that pack yields in a line-day

A pack that pushes few litres per line-day absorbs a lot of factory cost per litre.
Allocating conversion by LITRE instead of by LINE-TIME would flatten exactly the
distinction that matters when line-hours are scarce.

THE COST BASKET is stated explicitly below and is the arguable part — read it before
trusting any number out of this. Excluded on purpose: every COGS/variance account
(that IS the material, already priced in allocate.py), freight OUTWARD, advertising,
interest, bank charges, director remuneration, legal — none of them are the cost of
running a filling line.

ELECTRICITY — DO NOT PUT THE WHOLE PLANT BILL IN HERE (corrected 2026-08-30).
The Rs 26,04,139 bill is the KUNDLI PLANT, which Oil SHARES WITH BEVERAGES, and
Daman's tip is why it is big: "when we are producing water, water takes up a lot of
electricity since the machine is heavy... water was the main player in that."
Water is Beverages. Checked in the books, May-Jul 2026 per month:

    JIVO_BEVERAGES_HANADB  5680011 ELECTRICITY   Rs 15,76,107   (60%)
    JIVO_OIL_HANADB        5680011 + 5100020     Rs 11,74,510   (43%)
                                                 ---------------------
                                                 Rs 27,50,617 ~= the plant bill

The split is ALREADY IN THE BOOKS and Beverages carries the larger share, exactly as
the water story predicts. An earlier version of this engine forced the whole
Rs 26.04 L into Oil and overstated Oil's conversion cost by Rs 14.3 lakh a month.
Oil takes ONLY its own booked power.

SANITY GUARDS — this engine ABORTS rather than print a number it cannot defend.
Added 2026-08-30 after it published Rs 123/litre for a 500 ml pack. That figure was
impossible on its face (it implied a filling line producing 1,098 bottles in a whole
day, about twenty minutes of work) and it went out anyway, carrying a footnote saying
rare packs were overstated. A footnote is not a check. The guards below are:

    1. implied line-hours from real production must not exceed installed capacity
    2. no pack may cost more per litre than CEILING_RS_PER_LITRE to fill
    3. every pack must be assigned a real machine speed

Any breach exits non-zero with the offending rows. --force to print anyway.

Read-only. Writes a CSV.
"""
import argparse, collections, csv, os, subprocess, sys

HERE  = os.path.dirname(os.path.abspath(__file__))
JOLLY = os.path.dirname(HERE)
REPO  = os.path.dirname(JOLLY)
HANA  = os.path.join(REPO, "hana-sql", "hana-sql")
ENV   = os.path.join(REPO, "connections", "hana-office-bridge.env")
CO    = "JIVO_OIL_HANADB"

# ---- THE BASKET. share = how much of the account is the filling floor.
CONVERSION = {
    # direct — booked to the factory already
    "5100008": ("CASUAL LABOUR",                       1.00),
    "5100020": ("ELECTRICITY DIRECT EXPENSE",          1.00),
    "5100015": ("CONSUMABLE/DIRECT EXPENSE",           1.00),
    "5100004": ("UNLOADING/LOADING CHARGES-DIRECT",    1.00),
    "5100009": ("JOB WORK",                            1.00),
    "5100002": ("FREIGHT INWARD CHARGES-DIRECT",       1.00),
    # indirect — a share of it is the factory. THESE SHARES ARE ASSUMPTIONS.
    "5680011": ("ELECTRICITY (Oil's own; Bev pays its own)", 1.00),
    "5650016": ("REPAIR AND MAINTENANCE PLANT & MACH", 1.00),
    "5630001": ("SALARY EXPENSE",                      0.50),   # <-- needs a ruling
    "5660002": ("RENT",                                0.50),   # <-- needs a ruling
}
LINES         = 6                # reference/PLAN-AND-LINES.md (Manual excluded)
DAYS          = 26               # floor pattern: 12 h x 26 d
HOURS_PER_DAY = 12

# ---- BOTTLES PER HOUR. reference/PLAN-AND-LINES.md, from ji.jivo.in.
# Conversion cost is bought in LINE-TIME, and line-time is bought in BOTTLES, not
# litres: a 500 ml bottle occupies the filler for the same tick as a 1 L bottle.
# The old version divided cost by "median litres on an active day", which treated a
# 40-minute changeover run as a whole line-day and inflated every small and rare
# pack ~26x. Speeds are the mean of the lines that can actually run that pack.
SPEED = [   # (max pack litres, pack-type match, bottles/hour)
    (1.05,  "PET",   3345.0),   # JP 5400, Clear Pack 4800, 10 Head 2100, 6 Head 1080
    (2.10,  "PET",    990.0),   # 10 Head 1260, 6 Head 720
    (6.10,  "PET",   1500.0),   # Clear Pack 3000, 10 Head 900, 6 Head 600
    (999.0, "PET",   1500.0),
]
POUCH_BPH = 2100.0    # Hitech 1800, Samarpan 2400
TIN_BPH   = 240.0     # Tin Head, 4 tins/min — Daman 2026-08-29

# A litre of oil sells for roughly Rs 150-200. Conversion is a few rupees. Anything
# above this is arithmetic gone wrong, not an expensive pack.
CEILING_RS_PER_LITRE = 25.0
# Samples and miniatures (10 ml, 25 ml) legitimately cost a lot per LITRE — they take
# a whole filler tick for almost no volume. Rs/litre is the wrong measure for them and
# they are exempt from the ceiling; judge them on Rs/BOTTLE. Do NOT widen this to make
# a real failure go away.
SAMPLE_MAX_LITRES = 0.05


def pack_type(name):
    s = str(name).upper()
    if "DRUM" in s or "200 LTR" in s: return "DRUM"
    if "POUCH" in s:                  return "POUCH"
    if "TIN" in s or "KGS" in s:      return "TIN"
    if "JAR" in s:                    return "JAR"
    return "PET"


def bottles_per_hour(name, litres):
    t = pack_type(name)
    if t == "POUCH": return POUCH_BPH
    if t in ("TIN", "JAR"): return TIN_BPH
    if t == "DRUM": return None          # hand filled, no line
    for cap, _, bph in SPEED:
        if litres <= cap: return bph
    return SPEED[-1][2]

SQL = """
SELECT A."AcctCode" AS "AcctCode", MAX(A."AcctName") AS "AcctName",
       SUM(J."Debit"-J."Credit")/{n} AS "PER_MONTH"
FROM {co}.JDT1 J JOIN {co}.OACT A ON A."AcctCode"=J."Account"
WHERE A."ActType"='E' AND J."RefDate">='{a}' AND J."RefDate"<'{b}'
  AND A."AcctCode" IN ({accts})
GROUP BY A."AcctCode"
"""


def run(sql, env):
    r = subprocess.run([HANA, "-env", env, "-csv", sql],
                       capture_output=True, text=True, timeout=600)
    if r.returncode: sys.exit(f"HANA read failed: {r.stderr[:400]}")
    return list(csv.DictReader(r.stdout.splitlines()))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="a", default="2026-05-01")
    ap.add_argument("--to",   dest="b", default="2026-08-01")
    ap.add_argument("--months", type=int, default=3)
    ap.add_argument("--env", default=ENV)
    ap.add_argument("--salary-share", type=float, default=None,
                    help="override the factory share of SALARY EXPENSE (default 0.50)")
    ap.add_argument("--days", type=int, default=DAYS)
    ap.add_argument("--lines", type=int, default=LINES)
    ap.add_argument("--force", action="store_true",
                    help="print even if a sanity guard fails (does not disable the report)")
    ap.add_argument("--prod", default=None,
                    help="CSV of real production (CD,NM,PCS) to weight the cost by")
    ap.add_argument("--csv", default=os.path.join(JOLLY, "out", "conversion-cost.csv"))
    a = ap.parse_args()

    if a.salary_share is not None:
        CONVERSION["5630001"] = (CONVERSION["5630001"][0], a.salary_share)

    rows = run(SQL.format(co=CO, a=a.a, b=a.b, n=a.months,
                          accts=",".join(f"'{c}'" for c in CONVERSION)), a.env)
    got = {r["AcctCode"]: (r["AcctName"], float(r["PER_MONTH"])) for r in rows}

    print(f"\nJIVO Oil — CONVERSION COST   ({a.a} to {a.b}, /{a.months} months)\n")
    print(f"  {'ACCT':<10}{'NAME':<38}{'BOOKED/mth':>14}{'SHARE':>7}{'TAKEN':>14}")
    total = 0.0
    for code, (label, share) in CONVERSION.items():
        name, val = got.get(code, (label, 0.0))
        take = val * share
        total += take
        print(f"  {code:<10}{name[:37]:<38}{val:>14,.0f}{share:>7.2f}{take:>14,.0f}")

    line_days  = a.lines * a.days
    line_hours = line_days * HOURS_PER_DAY
    per_hour   = total / line_hours
    print(f"\n  {'TOTAL CONVERSION COST':<48}{'':>14}{'':>7}{total:>14,.0f} /month")
    print(f"  {a.lines} lines x {a.days} days x {HOURS_PER_DAY} h = {line_hours:,} line-hours")
    print(f"  => Rs {per_hour:,.0f} per line-hour\n")

    # ---- cost per bottle = Rs per line-hour / bottles that line does per hour
    sys.path.insert(0, HERE)
    from plan_units import pack_litres
    if not a.prod: sys.exit("need --prod <csv with CD,NM,PCS>")
    rows, out, tot_h, tot_l = list(csv.DictReader(open(a.prod))), [], 0.0, 0.0
    for r in rows:
        pk, _ = pack_litres(r["NM"])
        if pk is None: continue
        bph = bottles_per_hour(r["NM"], pk)
        if not bph: continue
        pcs = float(r["PCS"]); hrs = pcs / bph
        tot_h += hrs; tot_l += pcs * pk
        out.append(dict(code=r["CD"], name=r["NM"], pack_type=pack_type(r["NM"]),
                        pack_litres=pk, bottles_per_hour=bph, pieces_180d=round(pcs),
                        line_hours_180d=round(hrs, 1),
                        rs_per_bottle=round(per_hour / bph, 3),
                        rs_per_litre=round(per_hour / bph / pk, 3)))
    out.sort(key=lambda r: -r["line_hours_180d"])

    seen, shown = set(), []
    for r in out:
        k = (r["pack_type"], round(r["pack_litres"], 3))
        if k not in seen: seen.add(k); shown.append(r)
    print(f"  {'TYPE':<7}{'PACK':>8}{'BTL/HR':>9}{'Rs/BOTTLE':>11}{'Rs/LITRE':>10}")
    for r in sorted(shown, key=lambda x: (x["pack_type"], x["pack_litres"]))[:16]:
        print(f"  {r['pack_type']:<7}{r['pack_litres']:>8.4g}{r['bottles_per_hour']:>9,.0f}"
              f"{r['rs_per_bottle']:>11.2f}{r['rs_per_litre']:>10.2f}")

    months = 6.0
    print(f"\n  sanity check on the speeds:")
    print(f"    line-hours implied by 180d of real production : {tot_h:,.0f} h "
          f"({tot_h/months:,.0f} h/month)")
    print(f"    line-hours available at {HOURS_PER_DAY} h x {a.days} d x {a.lines} lines: "
          f"{line_hours:,} h/month")
    print(f"    => filling lines run at {tot_h/months/line_hours*100:.0f}% of the "
          f"{HOURS_PER_DAY}-hour pattern")
    print(f"    litres filled {tot_l:,.0f} over 180d = {tot_l/months:,.0f} L/month")

    # ---------------------------------------------------------------- GUARDS
    fails = []
    used = tot_h / months
    if used > line_hours:
        fails.append(f"implied line-hours {used:,.0f}/month EXCEED capacity "
                     f"{line_hours:,}/month — the speeds in SPEED[] are too slow")
    hot = [r for r in out if r["rs_per_litre"] > CEILING_RS_PER_LITRE
           and r["pack_litres"] > SAMPLE_MAX_LITRES]
    if hot:
        fails.append(f"{len(hot)} SKUs cost more than Rs {CEILING_RS_PER_LITRE}/litre "
                     f"to fill — check the denominator before believing them:")
        for r in sorted(hot, key=lambda x: -x["rs_per_litre"])[:5]:
            fails.append(f"      {r['rs_per_litre']:>9.2f} Rs/L  {r['pack_litres']:>7.4g} L  "
                         f"{r['name'][:44]}")
    missed = [r for r in rows if pack_litres(r["NM"])[0] is not None
              and bottles_per_hour(r["NM"], pack_litres(r["NM"])[0]) is None
              and pack_type(r["NM"]) != "DRUM"]
    if missed:
        fails.append(f"{len(missed)} SKUs have no machine speed assigned")

    if fails:
        print("\n  SANITY GUARD FAILED:")
        for f_ in fails: print(f"    ! {f_}")
        if not a.force:
            print("\n  refusing to write. Fix the inputs, or re-run with --force.\n")
            sys.exit(2)
        print("  --force given: writing anyway.\n")
    else:
        print(f"\n  guards passed: line-hours within capacity, no pack over "
              f"Rs {CEILING_RS_PER_LITRE}/litre, every pack has a speed.")

    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print(f"  wrote {a.csv}  ({len(out)} SKUs)")
    print("  NOTE: the 0.50 factory share on RENT is still an assumption.\n")


if __name__ == "__main__":
    main()
