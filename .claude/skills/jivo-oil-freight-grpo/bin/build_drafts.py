#!/usr/bin/env python3
"""Build Oil freight-GRPO draft payloads from a transporter's bill + parsed invoices.

One draft per BILTY. One line per SALE INVOICE on that bilty. The bilty's
FREIGHT + LABOUR split pro-rata on litres, last line absorbing the rounding
(proved exact against ABHIMAN GRPOs 25645/25646; labour rides with freight, C-0062).

Input: a bill spec JSON —
{
  "company": "JIVO_OIL_HANADB",
  "vendor":  "VENDA001676",
  "bill":    "DEL/260349",
  "series":  2477,                        # NNM1 series for the bilty MONTH
  "salesperson": 115,                     # clone from that transporter's last GRPO
  "bilties": [
    {"bilty":"DEL/260716","date":"2026-08-03","dim5":"TE",
     "freight":31480.00, "labour":0,      # BOTH required — labour 0 only if the bill has none
     "invoices":["626070718","626070712","626070721","626080101"]}
  ]
}
plus invoices.json from parse_invoices.py (run on EVERY invoice's PDF) and a
{invoice: CardCode} map.

Checked here, never typed (freight_checks.py):
  Effective Month (C-0093)  each line = the month of ITS OWN sale invoice date.
  Litres (C-0095)           from the tax invoice only: its printed litre Total; an invoice
                            that prints no litre table (CSD) is calculated, bottles x size.
  Packaging only            an invoice with only cartons/caps gets no line.

Usage: build_drafts.py bill.json invoices.json customers.json [-o drafts.json]
"""
import json, sys, argparse, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import freight_checks as fc

# constants measured over 205/205 Oil PICK & SHIP + ABHIMAN service-GRPO lines
ITEM_DESC   = "EDIBLE OIL"
ACCOUNT     = "5670001"
# TAX CODE IS NOT A CONSTANT — it depends on the transporter's own state.
# Interstate (vendor GSTIN 07 Delhi -> JIVO Oil 06 Haryana): RIGST@5
# Intrastate (vendor GSTIN 06 Haryana -> 06):                GST05R
# Always clone it from that vendor's own last GRPO; bill.json overrides.
TAX_CODE    = "RIGST@5"
LOCATION    = 2              # C-0025
DIM3        = "Del Bkhp"     # Oil. Never FACT_COM (that is the factory-bill code)
SUB_ACCOUNT = "SALES"        # SAP refuses the document without it
# C-0063: a line whose sale invoice is billed to JIVO WELLNESS or JIVO MART is a
# JIVO-to-JIVO movement and takes BST, not SALES. Decided PER LINE off U_ARNO —
# one bilty can carry both. bill.json may override with "bst_cards".
# ⚠ CardCodes are PER BOOK — the same code is a different party in another
# company. CUSTA000877 is JIVO MART - RJ in Mart and M/S FOOD MONDE in Oil.
# Never share one set across books. Verified 2026-08-31 from each book's OCRD:
#   SELECT "CardCode","CardName" FROM "<db>"."OCRD"
#    WHERE UPPER("CardName") LIKE '%JIVO WELLNESS%' OR UPPER("CardName") LIKE '%JIVO MART%';
BST_CARDS_BY_COMPANY = {
    'JIVO_OIL_HANADB': {
        'CUSTA000001', 'CUSTA000002', 'CUSTA000003', 'CUSTA000004', 'CUSTA001099',
        'CUSTA000606', 'CUSTA000827', 'CUSTA001113',
        'VENDA000001', 'VENDA000002', 'VENDA000003', 'VENDA000004', 'VENDA000483',
    },
    'JIVO_BEVERAGES_HANADB': {
        'CUSTA000001', 'CUSTA000002', 'CUSTA000003', 'CUSTA000004',
        'CUSTA000606', 'CUSTA000827',
        'VENDA000001', 'VENDA000002', 'VENDA000003', 'VENDA000004', 'VENDA000483',
    },
    'JIVO_MART_HANADB': {
        'CUSTA000001', 'CUSTA000827', 'CUSTA000874', 'CUSTA000875', 'CUSTA000876',
        'CUSTA000877', 'CUSTA000878', 'CUSTA000926',
        'VENDA000001', 'VENDA000004', 'VENDA000932', 'VENDA000942', 'VENDA000953',
        'VENDA001023',
    },
}


def sub_account(card, bst_cards):
    return "BST" if card in bst_cards else SUB_ACCOUNT


