#!/usr/bin/env python3
"""
extract.py — PHASE 3/4 static analyser for the Swiggy Instamart brand-portal corpus.

Reads the harvested webpack corpus in captures/js/ (the `brand-portal-client`
module-federation shell plus its 6 runtime remotes) and emits:

  endpoints-raw.tsv        every distinct API endpoint: host, path, method, app,
                           source chunk, the minified constant it is bound to,
                           and how the method was determined
  extract-evidence.json    the same rows plus the raw call-site context (evidence).
                           Deliberately NOT named endpoints-* : it holds minified JS
                           context strings (SVG namespaces, route literals), so a tool
                           that treats an "endpoints*" file as an inventory would
                           mis-read that noise as un-indexed endpoints.
  routes-raw.txt           every SPA page/route literal
  wired-reads.tsv          PHASE-4 partition: READ / READ_FILE
  writes-excluded.tsv      PHASE-4 partition: WRITE / EXPORT
  unknown-excluded.tsv     PHASE-4 partition: UNKNOWN (denied by default, G1)
  extract-stats.json       counts for the Phase-7 audit

READ-ONLY: only reads files already on disk. Zero network calls.

--- how host is resolved (all rules are read verbatim out of the corpus) ---
Each app has an env table with a [PRODUCTION] block naming its base hosts:
    partnerServiceBasePath              -> partner-api.swiggy.com
    brandPortalServiceBasePath          -> brand-portal-service-http.swiggy.com
    brandverseServiceBasePath           -> brand-portal-service-http.swiggy.com
    scmAPIGatewayBasePath               -> picker.swiggy.com          (im-vendor)
    movementPlanningAPIGatewayBasePath  -> picker.swiggy.com          (im-vendor)
    getOzoneHostName(BRAND)             -> ozone-idp-brands-im-kba.swiggy.com
    getOzoneHostName(INTERNAL)          -> partner-api.swiggy.com
The two shell constant maps prove the path->host split directly: the map of
`/instamart/v1/...` paths is consumed with partnerServiceBasePath and the map of
`/api/v1/...` paths with brandPortalServiceBasePath.
"""
import glob
import json
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
JS = os.path.join(HERE, "js")

APPS = ["brand-portal-client", "instamart", "im-vendor",
        "im-discounts", "brandverse", "im-sampling", "im-catalog"]

H_PARTNER = "partner-api.swiggy.com"
H_BPS = "brand-portal-service-http.swiggy.com"
H_PICKER = "picker.swiggy.com"
H_OZONE = "ozone-idp-brands-im-kba.swiggy.com"

# SPA route namespaces: a literal under one of these that carries no API version
# segment is a PAGE, not an endpoint.
ROUTE_ROOTS = ("/instamart", "/im-vendor", "/im-discounts", "/im-sampling",
               "/brandverse", "/im-catalog", "/login", "/account-select",
               "/employee-login", "/migration-bridge")
API_MARK = re.compile(r"/(?:api|v\d)(?:/|$)")

NOT_API = re.compile(r"""(?ix)
    \.(png|jpe?g|svg|gif|webp|woff2?|ttf|eot|css|map|ico|json|wasm|mp4|lottie|html)(\?|$)
  | ^/(?:assets?|static|images?|img|fonts?|media|dls-web-assets|IM-PD-Assets|PartnerPortal|swiggy/image)/
  | ^//
""")

# ---- name:"/path"  |  name="/path"  |  name:()=>`/path`  |  name:e=>`/path/${e}`
NAMED = re.compile(
    r"""([A-Za-z_$][\w$]{1,60})\s*[:=]\s*"""
    r"""(?:\([^)]{0,30}\)\s*=>\s*|[A-Za-z_$][\w$]{0,4}\s*=>\s*)?"""
    r"""["'`](/[A-Za-z0-9_./${}:%*-]{2,180})["'`]"""
)
# ---- any bare API-ish path literal (catches paths not bound to a constant)
# NOTE the optional leading slash: the im-discounts remote writes its paths WITHOUT
# one (`n.m.get("api/discounting/v1/campaign/file")`). Requiring "/" silently lost
# three real endpoints (campaign/disable, campaign/file, campaign/spins) until the
# independent auditor's generic regex flagged them.
BARE = re.compile(r"""["'`](/?(?:api|v\d|instamart|im-discounts|im-vendor)/[A-Za-z0-9_./${}:%*-]{2,180})["'`]""")

