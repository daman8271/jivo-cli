#!/usr/bin/env python3
"""
PHASE 0 v2 — freeze the MEASURED 1 August 2026 position.

Everything here was measured as at 2026-08-01 by the aug01-truth study and cross-checked
against SAP by an independent rewind (control: RM0000003 MUSTARD at BH-LO =
102,917.3978 L, reproduced to 4 decimals).

What v1 got wrong and this fixes:
  * FG opening was 664,341 L measured on 30 AUGUST. Truth: 461,225 L. 203,116 L too full.
  * standing invoiced-not-trucked was 84,465 L (a Jul-Aug AVERAGE). Truth: 467,089 L,
    measured per document from both exit doors — and 422,771 L of it was 31-July
    month-end billing that cleared in the first days.
  * inbound came from a naive open-PO query. That returns 141,034,848 L of phantom oil
    (3 POs keyed x1000) and 22.4M units on paper >90 days old that delivered 0.0%.
  * component universe was 247 items; 114 of them are in no August BOM. Real: 135.
  * Clear Pack 5 L rated 3,000/hr is REFUTED — observed median 831/hr, best 1,068.
  * Tin Head has NO config in the app; August peaked at 215/hr.
  * line clearance (51.3 min median) was missing entirely from the model.

ONLY 1 AUGUST IS OBSERVED. Everything after is computed by the simulator. The single
thing that legitimately arrives each day is that day's purchase orders — news landing,
not hindsight.
"""
import csv, json, os, re, subprocess, io, sys, collections
from datetime import date, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
CO = "JIVO_OIL_HANADB"
HELD = {"FG0000448", "FG0000451", "FG0000452"}

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def hana(sql):
    for env in ("hana-office-bridge.env", "hana-new.env"):
        r = subprocess.run([HANA, "-env", os.path.join(REPO, "connections", env), "-csv", sql],
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            txt = r.stdout
            d = "\t" if txt.count("\t") > txt.count(",") else ","
            return list(csv.DictReader(io.StringIO(txt), delimiter=d))
    sys.exit(f"HANA unreachable: {r.stderr[:200]}")

def read(p): return list(csv.DictReader(open(p)))
def yaml_front(p):
    s = open(p).read(); m = re.match(r"^---\n(.*?)\n---", s, re.S); out = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1); out[k.strip()] = v.strip().strip('"')
    return out

syn = {r["alias"]: r["canonical"] for r in read("reference/oil-synonyms.csv")
       if r.get("alias") and not str(r["alias"]).startswith("#")}
def canon(c): return syn.get(c, c)

# ---------------------------------------------------------------- plan
plan = [dict(code=r["code"], sku=r["sku"], head=r["head"], category=r["category"],
             pack_type=r["pack_type"], litres_per_piece=f(r["litres_per_piece"]),
             pieces=int(f(r["pieces"])), litres=f(r["litres"]))
        for r in read("out/plan-aug-resolved.csv") if r["pieces"] and r["code"] not in HELD]
codes = {p["code"] for p in plan}

# ---------------------------------------------------------------- BOM (+yield guard)
bom = collections.defaultdict(list)
for r in hana(f'''SELECT T."Code" F, C."Code" C, C."Quantity"/T."Qauntity" PER
    FROM {CO}.OITT T JOIN {CO}.ITT1 C ON C."Father"=T."Code"
    WHERE T."TreeType"='P' AND C."Type"<>290'''):
    bom[r["F"]].append([canon(r["C"]), f(r["PER"])])
for x in read("reference/reconstructed-boms.csv"):
    if x["father"] not in bom: bom[x["father"]].append([canon(x["child"]), f(x["per_piece"])])
byc = {p["code"]: p for p in plan}
for c, kids in list(bom.items()):
    if c not in byc: continue
    lpc = byc[c]["litres_per_piece"]
    oil = sum(per for ch, per in kids if ch.startswith("RM"))
    if lpc and oil:
        n = round(oil / lpc)
        if n >= 2 and abs(oil / lpc - n) / n < 0.02:
            bom[c] = [[ch, per / n] for ch, per in kids]
blends = collections.defaultdict(list)
for r in read("reference/blend-recipes.csv"):
    blends[r["blend"]].append([canon(r["component"]), f(r["per_litre"])])

items = {r["ItemCode"]: dict(name=r["ItemName"], uom=r["InvntryUom"])
         for r in hana(f'''SELECT "ItemCode","ItemName","InvntryUom" FROM {CO}.OITM
             WHERE "ItemCode" LIKE 'RM%' OR "ItemCode" LIKE 'PM%' OR "ItemCode" LIKE 'FG%' ''')}

# ---------------------------------------------------------------- MEASURED 1-AUG OPENING
stock = collections.defaultdict(float); at_zero = []
for r in read("out/aug01-materials-TRUTH.csv"):
    c = canon(r["code"]); q = f(r["chosen_qty"])
    stock[c] += q
    if str(r.get("at_zero", "")).strip().upper() in ("TRUE", "Y", "YES", "1"): at_zero.append(dict(code=r["code"], name=r["name"], kind=r.get("kind", "")))