def build(bill, inv, cust):
    bst_cards = set(bill.get('bst_cards')
                    or BST_CARDS_BY_COMPANY.get(bill['company'], ()))
    if not bst_cards:
        raise SystemExit(f"no BST card set for {bill['company']} — add one (C-0063)")
    if 'dim2' in bill:
        raise SystemExit("remove \"dim2\" from bill.json — Effective Month comes from each "
                         "line's own sale invoice date, never typed and never the bilty (C-0093)")
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
    packaging = {i for i in everyone if calc[i]['packaging_only']}          # C-0059
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
        invoices = [i for i in b['invoices'] if i not in packaging]
        skipped += [(b['bilty'], i) for i in b['invoices'] if i in packaging]
        if not invoices:
            skipped.append((b['bilty'], 'WHOLE BILTY — every invoice packaging-only'))
            continue

        amount = round(b['freight'] + b['labour'], 2)                      # C-0062
        l_each = [litres[i] for i in invoices]
        total  = sum(l_each)
        if total <= 0:
            raise SystemExit(f"bilty {b['bilty']}: 0 litres across its invoices — cannot split")
        lines, running = [], 0.0
        for k, (i, l) in enumerate(zip(invoices, l_each)):
            if k == len(invoices) - 1:
                amt = round(amount - running, 2)                           # last line absorbs rounding
            else:
                amt = round(amount * l / total, 2)
                running += amt
            lines.append({
                "ItemDescription": ITEM_DESC,
                "AccountCode": ACCOUNT,
                "LineTotal": amt,
                "TaxCode": bill.get('tax_code', TAX_CODE),
                "LocationCode": LOCATION,
                "CostingCode":  dim1(i),                       # C-0058
                "CostingCode2": fc.month(dates[i]),            # C-0093
                "CostingCode3": DIM3,
                "CostingCode5": b['dim5'],
                "U_BilltyNumber": b['bilty'],
                "U_BiltyDate": b['date'],
                "U_ARNO": i,
                "U_UNE_LTS": l,                                # C-0095
                "U_Sub_Account": sub_account(cust[i], bst_cards),
                "U_CardCode": cust[i],
                "U_Remarks": f"BILTY NO {b['bilty']}",
            })
        assert round(sum(x['LineTotal'] for x in lines), 2) == amount
        drafts.append({
            "DocObjectCode": "oPurchaseDeliveryNotes",
            "DocType": "dDocument_Service",
            "CardCode": bill['vendor'],
            "DocDate": b['date'], "TaxDate": b['date'], "DocDueDate": b['date'],
            "NumAtCard": b['bilty'],
            "Comments": f"BILTY NO {b['bilty']}",
            "Series": bill['series'],
            "BPL_IDAssignedToInvoice": 2,
            "SalesPersonCode": bill.get('salesperson', 115),
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
    bill = json.load(open(a.bill)); inv = json.load(open(a.invoices))
    cust = json.load(open(a.customers))
    drafts, skipped, warnings = build(bill, inv, cust)

    print(f"{bill['vendor']}  bill {bill['bill']}  company {bill['company']}  "
          f"series {bill['series']}  tax {bill.get('tax_code', TAX_CODE)}")
    grand = 0
    for d in drafts:
        lt = sum(x['U_UNE_LTS'] for x in d['DocumentLines'])
        tot = round(sum(x['LineTotal'] for x in d['DocumentLines']), 2)
        grand += tot
        print(f"\n  {d['NumAtCard']}  {d['DocDate']}  Dim5 {d['DocumentLines'][0]['CostingCode5']}"
              f"  {lt:,.0f} L  {tot:,.2f}")
        for x in d['DocumentLines']:
            bst = '  <- BST (JIVO-to-JIVO)' if x['U_Sub_Account'] == 'BST' else ''
            print(f"      inv {x['U_ARNO']}  {x['U_UNE_LTS']:>8,.0f} L  Dim1 {x['CostingCode']:<9}"
                  f" month {x['CostingCode2']}  {x['LineTotal']:>10,.2f}  {x['U_CardCode']}{bst}")
    for b, i in skipped:
        print(f"\n  SKIPPED {b}: {i}  (packaging only — C-0059)")
    for w in warnings:
        print(f"\n  NOTE {w}")
    print(f"\n  {len(drafts)} draft(s)   TOTAL {grand:,.2f}  <- must equal the bill footer (freight + labour)")
    json.dump(drafts, open(a.out, 'w'), indent=1)
    print(f"  -> {a.out}")


if __name__ == '__main__':
    main()