# ---- route-shaped literals (their own scan; see the note at the call site)
ROUTE_LITERAL = re.compile(
    r"""["'`]((?:/?)(?:instamart|im-vendor|im-discounts|im-sampling|brandverse|im-catalog|"""
    r"""login|account-select|employee-login|migration-bridge)"""
    r"""[A-Za-z0-9_./${}:*-]{0,110})["'`]""")

# ---- direct literal call sites: Client.get("api/discounting/v1/campaign/config")
# The path is the FIRST ARGUMENT, so the verb sits immediately to its left. This is
# the strongest method evidence available and resolves paths no constant points at.
LITERAL_CALL = re.compile(
    r"""\.(get|post|put|patch|delete)\(\s*["'`](/?(?:api|v\d|instamart|im-discounts|im-vendor)/[A-Za-z0-9_./${}:%*-]{2,180})["'`]""")

# ---- template literals whose path follows a ${...} interpolation, e.g.
#      `${(0,o.Cq)()}/api/v1/inventory/search/itemInventories`
#      `${base()}/api/v1/grn/search/${id}`
# The vendor + catalog apps build EVERY url this way, so a quoted-literal-only
# scan misses their entire surface.
TEMPLATE = re.compile(r"`([^`\\]{0,400}?)`")
TPL_PATH = re.compile(r"(/(?:api|v\d)/[A-Za-z0-9_./${}:%*-]{2,170})")

# ---- call sites:  Client.get(`${base()}${API.CONST}` ...)
CALLSITE = re.compile(r"\.(get|post|put|patch|delete)\(")
IDENT = re.compile(r"[A-Za-z_$][\w$]{2,60}")

# React-Query signals used only as a weak fallback
Q_READ = re.compile(r"useQuery|useSuspenseQuery|useInfiniteQuery|queryKey|queryFn")
Q_WRITE = re.compile(r"useMutation|mutationFn|mutationKey")

# ---- PHASE 4 classification vocabulary -------------------------------------
# Mutating verbs. Matched against whole path segments and hyphen/underscore parts.
WRITE_VERBS = {
    "create", "update", "delete", "remove", "edit", "modify", "upsert", "insert",
    "save", "submit", "upload", "cancel", "approve", "reject", "acknowledge",
    "ack", "schedule", "reschedule", "unschedule", "assign", "revoke", "dispute",
    "pay", "payout", "settle", "refund", "activate", "deactivate", "enable",
    "disable", "publish", "logout", "signout", "signin", "login", "initiate",
    "send", "resend", "reinvite", "invite", "sync", "toggle", "trigger",
    "generate", "impersonate", "impersonation", "subscribe", "draft", "reset",
    "confirm", "accept", "deny", "pause", "resume", "duplicate", "clone",
    "add", "put", "post", "patch", "set", "apply", "book", "release", "close",
    "complete", "finalize", "override", "adjust", "bid", "spend",
    "signinwithidp", "signinwithotp", "sendverificationcode", "createauthuri",
}
# File-download markers → READ_FILE (safe: consumes an existing artifact)
FILE_VERBS = {"download", "export-file", "pdf", "xlsx", "csv"}


CAMEL = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|\d+")


def segments(path):
    """Tokenise a path into lowercase words.

    Splits on '/', '-', '_' AND camelCase, because this codebase names endpoints
    both ways: `/api/v1/external/indent/item/update` and
    `/api/v1/searchPurchaseReturnLines`. Without camel splitting, `searchGrns`
    and `batchCancel` would both read as opaque single tokens.
    """
    out = []
    for seg in path.split("/"):
        if not seg or seg.startswith(("${", "{", ":")):
            continue
        s = seg.lower()
        out.append(s)
        for part in re.split(r"[-_]", s):
            if part:
                out.append(part)
        for part in CAMEL.findall(seg):
            out.append(part.lower())
    return out


def is_route(path):
    return path.startswith(ROUTE_ROOTS) and not API_MARK.search(path)


