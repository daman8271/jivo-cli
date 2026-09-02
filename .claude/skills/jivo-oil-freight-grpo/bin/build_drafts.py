#!/usr/bin/env python3
"""Build Oil freight-GRPO draft payloads from a transporter's bill + parsed invoices.

One draft per BILTY. One line per SALE INVOICE on that bilty. Freight split
pro-rata on litres, last line absorbing the rounding (proved exact against
ABHIMAN GRPOs 25645/25646).

Input: a bill spec JSON —
{
  "company": "JIVO_OIL_HANADB",
  "vendor":  "VENDA001676",
  "bill":    "DEL/260349",
  "series":  2477,                        # NNM1 series for the bilty MONTH
  "dim2":    "08-2026",                   # dispatch month, off the bilty date
  "salesperson": 115,                     # clone from that transporter's last GRPO
  "bilties": [
    {"bilty":"DEL/260716","date":"2026-08-03","dim5":"TE","freight":31480.00,
     "invoices":["626070718","626070712","626070721","626080101"]}
  ]
}
plus invoices.json from parse_invoices.py and a {invoice: CardCode} map.

Usage: build_drafts.py bill.json invoices.json customers.json [-o drafts.json]
"""
import json, sys, argparse

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
    drafts, skipped = [], []
    for b in bill['bilties']:
        invoices = []
        for i in b['invoices']:
            if i not in inv:
                raise SystemExit(f"invoice {i} not in invoices.json — parse its PDF first")
            if inv[i]['packaging_only']:        # C-0059
                skipped.append((b['bilty'], i))
                continue
            if not (inv[i]['ok_total'] and inv[i]['ok_pairing']):
                raise SystemExit(f"invoice {i} failed its parse self-check — read it by eye")
            invoices.append(i)
        if not invoices:
            skipped.append((b['bilty'], 'WHOLE BILTY — every invoice packaging-only'))
            continue

        litres = [inv[i]['total_printed'] for i in invoices]   # C-0060
        total  = sum(litres)
        lines, running = [], 0.0
        for k, (i, l) in enumerate(zip(invoices, litres)):
            if k == len(invoices) - 1:
                amt = round(b['freight'] - running, 2)         # last line absorbs rounding
            else:
                amt = round(b['freight'] * l / total, 2)
                running += amt
            lines.append({
                "ItemDescription": ITEM_DESC,
                "AccountCode": ACCOUNT,
                "LineTotal": amt,
                "TaxCode": bill.get('tax_code', TAX_CODE),
                "LocationCode": LOCATION,
                "CostingCode":  inv[i]['dim1'],                # C-0058
                "CostingCode2": bill['dim2'],
                "CostingCode3": DIM3,
                "CostingCode5": b['dim5'],
                "U_BilltyNumber": b['bilty'],
                "U_BiltyDate": b['date'],
                "U_ARNO": i,
                "U_UNE_LTS": l,
                "U_Sub_Account": sub_account(cust[i], bst_cards),
                "U_CardCode": cust[i],
                "U_Remarks": f"BILTY NO {b['bilty']}",
            })
        assert round(sum(x['LineTotal'] for x in lines), 2) == round(b['freight'], 2)
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
    return drafts, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bill'); ap.add_argument('invoices'); ap.add_argument('customers')
    ap.add_argument('-o', '--out', default='drafts.json')
    a = ap.parse_args()
    bill = json.load(open(a.bill)); inv = json.load(open(a.invoices))
    cust = json.load(open(a.customers))
    drafts, skipped = build(bill, inv, cust)

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
                  f" {x['LineTotal']:>10,.2f}  {x['U_CardCode']}{bst}")
    for b, i in skipped:
        print(f"\n  SKIPPED {b}: {i}  (packaging only — C-0059)")
    print(f"\n  {len(drafts)} draft(s)   TOTAL {grand:,.2f}  <- must equal the bill footer")
    json.dump(drafts, open(a.out, 'w'), indent=1)
    print(f"  -> {a.out}")


if __name__ == '__main__':
    main()
