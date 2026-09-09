"""Public scalar contract for independently refreshed source supplements."""
import hashlib
import ast
import math
import re
from datetime import datetime, timezone

CODE = re.compile(r'^(?:FG|PM|RM)\d{7}$')
DAY = re.compile(r'^\d{4}-\d{2}-\d{2}$')
LINES = {'JP Machine', 'Clear Pack', '10 Head', '6 Head', 'Tin Head', 'Pouch Machine'}


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def text(value, limit=300):
    if not isinstance(value, str):
        return ''
    return re.sub(r'https?://\S+|[\w.+-]+@[\w.-]+\.\w+|(?:/Users/|/root/|/home/)\S*|\+?\d[\d ()-]{8,}\d', '[redacted]', value)[:limit]


def stamp(value):
    if not isinstance(value, str):
        return None
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value
    except ValueError:
        return None


def numbers(value):
    return {k: number(v) for k, v in value.items() if CODE.fullmatch(str(k)) and number(v) is not None} if isinstance(value, dict) else {}


def ident(value):
    return hashlib.sha256(str(value).encode()).hexdigest()[:24]


def fresh(envelope, minutes):
    at = stamp(envelope.get('asOf'))
    if not at or envelope.get('ok') is not True:
        return False
    try:
        parsed = datetime.fromisoformat(at.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            return False
        return -300 <= (datetime.now(timezone.utc) - parsed).total_seconds() <= minutes * 60
    except ValueError:
        return False


def add_exim_transit(out, state, source_root):
    """Keep individual EXIM shipments beside factory POs; never reuse merged lead-time guesses."""
    if isinstance(out.get('materialSupply'), dict):
        return
    from pathlib import Path
    tree = ast.parse((Path(source_root) / 'live/freeze_live.py').read_text())
    mapping = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'OIL_NAME_TO_RM' for t in node.targets):
            mapping = ast.literal_eval(node.value)
    if not mapping:
        raise ValueError('Canonical EXIM oil map unavailable')
    inbound = state.get('exim', {}).get('inbound', {})
    at = stamp(inbound.get('fetched_at'))
    rows = inbound.get('on_the_way')
    if not isinstance(rows, list):
        out['sources'].append({'id':'exim_transit_events','label':'Individual oil shipments','asOf':at,'ok':False,'note':'Shipment records could not be read; supplier contract balances are not arrival dates.'})
        return
    events = out.setdefault('inboundEvents', [])
    for row in rows:
        if not isinstance(row, dict) or row.get('id') is None:
            continue
        code = mapping.get(str(row.get('oil', '')).upper().strip())
        qty = number(row.get('litres'))
        if not code or not CODE.fullmatch(code) or qty is None or qty <= 0:
            continue
        received = bool(row.get('grpo_number'))
        eta = stamp(row.get('eta'))
        events.append({'id':ident('exim-transit:' + str(row.get('id'))), 'source':'exim_transit', 'code':code, 'quantity':qty, 'unit':'L', 'orderedAt':stamp(row.get('created_at')), 'expectedAt':eta, 'asOf':at, 'dateBasis':'transit_eta' if eta else 'unverified', 'status':'received' if received else 'in_transit', 'confidence':'confirmed' if eta else 'unknown', 'stockIncluded':received, 'note':'Individual EXIM on-the-way shipment and its source ETA. Expected arrival is not a recorded receipt; overdue ETAs require a revised date. Supplier contract end dates and undrawn balances are not shipments.'})
    out['sources'].append({'id':'exim_transit_events','label':'Individual oil shipments','asOf':at,'ok':fresh({'asOf':at,'ok':state.get('sources',{}).get('exim',{}).get('ok') is True},45),'note':'Per-shipment EXIM quantities and ETAs; overdue or undated entries are held for confirmation.'})


