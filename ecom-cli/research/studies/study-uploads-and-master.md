# Domain study — `uploads-and-master` (upload · uploads · master · notifications · chatbot · auth)

Bundle: `study/bundles/uploads-and-master.json` · 37 endpoints · probe verdicts: **15 LIVE (200), 22 UNPROBED**
Evidence also read: the SPA bundle (`api-De44ElJm.js`, `uploaderUtils-D0yunz1d.js`,
`MasterSheetManager-CWEDZOOq.js`, `UploadHub-CFeNTXbc.js`, `FkGroceryUploader-qAJP3aLc.js`,
`shipmentAPI-DKVOXJWL.js`), the raw probe payloads in `probe/probe-run1.jsonl` and
`probe/probe-params.jsonl`, and the shipped `ecom-cli/spec.yaml` v0.1.0.

**Unlike the sibling shipment domain, this one is real: 15 endpoints returned live 200s and
I read their payloads.** Everything in §2 for those 15 is written from data. The 22 UNPROBED
endpoints are almost all **writes**, excluded by RULE 0 — they are not dead, and §5 says so
for each one individually.

---

## 1. What this domain is, in operator language

This is **the reference data the rest of the e-com app is built on, plus the paper trail of
how it got there.**

Every number on every dashboard in `ecom.jivo.in` comes from a file somebody uploaded — an
Amazon PO export, a Blinkit inventory sheet, an appointment CSV. This domain answers two
kinds of question. First: *"what does the system think a SKU is?"* — the product master
(907 channel-SKU rows mapping Amazon ASINs and Blinkit/Swiggy SKU ids to JIVO's SAP item
codes), the 19 Amazon fulfilment centres, the ads campaign master, the city/state/pincode
table. Second: *"where did this number come from?"* — the upload log (187 jobs, who uploaded
what file when, how many rows landed, how many errored).

