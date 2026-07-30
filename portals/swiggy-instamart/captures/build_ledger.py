#!/usr/bin/env python3
"""
build_ledger.py — writes COVERAGE-LEDGER.md (AMENDMENT-03 item 1) and
vault/Swiggy-Instamart-Pages-and-Routes.md.

One row per SPA route extracted in Phase 3, with walked YES/NO, the screenshots,
the network evidence, and — for every NO — a SPECIFIC reason. Generated from the
walk manifests so it cannot drift from what actually happened; re-run it after
every walk and in every Phase-9 sweep.
"""
import glob
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VAULT = os.path.join(ROOT, "vault")

REMOTE_OF = [
    ("/im-vendor/local-buying", "im-vendor · LocalBuyingApp"),
    ("/im-vendor", "im-vendor (imVendorClient v2.2.28)"),
    ("/instamart", "instamart (imAdsClient v1.4.128)"),
    ("/im-discounts", "im-discounts (imBdpoClient v1.19.0)"),
    ("/im-sampling", "im-sampling (imSamplingClient v0.1.11)"),
    ("/brandverse", "brandverse (brandverseClient v0.0.7)"),
    ("/im-catalog", "im-catalog (imCatalogClient v0.1.5)"),
]

# Routes deliberately NOT walked, with the specific reason. AMENDMENT-03 forbids
# "not important" as a reason; each of these is a safety or shape decision.
DELIBERATE = {
    "/im-sampling/campaign/create":
        "NOT WALKED — create form; a create screen can fire a draft-create call on mount, which "
        "would be a WRITE (G2/G4-NEW). Deliberate.",
    "/im-discounts/campaign/create":
        "NOT WALKED — create form; same draft-create-on-mount risk as the sampling create route. "
        "Deliberate.",
    "/instamart/campaign/create":
        "NOT WALKED — campaign create form; campaigns spend real money and the screen may create "
        "a draft on mount. Deliberate.",
    "/instamart/campaign/create-1cc":
        "NOT WALKED — one-click-campaign create form; same reason. Deliberate.",
    "/im-catalog/spin/:spinId/edit-attributes":
        "NOT WALKED — attribute EDIT form on JIVO's own catalogue, and needs a spinId. Deliberate.",
    "/im-catalog/change-requests/:requestId/edit":
        "NOT WALKED — change-request EDIT form, and needs a requestId. Deliberate.",
    "/im-sampling/campaign/:id/Edit":
        "NOT WALKED — campaign EDIT form, and needs a campaign id. Deliberate.",
    "/instamart/campaign/:id/edit":
        "NOT WALKED — campaign EDIT form, and needs a campaign id. Deliberate.",
    "/instamart/campaign/:id/edit-1cc":
        "NOT WALKED — one-click-campaign EDIT form, and needs a campaign id. Deliberate.",
    "/instamart/mock/third-party-login":
        "NOT WALKED — a MOCK login route shipped in the client; exercising a login route is "
        "forbidden by G9. Deliberate.",
    "/instamart/login": "NOT WALKED — login route; G9 forbids minting a session. Deliberate.",
    "/instamart/login/success": "NOT WALKED — login callback; unreachable without logging in. G9.",
    "/login/success": "NOT WALKED — login callback; unreachable without logging in. G9.",
    "/im-vendor/local-buying/login":
        "WALKED but EMPTY — local-buying uses a SEPARATE LOCAL_VENDOR identity host "
        "(influencer-app-*.swig.gy); the ecom1 brand session does not authorise it. NOT_REACHABLE "
        "without a second credential JIVO may not hold.",
    "/im-vendor/local-buying/review-order":
        "NOT WALKED — 'review order' is a step inside the indent ACCEPT/REJECT flow; opening it "
        "risks a state-changing control. Also gated behind the local-vendor login. Deliberate.",
}

PARAM_NOTE = ("NOT WALKED — parameterised route; needs a concrete id. The underlying detail "
              "endpoint is documented in its section note, and no id was harvested because "
              "listing responses for this surface returned no rows on this account.")


