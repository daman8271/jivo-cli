# Bundle-builder API — contract for the frontend

The backend is `distribution/server` (Go, stdlib only, binary `jivodist`). It
serves this API and the static files in `distribution/web/`.

Default bind: **`127.0.0.1:7788`** (`-addr` to change). That is not an auth
layer — it just keeps a service that generates production credentials off the
LAN.

```
cd distribution/server && go build -o jivodist .
cd distribution && ./server/jivodist          # http://127.0.0.1:7788
```

---

## Browser-facing hardening — what the frontend must send

This is **not** an auth layer and adds no operator-facing friction: no login, no
token, no prompt. It exists because a service on loopback is reachable by any
web page the operator happens to have open, and this one builds zips full of
production credentials on request.

The frontend must do exactly two things:

1. **Send `Content-Type: application/json` on every `POST` and every `DELETE`.**
   Without it the request is refused with `415`. This is deliberate: requiring
   a non-simple content type forces the browser to preflight any cross-origin
   attempt, and the preflight fails because the server never emits a single CORS
   header. `fetch()` from our own page passes untouched.
2. **Nothing else.** Same-origin requests from the served page carry
   `Sec-Fetch-Site: same-origin` automatically.

What the server enforces on **every** route, `/api/…` and the static root alike:

| Check | Failure | Why |
|---|---|---|
| `Host` must be the bound address (`127.0.0.1:PORT`, `localhost:PORT`, `[::1]:PORT`, or the exact `host:port` if `-addr` binds elsewhere) | `403` | DNS rebinding hands an attacker's page a live connection to loopback; the `Host` header still says their domain |
| `Sec-Fetch-Site`, when the browser sends it, must be `same-origin` or `none` | `403` | `cross-site`/`same-site` means another page initiated it |
| `POST`/`DELETE` must be `application/json` | `415` | forces preflight, which dies for want of CORS headers |
| No CORS headers are ever emitted | — | one `Access-Control-Allow-Origin` would undo all of the above |

`curl` and the CLI are unaffected: a missing `Sec-Fetch-Site` is treated as a
non-browser client, and they already send the right `Host`.

Responses that carry credential metadata or credentials themselves —
`/api/manifest`, `/api/bundles`, and the zip download — are sent with
`Cache-Control: no-store`.

## The one rule

**The UI renders only from `GET /api/manifest`.** No hardcoded tool list, no
hardcoded names, descriptions, sizes, targets or auth labels anywhere in the
frontend. Adding a CLI to `distribution/manifest.json` must be enough to make it
appear and be selectable. Anything the UI needs that is not in this payload is a
backend bug — ask for the field rather than hardcoding it.

