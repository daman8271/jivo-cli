#!/usr/bin/env python3
"""Independent factory gate GET collector. Full list pagination; private detail cache."""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import ssl
import time
import tomllib
import urllib.parse
import urllib.request
from collect_factory_supplement import NoRedirect, atomic, load, stamp
from dispatch_source import IST, eligible, normalize, normalize_entry, read_all

class DispatchFactory:
    def __init__(self, config):
        self.config = Path(config)
        self.ssl = ssl.create_default_context()
    def get(self, path, params=None):
        if not re.fullmatch(r'/gate-core/sales-dispatch/(?:\d+/)?', path): raise ValueError('Unapproved dispatch endpoint')
        config = tomllib.loads(self.config.read_text())
        base = urllib.parse.urlsplit(config['base_url'])
        if base.scheme != 'https' or base.hostname not in {'factory.jivo.in', 'ji.jivo.in'} or base.port not in (None, 443) or base.username or base.password or base.query or base.fragment or base.path.rstrip('/') != '/api/v1': raise ValueError('Factory origin refused')
        url = config['base_url'].rstrip('/') + path
        if params: url += '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + config['access_token'], 'Company-Code': 'JIVO_OIL'}, method='GET')
        opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=self.ssl))
        with opener.open(req, timeout=30) as response:
            data = response.read(16*1024*1024+1)
            if len(data) > 16*1024*1024: raise ValueError('Factory response too large')
            return json.loads(data)

def collect(client, cache, now, workers=6):
    today = dt.datetime.fromisoformat(now).astimezone(IST).date()
    start = str(min(today.replace(day=1), today-dt.timedelta(days=1)))
    end = str(today)
    rows, pages = read_all(client)
    selected = [r for r in rows if eligible(r, start, end)]
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True); cache.chmod(0o700)
    def detail(row):
        key = str(row['id']); target = cache / ('gate-'+key+'.json')
        fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        old = load(target) if target.exists() else None
        recent = row['gate_out_date'] >= str(today-dt.timedelta(days=1))
        limit = 60 if recent else 43200
        if old and old.get('fingerprint') == fingerprint and time.time()-dt.datetime.fromisoformat(old['asOf']).timestamp() < limit:
            return key, old['data']
        data = client.get('/gate-core/sales-dispatch/'+key+'/')
        normalize_entry(row, data)  # Never poison the cache with a list/detail race.
        atomic(target, {'asOf': stamp(), 'fingerprint': fingerprint, 'data': data})
        return key, data
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        details = dict(pool.map(detail, selected))
    result = normalize(rows, details, stamp(), start, end, pages)
    result['attemptedAt'] = now
    return result

def run_once(client, cache, output, workers=6):
    attempted = stamp()
    previous = load(output) if Path(output).exists() else None
    try:
        result = collect(client, cache, attempted, workers)
    except Exception as exc:
        result = {**(previous or {'version': 1, 'asOf': None, 'days': [], 'gateEntries': [], 'trips': []}),
                  'ok': False, 'complete': False, 'attemptedAt': attempted, 'expectedRefreshSeconds': 60,
                  'error': 'Dispatch refresh failed ('+type(exc).__name__+'); last successful evidence retained. Missing data is not zero.'}
    atomic(output, result)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--cache-dir', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--interval', type=int, default=60)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    client = DispatchFactory(args.config)
    while True:
        result = run_once(client, args.cache_dir, args.output, args.workers)
        print(json.dumps({'ok': result['ok'], 'complete': result['complete'], 'asOf': result['asOf'], 'gateEntries': len(result.get('gateEntries', []))}), flush=True)
        if args.once: return 0 if result['ok'] else 1
        time.sleep(max(30, args.interval))
if __name__ == '__main__': raise SystemExit(main())
