#!/usr/bin/env python3
"""
THE AUGUST SIMULATION v2 — a strict forward run from a MEASURED 1 August.

Reads ONLY sim/sim-inputs.json. Writes sim/days/day-NN.json, sim/events.json,
sim/summary.json.

THE RULE (Daman, 2026-08-31): only 1 August is observed. Every later day is computed
from the day before plus what the algorithm decided. The one thing that legitimately
arrives each day is that day's purchase orders — news landing, not hindsight.

WHAT v1 GOT WRONG (all corrected here):
  opening FG      664,341 L measured on 30 AUG   ->   461,225 L measured on 1 Aug
  standing pile   84,465 L (a Jul-Aug average)   ->   467,089 L, per document, and it
                                                      DRAINS over the first days
  inbound         naive open-PO query            ->   LIVE POs only (1,693 dead/phantom
                                                      rows dropped: 141M L of x1000
                                                      keying errors, 22.4M units of
                                                      >90-day paper that delivered 0.0%)
  Clear Pack 5 L  3,000/hr rated                 ->   1,000/hr (observed median 831)
  Tin Head        240/hr (owner's word)          ->   215/hr (August peak; no app config)
  line clearance  not modelled at all            ->   51.3 min per changeover
  line speed      rated                          ->   x0.50, the observed rate when running

THE LOOP THE OWNER ASKED FOR, made explicit and logged as events:
  need a SKU -> a component is at zero -> ORDER it -> it takes N days ->
  RUN SOMETHING ELSE meanwhile -> the component lands -> the SKU UNBLOCKS and runs.
"""
import json, collections, os
from datetime import date, timedelta

import os as _os
S = json.load(open(_os.environ.get("SIM_INPUTS", "sim/sim-inputs.json")))
L, R, OP = S["lines"], S["rules"], S["opening"]
import os as _os
FLUSH = R["flush_litres"]; EFF = R["efficiency"]
HOURS = float(_os.environ.get("SIM_HOURS", R["shift_hours"]))
# SIM_HOURS_SCHEDULE="1-13:22,14-30:12" overrides HOURS by day-of-month (taper
# scenarios). Unset = empty dict = every day falls back to HOURS, output unchanged.
def _sched(s):
    out = {}
    for part in s.split(","):
        rng, h = part.split(":"); a, _, b = rng.partition("-")
        for dd in range(int(a), int(b or a) + 1): out[dd] = float(h)
    return out
SCHED = _sched(_os.environ["SIM_HOURS_SCHEDULE"]) if _os.environ.get("SIM_HOURS_SCHEDULE") else {}
SUNDAYS_OFF = _os.environ.get("SIM_SUNDAYS_OFF", "1") == "1"
TAG = _os.environ.get("SIM_TAG", "")
CLEAR_H = R["line_clearance_min"] / 60.0
CEIL = R["storage_ceiling_l"]; PEAK = R["storage_peak_l"]
LEAD = R["lead_days"]; LAG = R["invoice_truck_lag_days"]
_h = S["meta"]["horizon"]
D0, D1 = date.fromisoformat(_h[0]), date.fromisoformat(_h[1])

# 15 L PET jars fill through the same head as the 5 L jars: the nozzle gives
# litres/hour, so pieces/hour scales by 1/3. DERIVED, not measured — no 15 L fill
# rate exists in reference/PLAN-AND-LINES.md or the app. Before this, slot() dropped
# 15 L PET into the 5 L bucket and it ran at 5-litre PIECE rates — 6,700-7,500 L/hr
# sustained, above 10 Head's full RATED litre throughput (252,786 L of September was
# booked in 39.5 line-hours). August is untouched: its only 15 L items are TINs.
for _sp in L.values():
    if "5L" in _sp and "15L" not in _sp: _sp["15L"] = _sp["5L"] / 3.0

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def slot(p):
    pt = str(p["pack_type"]).upper(); sku = str(p["sku"]).upper(); l = p["litres_per_piece"]
    if "DRUM" in pt: return "DRUM"
    if "TIN" in pt or "KGS" in sku: return "TIN"
    if "POUCH" in pt or "POUCH" in sku: return "POUCH"
    if l <= 1.05: return "1L"
    if l <= 2.05: return "2L"
    if l <= 3.05: return "3L"
    if l <= 4.05: return "4L"
    if l <= 5.05: return "5L"
    return "15L"

