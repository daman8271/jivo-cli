#!/usr/bin/env python3
"""
PHASE 0 — freeze every input the August simulation may use into ONE file.

sim/sim-inputs.json is the only thing the simulator, the message layer and the site
read. Nothing downstream may query SAP, EXIM or the factory app. If a number is not
in this file it does not exist. That is what stops the replay drifting or inventing.

Provenance is recorded per block so every figure on the site traces to its source.
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
        if r.returncode == 0: return list(csv.DictReader(io.StringIO(r.stdout)))
    sys.exit(f"HANA unreachable: {r.stderr[:200]}")

def read(path): return list(csv.DictReader(open(path)))

def yaml_front(path):
    s = open(path).read()
    m = re.match(r"^---\n(.*?)\n---", s, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1); out[k.strip()] = v.strip().strip('"')
    return out

# ---------------------------------------------------------------- synonyms
syn = {r["alias"]: r["canonical"] for r in read("reference/oil-synonyms.csv")
       if r.get("alias") and not str(r["alias"]).startswith("#")}
def canon(c): return syn.get(c, c)

# ---------------------------------------------------------------- plan
plan = []
for r in read("out/plan-aug-resolved.csv"):
    if not r["pieces"] or r["code"] in HELD: continue
    plan.append(dict(code=r["code"], sku=r["sku"], head=r["head"], category=r["category"],
                     pack_type=r["pack_type"], litres_per_piece=f(r["litres_per_piece"]),
                     pieces=int(f(r["pieces"])), litres=f(r["litres"])))

# ---------------------------------------------------------------- BOM
bom = collections.defaultdict(list)
for r in hana(f'''SELECT T."Code" F, C."Code" C, C."Quantity"/T."Qauntity" PER
    FROM {CO}.OITT T JOIN {CO}.ITT1 C ON C."Father"=T."Code"
    WHERE T."TreeType"='P' AND C."Type"<>290'''):
    bom[r["F"]].append([canon(r["C"]), f(r["PER"])])
for x in read("reference/reconstructed-boms.csv"):
    if x["father"] not in bom: bom[x["father"]].append([canon(x["child"]), f(x["per_piece"])])
# BOM yield guard (9 FGs with Qauntity=1 on a case BOM) — same rule as plan_explode.py
codes = {p["code"]: p for p in plan}
for c, kids in list(bom.items()):
    if c not in codes: continue
    lpc = codes[c]["litres_per_piece"]
    oil = sum(per for ch, per in kids if ch.startswith("RM"))
    if lpc and oil:
        n = round(oil / lpc)
        if n >= 2 and abs(oil / lpc - n) / n < 0.02:
            bom[c] = [[ch, per / n] for ch, per in kids]
# blends
blends = collections.defaultdict(list)
for r in read("reference/blend-recipes.csv"):
    blends[r["blend"]].append([canon(r["component"]), f(r["per_litre"])])

# ---------------------------------------------------------------- items
items = {}
for r in hana(f'''SELECT "ItemCode" IC, "ItemName" NM, "InvntryUom" U FROM {CO}.OITM
    WHERE "ItemCode" LIKE 'RM%' OR "ItemCode" LIKE 'PM%' OR "ItemCode" LIKE 'FG%' '''):
    items[r["IC"]] = dict(name=r["NM"], uom=r["U"])

# ---------------------------------------------------------------- opening position
stock = collections.defaultdict(float)
for r in read("out/aug01-stock.csv"): stock[canon(r["code"])] += f(r["onhand_aug01"])
fg = {}
for r in read("out/aug01-wip-fg.csv"):
    if str(r.get("kind", "")).upper() == "FG": fg[r["code"]] = f(r.get("qty_aug01"))
# pre-August open POs, landing on due date (overdue -> day 1)
inbound = collections.defaultdict(lambda: collections.defaultdict(float))
for r in read("out/aug01-open-po.csv"):
    q = f(r["qty_open_aug1"])
    if q <= 0: continue
    try: d = date.fromisoformat(str(r["due_date"])[:10])
    except ValueError: d = date(2026, 8, 1)
    if d < date(2026, 8, 1): d = date(2026, 8, 1)
    if d > date(2026, 8, 31): continue
    inbound[d.isoformat()][canon(r["code"])] += q

# ---------------------------------------------------------------- realise (pre-Aug only)
realise = {}
for x in read("out/realise-by-item-PRE-AUG.csv"):
    c = str(x["item"]).split("—")[0].split("-")[0].strip()[:9]
    if c.startswith("FG"): realise[c] = round(f(x["realise"]), 2)

# ---------------------------------------------------------------- REAL August order book (the demand shifts)
orders = []
for r in hana(f'''SELECT H."DocNum" N, H."DocDate" D, H."CardCode" CC, H."CardName" CN,
      L."ItemCode" IC, SUM(L."Quantity") Q, SUM(L."LineTotal") V
    FROM {CO}.ORDR H JOIN {CO}.RDR1 L ON L."DocEntry"=H."DocEntry"
    WHERE H."CANCELED"='N' AND H."DocDate">='2026-08-01' AND H."DocDate"<'2026-09-01'
      AND L."ItemCode" LIKE 'FG%'
    GROUP BY H."DocNum", H."DocDate", H."CardCode", H."CardName", L."ItemCode"'''):
    orders.append(dict(docnum=r["N"], date=str(r["D"])[:10], card=r["CC"], customer=r["CN"],
                       code=r["IC"], pieces=f(r["Q"]), value=f(r["V"])))
MART = {"CUSTA000001","CUSTA000002","CUSTA000003","CUSTA000004","CUSTA000606",
        "CUSTA000827","CUSTA000906","CUSTA001099","CUSTA001113"}
for o in orders:
    o["channel"] = "MART" if o["card"] in MART else ("MT" if any(k in o["customer"].upper()
                    for k in ("WAL MART","METRO","CANTEEN","RELIANCE","DMART","BIG BAZAAR")) else "GT")

# ---------------------------------------------------------------- people
people = []
for fn in sorted(os.listdir("people")):
    if not fn.endswith(".md") or fn.startswith(("_", "ASK", "DISPATCH", "MISSING", "ORG", "ROSTER", "SCOPE")): continue
    y = yaml_front(os.path.join("people", fn))
    if not y.get("whatsapp"): continue
    people.append(dict(name=y.get("name", fn[:-3]), whatsapp=y["whatsapp"],
                       display=y.get("phone_display", ""), title=y.get("title", ""),
                       function=y.get("function", "")))

out = dict(
  meta=dict(frozen="2026-08-30", as_of="2026-08-01", horizon=["2026-08-01","2026-08-31"],
            rule="Nothing downstream may read any source but this file."),
  provenance=dict(
    plan="AUG MONTHLY PLANNING 2026 By Gurvinder Vj 03.08.2026.xlsx, sheet FINAL (2), ruled by Daman 2026-08-29",
    units="sale-tonne = 1,000 L; purchase-tonne = 1,000 kg; oil 910 g/L (C-0050)",
    bom="SAP OITT/ITT1 + reference/reconstructed-boms.csv; yield guard for 9 case-BOMs",
    blends="RM0000021 GOLD + RM0000040 SO OLIVE only (Daman), ratios from Feb-Jul work orders",
    synonyms="reference/oil-synonyms.csv — groundnut=peanut etc. (Daman 2026-08-29)",
    stock="SAP OITW minus OINM movements since 2026-08-01, allow-listed godowns incl. BH-GJ",
    inbound="POs raised before 2026-08-01, landing on due date; overdue lands day 1",
    realise="Control Panel jivo sales data, May-Jul 2026 ONLY (no August leakage)",
    orders="SAP ORDR/RDR1, August 2026 — the real order book, used to shift priorities day by day",
    lines="reference/PLAN-AND-LINES.md — Daman's rulings 2026-08-29",
    storage="Daman's godown sheet 2026-08-29: 827,000 L working ceiling BH-BT+BH-PF (C-0054: physical = OnHand + invoiced-not-dispatched)",
    people="jolly/people/*.md — numbers given by Daman",
  ),
  lines={
    "JP Machine":    {"1L": 5400},
    "Clear Pack":    {"1L": 4800, "4L": 3000, "5L": 1500},   # 3,000 refuted: best-ever 2,695, typical 1,025-1,509
    "10 Head":       {"1L": 2100, "2L": 1260, "5L": 900},
    "6 Head":        {"1L": 1080, "2L": 720,  "5L": 600},
    "Pouch Machine": {"POUCH": 4200},
    "Tin Head":      {"TIN": 240},
  },
  rules=dict(shift_hours=12, working_days=26, sundays_off=True, any_oil_any_line=True,
             flush_litres=400, flush_oil_reused_monthly=True,
             efficiency_observed=0.47, storage_ceiling_l=827000, storage_opening_l=664341,
             lead_days=dict(oil=11, packaging=6),
             priority=["PO", "realise_per_line_hour", "premium"]),
  plan=plan, bom={k: v for k, v in bom.items() if k in codes}, blends=dict(blends),
  items={k: v for k, v in items.items()},
  opening=dict(stock=dict(stock), fg=fg),
  inbound_prebooked={k: dict(v) for k, v in inbound.items()},
  realise=realise, orders=orders, people=people,
)
os.makedirs("sim", exist_ok=True)
json.dump(out, open("sim/sim-inputs.json", "w"), indent=1)
print(f"sim/sim-inputs.json — {os.path.getsize('sim/sim-inputs.json')/1e6:.1f} MB")
print(f"  plan {len(plan)} SKUs · bom {len(out['bom'])} · items {len(items)} · stock {len(stock)} codes")
print(f"  inbound days {len(inbound)} · realise {len(realise)} · ORDERS {len(orders)} lines "
      f"({sum(o['pieces'] for o in orders):,.0f} pcs, Rs {sum(o['value'] for o in orders)/1e7:.1f} Cr)")
print(f"  people {len(people)}")
