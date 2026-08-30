#!/usr/bin/env python3
"""
Pull the LIVE plan straight from EXIM — no Excel, no round-trip.

GET /planning/latest/ returns the current monthly production plan as structured rows:
per-SKU, carrying the SAP FG item code, AND split into weeks (w1..w4). That is the
dated demand a scheduler needs, and it removes the hand-maintained workbook entirely.

Verified 2026-08-29: month 2026-09-01, "PRODUCTION PLANING MONTH OF SEP 2026",
uploaded 2026-08-27 by aahar831@gmail.com, 186 rows, 185 distinct FG codes,
grand_total 4,323,300 L (commodity 1,077,000 + premium 813,300 + ecom 2,433,000).
total_planning is LITRES — proven on the 5 L and 15 L packs (230,000 / 5 = 46,000 jars).

The Mac's TLS to eximbe.jivo.in is flaky, so the call is routed through the VPS,
which reaches it reliably. Read-only: GET only.
"""
import csv, json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fetch():
    env = {}
    for line in open("/Users/damanpreetsingh/jivogpt/.env"):
        if line.startswith("EXIM_") and "=" in line:
            k, v = line.strip().split("=", 1); env[k] = v.strip('"').strip("'")
    tok = json.load(open(os.path.join(REPO, "exim", ".secrets", "token.json")))["access"]
    r = subprocess.run(["ssh", "vps",
        f"curl -sS -m 60 -H 'Authorization: Bearer {tok}' '{env['EXIM_API']}/planning/latest/'"],
        capture_output=True, text=True, timeout=150)
    if r.returncode: sys.exit(f"fetch failed: {r.stderr[:300]}")
    return json.loads(r.stdout)

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def pack_type(sku):
    s = str(sku).upper()
    if "DRUM" in s or "200 LTR" in s: return "DRUM"
    if "TIN" in s or "KGS" in s:      return "TIN"
    if "POUCH" in s:                  return "POUCH"
    if "JAR" in s:                    return "JAR"
    return "PET"

def main():
    d = fetch()
    print(f"{d['title']}   month {d['month']}   v{d['version']}")
    print(f"  uploaded {d['uploaded_at'][:10]} by {d['uploaded_by']}  from {d['source_file']}")
    print(f"  {d['row_count']} rows   commodity {f(d['commodity_total']):,.0f} + premium "
          f"{f(d['premium_total']):,.0f} + ecom {f(d['ecom_total']):,.0f} = {f(d['grand_total']):,.0f} L\n")

    out, weeks = [], []
    for r in d["rows"]:
        code = str(r.get("code") or "").strip()
        if not code.startswith("FG"): continue
        tot = f(r["total_planning"])
        if tot <= 0: continue
        out.append(dict(
            row=r["id"], code=code, brand=r.get("brand"), head=r.get("head"),
            category=r.get("category"), sub=r.get("sub_category"), sku=r.get("sku"),
            per_ltrs=r.get("per_ltrs"), pack_type=pack_type(r.get("sku")),
            ltrs_box=r.get("ltrs_per_box"), case_pack=r.get("case_pack"),
            total_pcs="",                      # EXIM stores litres, not pieces
            gt_mt_roi_t=(f(r["commodity_monthly"]) + f(r["premium_monthly"])) / 1000.0,
            ecom_t=f(r["ecom_planning"]) / 1000.0,
            total_t=tot / 1000.0))             # -> sale-tonnes, the shape plan_units expects
        for w in (1, 2, 3, 4):
            lw = f(r.get(f"commodity_w{w}")) + f(r.get(f"premium_w{w}"))
            if lw: weeks.append(dict(code=code, sku=r.get("sku"), week=w, litres=lw))

    with open("out/plan-sep-FINAL2.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    with open("out/plan-sep-weeks.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["code", "sku", "week", "litres"]); w.writeheader(); w.writerows(weeks)

    print(f"wrote out/plan-sep-FINAL2.csv  {len(out)} SKUs, {sum(x['total_t'] for x in out)*1000:,.0f} L")
    print(f"wrote out/plan-sep-weeks.csv   {len(weeks)} week-rows — THIS IS THE DATED DEMAND\n")
    byw = {}
    for x in weeks: byw[x["week"]] = byw.get(x["week"], 0) + x["litres"]
    print("  trade plan by week (ecom is monthly-only, no week split):")
    for k in sorted(byw): print(f"    week {k}   {byw[k]:>12,.0f} L")

if __name__ == "__main__":
    main()
