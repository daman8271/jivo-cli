#!/usr/bin/env python3
"""
JIVO Oil — explode the August plan through SAP's BOMs into oil and packaging.

Input  : out/plan-aug-resolved.csv  (99 SKUs, litres + pieces, unit-clean)
Output : out/plan-aug-components.csv

Classification rule (2026-08-29). MAKE/BUY comes from what SAP DECLARES -- does
the item have a production BOM (OITT TreeType='P'). The behavioural signal (share
of volume produced through OWOR over 90 days) is carried ALONGSIDE it as a
cross-check and never overrides it. Where the two disagree the row is FLAGGED, not
silently resolved: an earlier engine used a >50% behavioural threshold as the
value, which turned 3 declared blends into 7 and labelled PET bottles as blends.

Units (C-0050): everything internal is LITRES and PIECES. Sale-side tonnes
(1 T = 1,000 L) and purchase-side tonnes (1 T = 1,000 kg @ 910 g/L) are printed
only at the edges.

Read-only.
"""
import argparse, collections, csv, io, os, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
CO   = "JIVO_OIL_HANADB"
DENSITY_G_PER_L = 910.0
MAX_DEPTH = 8
RECIPE_WINDOW = 90
AS_OF = "2026-08-01"     # BACKTEST: nothing after this date may enter any calculation

