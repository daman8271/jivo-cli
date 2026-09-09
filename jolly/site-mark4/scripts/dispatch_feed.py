"""Exact public field projection for the separate actual-dispatch board."""
from dispatch_source import instant, label, identifier

TOTALS = ('combinedLitres', 'wellnessLitres', 'martLitres', 'beveragesLitres', 'wellnessStorageLitres',
          'operationalWellnessLitres', 'operationalMartLitres', 'operationalUnclassifiedLitres')


def fields(value, names):
    if not isinstance(value, dict):
        raise ValueError('Dispatch record is invalid')
    return {k: value.get(k) for k in names}


def public_board(value):
    if not isinstance(value, dict) or value.get('version') != 1:
        raise ValueError('Dispatch board version invalid')
    if not instant(value.get('asOf')):
        raise ValueError('No successful dispatch observation exists')
    result = fields(value, ('version', 'ok', 'complete', 'asOf', 'attemptedAt', 'expectedRefreshSeconds'))
    result['sourceUrl'] = 'https://ji.jivo.in/dispatch'
    result['unitNote'] = 'Planning tonnes = recorded litres / 1,000; not measured physical weight.'
    result['scopeNote'] = 'Overall dispatch includes Wellness and Mart; Beverages is separate. Wellness storage includes BH-BT/BH-PF only.'
    result['coverage'] = fields(value.get('coverage'), ('fromDate', 'toDate', 'dateBasis', 'allCompanies', 'listRows', 'pages', 'listComplete', 'queryDateFilter'))
    result['days'] = [fields(row, ('date', 'gateEntryCount', 'tripCount', 'complete') + TOTALS) for row in value.get('days', [])]
    result['trips'] = [fields(row, ('id', 'date', 'departedAt', 'gateEntryIds', 'identityBasis') + TOTALS) for row in value.get('trips', [])]
    result['gateEntries'] = []
    for row in value.get('gateEntries', []):
        entry = fields(row, ('id', 'reference', 'tripId', 'identityBasis', 'company', 'date', 'departedAt', 'litres', 'planningTonnes', 'documentCount', 'wellnessStorageLitres', 'operationalWellnessLitres', 'operationalMartLitres', 'operationalUnclassifiedLitres', 'classificationConflict', 'detailComplete'))
        entry['warehouseLitres'] = [fields(x, ('warehouse', 'litres')) for x in row.get('warehouseLitres', [])]
        entry['items'] = []
        for item in row.get('items', []):
            public = fields(item, ('quantity', 'litres', 'operationalCompany', 'classificationBasis'))
            public.update({k: identifier(item.get(k)) for k in ('code', 'warehouse', 'uom')})
            public['name'] = label(item.get('name'))
            entry['items'].append(public)
        entry['issues'] = [label(x) for x in row.get('issues', [])]
        result['gateEntries'].append(entry)
    result['issues'] = [label(x) for x in value.get('issues', [])]
    if not value.get('ok'):
        result['error'] = 'Dispatch refresh failed; previous evidence retains its original observation time.'
    return result
