#!/usr/bin/env python3
"""
JIVO Oil — requirement exploded through the BLENDS, down to the oils we truly buy.

Why this exists (2026-08-27). The BOM tables (OITT/ITT1) stop at the blended oil,
so every earlier buy list said things like "buy 312,678 L of sunflower oil". JIVO
has not bought sunflower oil at all: over the last 90 days it made 743,445 L of it
from soyabean. The real recipes are not in the BOM — they are in the components
actually issued to production orders (OWOR -> WOR1), and they change every batch.

So this engine uses THREE sources:
  1. OITT/ITT1      finished good -> oil + packaging
  2. OWOR/WOR1      blended oil  -> base oils, volume-weighted over 90 days
  3. OWOR vs PDN1   the make/buy split, to know which of the two applies

Verified split, 90 days to 2026-08-27:
     CANOLA COLD PRESS      100% made      GROUNDNUT LOOSE     100% made
     REFINED SUNFLOWER      100% made      LOOSE OIL GOLD      100% made
     LOOSE REFINED OLIVE     93% made      COLD PRESS/REFINED  100% made
     SOYABEAN REFINED         2% made  <-- bought        MUSTARD LOOSE  7% made <-- bought
     PEANUT, CRUDE RAPESEED, RICE BRAN, POMACE            0% made <-- bought

Self-referencing components (olive made partly from olive) are reprocessing, not
new demand — they are skipped, otherwise the explosion never terminates.

Read-only.

    python3 jolly/engine/blend_mrp.py --env connections/hana-new.env \
        --groups MUSTARD,SUNFLOWER,GROUNDNUT,CANOLA
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
RECIPE_WINDOW = 90
MADE_THRESHOLD = 50          # % made over the window before we explode instead of buy
MAX_DEPTH = 8

SQL_REQ = """
SELECT I."ItemCode" AS FG, MAX(I."ItemName") AS NAME,
  GREATEST(0, IFNULL(MAX(O."OIH"),0) + GREATEST(0, {pct}*IFNULL(MAX(S."SG"),0))
    - IFNULL(MAX(F."FGQ"),0) - IFNULL(MAX(W."WIP"),0)) AS REQ
FROM {co}.OITM I
LEFT JOIN (SELECT L."ItemCode" C, SUM(L."OpenQty") OIH FROM {co}.RDR1 L
  JOIN {co}.ORDR H ON H."DocEntry"=L."DocEntry"
  WHERE H."DocStatus"='O' AND H."CANCELED"='N' GROUP BY L."ItemCode") O ON O.C=I."ItemCode"
LEFT JOIN (SELECT L."ItemCode" C, SUM(L."Quantity") SG FROM {co}.INV1 L
  JOIN {co}.OINV H ON H."DocEntry"=L."DocEntry"
  WHERE H."DocDate">='{m0}' AND H."DocDate"<'{m1}' AND H."CANCELED"='N'
  GROUP BY L."ItemCode") S ON S.C=I."ItemCode"
LEFT JOIN (SELECT "ItemCode" C, SUM("OnHand") FGQ FROM {co}.OITW
  WHERE "WhsCode" IN ({fgwh}) GROUP BY "ItemCode") F ON F.C=I."ItemCode"
LEFT JOIN (SELECT "ItemCode" C, SUM("PlannedQty"-"CmpltQty") WIP FROM {co}.OWOR
  WHERE "Status" IN ('P','R') AND "PostDate">='{wip}' GROUP BY "ItemCode") W ON W.C=I."ItemCode"
WHERE I."ItemCode" LIKE 'FG%' {grp}
GROUP BY I."ItemCode"
"""

SQL_BOM = """
SELECT T."Code" AS FATHER, T."Qauntity" AS YIELD, C."Code" AS CHILD, C."Quantity" AS QTY
FROM {co}.OITT T JOIN {co}.ITT1 C ON C."Father"=T."Code"
WHERE T."TreeType"='P' AND C."Type" <> 290
"""

SQL_RECIPE = """
WITH made AS (SELECT "ItemCode" IC, SUM("PlannedQty") Q FROM {co}.OWOR
  WHERE "PostDate">='{since}' GROUP BY "ItemCode"),
