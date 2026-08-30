#!/usr/bin/env python3
"""
JIVO Oil — what to run tomorrow, per line.

Answers the owner's question directly: given the plan, what is on hand right now, and
what each line can physically do, what should each line fill tomorrow and in what order.

Dated customer demand does NOT exist in SAP (zero FG order lines due beyond 7 days), but
it is not needed for this: the month's plan minus what is already made IS the demand, and
sequencing it is a capacity problem, not a forecasting one.

Line speeds: reference/PLAN-AND-LINES.md (Daman, 2026-08-29). One shift, 12 h.
ANY OIL RUNS ON ANY LINE — a line is constrained by CONTAINER SIZE only, never by oil.
FLUSHING: every oil change costs 400 L of the NEXT oil (Daman, 2026-08-29).
  flush time = 400 L / (pieces_per_hour x litres_per_piece)
  It is cheap in time (4-22 min) and expensive in MATERIAL. Sequence by oil to save
  oil, not to save hours.
PRIORITY (reference/PLANNING-MODEL.md): PO first, then realisation (Rs/L), then
PREMIUM over COMMODITY.

Realisation now comes LIVE from the Control Panel ("god software"), which is the
system that owns this number: jivo sales data -> per-item line_total / litres.
out/realise-by-item.csv.

THE RANKING METRIC IS Rs PER LINE-HOUR, NOT Rs PER LITRE.
Line-hours are the scarce resource, so what matters is what an hour of a line earns:

    Rs/hour = pieces_per_hour x litres_per_piece x realise_Rs_per_litre

Ranking by Rs/L alone would fill the shift with tiny high-value SKUs and waste the
line. Ranking by Rs/hour spends the constraint where it earns most. Premium remains
the tiebreak when two SKUs earn the same per hour.

Read-only against SAP.
"""
import argparse, collections, csv, io, os, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
CO = "JIVO_OIL_HANADB"
FG_WH  = "'BH-BT','BH-PF','GP-FG'"
# BH-GJ is IN for oil (Daman 2026-08-29): imports land there, crude goes to job work
# and cold-press comes back. Excluding it understated oil by 670,038 L.
MAT_WH = "'BH-BS','BH-PM','BH-LO','BH-NM','BH-SDL','GP-NM','GP-FG','BH-GJ'"
HOURS = 12.0

LINES = {
    "JP Machine":    {"1L": 5400},
    "Clear Pack":    {"1L": 4800, "4L": 3000, "5L": 3000},
    "10 Head":       {"1L": 2100, "2L": 1260, "5L": 900},
    "6 Head":        {"1L": 1080, "2L": 720,  "5L": 600},
    "Pouch Machine": {"POUCH": 4200},
    "Tin Head":      {"TIN": 240},
}

