"""Elapsed receiving-to-QA timing; source arrival and daily planning are separate."""
from datetime import datetime, timedelta, timezone
from statistics import median

IST = timezone(timedelta(hours=5, minutes=30))


def timestamp(value, date_edge=False):
    if not isinstance(value, str):
        return None
    try:
        if len(value) == 10 and not date_edge:
            return None  # A date cannot measure elapsed QA hours.
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        parsed = parsed.replace(tzinfo=IST) if parsed.tzinfo is None else parsed.astimezone(IST)
        return parsed + timedelta(days=1, microseconds=-1) if len(value) == 10 else parsed
    except (ValueError, TypeError):
        return None


def planning_day(ready):
    # Display date only. The engine reserves materials using the exact readyAt.
    return str(ready.date())


def qa_timing(receipts, supplier, code, unit, as_of):
    now = timestamp(as_of, True)
    samples = []
    for row in receipts:
        raw = row.get('raw', {})
        arrived, accepted = timestamp(row.get('arrivalDate')), timestamp(row.get('qaAcceptedAt'))
        if not supplier or (row.get('supplier'), row.get('code'), row.get('unit')) != (supplier, code, unit):
            continue
        if row.get('stage') not in {'usable', 'accepted_unposted'} or raw.get('cancelled') or raw.get('qcStatus') == 'REJECTED' or float(raw.get('rejectedQty') or 0) > 0 or row.get('quantity', 0) <= 0:
            continue
        if not now or not arrived or not accepted or not now-timedelta(days=90) <= arrived <= accepted <= now:
            continue
        samples.append((row, arrived, (accepted-arrived).total_seconds()/3600))
    if len({s[1].date() for s in samples}) < 3:
        return None
    hours = [s[2] for s in samples]
    return {'medianHours': median(hours), 'minHours': min(hours), 'maxHours': max(hours),
            'sampleCount': len(samples), 'historyFrom': str(min(s[1].date() for s in samples)),
            'historyTo': str(max(s[1].date() for s in samples)), 'evidenceIds': [s[0]['id'] for s in samples]}


def readiness(arrival, timing):
    arrived = timestamp(arrival, True)
    if not arrived:
        return None
    ready = arrived + timedelta(hours=timing['medianHours'])
    return {'sourceArrivalAt': arrival, 'arrivalTimeKnown': len(arrival) > 10,
            'qaMedianHours': timing['medianHours'], 'qaEstimatedAt': ready.isoformat(),
            'storesReleaseAt': None, 'timingVersion': 2, 'readyAt': ready.isoformat(),
            'usableEarliest': planning_day(arrived+timedelta(hours=timing['minHours'])),
            'usableExpected': planning_day(ready),
            'usableLatest': planning_day(arrived+timedelta(hours=timing['maxHours']))}
