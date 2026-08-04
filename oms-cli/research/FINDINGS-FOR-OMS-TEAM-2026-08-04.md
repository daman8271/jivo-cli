# OMS API — findings for the OMS team, 2026-08-04

Found while re-scraping `oms.jivo.in` to regenerate the read-only `oms-cli`.
Everything here was measured against production. Each item has a reproduction
you can paste.

Ordered by severity. **The first three are live security exposures and need a
decision today.** The rest are functional defects.

---

# 1. 🔴 CRITICAL — 29 API endpoints serve production data with NO authentication

`GET` these with **no `Authorization` header at all**, from any machine on the
internet, and they return HTTP 200 with real data.

Reproduce (nothing but curl, no credentials, no cookie, no VPN):

```bash
curl -s "https://oms.jivo.in/api/auth/users/list/" | head -c 400
```

Verified 2026-08-04 from two independent networks (an office Mac and a
Hostinger VPS with no JIVO credentials of any kind). Not a caching artefact —
the anonymous response contained two accounts created *after* the authenticated
call that preceded it.

### What is exposed

| endpoint | rows to an anonymous caller | what it is |
|---|---|---|
| `/api/auth/users/list/` | **54 users** | **every staff account: full `pbkdf2_sha256` password hash, email, phone, role, `is_superuser`** |
| `/api/sap/addresses/` | **35,722** | customer addresses incl. **GST numbers** (`gst_number`), full address, city, PIN |
| `/api/sap/parties/` | 3,358 | the customer/vendor master |
| `/api/sap/products/` | 2,637 | the product master |
| `/api/orders/stock-check/` | 1,900 | live stock positions |
| `/api/invoice/credit-limit/cards/` | 1,172 | **per-customer `balance`, `debtLine`, `creditLine`** |
| `/api/invoice/logs/all/` | 23 | invoice review queue: party name, total amount, SAP doc numbers |
| `/api/orders/schemes/`, `/schemes/manage/` | 72 | discount/scheme configuration |
| `/api/sap/logs/`, `/sap/branches/`, `/sap/product-varieties/` | — | sync logs, branch and variety master |
| `/api/auth/{categories,companies,mainGroup,roles,states}/` | — | reference master data |
| `/api/orders/{branch,dispatches,status,quotation-status,parties,products,staff-products}/` | — | order reference data |
| `/api/legal/*`, `/api/sku/all/` | — | compliance + SKU master |

Also unauthenticated: `GET /api/auth/users/{id}/parties/`, which discloses
which customers each named salesperson owns.

The full measured list is in `research/evidence/anon-open-endpoints.json`.

### Why the password hashes are the urgent part

`password` is being returned by the user serializer. The values are complete
Django PBKDF2-SHA256 hashes (1,000,000 iterations). The iteration count is
strong, so these are not trivially reversible — but they are **offline-crackable
at the attacker's leisure**, and any account whose password is weak, reused, or
dictionary-derived is compromised. One of the 54 accounts has
`is_superuser: true`.

The same `password` field is also returned by `GET /api/auth/profile/` (that one
does at least require a token) and by `POST /api/auth/login/` in the login
response. A client never needs it in any of the three.

### Suggested fix, in order

1. **Remove `password` from the user serializer entirely.** It is the single
   highest-impact change and touches one file. Do this first — it helps even
   before the authentication is fixed.
2. Put `IsAuthenticated` (plus the appropriate role check) on
   `/api/auth/users/list/`, `/api/auth/users/{id}/parties/`, and every endpoint
   in the table above. The likely cause is a missing
   `DEFAULT_PERMISSION_CLASSES` in `REST_FRAMEWORK` settings, which makes DRF
   default to `AllowAny` — that would explain why the affected set spans several
   unrelated apps.
3. **Force a password reset on all 54 accounts.** Assume the hashes are gone.
4. Check access logs for who has been calling these. We do not know how long
   this has been open; we can only say it is open now.

---

# 2. 🔴 CRITICAL — `DEBUG = True` in production, leaking infrastructure

Any error returns Django's full debug page — ~97 KB of HTML — to the caller.

Reproduce:

```bash
curl -s "https://oms.jivo.in/api/sku/pending/" -H "Authorization: Bearer <token>" | head -c 600
```

Django's own masking hides `SECRET_KEY`, passwords and JWT config. It does
**not** hide the rest, and the rest is the map of the estate:

- application source paths — `C:\LiveProjects\OMS\Backend\`
- the internal origin `http://127.0.0.1:8001`
- **PostgreSQL host `20.20.45.75/postgres`**
- **SAP HANA host `20.20.45.192/DSR`, and all four company schemas**
- **seven GST e-invoicing usernames** (`API_Jivo_HP`, `API_Jivo_PB`,
  `API_Jivo_DL`, `API_Jivo_RJ_01`, `API_Jivo_UP`, `API_Jivo_MH`, …)