used AS (SELECT O."ItemCode" IC, W."ItemCode" COMP, SUM(W."PlannedQty") Q
  FROM {co}.OWOR O JOIN {co}.WOR1 W ON W."DocEntry"=O."DocEntry"
  WHERE O."PostDate">='{since}' GROUP BY O."ItemCode", W."ItemCode")
SELECT u.IC AS FATHER, u.COMP AS CHILD, u.Q/m.Q AS PER_UNIT
FROM used u JOIN made m ON m.IC=u.IC WHERE m.Q>0
"""

SQL_SPLIT = """
WITH mk AS (SELECT "ItemCode" IC, SUM("PlannedQty") Q FROM {co}.OWOR
  WHERE "PostDate">='{since}' GROUP BY "ItemCode"),
bt AS (SELECT L."ItemCode" IC, SUM(L."InvQty") Q FROM {co}.PDN1 L
  JOIN {co}.OPDN G ON G."DocEntry"=L."DocEntry"
  WHERE G."DocDate">='{since}' AND G."CANCELED"='N' GROUP BY L."ItemCode")
SELECT I."ItemCode", IFNULL(mk.Q,0) AS MADE, IFNULL(bt.Q,0) AS BOUGHT
FROM {co}.OITM I LEFT JOIN mk ON mk.IC=I."ItemCode" LEFT JOIN bt ON bt.IC=I."ItemCode"
WHERE IFNULL(mk.Q,0)+IFNULL(bt.Q,0) > 0
"""

SQL_ITEMS = """
SELECT I."ItemCode", I."ItemName", I."InvntryUom" AS UOM,
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