plan = {p["code"]: dict(p, slot=slot(p)) for p in S["plan"]}
bom, blends, items, realise = S["bom"], S["blends"], S["items"], S["realise"]
DEF_R = 148.33
oils = {c for kids in bom.values() for c, _ in kids if c.startswith("RM")}
for b, kids in blends.items():
    oils.add(b); oils.update(c for c, _ in kids)

def oil_of(code):
    o = [(c, p) for c, p in bom.get(code, []) if c in oils]
    return max(o, key=lambda x: x[1])[0] if o else None
def lpc(c): return plan[c]["litres_per_piece"]
def rs_hour(c, rate): return rate * EFF * lpc(c) * realise.get(c, DEF_R)

# demand: the plan is the projection; POs are commitments layered on as they land.
# po_left / po_value hold REAL orders only (backlog + dated SAP orders); fc_left holds
# the FORECAST stream — the plan standing in for orders that do not exist yet. Mixing
# them put Rs 92 Cr of mostly-forecast money under a "po_open_value" label.
book = {c: dict(plan_left=max(0.0, p["pieces"] - f(OP["fg"].get(c, 0))), po_left=0.0, po_value=0.0, fc_left=0.0)
        for c, p in plan.items()}
# A backlog doc the freeze ALSO emits as a dated order row must not be seeded here too —
# it would count twice in want() and the sim would overproduce demand that cannot ship
# (August: 0 of 75 backlog docs overlap orders, so this changes nothing there;
#  September: all backlog docs re-enter as day-dated orders, so seeding is skipped).
_order_docs = {o["docnum"] for o in S["orders"]}
for b in S["backlog"]:
    if b["docnum"] in _order_docs: continue
    if b["code"] in book: book[b["code"]]["po_left"] += b["pieces"]; book[b["code"]]["po_value"] += b["value"]
orders_by_day = collections.defaultdict(list)
for o in S["orders"]:
    if o["code"] in plan: orders_by_day[o["date"]].append(dict(o))
assert S["orders"], "S['orders'] is empty — the freeze emitted no dated demand stream; re-run the freeze, then the sim"

stock = collections.defaultdict(float, {k: f(v) for k, v in OP["stock"].items()})
fg = collections.defaultdict(float, {k: f(v) for k, v in OP["fg"].items()})
inbound = collections.defaultdict(lambda: collections.defaultdict(float))
for d, m in S["inbound_prebooked"].items():
    for c, q in m.items(): inbound[d][c] += f(q)

# the 1-Aug standing pile: 467,089 L already billed, trucks going over the first days.
# 84 of 84 customer docs docked on 1 Aug or later, so it drains — it does not sit.
standing = collections.deque()
open_pile = f(OP["standing_l"])
# It leaves 45/35/20 over days 2, 3 and 4 (D0 + 1/2/3). Day 1's pile IS the live count
# — gen_live reconciles the end of day 1 to it — so nothing of it goes on day 1; the
# trucks start tomorrow. Seed only a real pile — a zero entry is noise in the queue.
if open_pile > 0:
    for i, share in enumerate([0.45, 0.35, 0.20]):
        standing.append([D0 + timedelta(days=i + 1), open_pile * share])

placed, events, days = [], [], []
on_oil = {ln: None for ln in L}
on_slot = {ln: None for ln in L}
blocked_since = {}          # code -> first day it was blocked (for the unblock story)
ordered_for = {}            # component -> day we ordered it because it blocked something

FG_OTHER = f(OP.get("fg_other_l", 0))   # FG outside the plan: never made, never shipped, always in the way
def fg_litres(): return FG_OTHER + sum(q * lpc(c) for c, q in fg.items() if c in plan and q > 0)
def standing_l(): return sum(v for _, v in standing)
def physical(): return fg_litres() + standing_l()
def ev(day, kind, **kw): events.append(dict(day=day, kind=kind, **kw))

