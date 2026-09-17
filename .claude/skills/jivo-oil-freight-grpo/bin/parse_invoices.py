#!/usr/bin/env python3
"""Read the Product Category block off JIVO AR invoice PDFs (Oil, Mart and Beverages layouts).

The block is the ONLY source for two fields on an Oil freight GRPO line:
  U_UNE_LTS  = the printed Total of the Litre column          (C-0095)
  Dim1       = the category with the biggest SUM of litres     (C-0058)

It sits beside the RTGS/NEFT bank block, so a plain text dump interleaves the
two columns and silently steals category names ("IFSC", "Bank" appear as
categories). We therefore read word coordinates and take only the words inside
the Category / Litre column bounds.

Usage:  parse_invoices.py <dir-of-pdfs> [-o invoices.json]
"""
import subprocess, re, glob, os, json, sys, argparse
from xml.etree import ElementTree as ET

WORD = '{http://www.w3.org/1999/xhtml}word'
NUM  = re.compile(r'^[\d,]+\.?\d*$')
# categories that are packaging, not oil — an invoice with ONLY these gets no
# GRPO line at all (C-0059)
NON_OIL = {'TIN', 'CAPS', 'CAP', 'CARTON', 'BOX', 'LABEL', 'PET', 'SHRINK'}
# the block's wording vs the Dim1 master's OcrCode (OOCR DimCode=1).
# The master truncates to 8 chars, so these MUST be mapped, not passed through.
DIM1 = {
    'SUNFLOWER': 'SUNFLOWR',
    'GROUNDNUT': 'GROUNDNT',
    'RICE BRAN': 'RICEBRAN',
}
# every Dim1 value we are willing to send. Anything else stops the run rather
# than reaching SAP as an invalid dimension.
KNOWN_DIM1 = {'OLIVE', 'CANOLA', 'MUSTARD', 'SOYABEAN', 'SUNFLOWR', 'GROUNDNT',
              'RICEBRAN', 'COCONUT', 'BLENDED', 'COFFEE', 'GHEE', 'HONEY',
              'SESAME', 'COTTONSD', 'WATER', 'DRINKS'}


def _words(pdf):
    """Words as (xMin, yMin, xMax, yMax, text, page)."""
    xml = subprocess.run(['pdftotext', '-bbox-layout', pdf, '-'],
                         capture_output=True, text=True).stdout
    out = []
    for n, page in enumerate(ET.fromstring(xml).iter('{http://www.w3.org/1999/xhtml}page')):
        out += [(float(w.get('xMin')), float(w.get('yMin')), float(w.get('xMax')),
                 float(w.get('yMax')), (w.text or '').strip(), n) for w in page.iter(WORD)]
    return out


