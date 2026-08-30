#!/usr/bin/env python3
"""
JIVO Oil — resolve the August plan into LITRES and PIECES.

Why this exists (2026-08-29). JIVO runs TWO tonne conventions on purpose (C-0050):
  SALE / PLANNING side   1 T = 1,000 L   (volume)   <- this sheet
  PURCHASE side          1 T = 1,000 kg  (weight)
Both are correct in their own half of the business. The sheet is NOT mislabelled --
76 of 76 testable rows satisfy TONS == TOTAL_PCS x PER_LTRS / 1000, exactly as the
sale-side convention says they should. The danger is only at the crossing: at
910 g/L one purchase-tonne is 1,098.9 L, so a sale-side figure sent to procurement
unconverted overstates the buy by 9.89%. Carry litres internally; convert once, at
the hand-off to purchasing.

Rulings this encodes (Daman / Gurvinder veerji, 2026-08-29):
  * FINAL (2), 4,156.4 sale-tonnes -> the plan of record. Other sheets are dead.
  * E-com (2,083.0) is IN scope.
  * 1 L of oil = 910 g.  => 1 real MT = 1,098.9 L  (matches SAP POR1.NumPerMsr)
  * The 200 LTR drums are 200 LITRES, and are filled BY HAND — no filling line,
    no bottle/cap/label BOM. TOTAL PCS on those rows is a formula artefact.
  * Pouch planning is taken from the pouch's own pack size.
  * "15 L" in the sheet is a BUCKET meaning "any tin over 12 L", not a fill. A tin
    SKU named by net weight (12/13/15 KGS) is filled to weight/910 litres; the 15 L
    is the container it goes into. Every tin runs at the SAME line speed regardless
    of size, so tin line-time is driven by total tin PIECES, not by size mix.

Litres per piece comes from the SKU NAME, which was right on all 9 rows where the
sheet's own columns contradicted each other. The columns are kept as cross-checks.

Read-only. Writes a CSV.
"""
import argparse, csv, re, sys

DENSITY_G_PER_L = 910.0
L_PER_MT = 1_000_000.0 / DENSITY_G_PER_L      # 1098.901...

def pack_litres(sku: str):
    """Litres in one saleable piece, parsed from the SKU name. (value, how)"""
    s = " " + str(sku).upper().replace(",", " ") + " "
    # COMBO / multi-pack: "1 LTR + 1 LTR COMBO" is 2 L in one saleable set.
    # Sum the sizes on either side of the '+' before any single-size rule runs.
    if "+" in s:
        parts = [p for p in s.split("+") if p.strip()]
        vals = []
        for part in parts:
            v, _ = _one_size(" " + part + " ")
            if v is not None: vals.append(v)
        if len(vals) >= 2:
            return sum(vals), f"combo {'+'.join(f'{v:g}' for v in vals)} L"
    return _one_size(s)

def _one_size(s: str):
    """First pack size in a string. Order matters: ml before kg before g before L."""
    # order matters: LTR before L, MLS/ML before M
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:MLS|ML)\b", s)
    if m: return float(m.group(1)) / 1000.0, "ml in name"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:KGS|KG)\b", s)
    if m: return float(m.group(1)) * 1000.0 / DENSITY_G_PER_L, f"{m.group(1)}kg @910g/L"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:GMS|GM|GRAM|G)\b", s)
    if m: return float(m.group(1)) / DENSITY_G_PER_L, f"{m.group(1)}g @910g/L"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:LTRS|LTR|LITRE|LITER|L)\b", s)
    if m: return float(m.group(1)), "ltr in name"
    return None, "unparsed"

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="out/plan-aug-FINAL2.csv")
    ap.add_argument("--csv",  default="out/plan-aug-resolved.csv")
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.plan)))
    out, unresolved = [], []

    for r in rows:
        t   = f(r["total_t"]) or 0.0
        lb, cp, pcs, pl = (f(r["ltrs_box"]), f(r["case_pack"]),
                           f(r["total_pcs"]), f(r["per_ltrs"]))
        litres = t * 1000.0                     # the column is kilolitres
        name_l, how = pack_litres(r["sku"])

        # cross-checks, kept for the flag column — never used as the value
        box_l = (lb / cp) if (lb and cp) else None
        pcs_l = (litres / pcs) if (litres and pcs) else None

        manual = "DRUM" in str(r["pack_type"]).upper() or "200 LTR" in str(r["sku"]).upper()
        lpc = name_l
        if manual: lpc, how = 200.0, "200 L drum (hand-filled)"

        flags = []
        if lpc is None: flags.append("NO_PACK_SIZE")
        else:
            if box_l is not None and abs(box_l - lpc) > 0.01: flags.append("BOX_DISAGREES")
            if pcs_l is not None and abs(pcs_l - lpc) > 0.01: flags.append("PCS_DISAGREES")
            if pl is not None and abs(pl - lpc) > 0.01:       flags.append("PERLTRS_DISAGREES")
        if manual: flags.append("HAND_FILLED")

        pieces = (litres / lpc) if (lpc and litres) else None
        if lpc is None and litres > 0: unresolved.append(r)

        out.append(dict(
            code=r["code"], sku=r["sku"], head=r["head"], category=r["category"],
            pack_type=r["pack_type"], plan_kl=t, litres=round(litres, 1),
            real_mt=round(litres * DENSITY_G_PER_L / 1_000_000.0, 3),
            litres_per_piece=round(lpc, 4) if lpc else "",
            lpc_source=how, pieces=round(pieces) if pieces else "",
            sheet_per_ltrs=pl if pl is not None else r["per_ltrs"],
            sheet_box_lpc=round(box_l, 4) if box_l else "",
            sheet_pcs_lpc=round(pcs_l, 4) if pcs_l else "",
            hand_filled="Y" if manual else "",
            flags="|".join(flags)))

    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

    tl = sum(x["litres"] for x in out)
    tm = sum(x["real_mt"] for x in out)
    print(f"wrote {a.csv} — {len(out)} SKUs")
    print(f"  plan            {sum(x['plan_kl'] for x in out):>14,.1f}  (sheet 'TONS')")
    print(f"  litres          {tl:>14,.0f} L")
    print(f"  sale-tonnes     {sum(x['plan_kl'] for x in out):>14,.1f} T    (1 T = 1,000 L)")
    print(f"  purchase-tonnes {tm:>14,.1f} T    (1 T = 1,000 kg @ {DENSITY_G_PER_L:.0f} g/L)")
    print(f"  order in SAP as {tl/L_PER_MT:>14,.1f} MTS  (POR1.NumPerMsr = {L_PER_MT:,.1f} L/MT)")
    res = [x for x in out if x["pieces"] != ""]
    print(f"  pieces resolved {len(res)}/{len(out)} SKUs, {sum(x['pieces'] for x in res):,.0f} pieces")
    if unresolved:
        print(f"\n  UNRESOLVED pack size on {len(unresolved)} rows with demand:")
        for r in unresolved: print(f"    {r['code']}  {r['sku']}  ({r['total_t']} kL)")

if __name__ == "__main__":
    main()