# honesty is stamped on every day file and the site prints it — it must describe THIS
# month's inputs. The freeze writes a month-true block into the inputs (September:
# ~60% of the demand stream is FORECAST buckets, 31-Aug stock, the derived 15 L rate);
# August's inputs carry none, so its original text stands. Never narrate a forecast
# as the measured order book.
HON = S.get("honesty") or dict(
    measured=["1-Aug stock, FG and standing pile (per document)", "the order book (SAP, dated)",
              "BOMs", "line speeds and clearance (ji.jivo.in)", "realise May-Jul", "lead times (12m pre-Aug)"],
    assumed=["supply arrives exactly on its lead time", f"{LAG}-day invoice-to-truck lag",
             f"lines run at {EFF*100:.0f}% of rated, the observed rate"])

today = D0
while today <= D1:
    key = today.isoformat(); working = (today.weekday() != 6) or not SUNDAYS_OFF
    day = dict(date=key, weekday=today.strftime("%A"), working=working, received=[], new_orders=[],
               runs=[], blocked=[], dispatched=[], bought=[], decisions=[], unblocked=[], flushes=0)

    # trucks leave -> space released — by DATE, wherever the entry sits. Until
    # 2026-09-05 this popped the head only, so a day-1 bill (due day 3) waited behind
    # the pile's day-4 tranche and left on day 4, a day past the lag the plant shows.
    # gen_live's "trucks never fall behind the billing queue" caught it the moment the
    # live pile fell below day-1 billing (4 Sep 21:39) and refused to publish for 14 h.
    standing = collections.deque(e for e in standing if e[0] > today)

    # 1 RECEIVE — and note anything that unblocks a SKU we were waiting on
    for c, q in inbound.pop(key, {}).items():
        stock[c] += q
        day["received"].append(dict(code=c, name=items.get(c, {}).get("name", c), qty=round(q)))
        if c in ordered_for:
            waited = (today - date.fromisoformat(ordered_for[c])).days
            day["unblocked"].append(dict(code=c, name=items.get(c, {}).get("name", c),
                                         qty=round(q), ordered_on=ordered_for[c], waited_days=waited))
            ev(key, "UNBLOCKED", code=c, name=items.get(c, {}).get("name", c), waited_days=waited)
            del ordered_for[c]

    # 2 DEMAND — today's POs land and outrank the projection. A FORECAST row is not
    # an order: it drives want(), never the committed-PO ledger.
    for o in orders_by_day.get(key, []):
        b = book[o["code"]]
        if o["channel"] == "FORECAST": b["fc_left"] += o["pieces"]
        else: b["po_left"] += o["pieces"]; b["po_value"] += o["value"]
        day["new_orders"].append(dict(docnum=o["docnum"], customer=o["customer"][:40], channel=o["channel"],
                                      code=o["code"], sku=plan[o["code"]]["sku"],
                                      pieces=round(o["pieces"]), value=round(o["value"])))

    hrs = SCHED.get(today.day, HOURS)
    if working:
        free = {ln: hrs for ln in L}
        headroom = max(0.0, CEIL - physical())
        throttle = headroom < 100000
        if throttle:
            day["decisions"].append(dict(kind="STORAGE_THROTTLE", headroom_l=round(headroom),
                text=f"Godown at {physical()/CEIL*100:.0f}% at start of day — capped to what can ship"))
            ev(key, "STORAGE_THROTTLE", pct_start_of_day=round(physical() / CEIL * 100), headroom_l=round(headroom))

        # want/prio see COMBINED demand (real + forecast) — identical scheduling to the
        # calibrated behaviour; only the LABELS (po_backed, book.po_open_*) are real-only.
        def want(c): return max(book[c]["plan_left"], book[c]["po_left"] + book[c]["fc_left"])
        def prio(c, rate):
            return (0 if book[c]["po_left"] + book[c]["fc_left"] > 0 else 1, -rs_hour(c, rate),
                    0 if plan[c]["head"] == "PREMIUM" else 1)
        made_l = 0.0; oil_day = 0.0
        for _ in range(400):
            placed_any = False
            for ln, sp in sorted(L.items(), key=lambda kv: -max(kv[1].values())):
                if free[ln] <= 0.05: continue
                cands = sorted([c for c in plan if plan[c]["slot"] in sp and want(c) >= 1],
                               key=lambda c: prio(c, sp[plan[c]["slot"]]))
                for c in cands:
                    rate = sp[plan[c]["slot"]] * EFF          # observed, not rated
                    o = oil_of(c)
                    change = on_oil[ln] is not None and o and o != on_oil[ln]
                    # The 51.3-min clearance is per CHANGEOVER — an oil change, a cold
                    # start, or a same-oil PACK-SIZE change (change parts still go on).
                    # Only the 400 L flush is oil-specific. Before this, 14 same-oil
                    # size changes in September booked zero minutes (~12 uncharged hours).
                    sizechg = on_slot[ln] is not None and plan[c]["slot"] != on_slot[ln]
                    if change: fh = FLUSH / (rate * lpc(c)) + CLEAR_H
                    elif on_oil[ln] is None or sizechg: fh = CLEAR_H
                    else: fh = 0.0
                    if fh >= free[ln]: continue
                    cap = (free[ln] - fh) * rate
                    cap = min(cap, max(0.0, headroom) / lpc(c))
                    binder = None
                    for ch, per in bom.get(c, []):
                        if per <= 0: continue
                        av = stock.get(ch, 0.0)
                        if ch in blends:
                            av = min((stock.get(k, 0.0) / kp) for k, kp in blends[ch] if kp > 0)
                        if av / per < cap: cap, binder = av / per, ch
                    did = min(want(c), cap)
                    if did < 1:
                        if binder:
                            day["blocked"].append(dict(code=c, sku=plan[c]["sku"], want=round(want(c)),
                                binder=binder, binder_name=items.get(binder, {}).get("name", binder)))
                            blocked_since.setdefault(c, key)
                        continue
                    for ch, per in bom.get(c, []):
                        if ch in blends:
                            for k, kp in blends[ch]: stock[k] -= did * per * kp
                        else: stock[ch] -= did * per
                    oil_day += did * sum(per for ch, per in bom.get(c, []) if ch in oils)
                    book[c]["plan_left"] = max(0.0, book[c]["plan_left"] - did)
                    # real orders are consumed first (they also ship first), spilling to
                    # forecast; po_value drains proportionally with po_left so open-PO
                    # money falls as the committed pieces are built — never a cumulative
                    # counter (it once reached Rs 92.38 Cr by day 30).
                    b_ = book[c]; take = min(did, b_["po_left"])
                    if take > 0:
                        b_["po_value"] -= b_["po_value"] * take / b_["po_left"]
                        b_["po_left"] -= take
                    b_["fc_left"] = max(0.0, b_["fc_left"] - (did - take))
                    fg[c] += did
                    lit = did * lpc(c); made_l += lit; headroom -= lit
                    if change: day["flushes"] += 1
                    free[ln] -= did / rate + fh
                    on_oil[ln] = o; on_slot[ln] = plan[c]["slot"]
                    day["runs"].append(dict(line=ln, code=c, sku=plan[c]["sku"], head=plan[c]["head"], oil=o,
                        pieces=round(did), litres=round(lit), hours=round(did / rate, 2),
                        flush_min=round(fh * 60), realise=realise.get(c, DEF_R),
                        rs_per_hour=round(rs_hour(c, sp[plan[c]["slot"]])), po_backed=book[c]["po_left"] > 0,
                        value=round(lit * realise.get(c, DEF_R))))
                    if c in blocked_since: del blocked_since[c]
                    placed_any = True; break
            if not placed_any: break

        # DISPATCH — PO-backed first; goods leave the floor after the measured truck lag
        shipped = 0.0
        for o in sorted([x for d, xs in orders_by_day.items() if d <= key for x in xs], key=lambda x: x["date"]):
            if o.get("_done") or o["pieces"] < 1: continue
            c = o["code"]; can = min(o["pieces"], fg.get(c, 0.0))
            if can < 1: continue
            fg[c] -= can; lit = can * lpc(c); shipped += lit
            standing.append([today + timedelta(days=LAG), lit])
            o["pieces"] -= can
            if o["pieces"] < 1: o["_done"] = True
            day["dispatched"].append(dict(docnum=o["docnum"], customer=o["customer"][:40], channel=o["channel"],
                                          sku=plan[c]["sku"], pieces=round(can), litres=round(lit)))

        # BUY — every material, ideal supply: it lands exactly on its lead time
        days_left = max(1, sum(1 for i in range((D1 - today).days + 1) if (today + timedelta(days=i)).weekday() != 6 or not SUNDAYS_OFF))
        need = collections.Counter()
        for c, b in book.items():
            w = max(b["plan_left"], b["po_left"])
            if w <= 0: continue
            for ch, per in bom.get(c, []): need[ch] += w * per
        for bl, kids in blends.items():
            if need.get(bl, 0) > 0:
                for ch, per in kids: need[ch] += need[bl] * per
        for m, tot in need.items():
            rate = tot / days_left
            if rate <= 0: continue
            lead = LEAD["oil"] if m.startswith("RM") else LEAD["packaging"]
            pipe = sum(inbound.get((today + timedelta(days=i)).isoformat(), {}).get(m, 0.0) for i in range(1, 40))
            cover = (stock.get(m, 0.0) + pipe) / rate
            if cover >= lead + 3 or days_left < 2: continue
            qty = rate * min(lead + 6, days_left + 1) - stock.get(m, 0.0) - pipe
            if qty <= 0 or (not m.startswith("RM") and qty < 500): continue
            land = today + timedelta(days=lead)
            if land > D1 + timedelta(days=7): continue
            inbound[land.isoformat()][m] += qty
            placed.append(dict(day=key, code=m, qty=round(qty), lands=land.isoformat()))
            day["bought"].append(dict(code=m, name=items.get(m, {}).get("name", m), qty=round(qty),
                                      uom=items.get(m, {}).get("uom", ""), lands=land.isoformat()))
            if stock.get(m, 0.0) < 1 and m not in ordered_for:
                ordered_for[m] = key
                ev(key, "ORDERED_BLOCKER", code=m, name=items.get(m, {}).get("name", m),
                   qty=round(qty), lands=land.isoformat(), lead=lead)

        zpm = [b for b in day["blocked"] if b["binder"].startswith("PM") and stock.get(b["binder"], 0) < 1]
        if zpm: ev(key, "PACKAGING_ZERO", items=[dict(code=z["binder"], name=z["binder_name"], sku=z["sku"], want=z["want"]) for z in zpm[:8]])
        zrm = [b for b in day["blocked"] if b["binder"].startswith("RM")]
        if zrm: ev(key, "OIL_SHORT", items=[dict(code=z["binder"], name=z["binder_name"], sku=z["sku"], want=z["want"]) for z in zrm[:6]])
        # a FORECAST slice must never be announced as a PO, whatever its size
        for n in [x for x in day["new_orders"] if x["value"] >= 5_000_000 and x["channel"] != "FORECAST"]: ev(key, "BIG_PO", **n)
        util = 1 - sum(free.values()) / (hrs * len(L))
        if util < 0.5 and day["blocked"]: ev(key, "LINES_IDLE", util=round(util * 100), blocked=len(day["blocked"]))
        ev(key, "BUILD_LIST", lines={ln: [dict(sku=r["sku"], pieces=r["pieces"], hours=r["hours"], oil=r["oil"])
                                          for r in day["runs"] if r["line"] == ln] for ln in L})
        day.update(made_litres=round(made_l), made_value=round(sum(r["value"] for r in day["runs"])),
                   shipped_litres=round(shipped), oil_used_l=round(oil_day), line_util=round(util * 100),
                   line_hours={ln: round(hrs - free[ln], 1) for ln in L})
    else:
        day.update(made_litres=0, made_value=0, shipped_litres=0, oil_used_l=0, line_util=0, line_hours={ln: 0 for ln in L})

    ph = physical()
    day.update(storage=dict(physical_l=round(ph), ceiling_l=CEIL, peak_l=PEAK, pct=round(ph / CEIL * 100, 1),
                            fg_in_godown_l=round(fg_litres()), invoiced_not_trucked_l=round(standing_l()),
                            headroom_l=round(CEIL - ph)),
               book=dict(plan_left_l=round(sum(b["plan_left"] * lpc(c) for c, b in book.items())),
                         po_open_l=round(sum(b["po_left"] * lpc(c) for c, b in book.items())),
                         po_open_value=round(sum(b["po_value"] for b in book.values())),
                         forecast_open_l=round(sum(b["fc_left"] * lpc(c) for c, b in book.items()))),
               oil_on_hand_l=round(sum(v for k, v in stock.items() if k in oils and v > 0)),
               waiting_on=[dict(code=c, name=items.get(c, {}).get("name", c), since=d) for c, d in sorted(ordered_for.items())],
               honesty=HON)
    days.append(day); today += timedelta(days=1)

