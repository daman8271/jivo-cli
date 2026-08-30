#!/usr/bin/env python3
"""
JIVO Oil — 1-Aug-2026 capability model.

Standing on 1 Aug with the stock we actually had and the POs already inbound:
what could we have MADE, and where does it run out?

Method (deliberately explicit — someone will check it):
  1. net_required = plan_pieces - finished_goods_on_hand - open_WIP   (floored at 0)
  2. availability per component = Aug-1 stock in the allow-listed godowns.
     A second pass adds the open PO quantity (qty_open_aug1). Both are reported.
  3. Multi-level netting. A component JIVO MAKES (the 2 blends, the 3 blown PET
     bottles, 3 more declared-MAKE oils) is available as (its own stock) PLUS
     (what its own inputs could produce). A leaf is only its own stock.
  4. makeable = min over components of (available / per-piece usage), capped at
     net_required. The binding component is the argmin — reported at the DEEPEST
     level, so if a blend is short because an oil under it is short, the oil is named.
  5. SHARED COMPONENTS: a naive per-SKU minimum double-counts a shared bottleneck.
     SKUs are therefore processed in PLAN PRIORITY ORDER (largest plan litres
     first) and each one CONSUMES from a running pool. This is an allocation
     CHOICE, not a fact — a different order gives a different per-SKU answer
     (the aggregate makeable total moves very little).

Read-only. Writes a CSV.
"""
import argparse, collections, csv, io, os, sys

J    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # jolly/
SCR  = os.environ.get("CAPSCRATCH", "/private/tmp/claude-501/-Users-damanpreetsingh-jivo-cli-jolly/fa970459-e8af-4540-91f8-0d51d51cf2e9/scratchpad")
EPS  = 1e-6
INF  = 1e15

