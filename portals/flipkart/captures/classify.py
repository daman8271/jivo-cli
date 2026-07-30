#!/usr/bin/env python3
"""PHASE 3+4 — precise extraction + classification of the Flipkart API surface.

READ-ONLY: parses the on-disk JS corpus only. No network.
Supersedes extract.py. Produces:
  endpoints-raw.tsv        surface | method | host | path | const | evidence_file
  wired-reads.tsv          READ + READ_FILE rows (safe to expose)
  writes-excluded.tsv      WRITE + EXPORT rows (documented, never wired)
  unknown-excluded.tsv     UNKNOWN rows (denied per G1, documented)
  sections.json            section -> [rows]  (business clustering)
  routes-raw.txt           surface | route
"""
import re, os, glob, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
JS = os.path.join(HERE, 'js')

# ---- path detection ----
# Accept only strings that look like an API path or a full API URL.
FULLURL_RE = re.compile(r'https?://([a-z0-9.-]+\.(?:flipkart\.(?:com|net)|flixcart\.com))(/[A-Za-z0-9_\-./:%~${}]*)')
LIT_RE = re.compile(r'["\'`]((?:/)?(?:napi|fed-ads|vendor|vendor-p|vendor-portal|api|v[0-9]|retail-palantir|triton|ryuk|oauth-service|sellers)[A-Za-z0-9_\-./:%~${}]{1,140})["\'`]')
ROUTE_RE = re.compile(r'["\'`](#?/[a-zA-Z][A-Za-z0-9_\-/:]{1,80})["\'`]')

JUNK = re.compile(
    r'\.(js|css|png|jpe?g|svg|gif|woff2?|ttf|eot|ico|map|html?|json|webp|mp4|pdf|txt|xlsx?|csv|zip)(\?|$|#)'
    r'|[<>\\|^`\s]'
    r'|/fk-sp-static/|/fk-p-fk-|node_modules|/api-docs/', re.I)

# A real endpoint path must begin with one of these API prefixes (after normalisation).
# This drops single-word marketing/i18n literals like /seller-blog, /api_hosts, /vendor_name_.
API_PREFIXES = ('/napi/', '/fed-ads/', '/vendor/', '/vendor-p/', '/vendor-portal/',
                '/api/', '/v1/', '/v2/', '/v3/', '/v0/', '/retail-palantir/', '/triton/',
                '/ryuk/', '/oauth-service/', '/sellers/', '/listings/', '/reports/',
                '/ads-bff/', '/snoopyIngestion/')


def is_real_api(p):
    if any(p.startswith(x) for x in API_PREFIXES):
        return True
    # full 3rd-party api host paths already carry host; accept if >=2 segments w/ api marker
    if re.search(r'^/[a-z0-9-]+/(?:v[0-9]|api)/', p):
        return True
    return False

# static-asset hosts (not API) to drop from full-URL matches
ASSET_HOSTS = ('static-assets-web.flixcart.com', 'retail.flixcart.com', 'img1a.flixcart.com',
               'rukmini', 'img.fkcdn', 'sdorigin')

WRITE_VERBS = ('create', 'update', 'delete', 'remove', 'submit', 'approve', 'reject',
               'acknowledge', 'confirm', 'accept', 'decline', 'cancel', 'add-', '/add',
               'edit', 'save', 'upload', 'import', 'activate', 'suspend', 'deactivate',
               'enable', 'disable', 'pause', 'resume', 'pay', 'settle', 'dispute', 'adjust',
               'raise', 'claim', 'invite', 'change-password', 'update-user', 'reinvite',
               'send-mail', 'send_', 'book', 'schedule', 'assign', 'mark-', 'set-', 'toggle',
               'register', 'generate')
EXPORT_VERBS = ('generatereport', 'report/generate', 'analytics/report', 'analytics/sales-report',
                'downloadreport', 'export', 'enqueue', 'request-report')
READFILE_VERBS = ('download', 'getfile', 'getdocument', 'download-file', 'download-feed',
                  'feed-download', 'invoice-debit-download', 'certificate', 'static-documents',
                  '/label', '/invoice', '/manifest')
READ_VERBS = ('list', 'get', 'fetch', 'search', 'summary', 'detail', 'view', 'dashboard',
              'count', 'filter', 'browse', 'categories', 'category', 'metrics', 'trends',
              'performance', 'profile', 'config', 'status', 'info', 'data', 'roles',
              'vendor-list', 'users/active', 'users/suspended', 'aggregate', 'available',
              'listing', 'reportcategories', 'getreports', 'query', 'stat')

