#!/usr/bin/env python3
"""
build_vault.py — generates the section notes, the master endpoint index, the
Atlas, Pages-and-Routes and the Screenshot Index for the Swiggy Instamart study.

Why generated: the Phase-7 audit requires that EVERY distinct path in
captures/endpoints-raw.tsv appears verbatim in the endpoint index, and that every
screenshot on disk is referenced from a vault note. Both are guaranteed here by
construction instead of asserted by hand, so a later walk that adds endpoints or
screenshots cannot silently break the claim — re-running this script fixes it.

Hand-written notes are NOT touched: _meta/*, *-Data-Model, *-Data-Inventory and
the README are authored directly.
"""
import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sections import SECTIONS, CATCHALL, assign          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VAULT = os.path.join(ROOT, "vault")
TODAY = "2026-07-30"

REMOTES = {
    "brand-portal-client": ("shell", "—", "the module-federation host"),
    "instamart": ("imAdsClient", "1.4.128", "/instamart"),
    "im-vendor": ("imVendorClient", "2.2.28", "/im-vendor"),
    "im-discounts": ("imBdpoClient", "1.19.0", "/im-discounts"),
    "brandverse": ("brandverseClient", "0.0.7", "/brandverse"),
    "im-sampling": ("imSamplingClient", "0.1.11", "/im-sampling"),
    "im-catalog": ("imCatalogClient", "0.1.5", "/im-catalog"),
}


def load_endpoints():
    rows = list(csv.DictReader(open(os.path.join(HERE, "endpoints-raw.tsv")), delimiter="\t"))
    for r in rows:
        r["section"] = assign(r["path"])
    return rows


def load_proven():
    """(host, path) -> {statuses, pages, max_body_len} from every live walk."""
    proven = defaultdict(lambda: {"st": set(), "pages": set(), "len": 0})
    for f in glob.glob(os.path.join(HERE, "walk*", "*.json")):
        base = os.path.basename(f)
        if base.startswith("_"):
            continue
        try:
            d = json.load(open(f))
        except Exception:
            continue
        label = d.get("label") or d.get("route") or base
        calls = d.get("calls") or d.get("captured") or []
        for c in calls:
            if c.get("phase") == "req":
                continue
            u = (c.get("url") or "").split("?")[0]
            if not u.startswith("http"):
                continue
            parts = u.split("/")
            if len(parts) < 4:
                continue
            host, path = parts[2], "/" + "/".join(parts[3:])
            k = (host, path)
            if c.get("status") is not None:
                proven[k]["st"].add(c["status"])
            proven[k]["pages"].add(label)
            proven[k]["len"] = max(proven[k]["len"], len(c.get("body") or ""))
    return proven


def shots_for(section_name, routes_by_section):
    """Screenshots belonging to a section, by matching route slugs in filenames."""
    out = []
    slugs = {re.sub(r"[^a-z0-9]+", "-", r.strip("/").lower()) for r in routes_by_section.get(section_name, [])}
    for p in sorted(glob.glob(os.path.join(HERE, "walk*", "*.png"))):
        rel = os.path.relpath(p, ROOT)
        base = os.path.basename(p).lower()
        for s in slugs:
            if s and s in base:
                out.append(rel)
                break
    return out


