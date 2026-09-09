#!/usr/bin/env python3
"""Read-only release checks for the owned material feed and public model.

Capture two invocations after separate live cycles to evidence refresh. Partial
coverage is reported, never converted to a passing assertion of completeness.
"""
import argparse
import json
import math
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def read(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    with urlopen(Request(url, data=data, headers={"Content-Type": "application/json"}), timeout=90) as response:
        assert response.status == 200
        return json.load(response)


def finite_nonnegative(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def check_ledger(ledger):
    assert ledger['version'] == 1 and ledger['revision']
    lots = {row['id']: row for row in ledger['lots']}
    assert len(lots) == len(ledger['lots']), 'Duplicate lot IDs'
    orders = {row['id']: row for row in ledger['orders']}
    assert len(orders) == len(ledger['orders']), 'Duplicate order-line IDs'
    for row in ledger['orders']:
        for key in ('orderedQty', 'bookReceivedQty', 'outstandingQty', 'notYetAtGateQty', 'atGateQty'):
            assert finite_nonnegative(row[key]), (row['id'], key)
        assert row['notYetAtGateQty'] <= row['outstandingQty'] + .01
    for row in lots.values():
        assert finite_nonnegative(row['quantity'])
        assert row['stockInclusion'] in ('included', 'excluded', 'unresolved')
        if row.get('orderId') and row['stage'] not in ('usable', 'rejected', 'cancelled', 'accepted_unposted', 'qc_pending', 'arrived'):
            assert row['orderId'] in orders, 'Dangling lot order'
    allocated = {}
    for event in ledger['expectedReceipts']:
        assert event['lotId'] in lots, 'Dangling forecast lot'
        lot = lots[event['lotId']]
        assert event['code'] == lot['code'] and event['unit'] == lot['unit']
        assert finite_nonnegative(event['quantity'])
        allocated[event['lotId']] = allocated.get(event['lotId'], 0) + event['quantity']
        assert allocated[event['lotId']] <= lot['quantity'] + .01, 'Forecast exceeds lot'
        if event.get('usableExpected') and event.get('arrivalExpected'):
            assert event['usableExpected'] >= event['arrivalExpected'], 'Usable before arrival'
        assert event['confidence'] in ('recorded', 'estimated')
    now = datetime.now(timezone.utc)
    coverage = []
    for row in ledger['coverage']['datasets']:
        observed = datetime.fromisoformat(row['asOf'].replace('Z', '+00:00')) if row.get('asOf') else None
        if observed is not None and observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        age = (now-observed).total_seconds() if observed else None
        coverage.append({'id': row['id'], 'asOf': row.get('asOf'), 'ok': row['ok'], 'complete': row['complete'], 'ageSeconds': round(age) if age is not None else None, 'expectedRefreshSeconds': row['expectedRefreshSeconds']})
    return coverage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--feed', default='https://mark4-astha.srv1685505.hstgr.cloud/inputs.json')
    parser.add_argument('--app', default='https://jivo-mark4-astha.vercel.app')
    parser.add_argument('--feed-only', action='store_true')
    args = parser.parse_args()
    source = read(args.feed)
    ledger = source['materialSupply']
    coverage = check_ledger(ledger)
    for code, quantity in ledger['stock']['byItem'].items():
        assert abs(source['opening']['stock'].get(code, 0)-quantity) < .01, f'Owned stock not applied: {code}'
    result = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'feed': args.feed, 'materialRevision': ledger['revision'], 'coverageComplete': ledger['coverage']['complete'], 'datasets': coverage, 'orders': len(ledger['orders']), 'lots': len(ledger['lots']), 'expectedReceipts': len(ledger['expectedReceipts']), 'actions': len(ledger['actions']), 'stages': {stage: sum(row['stage'] == stage for row in ledger['lots']) for stage in sorted({row['stage'] for row in ledger['lots']})}}
    if not args.feed_only:
        model = read(args.app.rstrip('/')+'/api/model')
        check_ledger(model['materialSupply'])
        assert model['scenario']['supplyMode'] == 'expected'
        assert model['scenario']['allowProposedSupply'] is False
        assert model['materialSupply']['revision'] == ledger['revision'], 'Model has not picked up latest material revision; recheck after cache interval'
        recorded = read(args.app.rstrip('/')+'/api/model', {'supplyMode': 'recorded'})
        assert recorded['scenario']['supplyMode'] == 'recorded'
        assert all(not event['included'] for event in recorded['inboundEvents'] if event['confidence'] == 'estimated')
        result['model'] = {'feedStatus': model['meta']['feedStatus'], 'materialRevision': model['materialSupply']['revision'], 'expectedLitres': model['summary']['plannedLitres'], 'recordedLitres': recorded['summary']['plannedLitres'], 'requiredActions': len(model['materialSupply']['requiredActions'])}
    result['passed'] = True
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
