#!/usr/bin/env python3
"""build_mark4_rulebook.py — writes reference/mark4-rulebook.json and reference/MARK4-RULEBOOK.md

The Mark 4 machine rulebook: every ruling from the 5 Sep 2026 meeting with Gurvinder
veerji (reference/meetings/2026-09-05-gurvinder-review.md) and Daman's clarifications
of 6 Sep 2026, plus every ASSUMPTION Mark 4 makes on top, plus the speeds computed from
the factory app's own records. Nothing here is typed from memory: speeds come from
out/august-actuals-SCORING.csv (136 real runs) and reference/app-line-configs-2026-09-06.json;
containers and bottle grams come from the SAP BOM frozen in sim/sep-inputs.json.

    cd jolly && python3 reference/build_mark4_rulebook.py

The engine (engine/august_sim.py via live/freeze_live.py) and the site's Assumptions
page both read the JSON. The MD is the human copy of the same object — never edit it
by hand; edit this script.
"""
import csv, io, json, re, statistics, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-09-06"
MEETING = "reference/meetings/2026-09-05-gurvinder-review.md"
QUESTIONS = "out/QUESTIONS-FOR-GURVINDER-2026-09-06.md"

# R15 — pack and bottle come from the recipe — lives in ONE place, because the
# freeze classes the SKUs this file never sees and gen re-derives it as AC06.
sys.path.insert(0, str(ROOT / "engine"))
from pack_class import ENGINE_SLOTS, FAMILIES, SLOTS, pack_class, sheet_slot, slot_by_litres  # noqa: E402

# ----------------------------------------------------------------------------- data
with open(ROOT / "sim/sep-inputs.json", encoding="utf-8") as _fh: S = json.load(_fh)
ITEMS, BOM, PLAN = S["items"], S["bom"], {p["code"]: p for p in S["plan"]}
with open(ROOT / "reference/app-line-configs-2026-09-06.json", encoding="utf-8") as _fh: CFG = json.load(_fh)
CFG = CFG.get("results") if isinstance(CFG, dict) else CFG
with open(ROOT / "out/august-actuals-SCORING.csv", encoding="utf-8") as _fh: lines_txt = _fh.read().splitlines()
RUNS = [r for r in csv.DictReader(io.StringIO("\n".join(lines_txt[1:]))) if r.get("section") == "APP_RUN"]

