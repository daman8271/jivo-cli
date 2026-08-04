# Domain study: invoices

17 paths — `/api/invoice/*`, `/api/sku/*`, `/api/legal/*`.
Studied 2026-08-04 against live `https://oms.jivo.in` with the `paramjot` token
(`role=admin`, `company=Jivo Wellness{id:1}`, `category=OIL{id:1}`). Every live
call below was a GET. No write endpoint was probed.

**Verdict tally: 11 publish · 6 exclude.** Three shipped commands are broken
upstream; one of the three (`invoices history`) turned out to be *fixed* and its
patch should be lifted.

---

### `/api/invoice/logs/all/`

- **command**: `invoices logs`   (NEW — reads like the shipped `invoices all`)
- **verdict**: publish
- **description**: The invoice review-and-approval queue. One row per invoice a
  salesperson has submitted out of a sales order, carrying the full SAP B1
  document payload, the finished-goods stock position at the time of submission,
  and where it currently sits between "submitted" and "posted into SAP".
- **params**:
  - `status` — string, optional, not positional.
    Observed enum (from the app's own tab list `p5`, bundle @1705759):
    `PENDING`, `APPROVED`, `POSTED_TO_SAP`, `REJECTED`, `EDITED`, `ERROR`,
    `CL_RAISED`, and the client-side sentinel `ALL`.
    Live counts on 2026-08-04: PENDING 5, POSTED_TO_SAP 14, ERROR 4,
    APPROVED 0, REJECTED 0, EDITED 0, CL_RAISED 0, **ALL 0**.
- **response**: `array` — 23 rows, 37,207 bytes, unpaginated.
  Row fields: `id`, `so_number`, `party_name`, `total_amount` (**string**, e.g.
  `"10091.00"`), `branch`, `warehouse`, `status`, `rejection_reason`,
  `error_message`, `invoice_payload` (nested object — the SAP B1 `Invoices`
  document), `sap_doc_num`, `sap_doc_entry`, `created_at`, `created_by`
  (**int user id**), `fg_stock` (array), `supersedes`, `supersedes_so_number`,
  `supersedes_status`, `supersedes_rejection_reason`, `superseded_by_id`.
  - `invoice_payload` keys: `Series`, `DocObjectCode`, `DocDate`, `TaxDate`,
    `DocDueDate`, `CardCode`, `NumAtCard`, `PayToCode`, `ShipToCode`,
    `SalesPersonCode`, `BPL_IDAssignedToInvoice`, `U_Recv_Date`,
    `U_Dipatch_Date` (sic — the backend's own typo), `DocumentLines[]`.
  - `DocumentLines[]` keys: `LineNum`, `BaseType` (17 = sales order),
    `BaseEntry`, `BaseLine`, `ItemCode`, `Quantity`, `WarehouseCode`,
    `TaxCode`, `ShipDate`, `BatchNumbers[]`.
  - `fg_stock[]` keys: `line_num`, `item_code`, `item_name`, `quantity`,
    `warehouse_code`, `warehouse_stock`.
- **evidence**: 200 bare (23 rows) and 200 for each of the 8 status values,
  all run live today. Bundle call site @1709858:
  `X6(\`/api/invoice/logs/all/${e===\`ALL\`?\`\`:\`?status=${e}\`}\`)`.
  `OPTIONS` names the view **"Invoice Log List wo Whs"**.
- **traps**:
  - **`status=ALL` returns an empty array, not everything.** `ALL` is a UI tab
    label; the app deliberately omits the whole `?status=` param when ALL is
    selected. A CLI that passes `--status ALL` through returns 0 rows and looks
    like a data problem. Treat `ALL` (and no flag) as "send no `status`".
    Verified live: `?status=ALL` -> 200, `[]`, 2 bytes.
  - `total_amount` is a **string**, not a number. Do not sum it without casting.
  - `created_by` here is an **integer user id**; the same field name in
    `/api/invoice/history/{id}/` is a **display name string**. Do not join them.
  - `error_message` is *sticky*: it survives a later successful post. Log 33 is
    `POSTED_TO_SAP` and still carries `"(135018) Please select sales person
    name"` from an earlier failed attempt. Reading `error_message` as "this
    invoice is broken" is wrong — read `status`.
  - All 23 rows are `branch: OIL` for this credential. That is a data fact for
    this token, not a scope constraint. The endpoint takes no `branch` param.
  - 13 of the 14 `POSTED_TO_SAP` rows have a `sap_doc_num`; log 21 has
    `sap_doc_num: null` and `sap_doc_entry: null`. Log 34 has a `sap_doc_num`
    but a null `sap_doc_entry`. Neither field is reliably populated.

---

### `/api/invoice/history/{id}/`

- **command**: `invoices history`   (SHIPPED — do not rename)
- **verdict**: **publish — and LIFT patch 0003**
- **description**: The full status timeline of one invoice in the review queue —
  every state it passed through, who moved it, and the SAP error text that
  bounced it, oldest first.
- **params**:
  - `id` — int, required, positional. The `id` from `/api/invoice/logs/all/`.
    (App source uses `e.invoice_log ?? e.id`, bundle @1715209 — history rows
    carry `invoice_log` pointing back at the log id.)
- **response**: `array` (the shipped spec said `object` — wrong).
  Row fields: `id` (history row id, distinct from the log id), `invoice_log`
  (the parent log id), `so_number`, `party_name`, `total_amount`, `status`,
  `rejection_reason`, `error_message`, `invoice_payload`, `created_at`,
  `created_by` (**display name string**, e.g. `"Harpreet"`,
  `"Warehouse Operations"`, or `null` for machine transitions).
- **evidence**: live today —
  ```
  GET /api/invoice/history/44/  -> 200, 879 bytes, 1 row
  GET /api/invoice/history/53/  -> 200, 4,868 bytes
  GET /api/invoice/history/33/  -> 200, 8,836 bytes, 10 rows
  GET /api/invoice/history/20/  -> 200, 14,693 bytes, 15 rows
  GET /api/invoice/history/999/ -> 404 {"error":"Invoice log not found"}
  ```
- **traps**:
  - **The shipped spec's "BACKEND ROUTE MISSING" note is now stale.** Patch 0003
    unregistered this command on 2026-07-19 because the route 404'd. It exists
    and works today. Re-register it. Confidence: high — four distinct real ids
    returned 200 with structured data, and an invented id returns a *typed*
    404 (`Invoice log not found`), which is a live view, not a missing URL.
  - Rows are not returned sorted; the app sorts by `created_at` then `id`.
  - `created_by` is `null` for automatic transitions (the SAP post attempt).

---

### `/api/invoice/all/`

- **command**: `invoices all`   (SHIPPED — do not rename)
- **verdict**: **exclude**
- **exclusion reason**: proven dead *(qualified: the route is alive but has no
  callable contract — see below. Keep the name reserved; do not reuse it.)*
- **description**: Would be the invoice review queue filtered to one warehouse.
  It is the warehouse-scoped twin of `/api/invoice/logs/all/`.
- **params**: **unresolved.** The server demands a "Warehouse Code" it will not
  name in any form we can send.
- **response**: `UNVERIFIED` — never returned anything but HTTP 400.
- **evidence**: every call returns
  `HTTP 400 {"error":"Warehouse Code is a required parameter."}`.
  Previously tried (prior probe): `warehouse`, `warehouse_code`, `whs_code`,
  `WarehouseCode`, `warehouseCode`, `wh_code`. Added today, then **stopped**:
  ```
  ?WhsCode=BH-BT                     -> 400  (same body)
  ?Warehouse%20Code=BH-BT            -> 400  (same body)
  header Warehouse-Code: BH-BT       -> 400  (same body)
  header X-Warehouse-Code: BH-BT     -> 400  (same body)
  header WhsCode: BH-BT              -> 400  (same body)
  ```
  (`BH-BT` is a real warehouse code, observed live in `/api/invoice/logs/all/`.)
- **what I found instead** — three pieces of evidence that close off the obvious
  hypotheses:
  1. **The SPA has no reference to this route at all.** `peek.py` finds zero
     occurrences of `invoice/all` in the 2 MB deployed bundle. The only
     `WarehouseCode` hits in the bundle are SAP B1 `DocumentLines` payload
     construction, not a query param. There is no observed call to copy, and
     there never was — the path came into the harvest from the *shipped spec*
     only (`lenses: shipped-only`).
  2. **`OPTIONS` names both views, and they are twins:**
     ```
     OPTIONS /api/invoice/all/       -> {"name":"Invoice Log List"}
     OPTIONS /api/invoice/logs/all/  -> {"name":"Invoice Log List wo Whs"}
     ```
     "wo Whs" = *without warehouse*. The OMS team forked this view to drop the
     warehouse requirement, and the app uses the forked one exclusively.
     `/api/invoice/all/` is superseded, not merely broken.
  3. **The header hypothesis is dead by construction.** The leaked Django
     settings (see `/api/sku/pending/` below) show
     `CORS_ALLOW_HEADERS = ('accept','authorization','content-type',
     'user-agent','x-csrftoken','x-requested-with','x-app-version',
     'x-build-number','x-platform','x-app-type','x-os-version','x-device-id')`
     — no warehouse header exists in the allowlist any browser client could
     send. And the login user object (`login.json`) has no warehouse/whs field,
     so it is not read off the profile either.
- **traps**:
  - **I could not resolve this contract, and I stopped rather than keep guessing
    names.** Eleven names across two transports all return the identical 400.
    Only the OMS team's `views.py` can settle it.
  - Publishing this as a working command repeats the exact failure this rescrape
    exists to fix (14 `hana` commands that ship, read correctly, and cannot
    succeed). **Recommendation for the generator: do not register a command;
    reserve the name `invoices all` so nothing else claims it, and point
    operators at `invoices logs`, which is the same data unfiltered.**
    Confidence that `invoices logs` is the right replacement: high — the view
    names say so. Confidence about the missing param name: none.

---

### `/api/invoice/credit-limit/cards/`

- **command**: `invoices credit-limit-cards`   (NEW)
- **verdict**: publish
- **description**: The credit-limit master for every customer account in one SAP
  company — how much each party currently owes, the credit line they are allowed,
  and the debt line. This is what the reviewer looks at before releasing an
  invoice for a party who is close to their limit.
- **params**:
  - `company` — string/int, optional (defaults to `1`), not positional.
    **Observed values: `1` and `2`.** Sourced from the app's own mapper
    (bundle @1707491):
    `S5 = e => String(e||\`\`).trim().toUpperCase() === \`BEVERAGE\` ? \`2\` : \`1\``
    — the app calls this endpoint as `?company=${S5(e.branch)}`, i.e. it maps
    the invoice's `branch` to a numeric SAP company id:
    **`OIL` (and anything not BEVERAGE) -> `1`, `BEVERAGE` -> `2`.**
- **response**: `object` — `{success: bool, data: [...]}`.
  `data[]` fields: `cardCode`, `cardName`, `cardType`, `balance`, `debtLine`,
  `creditLine` — **all money fields are strings** (`"15051.139800"`).
  Observed `cardType` values include `CASH SALE`, `ROI`.
- **evidence**: live today —
  ```
  bare              -> 200, 176,607 bytes, data rows = 1172
  ?company=1        -> 200, 176,607 bytes, data rows = 1172
  ?company=2        -> 200, 182,989 bytes, data rows = 1247
  ```
  The row counts match `/api/hana/all-customers/` exactly (OIL 1172,
  BEVERAGE 1247, API-FACTS §2), which independently confirms `1`=OIL, `2`=BEVERAGE.
- **traps**:
  - **`company` here is a numeric SAP company id, NOT the `branch` enum and NOT
    the `category` enum.** This API now has three tenant vocabularies:
    `branch` = `OIL|BEVERAGE` (hana/*), `category` = `OIL|BEVERAGES|MART`
    (sap/parties, auth), `company` = `1|2` (this endpoint). Sending
    `?company=OIL` was not probed and is not observed anywhere — do not.
  - Bare (no `company`) silently defaults to company 1 / OIL. A number quoted
    from a bare call is an **Oil** number. Same rule as SAP: never quote it
    without naming the company.
  - 1,172–1,247 rows in one unpaginated response (~177 KB). Needs
    `--compact`/`--csv` to be usable, same as `sap/addresses/`.
  - This is a HANA-backed master, not a local table — it is the live SAP
    balance, so it moves.

---

### `/api/invoice/credit-limit/flow/`

- **command**: `invoices credit-limit-flow`   (NEW)
- **verdict**: publish
- **description**: The approval chain for a credit-limit override request raised
  against one invoice — which named approver sits at which stage, in what order,
  and whether they approved, rejected or have not acted.
- **params**:
  - `invoice_id` — int, **required**, positional. Server's own words:
    `{"error":"invoice_id is a required parameter."}`. Value source: the `id`
    from `/api/invoice/logs/all/`.
  - `company` — optional, values `1`/`2` from `S5(branch)`; the app sends it
    (bundle @1713437: `?invoice_id=${id}&company=${S5(e.branch)}`).
    **Observed to be ignored by the server** — `invoice_id=33` returns byte-identical
    data with `company=1`, `company=2`, and with the param omitted. Document it
    as accepted-but-inert rather than claiming it selects anything.
- **response**: `object` — `{success: bool, data: [...]}`.
  `data[]` fields: `stageId`, `stageName`, `priority` (sort key), `assignedTo`
  (person's name), `actionStatus` (**`A`=Approved, `R`=Rejected, `P`=Pending** —
  from the app's own map `vme`, bundle @1707491), `actionDate`, `description`,
  `approvalRequired`, `rejectRequired`.
- **evidence**: I probed **all 23** invoice ids live. **Exactly two have
  credit-limit logs:**
  ```
  invoice_id=33 -> 200 {"success":true,"data":[{"stageId":996,
                   "stageName":"cl oil int 1","priority":1,
                   "assignedTo":"Preshit Jivo","actionStatus":"A",
                   "actionDate":"2026-07-31T08:43:36","description":" ",
                   "approvalRequired":1,"rejectRequired":1}]}
  invoice_id=20 -> 200 (same single stage, same approver)
  the other 21  -> 404 {"error":"No CreditLimitLogs entry found for the given invoice_id."}
  ```
- **traps**:
  - **404 is the normal case, not an error.** 21 of 23 invoices have no
    credit-limit request. A command that treats 404 as failure will look broken
    on almost every id. Render it as "no credit-limit request raised".
  - Rows come back unsorted; the app sorts by `priority`.
  - Only one approval stage exists today (`cl oil int 1`, Preshit Jivo). The
    shape is a chain, but the live data has a chain of length 1 — do not assume
    multi-stage behaviour is exercised.

---

### `/api/invoice/pending/`

- **command**: —
- **verdict**: **exclude**
- **exclusion reason**: write verb (POST)
- **description**: Submits a built invoice into the review queue. Bundle
  @1604601 shows it POSTing `{so_number, party_name, total_amount,
  status:"PENDING", branch, warehouse, created_by, edited_from, invoice_payload}`.
- **evidence**: harvested `POST`, never probed. RULE 0.
- **traps**: this is the entry point of the whole workflow — anything that
  "helpfully" retries a failed invoice would create a duplicate review row.

---

### `/api/invoice/{id}/update-status/`

- **command**: —
- **verdict**: **exclude**
- **exclusion reason**: write verb (PATCH)
- **description**: Approves, rejects or edits an invoice in the review queue.
- **evidence**: harvested `PATCH`, never probed. RULE 0.
- **traps**: an approval here ends with a document being posted into SAP B1.
  Never expose it, not even behind a confirm.

---

### `/api/invoice/credit-limit/request/`

- **command**: —
- **verdict**: **exclude**
- **exclusion reason**: write verb (POST, multipart)
- **description**: Raises a credit-limit override request against an invoice
  (with a supporting attachment) — the action that moves an invoice to
  `CL_RAISED` and creates the row `credit-limit/flow` reads.
- **evidence**: harvested `POST` + multipart-upload flag, never probed. RULE 0.
- **traps**: the app's own error text shows the server rejects duplicates
  (`"A credit-limit request has already been raised for this invoice."`), so a
  retry is not idempotent from the operator's point of view.

---

### `/api/sku/all/`

- **command**: `invoices skus`   (SHIPPED — do not rename)
- **verdict**: publish
- **description**: The local SKU image library — the product photographs OMS
  attaches to finished-goods item codes so invoice lines and the review screen
  can show the actual bottle.
- **params**: none observed.
- **response**: `array` (the shipped spec said `object` — wrong). Zero rows for
  this credential. Field names, from the app's own mapper (bundle @1674171,
  @1677452): `item_code`, `item_name`, `item_image` (a relative media path —
  the app prefixes it with the site origin, not `/api`), plus a created/updated
  timestamp rendered by `q8`.
- **evidence**: 200 bare, `[]`, 2 bytes.
- **traps**:
  - **A 0-row 200 is a data fact.** The image library is empty right now; that
    is not a scope constraint and must not be encoded as one.
  - `item_image` is relative and resolves against `https://oms.jivo.in`
    (`Da`), **not** against `https://oms.jivo.in/api`. A command that joins it
    to the API base produces dead links.

---

### `/api/sku/pending/`

- **command**: `invoices skus-pending`   (SHIPPED — do not rename)
- **verdict**: publish
- **exclusion reason**: n/a
- **description**: The finished-goods SKUs that still have **no product image
  uploaded** — the to-do list for whoever photographs the range. (Meaning read
  off the backend's own leaked source, below: HANA FG items minus the local SKU
  rows that have a non-empty `item_image`.)
- **params**: none that work. `branch` is *not* read by the view (proven below).
- **response**: `UNVERIFIED` — this endpoint has never returned a body. Expected
  shape from the app's mapper (`Wpe`, bundle @1674709): array of
  `{ItemCode, ItemName, U_Brand, U_Sub_Group, U_Variety, U_SKU, TotalQty}`.
- **evidence**: **HTTP 500 on every form, verified live today:**
  ```
  GET /api/sku/pending/                  -> 500, 97,647 bytes
  GET /api/sku/pending/?branch=OIL       -> 500, 98,114 bytes
  GET /api/sku/pending/?branch=BEVERAGE  -> 500, 98,189 bytes
  GET /api/sku/pending/?branch=MART      -> 500, 98,129 bytes
  ```
  All four:
  `TypeError: SalesOrderService.getFGItems() missing 1 required positional argument: 'branch'`
- **traps**:
  - **`?branch=` does not and cannot fix it.** The debug page leaks the view's
    own source at `C:\LiveProjects\OMS\Backend\SKU\views.py` line 44:
    ```python
    class SKUPendingList(APIView):
        def get(self, request):
            # 1. Fetch the master list from HANA
            all_skus = SalesOrderService().getFGItems()     # <- line 44, no argument
            # 2. Fetch local SKUs that ACTUALLY have images, and cast to a set for speed
            local_completed_skus = set(
                SKU.objects.exclude(item_image__exact='')
                           .exclude(item_image__isnull=True)
                           .values_list('item_code', flat=True)
    ```
    The call is hard-coded with no argument. No query parameter reaches it.
    This is a one-line backend fix (`getFGItems(branch)`), not a client problem.
  - Publish the command with the 500 documented. It is a real endpoint with a
    real purpose; it is broken today, and marking the response `UNVERIFIED` with
    the server's own wording is the honest record.

---

### 🔴 `/api/sku/pending/` — the DEBUG=True production leak

Serious enough to stand on its own. **Any authenticated caller** — no special
role; this is a plain `admin` token — gets **97.6 KB of Django debug HTML** back.
Because `DEBUG=True`, *every* unhandled exception on this backend renders this
page, so this one endpoint is only the doorbell.

`DEBUG: True` is stated verbatim in the leaked settings table. Django's
`cleanse_setting` masked the obvious secrets (`SECRET_KEY`, all `*PASSWORD*`,
`SIMPLE_JWT`, and the caller's own `HTTP_AUTHORIZATION`) as
`'********************'`. **Everything below was NOT masked and came back in
clear text:**

| leaked | value |
|---|---|
| internal origin | `http://127.0.0.1:8001`, `SERVER_SOFTWARE: waitress` behind `Microsoft-IIS/10.0` + `ARR/3.0` |
| stack versions | Django **5.2.10**, Python **3.14.3**, DRF, whitenoise |
| source tree | `C:\LiveProjects\OMS\Backend\`, `.venv`, `MEDIA_ROOT`, `STATIC_ROOT`, 24 distinct absolute server paths |
| OS account | `C:\Users\ADMIN\AppData\Local\Programs\Python\Python314\...` |
| **application source** | the real body of `SKU/views.py` around line 44 (shown above), plus DRF frames |
| **Postgres** | `HOST 20.20.45.75`, `USER postgres` |
| **HANA** | `HOST 20.20.45.192`, `USER DSR`, `OIL_SCHEMA JIVO_OIL_HANADB`, `BEVERAGE_SCHEMA JIVO_BEVERAGES_HANADB` |
| other SAP DBs | `JIVO_MART_HANADB`, `TEST_OIL_15122025` |
| **GST e-invoice (NIC) usernames** | `API_Jivo`, `API_Jivo_HP`, `API_Jivo_PB`, `API_Jivo_DL`, `API_Jivo_RJ_01`, `API_Jivo_UP`, `API_Jivo_MH` against `https://api.einvoice1.gst.gov.in` and `https://api.ewaybillgst.gov.in/v1.03` |
| SMB shares | `\\20.20.45.25\OMS_Attachments\{OIL,MART,BEVERAGE}_ATTACHMENTS\Bitmap`, SMB user `OMS` |
| other services | `CRYSTAL_URL http://20.20.45.75:8008`, `DSR_API_BASE` |
| mail | `smtp.gmail.com:587` as `mukesh.jivo03@gmail.com` |
| **`ALLOWED_HOSTS`** | `['103.89.45.75','127.0.0.1','10.0.2.2','localhost','192.168.1.240','*']` — **contains `'*'`** |
| **`CORS_ALLOW_ALL_ORIGINS`** | **`True`** |
| local variables | every traceback frame's locals, `Server time`, `INSTALLED_APPS`, `MIDDLEWARE` |

Reproduction, one line:

```bash
curl -s -H "Authorization: Bearer $TOKEN" https://oms.jivo.in/api/sku/pending/ | wc -c   # 97647
```

Three separate defects, in priority order for the OMS team:
1. **`DEBUG = False` in production.** This is the whole finding. Everything else
   in the table follows from it.
2. `CORS_ALLOW_ALL_ORIGINS = True` **and** `ALLOWED_HOSTS` containing `'*'` —
   any origin can drive this API with a stolen token, and Host-header checks are
   off.
3. `SalesOrderService().getFGItems()` needs its `branch` argument (`SKU/views.py`
   line 44) — the crash that exposes 1 and 2.

Related, from API-FACTS §6: the login response also returns the user's PBKDF2
password hash to the client. Same class of problem, different endpoint.

---

### `/api/sku/{item_code}/`

- **command**: `invoices sku`   (SHIPPED — do not rename)
- **verdict**: publish (GET only — see traps)
- **description**: The stored product image and name for one finished-goods item
  code.
- **params**:
  - `item_code` — string, required, positional. Value source: `ItemCode` from
    `/api/hana/fg-items/?branch=OIL` (443 rows, live) and `fg_stock[].item_code`
    in the invoice logs. The backend's own leaked source confirms
    `lookup_field = 'item_code'`.
- **response**: `object` — **UNVERIFIED for a hit.** Every real item code
  returns 404 because the local SKU table is empty (`/api/sku/all/` = 0 rows).
  Field names from the app's mapper: `item_code`, `item_name`, `item_image`.
- **evidence**: live today, with codes sourced from HANA, not invented —
  ```
  GET /api/sku/FG0000032/  -> 404 {"detail":"No SKU matches the given query."}
  GET /api/sku/FG0000386/  -> 404 {"detail":"No SKU matches the given query."}
  ```
  `FG0000032` (COLD PRESS 1 LTR 20 PCS) appears in invoice log 44's `fg_stock`;
  `FG0000386` is the first row of `/api/hana/fg-items/?branch=OIL`. Nothing was
  created — the DRF message is a retrieve miss, and the endpoint is a lookup on
  an existing queryset, not a `get_or_create`.
- **traps**:
  - **This path serves three verbs.** Bundle @1676236:
    `X6(K8(item_code))` = GET, `Z6(K8(id), formData, 'PATCH')` = multipart image
    update, `Gfe(K8(id))` = **DELETE** (`Gfe` is the axios DELETE wrapper,
    @1590749). Only the GET may be published; an exclusion keyed on path alone
    would wrongly kill the read, and a *generator* keyed on path alone would
    wrongly ship the write. Same hazard as the dual-verb paths in API-FACTS §5.
  - 404 is the expected result today for every code, because the image library
    is empty. That is data, not a broken command.

---

### `/api/sku/upload/`

- **command**: —
- **verdict**: **exclude**
- **exclusion reason**: write verb (POST, multipart)
- **description**: Uploads a cropped product photo against an item code
  (`FormData{item_code, item_name, item_image}`, bundle @1676089).
- **evidence**: `url-constant-only` + write-intent; never probed. RULE 0.
- **traps**: `X6`'s method defaults to GET (API-FACTS §1). This URL lives in a
  module const (`Gpe`) and is only ever passed to the multipart wrapper `Z6` —
  exactly the shape that fools method inference. Deny by path.

---

## The `/api/legal/` family — what this module actually is

**It is an FSSAI food-label compliance checker.** An operator uploads the
artwork PDF for a pack (up to 20 MB), the backend reads the label and reports,
field by field, whether every statutory declaration Indian packaged-food law
requires is actually printed on it — and flags what is missing or doesn't match
what JIVO declared.

The four GET endpoints are the reference masters it checks against; the upload
is the check itself.

From the app's own field map (`C7`, bundle @1825837) the checklist is:
`food_name`, `product_category`, `veg_nonveg` (the green/brown mark),
`barcode`, `ingredients`, `serving_details`, `nutritional_facts`,
`fssai_details`, `manufacturer_packer_details`, `importer_country_of_origin`,
`packaging_epr`, `date_of_mfg`, `expiry_date`, `batch_lot_number`, `mrp`,
`unit_sale_price`, `cost_block`, `jivo_trademark`, `iso_certification`,
`illustration_disclaimer`, `footnote_signs` — grouped in the UI (`P7`,
@1828037) as **Product information / Ingredients & nutrition / Regulatory
compliance / Commercial information**.

The analyser returns each field with a **status** — `ok` | `missing` |
`mismatch` | `na` (`k7`, @1827276) — and a **confidence** of `high`/`medium`/
`low` (scored 0.97 / 0.80 / 0.60 by `D7`). Its progress messages give away the
pipeline: *"Converting PDF pages to images… Reading the label artwork…
Extracting statutory declarations… Checking nutritional information…
Compiling the compliance report…"* (`F7`, @1828833). The report can be exported
as JSON.

Only one product has been set up so far: **"Kachi Ghani Mustard Oil Pouch"**
(item id 1, created 2026-07-27). The module is a week old and barely populated.

### `/api/legal/item/`

- **command**: `legal items`   (NEW — new resource `legal`)
- **verdict**: publish
- **description**: The food products whose pack labels are checked for FSSAI
  compliance. One row per product.
- **params**: none observed on GET.
- **response**: `array` — 1 row. Fields: `id`, `item_name`, `created_at`.
- **evidence**: 200, 97 bytes, `[{"id":1,"item_name":"Kachi Ghani Mustard Oil
  Pouch","created_at":"2026-07-27T09:35:48.484272Z"}]` (live today).
- **traps**: **dual-verb collection** — the same URL takes `POST {item_name}`
  (bundle @1852565), and `/api/legal/item/{id}/` takes `PATCH` and `DELETE`.
  Publish the collection GET only; deny `POST` on it and deny the `{id}` child
  path entirely (it has no GET).

### `/api/legal/uom/`

- **command**: `legal uoms`   (NEW)
- **verdict**: publish
- **description**: The units of measure used when declaring nutritional values
  on a label (g, kcal, mg …).
- **params**: none observed on GET.
- **response**: `array` — **0 rows**. Field names from the app's create call:
  `id`, `uom_name`, `uom_unit`.
- **evidence**: 200, `[]`, 2 bytes (live today).
- **traps**: dual-verb — `POST {uom_name, uom_unit}`, plus `PATCH`/`DELETE` on
  `/api/legal/uom/{id}/`. 0 rows is a data fact: the module is new.

### `/api/legal/nutrition/`

- **command**: `legal nutrition`   (NEW)
- **verdict**: publish
- **description**: The master list of nutrition rows (the nutrient lines that
  can appear in a nutritional-information table).
- **params**: none observed on GET.
- **response**: `array` — **0 rows**. Field shape not observable; the app posts
  a whole object and reads `id` back.
- **evidence**: 200, `[]`, 2 bytes (live today).
- **traps**: dual-verb — `POST`, plus `PATCH`/`DELETE` on
  `/api/legal/nutrition/{id}/`. Response shape beyond `id` is **UNVERIFIED**;
  I did not see a populated row.

### `/api/legal/item-nutrition/`

- **command**: `legal item-nutrition`   (NEW)
- **verdict**: publish
- **description**: The nutritional facts JIVO has declared for one product — the
  reference values an uploaded label is checked against.
- **params**:
  - `item_id` — int, optional in practice, not positional. Value source: the
    app's own call `Y.get(ehe, {params:{item_id: c}})` (bundle @1852048), where
    `c` is an `id` from `/api/legal/item/`.
- **response**: `object` — `{"nutritional_facts": []}`.
- **evidence**: live today —
  ```
  GET /api/legal/item-nutrition/            -> 200, 24 bytes, {"nutritional_facts":[]}
  GET /api/legal/item-nutrition/?item_id=1  -> 200, 24 bytes, {"nutritional_facts":[]}
  ```
- **traps**: it is the one endpoint in this family that returns a **dict, not a
  list** — the rows are under `nutritional_facts`. Omitting `item_id` does not
  error; it returns the same empty envelope, so an operator cannot tell "no such
  item" from "no facts declared". Contents of a populated row: **UNVERIFIED**.

### `/api/legal/upload/`

- **command**: —
- **verdict**: **exclude**
- **exclusion reason**: write verb (POST, multipart)
- **description**: Uploads a label-artwork PDF (≤ 20 MB) tagged to an
  `item_id` and runs the compliance analysis
  (`FormData{label_file, item_id}`, bundle @1835618).
- **evidence**: `url-constant-only` + write-intent; never probed. RULE 0.
- **traps**: same method-inference hazard as `sku/upload` — the URL sits in a
  module const (`zme`) and only ever reaches `Z6(..., 'POST')`. Deny by path.

---

## Domain summary

**What this domain is.** It is JIVO's invoice gate. A salesperson turns a sales
order into a draft SAP invoice; instead of going straight into SAP B1 it lands
in a review queue (`invoice/logs/all`), where a warehouse/approver role checks
the stock position (`fg_stock` carries the on-hand quantity per line at the
moment of submission) and the party's credit standing
(`invoice/credit-limit/cards`) before releasing it. On release the backend posts
the document into SAP; SAP frequently refuses it, and the refusal comes back as
`status: ERROR` with SAP's own message. If the refusal is a credit-limit breach,
someone raises an override request and it goes to a named approval chain
(`invoice/credit-limit/flow`). The whole back-and-forth is preserved per invoice
in `invoice/history/{id}`. Bolted onto the same app are two small side modules:
`/api/sku/` (product photographs keyed to item codes) and `/api/legal/` (a
week-old FSSAI label-compliance checker).

**The observed lifecycle**, read straight off history/20 and history/33:

```
PENDING -> APPROVED -> ERROR -> CL_RAISED -> ERROR -> ... -> POSTED_TO_SAP
                        ^                                          |
                        +---- resubmit / EDITED --------------------+
   REJECTED (reviewer refuses, rejection_reason set) is a terminal branch
```

Status enum (app source `p5`, confirmed live): `PENDING`, `APPROVED`,
`POSTED_TO_SAP`, `REJECTED`, `EDITED`, `ERROR`, `CL_RAISED`. `ALL` is a UI
sentinel and returns 0 rows if sent.

**This is not a clean pipe.** Of 23 invoices, 4 are stuck in `ERROR` and one
(id 20) bounced **15 times** before posting. The real SAP refusals seen today
are: *negative inventory*, *insufficient batch quantity*, *credit limit
exceeded*, *please select sales person name*, *batch not found*. Nine of the 23
invoices were still not posted at the time of this study.

**Traps that apply across the whole domain**
1. `status=ALL` returns nothing. Send no `status` instead.
2. Money fields are strings everywhere (`total_amount`, `balance`, `debtLine`,
   `creditLine`). Cast before arithmetic.
3. `created_by` is an **int id** in `logs/all` and a **name string** in
   `history/{id}`. Same name, different type, do not join.
4. `error_message` is sticky and survives a successful post. `status` is the
   truth.
5. Three tenant vocabularies now coexist: `branch` = `OIL|BEVERAGE`,
   `category` = `OIL|BEVERAGES|MART`, and (new, this domain) `company` = `1|2`
   where 1=OIL and 2=BEVERAGE. Never substitute one for another.
6. `/api/sku/{item_code}/` and the three `/api/legal/` collections are
   multi-verb paths. GET publishable, everything else denied — and the write
   URLs all live in module constants passed to the multipart/DELETE wrappers,
   which is precisely the shape that defeats method inference (API-FACTS §1).
7. `/api/sku/all/`, `/api/legal/uom/` and `/api/legal/nutrition/` return 0 rows
   for this credential. Data fact, not a scope constraint.

**Backend defects, with reproductions**

| # | endpoint | severity | reproduction | root cause |
|---|---|---|---|---|
| 1 | `/api/sku/pending/` | **critical** | `curl -H "Authorization: Bearer $T" https://oms.jivo.in/api/sku/pending/` -> 500, 97,647 bytes of Django debug HTML | `DEBUG=True` in production + `SalesOrderService().getFGItems()` missing its `branch` arg at `SKU/views.py:44`. `?branch=` cannot fix it — the call takes no argument. Leaks source, DB hosts, HANA schemas, GST API usernames, SMB paths, `ALLOWED_HOSTS=['*']`, `CORS_ALLOW_ALL_ORIGINS=True`. |
| 2 | `/api/invoice/all/` | high (shipped command dead) | any call -> `400 {"error":"Warehouse Code is a required parameter."}` — 11 param/header names tried across two transports | **unresolved.** The route is absent from the SPA bundle entirely; `OPTIONS` names it *"Invoice Log List"* against *"Invoice Log List wo Whs"* for `/api/invoice/logs/all/`, so it is the superseded warehouse-scoped twin. Only OMS's `views.py` can name the parameter. |
| 3 | `/api/invoice/history/{id}/` | **RESOLVED — lift the patch** | `curl .../api/invoice/history/33/` -> 200, 10 rows | The route the 2026-07-19 verify could not find now exists. Patch 0003 unregistered `invoices history`; re-register it. |

**Durable JIVO business truth worth recording as a correction**

- *An OMS "invoice" is not an SAP invoice until `status = POSTED_TO_SAP`.* The
  review queue holds a **proposed** SAP document (`invoice_payload`); nothing
  has moved in stock or in the ledger while it sits at PENDING/APPROVED/ERROR.
  Counting OMS invoice rows as sales, or their `total_amount` as turnover, will
  overstate — 9 of 23 rows today never reached SAP at all. Turnover stays
  `Invoices` net of GST in SAP.
- *In the OMS credit-limit endpoints, `company` is `1` = Oil and `2` = Beverage
  — a third tenant vocabulary alongside `branch` and `category`.* Confirmed by
  row counts matching `hana/all-customers` exactly (1172 / 1247).

**What I could not verify**
- The required parameter of `/api/invoice/all/`. Eleven names, two transports,
  identical 400. Recorded unresolved rather than guessed further.
- A populated response for `/api/sku/{item_code}/`, `/api/legal/nutrition/`,
  `/api/legal/uom/` and `/api/legal/item-nutrition/` — every one of them is
  genuinely empty today, so their field lists come from the app's source, not
  from a live row. Marked UNVERIFIED, not assumed.
- The real response of `/api/sku/pending/` — it has never once returned a body.
- Whether `company` on `credit-limit/flow` does anything. It is accepted and had
  no observable effect on the one id I could test it with (n=1 invoice, 2
  values). Recorded as inert with low confidence, not as absent.
