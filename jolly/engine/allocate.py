#!/usr/bin/env python3
"""
JIVO Oil — ALLOCATION. Given the oil we can actually get, what do we make first?

The shortage is real and permanent: demand is above supply and price is rationing.
So the question is not "what do we need" (jolly/engine/blend_mrp.py answers that)
but "we cannot make everything — which litres earn the most?"

    for every SKU we could make:
        material cost  = full roll-up through the BOM AND the blend recipes,
                         priced at what we actually paid over the last 90 days
        selling price  = what it actually realised, net of GST, from invoices
        oil litres     = litres of BOUGHT oil it consumes, after blending
        => contribution per litre of oil = (price - material cost) / oil litres

    rank by that, then pour the oil we have down the ranking, honouring what is
    already committed to customers first, and stopping when each base oil runs out.

Why per LITRE OF OIL and not per bottle: oil is the constraint. A bottle that
earns 30 rupees on 5 litres is worse than one earning 12 on 1 litre. Ranking by
margin per bottle would get this exactly backwards on every 5 LTR pack.

Greedy, not linear programming. Each base oil is a separate pool and a SKU is only
buildable while ALL of its oils last. Honest and explainable beats optimal-and-opaque
for a first version — and the ranking, not the last 2%, is where the money is.

Read-only.

    python3 jolly/engine/allocate.py --env connections/hana-new.env \
        --groups MUSTARD,SUNFLOWER,GROUNDNUT,CANOLA
"""
import argparse, collections, csv, os, subprocess, sys, tempfile
from datetime import date, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
CO = "JIVO_OIL_HANADB"
FG_WH  = "'BH-BT','BH-PF','GP-FG'"
MAT_WH = "'BH-BS','BH-PM','BH-LO','BH-NM','BH-SDL','GP-NM','GP-FG','GP-PM'"
MSL_PCT = 0.35
WIP_AGE = 60
WINDOW = 90
MADE_THRESHOLD = 50
MAX_DEPTH = 8

Q = {}
Q["req"] = """
SELECT I."ItemCode" FG, MAX(I."ItemName") NAME, MAX(I."U_Sub_Group") GRP,
  GREATEST(0, IFNULL(MAX(O."OIH"),0) + GREATEST(0, {pct}*IFNULL(MAX(S."SG"),0))
    - IFNULL(MAX(F."FGQ"),0) - IFNULL(MAX(W."WIP"),0)) REQ,
  IFNULL(MAX(O."OIH"),0) OIH
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
Q["bom"] = """SELECT T."Code" FATHER, T."Qauntity" YIELD, C."Code" CHILD, C."Quantity" QTY
FROM {co}.OITT T JOIN {co}.ITT1 C ON C."Father"=T."Code"
WHERE T."TreeType"='P' AND C."Type"<>290"""
Q["recipe"] = """
WITH made AS (SELECT "ItemCode" IC, SUM("PlannedQty") Q FROM {co}.OWOR
  WHERE "PostDate">='{since}' GROUP BY "ItemCode"),
used AS (SELECT O."ItemCode" IC, W."ItemCode" COMP, SUM(W."PlannedQty") Q
  FROM {co}.OWOR O JOIN {co}.WOR1 W ON W."DocEntry"=O."DocEntry"
  WHERE O."PostDate">='{since}' GROUP BY O."ItemCode", W."ItemCode")
SELECT u.IC FATHER, u.COMP CHILD, u.Q/m.Q PER_UNIT FROM used u JOIN made m ON m.IC=u.IC
WHERE m.Q>0"""
Q["split"] = """
WITH mk AS (SELECT "ItemCode" IC, SUM("PlannedQty") Q FROM {co}.OWOR
  WHERE "PostDate">='{since}' GROUP BY "ItemCode"),
