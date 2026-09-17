#!/usr/bin/env python3
"""Build Beverages freight-GRPO drafts from a transporter's consolidated bill.

Input : a TSV of the bill, one row per bilty (see --help for columns).
Output: payloads/<bilty>.json ready for `sapb1 draft grpo`, plus a check report.

Everything except the bill itself is pulled live from SAP. Nothing is written to
SAP by this script — it only reads and writes local files.

Built 2026-08-27 from ARNAV bill ATS-402 (44 bilties, Rs 3,12,135 -> drafts 15671-15714).

Checked here, and nothing is built if any fails (Daman + Mahak 2026-09-17):
  Litres (C-0095)   from the tax invoice only: the printed litre Total read by
                    jivo-oil-freight-grpo/bin/parse_invoices.py (--invoices); calculated only
                    when the invoice prints no litre table.
  Labour (C-0062)   each bilty's labour + freight must equal its total; the GRPO carries the total.
  Month (C-0093)    each line = the month of its own sale invoice date.
"""
import argparse, collections, csv, json, os, re, subprocess, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', 'jivo-oil-freight-grpo', 'bin'))
import freight_checks as fc

# JIVO WELLNESS + JIVO MART cards IN THE BEVERAGES BOOK (verified 2026-08-31 from
# that book's OCRD). Never reuse another book's list — CUSTA000877 is JIVO MART-RJ
# in Mart but M/S FOOD MONDE in Oil.
BST_CARDS_BEV = {
    'CUSTA000001', 'CUSTA000002', 'CUSTA000003', 'CUSTA000004',
    'CUSTA000606', 'CUSTA000827',
    'VENDA000001', 'VENDA000002', 'VENDA000003', 'VENDA000004', 'VENDA000483',
}


BEV = "JIVO_BEVERAGES_HANADB"
DEFAULT_HANA = "hana-sql/hana-sql"

# only to cross-check the transporter's Destination column against the ship-to
# state — Dim5 is ALWAYS the ship-to state, never this column.
DEST_MAP = {"DELHI": "DL", "DL": "DL", "HR": "HR", "HARYANA": "HR",
            "UP": "UP", "UTTAR PRADESH": "UP", "UK": "UK", "UTTARAKHAND": "UK",
            "PB": "PB", "PUNJAB": "PB", "RJ": "RJ", "RAJASTHAN": "RJ"}

# ---------------------------------------------------------------- pack volumes

def litres(descr, qty):
    """Litres for one invoice line. Pack volume is printed in the item name.

    Verified against the emailed AR-invoice PDFs on 8 of 8 invoices, and against
    480 of 497 historical keyed U_UNE_LTS values. A GIFT PACK is 10 x 200 ML.
    """
    u = descr.upper()
    if "GIFT PACK 10 BOTTLES" in u:
        return 2.0 * qty
    m = re.search(r"(\d+(?:\.\d+)?)\s*ML", u)
    if m:
        return float(m.group(1)) / 1000.0 * qty
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:LTR|LITRE)\b", u)
    if m:
        return float(m.group(1)) * qty
    raise ValueError("no pack volume in item name: %r" % descr)


def expand(cell):
    """'626088047/054' -> ['626088047','626088054'] — the suffix replaces the
    last N digits of the base. Confirmed by Daman 2026-08-27."""
    parts = [p.strip() for p in str(cell).split("/")]
    base = parts[0]
    return [base] + [base[: len(base) - len(s)] + s for s in parts[1:]]


# ---------------------------------------------------------------------- SAP io

def hana(sql, exe):
    r = subprocess.run([exe, sql], capture_output=True, text=True)
    if r.returncode != 0 or r.stdout.startswith("QUERY ERROR"):
        sys.exit("HANA query failed:\n" + (r.stdout or "") + (r.stderr or ""))
    return list(csv.DictReader(r.stdout.splitlines(), delimiter="\t"))


