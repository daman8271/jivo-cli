#!/usr/bin/env python3
"""
JIVO Oil — THE AUGUST BACKTEST.

Stand on 2026-08-01. Know NOTHING that happened after it. Produce the month's
production schedule, line by line, day by day. It is then scored against what the
factory actually did in August.

  *"We have all the reports for how we ran all the machines in August and we want to
   first make you do the same. We don't want you to cheat."* — Daman, 2026-08-29

NO-LEAKAGE RULES, enforced here and audited on every run:
  * opening stock, FG and WIP  -> as at 2026-08-01 (OITW minus OINM since)
  * inbound material           -> only POs raised BEFORE 1 Aug, landing on their DUE date
  * realisation Rs/L           -> May-Jul 2026 only (out/realise-by-item-PRE-AUG.csv)
  * blend recipes              -> Feb-Jul 2026 production orders only
  * make/buy split             -> 90 days ending 2026-07-31
  * line speeds, flush, packs  -> static master data, not time-dependent
Nothing dated 2026-08-01 or later is read. That is the whole point of the exercise.

THE MODEL
  Demand      the August plan, 96 SKUs, 4,146,400 L (3 not-ready SKUs held)
  Capacity    6 lines x 12 h x 26 days. Any oil runs on any line; only container
              size binds a SKU to a line.
  Flush       Time = 400 L / (line L per hour), EVERY changeover.
              Material = ~400 L per oil ONCE PER MONTH — the flush oil is reused and
              lasts about a month (Daman 2026-08-29), so it is not a per-change cost.
  Oil         STRICT, per oil, from the BOM. Daman 2026-08-29: "the substitutions are
              only done in the SAP" — SAP's work-order components are BOOKKEEPING, not
              a recipe. The floor does not pour soyabean into a sunflower tank. So the
              BOM is the truth and oil is NOT fungible. (An earlier version pooled oil
              and made the month look far more makeable than it was.)
  Packaging   STRICT per item. A mustard label fits nothing but a mustard bottle.
  Synonyms    Several RM codes are THE SAME MATERIAL under different names (Daman,
              2026-08-29): groundnut=peanut, canola=cold-press-rapeseed,
              crude-rapeseed-new=crude-rapeseed-domestic, olive=olive-dark-colour.
              reference/oil-synonyms.csv. Merging them BEFORE any shortage is computed
              is mandatory: a duplicate code invents a shortage on one side and
              stranded stock on the other, and both look completely credible. It cost
              this analysis a phantom 522,373 L groundnut shortage.
  Priority    Rs per LINE-HOUR = pieces/hr x L/piece x realise. Line-hours are the
              scarce resource, so value must be measured per hour of it, not per litre.
              Premium breaks ties.

Read-only.
"""
import argparse, collections, csv, io, os, subprocess, sys
from datetime import date, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
CO = "JIVO_OIL_HANADB"
AS_OF = date(2026, 8, 1)
HELD = {"FG0000448", "FG0000451", "FG0000452"}
FLUSH_L = 400.0
HOURS = 12.0
LINES = {
    "JP Machine":    {"1L": 5400},
    "Clear Pack":    {"1L": 4800, "4L": 3000, "5L": 3000},
    "10 Head":       {"1L": 2100, "2L": 1260, "5L": 900},
    "6 Head":        {"1L": 1080, "2L": 720,  "5L": 600},
    "Pouch Machine": {"POUCH": 4200},
    "Tin Head":      {"TIN": 240},
}
DEFAULT_REALISE = 148.33          # pre-Aug commodity average

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def q(env, sql):
    r = subprocess.run([HANA, "-env", env, "-csv", sql], capture_output=True, text=True, timeout=300)
    if r.returncode: sys.exit(f"HANA: {r.stderr[:400]}")
    return list(csv.DictReader(io.StringIO(r.stdout)))

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

