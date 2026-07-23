#!/usr/bin/env python3
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_DATE = "2026-07-19"
spec = json.load(open(f"{ROOT}/endpoints.json"))
pages = json.load(open(f"{ROOT}/pages.json"))
eps = spec["endpoints"]
os.makedirs(f"{ROOT}/endpoints", exist_ok=True)
os.makedirs(f"{ROOT}/pages", exist_ok=True)

ep_by_slug = {e["slug"]: e for e in eps}
ep_by_path = {(e["method"], e["path"]): e for e in eps}
# map canonical GET path -> endpoint file slug (for page links); filled after file_slug assigned
getpath_slug = {}
pageTitle = {p["slug"]: p["title"] for p in pages}


def params_cell(e):
    q = ", ".join(f"`{p}`" for p in e.get("query_params", []))
    return q or "—"


def pathparams_cell(e):
    q = ", ".join(f"`{p}`" for p in e.get("path_params", []))
    return q or "—"


# unique filename per (method,path): non-GET reads keep clean slug; collisions get method prefix
_seen = {}
for e in eps:
    fn = e["slug"]
    if fn in _seen or (
        e["method"] != "GET"
        and any(o["slug"] == e["slug"] and o["method"] == "GET" for o in eps)
    ):
        fn = f"{e['method'].lower()}_{e['slug']}"
    _seen[fn] = e["slug"]
    e["file_slug"] = fn
for e in eps:
    if e["method"] == "GET":
        getpath_slug.setdefault(e["path"], e["file_slug"])

# ---------- ENDPOINT DOCS ----------
for e in eps:
    slug = e["file_slug"]
    kind = e["kind"]
    title = f"EXIM endpoint — {e['method']} {e['path']}"
    sample = e.get("response_sample")
    sample_txt = json.dumps(sample, indent=2) if sample is not None else None
    used = [
        f"- [[pages/{pg}|{pageTitle.get(pg, pg)}]]" for pg in e.get("used_by_pages", [])
    ] or ["- _(not directly bound to a listed page)_"]
    related = [
        f"- [[endpoints/{x['file_slug']}|`{x['method']} {x['path']}`]]"
        for x in eps
        if x["category"] == e["category"] and x["file_slug"] != slug
    ][:8] or ["- _(none)_"]
    fm = [
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"created: {DOC_DATE}",
        f"updated: {DOC_DATE}",
        "project: jivogpt",
        "type: endpoint",
        "tags: [jivogpt, exim, api, endpoint]",
        f"method: {e['method']}",
        f"path: {e['path']}",
        f"category: {e['category']}",
        f"kind: {kind}",
        f"resource: {e.get('resource', '')}",
        "auth: bearer",
    ]
    body = [
        "---",
        "\n".join(fm),
        "---",
        "",
        f"# `{e['method']} {e['path']}`",
        "",
        f"> {e.get('desc', '')}",
        "",
        "## Request",
        "",
        "| | |",
        "|---|---|",
        f"| Method | `{e['method']}` |",
        f"| URL | `https://eximbe.jivo.in{e['path']}` |",
        "| Auth | `Authorization: Bearer <access_token>` |",
        f"| Query params | {params_cell(e)} |",
        f"| Path params | {pathparams_cell(e)} |",
    ]
    if e.get("request_body"):
        body.append(f"| Request body | `{e['request_body']}` |")
    body.append("")
    if kind in ("read", "detail"):
        body += [
            "## Response — real sample (trimmed)",
            "",
            "```json",
            sample_txt or "// (empty / needs params)",
            "```",
            "",
        ]
        body += [
            "## Field reference",
            "",
            "<!-- ENRICH:fields -->",
            "_Field-by-field meaning to be filled from the sample above._",
            "",
        ]
    else:
        tag = "SYNC TRIGGER" if kind == "sync" else "WRITE"
        body += [
            f"## ⚠️ {tag} — not wired into the CLI (v1 is read-only)",
            "",
            "This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.",
            "",
        ]
    body += ["## Used by pages", ""] + used + [""]
    body += ["## Related endpoints", ""] + related + [""]
    body += [
        "## Notes",
        "",
        f"- Kind: **{kind}**. Resource permission group: `{e.get('resource', '') or 'n/a'}`.",
        "- Read-only GET; safe to call repeatedly."
        if kind in ("read", "detail")
        else "- Mutating; requires explicit confirmation before use.",
        "",
        "Linked: [[API-INVENTORY]] · [[INDEX]]",
        "",
    ]
    open(f"{ROOT}/endpoints/{slug}.md", "w").write("\n".join(body))

# ---------- PAGE DOCS ----------
sec_pages = {}
for p in pages:
    sec_pages.setdefault(p["section"], []).append(p)
for p in pages:
    slug = p["slug"]
    ep_links = []
    for path in p["endpoints"]:
        es = getpath_slug.get(path) or getpath_slug.get(path.rstrip("/"))
        if es and es in ep_by_slug:
            ep_links.append(
                f"- [[endpoints/{es}|`GET {path}`]] — {ep_by_slug[es].get('desc', '')}"
            )
        else:
            ep_links.append(f"- `GET {path}`")
    ep_links = ep_links or [
        "- _(no backend calls captured — likely static/derived view)_"
    ]
    seed_paths = ", ".join(p["endpoints"][:4])
    related = [
        f"- [[pages/{q['slug']}|{q['title']}]]"
        for q in sec_pages.get(p["section"], [])
        if q["slug"] != slug
    ][:8] or ["- _(none)_"]
    fm = [
        f"title: {json.dumps(p['title'], ensure_ascii=False)}",
        f"created: {DOC_DATE}",
        f"updated: {DOC_DATE}",
        "project: jivogpt",
        "type: page",
        "tags: [jivogpt, exim, page]",
        f"route: {p['route']}",
        f"section: {p['section']}",
    ]
    body = (
        [
            "---",
            "\n".join(fm),
            "---",
            "",
            f"# {p['title']}",
            "",
            f"[[INDEX|JIVO EXIM]] › **{p['section']}** › {p['title']}",
            "",
            f"**Route:** `{p['route']}`  ·  **Web:** `https://exim.jivo.in{p['route']}`",
            "",
            "## What this page does",
            "",
            "<!-- ENRICH:what -->",
            f"_Overview to be enriched. Draws on: {seed_paths or 'n/a'}._",
            "",
            "## How it helps",
            "",
            "<!-- ENRICH:help -->",
            "_Business value to be enriched._",
            "",
            "## Backend endpoints",
            "",
        ]
        + ep_links
        + [
            "",
            "## Key data & interactions",
            "",
            "<!-- ENRICH:ui -->",
            "_Filters, toggles, exports, columns to be enriched._",
            "",
            "## Related pages (same section)",
            "",
        ]
        + related
        + ["", "Linked: [[INDEX]] · [[API-INVENTORY]]", ""]
    )
    open(f"{ROOT}/pages/{slug}.md", "w").write("\n".join(body))

print(f"generated {len(eps)} endpoint docs + {len(pages)} page docs")
