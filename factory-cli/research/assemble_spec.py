#!/usr/bin/env python3
"""Assemble spec.yaml v0.4.0 for the Printing Press from the domain study.

Inputs
  domain-learn workflow journal  — 20 per-domain specs, each already passed
                                   through an adversarial verifier
  HARVEST.json                   — 796 endpoints with methods + live probe status
  the existing spec.yaml         — the shape and the 19 good param declarations

Safety rules enforced here, in code, so they cannot be lost to a prompt:
  * publish ONLY endpoints with GET in their methods (dual-use paths publish
    the GET and nothing else — 141 of them)
  * never publish an endpoint flagged with any side-effect risk
  * never publish the hard denylist (/marketplace/settings/ — GET creates rows)
  * never publish an endpoint the live probe proved dead (404) or write-only (405)

PyYAML is not available in this environment, so YAML is emitted by hand. The
schema is shallow and fully controlled, so this is safe as long as every scalar
goes through q().
"""
import json
import os
import re
import sys
import collections

SP = os.path.dirname(os.path.abspath(__file__))
WF = "/Users/damanpreetsingh/.claude/projects/-Users-damanpreetsingh-jivo-cli/e035ad0b-bcf0-443b-b65c-4a94696c4409/subagents/workflows/wf_82833d3b-265/journal.jsonl"
REPO = "/Users/damanpreetsingh/jivo-cli/factory-cli"

# Endpoints that must never be published, whatever any agent concluded.
DENYLIST = {
    # GET is a get_or_create — provably creates rows (C-0007, patch 0007).
    "/marketplace/settings/",
    # Natural-key lookup (channel + order_id) on a verb that plausibly writes a
    # resolution. Unproven, and a natural key carries enough information to
    # construct a row — which is exactly how /marketplace/settings/ bit us.
    # Unproven resolves to excluded, never to "probably fine".
    "/marketplace/orders/resolve/",
    # The ".../view/" routes: suspected get_or_create, deliberately never probed
    # because the only way to test is to call one with a parent id that has no
    # child record — the act that would create it. Both placeholder spellings
    # and both slash forms are listed: the harvest and the domain studies
    # disagree on {id} vs {entry_id} and on the trailing slash, and a denylist
    # that misses on a spelling is not a denylist.
    "/security-checks/gate-entries/{id}/security/view",
    "/security-checks/gate-entries/{id}/security/view/",
    "/weighment/gate-entries/{id}/weighment/view",
    "/weighment/gate-entries/{id}/weighment/view/",
    "/raw-material-gatein/gate-entries/{id}/po-receipts/view",
    "/raw-material-gatein/gate-entries/{id}/po-receipts/view/",
    "/raw-material-gatein/gate-entries/{entry_id}/po-receipts/view",
    "/raw-material-gatein/gate-entries/{entry_id}/po-receipts/view/",
    # "get or create a DRAFT for this posting" is the textbook get_or_create
    # phrasing, and the parent posting id is sufficient to construct the child
    # draft. A verifier flagged it; the collection form /grpo/draft/ is already
    # HTTP 500 upstream, so nobody can even observe the safe behaviour to
    # confirm it. Unproven resolves to excluded.
    "/grpo/draft/{posting_id}/",
    "/grpo/draft/{id}/",
}


def denied(path):
    """Denylist match that cannot be defeated by a placeholder spelling.

    Two domain agents classified structurally identical ".../view/" endpoints
    differently, and the harvest and studies spell the placeholder {id} vs
    {entry_id} with and without a trailing slash. Comparing normalised forms
    means a rename cannot silently re-publish an excluded endpoint.
    """
    def norm(p):
        return re.sub(r"\{[^}]*\}", "{}", p).rstrip("/")
    n = norm(path)
    return any(norm(d) == n for d in DENYLIST)
# Broken upstream, not dangerous — excluded because a command that only ever
# errors is worse than an absent one. Each is documented in
# research/SPEC-NOTES-2026-08.md so it can be published the day it is fixed.
KNOWN_BROKEN = {
    "/grpo/draft/",                       # HTTP 500 (Django error page), all three companies
}

# Params that must NOT be declared even though the endpoint accepts them,
# because supplying them breaks the call.
POISON_PARAMS = {
    # /marketplace/reconciliation/ returns HTTP 500 when given either date bound;
    # it works correctly with neither. Publish the endpoint, omit the params.
    "/marketplace/reconciliation/": {"from_date", "to_date"},
}