def host_for(app, path, ctx):
    if path == "/time" or path.startswith("/instamart/v1/"):
        return H_PARTNER
    # `/im-discounts/v1/*` mirrors `/instamart/v1/*` exactly (account/get, account/list,
    # account/permissions, configs) and is fetched with the same client the shell points
    # at partnerService, so it resolves to partner-api. INFERRED, not observed live.
    if path.startswith("/im-discounts/v1/"):
        return H_PARTNER
    if path.startswith(("/v1/accounts", "/v2/accounts", "/v1/token", "/v1/otp")):
        return H_OZONE
    if app == "im-vendor":
        return H_PICKER
    m = re.search(r"https://([a-z0-9.-]+\.(?:swiggy\.com|instamart\.in))", ctx)
    if m and "media-assets" not in m.group(1):
        return m.group(1)
    return H_BPS


AUTH_PREFIXES = ("/v1/accounts", "/v2/accounts", "/v1/token", "/v1/otp")

READ_ISH = {"list", "search", "filter", "get", "fetch", "metrics", "metric",
            "details", "detail", "summary", "insights", "insight", "reports",
            "suggest", "suggestions", "estimate", "count", "view", "dashboard",
            "permissions", "configs", "config", "history", "status", "info",
            "options", "lines", "spins", "recommend", "accessinfo", "data"}


def classify(path, method, const):
    """Return (klass, why). Deny-by-default per G1.

    Precedence, most decisive first:
      1. auth / session endpoints  -> WRITE (they mint or destroy a session; G9)
      2. mutating HTTP verb        -> WRITE
      3. report generate/enqueue   -> EXPORT (G2: creates a row on the live acct)
      4. mutating path token       -> WRITE   (checked BEFORE download markers so
                                               `.../batch/submit` cannot pass as
                                               a file read)
      5. download marker           -> READ_FILE
      6. observed GET              -> READ
      7. POST with read semantics  -> READ    (POST-to-read list/search/metrics)
      8. anything else             -> UNKNOWN (denied)
    A row whose METHOD is unresolved can still be classified from strong path
    evidence, but the CLI allowlist additionally requires a resolved method —
    see the `wired` column.
    """
    segs = set(segments(path))
    name = (const or "").lower()

    if path.startswith(AUTH_PREFIXES):
        return "WRITE", "auth/session endpoint (mints, rotates or destroys a session — G9)"

    if method in ("PUT", "PATCH", "DELETE"):
        return "WRITE", f"observed HTTP {method}"

    if "initiate" in segs or "generate" in segs or "initiate" in name:
        return "EXPORT", "report generation / enqueue — creates a row + burns queue budget (G2)"

    hits = segs & WRITE_VERBS
    if hits:
        return "WRITE", f"mutating path token(s) {sorted(hits)}"

    # Constant-name check, TOKENISED. Substring matching produced false positives:
    # PREAPPROVED_CREATIVES -> "approve", so a read list was excluded as a write.
    # Tokenising gives {pre, approved, creatives}, and "approved" != "approve".
    nm_toks = set(re.split(r"[-_\s]+", name)) | {t.lower() for t in CAMEL.findall(const or "")}
    nm_hits = nm_toks & WRITE_VERBS
    if nm_hits:
        return "WRITE", f"mutating constant name token(s) {sorted(nm_hits)}"

    fhits = (segs & FILE_VERBS) | {v for v in FILE_VERBS if v in name}
    if fhits:
        return "READ_FILE", f"file-download marker {sorted(fhits)}"

    if method == "GET":
        return "READ", "observed GET"
    if method == "POST":
        if segs & READ_ISH or any(k in name for k in
                                  ("list", "get", "search", "fetch", "metric",
                                   "detail", "summary", "insight", "suggest")):
            return "READ", "POST-to-read (list/search/get/metrics semantics, no mutating token)"
        return "UNKNOWN", "POST with no read-or-write evidence"
    # method unresolved
    if segs & READ_ISH:
        return "UNKNOWN", "read-shaped path but METHOD UNRESOLVED — denied per G1"
    return "UNKNOWN", "method unresolved from the minified source — denied per G1"


