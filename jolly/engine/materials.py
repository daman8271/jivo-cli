#!/usr/bin/env python3
"""
JIVO Oil — production requirement, exploded ALL THE WAY DOWN to what must be bought.

    production requirement per FG   (open orders + MSL - godown stock - WIP)
      -> multi-level BOM explosion  netting stock at every level (proper MRP)
      -> leaves = things we BUY
      -> minus stock, minus what is on order
      -> against real per-vendor lead times

WHY MULTI-LEVEL (fixed 2026-08-27). The first version stopped one level below the
finished good and told the operator to BUY things JIVO actually MAKES:

    PET BOTTLE 1 LTR 40 GMS      is blown in-house from PREFORM 40 GMS 36 MM
    PET BOTTLE 1 LTR 52 GMS      from PREFORM 49.5 GMS 36 MM
    PET BOTTLE 1 LTR 23.8 GMS    from PREFORM 21/23 GMS
    CANOLA COLD PRESS LOOSE OIL  refined from CRUDE DEGUMMED RAPESEED x 1.0309

A buy list that names a made item is worse than no list: nobody can act on it, and
the real purchase (the preform, the crude) never gets raised. Now every item that
has its own production BOM is exploded through, and only true leaves are bought.

MSL basis: GROSS sales (operator call, 2026-08-27). --net-of-returns for the other.

Stock netting happens at EVERY level: if we need 100 bottles and 60 are in stock,
only 40 get blown, so only 40 preforms are needed. Netting only at the bottom
over-orders.

Read-only.

    python3 jolly/engine/materials.py --env connections/hana-new.env
"""
import argparse, collections, csv, os, subprocess, sys, tempfile
from datetime import date, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
CO = "JIVO_OIL_HANADB"
# ---- the ONLY godowns whose stock counts (Daman, 2026-08-29) -------------
# An allow-list, not an exclude-list: a warehouse nobody has ruled on must never
# silently start counting as available stock.
FG_WH  = "'BH-BT','BH-PF','GP-FG'"                       # finished goods
MAT_WH = ("'BH-BS','BH-PM','BH-LO','BH-NM','BH-SDL',"    # oil + packaging
          "'GP-NM','GP-FG','GP-PM'")                     # GP-PM added 2026-08-29:
# live godown, 8 movements in Aug. BH-PP deliberately still OUT — 5,023,302 units
# but zero movement since 2026-02-23, so its stock is unproven on the floor.
# Deliberately OUT: BH-OT (Param, not ours) · BH-WST (wastage) · BH-PC (already
# issued to the floor) · BH-GJ / BH-JW (at job workers) · every C&F and depot.
MSL_PCT = 0.35
WIP_AGE = 60
LEAD_HISTORY_DAYS = 365
MAX_BOM_DEPTH = 12          # cycle guard

REQ_SQL = """
SELECT I."ItemCode" AS FG, MAX(I."ItemName") AS NAME,
  GREATEST(0, IFNULL(MAX(O."OIH"),0)
    + GREATEST(0, {pct}*(IFNULL(MAX(S."SG"),0)-{retmul}*IFNULL(MAX(R."RT"),0)))
    - IFNULL(MAX(F."FGQ"),0) - IFNULL(MAX(W."WIP"),0)) AS REQ
FROM {co}.OITM I
LEFT JOIN (SELECT L."ItemCode" C, SUM(L."OpenQty") OIH FROM {co}.RDR1 L
  JOIN {co}.ORDR H ON H."DocEntry"=L."DocEntry"
  WHERE H."DocStatus"='O' AND H."CANCELED"='N' GROUP BY L."ItemCode") O ON O.C=I."ItemCode"
LEFT JOIN (SELECT L."ItemCode" C, SUM(L."Quantity") SG FROM {co}.INV1 L
  JOIN {co}.OINV H ON H."DocEntry"=L."DocEntry"
  WHERE H."DocDate">='{m0}' AND H."DocDate"<'{m1}' AND H."CANCELED"='N'
  GROUP BY L."ItemCode") S ON S.C=I."ItemCode"
LEFT JOIN (SELECT L."ItemCode" C, SUM(L."Quantity") RT FROM {co}.RIN1 L
  JOIN {co}.ORIN H ON H."DocEntry"=L."DocEntry"
  WHERE H."DocDate">='{m0}' AND H."DocDate"<'{m1}' AND H."CANCELED"='N'
  GROUP BY L."ItemCode") R ON R.C=I."ItemCode"
LEFT JOIN (SELECT "ItemCode" C, SUM("OnHand") FGQ FROM {co}.OITW
  WHERE "WhsCode" IN ({fgwh}) GROUP BY "ItemCode") F ON F.C=I."ItemCode"
LEFT JOIN (SELECT "ItemCode" C, SUM("PlannedQty"-"CmpltQty") WIP FROM {co}.OWOR
  WHERE "Status" IN ('P','R') AND "PostDate">='{wip}' GROUP BY "ItemCode") W ON W.C=I."ItemCode"
WHERE I."ItemCode" LIKE 'FG%' {grpfilter}
GROUP BY I."ItemCode"
"""