It also carries the alert inbox (91 notifications, nearly all "this SKU is about to run out
at this platform") and the app's built-in chat assistant's history.

Who opens it: anyone who has just been given a number they do not believe. An Accounts
person checking whether an Amazon ASIN is mapped to the right SAP code; an e-com executive
checking whether last night's PO file actually loaded; whoever is on the DOH alerts.

---

## 2. Endpoint table

Command names in **bold** are shipped v0.1.0 names — **contractual, do not rename.**
One row has no shipped name and gets a new one in the existing style.

Row counts are the server's own `count`/`total` field, read from the live payload.
**A count is not a page — see Trap 1.**

| command | path | what an operator gets (from the real payload) | required params | status |
|---|---|---|---|---|
| **account me** | `/api/auth/me` | The logged-in user: `id`, `email`, `first_name`, `last_name`, `is_active`, `is_superuser`, `is_staff`, `created_at`, plus three lists — `groups` (observed: Super Admin, Platform Admin, Operations Manager, Dispatch Operator, Finance Analyst, Viewer, Uploader, and one per platform), `permissions` (**144** on the probing account), and `platforms` (10 slugs: amazon, bigbasket, blinkit, citymall, flipkart, flipkart_grocery, jiomart, swiggy, zepto, zomato). Wrapped in a `user` key. | none | **LIVE** (3,695 B) |
| **account permissions** | `/api/auth/permissions` | The same permissions, grouped: `permissions[]` of `{module, count, permissions[]}`. See Trap 6 — `module` mostly is not a module. | none | **LIVE** (9,977 B) |
| `account feature-flags` *(new)* | `/api/auth/feature-flags` | Which optional features are switched on. Observed payload in full: `{"flags": {"uploader": true, "game_play": false}}`. Tiny (45 B) and genuinely useful — it tells you whether the uploader UI is even enabled. | none | **LIVE** |
| **master products** | `/api/master/products` | The product master, **907 rows**: `format` (the sales channel — see Trap 3), `format_sku_code` (that channel's own id; an ASIN on Amazon), `product_name` (the channel's listing title), `item` (JIVO's short name, e.g. `APPLE 200ML`), `sku_sap_code` (e.g. `FG0000258`), `sku_sap_name` (the full SAP item name), `case_pack`, `per_unit` (e.g. `200 MLS`), `per_unit_value`, `tax_rate` (a fraction — `0.05` = 5%), `uom`, `item_head`. Paginated: `results`, `count`, `page`, `page_size`. | none | **LIVE** (15,596 B, count 907) |
| **master fcs** | `/api/master/fcs` | The **19** Amazon fulfilment centres: `fc_id`, `fc_code` (`DED3`, `DED5`, `HBA4`, `HBL4`, `HCC2`, `HCC5`, `HCC6`, `HCI2`, `HDL2`, `HHR7`, …), `city`, `state`, `fc_name`, `region`. All 19 fit in one response (1,863 B). See Trap 4 — two of those columns are empty on every row. | none | **LIVE** (count 19) |
| **notifications list** | `/api/notifications` | The alert inbox, **91** rows + `unread_count`. Each row is a full DOH alert: `id`, `type` (observed `INVENTORY_DOH_LOW`), `title`, `message`, `format` + `platform_slug` (same thing, two spellings), `sku_code`, `sku_name`, `item`, `item_head`, `category`, `sub_category`, `brand`, `inventory_date`, `sales_max_date`, `month_start`, `units_sold`, `ltr_sold`, `soh_units`, `soh_ltr`, `drr_units`, `drr_ltr`, `doh`, `threshold`, `severity`, `read`, `is_read`, `active`, `resolved_at`, `first_seen_at`, `last_seen_at`, `created_at`, `link`, `payload`. | none — but see Trap 5, the SPA sends two you do not | **LIVE** (65,381 B, count 91) |
| **notifications get** | `/api/notifications/{id}` | One alert, same fields, wrapped in `notification` (singular) not `notifications`. Verified against real id **3707**. | `id` | **LIVE** (1,336 B) |
| **notifications inventory-doh** | `/api/notifications/inventory-doh/{id}` | Per the shipped spec, the SKU-level days-of-cover detail behind an alert. **Not probed** — but the id is knowable: every row from `notifications list` carries `link: "/notifications/inventory-doh/3707"`, so the alert id *is* the parameter. | `id` | UNPROBED (carry forward) |
| **upload master-sheet** | `/api/upload/master-sheet` | The editable master sheet behind `master products` — **907 rows**, 19 columns, richer than `master products`: adds `category`, `sub_category`, `brand`, `category_head` (e.g. `BEVERAGE`), `is_litre` / `is_litre_oil` (`Y`/`N` flags), `packaging_cost`. Shape is `{columns[], rows[], total, page, page_size}`. See Trap 2 — this and `master products` are the same table. | none | **LIVE** (11,615 B, total 907) |
| **upload ads-master** | `/api/upload/ads-master` | The ads campaign master, **99 rows**, 5 columns: `month` (a NAME, e.g. `APRIL` — not a date), `campaign_id` (a UUID), `sku_id` (the platform's numeric SKU id, e.g. `15685`), `item` (e.g. `CANOLA 1L`), `format` (e.g. `SWIGGY`). | none | **LIVE** (3,461 B, total 99) |
| **upload pincode-mapping** | `/api/upload/pincode-mapping` | **6,565 rows** of `city`, `state`, `pincode`. Read Trap 7 before using this — it is mostly a city→state list and the name oversells it. | none | **LIVE** (4,168 B, total 6,565) |
| **uploads list** | `/api/uploads` | The upload job log, **187 jobs**: `upload_id`, `main_table_name` (a human label, see Trap 8), `raw_file_name`, `original_file_name`, `uploaded_by` (an email), `uploaded_at`, `status` (observed `completed`), `row_count`, `error_count`, `warning_count`, `report_type` (observed `APPOINTMENT`, `AMAZON_PO`), and a `metadata` object with `upload_source`, `rows_inserted_staging`, `rows_inserted_final`, `rows_updated_final`, `async_processing`, `estimated_rows`. | none | **LIVE** (24,461 B, count 187) |
| **uploads get** | `/api/uploads/{id}` | One job in full, wrapped in `upload`, **plus a `summary` object** the list does not have: `summary_id`, `total_rows`, `valid_rows`, `error_rows`, `warning_rows`, `final_inserted_rows`. The detail also exposes `stored_file_path` (a server filesystem path) and `file_hash` (sha-256). Verified against real id **311**. | `id` | **LIVE** (1,539 B) |
| **chatbot health** | `/api/chatbot/health` | Whether the in-app assistant is up and which engine is behind it. Observed payload in full: `{"ok": true, "engine": "builtin"}`. | none | **LIVE** (30 B) |
| **chatbot conversations** | `/api/chatbot/conversations` | A bare **array** (not an object) of `{id, title, created_at, updated_at, message_count}`. 5 rows observed. See Trap 9 — these look like the calling user's own chats. | none | **LIVE** (706 B) |
| **chatbot conversation** | `/api/chatbot/conversations/{id}` | One conversation with its full `messages[]`: `{id, role, text, data, intent, engine, is_error, file, created_at}`. `data` carries the assistant's tabular answer (`rows`, `columns`, `suggestions`). Verified against real id **13**. | `id` | **LIVE** (4,090 B) |

**Count: 16 endpoints recommended for publication** — 15 carried forward from v0.1.0
(14 verified LIVE, 1 carried unverified), plus 1 new. **21 excluded (§5), plus 4 more found
outside the bundle.**

---

## 3. Traps

### Trap 1 — the row counts above are TOTALS, not what one call returns. `pincode-mapping` says 6,565 and hands you ~45 rows.

**Evidence:** the probe's own extractor prefers `count`/`total`/`total_count` over the length
of the returned array (`probe/probe.py`, `rows_of()`), and the byte sizes prove the gap:
`/api/upload/pincode-mapping` reports **total 6,565** in a **4,168-byte** response. 6,565 rows
of `{"row_id","city","state","pincode"}` cannot fit in 4 KB — that is roughly 45 rows.
Likewise `master products` reports **907** in 15,596 bytes (≈47 rows) and `uploads list`
reports **187** in 24,461 bytes (≈48 rows).

Elsewhere in this same app the observed default is `page: 0, page_size: 50`
(verbatim from live payloads of `/api/platform/amazon/pos` and `/api/sap/sales-invoices/{code}`),
and the uploader UI sends `page_size: 50` explicitly. The arithmetic above is consistent
with 50 for `master products` / `uploads list`, and looks smaller (~25) for the `/api/upload/*`
family. **I could not read the actual `page`/`page_size` values back — they sit past the
1,500-character sample cut in the probe log. Inferred, not observed.**

Every one of these responses *does* echo `page` and `page_size`. **The CLI should print them,
and the help text must say "count is the whole table; you got one page."** An operator who
runs `upload pincode-mapping` and reports "6,565 cities" is right about the table and wrong
about what they were shown; one who counts the rows on screen is wrong about both.

### Trap 2 — `master products` and `upload master-sheet` are the SAME 907 rows. They are not two datasets.

**Evidence:** both report exactly **907**, and the first rows are byte-identical in the
overlapping fields:

```
master/products      : {"format":"AMAZON","format_sku_code":"B0CYH9N7YW","product_name":"200 ml (Pack of 6) (Apple Sugar Free",
                        "item":"APPLE 200ML","sku_sap_code":"FG0000258","sku_sap_name":"GLASS BOTTLE 200 MLS APPLE 12 PCS", …}
upload/master-sheet  : {"row_id":"(28,55)","format_sku_code":"B0CYH9N7YW","product_name":"200 ml (Pack of 6) (Apple Sugar Free",
                        "item":"APPLE 200ML","format":"AMAZON","sku_sap_code":"FG0000258", …}
```

They differ in three ways that matter:

| | `master products` | `upload master-sheet` |
|---|---|---|
| purpose | the clean read view other screens consume | the **editable** view behind the uploader UI |
| columns | 12 | 19 — adds `category`, `sub_category`, `brand`, `category_head`, `is_litre`, `is_litre_oil`, `packaging_cost` |
| envelope | `{results, count, page, page_size}` | `{columns, rows, total, page, page_size}` |
| row key | none | `row_id` — **a Postgres ctid, see Trap 10** |

**Guidance for the CLI help:** *"Need category / brand / packaging cost? use
`upload master-sheet`. Need a clean list to join on? use `master products`. They are the same
907 rows."* Two operators pulling "the product master" from different commands and getting
different column sets is exactly how a reconciliation goes wrong.

### Trap 3 — `format` means **sales channel**, not pack format. And 907 is not 907 products.

**Evidence:** observed values of `format` are `AMAZON`, `SWIGGY` — channel names.
`format_sku_code` is that channel's own identifier (an ASIN like `B0CYH9N7YW` on Amazon, a
numeric id like `15685` on Swiggy). So the master is keyed **channel × SKU**, and the same
physical product appears once per channel it is listed on.

**Consequence: `count: 907` is the number of channel-SKU listings, not the number of
products JIVO sells.** Anyone reporting "we have 907 SKUs" from this endpoint is
over-counting by however many channels each product is on. To get distinct products you
must count distinct `sku_sap_code` yourself — the API offers no such aggregate. Field
`format_name` is accepted as a filter (see §4) which is the safe way to scope to one channel.

### Trap 4 — `master fcs` has two columns that are null on every single observed row.

**Evidence:** all 19 rows in the live payload have `"fc_name": null` and `"region": null`.
Not "sometimes null" — never populated in what came back. The only useful identifiers are
`fc_code` (`DED3`, `HBA4`, …), `city` and `state`.

A CLI table that prints `fc_name` as the human label will show a column of dashes and an
operator will conclude the FC master is broken. **Print `fc_code — city, state`.** Note also
that `city` is dirty in the familiar way: `DED3` is `GURGAON` and `DED5` is `GURUGRAM` —
the same city, two spellings, so grouping FCs by `city` under-counts.

### Trap 5 — the SPA calls `/api/notifications` with two filters that the spec does not declare, and one of them changes the answer.

**Evidence (SPA source, `api-De44ElJm.js`), verbatim:**

```js
… `/api/notifications`, {active_only: true, limit: 200})
  } catch(e){ if(e.status === 404) return {notifications: [], unread_count: 0, unavailable: true} … }
```

Two things follow.

**(a) My count of 91 was obtained with NO parameters.** The app asks for `active_only=true`.
I do not know the server's default when the flag is absent, so **91 may include resolved or
inactive alerts** — the rows carry both `active` and `resolved_at`, and the row I inspected
had `active: true, resolved_at: null`, which tells me the fields exist but not what the
default filter is. **The spec must declare `active_only` (bool) and `limit` (int, SPA sends
200) so an operator can reproduce what the UI shows.** Anyone comparing "the CLI says 91"
against "the bell icon says N" without matching filters will find a discrepancy that is not
a bug.

**(b) This is the app's clearest example of "empty ≠ no data".** The client explicitly
catches a **404** on this endpoint and substitutes an empty result flagged
`unavailable: true`. The backend can 404 here, and the SPA is written expecting it. **The CLI
must not collapse a 404 into "no notifications".** Report the HTTP status.

### Trap 6 — on `account permissions`, the field called `module` is usually not a module.

**Evidence (live payload):**

```json
{"module": "add_amazoninventory", "count": 1, "permissions": ["add_amazoninventory"]}
{"module": "add_asindohdaily",    "count": 1, "permissions": ["add_asindohdaily"]}
```

For Django's auto-generated model permissions the grouping is degenerate: each becomes its
own one-member "module". The app's *real* permission modules are the dotted strings visible
in `account me` — `admin.access`, `admin.dispatch.manage`, `admin.platform.manage`,
`dispatch.view`, `platform.amazon.access`, and (crucially, by its absence)
`amazon.shipment_planning.view`. **If you want to answer "what can this person do?", read the
dotted permissions from `account me`, not the `module` column from `account permissions`.**
That column will produce a list ~130 items long that answers nothing.

### Trap 7 — "pincode-mapping" is mostly not a pincode mapping.

**Evidence (live payload, first 11 rows verbatim):** 5 of 11 have `"pincode": null`. The
non-null ones are real (`744105`, `744102`, `523201`). And the data is dirty in a way that
will bite a join:

```json
{"row_id":"3928","city":"CALICT",    "state":"ANDAMAN AND NICOBAR ISLANDS","pincode":null}
{"row_id":"894", "city":"CALICUT",   "state":"ANDAMAN AND NICOBAR ISLANDS","pincode":"744105"}
{"row_id":"2876","city":"PORT BLAIR","state":"ANDAMAN AND NICOBAR ISLANDS","pincode":null}
{"row_id":"2877","city":"PORTBLAIR", "state":"ANDAMAN AND NICOBAR ISLANDS","pincode":null}
```

`CALICT`/`CALICUT` and `PORT BLAIR`/`PORTBLAIR` are duplicate spellings; Calicut is in
Kerala, not the Andamans. So: 6,565 rows is a **city→state lookup with an optional pincode
attached**, carrying typos and at least one geographic error. **Describe it as
"city/state list (pincode where known)", never as "the pincode master".** An operator who
joins orders to this on `city` will silently drop the misspelled ones.

I did not measure what fraction of all 6,565 rows have a null pincode — I only saw one page.
**Unmeasured; do not quote a percentage.**

### Trap 8 — the upload log gives three different row counts for the same job, and the biggest one is not the file's.

**Evidence (live payload, upload_id 311, verbatim):**

```json
"row_count": 223,
"metadata": {"report_type":"APPOINTMENT","upload_source":"file",
             "rows_inserted_staging": 223, "rows_inserted_final": 0, "rows_updated_final": 360}
```

The file had **223** rows. Zero rows were inserted into the main table. **360** rows in the
main table were *updated*. So:

- `row_count` / `rows_inserted_staging` = how many rows came out of the file.
- `rows_inserted_final` = new rows created.
- `rows_updated_final` = existing rows touched — **and it can exceed the file's row count**,
  because one file row can update several main-table rows.

Three defensible answers to "how many rows did that upload load?": 223, 0, or 360. And the
detail endpoint adds a fourth vocabulary — `summary.total_rows`, `valid_rows`, `error_rows`,
`warning_rows`, `final_inserted_rows`. **The CLI must label which number it is printing.**
The one an operator usually means is `rows_updated_final + rows_inserted_final`.

Related: `main_table_name` is a **human label**, not a database table — observed values
`"Amazon PO"` (with a space and capitals) and `"appointment"`. Do not feed it to anything
expecting an identifier. The machine-readable field is `report_type`
(`AMAZON_PO`, `APPOINTMENT`).

### Trap 9 — `chatbot conversations` looks like it is scoped to the calling user, and I could not prove it.

**Evidence:** 5 rows came back with ids `1, 6, 7, 9, 13` — sparse, which is what you get when
a global table is filtered. Four of the five are titled `"New chat"` with `message_count: 0`,
and the one with content (id 13, title `"hi"`) reads as the probing operator's own session.

**But I only have one account's view, so I cannot prove the filter exists.** If it does not,
this endpoint exposes other people's chat history — and those chats contain business data
(the assistant's own greeting in id 13 offers *"How many liters were delivered this month?"*,
*"Blinkit purchase orders this week"*). **Flag for a human: log in as a second user and check
whether conversation id 13 is visible.** Until then, describe the command as "chat history"
without promising whose. Low stakes for the CLI, real stakes if it is not scoped.

### Trap 10 — `row_id` on two of the three uploader tables is a Postgres ctid. It is not an id and it will change.

**Evidence (live payloads):**

```
upload/master-sheet     "row_id": "(28,55)"     ← ctid: (page, tuple)
upload/ads-master       "row_id": "(0,24)"      ← ctid
upload/pincode-mapping  "row_id": "3928"        ← a plain integer
```

A ctid is a *physical* address — page number and slot. **It changes whenever the row is
updated or the table is vacuumed.** Two of the three uploader tables therefore have no
stable key exposed through the API; the third does.

Consequences: never persist a `row_id` from `master-sheet` or `ads-master`; never quote one
to a colleague as "row (28,55)"; and be aware that the excluded `/update` and `/delete`
write endpoints presumably take this thing as their target — which is a design worth a
human's attention, but not ours to touch (RULE 0).

### Trap 11 — quantity fields here are in **pieces (single bottles)**, and `case_pack` is not a multiplier you should apply.

`master products` returns `case_pack: 1` for the Amazon glass-bottle rows whose
`sku_sap_name` reads `"GLASS BOTTLE 200 MLS APPLE 12 PCS"` and
`"GLASS BOTTLE 200 MLS GINGER ALE SUGAR FREE 6 PCS"`. **The "12 PCS" / "6 PCS" in the item
name and the `case_pack` field disagree, and `case_pack` is the one that describes how this
channel actually sells it.** This is the live-data confirmation of JIVO's standing
correction **C-0001**: quantities are in pieces, the "N PCS" in an item name is carton
configuration only, and multiplying by it inflates volume.

Applies directly to the notification fields too: `units_sold`, `soh_units`, `drr_units` are
**pieces**; `ltr_sold`, `soh_ltr`, `drr_ltr` are **litres**. For oils, litres × 0.91 gives
kg if a tonnage figure is wanted. **State the unit on every quantity this domain returns.**
`tax_rate` is a **fraction** (`0.05`), not a percentage — printing it raw next to a `%` sign
would show "0.05%".

### Trap 12 — `doh` can be negative, and it is not `soh ÷ drr`.

**Evidence (live payload, notification 3707, verbatim):**

```json
"soh_units": 0.0, "soh_ltr": 0.0, "drr_units": 0.0741, "drr_ltr": 0.037,
"doh": -2.0, "threshold": 5.0, "severity": "critical"
```

`0.0 ÷ 0.0741 = 0`, not `-2.0`. **So `doh` is not stock-on-hand divided by daily run rate,
and I could not determine how it is computed.** It goes negative, which usually means
oversold or a negative stock position, but that is my reading, not something I verified.
**Do not put a formula for `doh` in the CLI help.** Say "days of cover as the app computes
it; can be negative", and point at `soh_*` / `drr_*` for the raw inputs.

Also in the same row: `format: "AMAZON"` and `platform_slug: "amazon"` are the same fact
twice, and `read` and `is_read` are the same boolean twice. Pick one of each and say so.

### Trap 13 — the notification LIST wraps in `notifications` (plural); the DETAIL wraps in `notification` (singular).

**Evidence:** list → `{"notifications": [...], "unread_count": …, "count": 91}`;
detail → `{"notification": {...}}`. A spec that sets `response_path: notifications` for both
gets nothing back from the detail command. Same trap shape on uploads:
list → `{"results": [...]}`, detail → `{"upload": {...}, "summary": {...}}`.
And `chatbot conversations` is a **bare array** with no envelope at all, unlike every other
list in this domain.

### Trap 14 — the UI refuses to list the uploader tables without a filter. The API does not.

**Evidence (SPA source, `MasterSheetManager-CWEDZOOq.js`):**

```js
if(!searchTerm && !format && !…){ … setMsg({type:`error`, text:`Enter a search term or select a format to load rows.`}); return }
… await l.api.list({search: e, format_name: g, page_size: 50})
```

The guard is **client-side only** — my bare probe with no params returned rows from all
three tables. So the CLI can do something the UI will not let you do: dump the first page of
the whole master sheet. That is a feature, not a bug, but it means CLI output and UI output
will not match for anyone comparing them.

---

## 4. Recommended spec entries

Response types are taken from `live_response.top_type` on the real payload.

| # | command | method + path | params | response |
|---|---|---|---|---|
| 1 | **account me** | GET `/api/auth/me` | none | `object` (`user`) |
| 2 | **account permissions** | GET `/api/auth/permissions` | none | `object` (`permissions[]`) |
| 3 | `account feature-flags` **(new)** | GET `/api/auth/feature-flags` | none | `object` (`flags`); observed keys `uploader`, `game_play` (bool) |
| 4 | **master products** | GET `/api/master/products` | `page` (int), `page_size` (int), `search` (string) — *`search` is carried from the v0.1.0 spec; I could not confirm it from a live 200 or from the SPA. Carried forward unverified.* | `object`, `response_path: results` |
| 5 | **master fcs** | GET `/api/master/fcs` | `page` (int), `page_size` (int) | `object`, `response_path: results` |
| 6 | **notifications list** | GET `/api/notifications` | **add** `active_only` (bool — SPA sends `true`) and `limit` (int — SPA sends `200`); both verbatim SPA source, neither in v0.1.0 | `object` (`notifications`, `unread_count`, `count`) |
| 7 | **notifications get** | GET `/api/notifications/{id}` | `id` (string, req, positional) — verified with real id `3707` | `object`, wrapper key is **`notification`** singular |
| 8 | **notifications inventory-doh** | GET `/api/notifications/inventory-doh/{id}` | `id` (string, req, positional) — the id is a **notification id**; every list row's `link` field spells the URL out | **unverified** — carry v0.1.0's `object` |
| 9 | **upload master-sheet** | GET `/api/upload/master-sheet` | `page` (int), `page_size` (int, SPA sends 50), **add** `search` (string) and `format_name` (string) — both verbatim SPA source | `object`, `response_path: rows` (also returns `columns`, `total`) |
| 10 | **upload ads-master** | GET `/api/upload/ads-master` | same four as #9; `format_name` meaningful because the table has a `format` column | `object`, `response_path: rows` |
| 11 | **upload pincode-mapping** | GET `/api/upload/pincode-mapping` | `page`, `page_size`, `search`; **`format_name` is almost certainly meaningless here** — the table has no `format` column (columns are `city`, `state`, `pincode`). *Inferred; not tested.* | `object`, `response_path: rows` |
| 12 | **uploads list** | GET `/api/uploads` | `page` (int), `page_size` (int) | `object`, `response_path: results` |
| 13 | **uploads get** | GET `/api/uploads/{id}` | `id` (string, req, positional) — verified with real id `311` | `object` (`upload` + `summary`) |
| 14 | **chatbot health** | GET `/api/chatbot/health` | none | `object` (`ok`, `engine`) |
| 15 | **chatbot conversations** | GET `/api/chatbot/conversations` | none | **`array`** — the only bare array in this domain; do not set a `response_path` |
| 16 | **chatbot conversation** | GET `/api/chatbot/conversations/{id}` | `id` (string, req, positional) — verified with real id `13` | `object` (`messages[]`) |

**Group descriptions** — v0.1.0's are fine except `upload`, which I would sharpen because
"reference data" undersells the pincode trap:

- `account` — *"Authenticated account: current user, permissions and feature flags"* (extended for the new command)
- `master` — keep: *"Master data: product catalogue and fulfilment centres"*
- `notifications` — keep: *"Read-only notifications with unread count"*
- `upload` — suggest: *"Read-only views of the uploader's editable tables (master sheet, ads master, city/state list). Same 907 rows as `master products`, with more columns."*
- `uploads` — keep: *"Upload job history (read-only)"*
- `chatbot` — keep: *"Read-only access to the ecom app's built-in assistant (health + conversation history)"*

### The authentication carve-out (not business writes)

`POST /api/auth/login` and `POST /api/auth/refresh` mint and rotate a JWT. **They create no
business data** — no row in any operational table, nothing another operator can see, nothing
that affects a number on a dashboard. They are the CLI's authentication carve-out and are
already implemented by hand as `auth login` (`ecom-cli/internal/cli/jivo_login.go:115`
posts to `/api/auth/login`).

Two notes for whoever regenerates:

1. **Neither path is in this bundle** — the harvest's probe script deliberately skips
   `/login`, `/logout`, `/change-password`, `/refresh`, `/token/refresh`
   (`probe/probe.py` lines 37-38), and the reconciler produced no entry for them. Their
   absence here is not evidence they do not exist.
2. **`/api/auth/token/refresh` does NOT exist (404). The correct path is
   `/api/auth/refresh`.** The shipped CLI currently implements login only and tells the
   operator to re-run `auth login` when the token expires; a refresh command would be a
   genuine improvement and it should use `/api/auth/refresh`.

**These stay hand-authored. They must not be generated into the spec as ordinary endpoints**
— a generator that sees `POST` will either refuse them under RULE 0 or, worse, expose them
as generic write commands.

---

## 5. Exclusions

**21 in-bundle exclusions + 4 found outside the bundle.** Every one is a **write**. None is
dead — 22 of the 37 bundle rows are `UNPROBED` precisely because the probe is GET-only and
these are POSTs. Reporting any of them as dead would be wrong.

### In this bundle (21)

| # | endpoint | verb | reason |
|---|---|---|---|
| 1 | `/api/auth/change-password` | POST | **Write, and a credential change.** Changes a user's password. RULE 0. |
| 2 | `/api/auth/feature-flags/update` | POST | **Write, app-wide blast radius.** Toggles feature flags (`uploader`, `game_play`) for the application, not just the caller. RULE 0. |
| 3 | `/api/chatbot/message` | POST | **Write.** Creates a conversation and a message row; the assistant then runs queries and can generate files. RULE 0. |
| 4 | `/api/notifications/mark-all-read` | POST | **Write.** Marks every alert read — destroys the unread signal for whoever relies on it. RULE 0. |
| 5 | `/api/notifications/{id}/mark-read` | POST | **Write.** Same, for one alert. RULE 0. |
| 6 | `/api/upload/master-sheet/add` | POST | **Write.** Inserts a product-master row. RULE 0. |
| 7 | `/api/upload/master-sheet/update` | POST | **Write.** Edits a product-master row. RULE 0. |
| 8 | `/api/upload/master-sheet/delete` | POST | **Write, destructive.** Deletes a product-master row — every dashboard downstream depends on this table. RULE 0. |
| 9 | `/api/upload/master-sheet/bulk-upsert` | POST | **Write, bulk.** Body `{rows}`. RULE 0. |
| 10 | `/api/upload/master-sheet/preview` | POST | **Write-shaped.** Named "preview" and it may well be side-effect-free, **but it is a POST that takes `{rows}` and we have not verified it writes nothing** — and the sibling factory project learned this exact lesson the hard way (a GET on `/marketplace/settings/` created rows). Excluded until a human confirms. |
| 11 | `/api/upload/ads-master/add` | POST | **Write.** RULE 0. |
| 12 | `/api/upload/ads-master/update` | POST | **Write.** RULE 0. |
| 13 | `/api/upload/ads-master/delete` | POST | **Write, destructive.** RULE 0. |
| 14 | `/api/upload/ads-master/bulk-upsert` | POST | **Write, bulk.** RULE 0. |
| 15 | `/api/upload/ads-master/preview` | POST | **Write-shaped**, same reasoning as #10. |
| 16 | `/api/upload/pincode-mapping/add` | POST | **Write.** RULE 0. |
| 17 | `/api/upload/pincode-mapping/update` | POST | **Write.** RULE 0. |
| 18 | `/api/upload/pincode-mapping/delete` | POST | **Write, destructive.** RULE 0. |
| 19 | `/api/upload/pincode-mapping/bulk-upsert` | POST | **Write, bulk.** RULE 0. |
| 20 | `/api/upload/pincode-mapping/preview` | POST | **Write-shaped**, same reasoning as #10. |
| 21 | `/api/upload/batch` | POST | **Write, and the most dangerous endpoint in this bundle. The target table is caller-supplied.** Verbatim from two independent call sites: `shipmentAPI` sends `{table:'appointment_commit', unique_key:'appointment_id', upsert:true, data}`; `uploaderUtils` sends `{table, data, unique_key, upsert, expected_platform_format?, source_platform_format?}`. This is a generic "upsert arbitrary rows into a named table" endpoint. **It must be on the denylist by name, and it must never be reachable through any generic/passthrough command.** RULE 0. |

### Found outside this bundle (4) — include them so the denylist is complete

| # | endpoint | verb | reason |
|---|---|---|---|
| 22 | `/api/upload/delete-by-date` | POST | **Destructive bulk delete. Never publish, under any circumstance.** Confirmed in `bundle/uploaderUtils-D0yunz1d.js`, body verbatim: `{table, date_column, from_date, to_date, end_date_column?}`. It deletes every row from a **caller-named table** over a **caller-named date range**. One wrong `to_date` erases a month of a platform's data. This and #21 live in the same shared module and are the two highest-risk routes in the whole ecom app. |
| 23 | `/api/upload/fk-grocery-master` | POST | **Write.** Flipkart grocery master upsert. Confirmed in `UploadHub-CFeNTXbc.js` and `FkGroceryUploader-qAJP3aLc.js`, body `{data, upsert}`. RULE 0. |
| 24 | `/api/upload/flipkart-grocery/reprocess` | POST | **Write.** Re-runs enrichment over already-stored rows — rewrites existing data in place. Confirmed in `FkGroceryUploader-qAJP3aLc.js`. RULE 0. |
| 25 | `DELETE /api/chatbot/conversations/{id}` | DELETE | **Destructive.** Confirmed in `api-De44ElJm.js` (`deleteConversation`). The bundle records this path as GET-only because the delete is issued through a raw `fetch` the harvest lens did not attribute. **The GET is publishable (`chatbot conversation`); the DELETE must be blocked** — and because they share a path, this needs the same method-pinning treatment as the shipment domain's `shipments/{id}`. |

### Also a method restriction, not an exclusion

`/api/uploads` is published **for GET only**. Its POST is the app's main data-ingest route —
a multipart upload with `report_type`, `file`, `pasted_data`, `original_file_name`,
`uploaded_by`, `reprocess` (verbatim from `api-De44ElJm.js`), wrapped in a 3-attempt retry
loop. The bundle's `client_methods` for `/api/uploads` reads `["GET","POST"]`, so a
path-keyed generator will find the POST. **Pin the method.**

---

## Confidence summary

| claim | confidence | what would settle it |
|---|---|---|
| The 15 LIVE endpoints exist, are readable, and the fields I listed are real | **~99%** | Read from live 200 payloads captured in `probe/probe-run1.jsonl` and `probe/probe-params.jsonl`. |
| Row counts 907 / 99 / 6,565 / 187 / 907 / 19 / 91 | **~97%** | They are the server's own `count`/`total`. Residual risk: the totals may themselves be filtered (see the `active_only` issue on notifications). |
| Default page size is 50 for `master`/`uploads` and smaller for `/api/upload/*` | **~60%, inferred** | Arithmetic on byte sizes plus `page_size: 50` observed on *other* endpoints. The actual values sit past the probe's sample cut. One rerun printing the full envelope settles it. |
| `master products` and `upload master-sheet` are the same table | **~93%** | Identical count and byte-identical overlapping fields on the first rows. Not proven for all 907. |
| `row_id` is a Postgres ctid on two of three uploader tables | **~95%** | `"(28,55)"` / `"(0,24)"` is unmistakably ctid syntax; `pincode-mapping`'s `"3928"` is not. |
| `doh` is not `soh ÷ drr` | **~95%** | The observed row's arithmetic does not work. **How it *is* computed: I don't know, and I did not check the backend.** |
| `chatbot conversations` is scoped to the calling user | **~70%** | Sparse ids and the content pattern. **Needs a second account to confirm — flagged.** |
| All 25 excluded endpoints are writes | **~97%** | 21 have POST/DELETE as their only observed verb in the SPA; 4 were read verbatim out of the bundle with their request bodies. The three `/preview` routes are the soft ones — plausibly read-only, deliberately excluded anyway. |
| `/api/auth/token/refresh` is 404 and `/api/auth/refresh` is correct | **~90%** | Reported by the harvest lens, not re-verified by me in this session — the probe script skips both paths by design. |