fg_open = {}
for r in hana(f'''WITH s AS (SELECT "ItemCode" IC, SUM(IFNULL("InQty",0)-IFNULL("OutQty",0)) N
      FROM {CO}.OINM WHERE "DocDate" >= '2026-08-01' AND "Warehouse" IN ('BH-BT','BH-PF') GROUP BY "ItemCode"),
    n AS (SELECT "ItemCode" IC, SUM("OnHand") OH FROM {CO}.OITW WHERE "WhsCode" IN ('BH-BT','BH-PF') GROUP BY "ItemCode")
    SELECT n.IC, n.OH - IFNULL(s.N,0) Q FROM n LEFT JOIN s ON s.IC=n.IC WHERE n.OH - IFNULL(s.N,0) > 0'''):
    if r["IC"] in codes: fg_open[r["IC"]] = f(r["Q"])
# FG for SKUs the August plan never touches still sits in the godown and takes up room.
# The simulator never makes or ships them, so they are a constant block of occupancy —
# leaving them out understates the floor by ~83,000 L.
fg_plan_l = sum(q * byc[c]["litres_per_piece"] for c, q in fg_open.items())
fg_other_l = max(0.0, 461225 - fg_plan_l)

# ---------------------------------------------------------------- inbound (CREDIBLE only)
inbound = collections.defaultdict(lambda: collections.defaultdict(float))
skipped = 0
# Only LIVE open POs count. The study graded every row:
#   STALE_DEAD (1,590 rows)      — PO paper >90 days old at 1 Aug; delivered 0.0%
#   KEYING_ERROR_X1000 (3 rows)  — 141,034,848 L of phantom oil
#   EXIM_CONTRACT (3 rows)       — incl. the Ukraine crude, expired, no ETA, no GRPO
#   DUPLICATE_OF_SAP_PO (1 row)
# Counting any of them as inbound is how a planner convinces itself material is coming.
ACCEPT_CRED = {"LIVE"}
for r in read("out/aug01-inbound-TRUTH.csv"):
    if str(r.get("row_type", "")).upper() != "OPEN_PO": skipped += 1; continue
    if str(r.get("credibility", "")).upper() not in ACCEPT_CRED: skipped += 1; continue
    q = f(r.get("open_qty_aug01"))
    if q <= 0: continue
    c = canon(r.get("canonical_code") or r["code"])
    try: d = date.fromisoformat(str(r.get("due_on"))[:10])
    except ValueError: d = date(2026, 8, 1)
    if d < date(2026, 8, 1): d = date(2026, 8, 1)
    if d > date(2026, 8, 31): continue
    inbound[d.isoformat()][c] += q

# ---------------------------------------------------------------- realise, orders, backlog
realise = {}
for x in read("out/realise-by-item-PRE-AUG.csv"):
    c = str(x["item"]).split("—")[0].split("-")[0].strip()[:9]
    if c.startswith("FG"): realise[c] = round(f(x["realise"]), 2)

# The demand file carries THREE source systems and only ONE is an order book:
#   SAP_ORDR_RDR1                    real, dated, joinable        <- USE THIS
#   FACTORY_APP_orderproc_OMSmirror  dead OMS mirror, unjoinable, last sync 17 Aug,
#                                    overlaps SAP -> would double-count
#   FACTORY_APP_forecast43_SPR       the plant's own FORECAST, 3,126,479 pcs ALL dated
#                                    2026-08-01 -> a projection, not demand. Loading it
#                                    put 3.1M pieces of phantom orders on day one.
orders, backlog = [], []
for r in read("out/aug01-demand-TRUTH.csv"):
    if str(r.get("source_system", "")).strip() != "SAP_ORDR_RDR1": continue
    if r["item_code"] not in codes: continue
    rec = dict(docnum=r["order_ref"], date=str(r["date_raised"])[:10], customer=r["customer"][:60],
               channel=r["channel"], code=r["item_code"], pieces=f(r["pieces"]), value=f(r["value"]))
    if str(r.get("open_on_aug01", "")).strip().upper() in ("TRUE", "Y", "YES", "1"): backlog.append(rec)
    elif rec["date"] >= "2026-08-01" and rec["date"] <= "2026-08-31": orders.append(rec)

people = []
for fn in sorted(os.listdir("people")):
    if not fn.endswith(".md") or fn.startswith(("_", "ASK", "DISPATCH", "MISSING", "ORG", "ROSTER", "SCOPE")): continue
    y = yaml_front(os.path.join("people", fn))
    if y.get("whatsapp"):
        people.append(dict(name=y.get("name", fn[:-3]), whatsapp=y["whatsapp"],
                           display=y.get("phone_display", ""), title=y.get("title", ""), function=y.get("function", "")))

