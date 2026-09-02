# Control Panel `jivo` CLI — New-command build list

**What this is:** a diff of the full documented Control Panel endpoint surface
(`control-panel/recon/ENDPOINTS_RAW.txt` + `control-panel/vault/api/*.md`, ~60 endpoints)
against what the `jivo` CLI already implements (~41 commands across 7 interfaces:
`sales inventory oih accounts targets masterdata users`, plus the top-level `credit`,
`search`, `sync` commands). It lists every documented endpoint that is **not yet a CLI
command** and classifies it READ (buildable now) vs WRITE/ACTION (owner go-ahead required).

- **Coverage today:** 40 of the ~60 documented endpoints are already CLI commands.
- **Missing READs (buildable now):** 7 — see table 1.
- **WRITE/ACTION endpoints (documented, do NOT build without owner sign-off):** 16 — see table 2.
- Live-verified against `http://138.252.101.118:9080` as `preshit` (admin), 2026-08-25.
- Call patterns per `control-panel/vault/architecture.md`: **POST-JSON** / **GET-XHR** / **GET-query**.

---

## Table 1 — READ endpoints to add (prioritized)

| # | Proposed cmd | Endpoint | Call pattern | Params | Value to sales team | Effort | Live check |
|---|---|---|---|---|---|---|---|
| 1 | `inventory production-plan` | `GET /inventory/production/api/plan/` | GET-query | `items` = URL-encoded JSON `[{fg_code,qty},…]`; `warehouses` = `ALL`\|csv | **Highest.** Multi-SKU/basket production feasibility with **shared-component pooling** (`used_in` shows which FGs share an RM/PM, `required` summed across the basket). Answers "can we actually produce this whole order book / month plan?" — the fulfilment view behind OIH. Today only the single-item `inventory production-feasibility` exists; the basket version is missing. | Low–Med | **200**, full `materials[]` with `balance`/`short`/`elsewhere` (probed `FG0000149` qty 1) |
| 2 | `sales cogs` (or top-level `cogs`) | `GET /api/cogs/` | GET-query | `from_date`,`to_date` (`YYYY-MM-DD`); `param_type`; `otp` | Margin lens: total COGS, **COGS ₹/L**, total litres — pairs with the team's realise (₹/L) to give margin. **OTP-gated + needs `can_cogs`.** | Low | **403 `{"error":"Permission denied"}`** — money-gated; **not visible to `preshit` login** (`can_cogs:false`). Build the command, but it will deny for this login until an authorised OTP user runs it. |
| 3 | `accounts export-aging-detail` | `POST /realise/api/export-aging-detail/` | POST-JSON | `as_of` (`YYYY-MM-DD`); `parties` = `[CardCode,…]` | Collections: server-built `.xlsx` of **every open document + its remarks** for the filtered parties, aged to a date. Genuine server-side read → file (does not mutate SAP or the CP store). Route with `--deliver file:<path>`. | Med (binary blob) | `405` on GET (POST-only) — not executed (file gen) |
| 4 | `sales health` (or fold into `doctor`) | `GET /realise/api/health/` | GET-XHR | none | SAP-link liveness (`sap_connected`) + `message` + **whoami** (`username`,`role`) for scripts/monitoring. Partly redundant with `doctor`. | Low | **200** `{"sap_connected":true,"message":"SAP Connected","username":"preshit","role":"admin"}` |
| 5 | `sales export-xlsx` | `POST /realise/api/export-xlsx/` | POST-JSON | `filename`; `sheets:[{name,rows:[[cell…]]}]` | Generic xlsx builder — but the **client** assembles the rows, so from a CLI you'd be feeding it data you already fetched. Low CLI value; include only for parity. Does not mutate data. | Med | not executed (file gen) |
| 6 | `sales export-excel` | `POST /realise/api/export-excel/` | POST-JSON | `layout_rows` (client-built Realise-grid layout) | Same as #5: main Realise grid → xlsx from client-built `layout_rows`. Low CLI value. | Med | not executed (file gen) |
| 7 | `sales calculator-export` | `POST /realise/api/realise-calculator/export/` | POST-JSON | `filename`,`layout`(`separate`\|`single`),`plans[]`,`summary[]` | Renders realise-calculator plans to `.xlsx`. Needs plans the client already built → low CLI value. Does not mutate data. | Med | not executed (file gen) |

