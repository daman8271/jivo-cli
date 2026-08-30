#!/usr/bin/env python3
"""
JIVO Oil - REAL production throughput from SAP history (OWOR, last 180 days).

Reads the two extracts pulled from HANA:
    out/_owor_180d.csv       production orders  (OWOR + OITM name/category)
    out/_wor1_res_180d.csv   resource lines     (WOR1 ItemType=290)

Writes:
    out/line-throughput.csv         the contracted schema
    out/line-throughput-detail.csv  same rows + uom/type/category/day counts

PRODUCTION-DAY = the order's PostDate.  Validated against OIGN: 4,517 of 4,997
(90.4%) production goods-receipts are booked on the SAME DAY as the order's
PostDate, so PostDate is where the output actually landed.

An observation is one (item, PostDate) pair with the day's completed quantity
SUMMED over every order for that item on that day -- not per order.  78% of
orders open and close the same day, and several orders for one SKU routinely
share a day, so a per-order view would understate a day's real output.

Read-only.  Writes CSVs only.
"""
import csv, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
JOLLY = os.path.dirname(HERE)
OUT = os.path.join(JOLLY, "out")
sys.path.insert(0, HERE)
from plan_units import pack_litres           # reuse the settled parser

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def pctl(vals, p):
    """Linear-interpolation percentile (numpy default), p in 0..100."""
    if not vals: return 0.0
    s = sorted(vals)
    if len(s) == 1: return s[0]
    k = (len(s) - 1) * (p / 100.0)
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)

def median(vals): return pctl(vals, 50)

# ---------------------------------------------------------------- load
orders = list(csv.DictReader(open(os.path.join(OUT, "_owor_180d.csv"))))
reslines = list(csv.DictReader(open(os.path.join(OUT, "_wor1_res_180d.csv"))))

res_by_doc = collections.defaultdict(list)
for r in reslines:
    res_by_doc[r["DOCENTRY"]].append(r)

# resource BaseQty = litres per piece (SAP-native pack size, filling orders only)
sap_lpc = {}
for r in reslines:
    pass  # filled below once we know the order's item

# ---------------------------------------------------------------- filter
# Drop: cancelled orders, disassembly (Type='D' is teardown, not production),
# and orders that completed nothing.
kept, dropped = [], collections.Counter()
for o in orders:
    if o["OSTATUS"] == "C":       dropped["cancelled"] += 1; continue
    if o["OTYPE"] == "D":         dropped["disassembly"] += 1; continue
    if f(o["CMPLTQTY"]) <= 0:     dropped["zero_completed"] += 1; continue
    kept.append(o)

# SAP-native litres-per-piece from the resource line's BaseQty
for o in kept:
    for rl in res_by_doc.get(o["DOCENTRY"], []):
        b = f(rl["RBASEQTY"])
        if b > 0:
            sap_lpc.setdefault(o["ITEMCODE"], collections.Counter())[b] += 1

# ---------------------------------------------------------------- aggregate
day = collections.defaultdict(float)          # (item, postdate) -> qty
meta = {}
ordercount = collections.Counter()
rescodes = collections.defaultdict(set)
spans = []

for o in kept:
    ic = o["ITEMCODE"]
    day[(ic, o["POSTDATE"])] += f(o["CMPLTQTY"])
    ordercount[ic] += 1
    for rl in res_by_doc.get(o["DOCENTRY"], []):
        rescodes[ic].add(rl["RESCODE"])
    meta.setdefault(ic, {
        "name": o["ITEMNAME"] or "", "uom": o["UOM"] or "",
        "otype": o["OTYPE"], "utype": o["UTYPE"] or "", "usub": o["USUB"] or "",
    })
    if o["CLOSEDATE"] and o["POSTDATE"]:
        spans.append((o["POSTDATE"], o["CLOSEDATE"]))

byitem = collections.defaultdict(list)
for (ic, d), q in day.items():
    byitem[ic].append((d, q))

# ---------------------------------------------------------------- pack size
def resolve_pack(ic, name, uom):
    """(pack_litres, source). Bulk oil sold by the litre has no pack size."""
    if uom == "LTR":
        return None, "bulk (LTR) - no pack"
    c = sap_lpc.get(ic)
    if c:
        v = c.most_common(1)[0][0]
        return round(v, 4), "SAP resource BaseQty"
    v, how = pack_litres(name)
    if v: return round(v, 4), f"name: {how}"
    return None, "unparsed"

rows = []
for ic, obs in byitem.items():
    m = meta[ic]
    qtys = [q for _, q in obs]
    pl, plsrc = resolve_pack(ic, m["name"], m["uom"])
    rows.append({
        "item_code": ic,
        "item_name": m["name"],
        "pack_litres": ("%g" % pl) if pl else "",
        "orders": ordercount[ic],
        "total_completed": round(sum(qtys), 2),
        "median_units_per_day": round(median(qtys), 1),
        "p90_units_per_day": round(pctl(qtys, 90), 1),
        "resource_codes": "|".join(sorted(rescodes[ic])),
        # detail-only
        "_process": ("BOTTLE_BLOWING" if "JWPL09240005" in rescodes[ic]
                     else "BULK_OIL_BLEND" if (m["uom"]=="LTR" and m["otype"]=="P")
                     else "FILLING" if rescodes[ic] else "FILLING_NO_RESOURCE_LINE"),
        "_uom": m["uom"], "_otype": m["otype"], "_days": len(obs),
        "_pack_src": plsrc, "_category": m["utype"], "_variety": m["usub"],
        "_median_litres_per_day": round(median(qtys) * pl, 1) if pl else round(median(qtys), 1),
    })

rows.sort(key=lambda r: -r["total_completed"])

HDR = ["item_code","item_name","pack_litres","orders","total_completed",
       "median_units_per_day","p90_units_per_day","resource_codes"]
with open(os.path.join(OUT, "line-throughput.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=HDR, extrasaction="ignore")
    w.writeheader(); w.writerows(rows)

DHDR = HDR + ["_process","_uom","_otype","_days","_pack_src","_category","_variety","_median_litres_per_day"]
with open(os.path.join(OUT, "line-throughput-detail.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=DHDR)
    w.writeheader(); w.writerows(rows)

# ---------------------------------------------------------------- report
print(f"kept {len(kept)} orders of {len(orders)}   dropped: {dict(dropped)}")
print(f"items: {len(rows)}   item-days (observations): {len(day)}")
print(f"CSV  : {os.path.join(OUT,'line-throughput.csv')}")