bt AS (SELECT L."ItemCode" IC, SUM(L."InvQty") Q FROM {co}.PDN1 L
  JOIN {co}.OPDN G ON G."DocEntry"=L."DocEntry"
  WHERE G."DocDate">='{since}' AND G."CANCELED"='N' GROUP BY L."ItemCode")
SELECT I."ItemCode", IFNULL(mk.Q,0) MADE, IFNULL(bt.Q,0) BOUGHT FROM {co}.OITM I
LEFT JOIN mk ON mk.IC=I."ItemCode" LEFT JOIN bt ON bt.IC=I."ItemCode"
WHERE IFNULL(mk.Q,0)+IFNULL(bt.Q,0)>0"""
Q["cost"] = """
SELECT L."ItemCode", SUM(L."LineTotal")/NULLIF(SUM(L."InvQty"),0) PRICE
FROM {co}.PDN1 L JOIN {co}.OPDN G ON G."DocEntry"=L."DocEntry"
WHERE G."CANCELED"='N' AND G."DocDate">='{since}' AND L."InvQty">0
GROUP BY L."ItemCode\""""
Q["sell"] = """
SELECT L."ItemCode", SUM(L."LineTotal")/NULLIF(SUM(L."Quantity"),0) PRICE, SUM(L."Quantity") QTY
FROM {co}.INV1 L JOIN {co}.OINV H ON H."DocEntry"=L."DocEntry"
WHERE H."CANCELED"='N' AND H."DocDate">='{since}' AND L."Quantity">0
GROUP BY L."ItemCode\""""
Q["stock"] = """
SELECT I2."ItemCode" IC, IFNULL(H2.Q,0) ONHAND, IFNULL(O2.Q,0) ONORDER, I2."ItemName" NAME
FROM {co}.OITM I2
LEFT JOIN (SELECT "ItemCode" C, SUM("OnHand") Q FROM {co}.OITW
  WHERE "WhsCode" IN ({matwh}) GROUP BY "ItemCode") H2 ON H2.C=I2."ItemCode"
LEFT JOIN (SELECT "ItemCode" C, SUM("OnOrder") Q FROM {co}.OITW GROUP BY "ItemCode") O2
  ON O2.C=I2."ItemCode\""""


