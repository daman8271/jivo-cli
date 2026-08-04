#!/usr/bin/env python3
"""Emit the regenerated oms-spec.yaml.

Precedence for every field, strongest first:

  1. the SHIPPED v0.1.0 spec  - command name, resource, path spelling (incl. the
                                exact placeholder names), description, params.
                                Never overwritten by anything weaker.
  2. a DOMAIN STUDY overlay   - MAY ADD params and new endpoints, and supplies
                                the observed response type. It may not rename or
                                remove anything.
  3. the LIVE PROBE           - response type fallback where no study saw a body.

Skill rule 6 is enforced structurally: an endpoint present in the shipped spec
keeps its shipped resource AND command verbatim. There is no code path that can
rename one — `command_of()` returns the shipped pair or raises.

Skill rule 5 is enforced structurally too: every shipped endpoint is carried
forward unless it appears in DENYLIST, and DENYLIST contains no shipped path.
"Fewer working commands" cannot happen by omission, only by an explicit edit
here that the regression gate will then demand a justification for.

SAFETY BELONGS IN CODE, NOT IN PROSE. Excluded writes never enter the endpoint
list a generator iterates. A study once marked a dangerous endpoint by writing
`DO-NOT-PUBLISH` into its command_name field, which made its safety depend on
every downstream tool remembering to read a magic string. Here a write is denied
by normalised path+method in DENYLIST below, before anything can emit it.

usage: emit_spec.py <shipped-spec.yaml> <overlay.json> <probe.jsonl> [probe2.jsonl] > new-spec.yaml
"""
import json
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from normalise import norm  # noqa: E402

# ---------------------------------------------------------------- safety
# Normalised paths that must NEVER be published, whatever a study says.
# Matched on norm() output so a rename of {id} -> {invoice_id} cannot make this
# fail open (skill rule 8).
LENS_D = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "harvest", "lens-d-urlconf.json")

DENYLIST = {
    # auth mutators
    "/api/auth/login", "/api/auth/logout", "/api/auth/refresh",
    # order / quotation lifecycle
    "/api/orders/create", "/api/orders/create-scheme",
    "/api/orders/{}/update-status", "/api/orders/{}/cancel-quotation",
    "/api/orders/{}/delete-draft", "/api/orders/schemes/{}",
    "/api/orders/notifications/{}", "/api/orders/web-push/subscribe",
    # invoice / SAP document writes
    "/api/service-layer/invoice",          # POSTs a document into SAP B1
    "/api/invoice/pending", "/api/invoice/{}/update-status",
    "/api/invoice/credit-limit/request",
    "/api/sap/approve-sales-order", "/api/sap/sync/{}",
    # tracker writes
    "/api/tracker/actions/bulk", "/api/tracker/jsap/sync",
    "/api/tracker/invoices/{}/payment", "/api/tracker/admin/lookups/{}/{}",
    "/api/tracker/admin/stages/{}", "/api/tracker/admin/tracker-users/{}",
    "/api/tracker/admin/users/{}/stages",
    # user / party administration
    "/api/auth/users/create", "/api/auth/users/{}",
    "/api/auth/assign-parties", "/api/auth/assign-parties/bulk-upload",
    "/api/auth/remove-party", "/api/auth/bulk-party/assign-products",
    "/api/auth/party-product/bulk-add", "/api/auth/party-product/remove",
    "/api/auth/party-product/update-rate",
    # device registry, uploads, label config writes
    "/api/devices/register", "/api/sku/upload", "/api/legal/upload",
    "/api/ui-config/admin/labels/{}",
}

# Broken upstream on 2026-08-04. DELIBERATELY still published, with the reason
# in the description. Removing a shipped command is a regression an operator
# cannot distinguish from a bug; publishing it with an honest description costs
# nothing, tells them why before they run it, and means the command starts
# working the day the OMS team fixes the backend with no CLI change at all.
KNOWN_BROKEN = {
    "/api/hana/product-stock":
        "BROKEN UPSTREAM (2026-08-04): the OMS backend raises "
        "\"name 'unique_schemas' is not defined\" and returns HTTP 502 on every "
        "call, for both branches. Reported to the OMS team.",
    "/api/hana/product-so":
        "BROKEN UPSTREAM (2026-08-04): the OMS backend raises "
        "\"get_sales_orders_for_product() takes 1 positional argument but 2 were "
        "given\" and returns HTTP 500 on every call. Reported to the OMS team.",
    "/api/sku/pending":
        "BROKEN UPSTREAM (2026-08-04): the OMS backend raises "
        "\"getFGItems() missing 1 required positional argument: 'branch'\" and "
        "returns HTTP 500 on every call. Reported to the OMS team.",
    "/api/invoice/all":
        "BROKEN UPSTREAM (2026-08-04): returns HTTP 400 \"Warehouse Code is a "
        "required parameter\" for every parameter name tried, and the OMS web app "
        "never calls this route. Use `invoices logs` instead. Reported to the "
        "OMS team.",
}

