#!/usr/bin/env python3
"""PHASE 3 — static extraction of Flipkart API endpoints + SPA routes from the JS corpus.

READ-ONLY: parses files on disk only. Makes no network call.

Outputs (into captures/):
  endpoints-raw.tsv   surface \t method \t host \t path \t const \t evidence_file
  routes-raw.txt      surface \t route
"""
import re
import os
import glob
import json
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
JS = os.path.join(HERE, 'js')

# ---------------------------------------------------------------- known hosts
SELLER_HOST = 'seller.flipkart.com'
VENDOR_HOST = 'vendorhub.flipkart.com'

# API path shapes worth keeping. Anything matching these is a candidate endpoint.
API_PREFIXES = (
    'napi/', '/napi/',
    'fed-ads/', '/fed-ads/',
    '/vendor/', '/vendor-p/',
    '/api/', 'api/',
    '/v1/', '/v2/', '/v3/', '/v0/',
    '/retail-palantir/', '/triton/', '/ryuk/', '/snoopyIngestion/',
    '/oauth', '/sellers/',
)

# Strings that look like a path but are assets / i18n / css / junk.
JUNK_RE = re.compile(
    r'\.(js|css|png|jpg|jpeg|svg|gif|woff2?|ttf|eot|ico|map|html|json|webp|mp4|pdf|txt)(\?|$)'
    r'|^/(static|assets|images|img|fonts|node_modules)/'
    r'|[<>{}\\|^`\s]'
    r'|^\/+$',
    re.I)

# Path charset: keep template markers ${...} : and *
PATH_CHARS = r"[A-Za-z0-9_\-./:%~\$\{\}\*\(\)\[\]=&\?,+@!']"

METHOD_RE = re.compile(
    r'\b(?:method\s*[:=]\s*|type\s*[:=]\s*)["\']?(GET|POST|PUT|PATCH|DELETE|HEAD)["\']?'
    r'|\b(?:doHttp|http|axios|fetch|request)\.?(Get|Post|Put|Patch|Delete|get|post|put|patch|delete)\b',
    re.I)


def surface_of(path_file: str) -> str:
    return 'vendorhub' if '/vendorhub/' in path_file else 'seller'


def host_for(surface: str, p: str) -> str:
    """Resolve which host a path belongs to."""
    if surface == 'vendorhub':
        return VENDOR_HOST
    return SELLER_HOST


def clean(p: str) -> str:
    p = p.strip()
    if not p:
        return ''
    # normalise: drop a trailing ? and collapse repeated slashes (but keep template)
    p = re.sub(r'/{2,}', '/', p)
    return p


def is_api(p: str) -> bool:
    if not p or JUNK_RE.search(p):
        return False
    if len(p) < 4 or len(p) > 200:
        return False
    q = p if p.startswith('/') else '/' + p
    if not any(q.startswith(x if x.startswith('/') else '/' + x) for x in API_PREFIXES):
        # also accept anything containing a versioned api segment
        if not re.search(r'/(?:napi|fed-ads|api|v[0-9])/', q):
            return False
    # must contain at least one letter segment
    if not re.search(r'[A-Za-z]{3}', q):
        return False
    return True


def nearest_const(text: str, pos: int) -> str:
    """Look backwards for the minified constant / key name the literal was assigned to."""
    win = text[max(0, pos - 160):pos]
    for pat in (
        r'([A-Z][A-Z0-9_]{3,60})\s*[:=]\s*$',                 # CONST_NAME:
        r'([a-zA-Z_$][\w$]{2,60})\s*[:=]\s*$',                # camelKey:
        r'([A-Z][A-Z0-9_]{3,60})\s*[:=]\s*[`"\']?$',
    ):
        m = re.search(pat, win)
        if m:
            return m.group(1)
    m = re.findall(r'([A-Za-z_$][\w$]{2,60})\s*[:=]\s*(?:function|\()?', win)
    return m[-1] if m else ''


def nearest_method(text: str, pos: int) -> str:
    """Infer the HTTP verb from a window around the literal."""
    win = text[max(0, pos - 300):pos + 300]
    votes = collections.Counter()
    for m in METHOD_RE.finditer(win):
        v = (m.group(1) or m.group(2) or '').upper()
        if v:
            votes[v] += 1
    if votes:
        return votes.most_common(1)[0][0]
    return 'UNKNOWN'


def main():
    files = sorted(glob.glob(os.path.join(JS, 'seller', '*.js')) +
                   glob.glob(os.path.join(JS, 'vendorhub', '*.js')))
    lit_re = re.compile(r'["\'`](' + PATH_CHARS + r'{3,200}?)["\'`]')
    # template-literal concatenation:  `api/v1/po/${e}/items`
    rows = {}          # (surface, host, path) -> [method, const, file]
    routes = set()     # (surface, route)
    route_re = re.compile(r'["\'`](#?/[a-zA-Z][A-Za-z0-9_\-/:]{1,80})["\'`]')

    for f in files:
        surface = surface_of(f)
        try:
            s = open(f, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        base = os.path.basename(f)

        for m in lit_re.finditer(s):
            raw = clean(m.group(1))
            if not raw:
                continue
            if is_api(raw):
                p = raw if raw.startswith('/') else '/' + raw
                host = host_for(surface, p)
                key = (surface, host, p)
                if key not in rows:
                    rows[key] = [nearest_method(s, m.start()),
                                 nearest_const(s, m.start()), base]
                else:
                    # upgrade UNKNOWN if another site resolves the verb
                    if rows[key][0] == 'UNKNOWN':
                        v = nearest_method(s, m.start())
                        if v != 'UNKNOWN':
                            rows[key][0] = v

        # SPA routes — hash routes and react-router paths
        for m in route_re.finditer(s):
            r = m.group(1)
            if JUNK_RE.search(r) or len(r) < 3:
                continue
            # a route has no api marker
            if re.search(r'/(?:napi|fed-ads|api|v[0-9])/', r):
                continue
            routes.add((surface, r))

    out_e = os.path.join(HERE, 'endpoints-raw.tsv')
    with open(out_e, 'w') as fh:
        fh.write('surface\tmethod\thost\tpath\tconst\tevidence_file\n')
        for (surface, host, p), (meth, const, base) in sorted(rows.items()):
            fh.write(f'{surface}\t{meth}\t{host}\t{p}\t{const}\t{base}\n')

    out_r = os.path.join(HERE, 'routes-raw.txt')
    with open(out_r, 'w') as fh:
        fh.write('surface\troute\n')
        for surface, r in sorted(routes):
            fh.write(f'{surface}\t{r}\n')

    print(f'files scanned      : {len(files)}')
    print(f'distinct endpoints : {len(rows)}')
    print(f'distinct routes    : {len(routes)}')
    by = collections.Counter(k[0] for k in rows)
    print('endpoints by surface:', dict(by))
    bm = collections.Counter(v[0] for v in rows.values())
    print('endpoints by method :', dict(bm))
    br = collections.Counter(r[0] for r in routes)
    print('routes by surface   :', dict(br))


if __name__ == '__main__':
    main()