# routes that belong to each section, so screenshots can be attributed
SECTION_ROUTES = {
    "Purchase-Orders": ["/im-vendor/po-dashboard", "/im-vendor"],
    "PO-Booking-Appointments": ["/im-vendor/po-booking"],
    "Goods-Received-GRN": ["/im-vendor/grn"],
    "Returns-RTV-and-Purchase-Returns": ["/im-vendor/rtv", "/im-vendor/purchase-returns"],
    "Stock-On-Hand-and-Low-Stock": ["/im-vendor/stock-on-hand", "/im-vendor/low-stock"],
    "Availability-and-Fill-Rate": ["/im-vendor/availability"],
    "Vendor-Performance-Scores": ["/im-vendor/performance-vendor-scores",
                                  "/im-vendor/performance-item-list-view",
                                  "/im-vendor/performance-facility-view"],
    "Vendor-Downloads": ["/im-vendor/downloads"],
    "Local-Buying": ["/im-vendor/local-buying"],
    "Vendor-FAQ-Help": ["/im-vendor/faq"],
    "Sales-Reports": ["/instamart/sales", "/instamart/reports"],
    "Sales-Insights": ["/instamart/sales-insights", "/instamart"],
    "Ad-Campaigns": ["/instamart/campaign", "/instamart/ads", "/instamart/advertisement"],
    "Brand-Insights-Metrics": ["/instamart/bdpo"],
    "Keyword-And-Bid-Suggestions": [],
    "Creatives": [],
    "Requisition-Orders": ["/instamart/requisition-orders"],
    "Products-And-SPINs": [],
    "Ads-AI-Chat": [],
    "NPI-New-Product-Introduction": ["/instamart/npi"],
    "Discounts-BDPO": ["/im-discounts"],
    "Sampling-Campaigns": ["/im-sampling"],
    "Brandverse": ["/brandverse"],
    "Catalog-SPIN-Management": ["/im-catalog"],
    "Accounts-And-Entities": ["/account-select"],
    "Config-And-Feature-Flags": [],
    "Auth-Sessions-And-Login": ["/login", "/employee-login", "/migration-bridge"],
    "Telemetry-And-Third-Party": [],
    "Unclassified-Endpoints": [],
}


def fm(title, folder, tags, status="studied"):
    return (f"---\ntitle: {title}\ncreated: {TODAY}\nupdated: {TODAY}\n"
            f"project: jivo-cli\ntype: reference\n"
            f"tags: [swiggy, instamart, {folder}, {tags}]\nstatus: {status}\n---\n\n")


def ep_table(rows, proven):
    """Read-allowlist table + out-of-scope table for one section."""
    reads = [r for r in rows if r["class"] in ("READ", "READ_FILE")]
    outs = [r for r in rows if r["class"] in ("WRITE", "EXPORT")]
    unk = [r for r in rows if r["class"] == "UNKNOWN"]
    t = []
    t.append("### Read surface\n")
    if reads:
        t.append("| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |")
        t.append("|---|---|---|---|---|---|")
        for r in sorted(reads, key=lambda x: x["path"]):
            pv = proven.get((r["host"], r["path"]))
            # only claim PROVEN when a real HTTP status was captured. A capture that
            # recorded the page but no status is NOT proof, and an earlier version
            # rendered those as a bare "PROVEN " with no code.
            codes = sorted(c for c in (pv["st"] if pv else set()) if isinstance(c, int))
            if codes:
                note = ""
                if codes and all(c in (400, 401, 403) for c in codes):
                    note = " — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured"
                st = "**PROVEN LIVE " + ",".join(str(c) for c in codes) + "**" + note
            else:
                st = "documented (not observed live)"
            t.append(f"| {r['class']} | {r['method']} | `{r['host']}{r['path']}` | "
                     f"`{r['const'] or '—'}` | {st} | {r['evidence']} |")
    else:
        t.append("_No read endpoint is assigned to this section — it is a route/UI surface "
                 "that renders from endpoints documented in sibling notes._")
    t.append("")
    t.append("### Out of scope (writes / exports) — never exposed in a read-only CLI\n")
    if outs:
        t.append("| METHOD | Host · Path | Const | Why excluded |")
        t.append("|---|---|---|---|")
        for r in sorted(outs, key=lambda x: x["path"]):
            t.append(f"| {r['method']} | `{r['host']}{r['path']}` | `{r['const'] or '—'}` | "
                     f"{r['class']} — {r['evidence']} |")
    else:
        t.append("_None in this section._")
    t.append("")
    t.append("### UNKNOWN — documented but DENIED (G1: unknown means denied)\n")
    if unk:
        t.append("| METHOD | Host · Path | Const | Why it stays denied |")
        t.append("|---|---|---|---|")
        for r in sorted(unk, key=lambda x: x["path"]):
            t.append(f"| {r['method']} | `{r['host']}{r['path']}` | `{r['const'] or '—'}` | "
                     f"{r['evidence']} |")
    else:
        t.append("_None in this section._")
    return "\n".join(t)