# Corrections from the phase-4 adversarial verifiers, applied AFTER the studies
# because each one overturned something a study asserted. Kept in code so a
# re-run reproduces them; a hand-edit to the emitted YAML would not survive.
REFUTATION_OVERRIDES = {
    "/api/orders/list": {
        "param_enums": {
            # The orders study inferred 8 status values from what it saw in the
            # data. The master list has ELEVEN, published by `orders status`
            # (ids 1-11) and cross-published by dashboardW/charts'
            # status_distribution. All eleven were then verified live as real
            # filters - DRAFT / NEED_APPROVAL / BILLING_PENDING / ORDER_CREATED
            # return [] rather than the bare 263-row body, which is what
            # distinguishes "valid filter, no rows" from "ignored parameter".
            # Shipping the 8-value enum would have lost three working filters.
            "status": ["ORDER_CREATED", "RATE_APPROVAL", "BILLING",
                       "NEED_APPROVAL", "BILLING_PENDING", "APPROVED",
                       "REJECTED", "BILLING_REJECTED", "COMPLETED",
                       "AUDITOR_APPROVAL", "DRAFT"],
        },
        "append_description":
            "TRAPS: bare `orders list` is NOT the order book - it returns one "
            "slice (263 of 2,163 orders). `status` accepts a comma-separated "
            "list and unions them. `billing=true` DISCARDS any `status` you "
            "also pass (proven: six query strings, byte-identical bodies). "
            "`approval_pending=true` alone is a no-op.",
    },
    "/api/orders/quotation-overview": {
        "append_description":
            "The SAP doc numbers here are real: sampled (doc_num, doc_entry) "
            "pairs resolve exactly to SAP OQUT quotations. Note doc_num is NOT "
            "unique across companies - the same number exists in Oil and "
            "Beverages, so always pair it with the branch.",
    },
}

RESOURCE_DESC = {
    "account": "Authenticated account, users, roles, permissions and reference "
               "master data (companies, states, categories, main groups), plus "
               "the device registry and UI label config",
    "orders": "Sales orders, quotations, schemes, dispatches, approval flows and "
              "the order dashboard",
    "quotations": "Quotation overview and per-order quotation status",
    "dashboard": "Order dashboard widgets and charts",
    "sap": "The SAP Business One mirror inside OMS: synced parties, products, "
           "addresses, branches and sync logs. Covers all three SAP companies",
    "hana": "Live SAP HANA reads. EVERY command needs --branch (OIL or BEVERAGE) "
            "- it selects the SAP company database and the answer is meaningless "
            "without it",
    "invoices": "The invoice review-and-approval queue, credit limits and SKU "
                "master data",
    "tracker": "The OMS invoice tracker: invoices moving through stages, queues, "
               "vendors, alerts and reports. Needs a tracker grant separate from "
               "your app role - a plain admin gets HTTP 403",
    "legal": "FSSAI food-label compliance: pack artwork checked against the "
             "statutory declarations for an item",
}


# ---------------------------------------------------------------- yaml helpers
def yq(v):
    """Quote every scalar. An unquoted value containing ': ' is unparseable, and
    a study once emitted `type: string enum: IN | OUT` which broke the loader."""
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return '"' + s + '"'


def norm_type(t):
    """One bare token. `array of objects` -> `array`."""
    t = (t or "").strip().lower()
    if t.startswith("array"):
        return "array"
    if t.startswith("object"):
        return "object"
    if t in ("int", "integer"):
        return "int"
    if t in ("bool", "boolean"):
        return "bool"
    return "string" if t in ("string", "str") else (t or "object")


def lint(line):
    """Any unquoted value containing ': ' is a bug. Cheaper to catch here than
    five minutes into a generate that fails at the parser."""
    m = re.match(r"^\s*[\w-]+:\s+(?!['\"|>])(.*: .*)$", line)
    return m is not None