# proven-by-JIVO reads/writes (from seed intel) — authoritative overrides
PROVEN = {
    '/napi/metrics/bizReport/reportCategories': 'READ',
    '/napi/metrics/bizReport/report/checkReports': 'READ',
    '/napi/metrics/bizReport/report/generateReport': 'EXPORT',   # enqueue = WRITE
    '/napi/metrics/bizReport/downloadReport/earn_more_report.xlsx': 'READ_FILE',
    '/napi/metrics/bizReport/report/getReportsV2': 'READ',        # POST-read
    '/napi/metrics/bizReport/getReportsCount': 'READ',            # POST-read
    '/napi/graphql': 'READ',                                      # POST-read (query)
    '/napi/printing/certificate': 'READ',
    '/napi/printing/signature': 'READ',
    '/napi/sellerBuyerCommunications/getChatKey': 'READ',
    '/fed-ads/downloadV2': 'EXPORT',                              # POST returns CSV = export
    '/fed-ads/download/table': 'EXPORT',
    '/vendor/user-management/vendor-list': 'READ',
    '/vendor/purchase-orders': 'READ',
    '/vendor/purchase-order-download': 'READ_FILE',
    '/vendor/analytics/report': 'EXPORT',
    '/vendor/analytics/sales-report': 'EXPORT',
    '/vendor-p/getFile/v1/retail/documents/{id}/download': 'READ_FILE',
    '/vendor/user-management/user-activation/activate': 'WRITE',
    '/vendor/user-management/user-activation/suspend': 'WRITE',
    '/vendor/cataloging/create-fsn': 'WRITE',
    '/vendor/feeds/upload-feed-file': 'WRITE',
    '/vendor/user-management/change-password': 'WRITE',
    '/vendor/user-management/update-user': 'WRITE',
    '/vendor/support/send-mail': 'WRITE',
    '/login': 'WRITE',           # the one authorized login POST — not a data read
    '/select-vendor': 'WRITE',
    '/v1/token/refresh': 'WRITE',
    # --- PROVEN READ live this session (HTTP 200 read-only GET on 2026-07-30) ---
    # These override the auto-classifier, which conservatively tagged some as
    # WRITE (e.g. "users/suspended" hit the "suspend" verb) or UNKNOWN.
    '/vendor/user-management/vendor-list': 'READ',
    '/vendor/user-management/profile/my': 'READ',
    '/vendor/user-management/profile': 'READ',
    '/vendor/user-management/users/active': 'READ',
    '/vendor/user-management/users/suspended': 'READ',
    '/vendor/user-management/roles-and-warehouses': 'READ',
    '/vendor/user-management/user': 'READ',
    '/vendor/user-management/user-data': 'READ',
    '/vendor/uam/isResourcesAuthorised': 'READ',
    '/vendor/aggregate-entities': 'READ',
    '/vendor/config/sale-config': 'READ',
    '/vendor/cataloging/browse-tree': 'READ',
    '/vendor/cataloging/feed-list': 'READ',
    '/vendor/qc-norms/bis-list': 'READ',
    '/vendor/ticketPortalUrl': 'READ',
    '/vendor/operational-performance': 'READ',
    '/vendor/purchasing-trends': 'READ',
    '/vendor/purchase-orders-summary': 'READ',   # 400 w/o params, but a read
    '/vendor/return-orders-summary': 'READ',      # 500 w/o params, but a read
}


def normpath(p):
    if not p.startswith('/'):
        p = '/' + p
    p = re.sub(r'/{2,}', '/', p)
    p = p.rstrip('.,')
    # normalise template params to {id}
    p = re.sub(r'\$\{[^}]+\}', '{id}', p)
    p = re.sub(r':\w+', '{id}', p)
    return p


def classify(path, method):
    key = path
    if key in PROVEN:
        return PROVEN[key]
    pl = path.lower()
    # method-driven
    if method in ('PUT', 'PATCH', 'DELETE'):
        return 'WRITE'
    if any(v in pl for v in EXPORT_VERBS):
        return 'EXPORT'
    if any(v in pl for v in WRITE_VERBS):
        return 'WRITE'
    if any(v in pl for v in READFILE_VERBS):
        return 'READ_FILE'
    if method == 'GET':
        return 'READ'
    if any(v in pl for v in READ_VERBS) and method in ('GET', 'UNKNOWN'):
        return 'READ' if method == 'GET' else 'UNKNOWN_READLIKE'
    return 'UNKNOWN'


