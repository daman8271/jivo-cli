#!/usr/bin/env python3
"""Pre-check for a bulk-oil (tanker) GRPO before anything is written.

Answers the three questions that decide whether to key at all:
  1. Is this invoice / bilty ALREADY on a draft or a posted GRPO?  (all three books)
  2. Does the PO exist, is it open, and how much is left on it?
  3. What did the last GRPO against that vendor look like?  (the template to clone)

It also does the arithmetic, so the rate is never typed by hand.

    python3 precheck.py --invoice AABV/26-27/308 --po 220826145 \
        --bilty 8904 --gross-kg 42200 --short-kg 110 --taxable 6287800

Reads only. Requires the operator's env already sourced (SAPB1_*).
"""
import argparse, json, math, os, subprocess, sys
from decimal import Decimal, ROUND_HALF_UP

BOOKS = ["JIVO_OIL_HANADB", "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB"]
CLI = os.environ.get("SAPB1_CLI") or os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "sap-b1", "cli", "sapb1")


UNREACHABLE = {}


def q(entity, company, flt, select=None, orderby=None, top=None):
    cmd = [os.path.abspath(CLI), "query", entity, "--company", company,
           "--filter", flt, "--json"]
    if select:
        cmd += ["--select", select]
    if orderby:
        cmd += ["--orderby", orderby]
    if top:
        cmd += ["--top", str(top)]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        # C-0031: a login refused for THIS company is not "nothing found".
        UNREACHABLE.setdefault(company, out.stderr.strip().splitlines()[-1][:160]
                               if out.stderr.strip() else "query failed")
        return []
    try:
        return json.loads(out.stdout or "[]")
    except json.JSONDecodeError:
        return []


def esc(s):
    return str(s).replace("'", "''")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--invoice", required=True, help="vendor invoice no, exactly as printed")
    a.add_argument("--po", type=int, help="JIVO PO number printed on the PO")
    a.add_argument("--bilty", help="Bill of Lading / LR-RR no off the invoice")
    a.add_argument("--gross-kg", type=Decimal, help="quantity printed on the invoice, kg")
    a.add_argument("--short-kg", type=Decimal, default=Decimal(0),
                   help="ball-pen shortage on the invoice, kg")
    a.add_argument("--taxable", type=Decimal, help="taxable value printed on the invoice")
    args = a.parse_args()

    dup = False
    print("== 1. already keyed?  (drafts + posted, all three books) ==")
    for db in BOOKS:
        clauses = [f"NumAtCard eq '{esc(args.invoice)}'"]
        if args.bilty:
            clauses.append(f"U_BilltyNumber eq '{esc(args.bilty)}'")
        flt = "(" + " or ".join(clauses) + ")"
        sel = "DocEntry,DocNum,DocDate,NumAtCard,U_BilltyNumber,DocTotal,DocumentStatus"
        for label, rows in (
            ("DRAFT ", q("Drafts", db, f"DocObjectCode eq 'oPurchaseDeliveryNotes' and {flt}", sel)),
            ("POSTED", q("PurchaseDeliveryNotes", db, flt, sel)),
        ):
            for r in rows:
                dup = True
                print(f"  !! {label} {db[5:-7]:4} DocEntry {r['DocEntry']} DocNum {r['DocNum']} "
                      f"{r['DocDate'][:10]} {r['NumAtCard']} bilty {r.get('U_BilltyNumber')} "
                      f"Rs {r['DocTotal']:,.0f} {r['DocumentStatus']}")
    if dup:
        print("  STOP. It is already in. Do not key it again — say which document it is.")
    if UNREACHABLE:
        print("  the search was NOT complete — these books could not be read:")
        for db, why in UNREACHABLE.items():
            print(f"    - {db}: {why}")
        print("  C-0073: say exactly this to the operator. Do not call it 'not found'.")
    elif not dup:
        print("  none found in Oil, Mart or Beverages — safe to key")

    if args.po:
        print("\n== 2. the PO ==")
        for db in BOOKS:
            for p in q("PurchaseOrders", db, f"DocNum eq {args.po}"):
                l = p["DocumentLines"][0]
                print(f"  {db[5:-7]:4} DocEntry {p['DocEntry']} {p['CardCode']} {p['CardName']}")
                print(f"       {p['DocumentStatus']} branch {p['BPL_IDAssignedToInvoice']} "
                      f"series {p['Series']} total Rs {p['DocTotal']:,.0f}")
                print(f"       item {l['ItemCode']} {l['ItemDescription']} | {l['Quantity']} "
                      f"{l['UoMCode']} @ {l['Price']} | whs {l['WarehouseCode']} loc "
                      f"{l['LocationCode']} Dim1 {l['CostingCode']} tax {l['TaxCode']}")
                print(f"       STILL OPEN: {l['RemainingOpenQuantity']} {l['UoMCode']}")
                print("\n== 3. last GRPO on this vendor — the template to clone ==")
                for g in q("PurchaseDeliveryNotes", db,
                           f"CardCode eq '{p['CardCode']}'",
                           "DocEntry,DocNum,DocDate,TaxDate,NumAtCard,U_BilltyNumber,"
                           "U_BiltyDate,U_VehicleNoM,U_TransporterName,Comments,Series,"
                           "AttachmentEntry,DocTotal",
                           orderby="DocEntry desc", top=3):
                    print(f"  DocEntry {g['DocEntry']} {g['NumAtCard']} doc {g['DocDate'][:10]} "
                          f"tax {g['TaxDate'][:10]} bilty {g.get('U_BilltyNumber')} "
                          f"{g.get('U_VehicleNoM')} series {g['Series']} "
                          f"att {g.get('AttachmentEntry')}\n       {g.get('Comments')!r}")

    if args.gross_kg is not None and args.taxable is not None:
        net_kg = args.gross_kg - args.short_kg
        qty = net_kg / Decimal(1000)
        price = (args.taxable / qty).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        print("\n== 4. the numbers ==")
        print(f"  invoice qty      {args.gross_kg:,} kg")
        print(f"  shortage         {args.short_kg:,} kg   <- ball pen on the invoice")
        print(f"  GRPO Quantity    {qty} MTS   ({net_kg:,} kg — must equal the gate stamp)")
        print(f"  taxable (as printed, NOT reduced)  Rs {args.taxable:,}")
        print(f"  UnitPrice        {price}   = taxable / Quantity")
        print(f"  PackageQuantity  {math.ceil(qty)}   = ceil(Quantity)")
        print(f"  expected DocTotal Rs {args.taxable * Decimal('1.05'):,} (IGST 5%)"
              f"  — must equal the invoice's printed total")


if __name__ == "__main__":
    main()