OUT = f"sim/days{TAG}"
os.makedirs(OUT, exist_ok=True)
# A rolling re-plan writes FEWER day files than the last run (2 Sep: 29, not 30).
# Any day-NN.json left over from before is a stale artifact that a consumer will
# happily read as part of THIS run — clear them first.
import glob as _glob
for _old in _glob.glob(f"{OUT}/day-*.json"): os.remove(_old)
for i, d in enumerate(days, 1): json.dump(d, open(f"{OUT}/day-{i:02d}.json", "w"), indent=1)
json.dump(events, open(f"sim/events{TAG}.json", "w"), indent=1)
json.dump(dict(days=[dict(date=d["date"], working=d["working"], made_l=d["made_litres"], value=d["made_value"],
    shipped_l=d["shipped_litres"], util=d["line_util"], storage_pct=d["storage"]["pct"], runs=len(d["runs"]),
    blocked=len(d["blocked"]), new_orders=len(d["new_orders"]), bought=len(d["bought"]),
    unblocked=len(d["unblocked"])) for d in days],
    # the run's OWN shift configuration, so no consumer has to infer the pattern back
    # out of the output (a taper whose tail days are material-bound, not hours-bound,
    # is indistinguishable from a flat run by inspection alone).
    shift=dict(hours=HOURS, schedule=(_os.environ.get("SIM_HOURS_SCHEDULE") or None),
               sundays_off=SUNDAYS_OFF, lines=len(L)),
    totals=dict(made_l=sum(d["made_litres"] for d in days), value=sum(d["made_value"] for d in days),
                shipped_l=sum(d["shipped_litres"] for d in days), orders=len(S["orders"]),
                bought_lines=len(placed), events=len(events),
                oil_used_l=sum(d["oil_used_l"] for d in days),
                negative_stocks={k: round(v) for k, v in sorted(stock.items()) if v < -1},
                actual_made_l=S["actuals_for_scoring"]["made_l"],
                actual_util=S["actuals_for_scoring"]["line_utilisation_pct"])),
    open(f"sim/summary{TAG}.json", "w"), indent=1)