# Whole URL prefixes that are not routed at all. Django routing is prefix-based:
# if the module root 404s, its include() is not registered in urls.py and EVERY
# child 404s too — including the {id} sub-routes that cannot be probed directly
# for want of a real id. Excluding per-path would leak those children through,
# which is exactly what happened before this was added.
DEAD_PREFIXES = (
    # Every non-parameterised path 404s on all three companies, root included,
    # with Django's bare "Not Found" page. The SPA ships Production Planning
    # screens whose backend is not deployed. Reported in SPEC-NOTES; the CLI
    # cannot cover the gap.
    "/production-planning/",
)

# Live-proven dead: eight WMS endpoints that 404 since the warehouse restructure.
DEAD_404 = {
    "/warehouse/wms/dashboard/", "/warehouse/wms/stock/overview/",
    "/warehouse/wms/warehouses/summary/", "/warehouse/wms/batches/expiry/",
    "/warehouse/wms/billing/overview/", "/warehouse/wms/sales-orders/backlog/",
    "/warehouse/wms/stock/movements/", "/warehouse/wms/transfers/overview/",
}


def q(s):
    """Quote a scalar for YAML, always. Never emit a bare string."""
    if s is None:
        return "''"
    s = str(s).replace("\r", " ").replace("\n", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return "'" + s.replace("'", "''") + "'"


def load_domain_specs():
    # Preferred input: DOMAINS.json from apply_verdicts.py — the 20 studies with
    # every adversarial verdict applied. The workflow's own final return value
    # never reached the journal, so reconstructing it there is not just a
    # fallback, it is the only path that includes the two verdicts that had to
    # be re-run standalone after transport failures.
    dj = os.path.join(SP, "DOMAINS.json")
    if os.path.exists(dj):
        d = json.load(open(dj))
        unver = [x["group"] for x in d["domains"] if not x.get("verified_adversarially")]
        if unver:
            print(f"  WARNING: shipping WITHOUT adversarial review: {unver}")
        return d
    if not os.path.exists(WF):
        sys.exit(f"no domain-learn journal at {WF} — run phase 3 first")
    final = None
    for line in open(WF):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "result":
            continue
        r = d.get("result")
        if isinstance(r, str):
            try:
                r = json.loads(r)
            except Exception:
                continue
        if isinstance(r, dict) and "domains" in r:
            final = r
    if final is None:
        sys.exit("domain-learn has not produced its final result yet")
    return final


def load_harvest():
    h = json.load(open(os.path.join(SP, "HARVEST.json")))["endpoints"]
    return {e["path"]: e for e in h}


def cmd_name(path, domain):
    """Stable, kebab-case leaf command name derived from the path."""
    tail = path.strip("/")
    if tail.startswith(domain + "/"):
        tail = tail[len(domain) + 1:]
    tail = tail.replace("{id}", "by-id")
    parts = [p for p in tail.split("/") if p]
    return "-".join(parts) or "list"


def main():
    study = load_domain_specs()
    harvest = load_harvest()

    kept, dropped = [], collections.Counter()
    seen = set()

    for dom in study["domains"]:
        for e in dom.get("endpoints", []):
            path = e.get("path", "")
            if not path.startswith("/"):
                path = "/" + path
            e["path"] = path          # write it back: everything downstream reads e["path"]
            if path in seen:
                dropped["duplicate"] += 1
                continue

            if denied(path):
                dropped["denylist (mutates on GET)"] += 1
                continue
            if path in DEAD_404:
                dropped["dead 404 (WMS restructure)"] += 1
                continue
            if any(path.startswith(p) for p in DEAD_PREFIXES):
                dropped["unrouted module (prefix 404s)"] += 1
                continue
            if path in KNOWN_BROKEN:
                dropped["known-broken upstream (HTTP 500)"] += 1
                continue
            risk = (e.get("side_effect_risk") or "none").lower()
            if risk != "none":
                dropped[f"side-effect risk: {risk}"] += 1
                continue

            h = harvest.get(path)
            methods = (h or {}).get("methods") or []
            live = (h or {}).get("live_status") or {}
            # LIVE EVIDENCE BEATS CODE EVIDENCE. The harvest's methods are what
            # the React app CALLS, not what the server ALLOWS — a DRF ViewSet
            # routinely serves GET on a path the UI only ever POSTs to. Four
            # maintenance lookup endpoints (asset-categories, asset-departments,
            # asset-locations, spare-categories) are recorded POST-only because
            # the UI only creates through them, yet they return 200 on a bare
            # GET and v0.3.0 ships them. Dropping those as "write-only" silently
            # shrinks the CLI. A live 200 is proof the GET exists; nothing the
            # bundle says can override it.
            if methods and "GET" not in methods and 200 not in live.values():
                dropped["write-only"] += 1
                continue
            live = (h or {}).get("live_status") or {}
            if live and 200 not in live.values() and 400 not in live.values() and 403 not in live.values():
                # probed and never usable — 404/405/500 everywhere
                dropped[f"probe says unusable ({sorted(set(live.values()))})"] += 1
                continue

            seen.add(path)
            kept.append((dom, e, h))

    # ------------------------------------------------------------------
    # CARRY FORWARD v0.3.0. A regeneration must never silently ship a SMALLER
    # CLI than the one it replaces. Any endpoint the previous spec published is
    # re-published unless there is positive evidence against it: proven dead
    # (404/5xx), denylisted, or in a dead prefix. Twenty domain agents working
    # in parallel will each miss something — /barcode/dispatch/sessions/from-bill/
    # and /company/companies/ were simply never proposed by any of them — and an
    # operator whose command disappears has no way to know whether it was
    # deliberate. Absence of evidence is not evidence of absence.
    # ------------------------------------------------------------------
    # Paths any adversarial verdict removed. The carry-forward must respect
    # these: without it, restoring "everything v0.3.0 shipped" silently
    # resurrected three endpoints the verifiers had flagged as unsafe
    # (/barcode/dispatch/settings/, /notifications/preferences/,
    # /gate-core/sales-dispatch/lock/). A regression fix must not become a
    # safety regression.
    kills_path = os.path.join(SP, "VERDICT-KILLS.json")
    verdict_kills = set(json.load(open(kills_path))) if os.path.exists(kills_path) else set()

    prev_paths = re.findall(r"^\s+path:\s*(\S+)", open(os.path.join(REPO, "spec.yaml")).read(), re.M)
    prev_meta = {}
    cur = None
    for line in open(os.path.join(REPO, "spec.yaml")):
        m = re.match(r"^  ([a-z0-9-]+):\s*$", line)
        if m:
            cur = m.group(1)
        m = re.match(r"^\s+path:\s*(\S+)", line)
        if m:
            prev_meta[m.group(1)] = cur
    carried = 0
    for p in prev_paths:
        if p in seen or denied(p) or p in DEAD_404 or p in KNOWN_BROKEN:
            continue
        if p in verdict_kills:
            continue                                  # a verifier ruled it unsafe
        if any(p.startswith(pre) for pre in DEAD_PREFIXES):
            continue
        h = harvest.get(p) or {}
        live = h.get("live_status") or {}
        if live and 200 not in live.values() and 400 not in live.values():
            continue                                  # positively proven dead
        # a v0.3.0 endpoint no study proposed and nothing proves dead — keep it
        seen.add(p)
        dom = type("D", (), {"get": lambda self, k, d=None: ""})()
        kept.append(({"overview": "", "group": (prev_meta.get(p) or path_domain(p))},
                     {"path": p,
                      "command_name": cmd_name(p, (prev_meta.get(p) or path_domain(p))),
                      "description": f"GET {p}",
                      "required_params": [], "optional_params": [],
                      "carried_from": "v0.3.0"}, h))
        carried += 1
    if carried:
        print(f"  carried forward from v0.3.0 (no study proposed them, nothing proves them dead): {carried}")

    # group by resource
    resources = collections.OrderedDict()
    for dom, e, h in kept:
        domain = (h or {}).get("domain") or path_domain(e["path"])
        resources.setdefault(domain, {"description": dom.get("overview", "")[:200], "endpoints": []})
        resources[domain]["endpoints"].append((e, h))

    out = []
    w = out.append
    w("# GENERATED for the Printing Press — jivo-factory v0.4.0")
    w("# Re-scraped and live-verified 2026-08-03. READ-ONLY: GET endpoints only,")
    w("# and only those cleared of side effects (see patch 0007 / correction C-0007).")
    w("name: jivo-factory")
    w("description: " + q(
        "JIVO factory management CLI (ji.jivo.in / factory.jivo.in) — read-only access across "
        "JIVO_MART, JIVO_OIL and JIVO_BEVERAGES via --company: gate, vehicles, quality control, "
        "GRPO, barcode traceability, dispatch, production, WMS, maintenance, marketplace "
        "fulfilment, bottle blowing, labour and dashboards"))
    w("version: 0.4.0")
    w("base_url: https://factory.jivo.in/api/v1")
    w("health_check_path: /accounts/me/")
    w("category: developer-tools")
    w("required_headers:")
    w("- name: Company-Code")
    w("  value: JIVO_MART")
    w("auth:")
    w("  type: bearer_token")
    w("  header: Authorization")
    w("  format: Bearer {token}")
    w("  env_vars:")
    w("  - JIVO_FACTORY_TOKEN")
    w("config:")
    w("  format: toml")
    w("  path: ~/.config/jivo-factory-pp-cli/config.toml")
    w("resources:")

    n_ep = 0
    for rname, r in sorted(resources.items()):
        w(f"  {rname}:")
        w("    description: " + q(r["description"] or rname))
        w("    endpoints:")
        used = set()
        for e, h in sorted(r["endpoints"], key=lambda x: x[0]["path"]):
            name = e.get("command_name") or cmd_name(e["path"], rname)
            name = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-") or "list"
            base, i = name, 2
            while name in used:
                name = f"{base}-{i}"; i += 1
            used.add(name)

            req = e.get("required_params") or []
            desc = e.get("description") or f"GET {e['path']}"
            if req:
                desc = desc.rstrip(". ") + ". Required: " + ", ".join(p["name"] for p in req) + "."

            w(f"      {name}:")
            w("        method: GET")
            w(f"        path: {e['path']}")
            w("        description: " + q(desc))
            w("        response:")
            w(f"          type: {response_type(e['path'])}")
            poison = POISON_PARAMS.get(e["path"], set())
            params = []
            for p in req:
                if p.get("name") in poison:
                    continue
                params.append((p.get("name"), p.get("type") or "string", True, p.get("note") or ""))
            for p in (e.get("optional_params") or []):
                if p.get("name") in poison:
                    continue
                params.append((p.get("name"), p.get("type") or "string", False, p.get("note") or ""))
            if params:
                w("        params:")
                for pname, ptype, prequired, pnote in params:
                    if not pname:
                        continue
                    w(f"        - name: {pname}")
                    w(f"          type: {ptype}")
                    if prequired:
                        w("          required: true")
                    if pnote:
                        w("          description: " + q(pnote))
            n_ep += 1

    path = os.path.join(SP, "spec-0.4.0.yaml")
    open(path, "w").write("\n".join(out) + "\n")

    print(f"spec-0.4.0.yaml written: {len(resources)} resources, {n_ep} endpoints")
    print(f"  (current shipped spec: 183 endpoints)")
    print("\ndropped:")
    for k, v in dropped.most_common():
        print(f"  {v:4}  {k}")


def path_domain(p):
    return p.strip("/").split("/")[0].lower().replace("_", "-")


_SHAPES = None


def response_type(path):
    """The response type the LIVE probe observed — never a hardcoded default.

    The shipped v0.3.0 spec declares `type: object` for every endpoint, which is
    wrong for 104 of the 154 it covers: they return a bare JSON array. The
    declared type drives how the generated CLI and MCP parse the payload, so
    reproducing that default would reproduce the defect. Fall back to `object`
    only for endpoints the probe never saw return 200 (parameterised {id}
    routes, mostly), where we genuinely do not know.
    """
    global _SHAPES
    if _SHAPES is None:
        _SHAPES = {}
        for fn in ("probe-mart.jsonl", "probe-oil-bev.jsonl"):
            p = os.path.join(SP, fn)
            if not os.path.exists(p):
                continue
            for line in open(p):
                r = json.loads(line)
                if r.get("http") != 200 or r["path"] in _SHAPES:
                    continue
                _SHAPES[r["path"]] = "array" if isinstance(r.get("shape"), list) else "object"
    return _SHAPES.get(path, "object")


if __name__ == "__main__":
    main()