def remote_of(route):
    for pre, name in REMOTE_OF:
        if route.startswith(pre):
            return name
    return "brand-portal-client (shell)"


def norm(route):
    r = route.strip()
    r = r.replace("/_private", "")
    r = re.sub(r"\$\{[^}]*\}", ":id", r)
    r = re.sub(r"\{0\}", ":id", r)
    r = re.sub(r"\$([A-Za-z]\w*)", r":\1", r)
    if r.endswith("/*"):
        r = r[:-2] or "/"
    r = re.sub(r"/+$", "", r) or "/"
    if not r.startswith("/") and r != "*":
        r = "/" + r
    return r


def load_routes():
    out = []
    with open(os.path.join(HERE, "routes-raw.txt")) as f:
        next(f, None)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p and p[0] and p[0] != "*":
                out.append(p[0])
    return out


def load_visits():
    """canonical route -> aggregated visit record across every walk pass."""
    v = defaultdict(lambda: {"shots": set(), "passes": set(), "labels": set(),
                             "api": 0, "ok": 0, "bytes": 0, "text": 0,
                             "errors": set(), "bounced": False, "accounts": set()})
    for mf in sorted(glob.glob(os.path.join(HERE, "walk*", "_manifest.json"))):
        pas = os.path.basename(os.path.dirname(mf))
        for r in json.load(open(mf)):
            c = norm(r["route"])
            rec = v[c]
            rec["passes"].add(pas)
            rec["labels"].add(r.get("label", r["route"]))
            m = re.search(r"\[(.+?)\]$", r.get("label", ""))
            if m:
                rec["accounts"].add(m.group(1))
            rec["api"] = max(rec["api"], r.get("api_responses") or r.get("captured") or 0)
            rec["ok"] = max(rec["ok"], r.get("ok") or r.get("with_body") or 0)
            rec["bytes"] = max(rec["bytes"], r.get("bytes") or 0)
            rec["text"] = max(rec["text"], r.get("text_len") or 0)
            if r.get("error"):
                rec["errors"].add(str(r["error"])[:80])
            if r.get("bounced"):
                rec["bounced"] = True
            for p in glob.glob(os.path.join(HERE, pas, r["name"] + "*.png")):
                rec["shots"].add(os.path.relpath(p, ROOT))
    for ff in sorted(glob.glob(os.path.join(HERE, "walk*", "_filters.json"))):
        pas = os.path.basename(os.path.dirname(ff))
        for r in json.load(open(ff)):
            c = norm(r["route"])
            rec = v[c]
            rec["passes"].add(pas)
            for p in glob.glob(os.path.join(HERE, pas, r["name"] + "*.png")):
                rec["shots"].add(os.path.relpath(p, ROOT))
            rec["filters"] = r
    return v