def run(sql, env, tag=""):
    import time as _t; _s=_t.time()
    print(f"  [stage] {tag} ...", file=sys.stderr, flush=True)
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql); p = fh.name
    cmd = [HANA] + (["-env", env] if env else []) + ["-csv", "-f", p]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    finally:
        os.unlink(p)
    if r.returncode != 0 or r.stdout.lstrip().startswith("QUERY ERROR"):
        sys.exit("hana-sql failed:\n" + r.stdout + r.stderr)
    rows = list(csv.DictReader(r.stdout.splitlines()))
    print(f"  [stage] {tag} done {len(rows)} rows in {_t.time()-_s:.1f}s", file=sys.stderr, flush=True)
    return rows


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env"); ap.add_argument("--groups"); ap.add_argument("--csv")
    a = ap.parse_args()
    today = date.today()
    m1 = today.replace(day=1); m0 = (m1 - timedelta(days=1)).replace(day=1)
    since = today - timedelta(days=WINDOW)
    grp = ""
    if a.groups:
        gl = ",".join("'%s'" % g.strip().upper() for g in a.groups.split(",") if g.strip())
        grp = 'AND I."U_Sub_Group" IN (%s)' % gl

    reqs = run(Q["req"].format(co=CO, pct=MSL_PCT, m0=m0, m1=m1, fgwh=FG_WH, grp=grp,
                               wip=today - timedelta(days=WIP_AGE)), a.env)
    bom = collections.defaultdict(list)
    for r in run(Q["bom"].format(co=CO), a.env, "bom"):
        y = f(r["YIELD"]) or 1.0
        bom[r["FATHER"]].append((r["CHILD"], f(r["QTY"]) / y))
    recipe = collections.defaultdict(list)
    for r in run(Q["recipe"].format(co=CO, since=since), a.env, "recipe"):
        if r["FATHER"] != r["CHILD"] and not r["CHILD"].startswith("JWPL"):
            recipe[r["FATHER"]].append((r["CHILD"], f(r["PER_UNIT"])))
    pct_made = {}
    for r in run(Q["split"].format(co=CO, since=since), a.env, "split"):
        mk, bt = f(r["MADE"]), f(r["BOUGHT"])
        if mk + bt > 0: pct_made[r["ItemCode"]] = 100.0 * mk / (mk + bt)
    cost = {r["ItemCode"]: f(r["PRICE"]) for r in run(Q["cost"].format(co=CO, since=since), a.env, "cost")}
    sell = {r["ItemCode"]: f(r["PRICE"]) for r in run(Q["sell"].format(co=CO, since=since), a.env, "sell")}
    stock, name = {}, {}
    for r in run(Q["stock"].format(co=CO, matwh=MAT_WH), a.env, "stock"):
        stock[r["IC"]] = f(r["ONHAND"]) + f(r["ONORDER"]); name[r["IC"]] = r["NAME"]

    def made(c): return pct_made.get(c, 0) >= MADE_THRESHOLD and c in recipe

    # Per-unit cost and oil mix. Memoised AND cycle-broken.
    #
    # The blend graph is not a tree and not even a DAG: olive is made partly from
    # groundnut, groundnut partly from olive. A plain depth-capped walk therefore
    # re-expands the same nodes down every path — ~10 branches per level, 8 deep,
    # 10^8 traversals. Caching alone does not fix it, because nothing is cached
    # until the first (exponential) expansion returns.
    #
    # So: an explicit "visiting" set breaks the cycle at the point it closes, and
    # every item is cached the moment it resolves.
    _cache = {}

    def unit_of(code, visiting=frozenset()):
        """(cost, Counter of bought-oil litres) for ONE unit of `code`."""
        if code in _cache:
            return _cache[code]
        if code in visiting:                      # cycle: treat as bought here
            return (cost.get(code, 0.0),
                    collections.Counter({code: 1.0} if code[:2] in ("RM", "SF") else {}))
        kids = recipe[code] if made(code) else (bom.get(code, []) if code in bom else [])
        if not kids:
            oils = collections.Counter()
            if code[:2] in ("RM", "SF"):
                oils[code] = 1.0
            res = (cost.get(code, 0.0), oils)
        else:
            c = 0.0
            oils = collections.Counter()
            deeper = visiting | {code}
            for ch, per in kids:
                cc, oo = unit_of(ch, deeper)
                c += per * cc
                for k, v in oo.items():
                    oils[k] += per * v
            res = (c, oils)
        _cache[code] = res
        return res

    def rollup(code, qty, depth, cost_acc, oil_acc):
        c, oils = unit_of(code)
        cost_acc[0] += qty * c
        for k, v in oils.items():
            oil_acc[k] += qty * v

    print("  [stage] rollup ...", file=sys.stderr, flush=True)
    rows = []
    for _n, r in enumerate(reqs):
        need = f(r["REQ"])
        if need <= 0: continue
        c = [0.0]; oils = collections.Counter()
        for ch, per in bom.get(r["FG"], []):
            rollup(ch, per, 1, c, oils)
        oil_l = sum(oils.values())
        price = sell.get(r["FG"], 0.0)
        if price <= 0 or oil_l <= 0: continue
        contrib = price - c[0]
        rows.append(dict(fg=r["FG"], name=r["NAME"], grp=r["GRP"], need=need,
                         oih=f(r["OIH"]), price=price, mat=c[0], contrib=contrib,
                         oil_per=oil_l, per_litre=contrib / oil_l, oils=oils))

    rows.sort(key=lambda x: -x["per_litre"])

    pool = {o: stock.get(o, 0.0) for o in {k for r in rows for k in r["oils"]}}
    pool0 = dict(pool)

    def take(r, units):
        for o, per in r["oils"].items():
            if pool.get(o, 0) < per * units: return 0
        for o, per in r["oils"].items(): pool[o] -= per * units
        return units

    # committed orders first, then down the ranking
    print("  [stage] allocate ...", file=sys.stderr, flush=True)
    plan = collections.Counter()
    for r in sorted(rows, key=lambda x: -x["per_litre"]):
        if r["oih"] > 0: plan[r["fg"]] += take(r, min(r["oih"], r["need"]))
    for _m, r in enumerate(rows):
        # int(), not float. With a fractional remainder (lo=0.0, hi=0.5) the
        # midpoint floors back to 0.0 every pass and the search never terminates
        # — FG0000306 hung the whole engine on a part-bottle remainder.
        rest = int(r["need"] - plan[r["fg"]])
        if rest > 0:
            lo, hi = 0, rest
            while lo < hi:
                mid = (lo + hi + 1) // 2
                ok = all(pool.get(o, 0) >= per * mid for o, per in r["oils"].items())
                lo, hi = (mid, hi) if ok else (lo, mid - 1)
            if lo > 0: plan[r["fg"]] += take(r, lo)

    tot_need = sum(r["need"] for r in rows)
    tot_plan = sum(plan.values())
    print(f"ALLOCATION — {a.groups or 'all'} | prices & recipes from last {WINDOW}d\n")
    print(f"{'RANK':<5}{'SKU':<40}{'Rs/L OIL':>10}{'NEED':>10}{'CAN MAKE':>10}{'OIL L':>10}")
    for i, r in enumerate(rows, 1):
        made_q = plan[r["fg"]]
        flag = "" if made_q >= r["need"] else ("  PARTIAL" if made_q > 0 else "  << NONE")
        print(f"{i:<5}{r['name'][:39]:<40}{r['per_litre']:>10.2f}{r['need']:>10,.0f}"
              f"{made_q:>10,.0f}{r['oil_per']*made_q:>10,.0f}{flag}")
    print(f"\nDemand {tot_need:,.0f} bottles -> can make {tot_plan:,.0f} "
          f"({100*tot_plan/tot_need if tot_need else 0:.0f}%)")
    print(f"\n{'BASE OIL':<38}{'AVAILABLE':>13}{'USED':>13}{'LEFT':>13}")
    # Show EVERY oil, including the ones at zero. A pool at zero is not "nothing to
    # report" — it is the reason a SKU could not be made, and it was the single most
    # important line being hidden by a >0 filter.
    blocked = collections.Counter()
    for r in rows:
        if plan[r["fg"]] < r["need"]:
            for o in r["oils"]:
                if pool.get(o, 0) <= 0: blocked[o] += 1
    for o in sorted(pool0, key=lambda x: -pool0[x]):
        mark = f"  <<< BLOCKING {blocked[o]} SKUs" if blocked.get(o) else ""
        print(f"{name.get(o,o)[:37]:<38}{pool0[o]:>13,.0f}{pool0[o]-pool[o]:>13,.0f}{pool[o]:>13,.0f}{mark}")

    if a.csv:
        os.makedirs(os.path.dirname(os.path.abspath(a.csv)), exist_ok=True)
        with open(a.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rank","code","name","group","rs_per_litre_oil","sell_price",
                        "material_cost","contribution","oil_litres_per_bottle","need","can_make"])
            for i, r in enumerate(rows, 1):
                w.writerow([i, r["fg"], r["name"], r["grp"], f"{r['per_litre']:.2f}",
                            f"{r['price']:.2f}", f"{r['mat']:.2f}", f"{r['contrib']:.2f}",
                            f"{r['oil_per']:.3f}", f"{r['need']:.0f}", f"{plan[r['fg']]:.0f}"])
        print(f"\nwrote {a.csv}")


if __name__ == "__main__":
    main()