def main():
    rows = load_endpoints()
    proven = load_proven()
    by_sec = defaultdict(list)
    for r in rows:
        by_sec[r["section"]["name"]].append(r)

    all_secs = SECTIONS + ([CATCHALL] if by_sec.get(CATCHALL["name"]) else [])
    names = [s["name"] for s in all_secs]
    used_shots = set()

    # ---------------- section notes ----------------
    for s in all_secs:
        srows = by_sec.get(s["name"], [])
        shots = shots_for(s["name"], SECTION_ROUTES)
        used_shots.update(shots)
        sibs = [n for n in names if n != s["name"]][:6]
        body = [fm(s["name"].replace("-", " "), s["folder"], s["folder"])]
        body.append(f"# {s['name'].replace('-', ' ')}\n")
        body.append(f"> {s['short']}\n")
        body.append(s["long"] + "\n")
        body.append(f"**Endpoints in this section:** {len(srows)} "
                    f"({len([r for r in srows if r['class'] in ('READ','READ_FILE')])} read, "
                    f"{len([r for r in srows if r['class'] in ('WRITE','EXPORT')])} write/export, "
                    f"{len([r for r in srows if r['class']=='UNKNOWN'])} unknown/denied).\n")
        body.append("## API endpoints\n")
        body.append(ep_table(srows, proven) + "\n")
        body.append("## Gotchas\n")
        body.append(s["gotchas"] + "\n")
        body.append("## Screenshots (live read-only walk, 2026-07-30)\n")
        if shots:
            for sh in shots:
                body.append(f"- `{os.path.basename(sh)}`\n\n  ![screenshot]({os.path.relpath(os.path.join(ROOT, sh), VAULT)})")
        else:
            body.append("_No screenshot is attributed to this section; its endpoints are "
                        "exercised from pages captured under sibling notes. See "
                        "[[Swiggy-Instamart-Screenshot-Index]] for the full set._")
        body.append("")
        body.append("## Connections\n")
        body.append("- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · "
                    "[[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]")
        body.append("- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]")
        body.append("- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]")
        body.append("- Siblings: " + " · ".join(f"[[{n}]]" for n in sibs))
        d = os.path.join(VAULT, s["folder"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, s["name"] + ".md"), "w").write("\n".join(body) + "\n")

    # ---------------- master endpoint index ----------------
    out = [fm("Swiggy Instamart Endpoints (read-only master index)", "endpoints",
              "master-index")]
    out.append("# Swiggy Instamart — Read-Only Master Endpoint Inventory\n")
    out.append(f"Consolidated inventory of **all {len(rows)} distinct endpoint contracts** "
               "extracted from the harvested SPA corpus (the `brand-portal-client` shell + its "
               "6 module-federation remotes), grouped by section. This is the source of truth "
               "the read-only CLI is generated from.\n")
    out.append("`READ` / `READ_FILE` rows are safe to expose. `WRITE` / `EXPORT` rows mutate or "
               "side-effect and are **never** exposed. `UNKNOWN` rows have a binding but the "
               "method/posture was not proven from the minified source — per **G1 they are "
               "denied by default** and listed in full so nothing is hidden.\n")
    out.append("Atlas: [[00-Swiggy-Instamart-Atlas]] · Data model: [[Swiggy-Instamart-Data-Model]] "
               "· Inventory: [[Swiggy-Instamart-Data-Inventory]] · Auth: [[Auth-and-Access]] "
               "· Guardrails: [[Read-Only-Guardrails]] · Routes: "
               "[[Swiggy-Instamart-Pages-and-Routes]]\n")
    hc = Counter(r["host"] for r in rows)
    out.append("## Hosts (production)\n")
    out.append("| Host | Role | Endpoints |")
    out.append("|---|---|---|")
    roles = {
        "brand-portal-service-http.swiggy.com": "brand-portal data API (`brandPortalServiceBasePath`) — ads, sales, catalog, brandverse",
        "picker.swiggy.com": "**SCM / movement-planning gateway** (`scmAPIGatewayBasePath`) — the whole vendor/supply lane. Never touched by JIVO's existing automation.",
        "partner-api.swiggy.com": "partner service (`partnerServiceBasePath`) — accounts, configs, campaign, reports v2, server clock",
        "ozone-idp-brands-im-kba.swiggy.com": "ozone IdP, BRAND user pool — login/OTP/refresh/signout (all WRITE)",
    }
    for h, n in hc.most_common():
        out.append(f"| `{h}` | {roles.get(h, 'see section notes')} | {n} |")
    cc = Counter(r["class"] for r in rows)
    out.append("\n## Classification roll-up\n")
    out.append("| Class | Count | Exposed in the CLI? |")
    out.append("|---|---|---|")
    for k, lbl in (("READ", "yes"), ("READ_FILE", "yes"), ("WRITE", "**no**"),
                   ("EXPORT", "**no** (creates a queue row — G2)"),
                   ("UNKNOWN", "**no** (G1 denies unproven)")):
        out.append(f"| {k} | {cc.get(k, 0)} | {lbl} |")
    out.append(f"| **TOTAL** | **{len(rows)}** | |")
    out.append("")
    for s in all_secs:
        srows = by_sec.get(s["name"], [])
        out.append(f"\n---\n\n## [[{s['name']}]]\n")
        out.append(f"{s['short']} — {len(srows)} endpoint(s). "
                   f"Folder `vault/{s['folder']}/`.\n")
        if not srows:
            out.append("_Route/UI surface with no endpoint of its own._")
            continue
        out.append("| METHOD | Class | Host · Path | Const |")
        out.append("|---|---|---|---|")
        for r in sorted(srows, key=lambda x: (x["host"], x["path"])):
            out.append(f"| {r['method']} | {r['class']} | `{r['host']}{r['path']}` | "
                       f"`{r['const'] or '—'}` |")
    out.append("\n---\n\n## Connections\n")
    out.append("- " + " · ".join(f"[[{n}]]" for n in names))
    open(os.path.join(VAULT, "Swiggy-Instamart-Endpoints.md"), "w").write("\n".join(out) + "\n")

    # ---------------- screenshot index (guarantees zero orphans) -------------
    allshots = sorted(glob.glob(os.path.join(HERE, "walk*", "*.png")))
    si = [fm("Swiggy Instamart Screenshot Index", "captures", "screenshots")]
    si.append("# Screenshot Index — every capture from the live read-only walk\n")
    si.append(f"**{len(allshots)} screenshots** taken on {TODAY} by navigating JIVO's live "
              "Swiggy Instamart portal read-only (AMENDMENT-02 walk). Every file on disk is "
              "listed here, so the capture tree and the vault can never drift apart.\n")
    si.append("Passes: `walk1` = first route sweep · `walk2` = per-account sweep across all 6 "
              "remotes · `walk3` = filter/control inventory (`-a-default` before, `-b-widened` "
              "after) · `walk4` = full-response-body pass with tab clicks.\n")
    si.append("| # | Screenshot | Pass | Route / view | Open |")
    si.append("|---|---|---|---|---|")
    for i, p in enumerate(allshots, 1):
        rel = os.path.relpath(p, ROOT)
        pas = rel.split(os.sep)[1] if os.sep in rel else "?"
        base = os.path.basename(p)
        view = re.sub(r"^(sec|flt|d)-\d+-", "", base[:-4]).replace("-", " ")
        link = os.path.relpath(p, VAULT)
        si.append(f"| {i} | `{base}` | {pas} | {view} | [open]({link}) |")
    si.append("\n## Connections\n- [[00-Swiggy-Instamart-Atlas]] · "
              "[[Swiggy-Instamart-Pages-and-Routes]] · [[Study-Verification]]")
    open(os.path.join(VAULT, "Swiggy-Instamart-Screenshot-Index.md"), "w").write("\n".join(si) + "\n")

    print(f"sections written : {len(all_secs)}")
    print(f"endpoints indexed: {len(rows)}")
    print(f"screenshots      : {len(allshots)}")
    return rows, proven


if __name__ == "__main__":
    main()
