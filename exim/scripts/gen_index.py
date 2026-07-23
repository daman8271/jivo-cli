import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_DATE = "2026-07-19"
spec = json.load(open(f"{ROOT}/endpoints.json"))
eps = spec["endpoints"]
pages = json.load(open(f"{ROOT}/pages.json"))
tok = json.load(open(f"{ROOT}/.secrets/token.json"))
# recompute file_slug same way as gen_docs
_seen = {}
for e in eps:
    fn = e["slug"]
    if fn in _seen or (
        e["method"] != "GET"
        and any(o["slug"] == e["slug"] and o["method"] == "GET" for o in eps)
    ):
        fn = f"{e['method'].lower()}_{e['slug']}"
    _seen[fn] = 1
    e["file_slug"] = fn
SEC_ORDER = [
    "Reports",
    "Stock",
    "Domestic Contracts",
    "Accounts",
    "Commodity Price",
    "Exchange Rates",
    "License",
    "Administration",
]
sec_pages = {}
for p in pages:
    sec_pages.setdefault(p["section"], []).append(p)


def frontmatter(title, note_type, tags):
    return [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"created: {DOC_DATE}",
        f"updated: {DOC_DATE}",
        "project: jivogpt",
        f"type: {note_type}",
        f"tags: [{', '.join(tags)}]",
        "---",
        "",
    ]


# INDEX.md
L = frontmatter(
    "JIVO EXIM — Knowledge Base (Map of Content)",
    "map",
    ["jivogpt", "exim", "map-of-content"],
) + [
    "# JIVO EXIM — Knowledge Base (Map of Content)",
    "",
    "> Reverse-engineered documentation of the JIVO EXIM platform (`https://exim.jivo.in`, API `https://eximbe.jivo.in`).",
    "> Every **page** and every **API endpoint** is documented as an identical-format note. Links are Obsidian wikilinks.",
    "",
    "## Start here",
    "",
    "- [[README]] — what this vault is & how to use the `exim` CLI",
    "- [[ARCHITECTURE]] — how the app is built (SPA + REST + SAP sync)",
    "- [[AUTH]] — login / JWT / refresh flow",
    "- [[DOMAIN-MODEL]] — entities & permission resources",
    "- [[API-INVENTORY]] — table of all endpoints",
    "",
    f"**Scale:** {len(pages)} pages · {len([e for e in eps if e['kind'] in ('read', 'detail')])} read endpoints · {len([e for e in eps if e['kind'] in ('write', 'sync')])} write/sync endpoints.",
    "",
    "## Pages by section",
    "",
]
for s in SEC_ORDER:
    if s not in sec_pages:
        continue
    L.append(f"### {s}")
    for p in sorted(sec_pages[s], key=lambda x: x["title"]):
        L.append(f"- [[pages/{p['slug']}|{p['title']}]] — `{p['route']}`")
    L.append("")
L.append(
    "Linked: [[README]] · [[API-INVENTORY]] · [[ARCHITECTURE]] · [[AUTH]] · [[DOMAIN-MODEL]]"
)
open(f"{ROOT}/INDEX.md", "w").write("\n".join(L))

# API-INVENTORY.md
L = frontmatter("API Inventory", "reference", ["jivogpt", "exim", "api"]) + [
    "# API Inventory",
    "",
    f"Base URL: `{spec['api_base']}` · Auth: `{spec['auth']['header']}`",
    "",
    "## Read endpoints (safe GET — used by the CLI)",
    "",
    "| Method | Path | Params | Category | Used by | Doc |",
    "|---|---|---|---|---|---|",
]
for e in sorted(
    [x for x in eps if x["kind"] in ("read", "detail")],
    key=lambda x: (x["category"], x["path"]),
):
    prm = (
        ", ".join(
            e.get("query_params", [])
            + ["{" + p + "}" for p in e.get("path_params", [])]
        )
        or "—"
    )
    used = ", ".join(e.get("used_by_pages", [])[:3]) or "—"
    L.append(
        f"| `{e['method']}` | `{e['path']}` | {prm} | {e['category']} | {used} | [[endpoints/{e['file_slug']}\\|doc]] |"
    )