# Held by the business, not by materials (Daman, 2026-08-29) — same set plan_explode holds.
NOT_READY = {"FG0000451": "SKU not ready", "FG0000452": "SKU not ready",
             "FG0000448": "held; Manav owns the recipe"}

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def rd(p):
    return list(csv.DictReader(open(p)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(J, "out", "aug01-capability.csv"))
    a = ap.parse_args()

    # ---------- item master ---------------------------------------------------
    items = {r["CODE"]: r for r in rd(os.path.join(SCR, "items.csv"))}

    # ---------- BOMs (identical construction to engine/plan_explode.py) -------
    bom = collections.defaultdict(list)
    for r in rd(os.path.join(SCR, "bom.csv")):
        y = f(r["Y"]) or 1.0
        bom[r["F"]].append((r["C"], f(r["Q"]) / y))
    n_sap = len(bom)

    recon = collections.defaultdict(list)
    for x in rd(os.path.join(J, "reference", "reconstructed-boms.csv")):
        if x["father"] not in bom:
            recon[x["father"]].append((x["child"], float(x["per_piece"])))
    for k, v in recon.items():
        bom[k] = v

    BLENDS = {"RM0000021", "RM0000040"}
    for x in rd(os.path.join(J, "reference", "blend-recipes.csv")):
        bom.setdefault(x["blend"], []).append((x["component"], float(x["per_litre"])))

    # ---------- plan ----------------------------------------------------------
    plan = rd(os.path.join(J, "out", "plan-aug-resolved.csv"))   # all 99; 3 carry a ZERO plan

    # ---------- BOM-yield guard (same rule as plan_explode.py) ----------------
    yfix = {}
    for r in plan:
        c, lpc = r["code"], f(r["litres_per_piece"])
        if c not in bom or not lpc: continue
        boil = sum(per for ch, per in bom[c] if ch.startswith("RM"))
        if not boil: continue
        ratio = boil / lpc
        n = round(ratio)
        if n >= 2 and abs(ratio - n) / n < 0.02:
            yfix[c] = float(n)

    # effective per-PIECE direct BOM for each planned SKU
    direct = {}
    for r in plan:
        c = r["code"]
        if c in bom:
            s = yfix.get(c, 1.0)
            direct[c] = [(ch, per / s) for ch, per in bom[c] if ch != c]

    # ---------- the 1-Aug position -------------------------------------------
    stock = {r["code"]: f(r["onhand_aug01"]) for r in rd(os.path.join(J, "out", "aug01-stock.csv"))}
    po = collections.Counter()
    for r in rd(os.path.join(J, "out", "aug01-open-po.csv")):
        po[r["code"]] += f(r["qty_open_aug1"])

    wf = rd(os.path.join(J, "out", "aug01-wip-fg.csv"))
    fg_on = {r["code"]: f(r["qty_aug01"]) for r in wf if r["kind"] == "FG"}
    wip_on, wip_stale = collections.Counter(), collections.Counter()
    for r in wf:
        if r["kind"] != "WIP": continue
        wip_on[r["code"]] += f(r["qty_aug01"])
        if "STALE" in r["note"] or "BACKDATED" in r["note"]:
            wip_stale[r["code"]] += f(r["qty_aug01"])

    # extra stock for BOM children the components file never listed (held SKUs etc.)
    extra = os.path.join(SCR, "extra-stock.csv")
    if os.path.exists(extra):
        for r in rd(extra):
            stock.setdefault(r["CODE"], f(r["OH"]))

    # ---------- capacity / consume -------------------------------------------
    def capacity(code, pool, chain, memo_depth=0, oil_mode="bom", pack_mode="real"):
        """max units of `code` its INPUTS could produce from pool. (qty, deepest_binder)"""
        kids = bom.get(code)
        if not kids or memo_depth > 8: return 0.0, None
        best, who = None, None
        for ch, per in kids:
            if per <= 0 or ch == code or ch in chain: continue
            k = alias(ch, oil_mode)
            avail = INF if (ch in OILS and oil_mode == "inf") else (
                    INF if (ch not in OILS and pack_mode == "inf" and ch.startswith("PM")) else pool.get(k, 0.0))
            deep = None
            if ch in bom and oil_mode in ("bom", "inf"):
                sub, subdeep = capacity(ch, pool, chain | {code}, memo_depth + 1, oil_mode, pack_mode)
                deep = subdeep
                avail += sub
            r = avail / per
            if best is None or r < best - EPS:
                best, who = r, (deep or ch)
        if best is None: return 0.0, None
        return max(best, 0.0), who

    def consume(code, qty, pool, chain, depth=0, oil_mode="bom", pack_mode="real"):
        if qty <= EPS or depth > 8: return
        for ch, per in bom.get(code, []):
            if ch == code or ch in chain: continue
            if ch in OILS and oil_mode == "inf": continue
            if pack_mode == "inf" and ch.startswith("PM"): continue
            need = qty * per
            k = alias(ch, oil_mode)
            have = pool.get(k, 0.0)
            take = min(have, need)
            pool[k] = have - take
            rem = need - take
            if rem > EPS:
                if ch in bom and oil_mode in ("bom", "inf"):
                    consume(ch, rem, pool, chain | {code}, depth + 1, oil_mode, pack_mode)
                else:
                    pool[k] = pool.get(k, 0.0) - rem

    # ---- scenario machinery -------------------------------------------------
    # oil_mode: 'bom'  = every RM code stands alone, BOMs followed literally
    #           'group'= loose oils interchangeable INSIDE their OITM.U_Sub_Group
    #           'all'  = every LTR loose oil is one pool
    #           'inf'  = oil never binds (isolates the packaging ceiling)
    # pack_mode:'real' | 'inf'  (isolates the oil ceiling)
    OILS = {c for c, r in items.items()
            if c.startswith("RM") and r.get("UOM") == "LTR"}
    GRP  = {c: "GRP:" + (items[c].get("KIND") or "?") for c in OILS}

    def alias(code, oil_mode):
        if code not in OILS or oil_mode in ("bom", "inf"): return code
        return GRP[code] if oil_mode == "group" else "GRP:ALLOIL"

    def run(with_po, po_src=None, oil_mode="bom", pack_mode="real"):
        pool = {}
        for k, v in stock.items():
            a = alias(k, oil_mode); pool[a] = pool.get(a, 0.0) + v
        if with_po:
            for k, v in (po_src if po_src is not None else po).items():
                a = alias(k, oil_mode); pool[a] = pool.get(a, 0.0) + v
        res = {}
        for r in order:
            c = r["code"]
            nr = net_req[c]
            if c in NOT_READY:
                res[c] = (0.0, "HELD", "HELD"); continue
            if c not in direct:
                res[c] = (nr, "NO_BOM", "NO_BOM"); continue
            if nr <= 0:
                res[c] = (0.0, "", ""); continue
            cap, who, root = None, None, None
            for ch, per in direct[c]:
                if per <= 0: continue
                k = alias(ch, oil_mode)
                avail = INF if (ch in OILS and oil_mode == "inf") else (
                        INF if (pack_mode == "inf" and ch.startswith("PM")) else pool.get(k, 0.0))
                deep = None
                if ch in bom and oil_mode in ("bom", "inf"):
                    sub, subdeep = capacity(ch, pool, frozenset({c}), 0, oil_mode, pack_mode)
                    deep = subdeep
                    avail += sub
                ratio = avail / per
                if cap is None or ratio < cap - EPS:
                    cap, who, root = ratio, ch, (deep or ch)
            mk = max(0.0, min(nr, cap if cap is not None else 0.0))
            consume(c, mk, pool, frozenset(), 0, oil_mode, pack_mode)
            res[c] = (mk, who or "", root or who or "")
        return res, pool

    # ---------- net requirement, priority order ------------------------------
    net_req = {}
    for r in plan:
        c = r["code"]
        net_req[c] = max(0.0, f(r["pieces"]) - fg_on.get(c, 0.0) - wip_on.get(c, 0.0))
    order = sorted(plan, key=lambda r: -f(r["litres"]))          # ALLOCATION CHOICE

    # find BOM children with no stock figure at all -> report, treat as 0
    seen, missing = set(), set()
    def walk(code, ch=frozenset(), d=0):
        if d > 8: return
        for c2, _ in bom.get(code, []):
            if c2 == code or c2 in ch: continue
            seen.add(c2); walk(c2, ch | {code}, d + 1)
    for r in plan:
        walk(r["code"])
    for c in seen:
        if c not in stock: missing.add(c)

    res_s, pool_s = run(False)
    res_p, pool_p = run(True)

    # SENSITIVITY: the WIP probe proved 190 of 193 open work orders are stale
    # carry-overs (97% of JIVO Oil WOs close within a week; these are months old).
    # Re-run with stale WIP NOT counted as already-in-progress.
    net_req_full = dict(net_req)
    for r in plan:
        c = r["code"]
        net_req[c] = max(0.0, f(r["pieces"]) - fg_on.get(c, 0.0)
                              - (wip_on.get(c, 0.0) - wip_stale.get(c, 0.0)))
    res_p2, _ = run(True)
    res_s2, _ = run(False)
    net_req_nostale = dict(net_req)
    net_req = net_req_full

    # SENSITIVITY: 97.8% of the open PO lines were already past due on 1 Aug
    # (337 of them by more than a year). Restrict the inbound to lines ORDERED
    # in the 90 days to 1 Aug — i.e. what a buyer would actually still expect.
    po_recent = collections.Counter()
    for r in rd(os.path.join(J, "out", "aug01-open-po.csv")):
        if r["order_date"] >= "2026-05-03":
            po_recent[r["code"]] += f(r["qty_open_aug1"])
    res_p3, _ = run(True, po_recent)

    # ---------- total component demand on the NET requirement -----------------
    demand = collections.Counter()
    def expl(code, qty, ch=frozenset(), d=0):
        if d > 8: return
        for c2, per in bom.get(code, []):
            if c2 == code or c2 in ch: continue
            demand[c2] += qty * per
            expl(c2, qty * per, ch | {code}, d + 1)
    for r in plan:
        c = r["code"]
        if c in NOT_READY or c not in direct: continue
        expl(c, net_req[c] / yfix.get(c, 1.0))

    # ---------- write ---------------------------------------------------------
    rows = []
    for r in plan:
        c   = r["code"]
        pcs = f(r["pieces"]); lpc = f(r["litres_per_piece"])
        ms, bs, rs = res_s[c]
        mp, bp, rp = res_p[c]
        note = ("HELD — SKU not ready, business hold not a material shortage" if bp == "HELD"
                else ("no BOM in SAP" if bp == "NO_BOM"
                      else ("net requirement already covered by FG + WIP" if net_req[c] <= 0 else "")))
        short = max(0.0, net_req[c] - mp)
        rows.append(dict(
            code=c, sku=r["sku"], plan_pieces=int(round(pcs)),
            fg_onhand=int(round(fg_on.get(c, 0.0))), wip=int(round(wip_on.get(c, 0.0))),
            net_required=int(round(net_req[c])),
            makeable_stock_only=int(ms), makeable_with_po=int(mp),
            binding_component=bp,
            binding_component_name=(items.get(bp, {}).get("NAME", "") if bp not in ("", "HELD", "NO_BOM") else
                                    ("held — SKU not ready" if bp == "HELD" else
                                     ("no BOM in SAP" if bp == "NO_BOM" else ""))),
            root_binding_component=rp,
            root_binding_component_name=(items.get(rp, {}).get("NAME", "") if rp not in ("", "HELD", "NO_BOM") else ""),
            shortfall_pieces=int(round(short)),
            plan_litres_at_risk=round(short * lpc, 1),
            plan_litres=round(f(r["litres"]), 1),
            litres_per_piece=lpc,
            makeable_litres_with_po=round(mp * lpc, 1),
            makeable_litres_stock_only=round(ms * lpc, 1),
            binding_stock_only=bs,
            wip_stale_pieces=int(round(wip_stale.get(c, 0.0))),
            note=note))
    rows.sort(key=lambda x: -x["plan_litres_at_risk"])
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    # ---------- summary -------------------------------------------------------
    PL  = sum(x["plan_litres"] for x in rows)
    MLP = sum(x["makeable_litres_with_po"] for x in rows)
    MLS = sum(x["makeable_litres_stock_only"] for x in rows)
    NRL = sum(x["net_required"] * x["litres_per_piece"] for x in rows)
    FGL = sum(x["fg_onhand"] * x["litres_per_piece"] for x in rows)
    WPL = sum(x["wip"] * x["litres_per_piece"] for x in rows)

    print(f"SAP production BOMs {n_sap}; reconstructed {len(recon)}; blends {len(BLENDS)}")
    print(f"BOM-yield guard fired on {len(yfix)} FGs")
    print(f"missing stock figure for {len(missing)} BOM children: {sorted(missing)[:20]}")
    print(f"\nplan litres            {PL:>14,.0f}")
    print(f"FG on hand (litres)    {FGL:>14,.0f}")
    print(f"WIP (litres)           {WPL:>14,.0f}   of which stale {sum(x['wip_stale_pieces']*x['litres_per_piece'] for x in rows):,.0f}")
    print(f"net required           {NRL:>14,.0f}")
    print(f"makeable STOCK ONLY    {MLS:>14,.0f}   = {100*MLS/PL:.1f}% of plan")
    print(f"makeable WITH PO       {MLP:>14,.0f}   = {100*MLP/PL:.1f}% of plan")
    print(f"plan servable (FG+WIP+makeable, with PO) = {100*(MLP+FGL+WPL)/PL:.1f}%")

    full = [x for x in rows if x["net_required"] > 0 and x["shortfall_pieces"] == 0 and x["binding_component"] not in ("NO_BOM",)]
    zero = [x for x in rows if x["net_required"] > 0 and x["makeable_with_po"] == 0]
    nobom = [x for x in rows if x["binding_component"] == "NO_BOM"]
    held  = [x for x in rows if x["binding_component"] == "HELD"]
    print(f"\nSKUs fully makeable (net req > 0, zero shortfall) : {len(full)}")
    print(f"SKUs completely blocked (makeable 0)             : {len(zero)}")
    print(f"SKUs with NO BOM (unconstrained, flagged)        : {len(nobom)}  {[x['code'] for x in nobom]}")
    print(f"SKUs HELD (not ready)                            : {len(held)}  {[x['code'] for x in held]}")
    print(f"SKUs already covered by FG+WIP (net req 0)       : {len([x for x in rows if x['net_required']==0])}")

    # bottlenecks
    agg = collections.defaultdict(lambda: dict(skus=0, litres=0.0, blocked=0))
    for x in rows:
        b = x["root_binding_component"]
        if b in ("", "HELD", "NO_BOM"): continue
        if x["shortfall_pieces"] <= 0: continue
        agg[b]["skus"] += 1
        agg[b]["litres"] += x["plan_litres_at_risk"]
        if x["makeable_with_po"] == 0: agg[b]["blocked"] += 1
    print("\nTOP BOTTLENECKS (binding on a SKU that fell short), with-PO basis:")
    print(f"{'code':<12}{'name':<46}{'SKUs':>5}{'fullblk':>8}{'litres@risk':>14}{'demand':>13}{'avail+PO':>13}{'short':>13} uom")
    out_b = []
    for b, d in sorted(agg.items(), key=lambda kv: -kv[1]["litres"])[:15]:
        dem = demand.get(b, 0.0); av = stock.get(b, 0.0) + po.get(b, 0.0)
        sh  = max(0.0, dem - av)
        uom = items.get(b, {}).get("UOM", "")
        out_b.append((b, items.get(b, {}).get("NAME", ""), d["skus"], d["blocked"], d["litres"], dem, av, sh, uom))
        print(f"{b:<12}{items.get(b,{}).get('NAME','')[:44]:<46}{d['skus']:>5}{d['blocked']:>8}"
              f"{d['litres']:>14,.0f}{dem:>13,.0f}{av:>13,.0f}{sh:>13,.0f} {uom}")

    print("\nWORST 15 SKUs by plan litres at risk:")
    for x in rows[:15]:
        print(f"  {x['code']:<12}{x['sku'][:40]:<42}plan {x['plan_litres']:>10,.0f}L  "
              f"mk {x['makeable_litres_with_po']:>10,.0f}L  risk {x['plan_litres_at_risk']:>10,.0f}L  "
              f"<- {x['binding_component']} {x['binding_component_name'][:28]}")

    # sensitivity: stale WIP excluded
    nr2 = sum(max(0.0, x["plan_pieces"] - x["fg_onhand"] - (x["wip"] - x["wip_stale_pieces"])) * x["litres_per_piece"] for x in rows)
    lpc_of = {x["code"]: x["litres_per_piece"] for x in rows}
    m2p = sum(res_p2[c][0]*lpc_of[c] for c in lpc_of)
    m2s = sum(res_s2[c][0]*lpc_of[c] for c in lpc_of)
    print(f"\nSENSITIVITY — STALE WIP not counted as in-progress:")
    print(f"  net required {sum(net_req_nostale[c]*lpc_of[c] for c in lpc_of):,.0f} L (vs {NRL:,.0f} L)")
    print(f"  makeable with PO {m2p:,.0f} L = {100*m2p/PL:.1f}% of plan (vs {100*MLP/PL:.1f}%)")
    print(f"  makeable stock only {m2s:,.0f} L = {100*m2s/PL:.1f}% of plan (vs {100*MLS/PL:.1f}%)")
    m3 = sum(res_p3[c][0]*lpc_of[c] for c in lpc_of)
    print(f"\nSENSITIVITY — only POs ORDERED within 90d of 1 Aug count as inbound:")
    print(f"  makeable {m3:,.0f} L = {100*m3/PL:.1f}% of plan (vs {100*MLP/PL:.1f}% on all open POs)")

    print("\nSCENARIOS (all on the with-PO basis, same net requirement, same priority order):")
    def tot(rr): return sum(rr[c][0]*lpc_of[c] for c in lpc_of)
    scen = [
      ("A  BOMs followed literally  (DELIVERED)", "bom",   "real"),
      ("B  oil never binds -> PACKAGING ceiling", "inf",   "real"),
      ("C  packaging never binds -> OIL ceiling", "bom",   "inf"),
      ("D  oils swappable inside U_Sub_Group",    "group", "real"),
      ("E  every loose oil one pool",             "all",   "real"),
      ("F  oils pooled AND packaging free",       "all",   "inf"),
    ]
    for label, om, pm in scen:
        rr, _ = run(True, None, om, pm)
        t = tot(rr)
        print(f"  {label:<42}{t:>12,.0f} L   {100*t/PL:>5.1f}% of plan")

    # oil position in aggregate, independent of any BOM
    oil_stock = sum(v for k, v in stock.items() if k in OILS)
    oil_po    = sum(v for k, v in po.items() if k in OILS)
    import random
    base = list(order)
    alts = [("smallest plan litres first", sorted(base, key=lambda r: f(r["litres"]))),
            ("SKU code order", sorted(base, key=lambda r: r["code"]))]
    for i in range(6):
        rnd = list(base); random.Random(100+i).shuffle(rnd); alts.append((f"random #{i+1}", rnd))
    print("\nALLOCATION-ORDER SENSITIVITY (the priority rule is a CHOICE):")
    print(f"  {'largest plan litres first (DELIVERED)':<40}{MLP:>12,.0f} L  {100*MLP/PL:>5.1f}%")
    for label, o in alts:
        order[:] = o
        rr, _ = run(True)
        t = sum(rr[c][0]*lpc_of[c] for c in lpc_of)
        print(f"  {label:<40}{t:>12,.0f} L  {100*t/PL:>5.1f}%")
    order[:] = base

    print(f"\nOIL POSITION ON 1 AUG, ignoring every BOM (LTR loose-oil codes only):")
    print(f"  on hand in the allow-listed godowns  {oil_stock:>12,.0f} L")
    print(f"  on open PO                            {oil_po:>12,.0f} L")
    print(f"  together                              {oil_stock+oil_po:>12,.0f} L = "
          f"{100*(oil_stock+oil_po)/PL:.1f}% of the {PL:,.0f} L plan")
    print(f"wrote {a.out} — {len(rows)} rows")

if __name__ == "__main__":
    main()