# ---------------------------------------------------------------- shipped spec
def parse_shipped(path):
    """Return OrderedDict[norm_path] = dict(resource, command, raw_path, method,
    description, params[], response_type) preserving document order."""
    txt = open(path).read()
    out = OrderedDict()
    res = ep = None
    in_res = False
    lines = txt.split("\n")
    for i, line in enumerate(lines):
        if re.match(r"^resources:\s*$", line):
            in_res = True
            continue
        if in_res and re.match(r"^\S", line):
            in_res = False
        if not in_res:
            continue
        m = re.match(r"^  ([\w-]+):\s*$", line)
        if m:
            res, ep = m.group(1), None
            continue
        m = re.match(r"^      ([\w-]+):\s*$", line)
        if m:
            ep = m.group(1)
            continue
        m = re.match(r'^\s+path: "([^"]+)"', line)
        if not (m and res and ep and m.group(1).startswith("/api")):
            continue
        raw = m.group(1)
        # collect this endpoint's block
        block = []
        for j in range(i - 2, min(len(lines), i + 60)):
            if j > i and re.match(r"^      [\w-]+:\s*$", lines[j]):
                break
            block.append(lines[j])
        blk = "\n".join(block)
        d = re.search(r'description: "([^"]*)"', blk)
        rt = re.search(r"response:\s*\n\s+type:\s*(\w+)", blk)
        params = []
        for pm in re.finditer(
                r"-\s+name:\s*(\w+)\s*\n"
                r"(?:\s+type:\s*(\w+)\s*\n)?"
                r"(?:\s+required:\s*(\w+)\s*\n)?"
                r"(?:\s+positional:\s*(\w+)\s*\n)?"
                r'(?:\s+description:\s*"([^"]*)"\s*\n)?', blk):
            params.append({
                "name": pm.group(1),
                "type": pm.group(2) or "string",
                "required": (pm.group(3) or "false") == "true",
                "positional": (pm.group(4) or "false") == "true",
                "description": pm.group(5) or "",
            })
        out[norm(raw)] = {
            "resource": res, "command": ep, "raw_path": raw, "method": "GET",
            "description": d.group(1) if d else "",
            "params": params,
            "response_type": rt.group(1) if rt else None,
        }
    return out