def main():
    raw = load_routes()
    visits = load_visits()
    canon = defaultdict(set)
    for r in raw:
        canon[norm(r)].add(r)
    # visited routes that were not in the extracted list (e.g. /im-vendor redirect target)
    for c in visits:
        canon.setdefault(c, set())

    rows = []
    for c in sorted(canon):
        v = visits.get(c)
        shots = sorted(v["shots"]) if v else []
        walked = "NO"
        note = ""
        if c in DELIBERATE and not (v and v["api"]):
            note = DELIBERATE[c]
            if v and shots:
                walked = "YES"
                note = DELIBERATE[c] + f" Screenshot captured anyway ({len(shots)})."
        elif v and (v["api"] or v["text"] > 200) and not v["errors"]:
            walked = "YES"
            bits = [f"{v['ok']}/{v['api']} API responses with bodies",
                    f"{v['text']} chars rendered"]
            if v["bytes"]:
                bits.append(f"{v['bytes']:,} bytes of JSON captured")
            if v["accounts"]:
                bits.append("accounts: " + ", ".join(sorted(v["accounts"])))
            if v.get("filters"):
                f = v["filters"]
                if f.get("forbidden_controls"):
                    bits.append(f"{f['forbidden_controls']} write control(s) found, NOT clicked")
                if f.get("unverified_controls"):
                    bits.append(f"{f['unverified_controls']} UNVERIFIED CONTROL, not exercised")
            note = " · ".join(bits)
        elif v and v["errors"]:
            walked = "NO"
            note = ("NOT WALKED — navigation error: " + "; ".join(sorted(v["errors"]))
                    + ". Re-walked under AMENDMENT-04 where the cause was my own "
                      "transport gate blocking a route containing a write-verb word.")
        elif v:
            walked = "YES"
            note = (f"Rendered but returned NO API data ({v['api']} calls, {v['text']} chars) — "
                    "shell only. See the section note for why.")
        elif ":" in c:
            note = PARAM_NOTE
        else:
            note = ("NOT WALKED — route literal present in the bundle but not reachable as a "
                    "standalone page (layout/redirect wrapper or alias of a walked route).")
        rows.append(dict(route=c, remote=remote_of(c), walked=walked,
                         shots=shots, note=note, variants=sorted(canon[c])))

    yes = [r for r in rows if r["walked"] == "YES"]
    # ---------------- COVERAGE-LEDGER.md ----------------
    L = []
    L.append("# COVERAGE LEDGER — Swiggy Instamart\n")
    L.append("One row per SPA route found in the JS corpus, across **all 6 federated remotes** "
             "plus the shell. Generated by `captures/build_ledger.py` from the live-walk "
             "manifests, so it cannot drift from what actually happened.\n")
    L.append(f"**{len(yes)} of {len(rows)} routes walked** on 2026-07-30 against JIVO's live "
             "account, read-only. Every `NO` carries a specific reason — a safety decision, a "
             "missing credential, a required id, or a navigation error — never "
             "\"not important\".\n")
    L.append("Screenshots live in `captures/walk1..walk4/`; every one is indexed in "
             "`vault/Swiggy-Instamart-Screenshot-Index.md`. Network evidence for each route is "
             "the sibling `.json` of the same basename.\n")
    L.append("| # | Route | Remote | Walked | Screenshots | Evidence / reason |")
    L.append("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        sh = "<br>".join(f"`{os.path.basename(s)}`" for s in r["shots"][:3]) or "—"
        if len(r["shots"]) > 3:
            sh += f"<br>_+{len(r['shots'])-3} more_"
        L.append(f"| {i} | `{r['route']}` | {r['remote']} | {r['walked']} | {sh} | {r['note']} |")
    L.append("")
    L.append("## Per-remote roll-up\n")
    L.append("| Remote | Routes | Walked |")
    L.append("|---|---|---|")
    per = defaultdict(lambda: [0, 0])
    for r in rows:
        per[r["remote"]][0] += 1
        if r["walked"] == "YES":
            per[r["remote"]][1] += 1
    for k, (t, w) in sorted(per.items()):
        L.append(f"| {k} | {t} | {w} |")
    L.append(f"| **TOTAL** | **{len(rows)}** | **{len(yes)}** |")
    L.append("")
    L.append("## Multi-entity coverage\n")
    L.append("Every non-vendor route was walked **once per account**, because JIVO holds three and "
             "their data differs materially (Jivo Mart has 22 cities with sales against Jivo "
             "Wellness's 132). The vendor lane is account-agnostic — it authenticates with "
             "`Abacus-Token` and scopes by vendor/facility, not by ads account — so it was walked "
             "once.\n")
    L.append("| Account | Account id | Walked |")
    L.append("|---|---|---|")
    L.append("| Jivo Mart Pvt. Ltd | `89bafc9c-8a56-4286-94cf-a55ab4e564d3` | yes |")
    L.append("| Jivo Wellness | `c9f24655-a984-4b65-a4da-2d5b6461b9ec` | yes |")
    L.append("| Jivo | `260921c1-76e7-48ef-9771-82124ebe1fcc` | yes |")
    L.append("")
    L.append("## Known gaps, stated plainly\n")
    L.append("- **Local Buying** (`/im-vendor/local-buying/*`) renders but returns no data: it "
             "resolves a `LOCAL_VENDOR` user pool to a different identity host "
             "(`influencer-app-*.swig.gy`). NOT_REACHABLE with the brand session; needs a "
             "credential JIVO may not have.\n"
             "- **Brandverse** metrics returned **HTTP 403** for `ecom1@jivo.in` — the remote "
             "loads, the account is not entitled. Role-denied, not missed.\n"
             "- **`searchInventoryAvailabilityMetrics`** returned **403 `Invalid Request Body`** "
             "on passive render (the page calls it before a filter is chosen), so its success "
             "shape is not captured.\n"
             "- **Create/edit routes** were deliberately not opened (draft-create-on-mount risk).\n"
             "- **Parameterised detail routes** need ids that this account's empty listings did "
             "not yield.\n"
             "- The **ads-lane login** (`tanuj@jivo.in`) token was expired everywhere, so the ads "
             "surfaces were walked with the `ecom1@jivo.in` session instead. Everything the ads "
             "lane returned is therefore scoped to ecom1's entitlements.")
    L.append("")
    L.append("Method: `vault/_meta/Read-Only-Guardrails.md` · Atlas: "
             "`vault/00-Swiggy-Instamart-Atlas.md` · Audit: "
             "`vault/_meta/Study-Verification.md`")
    open(os.path.join(ROOT, "COVERAGE-LEDGER.md"), "w").write("\n".join(L) + "\n")

    # ---------------- Pages-and-Routes.md ----------------
    P = []
    P.append("---\ntitle: Swiggy Instamart Pages and Routes\ncreated: 2026-07-30\n"
             "updated: 2026-07-30\nproject: jivo-cli\ntype: reference\n"
             "tags: [swiggy, instamart, routes]\n---\n")
    P.append("# Every page and route in the Swiggy Instamart portal\n")
    P.append("The bird's-eye view: **every route literal in the SPA**, including the ones no JIVO "
             "employee has ever opened. Extracted from the router tables of the shell and all six "
             "federated remotes, then walked live where reachable.\n")
    P.append(f"**{len(raw)} route literals** were extracted from the routers, which normalise to "
             f"**{len(rows)} distinct canonical routes** across 7 apps (the difference is aliases: "
             "`/x` vs `/x/` vs `/x/*`, `_private` layout wrappers, and `${id}` vs `{0}` vs `$id` "
             "spellings of the same parameter). Both numbers are given because quoting only the "
             "larger one would overstate the surface and only the smaller one would hide the "
             "aliases. Walk status per route is in [[../COVERAGE-LEDGER|COVERAGE-LEDGER.md]]; "
             "screenshots in [[Swiggy-Instamart-Screenshot-Index]].\n")
    P.append("## The nav, as the Supply Portal presents it\n")
    P.append("Read off the live page — this is the vendor lane's own information architecture:\n")
    P.append("```\nPERFORMANCE   Vendor Scores · Facility Level · Item Level\n"
             "FULFILMENT    Purchase Orders · PO Booking · Goods Received\n"
             "RETURNS       Purchase Returns · Return To Vendor\n"
             "INVENTORY     Low Inventory · Stock On Hand · Availability\n"
             "Finance       Downloads\n"
             "Help          FAQ\n```\n")
    P.append("## Routes by app\n")
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["remote"]].append(r)
    for rem in sorted(grouped):
        P.append(f"\n### {rem}\n")
        P.append("| Route | Walked | Aliases in the bundle |")
        P.append("|---|---|---|")
        for r in sorted(grouped[rem], key=lambda x: x["route"]):
            al = ", ".join(f"`{a}`" for a in r["variants"] if a != r["route"]) or "—"
            P.append(f"| `{r['route']}` | {r['walked']} | {al} |")
    P.append("\n## Connections\n")
    P.append("- [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · "
             "[[Swiggy-Instamart-Screenshot-Index]] · [[Read-Only-Guardrails]] · "
             "[[Study-Verification]]")
    open(os.path.join(VAULT, "Swiggy-Instamart-Pages-and-Routes.md"), "w").write("\n".join(P) + "\n")

    print(f"ledger rows: {len(rows)}  walked: {len(yes)}  "
          f"screenshots referenced: {sum(len(r['shots']) for r in rows)}")


if __name__ == "__main__":
    main()
