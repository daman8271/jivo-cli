#!/usr/bin/env python3
"""Isolated browser QA: synthetic sources, real engine/auth/SQLite/AI service."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'service'))
from server import FEEDS, Service, make_server  # noqa: E402

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
LABEL = 'QA fixture • synthetic production data'
SOURCE_LINES = ['JP Machine', 'Clear Pack', '10 Head', '6 Head', 'Tin Head', 'Pouch Machine']


def source_documents():
    current = dt.datetime.now(IST)
    stamp = current.isoformat(timespec='seconds')
    today = current.date()
    day_anchor = today.isoformat() + 'T00:00:00+05:30'
    history = []
    for number in range(1, today.day):
        history.append({'date': today.replace(day=number).isoformat(), 'made_mes_l': 0,
                        'made_booked_l': 0, 'booked_by_item': {}, 'complete': True})
    value = {
        'schemaVersion': 1, 'meta': {'as_of': stamp, 'month': current.strftime('%B %Y'), 'sourceLabel': LABEL},
        'plan': [], 'bom': {}, 'blends': {}, 'items': {}, 'realise': {},
        'opening': {'stock': {}, 'fg': {}, 'fg_other_l': 0, 'standing_l': 0, 'fg_litres': 0},
        'orders': [], 'inbound_prebooked': {}, 'inbound_provenance': {}, 'lines': {},
        'history': {'status': 'complete', 'missing_dates': [], 'days': history},
        'sources': [{'id': 'qa-synthetic-source', 'label': LABEL, 'asOf': stamp, 'ok': True,
                     'note': 'Isolated browser test data. No live production, orders, stock or factory submissions.'}],
        'actual_lines': [], 'notes': [LABEL],
    }
    # Each recipe is explicitly synthetic, in physical pieces and litres. Oil is
    # a shared finite ledger; different carton sizes exercise the case editor.
    specs = [('QA-MUSTARD-1L', 'MUSTARD', 1, 'bottle', 20),
             ('QA-SUNFLOWER-2L', 'SUNFLOWER', 2, 'bottle', 6),
             ('QA-SUNFLOWER-15L', 'SUNFLOWER', 15, 'tin', 1)]
    for code, oil, fill, container, case_count in specs:
        name = f'QA SYNTHETIC {oil} {fill} LTR {case_count} PCS'
        pm, carton = f'PM-{code}', f'PM-CARTON-{code}'
        value['plan'].append({'code': code, 'sku': name, 'category': oil,
                              'pack_type': container.upper(), 'litres_per_piece': fill, 'pieces': 1_000_000})
        value['items'][code] = {'name': name, 'uom': 'PCS'}
        value['items'][pm] = {'name': f'PET BOTTLE {fill} LTR 40 GM' if container == 'bottle' else 'PRINTED TIN 15 LTR', 'uom': 'PCS'}
        value['items'][carton] = {'name': f'CORRUGATED CARTON {case_count} PCS', 'uom': 'PCS'}
        value['bom'][code] = [['RM-QA-OIL', fill], [pm, 1], [carton, 1 / case_count]]
        value['opening']['stock'][pm] = 10_000_000
        value['opening']['stock'][carton] = 10_000_000
        value['realise'][code] = 100
    value['items']['RM-QA-OIL'] = {'name': 'QA SYNTHETIC RECONCILED OIL', 'uom': 'LTR'}
    value['opening']['stock']['RM-QA-OIL'] = 10_000_000
    value['materialSupply'] = {
        'version': 1, 'revision': 'qa-synthetic-material-v1', 'asOf': stamp,
        'coverage': {'complete': True, 'datasets': [{'id': 'qa-exim', 'asOf': stamp,
            'attemptedAt': day_anchor, 'ok': True, 'complete': True, 'expectedRefreshSeconds': 180, 'note': LABEL}]},
        'stock': {'asOf': stamp, 'byItem': dict(value['opening']['stock']),
                  'oilSourcePolicy': 'exim_only', 'byWarehouse': {}, 'excludedWarehouses': [], 'conflicts': []},
        'orders': [], 'lots': [], 'expectedReceipts': [], 'actions': [],
    }
    factory = {'version': 1, 'revision': 'qa-synthetic-factory-v1',
               'attemptedAt': day_anchor, 'asOf': stamp, 'ok': True, 'complete': False,
               'expectedRefreshSeconds': 180, 'date': today.isoformat(), 'error': None,
               'lines': [{'line': line, 'coverage': 'unreported', 'status': 'UNKNOWN',
                          'runs': [], 'note': LABEL + '; no attributed actual observations.'} for line in SOURCE_LINES]}
    return {'input': value, 'factoryNow': factory}


def fetch_fixture(url):
    # No fallback to the network: only the two configured source contracts exist.
    key = next((key for key, feed in FEEDS.items() if feed == url), None)
    if key is None:
        raise ValueError('Fixture only supports the configured input/factory source contracts')
    return source_documents()[key]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8876)
    parser.add_argument('--db', default=os.getenv('MARK5_QA_DB', '/root/mark5-build/fixture.sqlite'))
    args = parser.parse_args()
    os.environ['MARK5_AUTO_AI'] = '0'
    for key in ('MARK5_SERVICE_SECRET', 'MARK5_WEBHOOK_SECRET'):
        if len(os.environ.get(key, '')) < 32:
            raise SystemExit('Load the existing private service environment; secrets are not generated or printed here.')
    service = Service(args.db, project=PROJECT, fetcher=fetch_fixture)
    # Bootstrap through the actual queue and engine, with no engine/AI override.
    queued = service.refresh()['job']['id']
    while service.job(queued)['status'] in ('queued', 'running'):
        if not service.work_one():
            raise RuntimeError('Fixture bootstrap queue did not progress')
    if service.job(queued)['status'] != 'succeeded':
        raise RuntimeError('Fixture bootstrap failed; inspect the isolated service job')
    snap = service.dashboard()
    print(json.dumps({'label': LABEL, 'port': args.port, 'db': args.db,
                      'tomorrow': snap['tomorrow']['date'], 'tomorrowLitres': snap['tomorrow']['totalLitres'],
                      'runs': [{'machine': run['machineId'], 'sku': run['code'], 'piecesPerCase': run['piecesPerCase']}
                               for run in snap['tomorrow']['runs']]}, ensure_ascii=False), flush=True)
    service.start(int(os.getenv('MARK5_QA_POLL_SECONDS', '180')))
    make_server(service, host='127.0.0.1', port=args.port).serve_forever()


if __name__ == '__main__':
    main()