def main():
    shipped = parse_shipped(sys.argv[1])
    overlay = {e["path"]: e for e in json.load(open(sys.argv[2]))["entries"]}

    probe_type = {}
    for f in sys.argv[3:]:
        for line in open(f):
            r = json.loads(line)
            if r.get("http") == 200 and r.get("json_top"):
                probe_type[norm(r["path"])] = (
                    "array" if r["json_top"] == "list" else "object")

    # ---- assemble ---------------------------------------------------------
    endpoints = OrderedDict()

    def command_of(p, ov):
        """Shipped name wins, always. Rule 6 has no override path."""
        if p in shipped:
            return shipped[p]["resource"], shipped[p]["command"]
        if ov and ov.get("resource") and ov.get("command"):
            return ov["resource"], ov["command"]
        raise SystemExit(f"no command name for new endpoint {p} — a study must name it")

    # 1. every shipped endpoint, carried forward unconditionally
    for p, sh in shipped.items():
        if p in DENYLIST:
            raise SystemExit(f"DENYLIST contains a SHIPPED path ({p}); that is a "
                             f"regression, not a safety rule — resolve by hand")
        endpoints[p] = dict(sh)

    # 1b. lens D — routes the SPA never calls, recovered from Django's URLconf.
    # Same rules as any other source: only what a bare GET proved, never a
    # guessed value, writes denied by name before they can reach here.
    lensd = {}
    if LENS_D and os.path.exists(LENS_D):
        ld = json.load(open(LENS_D))
        for e in ld["publish"]:
            lensd[norm(e["path"])] = e
        for e in ld["excluded"]:
            DENYLIST.add(norm(e["path"]))
        # Routes whose NAME marks them a write (sync/push/approve/reject/
        # update/delete/cancel/generate/...). They were never probed and are
        # denied by construction, so no later source can publish one.
        for e in ld.get("writes_denied", []):
            DENYLIST.add(norm(e["path"]))

    for p, e in lensd.items():
        if p in endpoints or p in DENYLIST:
            continue
        endpoints[p] = {
            "resource": e["resource"], "command": e["command"],
            "raw_path": e["path"], "method": "GET",
            "description": e["description"], "params": [
                {"name": q["name"], "type": q.get("type", "string"),
                 "required": bool(q.get("required")), "positional": False,
                 "description": q.get("description", "")}
                for q in e.get("params", [])],
            "response_type": e.get("response"),
        }

    # 2. study-published endpoints that are new
    for p, ov in overlay.items():
        if ov["verdict"] != "publish" or p in endpoints or p in DENYLIST:
            continue
        res, cmd = command_of(p, ov)
        raw = ov["raw_path"]
        if "{}" in norm(raw) and "{" not in raw.replace("{}", ""):
            raise SystemExit(f"{p}: anonymous placeholder; a study must name it")
        endpoints[p] = {
            "resource": res, "command": cmd, "raw_path": raw, "method": "GET",
            "description": ov["description"], "params": [], "response_type": None,
        }

    # 3. overlay merge — studies may ADD params and supply the response type
    for p, e in endpoints.items():
        ov = overlay.get(p)
        have = {q["name"] for q in e["params"]}
        if ov:
            for q in ov["params"]:
                if q["name"] in have:
                    continue
                d = q.get("note", "")
                if q.get("enum"):
                    d = f"One of: {' | '.join(q['enum'])}. " + d
                e["params"].append({
                    "name": q["name"], "type": norm_type(q.get("type")),
                    "required": bool(q.get("required")),
                    "positional": bool(q.get("positional")),
                    "description": d[:300],
                })
                have.add(q["name"])
            if ov.get("description") and (p not in shipped or not e["description"]):
                e["description"] = ov["description"]
            if ov.get("response_type"):
                e["response_type"] = ov["response_type"]
        if not e["response_type"]:
            e["response_type"] = probe_type.get(p) or "object"
        # DOMAIN-WIDE CONTRACT, enforced in code rather than per study.
        #
        # The live server rejects a call to EVERY /api/hana/ endpoint that omits
        # `branch`, with its own words:
        #     {"error":"branch is required and must be one of: OIL, BEVERAGE"}
        # Measured on all 14, no exceptions. Leaving it to each study to declare
        # meant the two endpoints a study marked `exclude` (product-stock,
        # product-so - both broken upstream) carried forward WITHOUT it, so they
        # would still have returned 400 on the day the OMS team fixed their
        # crash. A contract the server enforces uniformly belongs in one place.
        if p.startswith("/api/hana/") and "branch" not in have:
            e["params"].insert(0, {
                "name": "branch", "type": "string",
                "required": True, "positional": False,
                "description": "SAP company database to read. One of: OIL | BEVERAGE. "
                               "Required by the server on every hana endpoint; the "
                               "figures differ per branch, so an answer without it "
                               "is meaningless.",
            })
            have.add("branch")

        ro = REFUTATION_OVERRIDES.get(p)
        if ro:
            for q in e["params"]:
                vals = ro.get("param_enums", {}).get(q["name"])
                if vals:
                    q["description"] = ("One of: " + " | ".join(vals) + ". "
                                        + q.get("description", ""))[:400]
            if ro.get("append_description"):
                e["description"] = (e["description"] + " " +
                                    ro["append_description"]).strip()

        if p in KNOWN_BROKEN:
            e["description"] = KNOWN_BROKEN[p] + " | " + e["description"]
        # a path placeholder is always a required positional param
        for name in re.findall(r"\{(\w+)\}", e["raw_path"]):
            if name not in have:
                e["params"].insert(0, {
                    "name": name, "type": "int" if name.endswith("id") else "string",
                    "required": True, "positional": True,
                    "description": f"{name} path parameter",
                })
                have.add(name)

    # ---- emit -------------------------------------------------------------
    src = open(sys.argv[1]).read()
    head = src.split("\nresources:")[0]
    head = re.sub(r'^version: ".*"$', 'version: "0.2.0"', head, flags=re.M)
    head = re.sub(
        r'^description: ".*"$',
        'description: ' + yq(
            "JIVO OMS (Order Management System) CLI — READ-ONLY. Orders, "
            "quotations, schemes, approvals, party & product assignments, the "
            "SAP Business One mirror, live SAP HANA stock and pricing, the "
            "invoice review queue, FSSAI label compliance, and the invoice "
            "tracker at oms.jivo.in. Every command is a GET; no mutating "
            "endpoint is wrapped. HANA commands require --branch (OIL or "
            "BEVERAGE) — it picks the SAP company database."),
        head, flags=re.M)

    out = [head, "", "resources:"]
    by_res = OrderedDict()
    for p, e in endpoints.items():
        by_res.setdefault(e["resource"], []).append((p, e))

    for res, items in by_res.items():
        out.append(f"  {res}:")
        desc = RESOURCE_DESC.get(res)
        if desc:
            out.append(f"    description: {yq(desc)}")
        out.append("    endpoints:")
        for p, e in items:
            out.append(f"      {e['command']}:")
            out.append("        method: GET")
            out.append(f"        path: {yq(e['raw_path'])}")
            out.append(f"        description: {yq(e['description'] or e['command'])}")
            if e["params"]:
                out.append("        params:")
                for q in e["params"]:
                    out.append(f"          - name: {q['name']}")
                    out.append(f"            type: {norm_type(q['type'])}")
                    if q["required"]:
                        out.append("            required: true")
                    if q["positional"]:
                        out.append("            positional: true")
                    if q["description"]:
                        out.append(f"            description: {yq(q['description'])}")
            out.append("        response:")
            out.append(f"          type: {norm_type(e['response_type'])}")

    bad = [l for l in out if lint(l)]
    if bad:
        print("YAML LINT FAILED — unquoted scalars containing ': ':", file=sys.stderr)
        for l in bad[:10]:
            print("   ", l, file=sys.stderr)
        sys.exit(1)

    print("\n".join(out))
    print(f"\nemitted {len(endpoints)} endpoints across {len(by_res)} resources "
          f"(shipped {len(shipped)}, new {len(endpoints)-len(shipped)})",
          file=sys.stderr)


if __name__ == "__main__":
    main()
