#!/usr/bin/env python3
"""Merge the OMS harvest lenses into one inventory, keyed on the normalised path.

Two lenses, blind in different places, over one transport:

  A  extract_calls.py     `Y.<verb>(`/relative/path`)`      -> prefix /api
  B  extract_literals.py  `X6(Q6(`/api/absolute/path`,br))` -> already absolute

Both terminate in the single axios instance Y, so the union is the whole API
surface the SPA can reach — a real denominator, not a sample. Anything the
shipped spec has that neither lens sees is a genuine "no longer called by the
UI" signal (which is NOT the same as "dead server-side" — only the probe can
say that, and skill rule 5 forbids dropping it without positive evidence).

Domain is derived from the PATH, never from a lens label (skill rule: one lens
says PERSON_GATEIN, another person-gatein, and trusting the label splits one
domain into two).

  C  lens-c-indirect.json  path hoisted into a local/const, then passed
                           to the client elsewhere -> hand-curated with evidence

Lens C exists because A and B share a blind spot: both require the path literal
to sit syntactically AT the call site. `let i=`/orders/list/`+q; Y.get(i)` and
`var z7=`/legal/item/`` defeat both. It was found the way harvest.md predicts —
a shipped, working endpoint showing up as "not harvested" is the structural tell
of extraction bias, not a quirk of that endpoint.

usage: merge_lenses.py <calls.json> <literals.json> <shipped-spec.yaml> [lens-c.json]
       > inventory.json
"""
import json
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from normalise import norm  # noqa: E402

# A GET-with-params call site records its params object; capture the keys so the
# study phase starts from what the app itself sends, never from an invented
# value (skill rule 1).
PARAMS = re.compile(r"params\s*:\s*\{([^{}]*)\}")
KEY = re.compile(r"([A-Za-z_$][\w$]*)\s*:")


def domain_of_api(p):
    parts = [x for x in norm(p).split("/") if x]
    if parts and parts[0] == "api":
        parts = parts[1:]
    return parts[0] if parts else "unknown"


def observed_params(ctx):
    m = PARAMS.search(ctx)
    if not m:
        return []
    return sorted(set(KEY.findall(m.group(1))))


def shipped_paths(spec_path):
    txt = open(spec_path).read()
    out = {}
    # walk resource -> endpoints -> name / method / path
    res = ep = None
    for line in txt.split("\n"):
        m = re.match(r"^  ([\w-]+):\s*$", line)
        if m and m.group(1) not in ("env_vars",):
            res = m.group(1)
            continue
        m = re.match(r"^      ([\w-]+):\s*$", line)
        if m:
            ep = m.group(1)
            continue
        m = re.match(r'^\s+path: "([^"]+)"', line)
        if m and res and ep and m.group(1).startswith("/api"):
            out[norm(m.group(1))] = f"{res} {ep}"
    return out


def main():
    calls = json.load(open(sys.argv[1]))
    lits = json.load(open(sys.argv[2]))
    shipped = shipped_paths(sys.argv[3])

    inv = {}

    def add(raw_abs, method, lens, ctx, extra):
        k = norm(raw_abs)
        e = inv.setdefault(k, {
            "path": k, "domain": domain_of_api(k), "methods": set(),
            "lenses": set(), "raw": set(), "params": set(), "notes": set(),
        })
        e["methods"].add(method)
        e["lenses"].add(lens)
        e["raw"].add(raw_abs)
        e["params"].update(observed_params(ctx))
        e["notes"].update(extra)

    for c in calls:                       # lens A: relative -> absolute
        add("/api" + c["raw_path"], c["method"], "A-callsite", c["context"], set())

    for l in lits:                        # lens B: already absolute
        if not l["raw_path"].startswith("/api/"):
            continue
        if not l["reaches_http"]:
            continue
        notes = set()
        if "Q6" in l["callers"] or "t8" in l["callers"]:
            notes.add("branch-scoped")    # ?branch=OIL|BEVERAGE(S) appended
        if "Z6" in l["callers"]:
            notes.add("multipart-upload")

        # METHOD INFERENCE MUST FAIL CLOSED.
        #
        # X6's signature defaults to GET (`method: t?.method || `GET``), so the
        # first version of this simply defaulted to GET whenever it could not
        # see an options object. That marked `/api/service-layer/invoice/` —
        # which POSTs a document into SAP — as a readable GET endpoint, because
        # its write happens through a URL held in a local:
        #
        #     let r = Q6(`/api/service-layer/invoice/`, qfe(e.branch));
        #     o(`POST ${r} → submitting document…`)
        #
        # Defaulting an unknown method to GET on a read-only CLI is how a write
        # ships as a read. Unproven resolves to EXCLUDED (skill rule 1), so an
        # unrecognised shape is recorded as UNKNOWN and carries write_intent
        # until a bare live probe proves the server serves GET.
        ctx = l["context"]
        meth, notes_extra = None, set()
        m = re.search(r"method\s*:\s*[`'\"](\w+)[`'\"]", ctx)
        if m:
            meth = m.group(1).upper()
        elif "Z6" in l["callers"]:
            meth = "POST"
        elif "q6" in l["callers"] and "X6" not in l["callers"]:
            # q6() only BUILDS a URL string; it performs no request. A path that
            # only ever reaches q6 is a bare URL constant — typically a form
            # action or an <a href> download target — and its verb is unknown.
            meth = "UNKNOWN"
            notes_extra.add("url-constant-only")
        else:
            meth = "GET"                  # direct X6(path) with no options
        if re.search(r"\b(POST|PUT|PATCH|DELETE)\b", ctx) and meth == "GET":
            notes_extra.add("write-verb-in-context")
        if re.search(r"upload|submitting|submitted|FormData", ctx, re.I):
            notes_extra.add("write-intent-keyword")
        add(l["raw_path"], meth, "B-literal", ctx, notes | notes_extra)

    if len(sys.argv) > 4:                 # lens C: curated indirect paths
        for e in json.load(open(sys.argv[4]))["entries"]:
            k = norm(e["path"])
            rec = inv.setdefault(k, {
                "path": k, "domain": domain_of_api(k), "methods": set(),
                "lenses": set(), "raw": set(), "params": set(), "notes": set(),
            })
            rec["methods"].add(e["method"])
            rec["lenses"].add("C-indirect")
            rec["raw"].add(e["path"])
            rec["params"].update(e.get("params", []))
            if e.get("excluded"):
                rec["notes"].add("excluded:" + e["exclusion_reason"])

    for k, v in inv.items():
        v["methods"] = sorted(v["methods"])
        v["lenses"] = sorted(v["lenses"])
        v["raw"] = sorted(v["raw"])
        v["params"] = sorted(v["params"])
        v["notes"] = sorted(v["notes"])
        v["in_shipped_spec"] = shipped.get(k)
        v["get_capable"] = "GET" in v["methods"]

    out = {
        "inventory": [inv[k] for k in sorted(inv)],
        "shipped_not_harvested": sorted(set(shipped) - set(inv)),
        "shipped_total": len(shipped),
        "harvested_total": len(inv),
    }
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
