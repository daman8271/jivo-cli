"""Reconcile physical Factory receipts with its PO book and EXIM shipments.

All identities entering the public contract are opaque. Raw supplier and vehicle
identities are used only inside reconciliation, never copied to the publication.
"""
import hashlib
import json
import math
from datetime import timedelta
from statistics import median
from collections import defaultdict
from replenishment_history import day
from replenishment_history import forecasts
from material_timing import timestamp, qa_timing, readiness

PM_ROOMS = ('BH-BS', 'BH-PM', 'BH-NM', 'BH-SDL', 'GP-NM', 'GP-PM', 'GP-FG')
RM_ROOMS = ('BH-LO', 'BH-CRUDE', 'BH-EX', 'BH-GJ')


def identity(*parts):
    return hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:24]


def amount(value):
    try:
        value = float(value)
        if not math.isfinite(value):
            raise ValueError('Nonfinite material quantity')
        return value
    except (ValueError, TypeError):
        raise ValueError('Invalid material quantity')


def normalized(code, quantity, unit, oils, density):
    unit = str(unit or '').upper().strip()
    if code.startswith('PM') and unit in {'PCS', 'PC', 'PIECES', 'NOS', 'NO'}:
        return quantity, 'PCS'
    # Film and tape use their own inventory unit; they are never converted to pieces.
    if code.startswith('PM') and unit in {'KG','KGS','MTR','METER','METRE','METERS','METRES','ROLL','ROLLS'}:
        return quantity, 'KGS' if unit in {'KG','KGS'} else 'MTR' if unit in {'MTR','METER','METRE','METERS','METRES'} else 'ROLL'
    if code in oils:
        if unit in {'L', 'LTR', 'LTRS', 'LITRE', 'LITRES'}:
            return quantity, 'L'
        if density and unit in {'KG', 'KGS', 'MT', 'MTS', 'TON', 'TONNE'}:
            return quantity * (1000 if unit in {'MT', 'MTS', 'TON', 'TONNE'} else 1) / density, 'L'
    return None, unit


