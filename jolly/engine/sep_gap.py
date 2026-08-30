#!/usr/bin/env python3
"""
SEPTEMBER — the list that should have existed on 1 August, produced before the month starts.

The August backtest found that Rs 8.48 Cr of the month was blocked by 38 packaging items
sitting at zero stock and zero on order, while aggregate packaging coverage read a
comfortable 84%. Coverage does not average: one missing label stops its whole SKU.

This runs the same check against the LIVE September plan (EXIM /planning/latest/,
4,323,300 L) using TODAY's stock and open purchase orders, and prices what each gap
blocks. Ordered by revenue at risk, with the order-by date from measured lead times.

Read-only.
"""
import argparse, collections, csv, io, os, subprocess, sys
from datetime import date, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
CO = "JIVO_OIL_HANADB"
MAT_WH = "'BH-BS','BH-PM','BH-LO','BH-NM','BH-SDL','GP-NM','GP-FG','BH-GJ'"
LEAD_PM, LEAD_OIL = 6, 11          # measured medians
MONTH_START = date(2026, 9, 1)

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def q(sql):
    r = subprocess.run([HANA, "-env", os.path.join(REPO, "connections", "hana-office-bridge.env"), "-csv", sql],
                       capture_output=True, text=True, timeout=300)
    if r.returncode: sys.exit(f"HANA: {r.stderr[:300]}")
    return list(csv.DictReader(io.StringIO(r.stdout)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default="2026-08-29")
    ap.add_argument("--csv", default="out/september-gap-list.csv")
    a = ap.parse_args()
    today = date.fromisoformat(a.today)

    syn = {r["alias"]: r["canonical"] for r in csv.DictReader(open("reference/oil-synonyms.csv"))
           if r.get("alias") and not str(r["alias"]).startswith("#")}
    def canon(c): return syn.get(c, c)

    comp = list(csv.DictReader(open("out/plan-sep-components.csv")))
    plan = [r for r in csv.DictReader(open("out/plan-sep-resolved.csv")) if r["pieces"]]

    bom = collections.defaultdict(list)
    for r in q(f'''SELECT T."Code" F, C."Code" C, C."Quantity"/T."Qauntity" PER
        FROM {CO}.OITT T JOIN {CO}.ITT1 C ON C."Father"=T."Code"
        WHERE T."TreeType"='P' AND C."Type"<>290'''):
        bom[r["F"]].append((r["C"], f(r["PER"])))
    for x in csv.DictReader(open("reference/reconstructed-boms.csv")):
        if x["father"] not in bom: bom[x["father"]].append((x["child"], f(x["per_piece"])))

    stock = collections.defaultdict(float)
    for r in q(f'''SELECT "ItemCode" IC, SUM("OnHand") Q FROM {CO}.OITW
        WHERE "WhsCode" IN ({MAT_WH}) GROUP BY "ItemCode"'''):
        stock[canon(r["IC"])] += f(r["Q"])
    onorder = collections.defaultdict(float)
    # POR1."OpenQty" is in the PURCHASE unit, not the inventory unit. Oil is bought in
    # MTS at NumPerMsr = 1,098.9 L/MT, so summing OpenQty treats 376 tonnes of mustard
    # as 376 litres. That hid 1,107,113 L of real inbound oil and invented a shortage
    # that did not exist. "OpenInvQty" is the same quantity already converted to the
    # inventory unit — use it, and fall back to OpenQty x NumPerMsr if it is null.
    for r in q(f'''SELECT L."ItemCode" IC,
        SUM(COALESCE(L."OpenInvQty", L."OpenQty" * COALESCE(L."NumPerMsr",1))) Q
        FROM {CO}.POR1 L JOIN {CO}.OPOR H ON H."DocEntry"=L."DocEntry"
        WHERE H."DocStatus"='O' AND H."CANCELED"='N' GROUP BY L."ItemCode"'''):
        onorder[canon(r["IC"])] += f(r["Q"])

    realise = {}
    for x in csv.DictReader(open("out/realise-by-item-PRE-AUG.csv")):
        c = str(x["item"]).split("—")[0].split("-")[0].strip()[:9]
        if c.startswith("FG"): realise[c] = f(x["realise"])

    names = {r["code"]: r["name"] for r in comp}
    need = {r["code"]: f(r["required"]) for r in comp}

    # which SKU does each component block, and what is that worth
    blocks = collections.defaultdict(lambda: {"litres": 0.0, "value": 0.0, "skus": []})
    for r in plan:
        lit = f(r["litres"]); val = lit * realise.get(r["code"], 148.33)
        for c, per in bom.get(r["code"], []):
            k = canon(c)
            if per <= 0: continue
            blocks[k]["litres"] += lit; blocks[k]["value"] += val
            blocks[k]["skus"].append(r["sku"])

    rows = []
    for c, nd in need.items():
        if nd <= 0: continue
        k = canon(c)
        have = stock.get(k, 0.0) + onorder.get(k, 0.0)
        cover = have / nd * 100 if nd else 999
        if cover >= 100: continue
        b = blocks.get(k, {"litres": 0.0, "value": 0.0, "skus": []})
        lead = LEAD_OIL if c.startswith("RM") else LEAD_PM
        rows.append(dict(code=c, name=names.get(c, c), kind="OIL" if c.startswith("RM") else "PACK",
                         need=round(nd), on_hand=round(stock.get(k, 0.0)),
                         on_order=round(onorder.get(k, 0.0)), cover_pct=round(cover, 1),
                         short=round(max(0.0, nd - have)),
                         skus_blocked=len(set(b["skus"])),
                         litres_at_risk=round(b["litres"]),
                         value_at_risk=round(b["value"]),
                         lead_days=lead,
                         order_by=(MONTH_START - timedelta(days=lead)).isoformat(),
                         status="LATE" if today > MONTH_START - timedelta(days=lead) else "ok"))
    rows.sort(key=lambda r: (-(r["cover_pct"] < 1), -r["value_at_risk"]))
    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    zero = [r for r in rows if r["cover_pct"] < 1]
    print(f"=== SEPTEMBER 2026 — GAP LIST, as at {today} ===")
    print(f"    plan 4,323,300 L · month starts {MONTH_START} · {(MONTH_START-today).days} days away\n")
    print(f"{'CODE':<12}{'ITEM':<38}{'NEED':>11}{'HAVE':>10}{'ORD':>9}{'SKUs':>5}{'VALUE AT RISK':>15}")
    print("--- ZERO STOCK, ZERO ON ORDER — nothing can be made ---")
    for r in zero[:16]:
        print(f"{r['code']:<12}{r['name'][:37]:<38}{r['need']:>11,.0f}{r['on_hand']:>10,.0f}"
              f"{r['on_order']:>9,.0f}{r['skus_blocked']:>5}{r['value_at_risk']:>15,.0f}")
    print(f"\n  items at ZERO cover        {len(zero):>8}")
    print(f"  of which packaging         {len([r for r in zero if r['kind']=='PACK']):>8}")
    print(f"  of which oil               {len([r for r in zero if r['kind']=='OIL']):>8}")
    uniq = {s for r in zero for s in blocks.get(canon(r['code']), {'skus': []})['skus']}
    tv = sum(r["value_at_risk"] for r in zero)
    print(f"  distinct SKUs blocked      {len(uniq):>8}")
    print(f"  REVENUE AT RISK            Rs {tv:>12,.0f}   ({tv/1e7:.2f} Cr)")
    late = [r for r in rows if r["status"] == "LATE" and r["cover_pct"] < 1]
    print(f"\n  ALREADY LATE to order      {len(late):>8}   (packaging order-by "
          f"{(MONTH_START-timedelta(days=LEAD_PM)).isoformat()}, oil "
          f"{(MONTH_START-timedelta(days=LEAD_OIL)).isoformat()})")
    print(f"\nwrote {a.csv}  ({len(rows)} items under 100% cover)")

if __name__ == "__main__":
    main()
