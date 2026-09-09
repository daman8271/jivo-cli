"""Bounded, source-backed arrival windows for existing supplier orders.

The clock is anchored to the last actual receipt, never to the refresh time.
Blanket contracts use receipt cadence rather than their creation date.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median
from material_timing import qa_timing, readiness


def day(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        # Date-only values and source-local naive times are Factory calendar dates.
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone(timedelta(hours=5, minutes=30)))
        return parsed.date()
    except (ValueError, TypeError):
        return None


def forecasts(orders, receipts, as_of, horizon):
    today = day(as_of)
    end = day(horizon)
    if not today or not end or today > day('2026-09-10'):
        return [], [(o, 'Temporary packaging estimate expired; obtain the supplier date.') for o in orders]
    history = defaultdict(list)
    for receipt in receipts:
        raw = receipt.get('raw', {})
        if raw.get('cancelled') or raw.get('qcStatus') == 'REJECTED' or float(raw.get('rejectedQty') or 0) > 0:
            continue
        if receipt.get('stage') not in {'usable', 'accepted_unposted'} or receipt.get('quantity', 0) <= 0:
            continue
        if day(receipt.get('arrivalDate')) and today-timedelta(days=90) <= day(receipt['arrivalDate']) <= today:
            history[(receipt.get('supplier'), receipt['code'], receipt['unit'])].append(receipt)
    groups = defaultdict(list)
    for order in orders:
        if order['code'].startswith('PM') and order['notYetAtGateQty'] > 0:
            groups[(order.get('supplier'), order['code'], order['unit'])].append(order)
    expected, issues = [], []
    for key, group in groups.items():
        samples = history[key]
        batches = defaultdict(float)
        for sample in samples:
            batches[day(sample['arrivalDate'])] += sample.get('historyQuantity',sample['quantity'])
        dates = sorted(batches)
        # A recurring, same-vendor/item history must have at least three distinct days.
        if len(dates) < 3:
            issues.extend((o, 'Fewer than three same-supplier, same-material receipt dates; obtain a delivery date.') for o in group)
            continue
        gaps = [(b-a).days for a, b in zip(dates, dates[1:])]
        cadence = max(1, round(median(gaps)))
        batch = median(batches.values())
        timing = qa_timing(samples, key[0], key[1], key[2], as_of)
        if not timing:
            issues.extend((o, 'Receipt history exists, but matching elapsed QA timing is unavailable; confirm release timing.') for o in group)
            continue
        ordered = sorted(group, key=lambda o: (o.get('orderedAt') or '', o['id']))
        remaining = {o['id']: o['notYetAtGateQty'] for o in ordered}
        # Do not roll a missed expectation forward and present it as new evidence.
        arrival = dates[-1] + timedelta(days=cadence)
        if arrival < today:
            issues.extend((o, 'The next historical delivery window has already passed without a receipt; obtain a revised supplier date.') for o in group)
            continue
        index = 0
        while arrival <= end and sum(remaining.values()) > 0:
            capacity = batch
            for order in ordered:
                quantity = min(capacity, remaining[order['id']])
                if quantity <= 0:
                    continue
                # A new PO cannot receive a window before its own creation date.
                created = day(order.get('orderedAt'))
                if created and arrival < created:
                    continue
                expected.append({'id': order['id'] + '-history-' + str(index), 'lotId': order['id'] + '-outstanding',
                    'orderId': order['id'], 'code': order['code'], 'quantity': quantity, 'unit': order['unit'],
                    'arrivalEarliest': str(max(today, arrival-timedelta(days=max(0, cadence-min(gaps))))),
                    'arrivalExpected': str(arrival), 'arrivalLatest': str(arrival+timedelta(days=max(0, max(gaps)-cadence))),
                    **readiness(str(arrival), timing),
                    'usableEarliest': readiness(str(max(today, arrival-timedelta(days=max(0, cadence-min(gaps))))), timing)['usableEarliest'],
                    'usableLatest': readiness(str(arrival+timedelta(days=max(0, max(gaps)-cadence))), timing)['usableLatest'],
                    'temporaryUntil': '2026-09-10', 'basis': 'temporary_packaging_estimate', 'confidence': 'estimated', 'sampleCount': len(dates),
                    'historyFrom': str(dates[0]), 'historyTo': str(dates[-1]),
                    'evidenceIds': [s['id'] for s in samples],
                    'note': 'TEMPORARY until owner confirmation; expires after 10 September 2026. Same supplier/material/unit receipt cadence and batch size, capped by outstanding orders. Estimated QA release; no additional stores/posting delay assumed; actual availability unverified. Not a supplier promise.'})
                capacity -= quantity
                remaining[order['id']] -= quantity
            arrival += timedelta(days=cadence)
            index += 1
        if any(r['orderId'] in remaining for r in expected):
            issues.extend((o, 'Expected dates assume no additional stores/posting delay after estimated QA release; confirm usable-stock timing.') for o in group)
    return expected, issues