def parse(pdf):
    ws = _words(pdf)
    header = None
    # Oil prints "Category | Litre | Gross Wt", Mart "CATEGORY | Liter | Gross We", and
    # Beverages both "Category | Litre | Gross Wt" and "Category | Gross Wt | Liter".
    for a in [w for w in ws if w[4].lower() == 'category']:
        row = [w for w in ws if abs(w[1] - a[1]) < 4]
        lit = [w for w in row if w[4].lower() in ('litre', 'liter', 'litres', 'liters')]
        gro = [w for w in row if w[4].lower().startswith('gross')]
        if lit and gro:
            header = (a, lit[0], gro[0])
            break
    if not header:
        return None
    cat, lit, gro = header
    # the table can run onto the next page (Mahak: take page 2's Total) — read the header's
    # page from the header down, then the next page, as one continuous strip
    ws = [w[:5] for w in ws if w[5] == cat[5]] + \
         [(w[0], w[1] + 10000, w[2], w[3] + 10000, w[4]) for w in ws if w[5] == cat[5] + 1]
    cat_lo, cat_hi = cat[0] - 6, min(lit[0], gro[0]) - 6      # Category column
    num_lo, num_hi = min(lit[0], gro[0]) - 10, max(lit[2], gro[2]) + 30
    ytop = cat[3]

    def in_litre_column(w):
        # numbers are right-aligned under their header: judge by the RIGHT edge, and give
        # each number to the nearer header — works in either column order
        return num_lo <= w[2] <= num_hi and abs(w[2] - lit[2]) <= abs(w[2] - gro[2])

    total_lbl = [w for w in ws if w[1] > ytop and cat_lo <= w[0] < cat_hi
                 and w[4].lower().startswith('total')]
    ybot = total_lbl[0][1] - 1 if total_lbl else float('inf')

    # a category label can be TWO words ("RICE BRAN"). Group the words in the
    # category column by row, then join — reading them as separate labels
    # mis-pairs every row below it.
    _rows = {}
    for w in ws:
        if ytop < w[1] < ybot and cat_lo <= w[0] < cat_hi and re.fullmatch(r'[A-Z][A-Z]+', w[4]):
            _rows.setdefault(round(w[1] / 4), []).append((w[0], w[1], w[4]))
    cats = sorted((min(y for _, y, _ in g), ' '.join(t for _, _, t in sorted(g)))
                  for g in _rows.values())
    lits = sorted((w[1], float(w[4].replace(',', ''))) for w in ws
                  if ytop < w[1] < ybot and in_litre_column(w) and NUM.match(w[4]))

    printed = None
    if total_lbl:
        vals = [float(w[4].replace(',', '')) for w in ws
                if abs(w[1] - total_lbl[0][1]) < 4 and in_litre_column(w)
                and NUM.match(w[4])]
        if vals:
            printed = vals[0]

    rows = list(zip([c for _, c in cats], [l for _, l in lits]))
    by_cat = {}
    for c, l in rows:
        by_cat[c] = round(by_cat.get(c, 0) + l, 2)

    oil = {c: l for c, l in by_cat.items() if c not in NON_OIL}
    dim1_raw = max(oil.items(), key=lambda kv: kv[1])[0] if oil else None
    dim1 = DIM1.get(dim1_raw, dim1_raw)

    return {
        'rows': rows,
        'by_category': by_cat,
        'oil_categories': oil,
        'packaging_only': not oil,           # C-0059: skip this invoice entirely
        'total_printed': printed,
        'row_sum': round(sum(l for _, l in rows), 2),
        'dim1': dim1,
        'dim1_known': dim1 is None or dim1 in KNOWN_DIM1,
        'dim1_litres': max(oil.values()) if oil else None,
        # the self-checks that catch a mis-parse before it reaches SAP
        'ok_total': printed is not None and printed == round(sum(l for _, l in rows), 2),
        'ok_pairing': len(cats) == len(lits) and len(cats) > 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir')
    ap.add_argument('-o', '--out', default='invoices.json')
    a = ap.parse_args()

    res, bad = {}, 0
    for f in sorted(glob.glob(os.path.join(a.dir, '*.pdf'))):
        text = subprocess.run(['pdftotext', '-layout', f, '-'], capture_output=True, text=True).stdout
        inside = re.search(r'Invoice (?:Number|No\.?)\s*:\s*([67]\d{8})', text)
        named = re.search(r'(?<!\d)([67]\d{8})(?!\d)', os.path.basename(f))
        if inside and named and inside.group(1) != named.group(1):
            print(f"!! {os.path.basename(f)}: the file name says {named.group(1)} but the invoice "
                  f"prints {inside.group(1)} — using the printed number")
        num = (inside or named).group(1) if (inside or named) else None
        if not num:
            print(f"?? no invoice number in: {os.path.basename(f)}")
            continue
        r = parse(f)
        if r is None:
            if len(text.strip()) < 50 or re.search(r'categor', text, re.I):
                # a scan with no text, or a litre table the reader cannot match: never guess
                why = ('no text in the PDF (a scan or photo)' if len(text.strip()) < 50
                       else 'it has a Category table the reader could not match')
                res[num] = {'unreadable': True, 'why': why, 'total_printed': None}
                print(f"!! {num}  cannot read the litre table: {why}")
                bad += 1
            else:
                # CSD / institutional invoices print no litre table at all: the builder calculates
                res[num] = {'no_litre_block': True, 'total_printed': None, 'packaging_only': False,
                            'ok_total': False, 'ok_pairing': False, 'dim1': None, 'dim1_known': True}
                print(f"-- {num}  no litre table printed -> litres will be calculated (bottles x size)")
            continue
        res[num] = r
        good = r['ok_total'] and r['ok_pairing'] and r['dim1_known']
        flag = 'OK ' if good else '!! '
        bad += 0 if good else 1
        if not r['dim1_known']:
            print(f"   !! Dim1 {r['dim1']!r} is not a known OOCR DimCode=1 code — check the master")
        skip = '  [PACKAGING ONLY -> no GRPO line]' if r['packaging_only'] else ''
        print(f"{flag}{num}  total={r['total_printed']} sum={r['row_sum']} "
              f"Dim1={r['dim1']} ({r['dim1_litres']} L){skip}")
        print(f"      {r['rows']}")

    json.dump(res, open(a.out, 'w'), indent=1)
    print(f"\n{len(res)} invoice(s) -> {a.out}   FAILED CHECKS: {bad}")
    if bad:
        print("!! rows: the printed total is still used if the calculation agrees; otherwise the builder stops and names the invoice (C-0095).")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