def merge_material_supply(out, envelope):
    """Field-allowlist the independently observed ledger; hash every reference consistently."""
    data = envelope.get('data') if isinstance(envelope, dict) else None
    if not isinstance(data, dict) or data.get('version') != 1:
        out['sources'].append({'id': 'material_supply', 'label': 'Factory material reconciliation', 'asOf': None, 'ok': False, 'note': 'Reconciled material feed unavailable.'})
        return
    stages = {'ordered','loading','in_transit','arrived','qc_pending','accepted_unposted','usable','rejected','cancelled','conflict'}
    inclusion = {'included','excluded','unresolved'}
    clean = {'version': 1, 'revision': ident(data.get('revision')), 'asOf': stamp(data.get('asOf'))}
    datasets = []
    for row in (data.get('coverage') or {}).get('datasets', []):
        if not isinstance(row, dict):
            continue
        datasets.append({'id': text(row.get('id'), 100), 'asOf': stamp(row.get('asOf')), 'attemptedAt': stamp(row.get('attemptedAt')),
            'ok': row.get('ok') is True, 'complete': row.get('complete') is True,
            'expectedRefreshSeconds': number(row.get('expectedRefreshSeconds')), 'note': text(row.get('note'), 500)})
    clean['coverage'] = {'complete': envelope.get('ok') is True and (data.get('coverage') or {}).get('complete') is True, 'datasets': datasets}
    clean['unmappedShipments'] = [{'name': text(row.get('name'), 120), 'quantity': number(row.get('quantity')), 'unit': 'L',
        'eta': stamp(row.get('eta')), 'stage': row.get('stage') if row.get('stage') in stages else 'conflict'}
        for row in data.get('unmappedShipments', []) if isinstance(row, dict)]
    stock = data.get('stock') or {}
    clean['stock'] = {'asOf': stamp(stock.get('asOf')), 'byItem': numbers(stock.get('byItem')),
        'unitByItem': {code: text(unit, 20) for code, unit in stock.get('unitByItem', {}).items() if CODE.fullmatch(str(code))},
        'oilSourcePolicy': 'exim_only', 'unmappedOils': [{'name': text(r.get('name'), 120), 'quantity': number(r.get('quantity')), 'unit': 'L'} for r in stock.get('unmappedOils', []) if isinstance(r, dict)],
        'byWarehouse': {}, 'excludedWarehouses': [text(v, 30) for v in stock.get('excludedWarehouses', [])],
        'conflicts': [{'code': r.get('code') if CODE.fullmatch(str(r.get('code'))) else None, 'reason': text(r.get('reason'), 500)} for r in stock.get('conflicts', []) if isinstance(r, dict)]}
    for warehouse, rows in (stock.get('byWarehouse') or {}).items():
        if not re.fullmatch(r'[A-Z]{2}-[A-Z]{2,5}', warehouse) or not isinstance(rows, list):
            continue
        clean['stock']['byWarehouse'][warehouse] = [{'code': r['code'], 'quantity': number(r.get('quantity')),
            'unit': text(r.get('unit'), 20), 'asOf': stamp(r.get('asOf')), 'included': r.get('included') is True,
            'normalizedQuantity': number(r.get('normalizedQuantity')), 'normalizedUnit': text(r.get('normalizedUnit'), 20),
            'reason': text(r.get('reason'), 400)} for r in rows if isinstance(r, dict) and CODE.fullmatch(str(r.get('code')))]
    # Older cached collectors included factory oil when no tank was mapped.
    # Remove those exact contributions before marking the source contract EXIM-only.
    for rows in clean['stock']['byWarehouse'].values():
        for row in rows:
            if row['code'].startswith('RM'):
                if row['included'] and stock.get('oilSourcePolicy') != 'exim_only':
                    qty = row.get('normalizedQuantity')
                    clean['stock']['byItem'][row['code']] = max(0, clean['stock']['byItem'].get(row['code'], 0)-max(0, qty)) if qty is not None else 0
                row['included'] = False
                row['reason'] = 'Excluded: opening oil uses EXIM only; no factory balance fallback.'
    fields = {
        'orders': {'numbers': ('orderedQty','bookReceivedQty','outstandingQty','notYetAtGateQty','atGateQty'), 'dates': ('orderedAt','sourceAsOf'), 'refs': ('id',)},
        'lots': {'numbers': ('quantity',), 'dates': ('observedAt','arrivalDate','availabilityDate'), 'refs': ('id','orderId','shipmentId','receiptId')},
        'expectedReceipts': {'numbers': ('quantity','sampleCount'), 'dates': ('arrivalEarliest','arrivalExpected','arrivalLatest','usableEarliest','usableExpected','usableLatest','historyFrom','historyTo'), 'refs': ('id','lotId','orderId')},
        'actions': {'numbers': ('quantity',), 'dates': (), 'refs': ('id','orderId')},
    }
    for key, config in fields.items():
        clean[key] = []
        for row in data.get(key, []):
            if not isinstance(row, dict) or not CODE.fullmatch(str(row.get('code'))):
                continue
            value = {'code': row['code'], 'unit': text(row.get('unit'), 20)}
            value.update({k: number(row.get(k)) for k in config['numbers']})
            value.update({k: stamp(row.get(k)) for k in config['dates']})
            value.update({k: ident(row[k]) for k in config['refs'] if row.get(k) is not None})
            if key != 'orders':
                value['evidenceIds'] = [ident(v) for v in row.get('evidenceIds', [])]
            if key == 'orders':
                value.update(reconciliationComplete=row.get('reconciliationComplete') is True, notYetAtGateBasis=row.get('notYetAtGateBasis') if row.get('notYetAtGateBasis') in {'lifetime_receipts_net_book','unreconciled_upper_bound'} else 'unreconciled_upper_bound')
            elif key == 'lots':
                value.update(stage=row.get('stage') if row.get('stage') in stages else 'conflict', stockInclusion=row.get('stockInclusion') if row.get('stockInclusion') in inclusion else 'unresolved', reason=text(row.get('reason'), 700))
            elif key == 'expectedReceipts':
                if row.get('basis') not in {'supplier_due','shipment_eta','supplier_item_history','temporary_packaging_estimate','qc_history'} or row.get('confidence') not in {'recorded','estimated'}:
                    continue
                value.update(temporaryUntil=stamp(row.get('temporaryUntil')), basis=row['basis'], confidence=row['confidence'], note=text(row.get('note'), 700))
                if row.get('timingVersion') in (1, 2):
                    value.update(timingVersion=row['timingVersion'], readyAt=stamp(row.get('readyAt')), sourceArrivalAt=stamp(row.get('sourceArrivalAt')), arrivalTimeKnown=row.get('arrivalTimeKnown') is True, qaMedianHours=number(row.get('qaMedianHours')), qaEstimatedAt=stamp(row.get('qaEstimatedAt')), storesReleaseAt=stamp(row.get('storesReleaseAt')))
            elif key == 'actions':
                value.update(reason=text(row.get('reason'), 700), ownerRole=text(row.get('ownerRole'), 60), requiredConfirmation=text(row.get('requiredConfirmation'), 700))
            clean[key].append(value)
    out['materialSupply'] = clean
    out['sources'] = [s for s in out['sources'] if s['id'] not in {'opening_pm','opening_oil','opening_oil_drums','inbound','exim_transit_events'}]
    out['sources'].append({'id': 'material_supply', 'label': 'Factory stock, supplier orders and incoming loads', 'asOf': clean['asOf'], 'ok': clean['coverage']['complete'] and fresh(envelope, 10), 'note': 'Independent warehouse, supplier and gate/QC observations. Expected arrivals are separately qualified.'})
    if clean['stock']['byWarehouse']:
        out['opening']['stock'] = clean['stock']['byItem']
        out['opening']['packaging_pieces'] = sum(v for k, v in clean['stock']['byItem'].items() if k.startswith('PM'))
        out['opening']['oil_l'] = sum(v for k, v in clean['stock']['byItem'].items() if k.startswith('RM'))
        for code, unit in clean['stock']['unitByItem'].items():
            if code in out['items']:
                out['items'][code]['uom'] = unit
    out['inboundEvents'] = []
    out['inbound_prebooked'] = {}
    out['inbound_provenance'] = {}


