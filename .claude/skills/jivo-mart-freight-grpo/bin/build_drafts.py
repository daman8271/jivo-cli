#!/usr/bin/env python3
"""Build JIVO MART freight-GRPO draft payloads from a transporter's bill.

One draft per BILTY (LR), one line per SALE INVOICE, freight split pro-rata on
litres in WHOLE RUPEES (Mart's own convention — posted GRPO 13733).

MART IS NOT OIL. The tax is ON the document (forward charge), Dim3 is SUPPLY-C,
Dim4 is set, and PDN1 has no U_BiltyDate column at all.

Input: bill spec JSON —
{
  "company": "JIVO_MART_HANADB",
  "vendor":  "VENDA001018",
  "bill":    "NCR-349",
  "series":  2116,               # NNM1 series for the BILTY month
  "dim2":    "07-2026",
  "salesperson": 36,
  "tax_code": "IGST@18",         # clone from that vendor's own Mart GRPO
  "bpl": 1, "location": 1, "dim4": "SC-WARH",  # from OUR bill-to address (C-0064)
  "bilties": [
    {"bilty":"NCR-3226","date":"2026-07-13","dim5":"WB","freight":45091.00,
     "invoices":["707260200","706260939"]}
  ]
}
plus litres JSON from litres_from_sap.py and a {invoice: CardCode} map.

Usage: build_drafts.py bill.json litres.json customers.json [-o drafts.json]
"""
import json, argparse

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


def build(bill, lit, cust):
    bst = set(bill.get('bst_cards', BST_CARDS_MART))
    # "billed_to": "DL" | "HR" fills bpl/location/dim4 from OUR address (C-0064)
    if bill.get('billed_to'):
        a = OUR_ADDRESS[bill['billed_to'].upper()]
        bill = {**a, **bill}
    for f in ('bpl', 'location', 'dim4'):
        if f not in bill:
            raise SystemExit(f"{f} not set — read OUR bill-to address off the bill (C-0064), "
                             f"or pass \"billed_to\": \"DL\"/\"HR\"")
    drafts, skipped = [], []
    for b in bill['bilties']:
        invs = []
        for i in b['invoices']:
            if i not in lit:
                raise SystemExit(f"invoice {i} missing from litres.json")
            if lit[i]['packaging_only']:
                skipped.append((b['bilty'], i))
                continue
            invs.append(i)
        if not invs:
            skipped.append((b['bilty'], 'WHOLE BILTY — packaging only'))
            continue
        litres = [lit[i]['total_litres'] for i in invs]
        total, lines, run = sum(litres), [], 0
        for k, (i, l) in enumerate(zip(invs, litres)):
            amt = round(b['freight'] - run) if k == len(invs) - 1 else round(b['freight'] * l / total)
            run += amt
            lines.append({
                "ItemDescription": ITEM_DESC, "AccountCode": ACCOUNT,
                "LineTotal": float(amt), "TaxCode": bill['tax_code'],
                "LocationCode": bill.get('location', 2),
                "CostingCode": lit[i]['dim1'], "CostingCode2": bill['dim2'],
                "CostingCode3": DIM3, "CostingCode4": bill['dim4'],
                "CostingCode5": b['dim5'], "WTLiable": "tYES",
                "U_BilltyNumber": b['bilty'], "U_ARNO": i,
                "U_UNE_LTS": l,
                "U_Sub_Account": "BST" if cust[i] in bst else SUB_ACCOUNT,
                "U_CardCode": cust[i], "U_Remarks": REMARKS,
                "U_UNE_CUNT": "Y", "U_UNE_SCHI": "N",
            })
        assert round(sum(x['LineTotal'] for x in lines), 2) == round(b['freight'], 2)
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
    return drafts, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bill'); ap.add_argument('litres'); ap.add_argument('customers')
    ap.add_argument('-o', '--out', default='drafts.json')
    a = ap.parse_args()
    bill = json.load(open(a.bill))
    drafts, skipped = build(bill, json.load(open(a.litres)), json.load(open(a.customers)))
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
                  f" {x['LineTotal']:>10,.2f}  {x['U_CardCode']}{tag}")
    for b, i in skipped:
        print(f"\n  SKIPPED {b}: {i}")
    rate = float(''.join(c for c in bill['tax_code'] if c.isdigit()) or 0)
    print(f"\n  {len(drafts)} draft(s)  SUBTOTAL {sub:,.2f}  + tax@{rate:.0f}% "
          f"{sub*rate/100:,.2f}  = {sub*(1+rate/100):,.2f}   <- must equal the bill's NET")
    json.dump(drafts, open(a.out, 'w'), indent=1)
    print(f"  -> {a.out}")


if __name__ == '__main__':
    main()
