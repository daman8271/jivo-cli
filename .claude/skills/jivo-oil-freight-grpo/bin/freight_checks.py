#!/usr/bin/env python3
"""Checks shared by the three freight-GRPO builders (Oil, Mart, Beverages).

Rules from Mahak (USER19 GRPO desk), confirmed by Daman 2026-09-17:

  EFFECTIVE MONTH (C-0093)  each line = the month of ITS OWN sale invoice date.
  LITRES (C-0095)           from the TAX INVOICE only: the litre Total printed on it (all three
                              books; page 2's Total if the table runs over). An invoice that
                              prints no litre table (CSD / institutional) is calculated.
  CALCULATION               bottles x bottle size. Quantity is in bottles (C-0001); the
                              "16 PCS" in an item name is the carton, NEVER a multiplier.
                              "1 LTR 16 PCS" x 2 = 2 L.
  NO LITRE PRODUCT          an invoice with only cartons / caps (nothing sold by the litre)
                              gets no GRPO line.

Imported by build_drafts.py (Oil, Mart) and build.py (Beverages). Reads SAP only.
"""
import collections, csv, os, re, subprocess

TOLERANCE_L = 0.5
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))

# ONLY these groups are sold by the litre. Everything else (packaging, cookware, tea, services)
# is 0 L; an invoice with none of these gets no GRPO line. A new liquid group not listed here
# counts 0 L, so the calculation disagrees with the printed total and the builder warns.
LIQUID = {'OLIVE', 'MUSTARD', 'CANOLA', 'GROUNDNUT', 'SOYABEAN', 'SUNFLOWER', 'COCONUT',
          'RICE BRAN', 'BLENDED', 'SESAME', 'COTTON SEED', 'GHEE', 'WATER', 'DRINKS', 'PAIN OIL',
          'PALMOLEIN', 'PALM OIL', 'VEGETABLE OIL'}
# the group's wording -> the Dim1 master's OcrCode (8 chars)
DIM1 = {'SUNFLOWER': 'SUNFLOWR', 'GROUNDNUT': 'GROUNDNT', 'RICE BRAN': 'RICEBRAN',
        'COTTON SEED': 'COTTONSD', 'PALMOLEIN': 'PALM OIL', 'VEGETABLE OIL': 'VEGOIL'}

UNIT = r'(LTRS|LTR|LITRES|LITRE|LT|MLS|ML|L)\b'
SIZE = re.compile(r'(\d+(?:\.\d+)?)\s*' + UNIT)
SHARED_UNIT = re.compile(r'(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)\s*' + UNIT)   # "5 + 1 LTR"


def _env():
    if os.environ.get('HANA_ENV'):
        return os.environ['HANA_ENV']
    for name in ('hana.env', 'hana-new.env', 'hana-office-bridge.env'):
        p = os.path.join(ROOT, 'connections', name)
        if os.path.exists(p):
            return p
    return None