Corollary: `availability` is computed live by `os.Stat` on each binary, not read
from the manifest's `exists` flags. A component can be available on the machine
that wrote the manifest and unavailable on the machine running the server (this
is real: `portals/tankhapay/` exists only on Daman's Mac). Render availability
per target, every time.

---

## `GET /api/manifest`

The manifest's UI-relevant fields, enriched live per target.

```json
{
  "generated_at": "2026-08-10T14:00:00+05:30",
  "targets": ["mac-arm64", "windows"],
  "warnings": [
    "env-vault/all-env.txt was publicly readable on GitHub (verified 2026-08-05) — treat every credential in this bundle as burn-listed until it has been rotated."
  ],
  "components": [
    {
      "id": "hana-sql",
      "ui_name": "HANA SQL (direct SAP database)",
      "ui_description": "…from manifest…",
      "auth_mode": "baked-env",
      "auth_note": "Both connection variants ship: connections/hana.env (direct, office network) and connections/hana-tunnel.env (from home, through the tunnel). …",
      "sensitive": false,
      "availability": {
        "mac-arm64": { "ok": true, "tools_included": 1, "tools_skipped": 0, "warnings": [] },
        "windows":   { "ok": true, "tools_included": 1, "tools_skipped": 0,
                       "warnings": ["hana-sql.exe is STALE: built 2026-07-31, and lacks the hana_turnover / … MCP domain tools …"] }
      },
      "est_size_bytes": { "mac-arm64": 11030843, "windows": 7753625 }
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `generated_at` | RFC 3339, the moment the payload was computed. Not cached — call it again after a rebuild. |
| `targets` | The bundle targets. Currently `mac-arm64` and `windows`; treat it as data, not a constant. |
| `warnings` | Applies to every bundle regardless of selection. Show once, near the build button. |
| `components[].id` | The value to send in `POST /api/bundle`. |
| `components[].auth_mode` | One of the four below, or `unconfigured`. Drives the badge. |
| `components[].auth_note` | The honest one-liner behind the badge. Show it — the mode alone is not enough. |
| `components[].sensitive` | `true` means the bundle carries something like payroll data. Warrants a visible confirmation. |
| `components[].availability[target]` | Per-target. `ok: false` means the component contributes nothing for that target — disable the tick and show the warnings. |
| `components[].est_size_bytes[target]` | Uncompressed estimate, per target. For a running total; the real zip is smaller. |

### `auth_mode` — exactly four values

| Value | Means | The UI should say roughly |
|---|---|---|
| `baked-env` | Credentials are in the zip and the tool reads them itself. | "Ready to use" |
| `auth-login` | Credentials ship for reference, the binary does **not** read them; recipient runs `auth login` once. | "One login needed" |
| `home-config-install` | A file must be copied into the recipient's home directory (postsql → `~/.postsql/`). | "One file to install" |
| `external-token` | No useful long-lived credential can ship (blinkit/zepto/amazon/flipkart/swiggy: tokens are minted on Daman's Mac and expire). | "Limited access" |

Never render `baked-env`-style reassurance for the other three. Telling someone
a credential is set up when their binary never reads it is the exact silent
failure this repo's lessons document.

There is a fifth value the UI must handle but should never celebrate:
**`unconfigured`** — a component exists in `manifest.json` but nobody has
written down what its credentials do. Its `availability[*].ok` is `false` and a
warning says where to add the plan. Show it greyed out with the warning; do not
let it be ticked. It is a gap in the backend, not a kind of kit.

---

## `POST /api/bundle`

Request:

```json
{ "target": "mac-arm64", "components": ["sap-b1", "hana-sql"], "recipient": "karanpreet", "include_docs": true }
```

`Content-Type: application/json` is required (see the hardening section).

Response `200` — JSON first, so warnings are seen **before** the download:

```json
{
  "bundle_id": "20260810-1430-a1b2",
  "filename": "jivo-kit-mac-arm64-20260810-1430-a1b2-karanpreet.zip",
  "zip_path": "/Users/…/jivo-cli/distribution/dist/jivo-kit-mac-arm64-20260810-1430-a1b2-karanpreet.zip",
  "size_bytes": 48211903,
  "sha256": "…",
  "file_count": 214,
  "warnings": ["dsr-cli: DSR_* keys not found in distribution/secrets.local.env — shipped a blank template, dsr will not connect until it is filled in"],
  "skipped": [ { "component": "ecom-cli", "tool": "jivo-ecom-pp-mcp", "reason": "no windows binary prebuilt (ecom-cli/jivo-ecom-pp-mcp.exe has never been built)" } ],
  "download_url": "/api/bundle/20260810-1430-a1b2/download"
}
```

Show `warnings` and `skipped` **before** offering the download link. That is the
point of returning JSON rather than the file.

**Filename format** — `jivo-kit-<target>-<bundle_id>-<recipient>.zip`, where
`bundle_id` is `YYYYMMDD-HHMM-xxxx`. The id is embedded on purpose: two kits
built for the same person on the same day must not collide, and any zip found in
`dist/` can be mapped back to its id with no server-side state. Always use
`filename` and `download_url` as returned; never reconstruct them.

`sha256` is the digest of the file on disk. Note that two builds of the same
selection are **not** byte-identical — the README carries the bundle id and the
build time — so a differing digest across two builds is expected and is not a
tamper signal. Compare a digest only against the same file.

Errors — the body is always `{ "error": "…" }`:

| Status | When |
|---|---|
| `400` | unknown component, empty selection, bad target, malformed JSON, a staged path illegal on NTFS, or **a selection that resolves to nothing for the chosen target** (no component picked has a binary for it — a README-only zip is never returned as a success) |
| `403` | Host or `Sec-Fetch-Site` refused (see hardening) |
| `409` | the gitignore guard failed — the message says exactly which directory to add to `distribution/.gitignore` |
| `415` | `POST`/`DELETE` without `Content-Type: application/json` |
| `500` | anything else, including a component with no credential plan; the message is plain text meant to be shown |

One build runs at a time (server-side mutex). A second `POST` waits.

---

## `GET /api/bundle/{id}/download`

`application/zip`, `Content-Disposition: attachment`, `Cache-Control: no-store`.
`{id}` is the `bundle_id` from the build response, or the filename. Because the
id is embedded in the filename, a bundle stays reachable by its id across a
server restart. Anything else — and any bundle still being written — is `404`.

## `GET /api/bundles`

The finished zips in `distribution/dist/`, newest first:

```json
[ { "id": "20260810-1430-a1b2", "filename": "jivo-kit-…zip", "size_bytes": 48211903,
    "age_seconds": 312, "modified": "2026-08-10T14:30:00+05:30" } ]
```

`id` is read out of the filename, so it is the same whether or not this server
built the file. Bundles still being written (`*.zip.tmp`) are never listed: a
half-written credential zip must not look ready to send.

## `DELETE /api/bundle/{id}`

Removes the zip. `200` with `{ "deleted": "<filename>" }`. Requires
`Content-Type: application/json`. Works by id or by filename; either way the
bundle stops resolving under both. **These zips hold live credentials —
deleting after sending is part of the workflow, so make the delete button easy
to find.**

## `GET /`

Serves `distribution/web/`. If that directory does not exist yet, returns a
plain-text `404` saying so and pointing at `/api/manifest`.

---

## Things the UI must not do

- Do not hardcode component ids, names, targets or auth labels.
- Do not offer a download before the warnings have been rendered.
- Do not display credential **values**. Nothing in this API returns one, and
  nothing in the UI should ever fetch a file out of a bundle to display it.
- Do not build to a path the operator chooses. Output location is the server's
  decision (`distribution/dist/`), because that is the only directory git is
  guaranteed to ignore.