def surface_of(f):
    return 'vendorhub' if '/vendorhub/' in f else 'seller'


def host_for(surface, full_host=None):
    if full_host:
        return full_host
    return 'vendorhub.flipkart.com' if surface == 'vendorhub' else 'seller.flipkart.com'


def nearest_const(text, pos):
    win = text[max(0, pos - 140):pos]
    for pat in (r'([A-Z][A-Z0-9_]{3,60})\s*[:=]\s*[`"\']?$',
                r'([a-zA-Z_$][\w$]{2,50})\s*[:=]\s*[`"\']?$'):
        m = re.search(pat, win)
        if m:
            return m.group(1)
    return ''


def nearest_method(text, pos):
    win = text[max(0, pos - 220):pos + 220]
    votes = collections.Counter()
    for m in re.finditer(r'method\s*[:=]\s*["\'](get|post|put|patch|delete)["\']', win, re.I):
        votes[m.group(1).upper()] += 2
    for m in re.finditer(r'\b[a-zA-Z]{1,4}\.(get|post|put|patch|delete)\s*\(', win):
        votes[m.group(1).upper()] += 1
    for m in re.finditer(r'\b(doHttpGet|doGet|httpGet)\b', win):
        votes['GET'] += 2
    for m in re.finditer(r'\b(doHttpPost|doPost|httpPost)\b', win):
        votes['POST'] += 2
    return votes.most_common(1)[0][0] if votes else 'UNKNOWN'


def main():
    files = sorted(glob.glob(os.path.join(JS, 'seller', '*.js')) +
                   glob.glob(os.path.join(JS, 'vendorhub', '*.js')))
    rows = {}   # (surface,host,path) -> [method, const, file]
    routes = set()
    for f in files:
        surface = surface_of(f)
        base = os.path.basename(f)
        s = open(f, encoding='utf-8', errors='replace').read()

        def add(host, raw, pos):
            if JUNK.search(raw):
                return
            p = normpath(raw)
            if len(p) < 5 or not re.search(r'[A-Za-z]{3}', p):
                return
            if not is_real_api(p):
                return
            k = (surface, host, p)
            meth = nearest_method(s, pos)
            if k not in rows:
                rows[k] = [meth, nearest_const(s, pos), base]
            elif rows[k][0] == 'UNKNOWN' and meth != 'UNKNOWN':
                rows[k][0] = meth

        for m in LIT_RE.finditer(s):
            add(host_for(surface), m.group(1), m.start())
        for m in FULLURL_RE.finditer(s):
            h, p = m.group(1), m.group(2)
            if any(a in h for a in ASSET_HOSTS):
                continue
            add(h, p, m.start())
        for m in ROUTE_RE.finditer(s):
            r = m.group(1)
            if JUNK.search(r) or re.search(r'/(napi|fed-ads|api|v[0-9])/', r):
                continue
            routes.add((surface, r))

    # write outputs
    with open(os.path.join(HERE, 'endpoints-raw.tsv'), 'w') as fh:
        fh.write('surface\tmethod\thost\tpath\tclass\tconst\tevidence_file\n')
        for (surface, host, p), (meth, const, base) in sorted(rows.items()):
            cls = classify(p, meth)
            fh.write(f'{surface}\t{meth}\t{host}\t{p}\t{cls}\t{const}\t{base}\n')

    # partitions + sections
    part = collections.defaultdict(list)
    sections = collections.defaultdict(list)
    for (surface, host, p), (meth, const, base) in sorted(rows.items()):
        cls = classify(p, meth)
        rec = {'surface': surface, 'method': meth, 'host': host, 'path': p,
               'class': cls, 'const': const, 'file': base}
        bucket = 'read' if cls in ('READ', 'READ_FILE') else (
            'write' if cls in ('WRITE', 'EXPORT') else 'unknown')
        part[bucket].append(rec)
        sections[section_of(surface, host, p)].append(rec)

    def dump(name, recs):
        with open(os.path.join(HERE, name), 'w') as fh:
            fh.write('surface\tmethod\thost\tpath\tclass\tconst\tfile\n')
            for r in recs:
                fh.write('\t'.join(str(r[k]) for k in ('surface', 'method', 'host', 'path', 'class', 'const', 'file')) + '\n')
    dump('wired-reads.tsv', part['read'])
    dump('writes-excluded.tsv', part['write'])
    dump('unknown-excluded.tsv', part['unknown'])
    json.dump({k: v for k, v in sections.items()}, open(os.path.join(HERE, 'sections.json'), 'w'), indent=1)

    with open(os.path.join(HERE, 'routes-raw.txt'), 'w') as fh:
        fh.write('surface\troute\n')
        for surface, r in sorted(routes):
            fh.write(f'{surface}\t{r}\n')

    print('distinct endpoints:', len(rows))
    print('by class:', dict(collections.Counter(classify(p, rows[(su, h, p)][0]) for (su, h, p) in rows)))
    print('read-safe:', len(part['read']), ' write/export:', len(part['write']), ' unknown:', len(part['unknown']))
    print('routes:', len(routes))
    print('sections:', {k: len(v) for k, v in sorted(sections.items())})