def working_days(n=26):
    d, out = AS_OF, []
    while len(out) < n:
        if d.weekday() != 6: out.append(d)      # Sundays off
        d += timedelta(days=1)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=os.path.join(REPO, "connections", "hana-new.env"))
    ap.add_argument("--days", type=int, default=26)
    ap.add_argument("--hours", type=float, default=HOURS)
    ap.add_argument("--csv", default="out/august-month-plan.csv")
    ap.add_argument("--buy", action="store_true",
                    help="allow oil to be PURCHASED during the month, arriving after the measured lead time")
    ap.add_argument("--lead", type=int, default=11, help="oil lead time in days (measured median)")
    a = ap.parse_args()

    days = working_days(a.days)
    plan = [r for r in csv.DictReader(open("out/plan-aug-resolved.csv"))
            if r["pieces"] and r["code"] not in HELD]
    comp = list(csv.DictReader(open("out/plan-aug-components.csv")))

    # ---- realisation, PRE-AUGUST ONLY ---------------------------------------
    realise = {}
    for x in csv.DictReader(open("out/realise-by-item-PRE-AUG.csv")):
        c = str(x["item"]).split("—")[0].split("-")[0].strip()[:9]
        if c.startswith(("FG", "RM", "SF")): realise[c] = f(x["realise"])

    # ---- oil synonyms: fold every alias onto its canonical code -------------
    SYN = {r["alias"]: r["canonical"]
           for r in csv.DictReader(open("reference/oil-synonyms.csv"))}
    def canon(c): return SYN.get(c, c)

    # ---- BOM ----------------------------------------------------------------
    bom = collections.defaultdict(list)
    for r in q(a.env, f'''SELECT T."Code" F, C."Code" C, C."Quantity"/T."Qauntity" PER
        FROM {CO}.OITT T JOIN {CO}.ITT1 C ON C."Father"=T."Code"
        WHERE T."TreeType"='P' AND C."Type"<>290'''):
        bom[r["F"]].append((canon(r["C"]), f(r["PER"])))
    for x in csv.DictReader(open("reference/reconstructed-boms.csv")):
        if x["father"] not in bom: bom[x["father"]].append((canon(x["child"]), f(x["per_piece"])))

    # ---- OPENING POSITION at 2026-08-01 -------------------------------------
    stock = collections.defaultdict(float)
    for r in csv.DictReader(open("out/aug01-stock.csv")):
        stock[canon(r["code"])] += f(r["onhand_aug01"])
    fg = {}
    for r in csv.DictReader(open("out/aug01-wip-fg.csv")):
        if str(r.get("kind", "")).upper() == "FG": fg[r["code"]] = f(r.get("qty_aug01"))

    # ---- INBOUND: POs raised before 1 Aug, landing on their due date --------
    inbound = collections.defaultdict(lambda: collections.defaultdict(float))
    try:
        for r in csv.DictReader(open("out/aug01-open-po.csv")):
            qty = f(r.get("qty_open_aug1"))
            if qty <= 0: continue
            due = str(r.get("due_date") or "")[:10]
            try: dd = date.fromisoformat(due)
            except ValueError: dd = AS_OF
            if dd < AS_OF: dd = AS_OF                 # already overdue -> available day 1
            inbound[dd][canon(r["code"])] += qty
    except FileNotFoundError:
        pass

    # ---- oil pool -----------------------------------------------------------
    uom = {r["code"]: r["uom"] for r in comp}
    oils = {canon(r["code"]) for r in comp
            if r["code"].startswith("RM") and str(r["uom"]).startswith("LTR")}

    rows = []
    for r in plan:
        code = r["code"]
        want = f(r["pieces"]) - fg.get(code, 0.0)
        if want <= 0: continue
        kids = bom.get(code, [])
        oil_need = sum(p for c, p in kids if c in oils)
        pack = [(c, p) for c, p in kids if c not in oils and p > 0]
        rows.append(dict(code=code, sku=r["sku"], head=r.get("head", ""), slot=slot(r),
                         lpc=f(r["litres_per_piece"]), want=want, oil_per=oil_need,
                         pack=pack, oil=(max([(c, p) for c, p in kids if c in oils],
                                             key=lambda x: x[1])[0] if oil_need else "?"),
                         realise=realise.get(code, DEFAULT_REALISE)))

    def rs_hour(r, rate): return rate * (r["lpc"] or 1.0) * r["realise"]
    def prio(r):
        best = max((sp[r["slot"]] for sp in LINES.values() if r["slot"] in sp), default=1)
        return (-rs_hour(r, best), 0 if str(r["head"]).upper() == "PREMIUM" else 1)

    # STRICT: each oil is its own bucket. No pooling.
    for k in oils: stock.setdefault(k, 0.0)
    # flush oil: one 400 L charge per oil for the whole month, taken up front
    flush_charged = set()
    sched, flushes, dropped = [], 0, []
    on_oil = {ln: None for ln in LINES}
    day_tot = collections.OrderedDict()

    # ---- reorder policy (only with --buy) -----------------------------------
    # Procurement reacts: each day, for every oil, if what is on hand plus already
    # inbound will not cover the next LEAD days of burn, order the gap now. It lands
    # LEAD days later. Burn rate is the plan's own requirement spread over the month,
    # which is what a buyer standing on 1 August would use.
    burn = {}
    for r in rows:
        if r["oil_per"] > 0: burn[r["oil"]] = burn.get(r["oil"], 0.0) + r["want"] * r["oil_per"]
    for k in burn: burn[k] /= len(days)
    bought = collections.Counter()

    for di, d in enumerate(days):
        for code, qty in inbound.get(d, {}).items():
            stock[code] = stock.get(code, 0.0) + qty
        if a.buy:
            for k, b in burn.items():
                if b <= 0: continue
                horizon = b * a.lead
                pipeline = sum(inbound.get(days[j], {}).get(k, 0.0)
                               for j in range(di + 1, min(di + 1 + a.lead, len(days))))
                if stock.get(k, 0.0) + pipeline < horizon:
                    order_qty = horizon - stock.get(k, 0.0) - pipeline
                    land = di + a.lead
                    if land < len(days):
                        inbound[days[land]][k] += order_qty
                        bought[k] += order_qty
        free = {ln: a.hours for ln in LINES}
        made_today = 0.0
        while True:
            pool = [r for r in rows if r["want"] >= 1]
            if not pool: break
            placed = False
            for ln, sp in sorted(LINES.items(), key=lambda kv: -max(kv[1].values())):
                if free[ln] <= 0.02: continue
                runnable = [r for r in pool if r["slot"] in sp]
                if not runnable: continue
                # Walk candidates in priority order until one can actually run. Giving
                # up on the line because the FIRST choice is short of a label is the
                # bug that made the whole month stop on day 4.
                same = set(id(r) for r in runnable if r["oil"] == on_oil[ln])
                order = sorted(runnable, key=lambda r: (
                    prio(r)[0] * (0.85 if id(r) in same else 1.0), prio(r)[1]))
                pick = rate = None; fh = 0.0; did = 0.0
                for cand in order:
                    rt = sp[cand["slot"]]
                    lph = rt * (cand["lpc"] or 1.0)
                    f_h = 0.0
                    if on_oil[ln] is not None and cand["oil"] != on_oil[ln]:
                        f_h = FLUSH_L / lph
                        if f_h >= free[ln]: continue
                    cap = (free[ln] - f_h) * rt
                    if cand["oil_per"] > 0:
                        avail = stock.get(cand["oil"], 0.0)
                        if cand["oil"] not in flush_charged: avail -= FLUSH_L
                        cap = min(cap, max(0.0, avail) / cand["oil_per"])
                    for c, per in cand["pack"]:
                        cap = min(cap, stock.get(c, 0.0) / per)
                    d_ = min(cand["want"], cap)
                    if d_ >= 1:
                        pick, rate, fh, did = cand, rt, f_h, d_; break
                if pick is None: continue
                hrs = did / rate
                if fh: flushes += 1
                if pick["oil"] not in flush_charged and pick["oil_per"] > 0:
                    stock[pick["oil"]] = stock.get(pick["oil"], 0.0) - FLUSH_L
                    flush_charged.add(pick["oil"])
                stock[pick["oil"]] = stock.get(pick["oil"], 0.0) - did * pick["oil_per"]
                for c, per in pick["pack"]: stock[c] = stock.get(c, 0.0) - did * per
                free[ln] -= (hrs + fh); on_oil[ln] = pick["oil"]; pick["want"] -= did
                lit = did * pick["lpc"]; made_today += lit
                sched.append(dict(day=d.isoformat(), line=ln, code=pick["code"], sku=pick["sku"],
                                  head=pick["head"], slot=pick["slot"], oil=pick["oil"],
                                  pieces=round(did), litres=round(lit), hours=round(hrs, 2),
                                  flush_min=round(fh * 60, 1) if fh else "",
                                  realise=round(pick["realise"], 2),
                                  value_rs=round(lit * pick["realise"])))
                placed = True
            if not placed: break
        day_tot[d.isoformat()] = made_today

    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sched[0].keys())); w.writeheader(); w.writerows(sched)

    tl = sum(x["litres"] for x in sched); tv = sum(x["value_rs"] for x in sched)
    tp = sum(x["litres"] for x in sched if str(x["head"]).upper() == "PREMIUM")
    plan_l = sum(f(r["litres"]) for r in plan)
    print(f"=== AUGUST 2026 PLAN — built standing on {AS_OF}, no later data used ===\n")
    print(f"  demand (96 SKUs)     {plan_l:>14,.0f} L")
    print(f"  SCHEDULED            {tl:>14,.0f} L   ({tl/plan_l*100:.1f}% of plan)")
    print(f"  value                Rs {tv:>13,.0f}   ({tv/1e7:.2f} Cr)")
    print(f"  premium              {tp:>14,.0f} L   ({tp/tl*100:.0f}%)")
    print(f"  realise              Rs {tv/tl:>13,.2f}/L")
    print(f"  oil changes          {flushes:>14}")
    print(f"  days                 {len(days):>14}   {days[0]} .. {days[-1]}")
    left_oil = sum(max(0.0, stock.get(k, 0.0)) for k in oils)
    print(f"  oil left (per-oil)   {left_oil:>14,.0f} L   (stranded: right oil, wrong SKU)")
    if a.buy and bought:
        print(f"\n  OIL PURCHASED DURING THE MONTH (lead {a.lead} d): "
              f"{sum(bought.values()):>10,.0f} L")
        for k, v in bought.most_common(8):
            print(f"      {k}  {v:>12,.0f} L")
    left = sum(r["want"] * r["lpc"] for r in rows if r["want"] >= 1)
    print(f"  NOT scheduled        {left:>14,.0f} L")
    print(f"\n  {'DAY':<12}{'LITRES':>12}{'cum %':>8}")
    cum = 0
    for k, v in day_tot.items():
        cum += v
        print(f"  {k:<12}{v:>12,.0f}{cum/plan_l*100:>7.0f}%")
    print(f"\nwrote {a.csv}  ({len(sched)} runs)")

if __name__ == "__main__":
    main()