SQL_LEAD = """
SELECT L."ItemCode", MAX(G."CardName") AS VENDOR, COUNT(*) AS N,
  ROUND(AVG(DAYS_BETWEEN(P."DocDate",G."DocDate")),1) AS AVG_DAYS
FROM {co}.PDN1 L JOIN {co}.OPDN G ON G."DocEntry"=L."DocEntry"
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env"); ap.add_argument("--groups"); ap.add_argument("--csv")
    a = ap.parse_args()

    today = date.today()
    m1 = today.replace(day=1); m0 = (m1 - timedelta(days=1)).replace(day=1)
    since = today - timedelta(days=RECIPE_WINDOW)

    grp = ""
    if a.groups:
        gl = ",".join("'%s'" % g.strip().upper() for g in a.groups.split(",") if g.strip())
        grp = 'AND I."U_Sub_Group" IN (%s)' % gl

    reqs = run(SQL_REQ.format(co=CO, pct=MSL_PCT, m0=m0, m1=m1, fgwh=FG_WH,
                              grp=grp, wip=today - timedelta(days=WIP_AGE)), a.env)
    bom = collections.defaultdict(list)
    for r in run(SQL_BOM.format(co=CO), a.env):
        y = f(r["YIELD"]) or 1.0
        bom[r["FATHER"]].append((r["CHILD"], f(r["QTY"]) / y))
    recipe = collections.defaultdict(list)
    for r in run(SQL_RECIPE.format(co=CO, since=since), a.env):
        # WOR1 carries resource lines (JWPL… filling/blowing cost) exactly as ITT1
        # does. They are costing, never materials, and can never be purchased.
        if r["FATHER"] != r["CHILD"] and not r["CHILD"].startswith("JWPL"):
            recipe[r["FATHER"]].append((r["CHILD"], f(r["PER_UNIT"])))
    pct_made = {}
    for r in run(SQL_SPLIT.format(co=CO, since=since), a.env):
        mk, bt = f(r["MADE"]), f(r["BOUGHT"])
        if mk + bt > 0:
            pct_made[r["ItemCode"]] = 100.0 * mk / (mk + bt)
    items = {r["ItemCode"]: r for r in run(SQL_ITEMS.format(co=CO, matwh=MAT_WH), a.env)}
    leads = collections.defaultdict(list)
    for r in run(SQL_LEAD.format(co=CO, since=today - timedelta(days=365)), a.env):
        leads[r["ItemCode"]].append((f(r["AVG_DAYS"]), int(f(r["N"])), r["VENDOR"]))

    def is_made(code):
        return pct_made.get(code, 0) >= MADE_THRESHOLD and code in recipe

    # ---- pass 1: gross demand, level by level (no netting yet) ----------
    # Netting inside the recursion is wrong twice over: the same stock gets
    # consumed by every parent that asks for it, and an item that nets to zero
    # disappears from the report instead of showing as "covered".
    gross = collections.Counter()
    level = collections.defaultdict(int)
    frontier = []
    for r in reqs:
        q = f(r["REQ"])
        if q > 0:
            for child, per in bom.get(r["FG"], []):
                gross[child] += q * per
                level[child] = max(level[child], 1)
                frontier.append(child)

    for depth in range(1, MAX_DEPTH + 1):
        at = [c for c in list(gross) if level[c] == depth]
        if not at:
            continue
        for code in at:
            kids = recipe[code] if is_made(code) else (bom.get(code, []) if code in bom else [])
            for child, per in kids:
                level[child] = max(level[child], depth + 1)

    # ---- pass 2: net each item once, deepest-last, and push net demand down ----
    netted, make, buy = {}, collections.Counter(), collections.Counter()
    for depth in range(1, MAX_DEPTH + 2):
        for code in [c for c in list(gross) if level[c] == depth]:
            stock = f(items.get(code, {}).get("ONHAND", 0))
            net = max(0.0, gross[code] - stock)
            netted[code] = net
            kids = recipe[code] if is_made(code) else (bom.get(code, []) if code in bom else [])
            if kids:
                make[code] += net
                for child, per in kids:
                    gross[child] += net * per
            else:
                buy[code] += gross[code]      # report gross need; shortfall computed below

    print(f"MSL month {m0}..{m1} (GROSS) | recipes from {RECIPE_WINDOW}d of production orders"
          + (f" | FOCUS {a.groups.upper()}" if a.groups else ""))
    print(f"\n### WE BLEND THESE — a production run, not a purchase order")
    print(f"{'CODE':<12}{'OIL':<38}{'TO BLEND':>12}{'%MADE':>7}  MAIN INPUTS")
    for code, q in sorted(make.items(), key=lambda x: -x[1]):
        ing = sorted(recipe.get(code, []), key=lambda x: -x[1])[:3]
        s = " + ".join(f"{items.get(c,{}).get('ItemName',c)[:22]} {p:.2f}" for c, p in ing)
        print(f"{code:<12}{items.get(code,{}).get('ItemName',code)[:37]:<38}{q:>12,.0f}"
              f"{pct_made.get(code,0):>6.0f}%  {s}")

    print(f"\n### THE REAL SHOPPING LIST — oils and materials we actually buy")
    print(f"{'CODE':<12}{'MATERIAL':<38}{'NEED':>12}{'STOCK':>12}{'ONORDER':>12}{'SHORT':>11}  FASTEST")
    rows = []
    for code, q in sorted(buy.items(), key=lambda x: -x[1]):
        oh = f(items.get(code, {}).get("ONHAND", 0)); oo = f(items.get(code, {}).get("ONORDER", 0))
        short = q - oh - oo
        v = sorted(leads.get(code, []))
        rows.append((code, q, oh, oo, short, v[0] if v else None))
        if q < 500 and short <= 0:
            continue
        fa = v[0] if v else None
        lead = f"{fa[0]:.0f}d {fa[2][:24]}" if fa else "no purchase history"
        flag = "  <<<" if short > 0 else ""
        print(f"{code:<12}{items.get(code,{}).get('ItemName',code)[:37]:<38}{q:>12,.0f}"
              f"{oh:>12,.0f}{oo:>12,.0f}{short:>11,.0f}  {lead}{flag}")

    if a.csv:
        os.makedirs(os.path.dirname(os.path.abspath(a.csv)), exist_ok=True)
        with open(a.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["code", "name", "role", "need", "onhand", "onorder", "short",
                        "pct_made", "fastest_days", "fastest_vendor"])
            for code, q in list(make.items()):
                w.writerow([code, items.get(code, {}).get("ItemName", code), "BLEND",
                            f"{q:.0f}", "", "", "", f"{pct_made.get(code,0):.0f}", "", ""])
            for code, q, oh, oo, short, fa in rows:
                w.writerow([code, items.get(code, {}).get("ItemName", code), "BUY",
                            f"{q:.0f}", f"{oh:.0f}", f"{oo:.0f}", f"{short:.0f}",
                            f"{pct_made.get(code,0):.0f}",
                            fa[0] if fa else "", fa[2] if fa else ""])
        print(f"\nwrote {a.csv}")


if __name__ == "__main__":
    main()
