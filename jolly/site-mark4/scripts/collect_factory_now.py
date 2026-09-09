#!/usr/bin/env python3
"""Small, isolated, minutely factory read. Never infer activity from IN_PROGRESS.

Only the sanitized document is published. CLI reads explicitly require the live
API, disable its cache, and carry Oil company scope. No business write commands.
"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import tempfile

UTC = dt.timezone.utc
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
LINES = ('JP Machine', 'Clear Pack', '10 Head', '6 Head', 'Tin Head', 'Pouch Machine')
CODE = re.compile(r'^FG[A-Z0-9]{5,20}$')

def stamp():
    return dt.datetime.now(UTC).isoformat()

def timestamp(value):
    if not isinstance(value, str): return None
    try:
        d = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value if d.tzinfo else None
    except ValueError: return None

def time_key(value):
    valid = timestamp(value)
    return dt.datetime.fromisoformat(valid.replace('Z', '+00:00')).timestamp() if valid else float('-inf')

def number(value):
    if isinstance(value, bool) or value is None: return None
    try:
        n = float(value)
        return n if math.isfinite(n) and n >= 0 else None
    except (ValueError, TypeError): return None

def public_name(value):
    if not isinstance(value, str): return None
    value = re.sub(r'https?://\S+|[\w.+-]+@[\w.-]+\.\w+|(?:/Users/|/root/|/home/)\S*|\+?\d[\d ()-]{8,}\d', '[redacted]', value)
    return value[:180]

def public_note(value):
    # Remarks are free text and can name people. Publish only a narrow set of
    # operational labels; identity-bearing or unrecognised text stays private.
    if not isinstance(value, str) or not value.strip(): return None
    label = value.strip().lower()
    if re.fullmatch(r'(tea|lunch)( time| break)?|colse|close|closed|break|breakdown|power cut|power failure|cleaning|changeover', label):
        return label
    return 'Other remark withheld'

def normalize(today_rows, open_rows, yesterday_rows, now):
    current = dt.datetime.fromisoformat(now).astimezone(IST).date()
    date = str(current)
    if any(not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows) for rows in (today_rows, open_rows, yesterday_rows)):
        raise ValueError('Unexpected factory response shape')
    if any(r.get('date') != date for r in today_rows):
        raise ValueError('Factory ignored requested production date')
    open_by_id = {str(r.get('id')): r for r in open_rows}
    old_open = [r for r in open_rows if r.get('date') != date]
    result = []
    for line in LINES:
        rows = []
        conflict = False
        for r in today_rows:
            if r.get('line_name') != line: continue
            segments = r.get('segments')
            if not isinstance(segments, list):
                conflict = True
                segments = []
            active = [s for s in segments if s.get('is_active') is True and s.get('end_time') is None]
            if any(s.get('is_active') is True and s.get('end_time') is not None for s in segments) or len(active) > 1:
                conflict = True
            header = open_by_id.get(str(r.get('id')))
            live = header.get('live_status') if header else None
            header_matches = bool(header and all(header.get(k) == r.get(k) for k in ('date', 'line_name', 'item_code')))
            if header and not header_matches: conflict = True
            state = 'UNKNOWN'
            if r.get('status') == 'COMPLETED' and not active:
                state = 'COMPLETED'
            elif r.get('status') == 'DRAFT' and not active:
                state = 'NOT_STARTED'
            elif r.get('status') == 'IN_PROGRESS' and header_matches and live == 'RUNNING' and len(active) == 1:
                state = 'RUNNING'
            elif r.get('status') == 'IN_PROGRESS' and header_matches and live in ('STOPPED', 'PAUSED', 'BREAKDOWN') and not active:
                state = live
            else:
                conflict = True
            breakdowns = r.get('breakdowns', [])
            if not isinstance(breakdowns, list): conflict = True
            elif any(b.get('start_time') and b.get('end_time') is None for b in breakdowns):
                if active: conflict = True
                else: state = 'BREAKDOWN'
            qty = [number(s.get('produced_cases')) for s in segments]
            ppc, lpp = number(r.get('pieces_per_case')), number(r.get('litres_per_piece'))
            pieces = sum(qty) * ppc if all(q is not None for q in qty) and ppc is not None and ppc > 0 else None
            litres = pieces * lpp if pieces is not None and lpp is not None and lpp > 0 else None
            # Factory production-run required_qty is CASES (adapter contract),
            # whereas every board quantity is pieces or litres. A target is an
            # operator instruction, never a promise of eventual output.
            target_cases = number(r.get('required_qty'))
            target_pieces = target_cases * ppc if target_cases is not None and ppc is not None and ppc > 0 else None
            target_litres = target_pieces * lpp if target_pieces is not None and lpp is not None and lpp > 0 else None
            # Run-header totals are only rolled up at close. Sum the recorded
            # closed-segment minutes instead; never count an open segment's zero
            # as elapsed time or extrapolate a finish from operator-entered speed.
            closed = [s for s in segments if s.get('is_active') is False and timestamp(s.get('end_time'))]
            durations = [number(s.get('duration_minutes')) for s in closed]
            duration_complete = isinstance(r.get('segments'), list) and all(
                (s.get('is_active') is True and s.get('end_time') is None) or s in closed for s in segments)
            recorded_minutes = sum(durations) if duration_complete and all(n is not None for n in durations) else None
            latest = max((timestamp(v) for v in [r.get('updated_at'), *[s.get('updated_at') for s in segments]] if timestamp(v)), key=time_key, default=None)
            chosen = active[0] if active else max(segments, key=lambda s: time_key(s.get('start_time')), default=None)
            if active:
                started = timestamp(active[0].get('start_time'))
                if not started or not latest:
                    conflict = True
                else:
                    event = dt.datetime.fromisoformat(started.replace('Z', '+00:00'))
                    edited = dt.datetime.fromisoformat(latest.replace('Z', '+00:00'))
                    instant = dt.datetime.fromisoformat(now)
                    if event.astimezone(IST).date() != current or edited < event or max(event, edited) > instant + dt.timedelta(seconds=30): conflict = True
            code = r.get('item_code') if isinstance(r.get('item_code'), str) and CODE.fullmatch(r['item_code']) else None
            rows.append({'id': hashlib.sha256(('factory-run:' + str(r.get('id'))).encode()).hexdigest()[:20],
                         'code': code, 'product': public_name(r.get('product')), 'date': date,
                         'sourceUpdatedAt': latest, 'liveStatus': state,
                         'firstStartedAt': min((timestamp(s.get('start_time')) for s in segments if timestamp(s.get('start_time'))), key=time_key, default=None),
                         'timingSegments': [{'startedAt': timestamp(s.get('start_time')), 'endedAt': timestamp(s.get('end_time')), 'note': public_note(s.get('remarks'))} for s in segments],
                         'activeSegment': {'startedAt': timestamp(chosen.get('start_time')), 'endedAt': timestamp(chosen.get('end_time')), 'isActive': chosen.get('is_active') is True} if chosen else None,
                         'producedPieces': pieces, 'producedLitres': litres,
                         'targetPieces': target_pieces, 'targetLitres': target_litres,
                         'recordedRunningMinutes': recorded_minutes,
                         # Source run rated_speed is pieces/hour, already independent of carton size.
                         'ratedSpeedPiecesPerHour': number(r.get('rated_speed')),
                         'quantityBasis': 'Recorded segment cases × factory pieces per case; open segments can have unrecorded output.'})
        running = [r for r in rows if r['liveStatus'] == 'RUNNING']
        if len(running) > 1: conflict = True
        # A list/detail race is unresolved until the next read, never silently ignored.
        known_ids = {str(r.get('id')) for r in today_rows}
        if any(r.get('line_name') == line and r.get('date') == date and str(r.get('id')) not in known_ids for r in open_rows): conflict = True
        # Yesterday can be a real overnight shift. Older open headers are known
        # abandoned records, not evidence against a current dated active segment.
        previous_date = str(current - dt.timedelta(days=1))
        prior_running = [r for r in old_open if r.get('line_name') == line and r.get('date') == previous_date and r.get('live_status') == 'RUNNING']
        if prior_running: conflict = True
        rows.sort(key=lambda r: (r['liveStatus'] == 'RUNNING', time_key(r['sourceUpdatedAt'])), reverse=True)
        reported = [r for r in rows if r['liveStatus'] != 'NOT_STARTED']
        coverage = 'conflict' if conflict else 'reported' if reported else 'unreported'
        status = 'UNKNOWN' if conflict or not reported else 'RUNNING' if running else reported[0]['liveStatus']
        note = 'Factory-reported state, not a machine sensor. Quantities are recorded output, not a live counter.'
        if not reported: note = 'No started run reported for this machine today. This does not prove the machine is idle.'
        if conflict: note = 'Factory status and timing records need checking; current activity cannot be verified.'
        if prior_running: note += ' A prior-day run is still marked running; confirm whether it continued overnight.'
        stale_count = sum(r.get('line_name') == line for r in old_open)
        if stale_count: note += f' {stale_count} prior-day open record(s) excluded from today.'
        result.append({'line': line, 'coverage': coverage, 'status': status, 'runs': rows, 'note': note})
    core = {'version': 1, 'date': date, 'attemptedAt': now, 'asOf': now, 'ok': True, 'complete': True,
            'expectedRefreshSeconds': 60, 'lines': result, 'error': None}
    core['revision'] = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()[:24]
    return core

def read_cli(args, command):
    cmd = [args.cli, *command, '--company', 'JIVO_OIL', '--config', args.config,
           '--data-source', 'live', '--no-cache', '--json', '--timeout', '12s']
    done = subprocess.run(cmd, capture_output=True, timeout=18)
    if done.returncode or len(done.stdout) > 8_000_000:
        raise ValueError('Factory live read failed')
    payload = json.loads(done.stdout)
    if not isinstance(payload, dict) or payload.get('meta', {}).get('source') != 'live':
        raise ValueError('Factory response is not attested live')
    return payload.get('results')

def collect(args):
    date = dt.datetime.now(IST).date()
    commands = [
        ['production-execution', 'reports-daily-production', '--date', str(date)],
        ['production-execution', 'runs', '--status', 'IN_PROGRESS'],
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        today, opened = list(pool.map(lambda command: read_cli(args, command), commands))
    now = stamp()
    if dt.datetime.fromisoformat(now).astimezone(IST).date() != date:
        raise ValueError('Factory read crossed midnight; retry next cycle')
    return normalize(today, opened, [], now)

def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, separators=(',', ':'), allow_nan=False))
    os.chmod(temp, 0o600)
    temp.replace(path)

def archive_previous(output, next_value):
    # Publish complete bytes with an exclusive hard link. If archival fails,
    # leave the old current file intact so the next worker can retry rollover.
    try:
        previous = json.loads(Path(output).read_text())
    except FileNotFoundError:
        return
    old_date = dt.date.fromisoformat(previous['date'])
    if old_date >= dt.date.fromisoformat(next_value['date']) or not timestamp(previous.get('asOf')): return
    destination = Path(output).parent / 'reviews' / old_date.isoformat() / 'factory-now.json'
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = json.dumps(previous, separators=(',', ':'), allow_nan=False)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=destination.parent, prefix='.factory-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            pass  # A preserved day is immutable, including the user-saved copy.
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cli', required=True)
    p.add_argument('--config', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--interval', type=int, default=60)
    args = p.parse_args()
    while True:
        began = time.monotonic()
        try:
            value = collect(args)
        except Exception:
            try: previous = json.loads(Path(args.output).read_text())
            except (OSError, ValueError): previous = {'version': 1, 'date': str(dt.datetime.now(IST).date()), 'asOf': None, 'lines': [], 'revision': 'unavailable', 'expectedRefreshSeconds': 60}
            value = {**previous, 'attemptedAt': stamp(), 'ok': False, 'complete': False, 'error': 'Factory read failed. Previous records retain their original dates.'}
        archive_previous(args.output, value)
        atomic(args.output, value)
        print(json.dumps({'ok': value['ok'], 'asOf': value['asOf'], 'attemptedAt': value['attemptedAt'], 'seconds': round(time.monotonic() - began, 2)}), flush=True)
        if not args.interval: break
        time.sleep(max(1, args.interval - (time.monotonic() - began)))

if __name__ == '__main__': main()