BOM_SQL = """
SELECT T."Code" AS FATHER, T."Qauntity" AS YIELD, C."Code" AS CHILD, C."Quantity" AS QTY
FROM {co}.OITT T JOIN {co}.ITT1 C ON C."Father"=T."Code"
WHERE T."TreeType"='P'
  AND C."Type" <> 290          -- 290 = ORSC resource (filling/blowing COST lines,
                               -- e.g. JWPL09240002 "Filling Cost Commodities").
                               -- They sit in the BOM for costing. They are not
                               -- materials and can never be purchased.
"""

ITEM_SQL = """
SELECT I."ItemCode", I."ItemName", I."U_Sub_Group" AS KIND, I."InvntryUom" AS UOM,
  IFNULL(ST."ONHAND",0) AS ONHAND, IFNULL(ST."ONORDER",0) AS ONORDER
FROM {co}.OITM I
LEFT JOIN (SELECT I2."ItemCode" IC,
    IFNULL(H2.Q,0) ONHAND,      -- stock: ONLY the allow-listed godowns
    IFNULL(O2.Q,0) ONORDER      -- inbound: EVERY godown. Goods on order are on
                                -- their way in; which warehouse they are booked
                                -- against does not make them unavailable.
                                -- (Mustard's open POs sit against BH-GJ, the
                                -- Gujarat job worker — filtering those out zeroed
                                -- 465,334 L of real inbound oil.)
  FROM {co}.OITM I2
  LEFT JOIN (SELECT "ItemCode" C, SUM("OnHand") Q FROM {co}.OITW
    WHERE "WhsCode" IN ({matwh}) GROUP BY "ItemCode") H2 ON H2.C=I2."ItemCode"
  LEFT JOIN (SELECT "ItemCode" C, SUM("OnOrder") Q FROM {co}.OITW
    GROUP BY "ItemCode") O2 ON O2.C=I2."ItemCode") ST ON ST.IC=I."ItemCode"
"""

LEAD_SQL = """
SELECT L."ItemCode", MAX(G."CardName") AS VENDOR, COUNT(*) AS RECEIPTS,
       ROUND(AVG(DAYS_BETWEEN(P."DocDate", G."DocDate")),1) AS AVG_DAYS
FROM {co}.PDN1 L
JOIN {co}.OPDN G ON G."DocEntry"=L."DocEntry"
JOIN {co}.OPOR P ON P."DocEntry"=L."BaseEntry"
WHERE L."BaseType"=22 AND G."DocDate">='{since}'
GROUP BY L."ItemCode", G."CardCode"
"""


def run(sql, env):
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql); p = fh.name
    cmd = [HANA] + (["-env", env] if env else []) + ["-csv", "-f", p]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    finally:
        os.unlink(p)
    if r.returncode != 0 or r.stdout.lstrip().startswith("QUERY ERROR"):
        sys.exit("hana-sql failed:\n" + r.stdout + r.stderr)
    return list(csv.DictReader(r.stdout.splitlines()))


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0


