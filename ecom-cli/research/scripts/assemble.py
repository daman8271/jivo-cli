#!/usr/bin/env python3
"""Phase 5 — assemble the regenerated ecom spec.

Safety lives HERE, in code, not in the prose of a study. A domain study once
put a dangerous endpoint inside `endpoints[]` with the command name
"DO-NOT-PUBLISH" and a risk flag; its safety then depended on every downstream
tool remembering to read a magic string in a name field.

Four hard lists, all matched on NORMALISED paths (skill rule 8 — exact-string
membership fails open on exactly the entries most likely to have been renamed):

  DENYLIST       never published, whatever anything else says
  DEAD_PREFIXES  whole unrouted modules; per-path exclusion leaks {id} children
  KNOWN_BROKEN   5xx upstreams, excluded WITH the reason so they can come back
  POISON_PARAMS  params the endpoint accepts but that break it

Then the regression gate runs BEFORE anything else is emitted.
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

# ---------------------------------------------------------------- hard lists

# Every write the client makes, plus the writes only Lens A saw. Normalised.
# RULE 0: ecom is read-only. These are excluded structurally, not by convention.
DENYLIST = {norm(p) for p in [
    # auth
    "/api/auth/change-password", "/api/auth/feature-flags/update",
    # notifications
    "/api/notifications/mark-all-read", "/api/notifications/{}/mark-read",
    # chatbot
    "/api/chatbot/message",
    # dashboard inline editing
    "/api/dashboard/table-row/{}", "/api/dashboard/table-rows/{}",
    # platform targets + landing rate
    "/api/platform/month-targets/refresh",
    "/api/platform/primary-month-targets/refresh",
    "/api/platform/primary-month-targets/set-target",
    "/api/platform/{}/landing-rate/add", "/api/platform/{}/landing-rate/update",
    "/api/platform/{}/landing-rate/preview",
    "/api/platform/{}/landing-rate/bulk-upsert",
    "/api/platform/{}/month-targets/add",
    "/api/platform/{}/month-targets/refresh",
    "/api/platform/{}/month-targets/{}/refresh",
    "/api/platform/{}/month-targets/{}/update",
    "/api/platform/{}/primary-month-targets/add",
    "/api/platform/{}/primary-month-targets/refresh",
    "/api/platform/{}/primary-month-targets/{}/update",
    # reports
    "/api/reports/export",
    # shipment actions
    "/api/shipment/appointment-commits/manual-import",
    "/api/shipment/fc-channel", "/api/shipment/shipments/manual-plan",
    "/api/shipment/shipments/{}/approve", "/api/shipment/shipments/{}/dispatch",
    "/api/shipment/shipments/{}/reject", "/api/shipment/shipments/{}/submit",
    "/api/shipment/shipments/{}/items/{}",
    "/api/shipment/shipments/{}/switch/verify",
    "/api/shipment/shipments/{}/switch/email",      # Lens A, multipart POST
    # uploader CRUD
    "/api/upload/batch",
    "/api/upload/ads-master/add", "/api/upload/ads-master/update",
    "/api/upload/ads-master/delete", "/api/upload/ads-master/preview",
    "/api/upload/ads-master/bulk-upsert",
    "/api/upload/master-sheet/add", "/api/upload/master-sheet/update",
    "/api/upload/master-sheet/delete", "/api/upload/master-sheet/preview",
    "/api/upload/master-sheet/bulk-upsert",
    "/api/upload/pincode-mapping/add", "/api/upload/pincode-mapping/update",
    "/api/upload/pincode-mapping/delete", "/api/upload/pincode-mapping/preview",
    "/api/upload/pincode-mapping/bulk-upsert",
    # Lens A only - absent from every prior artefact
    "/api/upload/delete-by-date",          # DESTRUCTIVE bulk delete by date range
    "/api/upload/fk-grocery-master",
    "/api/upload/flipkart-grocery/reprocess",
    # auth mint/rotate: handled by the hand-authored `auth login`, not generated
    "/api/auth/login", "/api/auth/refresh",
]}

# Whole modules proven unrouted. None found on ecom this run: every 404 was a
# single leaf, and every module root answered. Kept as a live mechanism because
# a per-path exclusion would leak the {id} children we cannot probe.
DEAD_PREFIXES = []

KNOWN_BROKEN = {
    norm("/api/sap/sales-invoice-lines/{}"):
        "HTTP 500 on every DocEntry tried (37594, 37603, 37601, all from a live "
        "/api/sap/sales-invoices response): SAP HANA error (260) 'invalid column "
        "name: T1.UnitMsr'. Backend SQL defect, not data-dependent. Republish "
        "when fixed - see research/FINDINGS-FOR-ECOM-TEAM-2026-08.md item 1.",
}

PROVEN_DEAD = {
    norm("/api/platform/{}/month-on-month-sale"):
        "Django URL-resolver 404 (plain HTML, so slug-independent) on all of "
        "amazon, blinkit, zepto, swiggy, bigbasket, flipkart_grocery, zomato. "
        "The route no longer exists. Shipped as `platform month-on-month-sale` "
        "in v0.1.0; the current SPA no longer calls it either.",
}

POISON_PARAMS = {}      # none observed on ecom this run

# Platform restrictions the SERVER named, verbatim, in its own 400/404 bodies.
PLATFORM_RESTRICTED = {
    "/api/platform/{}/bigbasket-ads-dashboard": ["bigbasket"],
    "/api/platform/{}/bigbasket-ads-daily-dashboard": ["bigbasket"],
    "/api/platform/{}/blinkit-ads-dashboard": ["blinkit"],
    "/api/platform/{}/blinkit-brandfund-dashboard": ["blinkit"],
    "/api/platform/{}/blinkit-summary-report": ["blinkit"],
    "/api/platform/{}/flipkart-ads-dashboard": ["flipkart"],
    "/api/platform/{}/flipkart-fsn-dashboard": ["flipkart"],
    "/api/platform/{}/swiggy-ads-dashboard": ["swiggy"],
    "/api/platform/{}/swiggy-ads-daily-dashboard": ["swiggy"],
    "/api/platform/{}/swiggy-brandfund-dashboard": ["swiggy"],
    "/api/platform/{}/zepto-ads-dashboard": ["zepto"],
    "/api/platform/{}/zepto-ads-daily-dashboard": ["zepto"],
    "/api/platform/{}/zepto-brandfund-dashboard": ["zepto"],
    "/api/platform/{}/landing-rate":
        ["blinkit", "zepto", "swiggy", "bigbasket", "flipkart_grocery"],
    "/api/platform/{}/landing-rate/skus":
        ["blinkit", "zepto", "swiggy", "bigbasket", "flipkart_grocery"],
    "/api/platform/{}/monthly-sales-explorer":
        ["bigbasket", "blinkit", "swiggy", "zepto"],
    "/api/platform/{}/pendency-dashboard":
        ["blinkit", "zepto", "swiggy", "bigbasket"],
    "/api/platform/{}/region-doh-dashboard": ["swiggy", "zepto"],
}


def denied(path):
    p = norm(path)
    if p in DENYLIST:
        return "write endpoint (RULE 0)"
    if p in KNOWN_BROKEN:
        return "known broken upstream"
    if p in PROVEN_DEAD:
        return "proven dead"
    for pref in DEAD_PREFIXES:
        if p == pref or p.startswith(pref.rstrip("/") + "/"):
            return f"under dead prefix {pref}"
    return None


# ------------------------------------------------------------ regression gate

def regression_gate(old_paths, new_paths, verdicts):
    """Every endpoint the PREVIOUS spec published and the new one does not must
    carry a positive justification. Anything else is a BUG, not a result."""
    dropped = sorted(set(old_paths) - set(new_paths))
    ok, bugs = [], []
    for p in dropped:
        why = None
        if p in PROVEN_DEAD:
            why = "proven dead: " + PROVEN_DEAD[p]
        elif p in KNOWN_BROKEN:
            why = "proven broken: " + KNOWN_BROKEN[p]
        elif p in DENYLIST:
            why = "proven unsafe: write endpoint, RULE 0"
        else:
            st = (verdicts.get(p) or {}).get("status")
            if st == "DEAD":
                why = "proven dead: 404 on every value tried"
            elif st == "BROKEN_UPSTREAM":
                why = "proven broken: deterministic 5xx"
        (ok if why else bugs).append((p, why))
    return ok, bugs


# ------------------------------------------------------------- YAML emission

_NEEDS_QUOTE = re.compile(r'^\s|\s$|^$|^[-?:,\[\]{}#&*!|>\'"%@`]|: |#')


def yq(v):
    """Quote every scalar that could confuse a YAML parser.

    Two real failures this prevents: an agent emitted
    `type: string enum: IN | OUT` (embedded ': ' -> unparseable), and a
    carry-forward regex scraped the spec's own `config:` block and published
    `~/.config/<cli>/config.toml` as an endpoint under a `~` resource."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if _NEEDS_QUOTE.search(s) or s.lower() in ("true", "false", "null", "yes", "no", "on", "off", "~"):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def lint_scalar(s, where):
    """Lint the EMITTED form, not the raw value.

    Linting the raw value rejects a perfectly safe field just because its
    content happens to contain ': ' - the quoting helper exists precisely to
    make that safe. What must be checked is what actually lands in the file."""
    e = yq(s)
    if e.startswith('"') and e.endswith('"'):
        return                                   # quoted: safe by construction
    if ": " in e or e.startswith(("-", "?", ":", ",", "[", "]", "{", "}",
                                  "#", "&", "*", "!", "|", ">", "'", '"',
                                  "%", "@", "`")):
        raise SystemExit(f"YAML LINT: unsafe unquoted scalar in {where}: {e[:100]}")


