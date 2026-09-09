"""Pure, source-only dispatch normalization. Litres are recorded fields, not pack guesses."""
import datetime as dt
import math
import re

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
COMPANIES = ('JIVO_OIL', 'JIVO_MART', 'JIVO_BEVERAGES')
STORAGE = {'BH-BT', 'BH-PF'}

def number(value):
    if value is None or isinstance(value, bool): return None
    try:
        n = float(value)
        return n if math.isfinite(n) and n >= 0 else None
    except (ValueError, TypeError): return None

def instant(value):
    if not isinstance(value, str): return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed if parsed.tzinfo else None
    except ValueError: return None

def label(value):
    if not isinstance(value, str): return None
    return re.sub(r'https?://\S+|[\w.+-]+@[\w.-]+\.\w+|\+?\d[\d ()-]{8,}\d', '[redacted]', value)[:180]

def identifier(value):
    return str(value) if isinstance(value, (int, str)) and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', str(value)) else None

def read_all(client):
    rows, seen, count, pages = [], set(), None, None
    page = 1
    while pages is None or page <= pages:
        data = client.get('/gate-core/sales-dispatch/', {'all_companies': 1, 'page': page, 'page_size': 100})
        if not isinstance(data, dict) or not isinstance(data.get('results'), list): raise ValueError('Dispatch list shape')
        if not all(isinstance(data.get(k), int) and not isinstance(data[k], bool) for k in ('count', 'num_pages', 'page')): raise ValueError('Dispatch pagination shape')
        if count is None: count, pages = data['count'], data['num_pages']
        if count < 0 or not 1 <= pages <= 100 or (count, pages, page) != (data['count'], data['num_pages'], data['page']): raise ValueError('Dispatch pagination changed')
        for row in data['results']:
            key = identifier(row.get('id')) if isinstance(row, dict) else None
            if key is None or key in seen: raise ValueError('Dispatch duplicate or missing identity')
            seen.add(key); rows.append(row)
        page += 1
    if len(rows) != count: raise ValueError('Dispatch pagination incomplete')
    return rows, pages

def eligible(row, start, end):
    if row.get('status') != 'DISPATCHED': return False
    date = row.get('gate_out_date')
    departure = instant(row.get('dispatched_at'))
    if not date or not departure or str(departure.astimezone(IST).date()) != date: raise ValueError('Dispatch departure date unverified')
    return start <= date <= end

def operational_company(company, warehouse):
    if company == 'JIVO_BEVERAGES': return 'BEVERAGES', 'source company'
    if warehouse in ('GP-FG', 'GP-FGM'): return 'MART', 'owner warehouse ruling'
    if warehouse in STORAGE:
        return ('WELLNESS', 'owner warehouse ruling') if company == 'JIVO_OIL' else ('UNKNOWN', 'warehouse and source company conflict')
    if company in ('JIVO_OIL', 'JIVO_MART'):
        return ('WELLNESS' if company == 'JIVO_OIL' else 'MART'), 'source company; no separate warehouse ruling'
    return 'UNKNOWN', 'unclassified source company'

def normalize_entry(row, detail):
    for field in ('id', 'company_code', 'status', 'gate_out_date', 'dispatched_at', 'updated_at'):
        if detail.get(field) != row.get(field): raise ValueError('Dispatch list and detail conflict')
    company = row.get('company_code')
    if company not in COMPANIES: raise ValueError('Dispatch company unknown')
    if number(row.get('total_litres')) != number(detail.get('total_litres')): raise ValueError('Dispatch header quantity changed')
    documents = detail.get('documents')
    if not isinstance(documents, list) or len(documents) != detail.get('document_count'): raise ValueError('Dispatch documents incomplete')
    items, warehouses, issues, seen = [], {}, [], set()
    total = number(row.get('total_litres'))
    if total is None: issues.append('Recorded load litres missing')
    for doc in documents:
        if not isinstance(doc, dict) or not isinstance(doc.get('items'), list): raise ValueError('Dispatch items incomplete')
        for item in doc['items']:
            key = identifier(item.get('id'))
            if key is None or key in seen: raise ValueError('Dispatch item identity duplicate or missing')
            seen.add(key)
            litres, warehouse = number(item.get('total_litres')), identifier(item.get('warehouse_code'))
            if litres is None: issues.append('An item has no recorded litres; no unit conversion guessed')
            if warehouse is None: issues.append('An item has no recorded warehouse')
            if litres is not None and warehouse: warehouses[warehouse] = warehouses.get(warehouse, 0) + litres
            operational, basis = operational_company(company, warehouse)
            items.append({'operationalCompany': operational, 'classificationBasis': basis, 'code': identifier(item.get('item_code')), 'name': label(item.get('item_name')), 'warehouse': warehouse,
                          'quantity': number(item.get('quantity')), 'uom': identifier(item.get('uom')), 'litres': litres})
    if total is not None and (not items or all(i['litres'] is not None for i in items)) and abs(sum(i['litres'] for i in items) - total) > 0.01:
        issues.append('Item litres do not match recorded gate load')
    complete = not issues
    date = row['gate_out_date']
    arrival = identifier(row.get('arrival'))
    gate_id = identifier(row['id'])
    return {'id': gate_id, 'reference': identifier(row.get('entry_no')) or 'Gate-'+gate_id,
            'tripId': date+(':arrival-'+arrival if arrival else ':gate-'+gate_id),
            'identityBasis': 'factory arrival identity' if arrival else 'gate entry only; physical trip unverified',
            'company': company, 'date': date, 'departedAt': row['dispatched_at'],
            'litres': total, 'planningTonnes': total / 1000 if total is not None else None,
            'documentCount': len(documents), 'warehouseLitres': [{'warehouse': key, 'litres': round(value, 6)} for key, value in sorted(warehouses.items())],
            'wellnessStorageLitres': round(sum(v for k,v in warehouses.items() if k in STORAGE), 6) if complete and company == 'JIVO_OIL' else 0 if company != 'JIVO_OIL' else None,
            'operationalWellnessLitres': round(sum(i['litres'] for i in items if i['operationalCompany'] == 'WELLNESS'), 6) if complete else None,
            'operationalMartLitres': round(sum(i['litres'] for i in items if i['operationalCompany'] == 'MART'), 6) if complete else None,
            'operationalUnclassifiedLitres': round(sum(i['litres'] for i in items if i['operationalCompany'] == 'UNKNOWN'), 6) if complete else None,
            'classificationConflict': any(i['operationalCompany'] == 'MART' and company == 'JIVO_OIL' or i['operationalCompany'] == 'UNKNOWN' for i in items),
            'items': items, 'detailComplete': complete, 'issues': sorted(set(issues))}

