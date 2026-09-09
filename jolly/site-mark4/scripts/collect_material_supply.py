#!/usr/bin/env python3
"""Independent Factory supply workers. --mode orders discovers all suppliers;
--mode materials reads warehouse balances, gate/QC history and safe EXIM routes.
Only private cached records contain source identities. No source-system writes.
"""
import argparse
import ast
import calendar
import concurrent.futures
import csv
import datetime
import importlib
import json
import os
import pathlib
import re
import sys
import time
from collect_factory_supplement import Factory, atomic, load, stamp, IST
from material_supply import PM_ROOMS, RM_ROOMS, amount, reconcile


class MaterialFactory(Factory):
    def get(self, path, params=None):
        # Extend only the exact read routes used here; keep the original origin and redirect guards.
        return super().get(path, params)


def retained(cache, name, fn, max_age=0, interval=60):
    path = pathlib.Path(cache)/(name+'.json')
    previous = load(path) if path.exists() else None
    now = stamp()
    if previous and previous.get('ok') and max_age and time.time()-datetime.datetime.fromisoformat(previous['asOf']).timestamp() < max_age:
        return previous
    try:
        data = fn()
        result = {'ok': True, 'complete': True, 'asOf': stamp(), 'attemptedAt': now, 'data': data, 'expectedRefreshSeconds': interval}
    except Exception as exc:
        result = {**(previous or {'asOf': None, 'data': None}), 'ok': False, 'complete': False,
            'attemptedAt': now, 'error': 'Source read failed: '+type(exc).__name__, 'expectedRefreshSeconds': interval}
        if isinstance(getattr(exc, 'code', None), int):
            result['error'] += ' (HTTP '+str(exc.code)+')'
    atomic(path, result)
    return result