SECTION_MAP_SELLER = [
    ('report-centre', ('/napi/metrics/bizreport', 'reportcategories', 'getreports', 'bizreport', 'tally-reports')),
    ('ads-fed', ('/fed-ads', 'fkpromo', 'flipkart-ads')),
    ('graphql', ('/napi/graphql',)),
    ('printing', ('/napi/printing',)),
    ('communications', ('sellerbuyercommunications', '/napi/sbc', 'case-manager', 'notifications')),
    ('orders-shipments', ('/napi/orders', '/napi/my-orders', '/napi/shipments', '/napi/selfship',
                          '/napi/consignment', '/napi/putlist', 'fulfilment-rest')),
    ('fulfilment-fbf', ('/napi/fbf', '/napi/fbflite', 'fbfLite'.lower())),
    ('listings-catalog', ('/napi/listing', 'listingsmanagement', '/listings', 'createproductv2',
                          'edit-product', 'seller-products', 'alphalisting', 'image-enricher',
                          'cataloging', '/napi/document', 'catalogue')),
    ('pricing-ratecard', ('/napi/pricing', 'pricemanagement', 'ratecard', 'rate-card', 'price-scheduling')),
    ('inventory-stock', ('unifiedinventory', 'inventoryhealth', '/napi/inventory', '/napi/sfx', 'srm')),
    ('payments-finance', ('/napi/payment', '/payment', 'tds', 'partner-master', 'settlement')),
    ('returns-recall', ('/napi/returns', '/return', '/napi/recall')),
    ('promotions', ('/napi/promotions', 'promotion')),
    ('lending-capital', ('/napi/lending', 'lending', 'fkgrowthcapital', 'growthcapital')),
    ('seller-qna-ugc', ('sellerqna', 'qna', '/napi/ugc')),
    ('onboarding', ('selleronboarding', 'onboarding', '/spf', 'partnerservices')),
    ('profile-account', ('manageprofile', '/napi/profile', 'multiseller', 'partnerpermissions', '/napi/myp')),
    ('growth-insights', ('/napi/sir', 'insights', 'guidedassistance', 'gamification', '/napi/ga',
                         'ga-content-manager', 'riddler', 'yoda', '/napi/welcome', 'grow')),
    ('compliance-regulation', ('/napi/regulation', '/napi/audit', 'approval-store', 'compliance')),
    ('coe', ('/coe',)),
]
SECTION_MAP_VENDOR = [
    ('vendor-purchase-orders', ('purchase-order', 'purchase-orders', '/po', 'grn')),
    ('vendor-analytics', ('/vendor/analytics', 'aggregated-metrics', 'purchasing-trends', 'operational-performance')),
    ('vendor-catalog', ('cataloging', '/vendor/feeds', 'qc-norms')),
    ('vendor-payments', ('/vendor/payments', 'accounting', 'debit')),
    ('vendor-returns', ('return-orders', 'rtv')),
    ('vendor-users-access', ('user-management', 'uam', '/vendor/aggregate-entities')),
    ('vendor-documents', ('/vendor-p', 'document-service', 'getfile', 'getdocument')),
    ('vendor-config-support', ('/vendor/config', 'ticketportal', 'support', 'recon-tool', 'check-taas')),
]


def section_of(surface, host, path):
    pl = (path).lower()
    table = SECTION_MAP_VENDOR if surface == 'vendorhub' else SECTION_MAP_SELLER
    for name, keys in table:
        if any(k in pl for k in keys):
            return f'{surface}:{name}'
    return f'{surface}:other'


if __name__ == '__main__':
    main()
