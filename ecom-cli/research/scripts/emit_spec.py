#!/usr/bin/env python3
"""Emit the regenerated ecom spec.yaml.

Precedence for every field, strongest first:

  1. the SHIPPED v0.1.0 spec           - command name, description, params,
                                         enums. Never overwritten by anything
                                         weaker; regeneration must not lose
                                         metadata it already had.
  2. the LIVE PROBE                    - response type (observed, never the
                                         hardcoded `object` default), platform
                                         restrictions, required-param hints
  3. a DOMAIN STUDY overlay (optional) - descriptions and params for NEW
                                         endpoints, and additive params on
                                         existing ones

Rule 6 is enforced structurally: an endpoint present in the shipped spec keeps
its shipped `resource` AND `command` verbatim. There is no code path that can
rename one - `command_of()` returns the shipped pair or raises.
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(RUN, "harvest"))
from normalise import norm  # noqa: E402
from assemble import PLATFORM_RESTRICTED, yq, norm_type, lint_scalar  # noqa: E402

PLATFORM_SLUGS = ["amazon", "bigbasket", "blinkit", "citymall", "flipkart",
                  "flipkart_grocery", "jiomart", "swiggy", "zepto", "zomato"]

# New endpoints only. Existing ones keep their shipped names, always.
NEW_NAMES = {
    "/api/auth/feature-flags": ("account", "feature-flags"),
    "/api/dashboard/penetration-report": ("dashboard", "penetration-report"),
    "/api/dashboard/penetration-report/options": ("dashboard", "penetration-report-options"),
    "/api/platform/bigbasket/sales-explorer": ("platform", "bigbasket-sales-explorer"),
    "/api/platform/secondary-summary-version": ("platform", "secondary-summary-version"),
    "/api/platform/{}/blinkit-summary-report": ("platform", "blinkit-summary-report"),
    "/api/platform/{}/monthly-sales-explorer": ("platform", "monthly-sales-explorer"),
    "/api/reports/amazon-po/billing": ("reports", "amazon-po-billing"),
    "/api/reports/amazon-po/sku-pendency": ("reports", "amazon-po-sku-pendency"),
    "/api/reports/amazon-po/sku-pendency/filter-options": ("reports", "amazon-po-sku-pendency-filter-options"),
    "/api/reports/live/data": ("reports", "live-data"),
    "/api/reports/live/reports": ("reports", "live-reports"),
    "/api/shipment/appointments/{}/families": ("shipment", "appointment-families"),
    "/api/shipment/fc-switch-group": ("shipment", "fc-switch-group"),
    "/api/shipment/po-appointments": ("shipment", "po-appointments"),
}

RESOURCE_DESC = {
    "account": "Authenticated account: current user, permissions and feature flags",
    "chatbot": "Read-only access to the ecom app's built-in assistant (health + conversation history)",
    "dashboard": "Top-level analytics dashboards aggregated across all platforms",
    "master": "Master data: product catalogue and fulfilment centres",
    "notifications": "Read-only notifications with unread count",
    "platform": ("Per-platform dashboards. Many routes are restricted to specific "
                 "platforms - see the platform column in DOMAIN-GUIDE-2026-08.md"),
    "reports": "Report views: Amazon PO, appointment, and raw report tables",
    "sap": "SAP HANA read layer: distributors, inventory, sales invoices, stock",
    "shipment": ("Amazon Shipment Planner (read-only). Requires the "
                 "amazon.shipment_planning.view permission; returns 403 without it."),
    "tables": "Dynamic data-table browser over the underlying warehouse tables",
    "upload": "Read-only views of uploaded reference data",
    "uploads": "Upload job history (read-only)",
}


def path_params(path, overlay_names=None, shipped_names=None):
    """Named path placeholders.

    Priority: the SHIPPED names first - they are the operator-facing flag names
    and changing one is a breaking change. Then the names lens C read out of the
    app's own source (`{table}`, `{card_code}`). Deriving a name from the
    preceding path segment is only a last resort and produces nonsense like
    `{expiry_alert}` for a segment that actually holds a table name."""
    n_slots = path.count("{}")
    if shipped_names and len(shipped_names) == n_slots:
        return list(shipped_names)
    if overlay_names and len(overlay_names) == n_slots:
        return list(overlay_names)
    segs = [s for s in path.split("/") if s]
    names, prev = [], None
    for s in segs:
        if s == "{}":
            if prev == "platform":
                names.append("platform")
            elif prev:
                names.append(re.sub(r"[^a-z0-9]+", "_", prev.rstrip("s").lower()) or "id")
            else:
                names.append("id")
        prev = s
    seen, out = collections.Counter(), []
    for n in names:
        seen[n] += 1
        out.append(n if seen[n] == 1 else f"{n}_{seen[n]}")
    return out


def main():
    pubset = json.load(open(os.path.join(HERE, "publish-set.json")))
    oldmeta = json.load(open(os.path.join(HERE, "old-spec-meta.json")))
    verd = json.load(open(os.path.join(RUN, "probe", "probe-verdicts.json")))
    rec = json.load(open(os.path.join(RUN, "harvest", "reconciled.json")))
    canon = json.load(open(os.path.join(HERE, "canonical-paths.json")))
    lensc = json.load(open(os.path.join(HERE, "lensc-overlay.json")))
    overlay = {}
    op = os.path.join(HERE, "study-overlay.json")
    if os.path.exists(op):
        overlay = json.load(open(op))
        print(f"study overlay: {len(overlay)} entries")
    print(f"lens C overlay: {len(lensc)} paths")

    def command_of(p):
        if p in oldmeta:
            return oldmeta[p]["resource"], oldmeta[p]["command"]
        if p in NEW_NAMES:
            return NEW_NAMES[p]
        raise SystemExit(f"no command name for {p} - add it to NEW_NAMES; "
                         f"never auto-generate a name that could collide with a shipped one")

    groups = collections.defaultdict(dict)
    renames = []
    for p in pubset["publish"]:
        res, cmd = command_of(p)
        if p in oldmeta and (res, cmd) != (oldmeta[p]["resource"], oldmeta[p]["command"]):
            renames.append(p)                      # structurally impossible; belt and braces
        v = verd.get(p, {})
        r = rec.get(p, {})
        o = oldmeta.get(p, {})
        ov = overlay.get(p, {})

        desc = ov.get("description") or o.get("description") or ""
        if not desc:
            fn = (r.get("fn_names") or [None])[0]
            desc = f"{cmd.replace('-', ' ').capitalize()}" + (f" ({fn})" if fn else "")
        if ov.get("append_description"):
            desc = desc.rstrip(". ") + "." + ov["append_description"]

        # response type: OBSERVED, never the hardcoded default. The shipped spec
        # declared `object` for all 138 and was never checked.
        rtype = norm_type(v.get("sample_shape") or o.get("response_type") or "object")

        params = {pp["name"]: dict(pp) for pp in o.get("params", [])}
        # lens C sits between the shipped spec and the study: it is machine-read
        # from the app's own source, so it fills gaps and adds enums, but a
        # hand-written study correction still wins over it.
        for pp in lensc.get(p, {}).get("params", []):
            nm = pp["name"]
            base = params.get(nm, {"name": nm, "type": "string", "description": "",
                                   "enum": [], "required": False})
            if pp.get("type") and base.get("type") in (None, "", "string"):
                base["type"] = pp["type"]
            if pp.get("description") and not base.get("description"):
                base["description"] = pp["description"]
            if pp.get("required"):
                base["required"] = True
            if pp.get("enum") and not base.get("enum"):
                base["enum"] = pp["enum"]
            params[nm] = base
        for pp in ov.get("params", []):
            nm = pp.get("name")
            if not nm:
                continue
            base = params.get(nm, {"name": nm, "type": "string", "description": "",
                                   "enum": [], "required": False})
            for k in ("type", "description", "required"):
                if pp.get(k):
                    base[k] = pp[k]
            if pp.get("enum"):
                base["enum"] = pp["enum"]
            params[nm] = base

        # A correction may deliberately rename a path placeholder when the
        # shipped one was semantically wrong (expiry-alerts' `{platform}` really
        # holds a table name). That changes an operator-facing flag, so it is
        # opt-in per endpoint and recorded in the migration doc - never implicit.
        shipped_names = o.get("placeholders") or None
        if ov.get("drop_params"):
            shipped_names = None
        slots = path_params(p, lensc.get(p, {}).get("path_param_names"), shipped_names)
        for nm in slots:
            base = params.get(nm, {"name": nm, "type": "string", "description": "",
                                   "enum": [], "required": True})
            base["required"] = True
            if nm == "platform":
                allowed = PLATFORM_RESTRICTED.get(p) or PLATFORM_SLUGS
                base["enum"] = allowed
                if p in PLATFORM_RESTRICTED:
                    base["description"] = ("Platform slug. This endpoint is served ONLY for: "
                                           + ", ".join(allowed))
                elif not base["description"]:
                    base["description"] = "Platform slug"
            params[nm] = base

        # A correction may DROP a parameter the shipped spec got wrong. Without
        # this, expiry-alerts ships both `platform` (wrong, inherited) and
        # `table` (right, corrected) for a path with one placeholder.
        for nm in ov.get("drop_params", []):
            params.pop(nm, None)

        hint = v.get("param_hint")
        note = ""
        if hint:
            # The 400 body is raw JSON/DRF list. Keep the server's own wording -
            # it is the authoritative statement of what is required - but strip
            # the JSON scaffolding so the description reads as a sentence.
            h = re.sub(r"\s+", " ", str(hint)).strip()
            h = re.sub(r'^\s*[\[\{]\s*', "", h)
            h = re.sub(r'\s*[\]\}]\s*$', "", h)
            h = re.sub(r'^"?detail"?\s*:\s*', "", h)
            h = re.sub(r'^"?error"?\s*:\s*', "", h)
            h = h.strip().strip('"').strip()
            note = " Server requires: " + h[:150]
        if v.get("status") == "GATED":
            note += (" Requires additional permission; returns 403 otherwise. "
                     "Response shape UNVERIFIED (could not be read this run).")
        if v.get("status") == "LIVE_PARTIAL":
            note += " Served only for: " + ", ".join(v.get("available_for", []))

        # Emit the wire path with NAMED placeholders. The press substitutes by
        # matching a placeholder name against a declared param; an anonymous
        # `{}` disables substitution silently, and the CLI then sends the
        # literal brace - `GET /api/platform/{}/blinkit-ads-dashboard` -> 404.
        # Build passed, tests passed, patch checks passed; only an end-to-end
        # run caught it.
        wire = canon.get(p, p)
        for nm in slots:
            wire = wire.replace("{}", "{" + nm + "}", 1)
        if "{}" in wire:
            raise SystemExit(f"unfilled placeholder in {wire} (slots={slots})")

        groups[res][cmd] = {
            # the WIRE path, trailing slash included where the server needs one
            "method": "GET", "path": wire,
            "description": (desc + note).strip(),
            "params": [params[k] for k in params],
            "response_type": rtype,
        }

    if renames:
        raise SystemExit(f"RENAME DETECTED for {renames} - refusing to emit")

    # -------------------------------------------------------------- emit YAML
    L = []
    A = L.append
    A("name: jivo-ecom")
    A("description: " + yq(
        "JIVO e-commerce & quick-commerce analytics CLI (ecom.jivo.in) - read-only "
        "dashboards, master data, notifications, SAP mirror, Amazon PO reporting and "
        "per-platform metrics across Amazon, Blinkit, Zepto, Swiggy, BigBasket, "
        "Flipkart, Citymall, JioMart, Zomato"))
    A("version: 0.2.0")
    A("base_url: https://ecom.jivo.in")
    A("health_check_path: /api/auth/me")
    A("auth:")
    A("  type: bearer_token")
    A("  header: Authorization")
    A("  format: Bearer {token}")
    A("  env_vars:")
    A("  - JIVO_ECOM_TOKEN")
    A("config:")
    A("  format: toml")
    A("  path: ~/.config/jivo-ecom-pp-cli/config.toml")
    A("resources:")
    for res in sorted(groups):
        A(f"  {res}:")
        A(f"    description: {yq(RESOURCE_DESC.get(res, res))}")
        A("    endpoints:")
        for cmd in sorted(groups[res]):
            e = groups[res][cmd]
            lint_scalar(e["description"], f"{res}.{cmd}.description")
            A(f"      {cmd}:")
            A("        method: GET")
            A(f"        path: {yq(e['path'])}")
            A(f"        description: {yq(e['description'])}")
            if e["params"]:
                A("        params:")
                for pp in e["params"]:
                    A(f"        - name: {yq(pp['name'])}")
                    A(f"          type: {norm_type(pp.get('type') or 'string')}")
                    if pp.get("description"):
                        lint_scalar(pp["description"], f"{res}.{cmd}.{pp['name']}")
                        A(f"          description: {yq(pp['description'])}")
                    if pp.get("required"):
                        A("          required: true")
                    if pp.get("enum"):
                        A("          enum:")
                        for ev in pp["enum"]:
                            A(f"          - {yq(ev)}")
            A("        response:")
            A(f"          type: {e['response_type']}")

    # ---------------------------------------------------- structural assertions
    # Every path placeholder must have a declared param of the same name, or the
    # press emits a command that sends the literal brace to the server. Nothing
    # else in the pipeline catches this: the spec parses, the code generates, the
    # build and the whole test suite pass, and the failure only appears when a
    # human runs the command against the live API.
    problems = []
    for res, cmds in groups.items():
        for cmd, e in cmds.items():
            declared = {pp["name"] for pp in e["params"]}
            for ph in re.findall(r"\{([^{}]*)\}", e["path"]):
                if not ph:
                    problems.append(f"{res} {cmd}: anonymous placeholder in {e['path']}")
                elif ph not in declared:
                    problems.append(f"{res} {cmd}: path placeholder {{{ph}}} has no declared param "
                                    f"(declared: {sorted(declared)})")
    if problems:
        print("SPEC STRUCTURE ERRORS:")
        for p in problems:
            print("  ", p)
        raise SystemExit(1)
    print(f"structure ok: every path placeholder has a matching declared param")

    out = "\n".join(L) + "\n"
    dest = os.path.join(HERE, "spec-v0.2.0.yaml")
    open(dest, "w").write(out)
    n = sum(len(v) for v in groups.values())
    print(f"emitted {n} endpoints in {len(groups)} resources -> {dest}")
    print("resources:", {k: len(v) for k, v in sorted(groups.items())})
    types = collections.Counter(e["response_type"] for g in groups.values() for e in g.values())
    print("response types:", dict(types))
    print("total params:", sum(len(e["params"]) for g in groups.values() for e in g.values()))


if __name__ == "__main__":
    main()