def merge(out, envelope, kind):
    """Merge only known fields. Failure retains original dated data, never a fresh badge."""
    envelope = envelope if isinstance(envelope, dict) else {}
    data = envelope.get('data')
    available = isinstance(data, dict) and (isinstance(data.get('demandBook'), dict) and isinstance(data['demandBook'].get('online'), dict) and isinstance(data['demandBook'].get('trade'), dict) and isinstance(data.get('orders'), list) if kind == 'demand' else isinstance(data.get('inboundEvents'), list) and isinstance(data.get('recordedLabour'), dict) and isinstance(data.get('historyDays'), list) if kind == 'factory' else False)
    actual_at = (stamp(data['demandBook'].get('asOf')) or stamp(envelope.get('asOf'))) if available and kind == 'demand' else stamp(envelope.get('asOf'))
    complete = available and (data['demandBook'].get('coverage') == 'complete' if kind == 'demand' else (data.get('coverage') or {}).get('allSuppliers') is True)
    observed = {**envelope, 'asOf': actual_at}
    out['sources'].append({'id': f'{kind}_supplement', 'label': 'Exact open order book' if kind == 'demand' else 'Factory purchase orders and recorded costs', 'asOf': actual_at, 'ok': complete and fresh(observed, 15 if kind == 'demand' else 45), 'note': 'Independent source read; incomplete coverage or a failed refresh retains its original observation date.'})
    if not available:
        return
    if kind == 'demand':
        raw = data.get('demandBook')
        if isinstance(raw, dict):
            online = raw.get('online') or {}
            trade = raw.get('trade') or {}
            book = {'asOf': stamp(raw.get('asOf')) or stamp(envelope.get('asOf')), 'coverage': raw.get('coverage') if raw.get('coverage') in {'complete', 'partial', 'unavailable'} else 'unavailable'}
            book['online'] = {k: number(online.get(k)) for k in ('grossOpenLitres', 'quickCommerceLitres', 'amazonLitres', 'openValueExGst', 'openPoCount', 'priorMonthOpenLitres', 'dueThisMonthLitres', 'overdueLitres', 'laterDueLitres', 'undatedLitres', 'expiredExcludedLitres', 'unmappedLitres', 'acceptedOpenLitres', 'amazonAcceptedRemainingLitres', 'unacceptedRequestedLitres', 'planningDueLitres', 'acceptedPlanningDueLitres', 'priorMonthOpenPoCount', 'amazonPriorMonthOpenLitres', 'amazonPriorMonthOpenPoCount', 'unknownUnitLitres', 'quantityMismatchLitres', 'unknownUnitLineCount', 'outsideOilScopeLitres', 'outsideOilScopeAcceptedLitres', 'outsideOilScopePlanningDueLitres', 'outsideOilScopeAcceptedPlanningDueLitres', 'unknownUnitUnclassifiedLineCount', 'mappingConflictLitres', 'mappingConflictAcceptedLitres')}
            book['online']['dateBasis'] = text(online.get('dateBasis'))
            book['online']['byPlatform'] = [{'platform': text(r.get('platform'), 40), 'litres': number(r.get('litres')), 'acceptedLitres': number(r.get('acceptedLitres')), 'poCount': number(r.get('poCount'))} for r in online.get('byPlatform', []) if isinstance(r, dict) and number(r.get('litres')) is not None and number(r.get('poCount')) is not None]
            book['trade'] = {k: number(trade.get(k)) for k in ('grossOpenLitres', 'openOrderCount', 'openValueExGst', 'planningDueLitres', 'dueThisMonthLitres', 'overdueLitres', 'laterDueLitres', 'undatedLitres', 'otherCompanyOpenLitres', 'otherCategoryOpenLitres', 'unknownCompanyOpenLitres', 'sourceOrderCount', 'unknownActiveOrderCount')}
            book['trade'].update(companyScope=text(trade.get('companyScope')), scopeVerified=trade.get('scopeVerified') is True, isNetOutstanding=trade.get('isNetOutstanding') is True)
            book['trade'].update(isComplete=trade.get('isComplete') is True, headerAsOf=stamp(trade.get('headerAsOf')), unknownActiveOrders=[{'id':ident(r.get('id')), 'status':text(r.get('status'),40), 'createdAt':stamp(r.get('createdAt')), 'companyScope':'unknown', 'litres':None} for r in trade.get('unknownActiveOrders', []) if isinstance(r,dict)][:100])
            book['reconciliationNotes'] = [text(s, 600) for s in raw.get('reconciliationNotes', []) if isinstance(s, str)][:30]
            out['demandBook'] = book
        identity = data.get('factoryIdentity')
        if isinstance(identity, dict):
            out['factoryIdentity'] = {'asOf':stamp(identity.get('asOf')), 'items':{code:{'name':text(item.get('name'),180),'packLitres':number(item.get('packLitres')),'uom':text(item.get('uom'),20)} for code,item in (identity.get('items') or {}).items() if CODE.fullmatch(str(code)) and isinstance(item,dict)}}
        if isinstance(data.get('identityConflicts'), list):
            out['identityConflicts'] = [{'code':r['code'],'reason':text(r.get('reason'),500),'factoryName':text(r.get('factoryName'),180),'plannerName':text(r.get('plannerName'),180),'factoryPackLitres':number(r.get('factoryPackLitres')),'plannerPackLitres':number(r.get('plannerPackLitres'))} for r in data['identityConflicts'] if isinstance(r,dict) and CODE.fullmatch(str(r.get('code')))]
        if isinstance(data.get('orders'), list):
            rows = []
            for row in data['orders']:
                if not isinstance(row, dict) or number(row.get('pieces')) is None or row['pieces'] < 0:
                    continue
                rows.append({'docnum': ident(row.get('docnum') or row.get('sourceLineId')), 'sourceLineId': ident(row.get('sourceLineId') or row.get('docnum')), 'date': stamp(row.get('date')) or '', 'due': stamp(row.get('due')) or '', 'expiresAt': stamp(row.get('expiresAt')), 'code': row['code'] if CODE.fullmatch(str(row.get('code'))) else None, 'pieces': row['pieces'], 'value': number(row.get('value')), 'packLitres': number(row.get('packLitres')), 'remainingLitres': number(row.get('remainingLitres')), 'requestedLitres': number(row.get('requestedLitres')), 'requestedPieces': number(row.get('requestedPieces')), 'schemePieces': number(row.get('schemePieces')), 'channel': text(row.get('channel'), 30), '_src': text(row.get('_src'), 30), 'status': text(row.get('status'), 30), 'companyScope': text(row.get('companyScope'), 100), 'demand_basis': text(row.get('demand_basis'), 400), 'remainingBasis':text(row.get('remainingBasis'),400), 'dueBasis':text(row.get('dueBasis'),200), 'platform':text(row.get('platform'),40), 'sourceProductName':text(row.get('sourceProductName'),180), 'sourceSkuCode':text(row.get('sourceSkuCode'),40), 'sourcePackLitres':number(row.get('sourcePackLitres')), 'code_mapping_verified':row.get('code_mapping_verified') is True, 'mappingReason':text(row.get('mappingReason'),400), 'mappingIssue':text(row.get('mappingReason') or row.get('mappingIssue'),400), 'is_exact_sku_due': row.get('is_exact_sku_due') is True, 'value_basis': text(row.get('value_basis'), 200)})
            out['orders'] = rows
            out['backlog'] = []
            # Those old stamps described the replaced plan-only allocation.
            out['sources'] = [s for s in out['sources'] if s['id'] not in {'orders', 'orders_ecom'}]
        for code, item in (data.get('items') or {}).items():
            if CODE.fullmatch(str(code)) and isinstance(item, dict) and code not in out['items'] and item.get('factoryVerified') is True:
                out['items'][code] = {'name': text(item.get('name'), 180), 'uom': text(item.get('uom'), 20)}
        for code, recipe in (data.get('bom') or {}).items():
            if CODE.fullmatch(str(code)) and isinstance(recipe, list) and code not in out['bom']:
                out['bom'][code] = [[r[0], r[1]] for r in recipe if isinstance(r, list) and len(r) == 2 and CODE.fullmatch(str(r[0])) and number(r[1]) is not None and r[1] > 0]
    else:
        if isinstance(data.get('inboundEvents'), list):
            out['inboundEvents'] = []
            for row in data['inboundEvents']:
                if not isinstance(row, dict) or not CODE.fullmatch(str(row.get('code'))) or number(row.get('quantity')) is None or row['quantity'] < 0:
                    continue
                if row.get('source') not in {'factory_po', 'exim_transit', 'qc', 'legacy'} or row.get('status') not in {'open', 'in_transit', 'qc', 'received', 'cancelled'}:
                    continue
                out['inboundEvents'].append({'id': ident(row.get('id')), 'linkedOrderId': ident(row['linkedOrderId']) if row.get('linkedOrderId') else None, 'source': row['source'], 'code': row['code'], 'quantity': row['quantity'], 'unit': text(row.get('unit'), 20), 'orderedAt': stamp(row.get('orderedAt')), 'expectedAt': stamp(row.get('expectedAt')), 'asOf': stamp(row.get('asOf')), 'dateBasis': row.get('dateBasis') if row.get('dateBasis') in {'supplier_due', 'transit_eta', 'observed_lead', 'unverified'} else 'unverified', 'status': row['status'], 'confidence': row.get('confidence') if row.get('confidence') in {'confirmed', 'estimated', 'unknown'} else 'unknown', 'stockIncluded': row.get('stockIncluded') if isinstance(row.get('stockIncluded'), bool) else None, 'note': text(row.get('note'), 600)})
        labour = data.get('recordedLabour')
        if isinstance(labour, dict):
            runs = []
            for row in labour.get('runs', []):
                if not isinstance(row, dict) or row.get('line') not in LINES or not CODE.fullmatch(str(row.get('code'))) or not stamp(row.get('date')):
                    continue
                runs.append({'id': ident(row.get('id') or str(row)), 'date': row['date'], 'line': row['line'], 'code': row['code'], 'litres': number(row.get('litres')), 'labourCost': number(row.get('labourCost'))})
            out['supplements']['recordedLabour'] = {'asOf': stamp(labour.get('asOf')), 'windowFrom': stamp(labour.get('windowFrom')), 'windowTo': stamp(labour.get('windowTo')), 'basis': text(labour.get('basis'), 400), 'runs': runs}
        for row in data.get('historyDays', []):
            if not isinstance(row, dict) or not DAY.fullmatch(str(row.get('date'))):
                continue
            day = next((d for d in out['history']['days'] if d['date'] == row['date']), None)
            if day is None:
                continue
            day['mes_by_item_l'] = numbers(row.get('mes_by_item_l')) if isinstance(row.get('mes_by_item_l'), dict) else None
            # Keep the original booked/MES bases. Valuation checks composition
            # against them, rather than replacing an inconvenient total.
            v = row.get('booked_recorded_value')
            if isinstance(v, dict):
                day['booked_recorded_value'] = {'value': number(v.get('value')), 'coveredLitres': number(v.get('coveredLitres')), 'asOf': stamp(v.get('asOf')), 'basis': text(v.get('basis')), 'rows': number(v.get('rows'))}
        coverage = data.get('coverage')
        if isinstance(coverage, dict):
            out['sources'][-1]['note'] = f"Read {number(coverage.get('supplierCount'))} suppliers; all-supplier coverage: {coverage.get('allSuppliers') is True}. Open PO dates are creation dates, not delivery commitments."
    v = data.get('valuation')
    if isinstance(v, dict):
        out['valuation'] = {'asOf': stamp(v.get('asOf')), 'priceBasis': text(v.get('priceBasis'), 400), 'litresPerPiece': numbers(v.get('litresPerPiece')), 'rupeesPerLitre': numbers(v.get('rupeesPerLitre'))}
