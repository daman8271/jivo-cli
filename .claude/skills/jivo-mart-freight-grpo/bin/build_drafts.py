#!/usr/bin/env python3
"""Build JIVO MART freight-GRPO draft payloads from a transporter's bill.

One draft per BILTY (LR), one line per SALE INVOICE, the LR's FREIGHT + LABOUR split
pro-rata on litres in WHOLE RUPEES (Mart's own convention — posted GRPO 13733;
labour rides with freight, C-0062).

MART IS NOT OIL. The tax is ON the document (forward charge), Dim3 is SUPPLY-C,
Dim4 is set, and PDN1 has no U_BiltyDate column at all.

Input: bill spec JSON —
{
  "company": "JIVO_MART_HANADB",
  "vendor":  "VENDA001018",
  "bill":    "NCR-349",
  "series":  2116,               # NNM1 series for the BILTY month
  "salesperson": 36,
  "tax_code": "IGST@18",         # clone from that vendor's own Mart GRPO
  "bpl": 1, "location": 1, "dim4": "SC-WARH",  # from OUR bill-to address (C-0064)
  "bilties": [
    {"bilty":"NCR-3226","date":"2026-07-13","dim5":"WB",
     "freight":45091.00, "labour":0,          # BOTH required — labour 0 only if none
     "invoices":["707260200","706260939"]}
  ]
}
plus invoices.json from ../../jivo-oil-freight-grpo/bin/parse_invoices.py (run on EVERY
invoice's PDF — Mart prints the same litre table, headed "Liter") and a {invoice: CardCode} map.

Checked here, never typed (jivo-oil-freight-grpo/bin/freight_checks.py):
  Effective Month (C-0093)  each line = the month of ITS OWN sale invoice date.
  Litres (C-0095)           from the tax invoice only: its printed litre Total; an invoice
                            that prints no litre table is calculated, bottles x size.
  Dim1 (C-0058)             biggest category on the invoice's litre table (SAP groups if unread).
  Packaging only            an invoice with only cartons/caps gets no line.

Usage: build_drafts.py bill.json invoices.json customers.json [-o drafts.json]
"""
import json, argparse, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', 'jivo-oil-freight-grpo', 'bin'))
import freight_checks as fc

ITEM_DESC   = "EDIBLE OIL"
ACCOUNT     = "5670001"        # FREIGHT AND CARTAGE
DIM3        = "SUPPLY-C"       # Mart. Oil/Bev use Del Bkhp
SUB_ACCOUNT = "SALES"
REMARKS     = "Y"              # Mart keys a literal Y here, not the bilty text

# C-0063: JIVO-to-JIVO invoice -> BST. CardCodes are PER BOOK; this is MART's set.
# C-0064: branch + location + sub-budget are read off OUR bill-to address on the
# transporter's bill, never cloned from the last GRPO.
OUR_ADDRESS = {
    'DL': {'bpl': 1, 'location': 1, 'dim4': 'SC-WARH'},   # 07AAFCJ4102J1ZS Mayapuri
    'HR': {'bpl': 2, 'location': 2, 'dim4': 'SC-BHKR'},   # 06AAFCJ4102J1ZU Bhakarpur
}

BST_CARDS_MART = {
    'CUSTA000001', 'CUSTA000827', 'CUSTA000874', 'CUSTA000875', 'CUSTA000876',
    'CUSTA000877', 'CUSTA000878', 'CUSTA000926',
    'VENDA000001', 'VENDA000004', 'VENDA000932', 'VENDA000942', 'VENDA000953',
    'VENDA001023',
}