def norm_type(t):
    """`type:` must be one bare token. Never 'string enum: A | B'."""
    t = (t or "object").strip().split()[0].strip(",")
    return t if t in ("object", "array", "string", "integer", "number", "boolean") else "object"


if __name__ == "__main__":
    verd = json.load(open(os.path.join(RUN, "probe", "probe-verdicts.json")))
    rec = json.load(open(os.path.join(RUN, "harvest", "reconciled.json")))
    old = {}
    for l in open(os.path.join(RUN, "harvest", "OLD-SPEC.tsv")):
        res, ep, p = l.rstrip("\n").split("\t")
        old[norm(p)] = (res, ep)

    publish, excluded = {}, {}
    for p, v in sorted(rec.items()):
        d = denied(p)
        if d:
            excluded[p] = d
            continue
        st = (verd.get(p) or {}).get("status")
        get_capable = "GET" in (v["methods"] or [])
        if not get_capable and p not in old:
            excluded[p] = "client never GETs it and it is new since v0.1.0"
            continue
        publish[p] = v

    ok, bugs = regression_gate(old.keys(), publish.keys(), verd)
    print(f"publish: {len(publish)}   excluded: {len(excluded)}")
    print(f"\n== REGRESSION GATE ==\ndropped vs v0.1.0: {len(ok) + len(bugs)}")
    for p, why in ok:
        print(f"  OK   {p}\n       {why[:150]}")
    if bugs:
        print("\n  *** UNJUSTIFIED DROPS - these are BUGS, not results ***")
        for p, _ in bugs:
            print(f"  BUG  {p}   status={(verd.get(p) or {}).get('status')}")
        raise SystemExit(1)
    print("\n  no unjustified drops")
    print("\n== status of published set ==",
          collections.Counter((verd.get(p) or {}).get("status") for p in publish))
    json.dump({"publish": sorted(publish), "excluded": excluded},
              open(os.path.join(HERE, "publish-set.json"), "w"), indent=1)
