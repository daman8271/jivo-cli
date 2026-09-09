"""Exact public routes for owned, sanitized board artifacts; no write endpoint."""
import datetime as dt
import json
import re
from pathlib import Path

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
ROUTES = ('/factory-now.json', '/shift-baseline.json')

def read_board(root, route, now=None):
    date = (now or dt.datetime.now(IST)).astimezone(IST).date().isoformat()
    if root is None: raise ValueError('Board storage unavailable')
    root = Path(root)
    if route in ('/dispatch-now.json', '/storage-evidence.json'):
        path = root / route[1:]
        try:
            if path.stat().st_size > 10_000_000:
                raise ValueError('Board document exceeds limit')
            value = json.loads(path.read_text())
            if route == '/dispatch-now.json':
                from dispatch_feed import public_board
            else:
                from storage_evidence import public_board
            return json.dumps(public_board(value), separators=(',', ':'), allow_nan=False).encode()
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            raise ValueError('Dispatch or storage evidence unavailable')
    match = re.fullmatch(r'/review/(\d{4}-\d{2}-\d{2})/(factory-now|shift-baseline)\.json', route)
    if match:
        requested = dt.date.fromisoformat(match[1])
        if requested > dt.date.fromisoformat(date) or requested < dt.date(2026, 9, 1): raise ValueError('Review date outside recorded period')
        date = requested.isoformat()
        route = '/' + match[2] + '.json'
        file = root / 'reviews' / date / 'factory-now.json' if route == '/factory-now.json' else root / 'baselines' / (date + '.json')
        if route == '/shift-baseline.json' and (root / 'reviews' / date / 'shift-baseline.json').exists():
            file = root / 'reviews' / date / 'shift-baseline.json'
    elif route in ROUTES:
        file = root / 'factory-now.json' if route == '/factory-now.json' else root / 'baselines' / (date + '.json')
    else: raise ValueError('Unknown board route')
    try:
        if file.stat().st_size > 2_000_000: raise ValueError('Board document exceeds limit')
        body = json.loads(file.read_text())
        if not isinstance(body, dict) or body.get('version') != 1: raise ValueError('Board version invalid')
        if route == '/factory-now.json':
            if match and body.get('date') != date: raise ValueError('Archive date mismatch')
            from collect_factory_now import LINES
            if not isinstance(body.get('lines'), list) or any(r.get('line') not in LINES for r in body['lines']): raise ValueError('Board lines invalid')
            fields = ('version','revision','attemptedAt','asOf','ok','complete','expectedRefreshSeconds','date','error')
            clean = {k: body.get(k) for k in fields}
            clean['lines'] = []
            for row in body['lines']:
                r = {k: row.get(k) for k in ('line','coverage','status','note')}
                r['runs'] = []
                for run in row.get('runs', []):
                    x = {k: run.get(k) for k in ('id','code','product','date','sourceUpdatedAt','liveStatus','producedPieces','producedLitres','targetPieces','targetLitres','recordedRunningMinutes','ratedSpeedPiecesPerHour','quantityBasis','firstStartedAt')}
                    segment = run.get('activeSegment')
                    if isinstance(run.get('timingSegments'), list):
                        from collect_factory_now import public_note, timestamp
                        x['timingSegments'] = [{'startedAt': timestamp(s.get('startedAt')), 'endedAt': timestamp(s.get('endedAt')), 'note': public_note(s.get('note'))} for s in run['timingSegments'] if isinstance(s, dict)]
                    x['activeSegment'] = {k: segment.get(k) for k in ('startedAt','endedAt','isActive')} if isinstance(segment, dict) else None
                    r['runs'].append(x)
                clean['lines'].append(r)
        else:
            if body.get('date') != date or body.get('day', {}).get('date') != date or not isinstance(body.get('day', {}).get('runs'), list): raise ValueError('Baseline date invalid')
            clean = {k: body.get(k) for k in ('version','id','date','timeZone','capturedAt','inputAsOf','inputRevision','engineVersion','captureKind','scenario','day','sources','feedStatus')}
            if isinstance(body.get('factoryAtCapture'), dict):
                source = body['factoryAtCapture']
                clean['factoryAtCapture'] = {'asOf': source.get('asOf'), 'complete': source.get('complete') is True, 'lines': [
                    {'line': row.get('line'), 'coverage': row.get('coverage'), 'runs': [
                        {k: run.get(k) for k in ('id','code','pieces')} for run in row.get('runs', [])
                    ]} for row in source.get('lines', [])
                ]}
        return json.dumps(clean, separators=(',', ':'), allow_nan=False).encode()
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        if route == '/shift-baseline.json':
            return json.dumps({'version':1,'date':date,'status':'unavailable','reason':'Today’s original plan has not been saved yet.'}).encode()
        raise ValueError('Current factory records unavailable')
