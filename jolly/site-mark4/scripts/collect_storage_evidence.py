#!/usr/bin/env python3
"""Archive distinct source observations, without changing any business record."""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from storage_evidence import normalize


def read(path):
    return json.loads(path.read_text())


def collect(source_root, output):
    now = datetime.now(timezone.utc).isoformat()
    try:
        previous = read(output)
    except (OSError, ValueError):
        previous = None
    try:
        value = normalize(read(source_root / 'sim/live-inputs.json'), previous, now)
    except (OSError, ValueError, TypeError, KeyError) as error:
        if not previous:
            raise ValueError('Stock evidence unavailable') from error
        value = {**previous, 'ok': False, 'attemptedAt': now, 'error': 'Refresh failed; original stock timestamp retained.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, separators=(',', ':'), allow_nan=False))
    os.replace(temporary, output)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--interval', type=int, default=60)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    while True:
        try:
            value = collect(args.source_root, args.output)
            print(json.dumps({'ok': value['ok'], 'asOf': value['asOf'], 'snapshots': len(value['snapshots'])}), flush=True)
        except ValueError:
            print(json.dumps({'ok': False, 'error': 'Stock source is unavailable'}), flush=True)
            if args.once:
                raise
        if args.once:
            return
        time.sleep(max(30, args.interval))


if __name__ == '__main__':
    main()
