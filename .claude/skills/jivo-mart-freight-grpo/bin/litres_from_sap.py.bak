#!/usr/bin/env python3
"""Litres + Product Category per Mart AR invoice, computed from SAP.

Mart AR invoice PDFs are NOT reliably in any mailbox we can reach, so unlike Oil
(C-0060: read the printed Total) Mart litres are computed:

    litres = Σ (pack volume parsed from the item name × Quantity)

Quantity is in PIECES (C-0001) and the volume is printed in the item name.
Category comes from OITM.U_Sub_Group, which is what the invoice's Product
Category block prints.

⚠ VALIDATED ON ONE DOCUMENT ONLY (bilty NCR-3226, invoices 707260200 and
706260939 -> 600 L and 2,176 L, both matching posted GRPO 13733 exactly).
ALWAYS check the result against the transporter's weight column: bottled oil
lands about 0.90-1.05 kg/L. A miss there means the parse is wrong, not the paper.

Usage: litres_from_sap.py <invoice> [<invoice>...] [--company JIVO_MART_HANADB]
"""
import subprocess, re, sys, json, argparse, os, collections

ROOT = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True,
                      text=True).stdout.strip() or os.getcwd()
HANA = os.path.join(ROOT, 'hana-sql', 'hana-sql')
ENV = os.path.join(ROOT, 'connections', 'hana-office-bridge.env')

# the block's wording -> the Dim1 master's OcrCode (OOCR DimCode=1)
DIM1 = {'SUNFLOWER': 'SUNFLOWR', 'GROUNDNUT': 'GROUNDNT', 'RICE BRAN': 'RICEBRAN'}
NON_OIL = {'TIN', 'CAPS', 'CAP', 'CARTON', 'BOX', 'LABEL'}

# "5 LTR", "1L", "250 ML", and the "1 LTR +1 LTR COMBO" that is 2 L a piece
PACK = re.compile(r'(\d+(?:\.\d+)?)\s*(LTR|LITRE|LTRS|L|ML)\b')


def pack_litres(name):
    """Volume of ONE piece, in litres. Sums a '+' combo."""
    hits = PACK.findall(name.upper())
    if not hits:
        return None
    vals = [float(n) / (1000.0 if u == 'ML' else 1.0) for n, u in hits]
    # a combo names both halves ("1 LTR +1 LTR COMBO") -> one piece is the sum
    return sum(vals) if '+' in name else vals[0]


def rows(company, invoices):
    inlist = ','.join(str(int(i)) for i in invoices)
    q = (f'SELECT T0."DocNum",T1."Dscription",T1."Quantity",T2."U_Sub_Group" '
         f'FROM "{company}"."OINV" T0 '
         f'JOIN "{company}"."INV1" T1 ON T0."DocEntry"=T1."DocEntry" '
         f'LEFT JOIN "{company}"."OITM" T2 ON T1."ItemCode"=T2."ItemCode" '
         f'WHERE T0."DocNum" IN ({inlist})')
    out = subprocess.run([HANA, '-env', ENV, q], capture_output=True, text=True).stdout
    for ln in out.splitlines()[1:]:
        p = ln.split('\t')
        if len(p) >= 4:
            yield p[0], p[1], float(p[2]), (p[3] or '').strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('invoices', nargs='+')
    ap.add_argument('--company', default='JIVO_MART_HANADB')
    ap.add_argument('-o', '--out')
    a = ap.parse_args()

    per = collections.defaultdict(lambda: collections.defaultdict(float))
    unparsed = []
    for num, desc, qty, cat in rows(a.company, a.invoices):
        v = pack_litres(desc)
        if v is None:
            unparsed.append((num, desc))
            continue
        per[num][cat or '?'] += v * qty

    res = {}
    for num, cats in per.items():
        oil = {c: round(l, 2) for c, l in cats.items() if c not in NON_OIL}
        d1 = max(oil.items(), key=lambda kv: kv[1])[0] if oil else None
        res[num] = {'by_category': {c: round(l, 2) for c, l in cats.items()},
                    'total_litres': round(sum(cats.values()), 2),
                    'dim1': DIM1.get(d1, d1),
                    'packaging_only': not oil}
        print(f"{num}  {res[num]['total_litres']:>10,.2f} L  Dim1={res[num]['dim1']}"
              f"  {res[num]['by_category']}")
    for num, desc in unparsed:
        print(f"!! {num}: no pack size in {desc!r} — read that invoice by eye")
    if unparsed:
        print("Do NOT build from this until every line parses.")
    if a.out:
        json.dump(res, open(a.out, 'w'), indent=1)
    return 1 if unparsed else 0


if __name__ == '__main__':
    sys.exit(main())