def low_level_codes(bom):
    """Deepest level each item appears at. Standard MRP: net a level at a time,
    so an item used at two depths is only netted once, at its deepest use."""
    level = collections.defaultdict(int)
    frontier = [(fa, 0) for fa in bom]
    seen_depth = 0
    while frontier and seen_depth <= MAX_BOM_DEPTH:
        nxt = []
        for item, d in frontier:
            for child, _ in bom.get(item, []):
                if d + 1 > level[child]:
                    level[child] = d + 1
                    nxt.append((child, d + 1))
        frontier = nxt
        seen_depth += 1
    return level


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env"); ap.add_argument("--month"); ap.add_argument("--csv")
    ap.add_argument("--groups", help="comma-separated U_Sub_Group filter on the finished good, "
                    "e.g. MUSTARD,SUNFLOWER,GROUNDNUT,CANOLA (default: all)")
    ap.add_argument("--net-of-returns", action="store_true",
                    help="MSL on sales net of returns (default GROSS — operator call 2026-08-27)")
    a = ap.parse_args()

    today = date.today()
    if a.month:
        y, m = (int(x) for x in a.month.split("-"))
        m0 = date(y, m, 1); m1 = date(y + (m == 12), (m % 12) + 1, 1)
    else:
        m1 = today.replace(day=1); m0 = (m1 - timedelta(days=1)).replace(day=1)

    grpfilter = ""
    if a.groups:
        gl = ",".join("'%s'" % g.strip().upper() for g in a.groups.split(",") if g.strip())
        grpfilter = 'AND I."U_Sub_Group" IN (%s)' % gl
    reqs = run(REQ_SQL.format(co=CO, pct=MSL_PCT, m0=m0, m1=m1, fgwh=FG_WH,
                              retmul=1 if a.net_of_returns else 0, grpfilter=grpfilter,
                              wip=today - timedelta(days=WIP_AGE)), a.env)
    bom = collections.defaultdict(list)
    for r in run(BOM_SQL.format(co=CO), a.env):
        y = f(r["YIELD"]) or 1.0
        bom[r["FATHER"]].append((r["CHILD"], f(r["QTY"]) / y))

    items = {r["ItemCode"]: r for r in run(ITEM_SQL.format(co=CO, matwh=MAT_WH), a.env)}
    leads = collections.defaultdict(list)
    for r in run(LEAD_SQL.format(co=CO, since=today - timedelta(days=LEAD_HISTORY_DAYS)), a.env):
        leads[r["ItemCode"]].append((f(r["AVG_DAYS"]), int(f(r["RECEIPTS"])), r["VENDOR"]))

    # ---- level-by-level MRP netting -------------------------------------
    level = low_level_codes(bom)
    gross = collections.defaultdict(float)
    for r in reqs:
        q = f(r["REQ"])
        if q > 0:
            for child, per in bom.get(r["FG"], []):
                gross[child] += q * per

    net_of = {}
    for lvl in range(1, MAX_BOM_DEPTH + 2):
        at_level = [it for it in list(gross) if level.get(it, 1) == lvl]
        for it in at_level:
            need = gross[it]
            stock = f(items.get(it, {}).get("ONHAND", 0))
            net = max(0.0, need - stock)
            net_of[it] = net
            for child, per in bom.get(it, []):
                gross[child] += net * per

    rows = []
    for code, need in gross.items():
        info = items.get(code, {})
        oh = f(info.get("ONHAND", 0)); oo = f(info.get("ONORDER", 0))
        v = sorted(leads.get(code, []))
        rows.append(dict(code=code, name=info.get("ItemName", code), kind=info.get("KIND", ""),
                         uom=info.get("UOM", ""), level=level.get(code, 1), made=code in bom,
                         need=need, onhand=oh, onorder=oo,
                         short_vs_stock=need - oh, short_net=need - oh - oo,
                         fastest=v[0] if v else None, slowest=v[-1] if v else None))

    made = [m for m in rows if m["made"] and m["short_vs_stock"] > 0]
    buy = sorted([m for m in rows if not m["made"] and m["short_net"] > 0], key=lambda m: -m["short_net"])
    transit = sorted([m for m in rows if not m["made"] and m["short_vs_stock"] > 0 and m["short_net"] <= 0],
                     key=lambda m: -m["short_vs_stock"])

    print(f"MSL month {m0} .. {m1}  |  MSL basis: {'NET of returns' if a.net_of_returns else 'GROSS'}"
          f"{'  |  FOCUS: ' + a.groups.upper() if a.groups else ''}")
    print(f"{len(rows)} items in the explosion, {max([r['level'] for r in rows] or [1])} levels deep")
    print(f"MUST BUY: {len(buy)}   |   in transit only: {len(transit)}   |   MAKE in-house: {len(made)}\n")

    print("### WE MAKE THESE — do not buy them, they need a production run")
    print(f"{'CODE':<12}{'ITEM':<42}{'NEED':>12}{'STOCK':>12}{'TO MAKE':>12}  MADE FROM")
    for m in sorted(made, key=lambda m: -m["short_vs_stock"]):
        src = ", ".join(items.get(c, {}).get("ItemName", c)[:30] for c, _ in bom.get(m["code"], [])[:2])
        print(f"{m['code']:<12}{m['name'][:41]:<42}{m['need']:>12,.0f}{m['onhand']:>12,.0f}"
              f"{m['short_vs_stock']:>12,.0f}  {src}")

    print("\n### MUST BUY — stock + open POs do not cover it")
    print(f"{'CODE':<12}{'MATERIAL':<40}{'NEED':>12}{'STOCK':>12}{'ONORDER':>12}{'SHORT':>11}  FASTEST VENDOR")
    for m in buy:
        fa = m["fastest"]
        lead = f"{fa[0]:.0f}d {fa[2][:26]}" if fa else "NO PURCHASE HISTORY — vendor unknown"
        print(f"{m['code']:<12}{m['name'][:39]:<40}{m['need']:>12,.0f}{m['onhand']:>12,.0f}"
              f"{m['onorder']:>12,.0f}{m['short_net']:>11,.0f}  {lead}")

    print("\n### IN TRANSIT ONLY — the line starves if these do not land in time")
    print(f"{'CODE':<12}{'MATERIAL':<40}{'NEED':>12}{'STOCK':>12}{'ONORDER':>12}{'SHORT':>11}  LEAD")
    for m in transit[:20]:
        fa, sl = m["fastest"], m["slowest"]
        rng = f"{fa[0]:.0f}-{sl[0]:.0f}d" if fa else "n/a"
        print(f"{m['code']:<12}{m['name'][:39]:<40}{m['need']:>12,.0f}{m['onhand']:>12,.0f}"
              f"{m['onorder']:>12,.0f}{m['short_vs_stock']:>11,.0f}  {rng}")

    if a.csv:
        os.makedirs(os.path.dirname(os.path.abspath(a.csv)), exist_ok=True)
        with open(a.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["code", "name", "kind", "uom", "bom_level", "make_or_buy", "need",
                        "onhand", "onorder", "short_vs_stock", "short_net",
                        "fastest_days", "fastest_vendor", "slowest_days", "slowest_vendor"])
            for m in sorted(rows, key=lambda m: (m["level"], -m["need"])):
                fa, sl = m["fastest"], m["slowest"]
                w.writerow([m["code"], m["name"], m["kind"], m["uom"], m["level"],
                            "MAKE" if m["made"] else "BUY",
                            f"{m['need']:.2f}", f"{m['onhand']:.2f}", f"{m['onorder']:.2f}",
                            f"{m['short_vs_stock']:.2f}", f"{m['short_net']:.2f}",
                            fa[0] if fa else "", fa[2] if fa else "",
                            sl[0] if sl else "", sl[2] if sl else ""])
        print(f"\nwrote {a.csv}")


if __name__ == "__main__":
    main()