def scan_orders(client, cache, workers=4):
    """Successful suppliers replace their book; failed suppliers retain original rows/clocks."""
    catalog = retained(cache, 'suppliers', lambda: client.get('/po/vendors/'), interval=180)
    if not isinstance(catalog.get('data'), list):
        raise ValueError('Supplier catalog unavailable')
    vendors = sorted({r['vendor_code'] for r in catalog['data'] if r.get('vendor_code')})
    if not vendors or any(not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',v) for v in vendors):
        raise ValueError('Supplier catalog empty')
    def fetch(vendor):
        def get():
            data = client.get('/po/open-pos/', {'supplier_code': vendor})
            if not isinstance(data, list):
                raise ValueError('PO response is not a complete list')
            return data
        result = retained(pathlib.Path(cache)/'suppliers', vendor, get, interval=180)
        return vendor, result
    rows, readings = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for vendor, result in pool.map(fetch, vendors):
            readings.append({'supplier': vendor, **{k: result.get(k) for k in ('ok', 'complete', 'asOf', 'attemptedAt')}})
            for row in result.get('data') or []:
                rows.append({**row, 'supplier_code': vendor, 'sourceAsOf': result['asOf']})
    out = {'asOf': min((r['asOf'] for r in readings if r['asOf']), default=None),
        'attemptedAt': catalog['attemptedAt'], 'completedAt': stamp(),
        'ok': catalog['ok'] and all(r['ok'] for r in readings),
        'complete': catalog['ok'] and all(r['complete'] for r in readings),
        'supplierCount': len(vendors), 'supplierReadings': readings, 'orders': rows}
    atomic(pathlib.Path(cache)/'orders.json', out)
    return out


def read_stock(client, warehouse):
    rows, seen = [], set()
    for page in range(1, 101):
        data = client.get('/dashboards/stock/', {'warehouse': warehouse, 'sort_by': 'on_hand', 'sort_dir': 'desc', 'page': page, 'page_size': 200})
        if not isinstance(data, dict) or not isinstance(data.get('data'), list):
            raise ValueError('Stock response invalid')
        batch = data['data']
        for row in batch:
            if row.get('warehouse') != warehouse or row.get('item_code') in seen:
                raise ValueError('Stock warehouse or pagination mismatch')
            seen.add(row.get('item_code'))
            if amount(row.get('on_hand')) > 0:
                rows.append(row)
        if not batch or len(batch) < 200 or amount(batch[-1].get('on_hand')) <= 0 or page >= int(data.get('meta', {}).get('total_pages', 100)):
            return {'rows': rows}
    raise ValueError('Stock pagination cap reached')


def read_month(client, date):
    rows = []
    pages = 1
    page = 1
    while page <= pages:
        data = client.get('/grpo/all-entries/', {'month': date.month, 'year': date.year, 'page': page, 'page_size': 100})
        if not isinstance(data, dict) or not isinstance(data.get('results'), list):
            raise ValueError('Gate response invalid')
        pages = int(data['total_pages'])
        if pages > 100:
            raise ValueError('Gate pagination cap reached')
        rows.extend(data['results'])
        page += 1
    if len(rows) != int(data['count']):
        raise ValueError('Gate pagination incomplete')
    return rows


def months(today, count=3):
    value = today.replace(day=1)
    for _ in range(count):
        yield value
        value = (value-datetime.timedelta(days=1)).replace(day=1)


def source_record(name, result, seconds=None):
    return {'id': name, 'asOf': result.get('asOf'), 'attemptedAt': result.get('attemptedAt'),
        'ok': result.get('ok') is True, 'complete': result.get('complete') is True,
        'expectedRefreshSeconds': seconds if seconds is not None else result.get('expectedRefreshSeconds', 60), 'note': result.get('error') or 'Direct source observation; original clock retained on failure.'}


def read_gate(client, cache, today, workers=8):
    records = []
    entries = {}
    old_path = pathlib.Path(cache)/'unresolved.json'
    old = load(old_path) if old_path.exists() else {}
    dates = set(months(today))
    order_path = pathlib.Path(cache)/'orders.json'
    order_book = load(order_path) if order_path.exists() else {'orders': []}
    active = {str(po['po_number']) for po in order_book['orders'] if any(str(l.get('po_item_code','')).startswith(('PM','RM')) for l in po.get('items', []))}
    for path in pathlib.Path(cache).glob('gate-????-??.json'):
        dates.add(datetime.date.fromisoformat(path.stem[5:]+'-01'))
    for row in old.values():
        dates.add(datetime.date.fromisoformat(row['entry_time'][:10]).replace(day=1))
    unresolved_months = {row['entry_time'][:7] for row in old.values()}
    def fetch_month(date):
        name = 'gate-'+date.strftime('%Y-%m')
        fast = date == today.replace(day=1) or date.strftime('%Y-%m') in unresolved_months
        recent = date >= min(months(today))
        result = retained(cache, name, lambda d=date: read_month(client, d), max_age=0 if fast else 1800 if recent else 86400, interval=60 if fast else 1800 if recent else 86400)
        return date, name, result
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        month_results = list(pool.map(fetch_month, sorted(dates)))
    for date, name, result in month_results:
        recent = date >= min(months(today))
        records.append(source_record(name, result, 60 if date == today.replace(day=1) or date.strftime('%Y-%m') in unresolved_months else 1800 if recent else 86400))
        for row in result.get('data') or []:
            if not recent and not any(str(p.get('po_number')) in active for p in row.get('po_receipts', [])):
                continue
            entries[str(row['vehicle_entry_id'])] = row
    for ident, row in old.items():
        entries.setdefault(ident, row)
    receipts = []
    unresolved = {}
    def fetch_entry(pair):
        ident, entry = pair
        if not re.fullmatch(r'\d+',ident):
            raise ValueError('Invalid gate entry identity')
        if entry.get('phase') == 'CANCELLED':
            return None
        unsettled = not entry.get('is_fully_posted')
        # Only envelope PM/RM items can produce material receipts below. Empty gates
        # stay in unresolved discovery, but their detail cannot affect material supply.
        # This also avoids a vanished, item-less gate blocking every material balance.
        if not any(str(item.get('item_code', '')).startswith(('PM', 'RM'))
                   for po in entry.get('po_receipts', []) for item in po.get('items', [])):
            return ident, entry, unsettled, None, None
        interval = 60 if unsettled else 86400
        detail = retained(cache, 'detail-'+ident, lambda: client.get('/gate-core/raw-material-gate-entry/'+ident+'/'), max_age=0 if unsettled else 86400, interval=interval)
        linkage = retained(cache, 'link-'+ident, lambda: client.get('/raw-material-gatein/gate-entries/'+ident+'/po-receipts/view/'), max_age=0 if unsettled else 86400, interval=interval)
        return ident, entry, unsettled, detail, linkage
    # Each worker owns separate cache files; no shared requests or authentication mutations.
    # Finish every gate observation before reading warehouse stock below.
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        entry_results = list(pool.map(fetch_entry, entries.items()))
    for result in entry_results:
        if result is None:
            continue
        ident, entry, unsettled, detail, linkage = result
        if unsettled:
            unresolved[ident] = entry
        if detail is None:
            continue
        records.extend([source_record('receipt-detail-'+ident, detail, 60 if unsettled else 86400), source_record('receipt-link-'+ident, linkage, 60 if unsettled else 86400)])
        full = detail.get('data') or {}
        links = {str(item['id']): item.get('sap_line_num') for po in linkage.get('data') or [] for item in po.get('items', [])}
        full_items = {str(item['id']): item for po in full.get('po_receipts', []) for item in po.get('items', [])}
        for po in entry.get('po_receipts', []):
            for item in po.get('items', []):
                code = item.get('item_code', '')
                if not code.startswith(('PM', 'RM')):
                    continue
                iid = str(item['po_item_receipt_id'])
                enriched = full_items.get(iid, {})
                inspection = enriched.get('inspection') or {}
                qa = inspection.get('qam_approved_at') or (inspection.get('manager_decision') or {}).get('decided_at')
                final_status = inspection.get('final_status') or item.get('qc_status')
                slip = enriched.get('arrival_slip') or {}
                # Do not promote posting from an unchanged historical envelope.
                receipt = {'id': iid, 'gateId': ident, 'code': code, 'poNumber': po['po_number'],
                    'lineNum': links.get(iid), 'supplier': po.get('supplier_code'),
                    'quantity': amount(item['received_qty']), 'rejectedQty': amount(item.get('rejected_qty', 0)),
                    'unit': item['uom'], 'qcStatus': final_status, 'qaAcceptedAt': qa if final_status == 'ACCEPTED' else None,
                    'posted': po.get('is_posted') is True, 'arrivalDate': slip.get('arrival_datetime') or entry['entry_time'],
                    'vehicle': (full.get('vehicle') or {}).get('vehicle_number'),
                    'observedAt': detail.get('asOf'), 'stockSnapshotAfterPosting': False}
                receipts.append(receipt)
    atomic(old_path, unresolved)
    return receipts, records


def backfill_history(client, cache):
    """Discover older PO lifetimes independently; new suppliers can extend the range."""
    orders = load(pathlib.Path(cache)/'orders.json')
    dates = [datetime.date.fromisoformat(po['doc_date'][:10]) for po in orders['orders']
             if any(str(line.get('po_item_code','')).startswith(('PM','RM')) for line in po.get('items',[]))]
    if not dates:
        return {'ok': True, 'asOf': stamp(), 'months': 0}
    today = datetime.datetime.now(IST).date()
    first = min(dates).replace(day=1)
    last = min(months(today))
    result, count = True, 0
    while first < last:
        response = retained(cache, 'gate-'+first.strftime('%Y-%m'), lambda d=first: read_month(client,d), max_age=86400, interval=86400)
        result = result and response['ok']
        count += 1
        first = (first.replace(day=28)+datetime.timedelta(days=4)).replace(day=1)
    return {'ok': result, 'asOf': stamp(), 'months': count}


def reference_maps(root):
    tree = ast.parse((root/'live/freeze_live.py').read_text())
    mapping = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'OIL_NAME_TO_RM' for t in node.targets):
            mapping = ast.literal_eval(node.value)
    aliases = {}
    with (root/'reference/oil-synonyms.csv').open() as f:
        for row in csv.DictReader(f):
            values = list(row.values())
            if len(values) >= 2 and values[0].startswith('RM') and values[1].startswith('RM'):
                aliases[values[1]] = values[0]
    if not mapping:
        raise ValueError('Canonical oil name map unavailable')
    return mapping, aliases


