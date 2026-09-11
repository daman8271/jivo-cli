#!/usr/bin/env python3
"""
SEPTEMBER 2026 — freeze the opening position. A real forward plan, not a backtest.

August was scored against what happened. September has not happened, so this is the
plan itself: what to make, in what order, on which line, and what to order by when.

Opening = TODAY (2026-08-31), which is the eve of the month. Every correction learned
from the August rebuild is carried in:
  * synonyms merged before any shortage (groundnut=peanut etc.)
  * godown allow-list incl. BH-GJ and GP-PM (GODOWNS.md, settled 2026-08-29),
    excl. BH-OT / BH-PP / BH-PC / BH-WST
  * POR1 OpenInvQty (inventory units), never OpenQty
  * only LIVE purchase orders — no >90-day paper, no x1000 keying errors
  * demand from SAP ORDR only — not the OMS mirror, not the plant's own forecast
  * FG outside the plan still occupies the godown
  * Clear Pack 5 L 1,000/hr, Tin Head 215/hr, line clearance 51.3 min, 50% of rated
"""
import csv, json, os, re, subprocess, io, sys, collections, zlib
from datetime import date, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
# git tracks the darwin/arm64 build of hana-sql; a pull on a Linux box overwrites the
# local build with it (2 Sep). A Linux binary lives under its own name, out of git's way.
if os.path.exists(HANA + ".linux") and os.uname().sysname == "Linux": HANA = HANA + ".linux"
CO = "JIVO_OIL_HANADB"
# ROLLING: SIM_ASOF makes today the new day 1 and re-plans only what is left of the
# month. Unset it and the freeze is the original 1 Sept eve-of-month snapshot.
ASOF = os.environ.get("SIM_ASOF", "2026-09-01")
D0 = date.fromisoformat(ASOF)
MSTART = D0.replace(day=1)
D1 = (MSTART.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
ROLLING = D0 > MSTART
# GODOWNS.md (settled by Daman 2026-08-29) allow-lists GP-PM for oil+packaging too —
# omitting it hid 442,006 pcs incl. stock of 3 plan-BOM components (glass 500 ml).
MAT_WH = "'BH-BS','BH-PM','BH-LO','BH-NM','BH-SDL','GP-NM','GP-FG','BH-GJ','GP-PM'"
FG_WH = "'BH-BT','BH-PF'"

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0
def hana(sql):
    # HANA_ENV is set by engine/refresh.sh after it proves which env this box can reach
    # (the Mac tunnels, the VPS goes direct). Falls back to the historical order.
    _pref = os.environ.get("HANA_ENV")
    for env in ([f"{_pref}.env"] if _pref else []) + ["hana-office-bridge.env", "hana-vps-direct.env", "hana-new.env"]:
        if not os.path.exists(os.path.join(REPO, "connections", env)): continue
        r = subprocess.run([HANA, "-env", os.path.join(REPO, "connections", env), "-csv", sql],
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            t = r.stdout; d = "\t" if t.count("\t") > t.count(",") else ","
            return list(csv.DictReader(io.StringIO(t), delimiter=d))
    sys.exit("HANA unreachable")
def read(p): return list(csv.DictReader(open(p)))
def yf(p):
    s = open(p).read(); m = re.match(r"^---\n(.*?)\n---", s, re.S); o = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line: k, v = line.split(":", 1); o[k.strip()] = v.strip().strip('"')
    return o

syn = {r["alias"]: r["canonical"] for r in read("reference/oil-synonyms.csv")
       if r.get("alias") and not str(r["alias"]).startswith("#")}
def canon(c): return syn.get(c, c)

plan = [dict(code=r["code"], sku=r["sku"], head=r["head"], category=r["category"],
             pack_type=r["pack_type"], litres_per_piece=f(r["litres_per_piece"]),
             pieces=int(f(r["pieces"])), litres=f(r["litres"]))
        for r in read("out/plan-sep-resolved.csv") if r["pieces"]]
codes = {p["code"] for p in plan}; byc = {p["code"]: p for p in plan}

# ROLLING re-plan: the EXIM plan is for the WHOLE month, so re-freezing mid-month would
# re-plan volume the floor has ALREADY made. Net it off by month-to-date production
# (SAP OIGN/IGN1 receipts from production, the same source August was scored against).
# On day 1 of the month this subtracts nothing and the freeze is unchanged.
made_mtd = collections.Counter()
if ROLLING:
    for r in hana(f'''SELECT L."ItemCode" IC, SUM(L."Quantity") Q
        FROM {CO}.IGN1 L JOIN {CO}.OIGN H ON H."DocEntry"=L."DocEntry"
        WHERE H."CANCELED"='N' AND L."ItemCode" LIKE 'FG%'
          AND H."DocDate" >= '{MSTART.isoformat()}' AND H."DocDate" < '{ASOF}'
        GROUP BY L."ItemCode"'''):
        made_mtd[r["IC"]] += f(r["Q"])
    for p in plan:
        done = made_mtd.get(p["code"], 0.0)
        if done <= 0: continue
        p["pieces_planned_month"] = p["pieces"]; p["pieces_made_mtd"] = round(done)
        p["pieces"] = max(0, int(p["pieces"] - done))
        p["litres"] = round(p["pieces"] * p["litres_per_piece"], 2)

bom = collections.defaultdict(list)
for r in hana(f'''SELECT T."Code" F, C."Code" C, C."Quantity"/T."Qauntity" PER
    FROM {CO}.OITT T JOIN {CO}.ITT1 C ON C."Father"=T."Code"
    WHERE T."TreeType"='P' AND C."Type"<>290'''):
    bom[r["F"]].append([canon(r["C"]), f(r["PER"])])
for x in read("reference/reconstructed-boms.csv"):
    if x["father"] not in bom: bom[x["father"]].append([canon(x["child"]), f(x["per_piece"])])
for c, kids in list(bom.items()):
    if c not in byc: continue
    lp = byc[c]["litres_per_piece"]; oil = sum(p for ch, p in kids if ch.startswith("RM"))
    if lp and oil:
        n = round(oil / lp)
        if n >= 2 and abs(oil / lp - n) / n < 0.02: bom[c] = [[ch, p / n] for ch, p in kids]
blends = collections.defaultdict(list)
for r in read("reference/blend-recipes.csv"): blends[r["blend"]].append([canon(r["component"]), f(r["per_litre"])])
# canon() can alias two recipe lines onto one oil (peanut+groundnut -> RM0000011).
# Merge them, or the sim's per-entry availability check overstates what is buildable.
for b, kids in list(blends.items()):
    agg = collections.Counter()
    for c, p in kids: agg[c] += p
    blends[b] = [[c, p] for c, p in agg.items()]

items = {r["ItemCode"]: dict(name=r["ItemName"], uom=r["InvntryUom"])
         for r in hana(f'''SELECT "ItemCode","ItemName","InvntryUom" FROM {CO}.OITM''')}

# ---- opening: materials, FG, and what is genuinely inbound -----------------------
stock = collections.defaultdict(float)
for r in hana(f'''SELECT "ItemCode" IC, SUM("OnHand") Q FROM {CO}.OITW
    WHERE "WhsCode" IN ({MAT_WH}) GROUP BY "ItemCode"'''):
    if r["IC"].startswith(("RM", "PM")): stock[canon(r["IC"])] += f(r["Q"])
fg_open, fg_all_l = {}, 0.0
import importlib.util
spec = importlib.util.spec_from_file_location("pu", "engine/plan_units.py")
pu = importlib.util.module_from_spec(spec); spec.loader.exec_module(pu)
for r in hana(f'''SELECT W."ItemCode" IC, I."ItemName" NM, SUM(W."OnHand") Q FROM {CO}.OITW W
    JOIN {CO}.OITM I ON I."ItemCode"=W."ItemCode"
    WHERE W."WhsCode" IN ({FG_WH}) AND I."ItmsGrpCod" IN (102,115)
    GROUP BY W."ItemCode", I."ItemName" HAVING SUM(W."OnHand") > 0'''):
    q = f(r["Q"])
    if r["IC"] in codes: fg_open[r["IC"]] = q
    l, _ = pu.pack_litres(r["NM"])
    if l: fg_all_l += q * l
fg_plan_l = sum(q * byc[c]["litres_per_piece"] for c, q in fg_open.items())
fg_other_l = max(0.0, fg_all_l - fg_plan_l)

inbound = collections.defaultdict(lambda: collections.defaultdict(float))
inb_oil = inb_pm = 0.0
for r in hana(f'''SELECT L."ItemCode" IC, H."DocNum" N, H."DocDate" OD, L."ShipDate" DD,
      COALESCE(L."OpenInvQty", L."OpenQty"*COALESCE(L."NumPerMsr",1)) Q
    FROM {CO}.POR1 L JOIN {CO}.OPOR H ON H."DocEntry"=L."DocEntry"
    WHERE H."DocStatus"='O' AND H."CANCELED"='N'
      AND L."WhsCode" IN ({MAT_WH})
      AND H."DocDate" >= ADD_DAYS(DATE'{ASOF}', -90)'''):
    q = f(r["Q"])
    if q <= 0 or q > 5_000_000: continue          # x1000 keying-error guard
    c = canon(r["IC"])
    if not c.startswith(("RM", "PM")): continue
    # Most POs carry no ship date. Dumping them all on day 1 makes the plan fantasy —
    # so where the date is missing, land it at order date + the MEASURED lead time
    # (oil 11 d, packaging 6 d), which is what the buyer would actually expect.
    lead = 11 if c.startswith("RM") else 6
    try:
        d = date.fromisoformat(str(r["DD"])[:10])
    except (ValueError, TypeError):
        try: d = date.fromisoformat(str(r["OD"])[:10]) + timedelta(days=lead)
        except (ValueError, TypeError): d = D0
    # An OVERDUE PO (its lead time already elapsed) does not all arrive on the 1st.
    # A backlog clears over days, so spread overdue lines deterministically across the
    # first working week. This is an ASSUMPTION and it is declared in provenance.
    if d < D0:
        # crc32, not hash(): Python string hash is per-process randomised, so hash()
        # would re-scatter these dates on every rerun and the freeze would not be
        # reproducible. crc32 is stable across runs and machines.
        d = D0 + timedelta(days=(zlib.crc32((r["N"] + r["IC"]).encode()) % 5))
        while d.weekday() == 6: d += timedelta(days=1)
    if d > D1: continue
    inbound[d.isoformat()][c] += q
    if c.startswith("RM"): inb_oil += q
    else: inb_pm += q

realise = {}
for x in read("out/realise-by-item-PRE-AUG.csv"):
    c = str(x["item"]).split("—")[0].split("-")[0].strip()[:9]
    if c.startswith("FG"): realise[c] = round(f(x["realise"]), 2)

orders, backlog = [], []
# value = OPEN pieces x unit price (OpenQty*Price). SUM(LineTotal) was refuted: it
# counts the already-delivered part of part-shipped lines (and closed lines inside the
# doc+item group), overstating the open book's worth by Rs 14.4 Cr / 44%.
nonplan = dict(pieces=0.0, value=0.0, codes=set())
for r in hana(f'''SELECT H."DocNum" N, H."DocDate" D, H."DocDueDate" DUE, H."CardCode" CC, H."CardName" CN,
      L."ItemCode" IC, SUM(L."OpenQty") Q, SUM(L."OpenQty"*L."Price") V
    FROM {CO}.ORDR H JOIN {CO}.RDR1 L ON L."DocEntry"=H."DocEntry"
    WHERE H."CANCELED"='N' AND H."DocStatus"='O' AND L."ItemCode" LIKE 'FG%'
    GROUP BY H."DocNum",H."DocDate",H."DocDueDate",H."CardCode",H."CardName",L."ItemCode"'''):
    if f(r["Q"]) <= 0: continue
    if r["IC"] not in codes:
        # real open orders on FG codes OUTSIDE the 84-SKU plan: the sim cannot produce
        # them, so they are outside its world — counted so the exclusion is declared,
        # never silent (they were Rs 5.28 Cr on 29 codes at freeze time).
        nonplan["pieces"] += f(r["Q"]); nonplan["value"] += f(r["V"]); nonplan["codes"].add(r["IC"])
        continue
    backlog.append(dict(docnum=r["N"], date=str(r["D"])[:10], due=str(r["DUE"])[:10],
                        customer=r["CN"][:60],
                        code=r["IC"], pieces=f(r["Q"]), value=f(r["V"]),
                        channel="MART" if str(r["CC"]).startswith("CUSTA0000") else "TRADE"))

# ---- September demand, dated ------------------------------------------------------
# Two parts, and they are different things:
#  1) the OPEN BACKLOG — real orders already on the books. They ship as soon as the goods
#     exist, so they enter on day 1 (or on their promised date where it is in September).
#  2) the PLAN's own weekly buckets — the projection for demand not yet ordered. Without
#     it nothing ships after the backlog clears, the godown fills, and production stops.
#     This is a FORECAST standing in for orders that have not arrived yet, and it is
#     declared as such.
sep_orders = []
WORK = [D0 + timedelta(days=i) for i in range((D1 - D0).days + 1)]
WORK = [d for d in WORK if d.weekday() != 6]
for b in backlog:
    # dated by PROMISE (DocDueDate). Measured 2026-08-31: 131 of 138 open docs are
    # already overdue, so most of the backlog genuinely enters on day 1 — that is the
    # state of the book, not a modelling choice. A promise past the horizon clamps to 30 Sept.
    try: pd_ = date.fromisoformat(b["due"])
    except (ValueError, KeyError): pd_ = D0
    d = min(max(pd_, D0), D1)
    sep_orders.append(dict(b, date=d.isoformat(), _src="BACKLOG"))
# weekly plan buckets -> a daily forecast stream, net of what the backlog already covers
wk = collections.defaultdict(float)
for r in read("out/plan-sep-weeks.csv"):
    wk[(r["code"], int(r["week"]))] += f(r["litres"])
# The weekly buckets are the TRADE half of the plan only — EXIM carries no ecom_w1..4
# (verified live 2026-08-31: trade weeks sum exactly to trade monthly on all 186 rows,
# ecom 2,433,000 L is monthly-only). Without the remainder the sim can never ship 56%
# of the plan. Spread each SKU's un-bucketed litres across the WHOLE month's working
# days as week 0 — an even spread is an ASSUMPTION and is declared in provenance.
for p in plan:
    rem = p["litres"] - sum(v for (c, w), v in wk.items() if c == p["code"])
    if rem > 0.5: wk[(p["code"], 0)] += rem
covered = collections.Counter()
for b in backlog: covered[b["code"]] += b["pieces"]
for (code, w), lit in wk.items():
    if code not in byc: continue
    pcs = lit / (byc[code]["litres_per_piece"] or 1)
    take = min(pcs, max(0.0, covered[code])); covered[code] -= take
    pcs -= take
    if pcs < 1: continue
    wdays = (WORK if w == 0 else [d for d in WORK if (d.day - 1) // 7 + 1 == w]) or WORK[:6]
    per = pcs / len(wdays)
    for d in wdays:
        sep_orders.append(dict(docnum=f"FCST-W{w}-{code}", date=d.isoformat(), customer="(forecast — not yet ordered)",
                               channel="FORECAST", code=code, pieces=per,
                               value=per * byc[code]["litres_per_piece"] * realise.get(code, 148.33), _src="FORECAST"))

# the demand stream is ~60% forecast — say so where the day files will carry it
_fc_l = sum(o["pieces"] * byc[o["code"]]["litres_per_piece"] for o in sep_orders if o["_src"] == "FORECAST")
_dem_l = sum(o["pieces"] * byc[o["code"]]["litres_per_piece"] for o in sep_orders) or 1.0

people = []
for fn in sorted(os.listdir("people")):
    if not fn.endswith(".md") or fn.startswith(("_","ASK","DISPATCH","MISSING","ORG","ROSTER","SCOPE")): continue
    y = yf(os.path.join("people", fn))
    if y.get("whatsapp"):
        people.append(dict(name=y.get("name", fn[:-3]), whatsapp=y["whatsapp"],
                           display=y.get("phone_display",""), title=y.get("title",""), function=y.get("function","")))

out = dict(
  meta=dict(frozen=(D0 - timedelta(days=1)).isoformat(), as_of=ASOF,
            horizon=[D0.isoformat(), D1.isoformat()], month=D0.strftime("%B %Y"),
            rolling=ROLLING, replanned_days=(D1 - D0).days + 1,
            pieces_made_mtd=int(sum(made_mtd.values())) if ROLLING else 0,
            rule="A FORWARD PLAN, not a backtest. September has not happened. Only the 1-Sept opening is observed."),
  opening=dict(stock=dict(stock), fg=fg_open, fg_litres=round(fg_all_l), fg_plan_l=round(fg_plan_l),
               fg_other_l=round(fg_other_l), standing_l=0,
               oil_l=round(sum(v for k,v in stock.items() if k.startswith("RM"))),
               packaging_pieces=round(sum(v for k,v in stock.items() if k.startswith("PM"))),
               inbound_oil_l=round(inb_oil), inbound_packaging=round(inb_pm),
               backlog_pieces=round(sum(b["pieces"] for b in backlog)),
               backlog_value=round(sum(b["value"] for b in backlog)),
               backlog_nonplan_pieces=round(nonplan["pieces"]),
               backlog_nonplan_value=round(nonplan["value"]),
               backlog_nonplan_codes=len(nonplan["codes"]),
               at_zero=[dict(code=c, name=items.get(c,{}).get("name",c),
                             kind="OIL" if c.startswith("RM") else "PACKAGING")
                        for c in sorted({canon(ch) for kids in bom.values() for ch,_ in kids if ch in [canon(x) for x in items]})
                        if stock.get(c, 0.0) < 1 and any(c == canon(ch) for k in codes for ch,_ in bom.get(k, []))]),
  inbound_prebooked={k: dict(v) for k,v in inbound.items()},
  lines={"JP Machine":{"1L":5400},"Clear Pack":{"1L":4800,"4L":1000,"5L":1000},
         "10 Head":{"1L":2100,"2L":1260,"5L":900},"6 Head":{"1L":1080,"2L":720,"5L":600},
         "Pouch Machine":{"POUCH":4200},"Tin Head":{"TIN":215}},
  rules=dict(shift_hours=12, working_days=26, sundays_off=True, any_oil_any_line=True,
             flush_litres=400, line_clearance_min=51.3, efficiency=0.50,
             storage_ceiling_l=827000, storage_peak_l=923000,
             lead_days=dict(oil=11, packaging=6), invoice_truck_lag_days=2,
             priority=["PO","realise_per_line_hour","premium"]),
  actuals_for_scoring=dict(made_l=0, made_pieces=0, skus=0, plan_pct=0.0,
                           line_utilisation_pct=0.0, production_days=0,
                           note="September has not happened. Nothing to score against yet."),
  # stamped verbatim on every day file by the sim — it must be TRUE FOR SEPTEMBER.
  # August's hardcoded block ("1-Aug stock", "the order book (SAP, dated)") narrated a
  # 60%-forecast stream as the measured order book. Never do that.
  honesty=dict(
    measured=["31-Aug stock, FG and open POs (SAP, godown allow-list, OpenInvQty)",
              "the open order backlog (SAP ORDR, dated by promise; the 84 plan SKUs only)",
              "BOMs", "line speeds and clearance (ji.jivo.in, August-observed)",
              "realise May-Jul", "lead times measured: oil 11 d, packaging 6 d"],
    assumed=[f"{_fc_l/_dem_l*100:.0f}% of the demand stream is the monthly plan as dated FORECAST buckets, not orders (channel=FORECAST, separable)",
             "the un-bucketed ecom plan volume spreads evenly across working days — EXIM gives it no weekly split",
             "supply arrives exactly on its lead time", "2-day invoice-to-truck lag",
             "lines run at 50% of rated, the observed rate",
             "15 L PET fills at the 5 L slot's litres/hour (pieces/hr divided by 3) — DERIVED, no measured 15 L rate exists",
             "standing_l=0: stock invoiced on/before 31 Aug but not yet gated out is uncounted (optimistic on day-1 space)"]),
  provenance=dict(
    plan="EXIM GET /planning/latest/ — PRODUCTION PLANING MONTH OF SEP 2026, uploaded 2026-08-27 by aahar831@gmail.com, 186 rows / 185 FG codes / 4,323,300 L, weekly buckets. No Excel.",
    opening="SAP OITW as at 2026-08-31 (the eve of the month), godown allow-list incl. BH-GJ and GP-PM (GODOWNS.md, settled 2026-08-29).",
    inbound="Open POs raised in the last 90 days only, OpenInvQty in inventory units, x1000 guard. Where a PO carries no ship date, it lands at order-date + measured lead (oil 11 d, packaging 6 d). ASSUMPTION: lines already overdue on 1 Sept are spread deterministically across the first working week rather than all arriving on day one.",
    demand="Two streams: (1) the SAP ORDR open backlog, real orders, dated by PROMISE (DocDueDate; measured 2026-08-31: 131 of 138 open docs already overdue, so most enter day 1 — the state of the book, not an assumption); (2) the plan as a FORECAST for demand not yet ordered, net of the backlog: EXIM's weekly buckets where they exist (trade 1,890,300 L), plus the un-bucketed ecom volume (2,433,000 L — EXIM has no ecom weekly split) spread evenly across the month's working days as week 0. ASSUMPTION: the even ecom spread. Stream 2 is a projection, tagged channel=FORECAST so it can be separated on the site. NOT the OMS mirror (dead, unjoinable). SCOPE: the backlog counted here covers the 84 plan SKUs only — open FG orders on non-plan codes are outside the sim's world (it cannot produce them) and are counted separately in opening.backlog_nonplan_*. VALUE BASIS: order value = OpenQty x unit Price, the open pieces' worth — SUM(LineTotal) was refuted (it includes the delivered part of part-shipped lines; Rs 14.4 Cr / 44% overstatement).",
    standing="ASSUMPTION: standing_l=0 — any stock invoiced on/before 31 Aug but not yet gated out (C-0054) is NOT counted, which is optimistic on godown space. Not measured at freeze.",
    lines="ji.jivo.in masters with August observations: Clear Pack 5L 1,000/hr (rated 3,000 refuted), Tin Head 215/hr, clearance 51.3 min. The sim plans at these speeds x0.50 (rules.efficiency) — the August-calibrated effective rate (sim 2,122,639 L vs actual 2,119,237 L): CP 5L effectively 500/hr vs its observed median 831, Tin Head 107.5/hr vs its observed peak 215. Deliberately conservative — a reported tin shortfall is therefore an upper bound. 15 L PET has NO measured rate anywhere: the engine DERIVES it as the 5 L slot's pieces/hr divided by 3 (constant litres/hour through the same head).",
    august_lesson="The August rebuild found 5 input bugs. All corrections are carried here.",
  ),
  plan=plan, bom={k:v for k,v in bom.items() if k in codes}, blends=dict(blends),
  items=items, realise=realise, orders=sep_orders, backlog=backlog, people=people,
)
json.dump(out, open("sim/sep-inputs.json","w"), indent=1)
print(f"sim/sep-inputs.json — {os.path.getsize('sim/sep-inputs.json')/1e6:.1f} MB\n")
print(f"  plan            {len(plan)} SKUs, {sum(p['litres'] for p in plan):,.0f} L")
print(f"  FG on hand      {fg_all_l:,.0f} L (plan {fg_plan_l:,.0f} + other {fg_other_l:,.0f})")
print(f"  oil on hand     {out['opening']['oil_l']:,.0f} L")
print(f"  packaging       {out['opening']['packaging_pieces']:,.0f} pcs")
print(f"  inbound         oil {inb_oil:,.0f} L | packaging {inb_pm:,.0f} pcs over {len(inbound)} days")
print(f"  open backlog    {out['opening']['backlog_pieces']:,.0f} pcs  Rs {out['opening']['backlog_value']/1e7:.2f} Cr")
print(f"  components AT ZERO: {len(out['opening']['at_zero'])}")