def build(bill, inv, cust):
    bst = set(bill.get('bst_cards', BST_CARDS_MART))
    if 'dim2' in bill:
        raise SystemExit("remove \"dim2\" from bill.json — Effective Month comes from each "
                         "line's own sale invoice date, never typed and never the bilty (C-0093)")
    # "billed_to": "DL" | "HR" fills bpl/location/dim4 from OUR address (C-0064)
    if bill.get('billed_to'):
        a = OUR_ADDRESS[bill['billed_to'].upper()]
        bill = {**a, **bill}
    for f in ('bpl', 'location', 'dim4'):
        if f not in bill:
            raise SystemExit(f"{f} not set — read OUR bill-to address off the bill (C-0064), "
                             f"or pass \"billed_to\": \"DL\"/\"HR\"")
    for b in bill['bilties']:
        b['invoices'] = fc.clean(b['invoices'])
        if isinstance(b.get('labour'), bool) or not isinstance(b.get('labour'), (int, float)):
            raise SystemExit(f"bilty {b['bilty']}: give \"labour\" (0 if the bill has none) — "
                             f"the GRPO amount is freight + labour (C-0062)")

    twice = fc.repeated(b['invoices'] for b in bill['bilties'])
    if twice:
        raise SystemExit("NOT BUILT — fix these first:\n  " + "\n  ".join(twice))
    cust = {str(k): v for k, v in cust.items()}
    company = bill['company']
    everyone = sorted({i for b in bill['bilties'] for i in b['invoices']})
    dates = fc.invoice_dates(company, everyone)
    calc = fc.calculate(company, everyone)
    packaging = {i for i in everyone if calc[i]['packaging_only']}
    needs = [i for i in everyone if i not in packaging]
    litres, problems, warnings = fc.pick_litres(needs, inv, calc)
    problems += fc.skipped_but_printed(packaging, inv)

    def dim1(i):                                                             # C-0058
        p = inv.get(i)
        if p and p.get('ok_total') and p.get('ok_pairing') and p.get('dim1_known', True) and p.get('dim1'):
            return p['dim1']
        return calc[i]['dim1']
    for i in needs:
        if not dim1(i):
            problems.append(f"invoice {i}: no variety (Dim1) from the PDF or SAP — read it by eye")
    if problems:
        raise SystemExit("NOT BUILT — fix these first:\n  " + "\n  ".join(problems))

    drafts, skipped = [], []
    for b in bill['bilties']:
        invs = [i for i in b['invoices'] if i not in packaging]
        skipped += [(b['bilty'], i) for i in b['invoices'] if i in packaging]
        if not invs:
            skipped.append((b['bilty'], 'WHOLE BILTY — packaging only'))
            continue
        amount = round(b['freight'] + b['labour'])       # C-0062; Mart keys whole rupees
        if abs(amount - (b['freight'] + b['labour'])) > 0.001:
            warnings.append(f"bilty {b['bilty']}: freight + labour {b['freight'] + b['labour']:,.2f} "
                            f"rounded to {amount:,} (Mart GRPOs are whole rupees)")
        l_each = [litres[i] for i in invs]
        total, lines, run = sum(l_each), [], 0
        if total <= 0:
            raise SystemExit(f"bilty {b['bilty']}: 0 litres across its invoices — cannot split")
        for k, (i, l) in enumerate(zip(invs, l_each)):
            amt = round(amount - run) if k == len(invs) - 1 else round(amount * l / total)
            run += amt
            lines.append({
                "ItemDescription": ITEM_DESC, "AccountCode": ACCOUNT,
                "LineTotal": float(amt), "TaxCode": bill['tax_code'],
                "LocationCode": bill.get('location', 2),
                "CostingCode": dim1(i), "CostingCode2": fc.month(dates[i]),  # C-0058, C-0093
                "CostingCode3": DIM3, "CostingCode4": bill['dim4'],
                "CostingCode5": b['dim5'], "WTLiable": "tYES",
                "U_BilltyNumber": b['bilty'], "U_ARNO": i,
                "U_UNE_LTS": l,                                                    # C-0095
                "U_Sub_Account": "BST" if cust[i] in bst else SUB_ACCOUNT,
                "U_CardCode": cust[i], "U_Remarks": REMARKS,
                "U_UNE_CUNT": "Y", "U_UNE_SCHI": "N",
            })
        assert round(sum(x['LineTotal'] for x in lines), 2) == round(amount, 2)
        drafts.append({
            "DocObjectCode": "oPurchaseDeliveryNotes", "DocType": "dDocument_Service",
            "CardCode": bill['vendor'],
            "DocDate": b['date'], "TaxDate": b['date'], "DocDueDate": b['date'],
            "NumAtCard": b['bilty'], "Comments": f"BILTY NO {b['bilty']}",
            "Series": bill['series'],
            "BPL_IDAssignedToInvoice": bill.get('bpl', 2),
            "SalesPersonCode": bill.get('salesperson', 36),
            "DocumentLines": lines,
        })
    return drafts, skipped, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bill'); ap.add_argument('invoices'); ap.add_argument('customers')
    ap.add_argument('-o', '--out', default='drafts.json')
    a = ap.parse_args()
    if os.path.exists(a.out):
        os.remove(a.out)          # a stopped run must never leave an old drafts file to send
    bill = json.load(open(a.bill))
    drafts, skipped, warnings = build(bill, json.load(open(a.invoices)), json.load(open(a.customers)))
    print(f"{bill['vendor']}  bill {bill['bill']}  {bill['company']}  "
          f"series {bill['series']}  tax {bill['tax_code']}")
    sub = 0
    for d in drafts:
        t = sum(x['LineTotal'] for x in d['DocumentLines']); sub += t
        print(f"\n  {d['NumAtCard']}  {d['DocDate']}  Dim5 {d['DocumentLines'][0]['CostingCode5']}"
              f"  {sum(x['U_UNE_LTS'] for x in d['DocumentLines']):,.0f} L  {t:,.2f}")
        for x in d['DocumentLines']:
            tag = '  <- BST' if x['U_Sub_Account'] == 'BST' else ''
            print(f"      inv {x['U_ARNO']}  {x['U_UNE_LTS']:>9,.0f} L  Dim1 {x['CostingCode']:<9}"
                  f" month {x['CostingCode2']}  {x['LineTotal']:>10,.2f}  {x['U_CardCode']}{tag}")
    for b, i in skipped:
        print(f"\n  SKIPPED {b}: {i}")
    for w in warnings:
        print(f"\n  NOTE {w}")
    rate = float(''.join(c for c in bill['tax_code'] if c.isdigit()) or 0)
    print(f"\n  {len(drafts)} draft(s)  SUBTOTAL {sub:,.2f}  + tax@{rate:.0f}% "
          f"{sub*rate/100:,.2f}  = {sub*(1+rate/100):,.2f}   <- must equal the bill's NET")
    json.dump(drafts, open(a.out, 'w'), indent=1)
    print(f"  -> {a.out}")


if __name__ == '__main__':
    main()