def fetch_invoices(nums, exe):
    inlist = ",".join(nums)
    rows = hana(f'''
SELECT I."DocNum" AS DOCNUM, TO_VARCHAR(I."DocDate",'YYYY-MM-DD') AS INVDATE,
       I."CardCode" AS CARDCODE, I."CardName" AS CARDNAME, I."CANCELED" AS CANCELED,
       I."ShipToCode" AS SHIPTO, C."State" AS SHIPSTATE,
       L."Dscription" AS DESCR, L."Quantity" AS QTY, T."U_Sub_Group" AS CATEG
FROM "{BEV}"."OINV" I
JOIN "{BEV}"."INV1" L ON L."DocEntry"=I."DocEntry"
LEFT JOIN "{BEV}"."OITM" T ON T."ItemCode"=L."ItemCode"
LEFT JOIN "{BEV}"."CRD1" C ON C."CardCode"=I."CardCode" AND C."Address"=I."ShipToCode" AND C."AdresType"='S'
WHERE I."DocNum" IN ({inlist})''', exe)
    inv = {}
    for r in rows:
        e = inv.setdefault(r["DOCNUM"], dict(date=r["INVDATE"], card=r["CARDCODE"],
                                             name=r["CARDNAME"], cancelled=r["CANCELED"],
                                             shipstate=r["SHIPSTATE"], shipto=r["SHIPTO"],
                                             cat=collections.Counter()))
        g = (r["CATEG"] or "").strip().upper()
        if g not in fc.LIQUID and g != "GIFT PACK":      # cartons, caps, powder: 0 L (C-0095)
            continue
        try:
            e["cat"][r["CATEG"]] += litres(r["DESCR"], float(r["QTY"]))
        except ValueError:
            e.setdefault("unknown", []).append(r["DESCR"])
    return inv


def existing_grpos(bilties, exe):
    inlist = ",".join("'%s'" % b for b in bilties)
    posted = hana(f'''SELECT "NumAtCard" AS B,'posted' AS K,"DocEntry" AS E FROM "{BEV}"."OPDN"
                      WHERE "NumAtCard" IN ({inlist}) AND "CANCELED"='N' ''', exe)
    draft = hana(f'''SELECT "NumAtCard" AS B,'draft' AS K,"DocEntry" AS E FROM "{BEV}"."ODRF"
                     WHERE "ObjType"='20' AND "NumAtCard" IN ({inlist})''', exe)
    out = collections.defaultdict(list)
    for r in posted + draft:
        out[r["B"]].append((r["K"], r["E"]))
    return out


# ------------------------------------------------------------------ the build

def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""bill TSV columns (no header, tab separated):
  srl  bilty_date(YYYY-MM-DD)  bilty  invoice_cell  weight_kg  destination  to  labour  freight  total

Get the TSV from the transporter's own .xlsx in the mailbox, not from the scan:
  mail-cli/jmail search --sender <transporter> --since <date> --with-attachments
  mail-cli/jmail pull <uid> --out ./mail --types ''      # --types '' or the xlsx is skipped