out = dict(
  meta=dict(frozen="2026-08-31", as_of="2026-08-01", horizon=["2026-08-01", "2026-08-31"],
            rule="ONLY 1 August is observed. Every later day is computed. The one thing that arrives daily is that day's POs."),
  opening=dict(
    stock=dict(stock), fg=fg_open, at_zero=at_zero,
    fg_litres=461225, fg_pieces=277774, fg_plan_l=round(fg_plan_l), fg_other_l=round(fg_other_l),
    standing_l=467089, standing_31jul_l=422771, standing_docs=114,
    oil_l=721587, packaging_pieces=3652205,
    storage_book_pct=55.8, storage_physical_l=928314, storage_physical_pct=112.2,
    backlog_pieces=169040, backlog_value=47000000,
  ),
  inbound_prebooked={k: dict(v) for k, v in inbound.items()},
  lines={  # observed where the app's rated figure is refuted
    "JP Machine":    {"1L": 5400},
    "Clear Pack":    {"1L": 4800, "4L": 1000, "5L": 1000},
    "10 Head":       {"1L": 2100, "2L": 1260, "5L": 900},
    "6 Head":        {"1L": 1080, "2L": 720,  "5L": 600},
    "Pouch Machine": {"POUCH": 4200},
    "Tin Head":      {"TIN": 215},
  },
  rules=dict(shift_hours=12, working_days=26, sundays_off=True, any_oil_any_line=True,
             flush_litres=400, line_clearance_min=51.3, efficiency=0.50,
             storage_ceiling_l=827000, storage_peak_l=923000,
             lead_days=dict(oil=11, packaging=6), invoice_truck_lag_days=2,
             priority=["PO", "realise_per_line_hour", "premium"]),
  actuals_for_scoring=dict(made_l=2119237, made_pieces=1567277, skus=81,
                           plan_pct=51.0, line_utilisation_pct=32.5, production_days=25,
                           note="OUTCOME data. Never a simulator input — the yardstick only."),
  provenance=dict(
    opening_fg="SAP OITW minus OINM since 2026-08-01, BH-BT+BH-PF, groups 102+115. 461,225 L / 277,774 pcs. Reproduced independently to 0.3 L.",
    opening_materials="out/aug01-materials-TRUTH.csv — factory app stock-as-of AND SAP rewind; 0 mismatches in 7,858 cells once the day boundary is aligned. SAP OPENING chosen (the factory app returns end-of-day).",
    standing="Measured per document from BOTH exit doors (/gate-core/sales-dispatch/ + /warehouse/bst/): 467,089 L, 114 docs. 84 of 84 customer docs docked 1 Aug or later.",
    inbound="out/aug01-inbound-TRUTH.csv, credible rows only. Excludes 141,034,848 L of phantom oil (3 POs keyed x1000) and 22.4M units on paper >90 days old (0.0% delivery rate).",
    lines="ji.jivo.in line masters. Clear Pack 5L 3,000/hr REFUTED (observed median 831, best 1,068) -> 1,000. Tin Head has NO app config; Aug peak 215/hr. Line clearance 51.3 min median.",
    efficiency="Observed ~50% of rated when running (median 50.1% per run). Applied — a plan at rated speed is not achievable.",
    orders="SAP ORDR/RDR1. The factory app has no Oil order book of its own (its Order Processing is a dead OMS mirror, unjoinable, last sync 2026-08-17).",
    realise="Control Panel, May-Jul 2026 only. No August leakage.",
    synonyms="reference/oil-synonyms.csv. 98.3% of groundnut sits under the peanut alias; RM0000052 olive holds 294,993 L but ALL in BH-OT (Param's) so the godown rule excludes it.",
    caution="The factory app is NOT independent of SAP — its own metadata says on-hand is reconstructed from SAP OINM. Agreement is an implementation check, not two measurements.",
  ),
  plan=plan, bom={k: v for k, v in bom.items() if k in codes}, blends=dict(blends),
  items=items, realise=realise, orders=orders, backlog=backlog, people=people,
)
os.makedirs("sim", exist_ok=True)
json.dump(out, open("sim/sim-inputs.json", "w"), indent=1)
print(f"sim/sim-inputs.json rebuilt — {os.path.getsize('sim/sim-inputs.json')/1e6:.1f} MB\n")
print(f"  plan            {len(plan)} SKUs, {sum(p['litres'] for p in plan):,.0f} L")
print(f"  materials       {len(stock)} codes  ({sum(1 for v in stock.values() if v<=0)} at zero)")
print(f"  FG opening      {sum(fg_open.values()):,.0f} pcs across {len(fg_open)} SKUs")
print(f"  inbound days    {len(inbound)}   (phantom rows skipped: {skipped})")
print(f"  orders          {len(orders)} lines   backlog {len(backlog)} lines")
print(f"  people          {len(people)}")