def hana(sql):
    cmd = [os.path.join(ROOT, 'hana-sql', 'hana-sql')]
    if _env():
        cmd += ['-env', _env()]
    r = subprocess.run(cmd + [sql], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0 or r.stdout.startswith('QUERY ERROR'):
        raise SystemExit("SAP read failed:\n" + r.stdout + r.stderr)
    return list(csv.DictReader(r.stdout.splitlines(), delimiter='\t'))


def clean(nums):
    """Invoice numbers as digit strings; anything else stops the run."""
    out = [str(n).strip() for n in nums]
    bad = [n for n in out if not n.isdigit()]
    if bad:
        raise SystemExit(f"not an invoice number: {bad}")
    return out


def month(date):
    return date[5:7] + '-' + date[:4]


def repeated(invoice_lists):
    """Problems for any invoice that appears more than once on the bill."""
    seen = collections.Counter(i for lst in invoice_lists for i in lst)
    return [f"invoice {i} is on the bill {n} times — one line per invoice; check the bill"
            for i, n in seen.items() if n > 1]


def invoice_dates(company, nums):
    """{invoice: 'YYYY-MM-DD'} — each sale invoice's own date (C-0093)."""
    nums = clean(nums)
    rows = hana(f'SELECT "DocNum" AS N, TO_VARCHAR("DocDate",\'YYYY-MM-DD\') AS D '
                f'FROM "{company}"."OINV" WHERE "CANCELED"=\'N\' AND "DocNum" IN ({",".join(nums)})')
    got, twice = {}, set()
    for r in rows:
        if r['N'] in got:
            twice.add(r['N'])
        got[r['N']] = r['D']
    if twice:
        raise SystemExit(f"invoice number(s) {sorted(twice)} exist more than once in {company} — "
                         f"check which invoice the bill means")
    missing = [n for n in nums if n not in got]
    if missing:
        raise SystemExit(f"invoice(s) {missing} not found (or cancelled) in {company} — "
                         f"check the book (C-0061) before building")
    return got


def bottle_litres(name, sum_bundles):
    """Litres in ONE bottle, from the item name. None if the name gives no size.

    A "+" bundle is counted per book, measured against hand-keyed GRPOs Mar-Sep 2026:
      Mart  sum_bundles=True   both halves           (33 of 35 bundle invoices)
      Oil   sum_bundles=False  both only if COMBO,   (135 of 188)
                               else the first size — "COLD PRESS 5 LTR + POMACE OLIVE 1 LTR" = 5
    """
    u = SHARED_UNIT.sub(r'\1 \3 + \2 \3', name.upper())
    vals = [float(n) / (1000.0 if x in ('ML', 'MLS') else 1.0) for n, x in SIZE.findall(u)]
    if not vals:
        return None
    if '+' in u and (sum_bundles or 'COMBO' in u):
        return sum(vals)
    return vals[0]


def calculate(company, nums):
    """{invoice: {'litres': float|None, 'dim1': str|None, 'packaging_only': bool, 'why': str}}

    packaging_only = nothing on it is sold by the litre -> no GRPO line.
    litres is None when a litre line has no size in its name (e.g. a pouch in GMS, a tin in KG).
    dim1 is None (with why) when the biggest group is not a Dim1 code in this book.
    """
    nums = clean(nums)
    rows = hana(f'SELECT I."DocNum" AS N, R."Dscription" AS DSC, R."Quantity" AS QTY, '
                f'T."U_Sub_Group" AS G FROM "{company}"."OINV" I '
                f'JOIN "{company}"."INV1" R ON R."DocEntry"=I."DocEntry" '
                f'LEFT JOIN "{company}"."OITM" T ON T."ItemCode"=R."ItemCode" '
                f'WHERE I."CANCELED"=\'N\' AND I."DocNum" IN ({",".join(nums)})')
    codes = {r['C'] for r in hana(f'SELECT "OcrCode" AS C FROM "{company}"."OOCR" WHERE "DimCode"=1')}
    sum_bundles = company == 'JIVO_MART_HANADB'
    by = collections.defaultdict(list)
    for r in rows:
        by[r['N']].append(r)
    out = {}
    for n in nums:
        cats, unknown = collections.defaultdict(float), []
        for r in by.get(n, []):
            g = (r['G'] or '').strip().upper()
            if g not in LIQUID:
                continue
            size = bottle_litres(r['DSC'], sum_bundles)
            if size is None:
                unknown.append(r['DSC'])
                continue
            cats[g] += size * float(r['QTY'])
        top = max(cats.items(), key=lambda kv: kv[1])[0] if cats else None
        d1 = DIM1.get(top, top)
        why = ('no bottle size in: ' + '; '.join(unknown[:2])) if unknown else ''
        if d1 and d1 not in codes:
            why, d1 = (why + '; ' if why else '') + f"group {top} is not a Dim1 code in {company}", None
        out[n] = {
            'litres': None if unknown else round(sum(cats.values()), 2),
            'dim1': d1,
            'packaging_only': not cats and not unknown,
            'why': why,
        }
    return out


def pick_litres(needs, printed, calc):
    """Each invoice's litres, from its tax invoice (C-0095).

    needs   : invoice numbers that get a GRPO line
    printed : invoices.json from parse_invoices.py — {invoice: {...}}; every invoice must be there,
              because litres come from the tax invoice and nowhere else
    calc    : calculate() output

    Returns ({invoice: litres}, [problems], [warnings]). Any problem means: build nothing.
    """
    value, problems, warnings = {}, [], []
    for i in needs:
        p, c = printed.get(i), calc[i]['litres']
        if p is None:
            problems.append(f"invoice {i}: no tax invoice PDF read — get the invoice and run "
                            f"parse_invoices.py on it (litres come from the invoice only)")
        elif p.get('unreadable'):
            problems.append(f"invoice {i}: the invoice PDF cannot be read ({p.get('why')}) — open it; "
                            f"if its litre Total is clear, put it in invoices.json as total_printed "
                            f"with ok_total and ok_pairing true, then rebuild")
        elif p.get('no_litre_block'):
            if c is None:
                problems.append(f"invoice {i}: prints no litre table and cannot calculate "
                                f"({calc[i]['why']}) — read bottles x size off the invoice")
            else:
                value[i] = c
                warnings.append(f"invoice {i}: prints no litre table — litres calculated, {c:,.2f} L")
        elif (p.get('total_printed') is not None and p.get('ok_total') and p.get('ok_pairing')
              and p['total_printed'] == 0 and c):
            problems.append(f"invoice {i}: the invoice prints a litre Total of 0 but carries {c:,.2f} L "
                            f"of oil/water — open the PDF and check")
        elif p.get('total_printed') is not None and p.get('ok_total') and p.get('ok_pairing'):
            value[i] = p['total_printed']
            if c is not None and abs(c - value[i]) > TOLERANCE_L:
                warnings.append(f"invoice {i}: printed total {value[i]:,.2f} L, calculation "
                                f"{c:,.2f} L — used the printed total")
        elif p.get('total_printed') is not None and c is not None and abs(c - p['total_printed']) <= TOLERANCE_L:
            value[i] = p['total_printed']          # table mis-read, but its Total agrees with the bottles
        else:
            problems.append(f"invoice {i}: the litre table did not read cleanly (Total "
                            f"{p.get('total_printed')}, rows {p.get('row_sum')}, calculation {c}) — "
                            f"open the PDF, and if its Total is clear put it in invoices.json as "
                            f"total_printed with ok_total and ok_pairing true, then rebuild")
    return value, problems, warnings


def skipped_but_printed(skipped, printed):
    """Problems for invoices SAP calls 'nothing sold by the litre' whose PDF prints litres."""
    return [f"invoice {i}: SAP's item groups say no oil/water, but the invoice prints "
            f"{printed[i]['total_printed']:,.2f} L — its product group is missing from LIQUID "
            f"in freight_checks.py; do not skip it" for i in skipped
            if (printed.get(i) or {}).get('total_printed')]