# conservation law: bulk oil consumed must reconcile to litres produced
_oil = sum(d["oil_used_l"] for d in days); _made = sum(d["made_litres"] for d in days)
_neg = {k: round(v) for k, v in stock.items() if v < -1}
print(f"  CONSERVATION  oil consumed {_oil:,.0f} L vs produced {_made:,.0f} L "
      f"-> {abs(_oil - _made) / _made * 100 if _made else 0:.2f}% gap; negative stocks: {_neg or 'none'}")

t = sum(d["made_litres"] for d in days); v = sum(d["made_value"] for d in days)
A = S["actuals_for_scoring"]
print(f"=== AUGUST v2 — measured 1-Aug opening, {EFF*100:.0f}% observed line speed ===")
print(f"  PLANNED BY THE ALGO   {t:>12,.0f} L    Rs {v/1e7:.2f} Cr")
print(f"  the plant ACTUALLY did{A['made_l']:>12,.0f} L    ({A['line_utilisation_pct']}% utilisation)")
print(f"  vs plan 4,141,400 L   {t/4141400*100:>11.1f}%   (actual was {A['plan_pct']}%)")
print(f"  shipped               {sum(d['shipped_litres'] for d in days):>12,.0f} L")
print(f"  orders placed {len(placed)}   unblock events {sum(len(d['unblocked']) for d in days)}\n")
print(f"  {'DAY':<12}{'MADE L':>10}{'SHIP L':>10}{'UTIL':>6}{'STORE':>7}{'RUNS':>5}{'BLK':>4}{'PO+':>4}{'BUY':>4}{'UNBL':>5}")
for d in days:
    print(f"  {d['date']:<12}{d['made_litres']:>10,}{d['shipped_litres']:>10,}{d['line_util']:>5}%"
          f"{d['storage']['pct']:>6}%{len(d['runs']):>5}{len(d['blocked']):>4}{len(d['new_orders']):>4}"
          f"{len(d['bought']):>4}{len(d['unblocked']):>5}")