L += [
    "",
    "## Write / sync endpoints (documented, NOT wired into CLI v1)",
    "",
    "| Method | Path | Purpose | Doc |",
    "|---|---|---|---|",
]
for e in sorted(
    [x for x in eps if x["kind"] in ("write", "sync")], key=lambda x: x["path"]
):
    L.append(
        f"| `{e['method']}` | `{e['path']}` | {e.get('desc', '')} | [[endpoints/{e['file_slug']}\\|doc]] |"
    )
L.extend(["", "Linked: [[INDEX]] · [[ARCHITECTURE]] · [[AUTH]] · [[DOMAIN-MODEL]]"])
open(f"{ROOT}/API-INVENTORY.md", "w").write("\n".join(L))

# DOMAIN-MODEL.md
perms = tok.get("permissions", {})
L = frontmatter(
    "Domain Model & Permissions", "reference", ["jivogpt", "exim", "domain-model"]
) + [
    "# Domain Model & Permissions",
    "",
    "> Resources and allowed operations, taken from the live login permission map (user id "
    + str(tok.get("id"))
    + ").",
    "",
    "## Entities (high level)",
    "",
    "- **Stock Status** — imported raw-material stock lots moving through statuses (IN_CONTRACT → ON_THE_SEA → MUNDRA_PORT → ON_THE_WAY → AT_REFINERY → UNDER_LOADING → COMPLETED). See [[pages/stock-status|Stock Status]].",
    "- **Tanks** — physical storage tanks + tank items (oils), fill levels, logs. See [[pages/tank-monitoring|Tank Monitoring]].",
    "- **Domestic Contracts (DC)** — POs / delivery challans by financial year. See [[pages/domestic-contracts|Domestic Contracts]].",
    "- **Licenses** — Advance Authorisation & DFIA import/export licenses. See [[pages/advance-license|Advance License]].",
    "- **Items / Parties** — SAP-synced RM/FG item masters & business partners.",
    "- **Rates / Prices** — daily commodity prices, JIVO rates, market rates, exchange rates.",
    "- **Accounts** — SAP-synced open AR/AP/PO/GRPO, balance sheets, aging.",
    "",
    "## Permission resources (from token)",
    "",
    "| Resource | Ops |",
    "|---|---|",
]
for k in sorted(perms):
    L.append(f"| `{k}` | {', '.join(perms[k])} |")
L.extend(["", "Linked: [[INDEX]] · [[API-INVENTORY]] · [[ARCHITECTURE]]"])
open(f"{ROOT}/DOMAIN-MODEL.md", "w").write("\n".join(L))

# AUTH.md
a = spec["auth"]
open(f"{ROOT}/AUTH.md", "w").write(
    "\n".join(
        frontmatter("Authentication", "reference", ["jivogpt", "exim", "auth"])
        + [
            "# Authentication",
            "",
            "JWT (access + refresh) stored in the SPA's `localStorage`.",
            "",
            "## Login",
            "```http",
            "POST https://eximbe.jivo.in/account/login/",
            "Content-Type: application/json",
            "",
            '{"email":"...","password":"..."}',
            "```",
            "Returns: `{ access, refresh, name, email, id, permissions }`.",
            "",
            "## Authenticated requests",
            "```",
            "Authorization: Bearer <access_token>",
            "```",
            "",
            "## Refresh (on 401)",
            "```http",
            "POST https://eximbe.jivo.in/account/login/refresh/",
            "",
            '{"refresh":"<refresh_token>"}',
            "```",
            "Returns `{ access }`.",
            "",
            "## Logout",
            "`POST /account/logout/` with `{refresh_token}` — invalidates the refresh token. **Do not call from tooling** (kills the session).",
            "",
            "## Notes",
            "- Local helper: `scripts/eximapi.py` (`login()`, `get(path, params)` with auto-refresh).",
            "- Credentials (`EXIM_*`) live in the jivogpt root `.env` (gitignored).",
            "",
            "Linked: [[INDEX]] · [[API-INVENTORY]] · [[HARD-RULE]]",
        ]
    )
)
print("wrote INDEX.md, API-INVENTORY.md, DOMAIN-MODEL.md, AUTH.md")