**Notes on the exports (#3, #5, #6, #7):** their vault frontmatter says `readonly:false`
because they generate a file, but **none mutate business data** — they serialize
already-authorised reads into `.xlsx`. #3 is the one worth building (server assembles the
workbook from just `{as_of,parties}`); #5–#7 require the caller to pre-build the grid rows,
so they add little over the existing data commands.

**Already covered (do not rebuild):** the required-credit-limit page is served by the
top-level `credit` command (reads the page's embedded JSON), and per-invoice aging
**remarks** already come back inside `accounts aging-oil` / `aging-beverages` payloads —
there is **no** GET read endpoint for remarks (`GET /realise/api/aging-remark/` → `405`).

---

## Table 2 — WRITE / ACTION endpoints (documented — DO NOT build without owner go-ahead)

The Control Panel is a **separate Django app**. RULE 0 authorises writes to **SAP only**;
writing back to the Control Panel (targets, credit locks, rate lists, remarks, users) needs
the owner's explicit sign-off. Listed here so a future AI recognises them and refuses.

| # | Name | Endpoint | Effect |
|---|---|---|---|
| 1 | save-targets | `POST /api/save-targets/` | Overwrites product-level monthly TGT (litres + ₹/L rate) for a month/year. Gated behind `verify-pin` re-auth. |
| 2 | verify-pin | `POST /realise/api/verify-pin/` | Admin **password** re-auth gate (`{pin:<password>}`). Auth-sensitive; unlocks the target editor. Verifies only, no direct mutation. |
| 3 | credit-lock | `POST /realise/api/credit-lock/` | Freezes Total Outstanding + Required Limit on required-credit-limit for `{days}` (1–3650). |
| 4 | credit-unlock | `POST /realise/api/credit-unlock/` | Releases the active credit lock immediately (`{}`). |
| 5 | rate-list-save | `POST /realise/api/rate-list/save/` | Persists a realise-calculator plan/comparison to the saved rate-list (`name,state,scope,payload`). |
| 6 | rate-list-delete | `POST /realise/api/rate-list/delete/` | Deletes one saved rate-list result by `{id}`. Destructive. |
| 7 | calculator-upload | `POST /realise/api/realise-calculator/upload/` | Accepts a `.xlsx` upload; parses rows for the Planning/Compare grids. |
| 8 | calculator-order-upload | `POST /realise/api/realise-calculator/order-upload/` | Order-tab variant of #7; accepts a `.xlsx` upload, fills Old+New order grids. |
| 9 | save-closing-remark | `POST /realise/api/save-closing-remark/` | Persists a period closing remark/sign-off server-side (`{period,remark}`). |
| 10 | aging-remark (save) | `POST /realise/api/aging-remark/` | Save/update one open-invoice remark in the CP overlay (`{code,row_key,remark}`). Overlay only — SAP untouched. |
| 11 | aging-remark-upload-oil | `POST /realise/api/aging-remark-upload-oil/` | Bulk-import Oil remarks/special-prices from a spreadsheet (`multipart: file,as_of`). |
| 12 | aging-remark-upload-beverages | `POST /realise/api/aging-remark-upload-beverages/` | Bulk-import Beverages remarks/special-prices (`multipart: file,as_of`). |
| 13 | aging-remark-clear-oil | `POST /realise/api/aging-remark-clear-oil/` | Erase ALL saved Oil remarks/special-prices, book-wide. **Irreversible.** |
| 14 | aging-remark-clear-beverages | `POST /realise/api/aging-remark-clear-beverages/` | Erase ALL saved Beverages remarks/special-prices, book-wide. **Irreversible.** |
| 15 | users-save | `POST /api/users/save/` | Create/update a Control Panel user — identity, password, active flag, Realise role, permission groups (home-grown RBAC). |
| 16 | users-delete | `POST /api/users/delete/` | Permanently delete a Control Panel user. Destructive. |

---

*Generated 2026-08-25 from a live diff (session as `preshit`, read-only). Reads #1–#4 were
GET-probed live; the exports and every Table-2 endpoint were classified from
`vault/api/*.md` and confirmed POST-only where checked (`405` on GET), never executed.*
