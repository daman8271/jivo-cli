#!/usr/bin/env python3
"""
Roll the month schedule up into WEEKS, per line — the view a plant manager reads.

Reads out/august-month-plan.csv (day/line/SKU runs) and reports, per week and line:
what runs, how many hours, how many oil changes, litres and value. Flushes are already
costed in the month plan (400 L of the next oil, time = 400 / line L-per-hour); this
view just counts and attributes them.
"""
import csv, collections, sys
from datetime import date

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

src = sys.argv[1] if len(sys.argv) > 1 else "out/august-month-plan.csv"
rows = list(csv.DictReader(open(src)))
if not rows: sys.exit("no runs in " + src)

start = min(date.fromisoformat(r["day"]) for r in rows)
def week(d): return (date.fromisoformat(d) - start).days // 7 + 1

for r in rows: r["_w"] = week(r["day"])
weeks = sorted({r["_w"] for r in rows})
lines = ["JP Machine", "Clear Pack", "10 Head", "6 Head", "Pouch Machine", "Tin Head"]

grand_l = grand_v = 0
for w in weeks:
    wr = [r for r in rows if r["_w"] == w]
    d0, d1 = min(r["day"] for r in wr), max(r["day"] for r in wr)
    wl = sum(f(r["litres"]) for r in wr); wv = sum(f(r["value_rs"]) for r in wr)
    wf = sum(1 for r in wr if r["flush_min"])
    grand_l += wl; grand_v += wv
    print(f"\n{'='*78}")
    print(f"WEEK {w}   {d0} .. {d1}     {wl:>10,.0f} L    Rs {wv/1e7:>5.2f} Cr    {wf} oil changes")
    print(f"{'='*78}")
    for ln in lines:
        lr = [r for r in wr if r["line"] == ln]
        if not lr: 
            print(f"  {ln:<15} IDLE"); continue
        hrs = sum(f(r["hours"]) for r in lr)
        fl = sum(1 for r in lr if r["flush_min"])
        fm = sum(f(r["flush_min"]) for r in lr)
        lit = sum(f(r["litres"]) for r in lr)
        val = sum(f(r["value_rs"]) for r in lr)
        agg = collections.defaultdict(lambda: [0.0, 0.0])
        for r in lr:
            agg[r["sku"]][0] += f(r["pieces"]); agg[r["sku"]][1] += f(r["litres"])
        top = sorted(agg.items(), key=lambda kv: -kv[1][1])[:4]
        print(f"  {ln:<15}{hrs:>6.1f} h  {lit:>9,.0f} L  Rs {val/1e5:>6,.1f} L  "
              f"{fl} flush ({fm:.0f} min)")
        for sku, (p, l) in top:
            print(f"       {sku[:52]:<54}{p:>9,.0f} pcs {l:>9,.0f} L")
        if len(agg) > 4: print(f"       + {len(agg)-4} more SKUs")
print(f"\n{'='*78}")
print(f"MONTH   {grand_l:>12,.0f} L    Rs {grand_v/1e7:.2f} Cr    "
      f"{sum(1 for r in rows if r['flush_min'])} oil changes total")
