"""Preserve dated BH stock readings without claiming physical reconciliation."""
import hashlib
import math
from datetime import datetime, timezone

SCOPE = ['BH-BT', 'BH-PF']


def stamp(value):
    if not isinstance(value, str):
        raise ValueError('Missing stock observation timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Stock observation timezone is missing')
    return parsed


def quantity(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError('Stock quantity is unknown or invalid')
    return value


def normalize(raw, previous, now):
    """A later refresh must not give an older physical observation a new date."""
    provenance = raw.get('provenance', {}).get('opening_fg', {})
    note = str(provenance.get('note', ''))
    if provenance.get('source') != 'factory_production' or not all(w in note for w in SCOPE) or 'GP-' in note:
        raise ValueError('Finished-goods warehouse scope is not attested')
    mode = str(provenance.get('mode', ''))
    at = mode.split(' ', 1)[1] if mode.startswith(('carried ', 'last-good ')) else provenance.get('server_at') or provenance.get('fetched_at')
    observed, checked = stamp(at), stamp(now)
    if (observed - checked).total_seconds() > 300:
        raise ValueError('Stock observation is in the future')
    litres = quantity(raw.get('opening', {}).get('fg_litres'))
    entry = {'observedAt': at, 'recordedFgLitres': litres}
    history = [dict(x) for x in (previous or {}).get('snapshots', [])]
    same = [x for x in history if x.get('observedAt') == at]
    if same and any(x.get('recordedFgLitres') != litres for x in same):
        raise ValueError('Stock changed without a new observation timestamp')
    if history and observed < max(stamp(x['observedAt']) for x in history):
        raise ValueError('Stock observation moved backwards')
    if not same:
        history.append(entry)
    history = sorted(history, key=lambda x: stamp(x['observedAt']))[-1000:]
    prior = next((x for x in reversed(history) if stamp(x['observedAt']) < observed), None)
    # Retain the source's assumption explicitly; it is never called physical stock.
    assumed = raw.get('opening', {}).get('standing_l')
    assumed = quantity(assumed) if assumed is not None else None
    result = {
        'version': 1, 'asOf': at, 'attemptedAt': now, 'ok': True,
        'expectedRefreshSeconds': 60, 'expectedObservationSeconds': 3600, 'scope': SCOPE,
        'recordedFgLitres': litres, 'snapshots': history,
        'previousObservation': prior,
        'recordedChangeLitres': litres - prior['recordedFgLitres'] if prior else None,
        'legacyWaitingEstimateLitres': assumed,
        'legacyPlanningPressureLitres': litres + assumed if assumed is not None else None,
        'physicalReconciliation': {
            'complete': False, 'calculatedClosingLitres': None,
            'physicalClosingLitres': None, 'varianceLitres': None,
            'missing': ['Whether stock is deducted at billing, loading or gate departure',
                        'Matched production, transfers, returns and adjustments for the observation interval',
                        'A matching physical closing count including billed goods still inside'],
        },
        'note': 'Factory-recorded FG for BH-BT/BH-PF only. The billed-waiting amount is a legacy mixed-book estimate, not a verified BH physical count. Gate departures must not be subtracted again from a later stock reading.',
        'error': None,
    }
    result['revision'] = hashlib.sha256(repr((at, litres, assumed, history)).encode()).hexdigest()[:24]
    return result


def public_board(value):
    """An allow-list at the publisher door; never expose extra stored fields."""
    if not isinstance(value, dict) or value.get('version') != 1 or value.get('scope') != SCOPE:
        raise ValueError('Stock evidence scope/version invalid')
    stamp(value['asOf']); stamp(value['attemptedAt']); quantity(value['recordedFgLitres'])
    clean = {k: value.get(k) for k in ('version', 'revision', 'asOf', 'attemptedAt', 'ok', 'expectedRefreshSeconds', 'expectedObservationSeconds', 'scope', 'recordedFgLitres', 'recordedChangeLitres', 'legacyWaitingEstimateLitres', 'legacyPlanningPressureLitres')}
    clean['snapshots'] = [{'observedAt': x['observedAt'], 'recordedFgLitres': quantity(x['recordedFgLitres'])} for x in value.get('snapshots', [])[-1000:] if stamp(x['observedAt'])]
    previous = value.get('previousObservation')
    clean['previousObservation'] = {'observedAt': previous['observedAt'], 'recordedFgLitres': quantity(previous['recordedFgLitres'])} if previous else None
    clean['physicalReconciliation'] = {'complete': False, 'calculatedClosingLitres': None, 'physicalClosingLitres': None, 'varianceLitres': None,
        'missing': ['Stock deduction timing', 'Complete movements between matching stock readings', 'Matching physical closing count']}
    clean['note'] = 'Recorded FG: BH-BT/BH-PF only. Legacy billed-waiting estimate is not verified physical stock. Historical departures are not subtracted twice.'
    clean['error'] = None if value.get('ok') is True else 'Stock refresh failed; the last good reading retains its original timestamp.'
    return clean
