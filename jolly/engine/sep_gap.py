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

def main_frozen(a):
    """The VERIFIED-freeze mode (2026-08-31): no live HANA. Reads the frozen, verified
    sim inputs (stock + live-PO inbound as at 31 Aug) and the verified simulated days,
    and computes for EVERY component the plan needs:
      - cover against the month's full requirement (synonyms merged),
      - the FIRST DAY the scheduled September runs would consume past real supply
        (opening + live POs — the sim's own paper orders are deliberately excluded),
      - therefore THE LAST DAY IT CAN BE ORDERED without blocking that run
        (first_short_day - lead; material ordered day X lands and is usable day X+lead).
    Items whose SKUs never got scheduled at all fall back to first demand date
    (basis=unscheduled). Writes CSV + JSON.
    """
    import glob, json
    today = date.fromisoformat(a.today)
    S = json.load(open(a.inputs))
    D0 = date.fromisoformat(S["meta"]["horizon"][0])

    syn = {r["alias"]: r["canonical"] for r in csv.DictReader(open("reference/oil-synonyms.csv"))
           if r.get("alias") and not str(r["alias"]).startswith("#")}
    def canon(c): return syn.get(c, c)

    bom, blends, items, realise = S["bom"], S["blends"], S["items"], S["realise"]
    plan = {p["code"]: p for p in S["plan"]}
    DEF_R = 148.33

    def explode(code, pieces):
        """FG pieces -> {orderable component: qty}, blends expanded to constituents."""
        out = collections.Counter()
        for ch, per in bom.get(code, []):
            if per <= 0: continue
            if ch in blends:
                for k, kp in blends[ch]: out[canon(k)] += pieces * per * kp
            else:
                out[canon(ch)] += pieces * per
        return out

    # month need + which SKUs each component supports (plan litres x realise)
    need = collections.Counter()
    supports = collections.defaultdict(dict)          # comp -> {fg: value}
    sup_litres = collections.defaultdict(dict)        # comp -> {fg: litres}
    for c, p in plan.items():
        val = p["litres"] * realise.get(c, DEF_R)
        for k, q in explode(c, p["pieces"]).items():
            need[k] += q
            supports[k][c] = val
            sup_litres[k][c] = p["litres"]

    stock = collections.Counter()
    for k, v in S["opening"]["stock"].items(): stock[canon(k)] += f(v)
    onorder = collections.Counter(); inb_by_day = collections.defaultdict(collections.Counter)
    for d, m in S["inbound_prebooked"].items():
        for k, v in m.items():
            onorder[canon(k)] += f(v); inb_by_day[d][canon(k)] += f(v)

    # requirement timeline = the verified scheduled runs, day by day
    use_by_day = collections.defaultdict(collections.Counter)
    for fp in sorted(glob.glob(os.path.join(a.days_dir, "day-*.json"))):
        d = json.load(open(fp))
        for r in d["runs"]:
            for k, q in explode(r["code"], r["pieces"]).items():
                use_by_day[d["date"]][k] += q
    daylist = sorted(use_by_day.keys() | inb_by_day.keys())

    # first demand date per FG (fallback basis for SKUs never scheduled)
    first_dem = {}
    for o in S["orders"]:
        c = o["code"]
        if c not in first_dem or o["date"] < first_dem[c]: first_dem[c] = o["date"]

    rows = []
    for k in sorted(need):
        nd = need[k]
        if nd <= 0: continue
        oh, oo = stock.get(k, 0.0), onorder.get(k, 0.0)
        cover = (oh + oo) / nd * 100
        # walk the month: cum use vs opening + cum REAL inbound
        cum_u = cum_i = 0.0; short_day = None
        for d in daylist:
            cum_i += inb_by_day.get(d, {}).get(k, 0.0)
            cum_u += use_by_day.get(d, {}).get(k, 0.0)
            if cum_u > oh + cum_i + 1e-6: short_day = d; break
        used_month = sum(m.get(k, 0.0) for m in use_by_day.values())
        basis = "scheduled_runs"
        if short_day is None and cover < 100 and used_month < 1:
            # its SKUs never made it onto a line — anchor to first real/forecast demand
            basis = "unscheduled"
            dts = [first_dem.get(c) for c in supports[k] if first_dem.get(c)]
            short_day = min(dts) if dts else D0.isoformat()
        lead = a.lead_oil if k.startswith("RM") else a.lead_pm
        order_by = ""
        status = "covered"
        if short_day is not None:
            ob = date.fromisoformat(short_day) - timedelta(days=lead)
            order_by = ob.isoformat()
            status = "LATE — order today, run slips" if ob <= today else "ok"
        zero = oh < 1 and oo < 1
        rows.append(dict(code=k, name=items.get(k, {}).get("name", k),
                         kind="OIL" if k.startswith("RM") else "PACK",
                         uom=items.get(k, {}).get("uom", ""),
                         need=round(nd), on_hand=round(oh), on_order=round(oo),
                         cover_pct=round(min(cover, 999.9), 1),
                         short=round(max(0.0, nd - oh - oo)),
                         at_zero="YES" if zero else "",
                         skus_blocked=len(supports[k]) if zero else 0,
                         litres_at_risk=round(sum(sup_litres[k].values())) if zero else 0,
                         value_at_risk=round(sum(supports[k].values())) if zero else 0,
                         lead_days=lead,
                         first_short_day=short_day or "",
                         order_by=order_by, order_basis=basis if short_day else "",
                         status=status,
                         skus=";".join(sorted(plan[c]["sku"][:30] for c in supports[k]))[:180]))
    rows.sort(key=lambda r: (r["at_zero"] != "YES", -r["value_at_risk"],
                             r["order_by"] or "9999", -r["short"]))

    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    zero = [r for r in rows if r["at_zero"] == "YES"]
    # blocked value DEDUPLICATED: union of distinct SKUs any zero item blocks
    blocked_fg = {}
    for r in zero:
        for c, v in supports[r["code"]].items(): blocked_fg[c] = v
    tv = sum(blocked_fg.values())
    tv_itemsum = sum(r["value_at_risk"] for r in zero)
    # August's money list counted cover < 1% ("zero cover", a sliver of stock allowed) —
    # compute the same so September is comparable to August's 38 items / Rs 8.48 Cr
    sub1 = [r for r in rows if r["cover_pct"] < 1]
    sub1_fg = {}
    for r in sub1:
        for c, v in supports[r["code"]].items(): sub1_fg[c] = v
    wk1_end = (D0 + timedelta(days=6)).isoformat()
    wk1 = [r for r in rows if r["order_by"] and r["order_by"] <= wk1_end and r["cover_pct"] < 100]
    late = [r for r in rows if r["status"].startswith("LATE")]

    summary = dict(
        generated=today.isoformat(), month=S["meta"]["month"],
        basis="verified freeze sim/sep-inputs.json + verified scheduled runs " + a.days_dir,
        components_in_plan=len(rows),
        under_100_cover=len([r for r in rows if r["cover_pct"] < 100]),
        items_at_zero=len(zero),
        zero_pack=len([r for r in zero if r["kind"] == "PACK"]),
        zero_oil=len([r for r in zero if r["kind"] == "OIL"]),
        skus_blocked_by_zero=len(blocked_fg),
        blocked_value_rs=round(tv),
        blocked_value_note="deduplicated across SKUs (one SKU counted once however many "
                           "zero items block it); per-item sum would be %d" % round(tv_itemsum),
        must_order_week1=len(wk1),
        already_late=len(late),
        august_comparable=dict(
            definition="cover < 1% (August's zero-cover rule: a sliver of stock allowed)",
            items=len(sub1), skus_blocked=len(sub1_fg),
            blocked_value_rs=round(sum(sub1_fg.values())),
            codes=[r["code"] for r in sub1]),
        lead_days=dict(oil=a.lead_oil, packaging=a.lead_pm),
        synonyms="merged (reference/oil-synonyms.csv; freeze already canonical — no alias codes present)")
    jpath = a.csv.replace(".csv", ".json")
    json.dump(dict(summary=summary, rows=rows), open(jpath, "w"), indent=1)

    print(f"=== SEPTEMBER 2026 — ORDER-BY LIST, from the verified freeze, as at {today} ===")
    print(f"{'CODE':<12}{'ITEM':<38}{'NEED':>10}{'HAVE':>9}{'ORD':>9}{'CVR%':>7}  {'ORDER BY':<11}{'VALUE AT RISK':>14}")
    for r in [x for x in rows if x["at_zero"] == "YES"][:20]:
        print(f"{r['code']:<12}{r['name'][:37]:<38}{r['need']:>10,}{r['on_hand']:>9,}"
              f"{r['on_order']:>9,}{r['cover_pct']:>7}  {r['order_by']:<11}{r['value_at_risk']:>14,}")
    print(f"\n  components in plan             {len(rows):>8}")
    print(f"  under 100% cover               {summary['under_100_cover']:>8}")
    print(f"  at ZERO (no stock, no PO)      {len(zero):>8}   ({summary['zero_pack']} packaging, {summary['zero_oil']} oil)")
    print(f"  distinct SKUs blocked          {len(blocked_fg):>8}")
    print(f"  BLOCKED VALUE (dedup)          Rs {tv:>12,.0f}   ({tv/1e7:.2f} Cr; per-item sum {tv_itemsum/1e7:.2f} Cr)")
    print(f"  under COVER<1% (Aug's rule)    {len(sub1):>8}   blocking Rs {sum(sub1_fg.values()):,.0f} "
          f"({sum(sub1_fg.values())/1e7:.2f} Cr) across {len(sub1_fg)} SKUs")
    print(f"  must order in week 1           {summary['must_order_week1']:>8}   (order_by <= {wk1_end})")
    print(f"  of which ALREADY LATE          {len(late):>8}")
    print(f"\nwrote {a.csv} and {jpath}  ({len(rows)} components)")
    return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default="2026-08-29")
    ap.add_argument("--csv", default="out/september-gap-list.csv")
    ap.add_argument("--inputs", default=None, help="frozen verified sim inputs; skips live HANA")
    ap.add_argument("--days-dir", default="sim/days-sep", help="verified simulated days")
    ap.add_argument("--lead-oil", type=int, default=LEAD_OIL)
    ap.add_argument("--lead-pm", type=int, default=LEAD_PM)
    a = ap.parse_args()
    if a.inputs:
        return main_frozen(a)
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