def reconcile(raw):
    at = raw['asOf']
    oils = set(raw['oilCodes'])
    density = raw.get('densityKgPerLitre')
    aliases = raw.get('aliases', {})
    canonical = lambda code: aliases.get(code, code)
    stock = defaultdict(float)
    stock_units = {}
    rooms = {}
    conflicts, actions, lots, orders = [], [], [], []
    unmapped_oils = []
    dataset = raw.get('datasets', [])
    def action(code, quantity, unit, reason, refs=(), order=None, owner='Purchase team'):
        actions.append({'id': identity('action', code, order, reason), 'code': code, 'quantity': quantity,
            'unit': unit, 'orderId': order, 'reason': reason, 'ownerRole': owner,
            'requiredConfirmation': reason, 'evidenceIds': list(refs)})
    tanks = {}
    for row in raw.get('tanks', []):
        code = canonical(row.get('code', ''))
        if code in oils:
            tanks[code] = tanks.get(code, 0) + amount(row['quantity'])
        else:
            conflicts.append({'code': code, 'reason': 'EXIM oil has no verified canonical material mapping.'})
            unmapped_oils.append({'name': row.get('name', 'Unmapped EXIM oil'), 'quantity': amount(row['quantity']), 'unit': 'L'})
    stock.update(tanks)
    stock_units.update({code: 'L' for code in tanks})
    for warehouse, block in raw.get('stock', {}).items():
        detail = []
        for row in block['rows']:
            code = canonical(row.get('item_code', ''))
            if not code.startswith(('PM', 'RM')):
                continue
            qty = amount(row.get('on_hand'))
            converted, unit = normalized(code, qty, row.get('uom'), oils, density)
            eligible = warehouse in PM_ROOMS and code.startswith('PM')
            detail.append({'code': code, 'quantity': qty, 'unit': str(row.get('uom', '')), 'asOf': block['asOf'],
                'included': eligible and converted is not None, 'normalizedQuantity': converted,
                'normalizedUnit': unit, 'reason': 'Excluded: opening oil uses EXIM only; no factory balance fallback.' if code.startswith('RM') else 'Packaging warehouse explicitly allowed by the owner.' if warehouse in {'BH-NM', 'GP-NM'} else 'Factory warehouse balance.'})
            if eligible and converted is not None:
                if code in stock_units and stock_units[code] != unit:
                    raise ValueError('Conflicting stock units for one material')
                stock_units[code] = unit
                stock[code] += max(0, converted)
            elif eligible and qty:
                conflicts.append({'code': code, 'reason': 'Stock unit cannot be converted to the recipe unit.'})
        rooms[warehouse] = detail
    receipt_rows = []
    unique_receipts = {}
    for receipt in raw.get('receipts', []):
        if receipt['id'] in unique_receipts and unique_receipts[receipt['id']] != receipt:
            raise ValueError('Conflicting duplicate receipt identity')
        unique_receipts[receipt['id']] = receipt
    invalid_links = set()
    po_index = {(str(po['po_number']), line['line_num']): (canonical(line.get('po_item_code','')), po.get('supplier_code'), normalized(canonical(line.get('po_item_code','')), amount(line['ordered_qty']), line['uom'], oils, density)[1])
                for po in raw.get('orders', []) for line in po.get('items', [])}
    for row in unique_receipts.values():
        code = canonical(row['code'])
        converted, unit = normalized(code, amount(row['quantity']), row['unit'], oils, density)
        if converted is None:
            action(code, amount(row['quantity']), row['unit'], 'Confirm material unit or conversion before planning this receipt.', [identity('receipt', row['id'])], owner='Stores team')
            continue
        rejected, _ = normalized(code, amount(row.get('rejectedQty', 0)), row['unit'], oils, density)
        rejected = rejected or 0
        quantity = max(0, converted-rejected)
        order_key = (str(row.get('poNumber')), row.get('lineNum'))
        order_id = identity('JIVO_OIL', *order_key)
        link_conflict = order_key in po_index and po_index[order_key] != (code, row.get('supplier'), unit)
        if link_conflict:
            invalid_links.add(order_key)
            action(code, quantity, unit, 'Receipt material, supplier or unit disagrees with its current PO line; reconcile the identity before forecasting.', [identity('receipt', row['id'])], order_id, 'Stores team')
        if not row.get('posted') and not row.get('cancelled'):
            if row.get('lineNum') is None:
                action(code, quantity, unit, 'Receipt is missing its exact PO line; reconcile before adding outstanding supply.', [identity('receipt', row['id'])], owner='Stores team')
        stage = 'cancelled' if row.get('cancelled') else 'rejected' if row.get('qcStatus') == 'REJECTED' else 'usable' if row.get('posted') else 'accepted_unposted' if row.get('qcStatus') == 'ACCEPTED' else 'qc_pending'
        if link_conflict:
            stage = 'conflict'
        included = 'included' if row.get('posted') and row.get('stockSnapshotAfterPosting') else 'unresolved' if stage in {'usable', 'accepted_unposted'} else 'excluded'
        lot = {'id': identity('receipt', row['id']), 'code': code, 'quantity': quantity, 'unit': unit,
            'stage': stage, 'orderId': order_id, 'receiptId': identity('receipt', row['id']),
            'observedAt': row.get('observedAt', at), 'stockInclusion': included,
            'arrivalDate': row.get('arrivalDate'), 'availabilityDate': row.get('availableAt'),
            'evidenceIds': [identity('gate', row.get('gateId')), identity('receipt', row['id'])],
            'reason': 'Factory receipt lifecycle. QC acceptance alone does not establish inclusion in warehouse stock.'}
        lots.append(lot)
        if included == 'unresolved':
            action(code, quantity, unit, 'Confirm whether this received quantity is already in usable stock; do not add it twice.', lot['evidenceIds'], order_id, 'Stores team')
        receipt_rows.append({**lot, 'qaAcceptedAt': row.get('qaAcceptedAt'), 'supplier': row.get('supplier'), 'vehicle': row.get('vehicle'), 'raw': row})
        if rejected:
            lots.append({**lot, 'id': identity('rejection', row['id']), 'quantity': rejected, 'stage': 'rejected', 'stockInclusion': 'excluded'})
            action(code, rejected, unit, 'Rejected receipt remains in the PO reconciliation; confirm supplier replacement or cancellation before promising another arrival.', lot['evidenceIds'], order_id)
        elif stage == 'rejected':
            action(code, quantity, unit, 'QC rejected this receipt; confirm supplier replacement or cancellation before promising another arrival.', lot['evidenceIds'], order_id)
    for po in raw.get('orders', []):
        for line in po.get('items', []):
            code = canonical(line.get('po_item_code', ''))
            if not code.startswith(('PM', 'RM')):
                continue
            key = (str(po['po_number']), line['line_num'])
            ordered, unit = normalized(code, amount(line['ordered_qty']), line['uom'], oils, density)
            if ordered is None:
                action(code, amount(line['remaining_qty']), line['uom'], 'Confirm material unit or conversion before planning this order.', owner='Purchase team')
                continue
            remaining, _ = normalized(code, amount(line['remaining_qty']), line['uom'], oils, density)
            received, _ = normalized(code, amount(line['received_qty']), line['uom'], oils, density)
            physical = [r for r in receipt_rows if str(r['raw'].get('poNumber')) == key[0] and r['raw'].get('lineNum') == key[1]
                        and r['code'] == code and r.get('supplier') == po.get('supplier_code') and r['unit'] == unit and not r['raw'].get('cancelled')]
            history_complete = bool(day(raw.get('historyFrom')) and day(po['doc_date']) and day(raw['historyFrom']) <= day(po['doc_date']) and raw.get('receiptHistoryComplete'))
            physical_total = sum(normalized(code, amount(r['raw']['quantity']), r['raw']['unit'], oils, density)[0] for r in physical)
            # is_posted=false can already be included in PO.received_qty (verified
            # Factory examples). Only lifetime physical receipts minus the PO book
            # establishes the extra at-gate quantity. A partial history cannot.
            linked_complete = all(r['raw'].get('lineNum') is not None for r in receipt_rows if str(r['raw'].get('poNumber')) == key[0] and r['code'] == code)
            reliable = history_complete and linked_complete and key not in invalid_links and physical_total+.001 >= received and physical_total <= ordered+.001
            gated = min(max(0, remaining), max(0, physical_total-received)) if reliable else 0
            row = {'id': identity('JIVO_OIL', *key), 'code': code, 'unit': unit, 'orderedAt': po['doc_date'],
                'orderedQty': ordered, 'bookReceivedQty': received, 'outstandingQty': max(0, remaining),
                'notYetAtGateQty': max(0, remaining-gated), 'atGateQty': gated,
                'reconciliationComplete': reliable, 'notYetAtGateBasis': 'lifetime_receipts_net_book' if reliable else 'unreconciled_upper_bound',
                'sourceAsOf': po.get('sourceAsOf', raw.get('ordersAsOf', at)), 'supplier': po.get('supplier_code')}
            # An unresolved line match could double-count an already arrived load.
            unknown = [r for r in receipt_rows if str(r['raw'].get('poNumber')) == key[0] and r['code'] == code and r['raw'].get('lineNum') is None and not r['raw'].get('posted')]
            if unknown or key in invalid_links or not reliable:
                action(code, row['notYetAtGateQty'], unit, 'Unlinked receipt on this PO/material prevents a reliable outstanding arrival quantity.', [r['id'] for r in unknown], row['id'], 'Stores team')
                row['unresolvedReceiptLink'] = True
                if not reliable:
                    action(code, remaining, unit, 'PO received balance and complete lifetime gate receipts are not reconciled; outstanding quantity is visible but its undelivered part needs confirmation.', [row['id']], row['id'], 'Stores team')
                for receipt in physical:
                    current = next(l for l in lots if l['id'] == receipt['id'])
                    if current['stockInclusion'] != 'included':
                        current.update(stage='conflict', stockInclusion='unresolved', reason='PO lifetime gate history is incomplete or disagrees with the received balance; quantity cannot be added again.')
                        receipt['stage'] = 'conflict'
            else:
                # PO.received_qty proves aggregate accounting, not which load was
                # posted. Preserve physical stages/quantities and hold ambiguous
                # current receipts; never use a FIFO fiction to release QC stock.
                if received > 0:
                    for receipt in physical:
                        current = next(l for l in lots if l['id'] == receipt['id'])
                        if current['stockInclusion'] != 'included':
                            current['stockInclusion'] = 'unresolved'
                            current['reason'] = 'PO book receipts overlap physical gate history; the individual load included in stock is not established. Physical QC stage is unchanged.'
                            receipt['stockInclusion'] = 'unresolved'
            orders.append(row)
    # Link EXIM to exact physical load by vehicle, supplier, canonical material and quantity.
    for shipment in raw.get('shipments', []):
        code = canonical(shipment['code'])
        quantity = amount(shipment['quantity'])
        sid = identity('exim', shipment['id'])
        matches = [r for r in receipt_rows if r['code'] == code and shipment.get('vehicle') and r.get('vehicle') == shipment['vehicle'] and r.get('supplier') == shipment.get('supplier')
                   and day(r.get('arrivalDate')) and day(shipment.get('createdAt')) and day(r['arrivalDate']) >= day(shipment['createdAt'])
                   and abs(normalized(code, amount(r['raw']['quantity']), r['raw']['unit'], oils, density)[0]-quantity) <= max(1, quantity*.001)]
        if len(matches) == 1:
            matches[0]['shipmentId'] = sid
            next(l for l in lots if l['id'] == matches[0]['id'])['shipmentId'] = sid
            continue
        stage = shipment.get('stage', 'in_transit')
        lot = {'id': sid, 'code': code, 'quantity': quantity, 'unit': 'L', 'stage': stage,
            'shipmentId': sid, 'observedAt': shipment.get('asOf', at), 'stockInclusion': 'unresolved' if stage == 'ordered' else 'excluded',
            'arrivalDate': shipment.get('eta'), 'availabilityDate': None, 'evidenceIds': [sid],
            'reason': 'EXIM shipment ETA is an arrival date, not a QC or stock-release date.'}
        lots.append(lot)
        if len(matches) > 1:
            lot.update(stage='conflict', stockInclusion='unresolved')
            action(code, quantity, 'L', 'Shipment matches several factory receipts; confirm exact linkage.', [sid], owner='Stores team')
        else:
            action(code, quantity, 'L', 'Confirm shipment arrival and QC/stock-release date before treating this oil as usable.', [sid])
        # The Factory contract ledger and EXIM describe the same purchase. No second forecast of its oil.
    forecast_orders = []
    for order in orders:
        lot = {'id': order['id']+'-outstanding', 'code': order['code'], 'quantity': order['notYetAtGateQty'],
            'unit': order['unit'], 'stage': 'conflict' if order.get('unresolvedReceiptLink') else 'ordered', 'orderId': order['id'], 'observedAt': order['sourceAsOf'],
            'stockInclusion': 'unresolved' if order['code'].startswith('RM') or order.get('unresolvedReceiptLink') else 'excluded', 'evidenceIds': [order['id']], 'reason': 'Unreconciled upper bound from the PO outstanding balance; the undelivered quantity is not yet established.' if order.get('unresolvedReceiptLink') else 'Existing supplier order net of complete lifetime gate receipts and the PO received balance. Oil contract overlap requires shipment reconciliation.'}
        if lot['quantity']:
            lots.append(lot)
        # Raw oil contracts may overlap EXIM without a proven PO link. Never infer two receipt streams.
        if order['code'].startswith('RM'):
            action(order['code'], order['notYetAtGateQty'], order['unit'], 'Confirm drawdown and shipment linkage for this bulk oil contract.', [order['id']], order['id'])
        elif not order.get('unresolvedReceiptLink'):
            forecast_orders.append(order)
    expected, issues = forecasts(forecast_orders, receipt_rows, at, str((day(at).replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)))
    # Each estimated part receives its own lot; the residual stays undated.
    for estimate in expected:
        original = next((lot for lot in lots if lot['id'] == estimate['lotId']), None)
        if not original or estimate['quantity'] > original['quantity']:
            raise ValueError('Temporary packaging split exceeds outstanding lot')
        original['quantity'] -= estimate['quantity']
        split = {**original, 'id': estimate['id'] + '-lot', 'quantity': estimate['quantity'], 'arrivalDate': estimate['arrivalExpected'], 'reason': estimate['note']}
        lots.append(split)
        estimate['lotId'] = split['id']
    lots = [lot for lot in lots if lot['quantity'] > 0]
    # Shipment ETAs and already-gated QC waits use this supplier/material's actual QA latency.
    # This conditional forecast never releases a currently accepted-but-unposted lot.
    candidates = []
    for receipt in receipt_rows:
        if receipt['stage'] == 'qc_pending' and receipt['stockInclusion'] == 'excluded':
            candidates.append((receipt, receipt.get('supplier'), receipt.get('arrivalDate'), 'qc_history'))
    for shipment in raw.get('shipments', []):
        lot = next((l for l in lots if l['id'] == identity('exim', shipment['id'])), None)
        if lot and lot['stage'] == 'in_transit':
            candidates.append((lot, shipment.get('supplier'), shipment.get('eta'), 'shipment_eta'))
    for lot, supplier, arrival, basis in candidates:
        if not day(arrival):
            continue
        if basis == 'shipment_eta' and timestamp(arrival, True) < timestamp(at, True):
            action(lot['code'], lot['quantity'], lot['unit'], 'Source ETA passed without an exact linked gate receipt. Obtain a revised source ETA; no automatic date rollover.', [lot['id']])
            continue
        timing = qa_timing(receipt_rows, supplier, lot['code'], lot['unit'], at)
        if not timing:
            continue
        ready = readiness(arrival, timing)
        if not ready or ready['usableExpected'] < str(day(at)):
            continue
        observed = timestamp(lot.get('observedAt'), True)
        if basis == 'qc_history' and observed and timestamp(ready['qaEstimatedAt']) < observed:
            action(lot['code'], lot['quantity'], lot['unit'], 'Expected QA approval time passed, but the latest source observation still says QC pending. Obtain a QA update before planning availability.', [lot['id']], lot.get('orderId'), 'QA and stores teams')
            continue
        expected.append({'id': lot['id']+'-qa', 'lotId': lot['id'], 'orderId': lot.get('orderId'),
            'code': lot['code'], 'quantity': lot['quantity'], 'unit': lot['unit'],
            'arrivalEarliest': str(day(arrival)), 'arrivalExpected': str(day(arrival)), 'arrivalLatest': str(day(arrival)),
            **ready, 'basis': basis, 'confidence': 'estimated',
            'sampleCount': timing['sampleCount'], 'historyFrom': timing['historyFrom'],
            'historyTo': timing['historyTo'], 'evidenceIds': [lot['id']]+timing['evidenceIds'],
            'note': 'Source arrival plus matching supplier/material/unit elapsed receiving-to-QA hours, not laboratory working hours. Date-only ETA uses end of IST day. Hourly planning may start in the remaining shift hours after estimated QA; no automatic extra day. Stores release is unknown; conditional assumption: no additional stores delay.'})
        action(lot['code'], lot['quantity'], lot['unit'], 'Expected availability assumes no stores delay after estimated QA clearance; confirm usable release.', [lot['id']], lot.get('orderId'), 'QA and stores teams')
    for order, reason in issues:
        action(order['code'], order['notYetAtGateQty'], order['unit'], reason, [order['id']], order['id'])
    for order in orders:
        order.pop('supplier', None)
        order.pop('unresolvedReceiptLink', None)
    complete = bool(dataset) and all(d.get('ok') and d.get('complete') for d in dataset)
    result = {'version': 1, 'asOf': at, 'coverage': {'complete': complete, 'datasets': dataset},
        'stock': {'asOf': min((b['asOf'] for b in raw.get('stock', {}).values()), default=None),
            'byItem': dict(stock), 'unitByItem': stock_units, 'byWarehouse': rooms, 'excludedWarehouses': ['BH-OT', 'BH-PP', 'BH-WST', 'GP-FGM'], 'conflicts': conflicts, 'oilSourcePolicy': 'exim_only', 'unmappedOils': unmapped_oils},
        'orders': orders, 'lots': lots, 'expectedReceipts': expected, 'actions': actions,
        'unmappedShipments': [{'name': row.get('name', 'Unknown EXIM oil'), 'quantity': row.get('quantity'), 'unit': 'L', 'eta': row.get('eta'), 'stage': row.get('stage')} for row in raw.get('unmappedShipments', [])]}
    result['revision'] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()[:24]
    return result