def total(rows, company=None, key='litres'):
    values = [row[key] for row in rows if company is None or row['company'] == company]
    return round(sum(values), 6) if all(v is not None for v in values) else None

def totals(rows):
    chosen = [r for r in rows if r['company'] in ('JIVO_OIL', 'JIVO_MART')]
    return {'combinedLitres': total(chosen), 'wellnessLitres': total(rows, 'JIVO_OIL'), 'martLitres': total(rows, 'JIVO_MART'),
            'beveragesLitres': total(rows, 'JIVO_BEVERAGES'), 'wellnessStorageLitres': total(rows, 'JIVO_OIL', 'wellnessStorageLitres'),
            **{key: total(chosen, key=key) for key in ('operationalWellnessLitres', 'operationalMartLitres', 'operationalUnclassifiedLitres')}}

def normalize(rows, details, now, start, end, pages):
    parsed = instant(now)
    if not parsed: raise ValueError('Observation timestamp missing timezone')
    selected = [r for r in rows if eligible(r, start, end)]
    entries = [normalize_entry(r, details[str(r['id'])]) for r in selected]
    entries.sort(key=lambda r: (r['departedAt'], r['id']), reverse=True)
    trips = []
    for key in sorted({e['tripId'] for e in entries}):
        group = [e for e in entries if e['tripId'] == key]
        # Arrival identity is the source's shared physical arrival, not a plate-day guess.
        trips.append({'id': key, 'date': group[0]['date'], 'departedAt': max(r['departedAt'] for r in group),
                      'gateEntryIds': [r['id'] for r in group], 'identityBasis': group[0]['identityBasis'], **totals(group)})
    days = []
    day = dt.date.fromisoformat(start)
    while str(day) <= end:
        group = [e for e in entries if e['date'] == str(day)]
        chosen = [e for e in group if e['company'] in ('JIVO_OIL', 'JIVO_MART')]
        days.append({'date': str(day), **totals(group), 'gateEntryCount': len(chosen),
                     'tripCount': len({e['tripId'] for e in chosen}), 'complete': all(e['detailComplete'] for e in group)})
        day += dt.timedelta(days=1)
    return {'version': 1, 'ok': True, 'complete': all(e['detailComplete'] for e in entries), 'asOf': now, 'attemptedAt': now,
            'expectedRefreshSeconds': 60, 'sourceUrl': 'https://ji.jivo.in/dispatch',
            'coverage': {'fromDate': start, 'toDate': end, 'dateBasis': 'DISPATCHED and actual gate_out_date, checked against dispatched_at in IST',
                         'allCompanies': True, 'listRows': len(rows), 'pages': pages, 'listComplete': True, 'queryDateFilter': None},
            'unitNote': 'Planning tonnes = source litres / 1,000. This is not measured physical weight.',
            'scopeNote': 'Headline includes Wellness and Mart. Beverages is separate. Only Wellness BH-BT/BH-PF dispatch frees the production godown.',
            'days': days, 'gateEntries': entries, 'trips': trips,
            'issues': sorted({issue for e in entries for issue in e['issues']})}
