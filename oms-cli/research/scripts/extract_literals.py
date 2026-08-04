#!/usr/bin/env python3
"""Lens B — every path-shaped literal in the bundle, with proof of what it feeds.

Lens A (extract_calls.py) anchors on `<recv>.<verb>(` and therefore sees only
the RELATIVE family that rides the axios baseURL:

    Y.get(`/hana/so/`, {params:{card_code:e}})

OMS has a SECOND family that lens A is structurally blind to. A wrapper takes an
ABSOLUTE /api/... path, strips the /api prefix back off, and hands it to the very
same axios instance:

    q6 = e => `${Ea}${/\\/api$/i.test(Ea) ? e.replace(/^\\/api/i,``) : e}`   // Ea = ".../api"
    X6 = async (e,t) => { let {url:n} = J6(e); return Y.request({url:n, method:t?.method||`GET`, ...}) }
    Z6 = async (e,t,n=`POST`) => Y.request({url:r, method:n, data:t, ...})   // multipart
    Q6 = (e,t) => `${e}${e.includes(`?`)?`&`:`?`}branch=${encodeURIComponent(t)}`

    await X6(Q6(`/api/hana/all-customers/`, n))

Because the literal is nested inside `Q6(...)` inside `X6(...)`, no "first
argument of a verb call" reader can reach it. So this lens inverts the anchor:
find every literal, then look OUTWARD for the evidence that it reaches an HTTP
client. Six independent lenses on factory all shared one blind spot and lost 157
paths; the fix is lenses that fail differently, not more lenses that fail alike.

ANCHORING NOTE (this bit was got wrong once, and silently). The first version
tokenised the whole 2 MB file left to right, treating every quote as a literal
opener. Minified bundles are full of regex literals, and one regex containing an
unpaired quote (`/["']/`) desynchronises the walk, which then swallows a huge
span and skips every real literal inside it. It reported 75 path literals and
ZERO starting with /api/, on a file peek had already shown contained
`X6(`/api/sku/all/`)`. A lens that returns a plausible small number is
indistinguishable from a lens that works, which is why the count was checked
against a known-present path instead of accepted.

The fix: never walk the whole file. Anchor on the two-character sequence
<quote>/ and read the literal from there. Desync is then impossible, because
every read starts at a position independently proven to open a literal.

Discrimination (harvest.md): a path is only reported with evidence it reaches an
HTTP client. We record the enclosing call tokens so react-router `path:"..."`
strings and asset URLs can be told apart from real REST calls.

usage: extract_literals.py <bundle.js> [more.js ...]   -> JSON on stdout
"""
import json
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from extract_calls import read_literal  # noqa: E402

# Wrappers proven (by reading their definitions in the bundle) to terminate in
# Y.request(...). X6/Z6 take the path; q6/J6 build the URL; Q6/t8 decorate it
# with ?branch=.
HTTP_WRAPPERS = ("X6", "Z6", "q6", "J6", "Q6", "t8")

OPENER = re.compile(r"[\"'`]/")
ENCLOSING = re.compile(r"([A-Za-z_$][\w$]*)\s*\($")


def enclosing_calls(src, start, want=3):
    """Walk left from the literal over balanced argument text, collecting the
    identifiers of the calls whose argument lists contain it.

    X6(Q6(`/api/...`, n)) yields ["Q6", "X6"] — the inner decorator and the
    outer transport. Both matter: Q6 proves the ?branch= tenant param applies,
    X6 proves it reaches HTTP.
    """
    names, j, depth, guard = [], start - 1, 0, 0
    while j >= 0 and guard < 6000 and len(names) < want:
        guard += 1
        ch = src[j]
        if ch in ")]}":
            depth += 1
        elif ch == "(":
            if depth == 0:
                m = ENCLOSING.search(src[max(0, j - 40):j + 1])
                names.append(m.group(1) if m else "?")
            else:
                depth -= 1
        elif ch in "[{":
            if depth:
                depth -= 1
        j -= 1
    return names


def scan(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    out, seen = [], set()
    for m in OPENER.finditer(src):
        start = m.start()
        if start in seen:
            continue
        body, end = read_literal(src, start)
        if body is None or not body.startswith("/"):
            continue
        seen.add(start)
        if "/" not in body[1:] and "${" not in body:
            continue                        # "/" alone, separators, flags
        callers = enclosing_calls(src, start)
        out.append({
            "file": path.rsplit("/", 1)[-1],
            "raw_path": body,
            "offset": start,
            "callers": callers,
            "reaches_http": any(c in HTTP_WRAPPERS for c in callers),
            # Wide window on purpose. The method lives in an options object
            # AFTER the path (`X6(`/x/`,{method:`POST`})`), and the write intent
            # for a URL held in a constant can sit hundreds of chars away
            # (`let r=Q6(`/api/service-layer/invoice/`,..); o(`POST ${r} ...`)`).
            # A narrow window silently reads those as GET.
            "context": src[max(0, start - 300):min(len(src), end + 500)],
        })
    return out


def main():
    all_hits = []
    for p in sys.argv[1:]:
        all_hits.extend(scan(p))
    json.dump(all_hits, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