def f(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d

# Who imports engine/pack_class.py. COMPUTED, never asserted: the rulebook is read
# on the site's /assumptions page, and a published claim that the BOM rule is in
# force when it is not would be a lie in the one place a reader goes to check.
PACK_CLASS_PLANNED = ["live/freeze_live.py", "live/gen_live.py"]
def pack_class_callers():
    seen = []
    for rel in ["reference/build_mark4_rulebook.py", "engine/_pack_class_test.py",
                "engine/august_sim.py", "live/freeze_live.py", "live/gen_live.py", "live/collect.py"]:
        fp = ROOT / rel
        if fp.exists() and re.search(r"(?:from|import)\s+(?:engine\.)?pack_class\b", fp.read_text(encoding="utf-8")):
            seen.append(rel)
    return seen

# ------------------------------------------------------------------ pack class
# The rule itself is engine/pack_class.py — imported above, so the freeze and the
# site's AC06 check run the SAME code over the SKUs that are not on this sheet.
sku_pack = {}
for code, p in PLAN.items():
    sku_pack[code] = dict(sku=p["sku"], litres_per_piece=p["litres_per_piece"], sheet_pack_type=p["pack_type"],
                          **pack_class(code, BOM, ITEMS, p["litres_per_piece"], p["pack_type"]),
                          sheet_slot=sheet_slot(p["sku"], p["pack_type"], p["litres_per_piece"]))
# Where Mark 4 puts a product on a different machine than the engine does today.
# Both halves are computed — the left by the legacy sheet rule, the right by R15 —
# so this list shrinks by itself when the chain starts reading the rulebook.
ENGINE_SLOT_DISAGREES = sorted(c for c, v in sku_pack.items() if v["sheet_slot"] != v["engine_slot"])

# ------------------------------------------------------------- observed speeds
def run_slot(r):
    """The slot an August run belongs to, from its PRODUCT NAME — the fallback for
    the runs whose item code is not on the plan sheet. run_pack() prefers the BOM."""
    n = r["product"].upper(); l = f(r["pack_litres"])
    if "POUCH" in n: return "POUCH"
    if "KGS" in n or "TIN" in n or re.search(r"15\s*L", n): return "15L" if (l >= 12 or "KGS" in n or re.search(r"15\s*L", n)) else ("3L" if l <= 3.05 else "5L")
    if "200 L" in n: return "DRUM"
    return slot_by_litres(l, "PET")

def run_pack(r):
    """(slot, containers per logged piece) for an August run. The BOM rule (R15)
    when the app's item code is on the plan sheet, the name otherwise — one rule
    for what a run measures and what the plan schedules, or a run of one pack sets
    the speed of another. The app logs SETS for a combo, so its speed is scaled to
    the bottles the line actually filled (B13)."""
    v = sku_pack.get(r.get("item_code"))
    if v and v["slot"]: return v["slot"], v["fills_per_piece"]
    return run_slot(r), 1

# A combo run and a plain run of the same bottle are NOT one population, and
# averaging them together is not a measurement of either (B19). On Clear Pack the
# two clusters do not overlap at any point: plain 1 L 1,942-2,927 bottles/hr, combo
# sets 87-1,277. So the key carries whether the piece was a multi-fill, and the
# combo evidence gets its own published block (LINES[..]["speeds_multi"]).
obs_raw = defaultdict(list)          # (speed, minutes) per usable run
for r in RUNS:
    mins = f(r["segment_running_minutes"]); pcs = f(r["pieces"])
    if mins < 60 or pcs <= 0: continue                     # under an hour: too short to give a speed
    if mins > 20 * 60: continue                            # a run left open — the clock, not the machine
    slot, fills = run_pack(r)
    obs_raw[(r["line"], slot, fills > 1)].append((pcs * fills / (mins / 60.0), mins))
SUSTAINED_MIN = 180                                        # a run of 3 hours or more: long enough to mean something

rated = defaultdict(list)
for c in CFG:
    if not c.get("is_active"): continue
    ln, sp, name = c.get("line_name"), f(c.get("rated_speed")), str(c.get("config_name") or "")
    m = re.match(r"(\d+)\s*LTR", name.upper())
    if m: rated[(ln, f"{int(m.group(1))}L")].append(sp)
    elif ln == "Pouch Machine": rated[(ln, "POUCH")].append(sp)   # Hitech + Samarpan, two machines side by side
RATED_EXTRA = {("Tin Head", "15L"): (240.0, "Daman 2026-08-29: 4 tins/min; no app config row")}
CARRIED = {("Clear Pack", "4L"): (1000.0, "Mark 3 carried table; no app config, no August run")}
DERIVED = {("10 Head", "3L"): (("10 Head", "5L"), "3 L assumed to run at the 10 Head's 5 L planning rate (A15)"),
           ("Tin Head", "3L"): (("Tin Head", "15L"), "same tins-per-hour as 15 L (A05)"),
           ("Tin Head", "5L"): (("Tin Head", "15L"), "same tins-per-hour as 15 L (A05)")}

EFF = 0.8
MIN_RUNS_FOR_CAP = 3
IMPLAUSIBLE = 1.2       # a logged speed above 120% of rating is the clock, not the machine (one-hour segments carrying a day's pieces)
# Litres in one container of each slot, for the clock guard below. A drum is out of
# Mark 4 (R14) but the number is here so a drum run cannot slip past unchecked.
SLOT_LITRES = {"1L": 1.0, "2L": 2.0, "3L": 3.0, "4L": 4.0, "5L": 5.0, "15L": 15.0,
               "POUCH": 1.0, "DRUM": 200.0}
def rated_of(ln, slot):
    if rated.get((ln, slot)):
        vals = rated[(ln, slot)]
        rt = sum(vals) if (ln, slot) == ("Pouch Machine", "POUCH") else statistics.median(vals)
        return rt, "ji.jivo.in line-configs 2026-09-06" + (" (two machines SUMMED)" if slot == "POUCH" else "")
    if (ln, slot) in RATED_EXTRA: return RATED_EXTRA[(ln, slot)]
    return None, None
def line_litres_ceiling(ln):
    """The most litres an hour any RATED slot on this line can pour (B18).

    The clock guard has to work WITHOUT a rating, because a slot the app never
    rated is exactly where a one-hour segment carrying a whole day's pieces has
    nothing to check it. One machine cannot beat its own best rated slot by half
    again whatever bottle is on it, so litres an hour is the ceiling that travels
    across slots. None when the line has no rated slot at all."""
    lit = [rated_of(l, s)[0] * SLOT_LITRES[s]
           for (l, s) in list(rated) + list(RATED_EXTRA)
           if l == ln and SLOT_LITRES.get(s) and rated_of(l, s)[0]]
    return max(lit) if lit else None
_speed_cache = {}
def speed_block(ln, slot, multi=False):
    """The speed evidence for one line and pack. `multi` is the same line and pack
    when the saleable piece holds more than one container (a combo set): its own
    population, never merged into the plain one, and no carried or derived
    fallback — a rate invented for a combo would be a number about nothing."""
    if (ln, slot, multi) in _speed_cache: return _speed_cache[(ln, slot, multi)]
    rt, rt_basis = rated_of(ln, slot)
    raw = obs_raw.get((ln, slot, multi), [])
    ceiling_l = line_litres_ceiling(ln) if rt is None else None
    slot_l = SLOT_LITRES.get(slot)
    def clock_error(x):
        if rt is not None: return x > IMPLAUSIBLE * rt
        if ceiling_l and slot_l: return x * slot_l > IMPLAUSIBLE * ceiling_l
        return False
    kept = [(x, m) for x, m in raw if not clock_error(x)]
    o = [x for x, _m in kept]
    dropped = len(raw) - len(kept)
    med = round(statistics.median(o)) if o else None
    # A run under 3 hours is a trial, a changeover or a mis-clocked segment. `best`
    # has always excluded them; the median must too, or the typical branch plans
    # from the very runs the best branch threw away (6 Head 3 L was [11, 820, 4183]
    # in pieces/hr, and the 71-minute 4,183 set the median that became the plan).
    sustained = [x for x, m in kept if m >= SUSTAINED_MIN]
    med_sus = round(statistics.median(sustained)) if sustained else None
    best = round(max(sustained)) if sustained else (round(max(o)) if o else None)
    # planning_basis is the sentence a person reads; planning_rule is the same
    # thing as data, so gen_live.py can RECOMPUTE `planning` (AC05) instead of
    # parsing prose. Keep the two in step: one branch sets both.
    rule = dict(kind=None, factor=None, rated=rt, best=best, median=med, median_sustained=med_sus,
                runs=len(o), runs_sustained=len(sustained), sustained_min_minutes=SUSTAINED_MIN,
                min_runs=MIN_RUNS_FOR_CAP, carried_from=None, derived_from=None)
    if rt is not None and best is not None and len(o) >= MIN_RUNS_FOR_CAP:
        plan = min(EFF * rt, best); basis = f"min(80% x rated, best sustained August run of 3 h+) over {len(o)} runs"
        rule.update(kind="capped", factor=EFF)
    elif rt is not None:
        plan = EFF * rt; basis = "80% x rated" + (f" (only {len(o)} usable August run(s), too few to cap)" if o else " (no August run)")
        rule.update(kind="rated", factor=EFF)
    elif med_sus is not None and len(sustained) >= MIN_RUNS_FOR_CAP:
        plan = med_sus; basis = f"typical (median) August run of 3 h+, no rating in the app, over {len(sustained)} runs — no 80% on top, a typical run already carries the inefficiency"
        rule.update(kind="typical")
    elif not multi and (ln, slot) in CARRIED:
        plan = EFF * CARRIED[(ln, slot)][0]; basis = "80% x " + CARRIED[(ln, slot)][1]
        rule.update(kind="carried", factor=EFF, carried_from=CARRIED[(ln, slot)][0])
    elif not multi and (ln, slot) in DERIVED:
        src, why = DERIVED[(ln, slot)]; plan = speed_block(*src)["planning"]; basis = "DERIVED: " + why
        rule.update(kind="derived", derived_from=list(src))
    else:
        plan = None
        basis = ("NO RATE — needs a ruling"
                 + (f" (the {len(o)} usable August run(s) are too few to be a typical rate)" if o else ""))
        rule.update(kind="none")
    if dropped:
        basis += (f"; {dropped} run(s) discarded as clock errors — above "
                  + (f"{int(IMPLAUSIBLE*100)}% of rating" if rt is not None
                     else f"{int(IMPLAUSIBLE*100)}% of this line's best rated litres/hour"))
    blk = dict(rated=rt, rated_basis=rt_basis, multi_fill=multi,
               # the whole kept spread, not just its middle: a median of 820 over
               # [11, 820, 4183] reads like a measurement and is not one.
               aug_min=round(min(o)) if o else None, aug_median=med, aug_max=round(max(o)) if o else None,
               aug_median_sustained=med_sus, aug_best=best,
               aug_runs=len(o), aug_runs_sustained=len(sustained), aug_runs_discarded=dropped,
               planning=round(plan) if plan is not None else None, planning_basis=basis, planning_rule=rule,
               # `rated` is what the machine is rated at; `planning` is what the plan
               # may book — the 80% and the August cap are ALREADY inside it. The
               # engine's `lines` table holds rated speeds and multiplies by
               # rules.efficiency at run time; a planning speed put in that table
               # with rules.efficiency still at 0.5 halves the plant.
               post_efficiency=True)
    _speed_cache[(ln, slot, multi)] = blk
    return blk

# --------------------------------------------------------------- eligibility
# pref 1 = fill here first; 2 = when pref-1 lines are full that day; 3 = last resort.
LINES = {
  "JP Machine":  {"app_line_id": 2, "slots": {
      "1L": {"26G": 1, "ROUND-23.8G": 1, "SMALL": 1, "52G": 3}},
      "notes": ["1-litre mustard first (26 g and round bottles). Groundnut 52 g allowed: 43,584 L in August.",
                "Can run as the ONE night line (meeting 11:18-11:30: 'today the preference was mustard on JP')."]},
  "Clear Pack":  {"app_line_id": 1, "slots": {
      "1L": {"40G": 1, "52G": 2}, "2L": {"ANY": 2}, "4L": {"ANY": 2}, "5L": {"HDPE": 1}},
      "notes": ["Never 3 L, never 15 L, never tins (meeting 03:03, 05:38).",
                "40 g today (sunflower, canola). 52 g 'we can if we want' (Daman 2026-09-06) — allowed, not preferred.",
                "No 75 g bottle: sesame 1 L cannot run here (meeting 11:42). No 26 g: mustard belongs to JP.",
                "August: 284,060 L of 5 L HDPE in 10 runs — the plant's biggest 5 L line by record."]},
  "10 Head":     {"app_line_id": 3, "slots": {
      "1L": {"52G": 1, "75G": 1, "SMALL": 2, "40G": 2, "26G": 3, "ROUND-23.8G": 3}, "2L": {"ANY": 1}, "3L": {"HDPE": 2}, "5L": {"HDPE": 3}},
      "notes": ["1 L and 2 L preferred — all ten heads usable (meeting 07:49).",
                "Takes every 1 L bottle Clear Pack cannot (meeting 11:50). 5 L allowed but poor: heads too close (07:36).",
                "Never 15 L, never tins."]},
  "6 Head":      {"app_line_id": 4, "slots": {
      "5L": {"HDPE": 1, "TIN": 1}, "3L": {"HDPE": 1, "TIN": 2}, "2L": {"ANY": 2}, "1L": {"ANY": 3}},
      "notes": ["5 L first: spaced heads; labeller broken; printed 5 L tins need no label (meeting 08:21-08:44). August: 137,520 L HDPE + 62,600 L tins.",
                "3 L HDPE ran here 3 times in August (23,886 L) — the SKU Mark 3 called unproducible.",
                "Never 15 L."]},
  "Tin Head":    {"app_line_id": 6, "slots": {
      "15L": {"TIN": 1}, "3L": {"TIN": 1}, "5L": {"TIN": 2}},
      "notes": ["All 15-litre tins, always (meeting 08:15-08:20). Includes the 15 kg / 12 kg / 13 kg tins.",
                "3 L tins here by Daman's call 2026-09-06 (open question 4 for Gurvinder). 5 L tins prefer the 6 Head."]},
  "Pouch Machine": {"app_line_id": 5, "slots": {"POUCH": {"ANY": 1}},
      "notes": ["Pouches only. No requirement today; run on a day labour is free (meeting 12:23-12:45)."]},
}
EXCLUDED_LINES = {"Manual": "app line_id 7 — one DRAFT run ever, never a drum. Out of Mark 4 (Daman 2026-09-06)."}

for ln, spec in LINES.items():
    spec["speeds"] = {slot: speed_block(ln, slot) for slot in spec["slots"]}
    # ...and, only where the line has actually run one, the same pack as a combo
    # set. Published where the evidence is, blank where it is not: a line with no
    # combo record has NO combo rate, and a SKU whose fills_per_piece is above 1
    # cannot be scheduled there until someone gives one (B19).
    spec["speeds_multi"] = {slot: speed_block(ln, slot, True) for slot in spec["slots"]
                            if obs_raw.get((ln, slot, True))}
    spec["speeds_multi_note"] = ("Use this block, not `speeds`, for a SKU whose sku_pack.fills_per_piece "
                                 "is above 1. Both are in bottles (containers) per hour.")
    spec["aug_litres_by_slot"] = {}
    spec["aug_litres_multi_by_slot"] = {}
for r in RUNS:
    ln = r["line"]
    if ln in LINES:
        s, fills = run_pack(r)
        key = "aug_litres_multi_by_slot" if fills > 1 else "aug_litres_by_slot"
        LINES[ln][key][s] = round(LINES[ln][key].get(s, 0) + f(r["litres"]))

# ------------------------------------------------------------------ rulings
SETTLED = [
 dict(id="R01", rule="Factory truth is ji.jivo.in, never SAP, for production, stock, dispatch and lines.", source="jolly/CLAUDE.md RULE 0 (Daman 2026-09-03)"),
 dict(id="R02", rule="A shift is 12 clock hours with lunch and tea inside it: 10 working hours per session. Day + night = 20 hours, not 22, not 24.", source="meeting 14:13-14:43"),
 dict(id="R03", rule="Labour allows ONE line at night. Which one is the plant's call; the plan names its pick each day.", source="meeting 11:06-11:31"),
 dict(id="R04", rule="Sunday: no production. Sunday is for dispatch — relieve the godown.", source="meeting 13:14-13:41"),
 dict(id="R05", rule="Plan at 80% of capacity. If the machine gives more, good.", source="meeting 08:46-09:20; Daman 2026-09-06: '80% efficiency in relation to speed'"),
 dict(id="R06", rule="Keep one product running on a line all day. Every changeover lowers efficiency and output and raises labour cost.", source="meeting 09:28-09:59"),
 dict(id="R07", rule="Clear Pack cannot fill 3 L or 15 L. 10 Head and 6 Head cannot fill 15 L. 15-litre tins only on the Tin Head.", source="meeting 03:03-03:19, 05:38-05:57, 08:05-08:20"),
 dict(id="R08", rule="3 L runs on the 10 Head and the 6 Head.", source="meeting 03:03-03:19; August: 6 Head 23,886 L"),
 dict(id="R09", rule="JP: 1-litre mustard (Kachi Ghani; the 26 g and round bottles run best). Groundnut 1 L allowed.", source="meeting 06:22-06:43, 12:13-12:20; Daman 2026-09-06 'majorly mustard, also groundnut'"),
 dict(id="R10", rule="Clear Pack: 1 L in the 40 g bottle (canola, sunflower); the 52 g bottles allowed. Sesame (75 g) never.", source="meeting 06:43-07:07, 11:42; Daman 2026-09-06"),
 dict(id="R11", rule="10 Head: 1 L and 2 L preferred (all ten heads usable). Every 1 L bottle Clear Pack cannot fill goes here. 5 L possible but poor.", source="meeting 07:07-07:49, 11:50"),
 dict(id="R12", rule="6 Head: 5 L first (spaced heads; labeller broken; printed 5 L tins need no label), then 3 L, then leftover 1 L / 2 L.", source="meeting 07:18-07:26, 08:05-08:44"),
 dict(id="R13", rule="Pouches only on the pouch machine. No pouch requirement today.", source="meeting 09:20, 12:23"),
 dict(id="R14", rule="Drums are filled by hand and are OUT of Mark 4: the three 200 L SKUs are listed as 'filled by hand, not scheduled', never as stuck.", source="Daman 2026-09-06 (meeting 02:45-04:07 for the manual drum line)"),
 dict(id="R15", rule="The pack of a product comes from its recipe (BOM container item), never from the plan sheet's pack-type column. Seven '15 LTR PET' rows and SO Olive 5 L are tins.", source="BOM check 2026-09-06; meeting 08:05 'they are 15-litre tins'; Daman 2026-09-06 yes"),
 dict(id="R16", rule="Make at least ₹2 crore of goods a day; ₹2.5 crore a day finishes the plan sheet.", source="meeting 13:41-14:11; Daman 2026-09-06 'it is yes'"),
 dict(id="R17", rule="Do not plan from POs alone — GT/MT orders bunch in the last weeks of the month and the buffer runs out. Production planning predicts the month's POs from past GT/MT sales (excluding e-com) and is ready for them.", source="meeting 10:19-11:02; Daman 2026-09-06"),
 dict(id="R18", rule="Past GT/MT sales are read from OMS and from SAP bills. E-com stays on its POs.", source="Daman 2026-09-06"),
 dict(id="R19", rule="A product with no order behind it and last-in-sales goes last (canola 5 L 4 pcs).", source="meeting 10:07-10:27"),
 dict(id="R20", rule="The 1-litre pack moves from a 16-piece carton to a 20-piece carton wherever 16 was used. A recipe change; a major step.", source="meeting 04:26-04:43, 15:51-16:02"),
 dict(id="R21", rule="'Trucks that left today' is irrelevant. Show the open dispatch book in days of pendency and 'billed today, on a truck when' (2 days usual, 14 worst).", source="meeting 00:43-01:08"),
 dict(id="R22", rule="The overview must read line by line, not as one total.", source="meeting 05:11-05:23"),
 dict(id="R23", rule="Godown = BH-BT + BH-PF finished goods against 827,000 L working / 923,000 L peak. It is over 90% full.", source="STORAGE-CAPACITY.md; meeting 13:24; Daman 2026-09-06"),
 dict(id="R24", rule="Labour cost comes from the factory app (ji.jivo.in): crew per run, hours.", source="meeting 12:43-13:03; Daman 2026-09-06 'JA = factory app'"),
 dict(id="R25", rule="When a material is missing, the person responsible enters WHY; when the plan says X and the plant runs Y, the system asks the relevant person and keeps the answer as a rule. Messages via WhatsApp — NOT in this build (Daman 2026-09-06: build Mark 4 first).", source="meeting 15:21-16:54; Daman 2026-09-06"),
 dict(id="R26", rule="Every assumption Mark 4 makes is listed on its own page: what is taken as fact, the exact data used, and what would change it.", source="Daman 2026-09-06"),
 dict(id="R27", rule="Only day 1 is observed; every later day is computed. Forecast rows stay triple-tagged. No real phone number ever. Never type a business number into the site.", source="jolly/CLAUDE.md"),
]

ASSUMED = [
 dict(id="A01", assumption="Planning speed per line and pack = min(80% x the app's rated speed, the best August run that lasted 3 hours or more) when at least 3 usable August runs exist; else 80% x rated; for a pack the app has no rating for, the typical (median) August run; else 80% x the Mark 3 carried table. A usable run logged at least 60 minutes; a logged speed above 120% of the rating is discarded as a clock error (one-hour segments carrying a whole day's pieces).",
      why="80% of capacity is the ruling (R05). The app's rated speeds were never reached in August (JP typical 39% of rated), so 'capacity' is capped at what the machine has demonstrated. A run left open through breaks makes August speeds read slower than they were, so the cap is conservative.",
      changes_it="Gurvinder's answer to question 1 (his own capacity number per machine)."),
 dict(id="A02", assumption="Packs of 1 L or less (200 ml, 250 ml, 500 ml, 869 g / 954 ml) fill in the 1 L slot at the 1 L pieces-per-hour rate.", why="No August run of 250/500 ml exists; JP ran 200 ml and 954 ml in August.", changes_it="A measured small-pack run in the app."),
 dict(id="A03", assumption="Bottle family decides eligibility on JP, Clear Pack and 10 Head (26 g / round / 40 g / 52 g / 75 g / small). 2 L, 3 L, 4 L, 5 L bottles are one family each.", why="Meeting 06:22-07:07: the lines' efficiency is bottle-specific. No ruling separates 2 L or 5 L bottles.", changes_it="The machine-spec sheet Daman will give for Mark 5/6."),
 dict(id="A04", assumption="3-litre tins fill on the Tin Head (fallback 6 Head).", why="Daman 2026-09-06: tins have a shape, they go on the tin machine. No August record of a 3 L tin run.", changes_it="Gurvinder question 4."),
 dict(id="A05", assumption="Tin Head fills 3 L and 5 L tins at the same pieces-per-hour as 15 L tins (240/hr rated).", why="No rate exists for smaller tins on the Tin Head.", changes_it="A measured run, or Gurvinder question 1."),
 dict(id="A06", assumption="The Tin Head is available every working day of September.", why="It ran 1 day in June, 1 in July, 2 in August, 1 so far in September; the plan needs about 7 full days of it.", changes_it="Gurvinder question 5."),
 dict(id="A07", assumption="The night line is chosen each day as the line with the most PO-backed litres still unmade after the day session; ties go to JP (mustard).", why="R03 says one line, the plant's call; the meeting's example was mustard on JP.", changes_it="A daily pick from Gurvinder (later: via the why-loop)."),
 dict(id="A08", assumption="A changeover (oil change, cold start, or pack-size change) costs 51.3 minutes of line clearance; an oil change also flushes 400 L. A pack-size change costs no more than that.", why="Mark 3's measured clearance; nobody has said how long a 1 L → 5 L change takes.", changes_it="Gurvinder question 7."),
 dict(id="A09", assumption="Expected GT/MT demand per SKU = the average of the last 3 months of GT/MT billing (SAP invoices, Oil book, channel GT/MT, e-com and inter-company excluded), shaped by week-of-month from the same history. The OMS open book supplies real orders on top.", why="R17/R18. SAP bills are the only complete 3-month record; OMS history before 2 Sep is not yet backfilled.", changes_it="Gurvinder question 12 (months, per product or per oil); the OMS backfill."),
 dict(id="A10", assumption="A new FG code seen in the factory app but absent from the plan sheet is the same product as the plan row with the same name minus its carton count (16 PCS ↔ 20 PCS). Pieces targets stay; the carton item changes.", why="R20; Cold Press Groundnut 1 L 20 pcs (FG0000461) has run on the 10 Head since 3 Sep and is not in the 31 Aug sheet.", changes_it="Gurvinder question 11."),
 dict(id="A11", assumption="Dispatch continues on Sundays at the weekday rate.", why="R04: Sunday is for dispatch. No measured Sunday gate rate yet.", changes_it="Sunday gate-out data from ji.jivo.in after the first live Sunday."),
 dict(id="A12", assumption="₹ of goods made = litres made x each SKU's realise rate (Mark 3's realise table). The plan sheet is worth ₹75.2 crore at those rates, i.e. ₹2.5 crore a day over 30 days.", why="R16 needs a rupee value per litre; realise is the only per-SKU rate we hold.", changes_it="Gurvinder question 13 (₹200/kg average, 3,000 t)."),
 dict(id="A13", assumption="Yellow mustard 1 L (75 g bottle) fills on the 10 Head or 6 Head, not JP.", why="August ran it on the 6 Head (6-7 Aug) and 10 Head (26-27 Aug), never on JP. Daman 2026-09-06: 'go with where you think it should run'.", changes_it="Gurvinder question 3."),
 dict(id="A15", assumption="3 L on the 10 Head runs at the 10 Head's 5 L planning rate.", why="No app config and no August run for 3 L on the 10 Head; the 6 Head's 3 L record is the only 3 L data.", changes_it="A measured 10 Head 3 L run."),
 dict(id="A16", assumption="Three small packs (Kachi Ghani 500 ml, Sunflower 200 ml, Sesame 500 ml) have no bottle in their recipe; they are classed SMALL by litres and fill in the 1 L slot.", why="SAP BOM lists only the oil for FG0000448, FG0000451, FG0000452.", changes_it="A completed BOM in SAP."),
 dict(id="A17", assumption="'GT/MT sales' means every outside channel except e-commerce: the customer's SAP channel (OCRD.U_Main_Group) in GT, MT, ROI, CORPORATE, HORECA, CSD or REFERENCE. Excluded: E-COMMERCE, BRANCH, STAFF, CASH SALE, and the 9 Oil inter-company cards (correction C-0005) — on Oil's books the whole e-commerce channel is the JIVO MART transfer (CUSTA000606). The excluded totals are published beside the included ones.",
      why="R17/R18 say GT/MT excluding e-com; Gurvinder's words at 10:37 were 'GT/MT sales, apart from e-commerce'. ROI, corporate, HORECA and CSD are outside customers the plant must also make for.", changes_it="Gurvinder question 12, or Daman naming the channels."),
 dict(id="A18", assumption="Expected demand covers every SKU that sold in the last 3 months, not only the plan sheet's 84 rows: 61 sold SKUs are absent from the sheet (844,054 L in June-August, 27% of outside litres). They enter the plan as expected orders at their trailing average, ranked by sales, below PO-backed work.", why="A plan that ignores a quarter of what customers buy will be wrong on the lines those SKUs occupy.", changes_it="Gurvinder question 12; the plan sheet being extended."),
 dict(id="A14", assumption="40 g bottles never run on JP; 75 g and 26 g bottles never run on Clear Pack.", why="Not ruled, never observed in August; JP is the mustard line, Clear Pack refused sesame (75 g).", changes_it="A ruling or an observed run."),
]
# Written in the order they were settled; PUBLISHED in id order, because the site's
# /assumptions page is a reference table and A14 sitting after A18 reads as a defect
# in the rulebook itself. The MD renders these same lists, so sort them once, here.
SETTLED.sort(key=lambda r: r["id"])
ASSUMED.sort(key=lambda a: a["id"])

# --------------------------------------------------- choices the build made
# Where a ruling and an assumption both run out, the build still has to decide
# something. Every such decision is written here ONCE, shows on /assumptions and
# in the MD, and is the first place to look when the plan does something odd.
# Nothing here is a business fact — each is a mechanism chosen to satisfy a rule.
BUILD_CHOICES = [
 dict(id="B01", choice="A product may only move to a second- or third-choice line when EVERY better line for it has less than one line-clearance of free hours left that day — i.e. the better line could not start it anyway.",
      why="The rulebook says a SKU spills to a preference-2 line only when the preference-1 lines are full. 'Full' has to mean 'cannot start another run', because the planner fills a line down to a sliver of an hour; treating a leftover 20 minutes as free hours would strand work on the wrong machine.",
      changes_it="A ruling that a product may open on a second-choice line while its first choice still has time (for instance to keep two lines on the same oil)."),
 dict(id="B02", choice="One product change per line per session. Whatever the line was running yesterday ranks first inside its preference band; a second change is allowed only when the line would otherwise stand idle with more than one clearance of hours free, and every such lift is printed in the day's decisions.",
      why="R06: keep one product on a line all day. Ranking rather than forbidding keeps the value order intact inside the rule, and the printed lift keeps the exception visible instead of silent.",
      changes_it="Gurvinder's answer to question 7 (what a pack-size change really costs), or a ruling that a line may change twice."),
 dict(id="B03", choice="The night line is the line with the most order-backed litres still unmade after the day session, counting only products that line can fill; ties go to JP. With no order-backed litres left, the line with the most expected and plan-sheet litres; with nothing left at all, no night session. The reason is published every day.",
      why="R03 gives one line at night and calls the pick the plant's call; A07 fixes the rule and the JP tie. Publishing the runners-up and the reason is what lets Gurvinder overrule it.",
      changes_it="A daily pick from Gurvinder, or his answer to question 8."),
 dict(id="B04", choice="On Sunday nothing is made, but orders are still filled from stock and the trucks leave after the usual wait, exactly as on a weekday.",
      why="R04: Sunday is for dispatch, to relieve the godown. Mark 3 skipped dispatch on Sundays only because it sat inside the same block as production.",
      changes_it="A measured Sunday gate rate from ji.jivo.in that differs from a weekday's (A11)."),
 dict(id="B05", choice="Expected orders are shaped by week of month in five buckets — days 1-7, 8-14, 15-21, 22-28, 29 to month end — using a product's own three-month shape when it sold in all three months, otherwise the shape of all products together. Real OMS orders for the same product in the same days are taken off the top; e-com is never netted, it keeps its own POs.",
      why="R17: orders bunch at month end, and a flat spread would leave the plant short in the last week. A product that sold in only one month has too thin a shape of its own to trust. R18 keeps e-com on its POs.",
      changes_it="Gurvinder's answer to question 12 (how many months, per product or per oil)."),
 dict(id="B06", choice="A product that sells but is not on the plan sheet joins the plan only when SAP's recipe names its oil and its container can be classed. The rest are published as expected demand the plan cannot place, each with the reason.",
      why="A18. Without a recipe the planner cannot book the oil, the bottle or the carton, so scheduling it would quietly invent material it does not have. Publishing the rest keeps the gap visible instead of dropping it.",
      changes_it="A completed recipe in SAP, or the plan sheet being extended to cover them."),
 dict(id="B07", choice="For a product that sells but is not on the plan sheet, the rupees a litre are its own three-month billing average.",
      why="A12 uses the plan sheet's realise rate, and these products have none. Their own billing is the only rate that belongs to them; the default rate would flatter or punish them arbitrarily.",
      changes_it="The plan sheet being extended (it carries a realise rate per row)."),
 dict(id="B08", choice="Products that are only expected — no order behind them yet — are ranked by their trailing monthly litres, below everything with a real order and above the rest of the plan sheet.",
      why="R19: what nobody has ordered and nobody has been buying goes last. Trailing litres is the same measure R17 uses to expect the order in the first place.",
      changes_it="A ruling that names a different order of priority."),
 dict(id="B09", choice="Pendency of the open dispatch book = the litres still to go out divided by the average litres that left the gate on each of the last seven recorded days — for all three books, and for Oil on its own. When no day has a record yet it is published as blank with the reason, never as zero.",
      why="Gurvinder asked how many days of pendency the open book carries (R21). Days of work at the recent gate pace is the plain reading, and both halves come from ji.jivo.in.",
      changes_it="A ruling on the window (seven days, or the month), or a gate rate that stops being flat enough to average."),
 dict(id="B10", choice="Rupees of goods made = the goods receipts booked in the factory app, valued at each product's realise rate; a product outside the plan sheet is valued at its own billing rate, and only a product with neither gets the default rate. Each of the three shares is published.",
      why="R16 needs a rupee figure against the ₹2 crore floor. Goods receipts are the fuller count — the machines' own reports see about two-thirds of the plant. Splitting the valuation keeps a default-rate share visible instead of hidden inside one total.",
      changes_it="Gurvinder's answer to question 13 (₹200 a kilo over 3,000 tonnes)."),
 dict(id="B11", choice="A once-a-day input file older than eight days, or covering the wrong month, is treated as stale: the plan falls back to what it used before and says so on the page.",
      why="Both daily inputs are written by a cron job that can silently stop. A quietly stale file is worse than a named fallback, and eight days survives a long weekend plus a failed night without hiding a dead job.",
      changes_it="A ruling on how old is too old, or the jobs becoming monitored in their own right."),
 dict(id="B12", choice="Material is ordered against expected orders as well as against real ones.",
      why="R17 is the whole point of expecting the orders: the packaging has to be there before the order arrives. Buying only against real orders would leave every expected-only product permanently without a bottle.",
      changes_it="A ruling that material is bought against confirmed orders only."),
 dict(id="B13", choice="When a recipe uses more than one container per saleable piece, the line is planned in CONTAINERS, not in pieces: the slot and the bottle come from one container's litres (the piece divided by how many the recipe names), and the piece count is multiplied by the same number to get line time and material.",
      why="R15 says the recipe decides the pack, and the recipe of the four combo rows names two one-litre bottles per set. Reading the set as a two-litre pack put them on a machine no two-litre bottle needed, at half the bottle count and the wrong bottle family — so the mustard combo escaped both the mustard rule and the bottle rule at once.",
      changes_it="A ruling that a combo set is filled some other way, or a recipe that names its containers differently."),
 dict(id="B14", choice="A recipe child whose name only MENTIONS a container — a carton, a label, a cap, a tin strip, a sleeve — is not the container. The container is the first child left after those are set aside.",
      why="Twenty-two of the plan's recipes list something that mentions the container beside the real one, and one pouch row lists its carton first. Today the right item happens to come first almost everywhere, which is luck; the freeze will class products this sheet never saw.",
      changes_it="An item-type field on the BOM child (SAP has one) being read instead of the name."),
 dict(id="B15", choice="A product whose size nothing states — not the sheet, not its container's name — gets no slot at all and is published as unplaceable, never guessed into the smallest bottle.",
      why="The classifier used to read a missing size as zero litres and call it a small pack, which is a silent wrong machine. No plan row is in that state today; the freeze will meet ones that are.",
      changes_it="The product's size reaching the sheet or its recipe."),
 dict(id="B16", choice="A machine slot with no rating in the app and too few usable August runs to be a typical rate is published with NO planning speed, and nothing is scheduled on it until someone gives one. Two slots are in that state: Clear Pack 2 L (every one of its August two-litre runs was a combo set of one-litre bottles, so the line has no record of filling a two-litre bottle at all) and 6 Head 3 L (three runs, one of them a 71-minute clock error, one a 48-piece trial).",
      why="A speed measured on one pack is not evidence about another, and a plausible number carries further than a blank. Nothing is stranded either way: 2 L keeps the 10 Head and the 6 Head, both rated, and 3 L keeps the 10 Head and the Tin Head.",
      changes_it="Gurvinder's answer to question 1 (his own speed per machine), or a measured run."),
 dict(id="B17", choice="A recipe quantity is read as a COUNT of containers only when something confirms it: the container's own printed size times that quantity comes back to the piece, or — when the container prints no size — the child is counted in pieces. A container measured in kilograms, litres or metres carries an amount of that child, never a count.",
      why="The four combo rows name two 1-litre bottles per set and the arithmetic confirms it (2 x 1 L = the 2 L piece). Three pouch rows name their film in KGS. Read as a bare number, 15 kg of steel on a 200 L drum becomes fifteen drums, its litres divided by fifteen, and the row lands on a machine that fills nothing like it.",
      changes_it="An item-type or packaging field on the BOM child being read instead of the unit and the printed size."),
 dict(id="B18", choice="A logged run is discarded as a clock error when it beats 120% of its slot's rating — or, where the app has no rating for that slot, when its LITRES an hour beat 120% of the most litres an hour any rated slot on the same line can pour. A run under three hours never sets a median or a best.",
      why="The old guard needed a rating, so it was switched off in exactly the slots where nothing else could catch a mis-clocked segment. 6 Head 3 L was [11, 820, 4183] pieces an hour: 4,183 three-litre bottles is 12,540 L/hr on a line whose best rated slot pours 3,000, and the 71-minute segment that produced it set the median that became the planning speed — a three-litre pack filling faster in litres than the five-litre on the same heads.",
      changes_it="Real rated speeds for the unrated slots (Gurvinder question 1), or run segments that close when the run stops."),
 dict(id="B19", choice="A combo set and a plain bottle of the same size are separate evidence. Each line publishes a second speed table for the packs it has run as combos; a line with no combo record has no combo rate, and a SKU whose recipe holds more than one container cannot be scheduled there until someone gives one.",
      why="On Clear Pack the two clusters do not overlap at any point — plain 1 L at 1,942-2,927 bottles an hour, combo sets at 87-1,277. Pooling them published a 'typical' of 1,610 that describes neither, and planned the four combo SKUs at 2,927 bottles an hour, about 29 line-hours for work the line has never done in under 67.",
      changes_it="Gurvinder's answer to question 1, a combo run on another line, or a ruling that a set is bundled off the line."),
 dict(id="B20", choice="THE STORAGE CEILING IS A HARD CAP ON EVERY RUN. No run may be longer than the headroom left in the godown — the declared 827,000 L working ceiling minus what is physically in it, finished goods plus stock already billed but not yet trucked out. The headroom is worked out afresh at the start of every day and comes down litre for litre as the day's runs are made, so once it reaches zero the plant stops for the day whatever hours, material and orders are left. When the headroom is what stops a product, the day says so with a held-up row naming STORAGE as the binder, exactly as it does for a missing bottle.",
      why="Gurvinder ruled the godown limit (R09/R20) and Daman declared the figure, but neither said what the planner should DO when the plan reaches it, so this is the build's choice and not a ruling. Making it anyway would publish a month the warehouse cannot hold: goods stay in the godown until they are physically DISPATCHED, not when they are billed, so a plan that ignores the ceiling is a plan that overflows it. It is the single biggest hand on this month's sheet — bigger than hours, bigger than material — and it was applied silently in one line of the engine with its name in no rule, no assumption and no choice. A cap nobody can see is a cap nobody can argue with.",
      changes_it="A ruling that the plant may build ahead past the ceiling (a hired warehouse, or the 923,000 L peak used as the working limit instead), a faster gate that empties the godown sooner, or Gurvinder ruling that the planner should idle the cheapest machines rather than cap every run alike."),
]

# ----------------------------------------------------------------- the rest
RULEBOOK = dict(
  id="mark4-rulebook", version=f"mark4-{TODAY}", written=TODAY, owner="Gurvinderjeet Singh (planning); Daman (product)",
  sources=dict(meeting=MEETING, questions_for_gurvinder=QUESTIONS, august_runs="out/august-actuals-SCORING.csv (136 real runs, ji.jivo.in)",
               app_line_configs="reference/app-line-configs-2026-09-06.json (ji.jivo.in, read 2026-09-06)",
               bom="sim/sep-inputs.json bom + items (SAP BOM frozen 2026-08-31)", mark3="jolly/CLAUDE.md, reference/PLAN-AND-LINES.md"),
  settled=SETTLED, assumed=ASSUMED, build_choices=BUILD_CHOICES,
  shift=dict(hours_per_session=10, sessions_per_day_max=2, night_lines_max=1, sundays_off=True, working_days_basis="Mon-Sat", source="R02 R03 R04",
             supersedes="reference/PLAN-AND-LINES.md 'Shift length is a DECISION' (12 h / 22 h, Daman 2026-08-29)"),
  efficiency=dict(planning_factor=EFF, applies_to="rated speed (ji.jivo.in line-configs)", cap="best August hour when >= 3 runs", min_runs_for_cap=MIN_RUNS_FOR_CAP, source="R05 A01",
                  planning_is_post_efficiency=True, rules_efficiency_when_planning_speeds_are_used=1.0,
                  warning="Every `planning` speed here is POST-efficiency. sim/*-inputs.json `lines` holds PRE-efficiency RATED speeds and engine/august_sim.py multiplies them by rules.efficiency (0.5 in Mark 3). Whoever moves these speeds into `lines` sets rules.efficiency to 1.0 in the same commit, or the plant runs at half and every cross-check still passes.",
                  supersedes="rules.efficiency 0.5 flat (Mark 2/3) and the 50% derate on Clear Pack 5 L / Tin Head"),
  pack_class=dict(source="BOM container child (R15)", slots=SLOTS, families=FAMILIES,
                  implementation="engine/pack_class.py", used_by=pack_class_callers(), to_be_wired=[r for r in PACK_CLASS_PLANNED if r not in pack_class_callers()],
                  fills_rule="sku_pack.fills_per_piece is how many containers the line fills per saleable piece, and fills_basis says what confirmed it (B17). Above 1 the line time and the material are pieces x fills, and the SPEED comes from lines[..].speeds_multi[slot], never speeds[slot] (B19).",
                  container_check="container_litres is the size printed on the container item and container_ratio is litres_per_fill over it. They legitimately differ by a tenth on a tin sold by weight (15 KGS into a 15 LTR tin); a ratio outside 0.8-1.25 sets container_disagrees, and no plan row sets it today.",
                  engine_slots=ENGINE_SLOTS,
                  engine_slot_rule="The engine, gen and the freeze key `lines` by a DIFFERENT vocabulary, in which every tin is one 'TIN' bucket at one pieces-per-hour. Map with pack_class.engine_slot() before touching that table; never key a Mark 4 slot straight across.",
                  engine_slot_disagrees=ENGINE_SLOT_DISAGREES,
                  engine_slot_disagrees_note="Products the legacy sheet rule puts on a different machine than R15 does. Each one is a Mark 3 misplacement, not a data error."),
  sku_pack=sku_pack,
  lines=LINES, excluded_lines=EXCLUDED_LINES,
  preference_semantics="pref 1 lines are filled first; a SKU spills to a pref-2 line only when every pref-1 line has no free hours that day; pref 3 only when 1 and 2 are full. Within one pref, the engine's value ranking decides.",
  changeover=dict(clearance_min=51.3, flush_l_per_oil_change=400, one_product_per_line_per_session=True, source="R06 A08",
                  rule="Prefer continuing yesterday's product on a line. At most one product change per line per session unless the line would otherwise sit idle."),
  night=dict(rule="At most one line gets a second 10-hour session per day; the plan names it and says why.", pick="most PO-backed litres unmade after the day session; tie → JP", source="R03 A07"),
  demand=dict(real_orders=["OMS open book (GT/MT)", "ecom.jivo.in POs"], expected_orders="3-month GT/MT billing average per SKU, week-of-month shaped (A09, A17, A18)",
              baseline_file="live/state/demand_baseline.json (written daily by live/demand_baseline_sap.py — the one allowed SAP read; see reference/DEMAND-BASELINE-SOURCE.md)",
              channels_included=["GT", "MT", "ROI", "CORPORATE", "HORECA", "CSD", "REFERENCE"],
              excluded_channels=["E-COMMERCE (= the JIVO MART transfer on Oil's books)", "BRANCH", "STAFF", "CASH SALE", "9 inter-company cards (C-0005)"], months=3, target="the plan sheet (₹2.5 Cr/day)",
              priority=["PO-backed", "expected (ranked by trailing sales)", "plan-sheet remainder"], tagging="forecast rows keep channel=FORECAST, docnum FCST-*, customer '(forecast — not yet ordered)'", source="R17 R18 R19 R27"),
  money=dict(floor_inr_per_day=20_000_000, target_inr_per_day=25_000_000, basis="litres made x realise per SKU (A12)", source="R16"),
  dispatch=dict(headline="open dispatch book: pendency in days; billed today → on a truck when (median, p90)", remove="trucks that left today",
                measure="ji.jivo.in gate-core sales-dispatch: gate_out_date − sap_doc_date per DISPATCHED row, last 30 days; refreshed daily, never every 3 minutes", source="R21"),
  storage=dict(ceiling_l=827000, peak_l=923000, rooms=["BH-BT", "BH-PF"], standing="cheap-path PENDING+BOOKED pile x Oil share", source="R23; unchanged from Mark 3"),
  carton_change=dict(from_pcs=16, to_pcs=20, pack="1 L", known_new_code={"FG0000461": "FG0000142"}, rule="A10", source="R20"),
  drums=dict(scheduled=False, skus=[c for c, v in sku_pack.items() if v["slot"] == "DRUM"], display="filled by hand, not scheduled here", source="R14"),
  labour=dict(source="ji.jivo.in run labour_count / run-labour", crew_median_aug={"10 Head": 18, "6 Head": 18, "Clear Pack": 18, "JP Machine": 18, "Pouch Machine": 12, "Tin Head": 15}, note="cost-rates endpoint returned 404 on 2026-09-06; per-run labour lines exist"),
  site=dict(new_page="/assumptions — 'What Mark 4 takes as fact': every settled ruling with its source, every assumption with why and what changes it, the speed table (rated / August typical / August best / planning / basis), the eligibility matrix, data freshness, the open questions for Gurvinder with status. Generated from this file + honesty.assumed; no typed numbers.",
            overview=["per-line strip: running now, planned today, hours of 10 (20 if night), done vs plan", "₹ of goods made today vs ₹2.5 Cr target and ₹2 Cr floor; month to date", "dispatch book pendency (days) + billed→truck median/p90 replaces 'trucks left today'", "stuck list: material and no-order reasons only; drums shown as manual"],
            keep=["only day 1 observed", "FORECAST triple-tag", "phone mask", "HAPPENED days", "Mark 3 pages keep working"]),
  acceptance_checks=[
   "AC01 No run of a TIN item on any line except Tin Head, and 5 L / 3 L tins on the 6 Head.",
   "AC02 No 15L slot on Clear Pack, 10 Head or 6 Head. No 3L on Clear Pack. No POUCH outside Pouch Machine. No DRUM scheduled anywhere.",
   "AC03 The three drum SKUs appear in the plan output as manual/not-scheduled and never in a 'stuck: no machine' list.",
   "AC04 Every line ≤ 10 h on any day; at most ONE line per day up to 20 h; Sundays 0 production hours; the night line is named per day.",
   "AC05 lines.json publishes per line-slot: rated, aug_median, aug_best, planning, basis; planning equals the A01 rule.",
   "AC06 Pack class of every plan SKU equals the BOM container (R15): the 7 '15 LTR' rows + FG0000232 are TIN.",
   "AC07 Bottle-family eligibility holds in every run: no 75G/26G on Clear Pack; no 40G/75G on JP; JP 1 L runs are 26G/ROUND/SMALL or 52G.",
   "AC08 Forecast rows triple-tagged; demand baseline published with months, source, channel filter, exclusions; its totals reconcile to the source within 0.5%.",
   "AC09 overview.json carries ₹ made today, target, floor, per-line strip, dispatch pendency and lag median/p90 with basis; 'trucks left today' is not a headline.",
   "AC10 assumptions.json lists every R* and A* id from this rulebook and every open question; the site's /assumptions renders them; check:numbers and the phone-mask scan pass.",
   "AC11 gen_live.py cross-checks pass (all existing + new); `next build` passes; fixtures synced; every existing Mark 3 route still renders.",
   "AC12 The offline chain (freeze_live → august_sim → gen_live) runs on the committed fixtures with rc=0 and the plan shows the rulebook in effect (spot-check: Soyabean 15 L on Tin Head; Cold Press 3 L on 6 Head or 10 Head; Kachi Ghani 1 L on JP).",
  ],
)

# The writes and the summary happen only when this file is RUN. Imported — which is
# how engine/_pack_class_test.py exercises the speed rule on buckets the plant has
# not produced — it computes everything and touches nothing.

# ------------------------------------------------------------------- the MD
def md():
    L = []
    L.append(f"# Mark 4 rulebook — what the planner takes as fact\n")
    L.append(f"Generated {TODAY} by `reference/build_mark4_rulebook.py` from the 5 Sep meeting with Gurvinder veerji, Daman's clarifications of 6 Sep, the factory app's records and the SAP BOM. **Do not edit by hand** — edit the script. Machine copy: `reference/mark4-rulebook.json`. Open questions: `{QUESTIONS}`.\n")
    L.append("## Settled rulings\n\n| # | Rule | Source |\n|---|---|---|")
    for r in SETTLED: L.append(f"| {r['id']} | {r['rule']} | {r['source']} |")
    L.append("\n## Assumptions Mark 4 makes on top\n\n| # | Assumption | Why | What would change it |\n|---|---|---|---|")
    for a in ASSUMED: L.append(f"| {a['id']} | {a['assumption']} | {a['why']} | {a['changes_it']} |")
    L.append("\n## Choices this build made where the rulebook was silent\n")
    L.append("Not business facts — mechanisms the build had to pick to satisfy a ruling. Each one is the first place to look when the plan does something odd, and each can be replaced by a ruling.\n")
    L.append("| # | Choice | Why | What would change it |\n|---|---|---|---|")
    for b in BUILD_CHOICES: L.append(f"| {b['id']} | {b['choice']} | {b['why']} | {b['changes_it']} |")
    L.append("\n## Speeds the plan uses (containers per hour)\n")
    L.append(f"**Planning** already has the {int(EFF*100)}% and the August cap inside it. The engine's own `lines` table holds RATED speeds and derates them at run time — moving a planning speed into that table without turning that derate off runs the plant at half.\n")
    L.append("**Aug range** is the whole kept spread, min to max. A median sitting in the middle of a 380x spread is not a measurement, and the column is there so it cannot look like one.\n")
    L.append("| Line | Pack | App rated | Aug range | Aug typical (3 h+) | Aug best | Aug runs (3 h+) | **Planning** | Basis |\n|---|---|---:|---:|---:|---:|---:|---:|---|")
    def _speed_rows(table, tag=""):
        for ln, spec in LINES.items():
            for slot, sp in spec[table].items():
                n = lambda v: f"{round(v):,}" if v is not None else "—"
                rng = f"{sp['aug_min']:,}–{sp['aug_max']:,}" if sp["aug_runs"] else "—"
                L.append(f"| {ln} | {slot}{tag} | {n(sp['rated'])} | {rng} | "
                         f"{n(sp['aug_median_sustained'])} | {n(sp['aug_best'])} | "
                         f"{sp['aug_runs']} ({sp['aug_runs_sustained']}) | "
                         f"**{n(sp['planning'])}** | {sp['planning_basis']} |")
    _speed_rows("speeds")
    L.append("\n### The same lines when the piece is a COMBO SET (B19)\n")
    L.append("A set of two bottles is not a two-litre pack and it is not a plain one-litre run either. These blocks are the line's own record of filling combos, in bottles per hour; a line absent from this table has no combo rate, so a combo cannot be scheduled on it.\n")
    L.append("| Line | Pack | App rated | Aug range | Aug typical (3 h+) | Aug best | Aug runs (3 h+) | **Planning** | Basis |\n|---|---|---:|---:|---:|---:|---:|---:|---|")
    _speed_rows("speeds_multi", " combo")
    L.append("\n## Which pack and bottle goes on which line (1 = first choice, 2 = when 1 is full, 3 = last resort)\n\n| Line | Pack | Bottle family → preference | August litres | of which combo |\n|---|---|---|---:|---:|")
    for ln, spec in LINES.items():
        for slot, fams in spec["slots"].items():
            L.append(f"| {ln} | {slot} | " + ", ".join(f"{k} → {v}" for k, v in fams.items())
                     + f" | {spec['aug_litres_by_slot'].get(slot, 0):,} | {spec['aug_litres_multi_by_slot'].get(slot, 0):,} |")
    L.append("\nExcluded: " + "; ".join(f"**{k}** — {v}" for k, v in EXCLUDED_LINES.items()))
    L.append("\n## Products whose plan-sheet pack type disagrees with the recipe (recipe wins, R15)\n")
    for c, v in sku_pack.items():
        if v["sheet_disagrees"]: L.append(f"- {c} {v['sku']} — sheet says {v['sheet_pack_type']}, recipe uses {v['container_name']}")
    L.append("\n## Products Mark 4 moves to a different machine than Mark 3 does\n")
    L.append("The first two columns are the engine's own buckets, where every tin is one 'TIN'. The last two are what the recipe says the line actually fills. Every row here is a Mark 3 misplacement.\n")
    L.append("| Code | Product | Engine bucket, before | after | Mark 4 pack | Bottle | Fills per piece |\n|---|---|---|---|---|---|---:|")
    for c in ENGINE_SLOT_DISAGREES:
        v = sku_pack[c]
        L.append(f"| {c} | {v['sku']} | {v['sheet_slot']} | {v['engine_slot']} | {v['slot']} | {v['family']} | {v['fills_per_piece']} |")
    L.append("\n## Acceptance checks (Proof runs these)\n")
    for a in RULEBOOK["acceptance_checks"]: L.append(f"- {a}")
    return "\n".join(L) + "\n"



def write():
    out_json = ROOT / "reference/mark4-rulebook.json"
    out_json.write_text(json.dumps(RULEBOOK, indent=1, ensure_ascii=False), encoding="utf-8")
    (ROOT / "reference/MARK4-RULEBOOK.md").write_text(md(), encoding="utf-8")
    print("wrote", out_json.relative_to(ROOT), "and reference/MARK4-RULEBOOK.md")
    print(f"settled {len(SETTLED)} · assumed {len(ASSUMED)} · lines {len(LINES)} · plan SKUs mapped {len(sku_pack)} · sheet disagrees {sum(v['sheet_disagrees'] for v in sku_pack.values())}")
    for ln, spec in LINES.items():
        for table, tag in (("speeds", ""), ("speeds_multi", " COMBO")):
            for slot, sp in spec[table].items():
                print(f"  {ln:<14} {slot + tag:<12} rated {str(sp['rated']):>7} med {str(sp['aug_median']):>5} "
                      f"best {str(sp['aug_best']):>5} n={sp['aug_runs']:<3} → plan {sp['planning']}  [{sp['planning_basis']}]")
    fam = defaultdict(int)
    for v in sku_pack.values(): fam[(v['slot'], v['family'])] += 1
    print("  slot/family coverage:", dict(sorted(fam.items())))



if __name__ == "__main__":
    write()