def q(env, sql):
    r = subprocess.run([HANA, "-env", env, "-csv", sql], capture_output=True, text=True, timeout=240)
    if r.returncode: sys.exit(f"HANA: {r.stderr[:400]}")
    return list(csv.DictReader(io.StringIO(r.stdout)))

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def slot(r):
    pt = str(r["pack_type"]).upper(); sku = str(r["sku"]).upper(); l = f(r["litres_per_piece"])
    if "DRUM" in pt: return "DRUM"
    if "TIN" in pt or "KGS" in sku: return "TIN"
    if "POUCH" in pt or "POUCH" in sku: return "POUCH"
    if l <= 1.05: return "1L"
    if l <= 2.05: return "2L"
    if l <= 3.05: return "3L"
    if l <= 4.05: return "4L"
    return "5L"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=os.path.join(REPO, "connections", "hana-new.env"))
    ap.add_argument("--hours", type=float, default=HOURS)
    ap.add_argument("--csv", default="out/day-plan.csv")
    ap.add_argument("--plan", default="out/plan-aug-resolved.csv")
    ap.add_argument("--components", default="out/plan-aug-components.csv")
    a = ap.parse_args()

    plan = [r for r in csv.DictReader(open(a.plan)) if r["pieces"]]
    HELD = {"FG0000448", "FG0000451", "FG0000452"}
    plan = [r for r in plan if r["code"] not in HELD]

    comp = list(csv.DictReader(open(a.components)))
    need = {c["code"]: f(c["required"]) for c in comp}

    # BOM: what one piece of each FG consumes
    bom = collections.defaultdict(list)
    for r in q(a.env, f'''SELECT T."Code" F, C."Code" C, C."Quantity"/T."Qauntity" PER
        FROM {CO}.OITT T JOIN {CO}.ITT1 C ON C."Father"=T."Code"
        WHERE T."TreeType"='P' AND C."Type"<>290'''):
        bom[r["F"]].append((r["C"], f(r["PER"])))

    # stock now
    stock = {r["IC"]: f(r["Q"]) for r in q(a.env, f'''SELECT "ItemCode" IC, SUM("OnHand") Q
        FROM {CO}.OITW WHERE "WhsCode" IN ({MAT_WH}) GROUP BY "ItemCode"''')}
    fg = {r["IC"]: f(r["Q"]) for r in q(a.env, f'''SELECT "ItemCode" IC, SUM("OnHand") Q
        FROM {CO}.OITW WHERE "WhsCode" IN ({FG_WH}) GROUP BY "ItemCode"''')}

    # which oil does each SKU need (for changeover grouping)
    oil_of = {}
    for c, kids in bom.items():
        oils = [(k, p) for k, p in kids if k.startswith("RM")]
        if oils: oil_of[c] = max(oils, key=lambda x: x[1])[0]

    # remaining to make, and whether stock allows it
    rows = []
    for r in plan:
        code = r["code"]; want = f(r["pieces"]) - fg.get(code, 0.0)
        if want <= 0: continue
        kids = bom.get(code, [])
        cap = want; binder = ""
        for ch, per in kids:
            if per <= 0: continue
            can = stock.get(ch, 0.0) / per
            if can < cap: cap, binder = can, ch
        rows.append(dict(code=code, sku=r["sku"], head=r.get("head",""), slot=slot(r), want=want,
                         makeable=max(0.0, cap), binder=binder,
                         oil=oil_of.get(code, "?"), lpc=f(r["litres_per_piece"])))

    # ---- assign -------------------------------------------------------------
    # Rule, stated so it can be argued with: take the highest-priority item a line can
    # physically run, then KEEP THAT LINE ON THAT OIL until the oil is exhausted or the
    # shift ends. Only then flush to the next oil. Premium outranks commodity.
    FLUSH_L = 400.0
    free = {ln: a.hours for ln in LINES}
    on_oil = {ln: None for ln in LINES}
    sched = collections.defaultdict(list)
    blocked = []
    flush_oil_used = collections.Counter()

    # realisation Rs/L, live from the Control Panel
    realise = {}
    try:
        for x in csv.DictReader(open("out/realise-by-item.csv")):
            code = str(x["item"]).split("\u2014")[0].split("-")[0].strip()[:9]
            if code.startswith(("FG", "RM", "SF")): realise[code] = f(x["realise"])
    except FileNotFoundError:
        pass
    grp_realise = {}
    for r in rows:
        if r["code"] in realise: continue
    DEFAULT_REALISE = 156.0        # commodity average, used only when an item never sold

    def rs_per_litre(r):
        return realise.get(r["code"], DEFAULT_REALISE)

    def rs_per_hour(r, rate):
        return rate * (r["lpc"] or 1.0) * rs_per_litre(r)

    def prio(r):
        # negative so min() picks the best; premium breaks ties
        best = max((sp[r["slot"]] for sp in LINES.values() if r["slot"] in sp), default=1)
        return (-rs_per_hour(r, best), 0 if str(r.get("head", "")).upper() == "PREMIUM" else 1)

    pool = [r for r in rows if min(r["want"], r["makeable"]) >= 1]
    for r in rows:
        if min(r["want"], r["makeable"]) < 1: blocked.append(r)

    guard = 0
    while pool and guard < 4000:
        guard += 1
        placed = False
        for ln, sp in sorted(LINES.items(), key=lambda kv: -max(kv[1].values())):
            if free[ln] <= 0.02: continue
            runnable = [r for r in pool if r["slot"] in sp]
            if not runnable: continue
            # prefer staying on the oil already in the line — no flush
            # staying on the same oil avoids a 400 L flush, so it gets a head start —
            # but only if it is within 15% of the best alternative on Rs/hour.
            same = [r for r in runnable if r["oil"] == on_oil[ln]]
            best_any = min(runnable, key=prio)
            if same:
                best_same = min(same, key=prio)
                pick = best_same if rs_per_hour(best_same, sp[best_same["slot"]]) >= \
                       0.85 * rs_per_hour(best_any, sp[best_any["slot"]]) else best_any
            else:
                pick = best_any
            rate = sp[pick["slot"]]
            lph = rate * (pick["lpc"] or 1.0)          # line throughput in LITRES/hour
            flush_h = 0.0
            if on_oil[ln] is not None and pick["oil"] != on_oil[ln]:
                flush_h = FLUSH_L / lph                 # 400 L pushed through at line speed
                if flush_h >= free[ln]: continue        # no room to even flush
                flush_oil_used[pick["oil"]] += FLUSH_L
            usable = free[ln] - flush_h
            run = min(pick["want"], pick["makeable"])
            hrs = min(run / rate, usable)
            did = hrs * rate
            if did < 1: continue
            sched[ln].append(dict(**pick, line=ln, rate=rate, pieces=did, hours=hrs,
                                  flush_h=flush_h, realise=rs_per_litre(pick),
                                  rs_hour=rs_per_hour(pick, rate)))
            free[ln] -= (hrs + flush_h)
            on_oil[ln] = pick["oil"]
            pick["want"] -= did
            pick["makeable"] -= did
            if min(pick["want"], pick["makeable"]) < 1: pool.remove(pick)
            placed = True
        if not placed: break
    for r in pool:
        r["why"] = "every line that can run " + r["slot"] + " was full"
        blocked.append(r)

    print(f"=== TOMORROW — one {a.hours:g}-hour shift ===\n")
    tot_p = tot_l = 0; changeovers = 0
    out = []
    for ln in LINES:
        runs = sched.get(ln, [])
        if not runs:
            print(f"{ln:<15} IDLE — nothing it can run is unblocked\n"); continue
        print(f"{ln}  ({a.hours - free[ln]:.1f} h of {a.hours:g})")
        for i, x in enumerate(runs, 1):
            flush = ""
            if x["flush_h"] > 0:
                changeovers += 1
                flush = f"  << FLUSH {FLUSH_L:.0f} L, {x['flush_h']*60:.0f} min"
            lit = x["pieces"] * x["lpc"]
            hd = "P" if str(x.get("head","")).upper() == "PREMIUM" else "c"
            print(f"   {i}. [{hd}] {x['sku'][:36]:<38}{x['pieces']:>8,.0f} pcs {x['hours']:>5.1f} h "
                  f"Rs{x['realise']:>6,.0f}/L  Rs{x['rs_hour']/1000:>6,.0f}k/h{flush}")
            tot_p += x["pieces"]; tot_l += lit
            out.append(dict(line=ln, seq=i, code=x["code"], sku=x["sku"], slot=x["slot"],
                            head=x.get("head",""), oil=x["oil"], rate_per_hr=x["rate"],
                            pieces=round(x["pieces"]), litres=round(lit),
                            hours=round(x["hours"], 2),
                            realise_rs_l=round(x["realise"], 2),
                            rs_per_hour=round(x["rs_hour"]),
                            value_rs=round(x["pieces"]*x["lpc"]*x["realise"]),
                            flush_min=round(x["flush_h"]*60, 1) if x["flush_h"] else ""))
        print()
    with open(a.csv, "w", newline="") as fh:
        if out:
            w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    prem = sum(x["pieces"]*x["lpc"] for ln in sched for x in sched[ln]
               if str(x.get("head","")).upper()=="PREMIUM")
    print(f"TOMORROW'S OUTPUT   {tot_p:>12,.0f} pieces   {tot_l:>12,.0f} L")
    print(f"  of which PREMIUM  {prem:>12,.0f} L ({prem/tot_l*100 if tot_l else 0:.0f}%)")
    fl = sum(flush_oil_used.values())
    print(f"  oil changes       {changeovers:>12}  costing {fl:,.0f} L of flush oil "
          f"({fl/tot_l*100 if tot_l else 0:.1f}% of output)")
    for o, v in flush_oil_used.most_common():
        print(f"      flush into {o}: {v:,.0f} L")
    val = sum(x["pieces"]*x["lpc"]*x["realise"] for ln in sched for x in sched[ln])
    print(f"  at the floor's real ~47% efficiency this lands near {tot_l*0.47:,.0f} L")
    print(f"\n  VALUE OF TOMORROW  Rs {val:>14,.0f}   ({val/1e7:.2f} Cr)")
    print(f"  average realise    Rs {val/tot_l if tot_l else 0:>14,.2f}/L   "
          f"vs PREMIUM 195.72 / COMMODITY 155.98")
    fv = sum(flush_oil_used.values()) * 156
    print(f"  flush oil (reused, so this is the WORST case if it were scrapped): Rs {fv:,.0f}")
    if blocked:
        print(f"\n=== CANNOT RUN ({len(blocked)}) — biggest first ===")
        for r in sorted(blocked, key=lambda x: -x["want"])[:12]:
            why = r.get("why") or f"short of {r['binder']} ({stock.get(r['binder'],0):,.0f} on hand)"
            print(f"   {r['code']:<12}{r['sku'][:42]:<44}{r['want']:>9,.0f} pcs   {why}")
    print(f"\nwrote {a.csv}")

if __name__ == "__main__":
    main()
