#!/usr/bin/env python3
"""Rebuild the Amendment-04 audit trail from raw walk _nonget.json with
STRUCTURE-PRESERVING redaction (G6 = redact VALUES not STRUCTURE).

Outputs:
  nonget-allowed.tsv    genuine Flipkart app-fired non-GET reads (query/authz/POST-read)
  nonget-flagged.tsv    non-GET that mutates or whose op TYPE is 'mutation' / path write-verb
  nonget-telemetry.tsv  analytics/telemetry beacons (GA, mixpanel, snoopy, csp, clarity) — noise
Keys, operationName, operationType and enum-ish discriminators stay readable; only
free-text/ids/amounts/tokens and the GraphQL query doc are redacted.
"""
import os, glob, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
TELE = re.compile(r'google-analytics|googletagmanager|googleapis|firebaseinstallations|mixpanel|/snoopyIngestion|csp\.flipkart|clarity\.ms|doubleclick|/collect|nr-data\.net|/track/?$|/engage/?$|trackEvent', re.I)
KEEP_KEY = {'operationName', 'action', 'resource', 'requestId', 'state', 'status', 'type',
            'sortColumn', 'sortOrder', 'listingState', 'orderState', 'page', 'pageSize',
            'businessUnit', 'entity', 'view_id', 'reportId', 'timeGranularity', 'operator',
            'group_by', 'metrics', 'field', 'name', 'function', 'entity_type'}
ENUM = re.compile(r'^[A-Z][A-Z0-9_]{1,48}$')


def redact(v, key=None):
    if isinstance(v, dict):
        return {k: redact(val, k) for k, val in v.items()}
    if isinstance(v, list):
        return [redact(x, key) for x in v][:12]
    if isinstance(v, str):
        if key in ('operationName', 'operationType'):
            return v
        if key == 'query' or key == 'mutation':
            return '<gql-doc>'
        if key in KEEP_KEY or ENUM.match(v) or (len(v) <= 24 and not re.search(r'\d{4,}', v)):
            return v
        return '<redacted>'
    if isinstance(v, (int, float, bool)) or v is None:
        return v
    return '<redacted>'


def op_type(body_str):
    # look at the query doc for the leading operation keyword
    m = re.search(r'"query"\s*:\s*"\s*(query|mutation|subscription)\b', body_str)
    if m:
        return m.group(1)
    if re.search(r'\bmutation\b', body_str):
        return 'mutation?'
    return 'query?' if 'graphql' in body_str.lower() or '"operationName"' in body_str else 'n/a'


def shape(body_str):
    try:
        j = json.loads(body_str)
        return json.dumps(redact(j), separators=(',', ':'))[:400]
    except Exception:
        # not JSON (truncated / form) — redact long tokens only
        return re.sub(r'(?=[A-Za-z0-9_\-]*\d)[A-Za-z0-9_\-]{16,}', '<redacted>', body_str)[:220]


allowed, flagged, tele = [], [], []
seen = set()
for nf in sorted(glob.glob(os.path.join(HERE, '*-walk', '_nonget.json'))):
    group = os.path.basename(os.path.dirname(nf)).replace('-walk', '')
    for r in json.load(open(nf)):
        url = r.get('url', ''); meth = r.get('method', ''); body = r.get('body', '') or ''
        path = re.sub(r'\?.*', '', url)
        opname = ''
        m = re.search(r'"operationName"\s*:\s*"([^"]*)"', body)
        if m:
            opname = m.group(1)
        key = (meth, path, opname)
        if key in seen:
            continue
        seen.add(key)
        if TELE.search(url):
            tele.append((group, meth, url))
            continue
        ot = op_type(body) if 'graphql' in url else 'n/a'
        sh = shape(body)
        row = (group, meth, url, opname, ot, sh)
        # mutation if the op type is mutation, or the path carries a write verb
        seg = set(re.split(r'[-_/]', path.lower()))
        pathmut = bool(seg & {'create', 'update', 'delete', 'submit', 'approve', 'upload',
                              'cancel', 'activate', 'suspend', 'generate', 'settle', 'pay'})
        if ot.startswith('mutation') or pathmut:
            flagged.append(row)
        else:
            allowed.append(row)

with open(os.path.join(HERE, 'nonget-allowed.tsv'), 'w') as fh:
    fh.write('group\tmethod\turl\toperationName\top_type\tbody_shape_redacted\n')
    for g, m, u, o, t, s in allowed:
        fh.write(f'{g}\t{m}\t{u}\t{o}\t{t}\t{s}\n')
with open(os.path.join(HERE, 'nonget-flagged.tsv'), 'w') as fh:
    fh.write('group\tmethod\turl\toperationName\top_type\tbody_shape_redacted\treason\n')
    for g, m, u, o, t, s in flagged:
        fh.write(f'{g}\t{m}\t{u}\t{o}\t{t}\t{s}\tmutation-type-or-write-verb\n')
with open(os.path.join(HERE, 'nonget-telemetry.tsv'), 'w') as fh:
    fh.write('group\tmethod\turl\n')
    for g, m, u in tele:
        fh.write(f'{g}\t{m}\t{u}\n')

print(f'allowed (reads): {len(allowed)}  flagged (mutation/write): {len(flagged)}  telemetry: {len(tele)}')
if flagged:
    print('FLAGGED:')
    for g, m, u, o, t, s in flagged:
        print(f'  [{g}] {m} {u}  op={o} type={t}')
