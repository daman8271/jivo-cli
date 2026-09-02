#!/usr/bin/env python3
"""
GAUTAM'S BUILD LIST — the daily what-to-run-on-what-machine sheet, September 2026.

Daman, 2026-08-31: "Gautam is responsible for what to run on what machine. Teach him:
'Gautam, run this on this machine.' Every day, and it changes as POs land."

Reads the VERIFIED simulated days (sim/days-sep/*.json — only day 1 is observed, every
later day is computed) and emits, per day, per machine, the runs IN SEQUENCE with the
oil, the SKU, litres, and the changeover called out between runs:
  - OIL CHANGE      = 400 L flush of the next oil (time only — the oil is reused)
                      + 51.3 min line clearance
  - LINE CLEARANCE  = 51.3 min (cold start, or a pack-size change on the same oil)
  - continuation    = 0 min (same oil, same pack size)
The changeover minutes are the sim's own charged minutes (run.flush_min), so the sheet
reconciles to the simulated line-hours exactly. The plan changes as POs land: each
day carries `news` (materials landed / SKUs unblocked / real POs entering the book).

Writes out/build-list-sep.json and out/build-list-sep.csv.
    SIM_INPUTS=sim/sep-inputs.json SIM_TAG=-sep python3 engine/build_list.py
"""
import csv, glob, json, os
from datetime import date

INPUTS = os.environ.get("SIM_INPUTS", "sim/sep-inputs.json")
TAG = os.environ.get("SIM_TAG", "-sep")
S = json.load(open(INPUTS))
items = S["items"]
CLEAR_MIN = S["rules"]["line_clearance_min"]      # 51.3
FLUSH_L = S["rules"]["flush_litres"]              # 400

def oil_name(code):
    return items.get(code, {}).get("name", code or "—")

days_json, csv_rows, sample_day1 = [], [], []
prev_oil, prev_slot = {}, {}                      # line state persists ACROSS days (as in the sim)
tot_runs = tot_oilchg = tot_clear = 0

for fp in sorted(glob.glob(f"sim/days{TAG}/day-*.json")):
    d = json.load(open(fp))
    entry = dict(date=d["date"], weekday=d["weekday"], working=d["working"],
                 made_litres=d["made_litres"], made_value=d["made_value"],
                 line_util=d["line_util"], machines=[],
                 news=dict(materials_landed=len(d["received"]),
                           unblocked=[u["name"] for u in d["unblocked"]],
                           real_pos_entering=sum(1 for n in d["new_orders"] if n["channel"] != "FORECAST"),
                           forecast_rows=sum(1 for n in d["new_orders"] if n["channel"] == "FORECAST")))
    if not d["working"]:
        entry["note"] = "Sunday — plant off"
        days_json.append(entry); continue

    by_line = {}
    for r in d["runs"]: by_line.setdefault(r["line"], []).append(r)
    for ln, rs in by_line.items():
        m = dict(machine=ln, hours_used=d["line_hours"].get(ln, 0), runs=[])
        for seq, r in enumerate(rs, 1):
            po = prev_oil.get(ln)
            chg = None
            if r["flush_min"] > 0:
                if po is not None and r["oil"] and r["oil"] != po:
                    fl = max(0, r["flush_min"] - round(CLEAR_MIN))
                    chg = dict(minutes=r["flush_min"], kind="OIL CHANGE",
                               note=f"flush {FLUSH_L} L {oil_name(r['oil'])[:34]} (~{fl} min, oil reused) "
                                    f"+ {CLEAR_MIN} min line clearance — {oil_name(po)[:30]} → {oil_name(r['oil'])[:30]}")
                    tot_oilchg += 1
                elif po is None:
                    chg = dict(minutes=r["flush_min"], kind="LINE CLEARANCE",
                               note=f"{CLEAR_MIN} min clearance (line start)")
                    tot_clear += 1
                else:
                    chg = dict(minutes=r["flush_min"], kind="LINE CLEARANCE",
                               note=f"{CLEAR_MIN} min clearance (pack-size change, same oil)")
                    tot_clear += 1
            m["runs"].append(dict(seq=seq, code=r["code"], sku=r["sku"],
                                  oil=r["oil"], oil_name=oil_name(r["oil"]),
                                  pieces=r["pieces"], litres=r["litres"], hours=r["hours"],
                                  changeover_before=chg, po_backed=r["po_backed"]))
            csv_rows.append(dict(date=d["date"], line=ln, seq=seq, code=r["code"], sku=r["sku"],
                                 oil_code=r["oil"] or "", oil_name=oil_name(r["oil"]),
                                 pieces=r["pieces"], litres=r["litres"], hours=r["hours"],
                                 changeover_min=r["flush_min"],
                                 changeover_kind=chg["kind"] if chg else "",
                                 changeover_note=chg["note"] if chg else "",
                                 po_backed=r["po_backed"]))
            prev_oil[ln] = r["oil"]; tot_runs += 1
        entry["machines"].append(m)
    days_json.append(entry)

# human-readable day 1
d1 = days_json[0]
sample_day1.append(f"GAUTAM — {d1['date']} ({d1['weekday']}) ka plan: {d1['made_litres']:,} L, lines {d1['line_util']}%")
for m in d1["machines"]:
    sample_day1.append(f"{m['machine']} ({m['hours_used']}h):")
    for r in m["runs"]:
        if r["changeover_before"]:
            c = r["changeover_before"]
            sample_day1.append(f"   ↻ {c['kind']} {c['minutes']} min — {c['note']}")
        sample_day1.append(f"   {r['seq']}. {r['sku']} — {r['oil_name'][:32]} — "
                           f"{r['pieces']:,} pcs = {r['litres']:,} L ({r['hours']}h)"
                           + ("  [PO-backed]" if r["po_backed"] else ""))

meta = dict(month=S["meta"]["month"], generated="2026-08-31",
            source=f"sim/days{TAG}/ — the verified forward simulation (only day 1 observed; "
                   "every later day computed; the plan changes as POs land, carried in `news`)",
            rules=dict(flush_litres=FLUSH_L, line_clearance_min=CLEAR_MIN,
                       note="an oil change costs TIME not material: 400 L of the next oil is "
                            "run through and reused, plus 51.3 min clearance; a pack-size "
                            "change on the same oil costs the 51.3 min clearance only"),
            recipient=dict(name="Gautam Chanana", whatsapp="+918607332900",
                           display="+91 86073 32900", title="Production incharge"),
            totals=dict(days=len(days_json), working_days=sum(1 for x in days_json if x["working"]),
                        runs=tot_runs, oil_changes=tot_oilchg, clearances_only=tot_clear,
                        litres=sum(x["made_litres"] for x in days_json)),
            sample_day1=sample_day1)

json.dump(dict(meta=meta, days=days_json), open(f"out/build-list{TAG}.json", "w"), indent=1)
with open(f"out/build-list{TAG}.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys())); w.writeheader(); w.writerows(csv_rows)

print(f"build list: {meta['totals']['days']} days ({meta['totals']['working_days']} working), "
      f"{tot_runs} runs, {tot_oilchg} oil changes (400 L flush + {CLEAR_MIN} min), "
      f"{tot_clear} clearance-only, {meta['totals']['litres']:,} L")
print(f"wrote out/build-list{TAG}.json and out/build-list{TAG}.csv\n")
print("\n".join(sample_day1))