- SMB attachment share paths
- exact versions: Django 5.2.10, Python 3.14.3
- **`ALLOWED_HOSTS` contains `'*'` and `CORS_ALLOW_ALL_ORIGINS: True`**

`CORS_ALLOW_ALL_ORIGINS: True` combined with finding #1 means any website a
JIVO employee visits can read these endpoints from their browser.

**Fix:** `DEBUG = False` in the production settings, and set a real
`ALLOWED_HOSTS`. Rotate the GST e-invoicing credentials — the usernames are out.

---

# 3. 🟠 The whole tracker UI is broken for every OMS admin

The SPA grants any user with `role === 'admin'` the tracker menu
(`Dn(s, role==='admin')`, bundle offset 233754). The server then refuses every
call those pages make, because tracker access is a **separate** grant.

Reproduce with a global-admin token:

```bash
curl -s "https://oms.jivo.in/api/tracker/my-queue/"     -H "Authorization: Bearer <admin token>"
# {"detail":"You do not have access to this tracker page."}
curl -s "https://oms.jivo.in/api/tracker/all-invoices/" -H "Authorization: Bearer <admin token>"
# {"detail":"Tracker administration is restricted to tracker admins."}
```

All 12 probed tracker endpoints 403 for a global admin, in two flavours. Either
the front-end gate should match the server's (`tracker_admin` / `tracker_entry`
/ `tracker_user` roles), or admins should inherit tracker access. Right now the
menu is visible and every page in it fails.

---

# 4. 🟠 Three endpoints crash — a half-finished `branch` refactor

All three are the same root cause: `branch` was added to the service layer and
three call sites were not updated.

| endpoint | status | error |
|---|---|---|
| `/api/hana/product-stock/` | 502 | `name 'unique_schemas' is not defined` |
| `/api/hana/product-so/` | 500 | `Queries.get_sales_orders_for_product() takes 1 positional argument but 2 were given` — `hana\services\services.py:23` |
| `/api/sku/pending/` | 500 | `SalesOrderService.getFGItems() missing 1 required positional argument: 'branch'` — `SKU/views.py:44` calls it with no argument at all |

```bash
curl -s "https://oms.jivo.in/api/hana/product-stock/?branch=OIL" -H "Authorization: Bearer <token>"
```

Fails identically on `branch=OIL` and `branch=BEVERAGE`, so it is not a data
issue. These are 100 % failure rates, not intermittent.

---

# 5. 🟡 `/api/invoice/all/` cannot be called by anyone

Returns `400 {"error":"Warehouse Code is a required parameter."}` for **eleven**
candidate parameter names across two transports (`warehouse`, `warehouse_code`,
`whs_code`, `WarehouseCode`, `warehouseCode`, `wh_code`, …). The route appears
nowhere in the deployed SPA bundle, so there is no client call to copy.

`OPTIONS` says it is `"Invoice Log List"`, versus `"Invoice Log List wo Whs"`
for `/api/invoice/logs/all/` — so it looks like the superseded, warehouse-scoped
twin of an endpoint that still works. If it is dead, please delete the route; if
it is live, please tell us the parameter name.

---

# 6. 🟡 `category` is silently ignored on one endpoint but honoured on its sibling

`GET /api/auth/users/{id}/parties/?category=BEVERAGES` and `?category=MART`
both return the identical 15 OIL rows — the filter is accepted and dropped. The
same parameter works correctly on `/api/auth/parties/{card_code}/products/`.

A silently-ignored filter is worse than a rejected one: the caller gets a
plausible wrong answer.

---

# 7. 🟡 Duplicate main-group rows

`GET /api/auth/mainGroup/` returns both `CALL CENTER` (id 8) and `CALL CENTRE`
(id 28). Two spellings of one channel will split any report grouped on it.

---

# 8. 🔵 Note — SAP price list 1 is empty, so `item-price` returns nothing useful

Not an OMS bug, but it makes an OMS endpoint useless. ~99.6 % of parties are on
`ListNum` 1, and `MAX(Price)` on price list 1 is 0 in **both** the Oil and
Beverages company databases. `GET /api/hana/item-price/` therefore returns 0 or
null for virtually every customer. JIVO's real rates evidently live outside SAP
pricing. Worth knowing before anyone builds on that endpoint.

---

## How this was found

A read-only survey: 125 endpoint paths harvested from the deployed SPA bundle,
then probed live with GET only, no invented parameter values, and no write verb
ever sent. Nothing was created, updated or deleted on OMS during this work.

Contact: the JIVO CLI toolkit maintainers (`jivo-cli` repo,
`oms-cli/research/` has the full evidence set).