def q(env, sql):
    r = subprocess.run([HANA, "-env", env, "-csv", sql],
                       capture_output=True, text=True, timeout=300)
    if r.returncode:
        sys.exit(f"HANA error: {r.stderr[:800]}")
    return list(csv.DictReader(io.StringIO(r.stdout)))

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=os.path.join(REPO, "connections", "hana-new.env"))
    ap.add_argument("--plan", default="out/plan-aug-resolved.csv")
    ap.add_argument("--csv",  default="out/plan-aug-components.csv")
    a = ap.parse_args()

    plan = [r for r in csv.DictReader(open(a.plan)) if r["pieces"]]
    print(f"plan: {len(plan)} SKUs with demand")

    # ---- BOMs: father -> [(child, qty per one father piece)] -----------------
    bom = collections.defaultdict(list)
    for r in q(a.env, f'''SELECT T."Code" F, T."Qauntity" Y, C."Code" C, C."Quantity" Q
        FROM {CO}.OITT T JOIN {CO}.ITT1 C ON C."Father"=T."Code"
        WHERE T."TreeType"='P' AND C."Type" <> 290'''):
        y = f(r["Y"]) or 1.0
        bom[r["F"]].append((r["C"], f(r["Q"]) / y))
    print(f"BOMs loaded: {len(bom)} parents")

    # ---- reconstructed BOMs --------------------------------------------------
    # 4 planned SKUs have no BOM anywhere: no OITT row of any TreeType, in any of
    # the three company DBs, never produced, never invoiced, zero stock. They are
    # new item-master rows (created Jun/Jul 2026) that reached the plan before
    # anyone built their bill of materials. Every packaging component they need
    # ALREADY EXISTS in the item master -- the labels were created and never used.
    # These are rebuilt from the nearest sibling BOM and are flagged RECONSTRUCTED
    # in the output. They are an estimate, not SAP data.
    recon = collections.defaultdict(list)
    rpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "reference", "reconstructed-boms.csv")
    if os.path.exists(rpath):
        for x in csv.DictReader(open(rpath)):
            if x["father"] not in bom:
                recon[x["father"]].append((x["child"], float(x["per_piece"])))
        for k, v in recon.items(): bom[k] = v
        if recon: print(f"reconstructed BOMs applied: {len(recon)} FGs")

    # ---- the two real blends (Daman, 2026-08-29) ------------------------------
    # JIVO blends exactly TWO oils: RM0000021 LOOSE OIL GOLD and RM0000040 SO OLIVE.
    # Everything else is bought, whatever the production-order history suggests.
    # Neither has a BOM, so the recipe comes from what was actually issued to their
    # production orders over 180 days (OWOR -> WOR1). Both sum to ~100%.
    for x in csv.DictReader(open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "reference", "blend-recipes.csv"))):
        bom.setdefault(x["blend"], []).append((x["component"], float(x["per_litre"])))
    BLENDS = {"RM0000021", "RM0000040"}
    print(f"blends: {', '.join(sorted(BLENDS))} — every other oil is BOUGHT")

    # SKUs in the plan whose product is not ready to sell yet (Daman, 2026-08-29).
    # They carry plan tonnage but nothing should be ordered for them.
    NOT_READY = {"FG0000451": "COLD PRESS SUNFLOWER 200 ML (70 pcs) — SKU not ready",
                 "FG0000452": "SESAME OIL 500 MLS — SKU not ready",
                 "FG0000448": "MUSTARD KACHI GHANI 500 ML — held; Manav owns the recipe"}

    # ---- item master ---------------------------------------------------------
    items = {r["ItemCode"]: r for r in q(a.env, f'''SELECT I."ItemCode", I."ItemName",
        I."U_Sub_Group" KIND, I."InvntryUom" UOM FROM {CO}.OITM I''')}
    print(f"items: {len(items)}")

    # ---- behavioural cross-check: share made through production orders -------
    made_share = {}
    for r in q(a.env, f'''WITH made AS (SELECT "ItemCode" IC, SUM("PlannedQty") Q FROM {CO}.OWOR
          WHERE "PostDate" >= ADD_DAYS(DATE'{AS_OF}', -{RECIPE_WINDOW})
            AND "PostDate" < DATE'{AS_OF}' GROUP BY "ItemCode"),
        recd AS (SELECT L."ItemCode" IC, SUM(L."Quantity") Q FROM {CO}.PDN1 L
          JOIN {CO}.OPDN H ON H."DocEntry"=L."DocEntry"
          WHERE H."DocDate" >= ADD_DAYS(DATE'{AS_OF}', -{RECIPE_WINDOW})
            AND H."DocDate" < DATE'{AS_OF}' AND H."CANCELED"='N'
          GROUP BY L."ItemCode")
        SELECT IFNULL(m.IC, r.IC) IC, IFNULL(m.Q,0) MADE, IFNULL(r.Q,0) BOUGHT
        FROM made m FULL OUTER JOIN recd r ON m.IC=r.IC'''):
        mq, bq = f(r["MADE"]), f(r["BOUGHT"])
        if mq + bq > 0: made_share[r["IC"]] = mq / (mq + bq)

    # ---- explode -------------------------------------------------------------
    need = collections.Counter()       # component -> pieces / litres required
    level = {}
    skipped_self = collections.Counter()

    def explode(code, qty, depth, chain):
        # A component is recorded ONCE, by its parent, in the loop below. A leaf
        # therefore records nothing here -- doing both double-counts every leaf,
        # which is exactly what it did on the first run (oil came out 2.29x the plan).
        if depth > MAX_DEPTH: return
        kids = bom.get(code)
        if not kids: return
        for child, per in kids:
            if child == code or child in chain:        # reprocessing, not new demand
                skipped_self[child] += 1
                continue
            need[child] += qty * per
            level[child] = max(level.get(child, 0), depth)
            explode(child, qty * per, depth + 1, chain | {code})

    # ---- guard: BOMs whose yield (OITT."Qauntity") was never set --------------
    # 10 FG BOMs describe a CASE but carry Qauntity=1, so every component reads as
    # per-bottle when it is per-case. The tell is exact: BOM oil per unit divided by
    # the pack size lands on a whole number equal to the case pack (20x, 16x, 24x,
    # 10x, 4x). Left alone this asked for 289,006 L of oil that no bottle can hold.
    # Genuine overfill across every other SKU is 1,110 L (0.03%), so anything at or
    # above 2x is an error, not wastage.
    yield_fix = {}
    for r in plan:
        c, lpc = r["code"], f(r["litres_per_piece"])
        if c not in bom or not lpc: continue
        bom_oil = sum(per for ch, per in bom[c] if ch.startswith("RM"))
        if not bom_oil: continue
        ratio = bom_oil / lpc
        n = round(ratio)
        if n >= 2 and abs(ratio - n) / n < 0.02:
            yield_fix[c] = float(n)

    unexploded, held = [], []
    for r in plan:
        pieces = f(r["pieces"])
        if r["code"] in NOT_READY:
            held.append(r); continue
        if r["code"] not in bom:
            unexploded.append(r); continue
        explode(r["code"], pieces / yield_fix.get(r["code"], 1.0), 1, frozenset())

    if yield_fix:
        print(f"\nBOM yield unset on {len(yield_fix)} FGs — scaled down by their case pack:")
        for c, n in sorted(yield_fix.items(), key=lambda kv: -kv[1]):
            sku = next(x["sku"] for x in plan if x["code"] == c)
            print(f"    {c:<12}{sku[:46]:<48}/{n:.0f}")

    # ---- write ---------------------------------------------------------------
    out = []
    for code, qty in need.items():
        i = items.get(code, {})
        declared = "BLEND" if code in BLENDS else ("MAKE" if code in bom else "BUY")
        share = made_share.get(code)
        behav = None if share is None else ("MAKE" if share >= 0.5 else "BUY")
        flag = "DECLARED_VS_BEHAVIOUR" if (behav and behav != declared) else ""
        out.append(dict(code=code, name=i.get("ItemName", code), kind=i.get("KIND", ""),
                        uom=i.get("UOM", ""), level=level.get(code, 0),
                        declared=declared, behaviour=behav or "",
                        made_share=f"{share:.2f}" if share is not None else "",
                        required=round(qty, 2), flag=flag))
    out.sort(key=lambda r: -r["required"])
    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

    pm = [r for r in out if r["code"].startswith("PM")]
    rm = [r for r in out if r["code"].startswith("RM")]
    # Only LEAVES are purchases. An intermediate (an oil we blend) carries a real
    # gross requirement, but adding it to its own inputs would count the same
    # litre twice.
    rm_buy = [r for r in rm if r["declared"] == "BUY"]
    rm_make = [r for r in rm if r["declared"] in ("MAKE", "BLEND")]
    oil_l = sum(r["required"] for r in rm_buy)
    print(f"\nwrote {a.csv} — {len(out)} components")
    print(f"  packaging (PM) {len(pm):>4} items  {sum(r['required'] for r in pm):>14,.0f} pcs")
    print(f"  oil to BUY(RM) {len(rm_buy):>4} items  {oil_l:>14,.0f} L")
    print(f"                                {oil_l*DENSITY_G_PER_L/1e6:>14,.1f} purchase-tonnes")
    if rm_make:
        print(f"  oil we MAKE    {len(rm_make):>4} items  "
              f"{sum(r['required'] for r in rm_make):>14,.0f} L  (their inputs are in the buy list)")
    dis = [r for r in out if r["flag"]]
    print(f"\n  declared vs behaviour DISAGREE on {len(dis)} items (flagged, declared wins):")
    for r in dis[:12]:
        print(f"    {r['code']:<12}{r['name'][:40]:<42}declared={r['declared']:<5}"
              f"behaviour={r['behaviour']:<5}({r['made_share']})")
    if held:
        print(f"\n  HELD — SKU not ready, nothing ordered ({len(held)}):")
        for r in held:
            print(f"    {r['code']}  {r['sku'][:44]:<46}{f(r['plan_kl']):>7.1f} kL  {NOT_READY[r['code']]}")
    if unexploded:
        print(f"\n  NO BOM — could not explode {len(unexploded)} SKUs:")
        for r in unexploded:
            print(f"    {r['code']}  {r['sku'][:46]:<48}{f(r['plan_kl']):>7.1f} kL")
    if skipped_self:
        print(f"\n  self-referencing components skipped (reprocessing): {len(skipped_self)}")

if __name__ == "__main__":
    main()