The sheet name inside the workbook is the bill number (ATS:402 -> sheet '402').""")
    ap.add_argument("bill", help="TSV of the bill")
    ap.add_argument("--vendor", required=True, help="Bev vendor CardCode, e.g. VENDA000948")
    ap.add_argument("--series", type=int, required=True, help="Bev GRPO series for the month, e.g. 2481")
    ap.add_argument("--taxcode", default="RIGST@5",
                    help="from the TRANSPORTER's GSTIN state vs the 06 branch, never the "
                         "destination (C-0049). Delhi transporter -> RIGST@5")
    ap.add_argument("--invoices", required=True,
                    help="invoices.json from parse_invoices.py, run on every invoice's PDF (C-0095)")
    ap.add_argument("--out", default="payloads")
    ap.add_argument("--ignore-existing", action="store_true",
                    help="build payloads even for bilties already in SAP (use after a delete)")
    ap.add_argument("--hana", default=DEFAULT_HANA)
    a = ap.parse_args()

    rows = [l.rstrip("\n").split("\t") for l in open(a.bill) if l.strip()]
    for r in rows:                  # a stopped run must never leave an old payload to send
        old = os.path.join(a.out, r[2] + ".json")
        if os.path.exists(old):
            os.remove(old)
    allinv, bilties = [], []
    for r in rows:
        allinv += expand(r[3])
        bilties.append(r[2])
    inv = fetch_invoices(allinv, a.hana)
    seen = existing_grpos(bilties, a.hana)

    # C-0095: litres from the tax invoice (printed Total; calculated only when none is printed)
    allinv = fc.clean(allinv)
    stops = fc.repeated([allinv])
    stops += [f"invoice {i} not in Beverages OINV (wrong company? check the consignees)"
              for i in dict.fromkeys(allinv) if i not in inv]
    stops += [f"invoice {i} is CANCELLED" for i in dict.fromkeys(allinv)
              if i in inv and inv[i]["cancelled"] == "Y"]
    zero = {i for i in inv if not inv[i]["cat"] and not inv[i].get("unknown")}   # nothing sold by the litre
    ready = [i for i in dict.fromkeys(allinv) if i in inv and i not in zero]
    parsed = json.load(open(a.invoices))
    litres_of, bad, notes = fc.pick_litres(
        ready, parsed,
        {i: {'litres': None if inv[i].get("unknown") else round(sum(inv[i]["cat"].values()), 2),
             'why': 'no bottle size in: ' + '; '.join(inv[i].get("unknown", [])[:2])} for i in ready})
    stops += bad + fc.skipped_but_printed(zero, parsed)

    def dim1(i):          # the invoice's litre table, else SAP's dominant group
        p = parsed.get(i) or {}
        if p.get('ok_total') and p.get('ok_pairing') and p.get('dim1'):
            return p['dim1']
        return inv[i]["cat"].most_common(1)[0][0] if inv[i]["cat"] else None
    stops += [f"invoice {i}: no variety (Dim1) from the invoice or SAP — read it by eye"
              for i in ready if not dim1(i)]
    for r in rows:                                   # C-0062: labour + freight = total
        if abs(float(r[7] or 0) + float(r[8] or 0) - float(r[9])) > 0.5:
            stops.append(f"bilty {r[2]}: labour {r[7]} + freight {r[8]} is not the total {r[9]}")
    if stops:
        sys.exit("NOT BUILT — fix these first:\n  " + "\n  ".join(stops))

    problems, out = [], []
    for r in rows:
        _srl, bdate, bilty, cell, wt, dest, to, _lab, _fr, tot = r[:10]
        tot = float(tot)
        invs = [i for i in expand(cell) if i not in zero]          # no litre product -> no line
        if not invs:
            problems.append(f"bilty {bilty}: nothing sold by the litre on it — no GRPO")
            continue

        for i in invs:
            if i not in inv:
                problems.append(f"bilty {bilty}: invoice {i} not in Beverages OINV "
                                f"(wrong company? check the consignees)")
            elif inv[i]["cancelled"] == "Y":
                problems.append(f"bilty {bilty}: invoice {i} is CANCELLED")
        if any(i not in inv for i in invs):
            continue
        if bilty in seen and not a.ignore_existing:
            problems.append(f"bilty {bilty}: already in SAP as {seen[bilty]} — skipped")
            continue

        lts = [litres_of[i] for i in invs]                           # C-0095
        total_l = sum(lts)
        if total_l <= 0:
            problems.append(f"bilty {bilty}: zero litres")
            continue

        # freight splits litre-wise; the last line absorbs the rounding (C-0048)
        share = [round(tot * x / total_l) for x in lts[:-1]]
        share.append(round(tot - sum(share)))

        cards = {inv[i]["card"] for i in invs}
        if len(cards) > 1:
            problems.append(f"bilty {bilty}: invoices span {len(cards)} consignees {sorted(cards)}")

        # kg/L sanity — bottled water lands 1.00-1.15; outside that, re-check the mapping
        if wt:
            ratio = float(wt) / total_l
            if not 0.95 <= ratio <= 1.35:
                problems.append(f"bilty {bilty}: kg/L = {ratio:.2f} (expect ~1.0-1.15) — "
                                f"{wt} kg vs {total_l:,.0f} L, verify the invoice mapping")

        lines = []
        for i, (iv, l, s) in enumerate(zip(invs, lts, share)):
            e = inv[iv]
            dim5 = e["shipstate"]          # the SHIP-TO state (Daman 2026-08-27)
            if not dim5:
                problems.append(f"bilty {bilty}: invoice {iv} has no ship-to state — "
                                f"read it off the invoice ({e['shipto']})")
                dim5 = ""
            d = DEST_MAP.get(dest.strip().upper())
            if d and dim5 and d != dim5:
                problems.append(f"bilty {bilty}: transporter says '{dest}' ({d}) but ship-to state "
                                f"is {dim5} — Dim5 follows the SHIP-TO; keyed {dim5}")
            lines.append({
                "AccountCode": "5670001",
                "ItemDescription": "WATER",      # water AND drinks -> WATER (Daman 2026-08-27)
                "LineTotal": s,
                "TaxCode": a.taxcode,
                "LocationCode": 2,
                "SACEntry": 3,                   # 996812 freight; constant in Bev, unlike Oil
                "SalesPersonCode": 3,
                "CostingCode": dim1(iv),                        # Dim1 = dominant category
                "CostingCode2": fc.month(e["date"]),  # Dim2 = that line's INVOICE month (C-0093)
                "CostingCode3": "Del Bkhp",
                "CostingCode5": dim5,
                "WTLiable": "tNO",               # a GRPO never deducts TDS (C-0039)
                "U_BilltyNumber": bilty,
                "U_BiltyDate": bdate,
                "U_ARNO": iv,
                "U_CardCode": e["card"],
                # C-0063: JIVO-to-JIVO sale invoice -> BST, decided per line.
                # CardCodes are PER BOOK; this set is the Beverages book's.
                "U_Sub_Account": "BST" if e["card"] in BST_CARDS_BEV else "SALES",
                "U_Remarks": f"BILTY NO {bilty}",
                "U_UNE_LTS": round(l, 2),
                "U_UNE_CALI": "Y",
                "U_UNE_CUNT": "Y",
                "U_UNE_SCHI": "N",
            })
        out.append((bilty, {
            "CardCode": a.vendor, "DocType": "dDocument_Service", "Series": a.series,
            "NumAtCard": bilty, "DocDate": bdate, "TaxDate": bdate, "DocDueDate": bdate,
            "BPL_IDAssignedToInvoice": 2, "DocumentSubType": "bod_None", "DocCurrency": "INR",
            "Comments": f"BILTY NO {bilty}", "DocumentLines": lines}))

    os.makedirs(a.out, exist_ok=True)
    for bilty, doc in out:
        json.dump(doc, open(os.path.join(a.out, bilty + ".json"), "w"), indent=1)

    paper = sum(float(r[9]) for r in rows)
    built = sum(l["LineTotal"] for _, d in out for l in d["DocumentLines"])
    print(f"bill rows      : {len(rows)}")
    print(f"payloads built : {len(out)}  ({sum(len(d['DocumentLines']) for _, d in out)} lines) -> {a.out}/")
    print(f"paper total    : Rs {paper:,.2f}")
    print(f"payload total  : Rs {built:,.2f}  {'TIES' if abs(paper-built) < 0.01 else '*** DOES NOT TIE ***'}")
    problems += notes
    print(f"\nchecks: {'all clean' if not problems else str(len(problems)) + ' to look at'}")
    for p in problems:
        print("  ! " + p)
    return 1 if abs(paper - built) >= 0.01 else 0


if __name__ == "__main__":
    sys.exit(main())