def collect_materials(client, args):
    cache = pathlib.Path(args.cache_dir)
    root = pathlib.Path(args.source_root)
    today = datetime.datetime.now(IST).date()
    mapping, aliases = reference_maps(root)
    datasets, stock = [], {}
    receipts, gate_status = read_gate(client, cache, today)
    datasets.extend(gate_status)
    def fetch_warehouse(warehouse):
        return warehouse, retained(cache, 'stock-'+warehouse, lambda: read_stock(client, warehouse))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        warehouse_results = list(pool.map(fetch_warehouse, PM_ROOMS+RM_ROOMS))
    for warehouse, result in warehouse_results:
        datasets.append(source_record('stock-'+warehouse, result))
        if result.get('data') is not None:
            stock[warehouse] = {**result['data'], 'asOf': result['asOf']}
    # Gate posting is observed BEFORE the subsequent current warehouse read.
    # This establishes inclusion for posted packaging, not for undated manual oil dips.
    stock_complete = all(r.get('ok') and r.get('complete') for r in datasets if r['id'].startswith('stock-'))
    for receipt in receipts:
        receipt['stockSnapshotAfterPosting'] = stock_complete and receipt['posted'] and receipt['code'].startswith('PM')
    # These existing EXIM functions only read documented safe routes. Never invoke fetch()/its shared cache.
    sys.path.insert(0, str(root))
    exim = importlib.import_module('live.adapters.exim')
    def tanks_read():
        errors = []
        data = exim._tanks(errors)
        if errors:
            raise ValueError('EXIM tank source incomplete')
        return data
    tank_result = retained(cache, 'exim-tanks', tanks_read)
    tank_dataset = source_record('exim-tanks', tank_result, 86400)
    tank_dataset['asOf'] = (tank_result.get('data') or {}).get('reading_at')
    tank_dataset['checkedAt'] = tank_result.get('asOf')
    tank_dataset['pollIntervalSeconds'] = 60
    tank_dataset['note'] = 'Manual tank dip timestamp, not a sensor; source API polled every minute. Individual tanks may have older readings.'
    datasets.append(tank_dataset)
    tanks = [{'code': mapping.get(str(r.get('oil', '')).upper().strip(), ''), 'quantity': r['litres'], 'name': str(r.get('oil', ''))}
             for r in (tank_result.get('data') or {}).get('by_oil', [])]
    shipments = []
    unmapped_shipments = []
    for status, stage in [('ON_THE_WAY', 'in_transit'), ('OUT_SIDE_FACTORY', 'arrived'), ('UNDER_LOADING', 'loading'), ('IN_CONTRACT', 'ordered')]:
        def get(s=status):
            data = exim._cli('stock-status', 'get', '--status', s)
            if isinstance(data, dict):
                data = data.get('results', data.get('data'))
            if not isinstance(data, list):
                raise ValueError('EXIM shipment list invalid')
            return data
        result = retained(cache, 'exim-'+status.lower(), get)
        datasets.append(source_record('exim-'+status.lower(), result))
        for row in result.get('data') or []:
            if row.get('deleted') or amount(row.get('quantity', 0)) <= 0:
                continue
            code = mapping.get(str(row.get('item_name', '')).upper().strip())
            if not code:
                unmapped_shipments.append({'name': str(row.get('item_name', 'Unknown EXIM oil')), 'quantity': amount(row.get('quantity_in_litre')) if row.get('quantity_in_litre') is not None else None, 'unit': 'L', 'eta': row.get('eta'), 'stage': stage})
                continue
            shipments.append({'id': row['id'], 'parent': row.get('parent'), 'code': code,
                'quantity': amount(row.get('quantity_in_litre')), 'supplier': row.get('vendor_code'), 'createdAt': row.get('created_at'),
                'vehicle': row.get('vehicle_number'), 'eta': row.get('eta'), 'stage': stage, 'asOf': result['asOf']})
    order_path = cache/'orders.json'
    orders = load(order_path) if order_path.exists() else {'ok': False, 'complete': False, 'orders': [], 'asOf': None}
    if orders.get('asOf') and time.time()-datetime.datetime.fromisoformat(orders['asOf']).timestamp() > 600:
        orders = {**orders, 'ok': False, 'complete': False, 'error': 'All-supplier scan is overdue; previous rows retained.'}
    datasets.append(source_record('factory_purchase_orders', orders, 180))
    raw = {'asOf': stamp(), 'horizonEnd': str(today.replace(day=calendar.monthrange(today.year, today.month)[1])),
        'historyFrom': str(min(months(today))), 'receiptHistoryComplete': all(r['ok'] and r['complete'] for r in gate_status),
        'oilCodes': sorted(set(mapping.values()) | set(aliases.values())), 'aliases': aliases,
        'densityKgPerLitre': .91, 'stock': stock, 'tanks': tanks, 'receipts': receipts,
        'orders': orders['orders'], 'ordersAsOf': orders.get('asOf'), 'shipments': shipments, 'unmappedShipments': unmapped_shipments, 'datasets': datasets}
    # Only a contiguous sequence of complete monthly snapshots extends coverage.
    first = today.replace(day=1)
    while True:
        before = (first-datetime.timedelta(days=1)).replace(day=1)
        block = next((d for d in gate_status if d['id']=='gate-'+before.strftime('%Y-%m')), None)
        if not block or not block['ok'] or not block['complete']:
            break
        first = before
    raw['historyFrom'] = str(first)
    raw['oilCodes'] = sorted(set(raw['oilCodes']) | {aliases.get(row['item_code'], row['item_code']) for block in stock.values() for row in block['rows'] if str(row.get('item_code','')).startswith('RM') and re.search(r'\bOIL\b',str(row.get('item_name','')), re.I)})
    atomic(cache/'material-raw.json', raw)
    output = reconcile(raw)
    return {'asOf': output['asOf'], 'ok': output['coverage']['complete'], 'data': output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=['orders', 'materials', 'history'])
    parser.add_argument('--config', required=True)
    parser.add_argument('--cache-dir', required=True)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--output')
    parser.add_argument('--interval', type=int, default=60)
    args = parser.parse_args()
    if args.mode == 'materials' and not args.output:
        parser.error('--output is required for materials')
    while True:
        began = time.monotonic()
        try:
            client = MaterialFactory(args.config, args.cache_dir)
            result = scan_orders(client, args.cache_dir) if args.mode == 'orders' else backfill_history(client,args.cache_dir) if args.mode == 'history' else collect_materials(client, args)
            if args.output:
                atomic(args.output, result)
            print(json.dumps({'mode': args.mode, 'ok': result['ok'], 'asOf': result['asOf'], 'seconds': round(time.monotonic()-began, 2)}), flush=True)
        except Exception as exc:
            if args.output and pathlib.Path(args.output).exists():
                previous = load(args.output)
                atomic(args.output, {**previous, 'ok': False, 'attemptedAt': stamp(), 'error': 'Material source refresh failed; last evidence retained.'})
            print(json.dumps({'mode': args.mode, 'ok': False, 'errorType': type(exc).__name__}), flush=True)
            if not args.interval:
                raise
        if not args.interval:
            break
        time.sleep(max(1, args.interval-(time.monotonic()-began)))


if __name__ == '__main__':
    main()