def main():
    named_paths = {}     # (app, const) -> path
    rows = {}            # (host, path) -> row
    routes = defaultdict(set)
    const_method = defaultdict(Counter)
    known_consts = set()
    files = 0
    total_bytes = 0
    sources = {}

    # ---------- pass 1: constant maps + bare literals
    for app in APPS:
        d = os.path.join(JS, app)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".js"):
                continue
            s = open(os.path.join(d, fn), errors="ignore").read()
            files += 1
            total_bytes += len(s)
            sources[(app, fn)] = s

            for m in NAMED.finditer(s):
                const, path = m.group(1), m.group(2)
                if NOT_API.search(path):
                    continue
                if is_route(path):
                    routes[path].add((app, const))
                    continue
                if not API_MARK.search(path) and path != "/time":
                    continue
                named_paths[(app, const)] = path
                known_consts.add(const)

            # Route-shaped literals get their own scan. They used to fall out of the
            # (previously looser) BARE pattern via is_route(); once BARE was tightened
            # to api-prefixed paths, 12 routes silently vanished from Pages-and-Routes
            # until the count was compared against the previous run.
            for m in ROUTE_LITERAL.finditer(s):
                r = m.group(1)
                if not r.startswith("/"):
                    r = "/" + r
                if NOT_API.search(r) or API_MARK.search(r):
                    continue
                routes[r].add((app, ""))

            for m in BARE.finditer(s):
                path = m.group(1)
                if not path.startswith("/"):
                    path = "/" + path
                if NOT_API.search(path):
                    continue
                if is_route(path):
                    routes[path].add((app, ""))
                    continue
                if not API_MARK.search(path) and path != "/time":
                    continue
                ctx = s[max(0, m.start() - 340): m.end() + 260].replace("\n", " ")
                host = host_for(app, path, ctx)
                key = (host, path)
                if key not in rows:
                    rows[key] = {"host": host, "path": path, "method": "UNKNOWN",
                                 "method_src": "", "app": app, "file": fn,
                                 "const": "", "ctx": ctx[:700]}

            # direct literal call sites — strongest method evidence
            for m in LITERAL_CALL.finditer(s):
                verb, raw = m.group(1).upper(), m.group(2)
                path = raw if raw.startswith("/") else "/" + raw
                if NOT_API.search(path) or is_route(path):
                    continue
                ctx = s[max(0, m.start() - 340): m.end() + 300].replace("\n", " ")
                host = host_for(app, path, ctx)
                key = (host, path)
                r = rows.setdefault(key, {"host": host, "path": path, "method": "UNKNOWN",
                                          "method_src": "", "app": app, "file": fn,
                                          "const": "", "ctx": ctx[:700]})
                if r["method"] == "UNKNOWN" or r["method"] == verb:
                    r["method"] = verb
                    r["method_src"] = f'direct literal call site .{m.group(1)}("{raw}")'
                elif r["method"] != verb:
                    # same path served by two verbs (e.g. tnc/acceptance GET + POST):
                    # keep the mutating one so deny-by-default wins.
                    if verb in ("PUT", "PATCH", "DELETE", "POST"):
                        r["method"] = verb
                        r["method_src"] = (f'direct literal call site .{m.group(1)}("{raw}") '
                                           f'— path also served by another verb; kept the '
                                           f'mutating one so deny-by-default wins')

            # template-literal urls: `${basePathFn()}/api/v1/...`
            for tm in TEMPLATE.finditer(s):
                body = tm.group(1)
                if "/" not in body:
                    continue
                for pm in TPL_PATH.finditer(body):
                    path = pm.group(1)
                    if NOT_API.search(path) or is_route(path):
                        continue
                    ctx = s[max(0, tm.start() - 420): tm.end() + 420].replace("\n", " ")
                    host = host_for(app, path, ctx)
                    # These apps assign the template to a local, then call
                    # Client.post(local, body, headers) a few tokens later. The
                    # nearest client verb AFTER the template is the method.
                    verb, vsrc = "UNKNOWN", ""
                    fwd = s[tm.end(): tm.end() + 420]
                    vm = re.search(r"\.(get|post|put|patch|delete)\(", fwd)
                    if vm:
                        verb = vm.group(1).upper()
                        vsrc = f"nearest client .{vm.group(1)}() after the template url"
                    key = (host, path)
                    if key not in rows:
                        rows[key] = {"host": host, "path": path,
                                     "method": verb, "method_src": vsrc,
                                     "app": app, "file": fn, "const": "",
                                     "ctx": ctx[:700]}
                    elif rows[key]["method"] == "UNKNOWN" and verb != "UNKNOWN":
                        rows[key]["method"] = verb
                        rows[key]["method_src"] = vsrc

    # ---------- pass 2: const -> method, from client call sites
    # 2a: Client.post(`${base()}${API.CONST}`, ...) — const inside the call args
    for (app, fn), s in sources.items():
        for m in CALLSITE.finditer(s):
            verb = m.group(1).upper()
            window = s[m.end(): m.end() + 300]
            for ident in IDENT.findall(window):
                if ident in known_consts:
                    const_method[ident][verb] += 1
                    break

    # 2b: the dominant shape in this codebase —
    #        const url = `${basePathFn()}${API.CONST}`;
    #        ... yield Client.post(url, body, headers)
    #     the url is assigned to a local first, so the const is NOT inside the
    #     call args. Resolve by taking the nearest client verb AFTER the template.
    TPL_CONST = re.compile(r"`\$\{[^`]{0,160}?\}\$\{[^`{}]{0,60}?\.([A-Za-z_$][\w$]{2,60})\}[^`]{0,40}`")
    for (app, fn), s in sources.items():
        for m in TPL_CONST.finditer(s):
            const = m.group(1)
            if const not in known_consts:
                continue
            vm = re.search(r"\.(get|post|put|patch|delete)\(", s[m.end(): m.end() + 700])
            if vm:
                const_method[const][vm.group(1).upper()] += 1

    # ---------- pass 3: attach consts + methods to rows
    for (app, const), path in named_paths.items():
        # locate a context for host inference
        ctx = ""
        for (a, fn), s in sources.items():
            if a != app:
                continue
            i = s.find(f'{const}:"{path}"')
            if i < 0:
                i = s.find(f'"{path}"')
            if i >= 0:
                ctx = s[max(0, i - 340): i + 400].replace("\n", " ")
                srcfile = fn
                break
        else:
            srcfile = ""
        host = host_for(app, path, ctx)
        key = (host, path)
        r = rows.setdefault(key, {"host": host, "path": path, "method": "UNKNOWN",
                                  "method_src": "", "app": app,
                                  "file": srcfile, "const": "", "ctx": ctx[:700]})
        if const not in r["const"].split(","):
            r["const"] = ",".join(filter(None, [r["const"], const]))
        if r["app"] == "brand-portal-client" and app != "brand-portal-client":
            pass  # keep the shell attribution; it owns the shared constant map
        mv = const_method.get(const)
        if mv and r["method"] == "UNKNOWN":
            r["method"] = mv.most_common(1)[0][0]
            r["method_src"] = f"call site .{r['method'].lower()}() on {const}"

    # ---------- pass 4: weak fallback from react-query signals
    for r in rows.values():
        if r["method"] != "UNKNOWN":
            continue
        if Q_WRITE.search(r["ctx"]):
            r["method"], r["method_src"] = "UNKNOWN", "co-located useMutation (write-ish)"
        elif Q_READ.search(r["ctx"]):
            r["method"], r["method_src"] = "UNKNOWN", "co-located useQuery (read-ish)"

    # ---------- LIVE-WALK EVIDENCE (AMENDMENT-02: the walk is PRIMARY evidence)
    # The application firing a request during a page render we navigated to is
    # stronger proof of an endpoint's method than any static inference. Fold that
    # in BEFORE classifying, so an endpoint the static pass left UNKNOWN but the
    # walk observed returning 2xx data is correctly a proven READ.
    #
    # Guarded: only a non-mutating path may be upgraded this way. If the path
    # carries a write token the observation is recorded but the class is NOT
    # relaxed — an app-fired POST to .../indent/accept is still a write.
    observed = {}
    for wf in glob.glob(os.path.join(HERE, "walk*", "*.json")):
        if os.path.basename(wf).startswith("_"):
            continue
        try:
            d = json.load(open(wf))
        except Exception:
            continue
        for c in (d.get("calls") or []) + (d.get("captured") or []):
            if c.get("phase") == "req":
                continue
            u = (c.get("url") or "").split("?")[0]
            if not u.startswith("http"):
                continue
            pp = u.split("/")
            if len(pp) < 4:
                continue
            host, path = pp[2], "/" + "/".join(pp[3:])
            st, meth = c.get("status"), (c.get("method") or "").upper()
            if not meth:
                continue
            e = observed.setdefault((host, path), {"m": set(), "st": set(), "bytes": 0})
            e["m"].add(meth)
            if st:
                e["st"].add(st)
            e["bytes"] = max(e["bytes"], len(c.get("body") or ""))

    upgraded = 0
    for (host, path), e in observed.items():
        r = rows.get((host, path))
        if r is None:
            continue
        ok = any(200 <= s < 300 for s in e["st"])
        r["observed"] = f"live: {sorted(e['m'])} -> {sorted(e['st'])}, {e['bytes']}B"
        if r["method"] == "UNKNOWN" and ok and len(e["m"]) == 1:
            meth = next(iter(e["m"]))
            if not (set(segments(path)) & WRITE_VERBS):
                r["method"] = meth
                r["method_src"] = (f"PROVEN LIVE — the app fired {meth} during a page render "
                                   f"and got HTTP {sorted(e['st'])} with {e['bytes']}B of JSON")
                upgraded += 1

    # ---------- PHASE 4 classification
    for r in rows.values():
        r["class"], r["why"] = classify(r["path"], r["method"], r["const"])
        # G1: only a READ with a PROVEN method may reach the CLI allowlist.
        r["wired"] = "yes" if (r["class"] in ("READ", "READ_FILE")
                               and r["method"] in ("GET", "POST")) else "no"

    # ---------- write outputs
    order = sorted(rows, key=lambda k: (k[0], k[1]))

    with open(os.path.join(HERE, "endpoints-raw.tsv"), "w") as f:
        f.write("host\tpath\tmethod\tclass\twired\tapp\tsource_chunk\tconst\tevidence\n")
        for k in order:
            r = rows[k]
            f.write("\t".join([r["host"], r["path"], r["method"], r["class"], r["wired"],
                               r["app"], r["file"], r["const"],
                               (r["method_src"] or r["why"]) +
                               (" | " + r["observed"] if r.get("observed") else "")]) + "\n")

    with open(os.path.join(HERE, "extract-evidence.json"), "w") as f:
        json.dump([rows[k] for k in order], f, indent=1)

    for fname, keep in (("wired-reads.tsv", {"READ", "READ_FILE"}),
                        ("writes-excluded.tsv", {"WRITE", "EXPORT"}),
                        ("unknown-excluded.tsv", {"UNKNOWN"})):
        with open(os.path.join(HERE, fname), "w") as f:
            f.write("host\tpath\tmethod\tclass\tapp\tconst\twhy\n")
            for k in order:
                r = rows[k]
                if r["class"] in keep:
                    f.write("\t".join([r["host"], r["path"], r["method"],
                                       r["class"], r["app"], r["const"],
                                       r["why"]]) + "\n")

    with open(os.path.join(HERE, "routes-raw.txt"), "w") as f:
        f.write("route\tapps\tconstants\n")
        for rt in sorted(routes):
            apps = ",".join(sorted({a for a, _ in routes[rt]}))
            cs = ",".join(sorted({c for _, c in routes[rt] if c}))
            f.write(f"{rt}\t{apps}\t{cs}\n")

    stats = {
        "corpus_files": files,
        "corpus_bytes": total_bytes,
        "distinct_endpoints": len(rows),
        "distinct_routes": len(routes),
        "by_host": dict(Counter(r["host"] for r in rows.values()).most_common()),
        "by_app": dict(Counter(r["app"] for r in rows.values()).most_common()),
        "by_method": dict(Counter(r["method"] for r in rows.values()).most_common()),
        "by_class": dict(Counter(r["class"] for r in rows.values()).most_common()),
        "consts_with_resolved_method": len(const_method),
        "observed_live": len(observed),
        "upgraded_by_live_evidence": upgraded,
    }
    with open(os.path.join(HERE, "extract-stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
