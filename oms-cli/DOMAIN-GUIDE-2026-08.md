# OMS — what each domain means, and the traps

`oms-pp-cli` is a **read-only** window into JIVO's Order Management System at
`oms.jivo.in`. 108 GET endpoints across 10 resources. Nothing in it can write.

This is the document to read before you answer a question with an OMS number.
Everything here was measured against the live API on 2026-08-04; where a claim
is unverified it says so.

---

## The one rule that will bite you first: `branch`

Every `/api/hana/` endpoint requires `--branch`, and it selects **a different
SAP company database**:

| `--branch` | SAP company |
|---|---|
| `OIL` | JIVO_OIL_HANADB |
| `BEVERAGE` | JIVO_BEVERAGES_HANADB |

There is **no MART branch**. OMS's HANA layer cannot reach JIVO Mart.

Why it matters more than it looks:

- The same `CardCode` is often a **different party** in each company. 298 of the
  1,165 shared codes differ (e.g. `CUSTA001041` is HIMJYOTI TRADERS in Oil and
  RAKESH KUMAR in Beverages). 117 of 328 shared FG item codes likewise.
- **Never join Oil data to Beverages data on a code.** Never quote a HANA figure
  without naming its branch.

`branch` is **not** the same enum as `category`, which appears elsewhere in the
API:

| param | values | used by |
|---|---|---|
| `branch` | `OIL`, `BEVERAGE` | `hana *`, `service-layer` |
| `category` | `OIL`, `BEVERAGES`, `MART` | `sap party-categories`, `account *` |

Singular vs plural, and MART exists in only one of them. Mixing them up returns
a plausible wrong answer rather than an error.

---

## The domains

### `account` — who you are, and the reference data everything else keys on

`account profile` is the health check and it explains most surprises: your role,
company, main groups, states, category and page permissions. If another command
returns zero rows or a 403, look here first.

The reference tables are the ones you will use constantly:

- `account categories` — the 3 SAP companies (OIL / BEVERAGES / MART). Field is
  `category`, not `name`.
- `account companies` — 2 legal entities. Jivo Wellness covers **both** OIL and
  BEVERAGES; nobody sits on Jivo Mart.
- `account roles` — 9 roles. The three `tracker_*` roles are a **separate grant**
  that an `admin` does not inherit.
- `account main-groups` — 27 sales channels. ⚠ `CALL CENTER` (id 8) and
  `CALL CENTRE` (id 28) are both live — a duplicate that will split any report
  grouped on channel.
- `account states` — 27 territories using **JIVO's own codes, not ISO**:
  Bihar `BH`, Kerala `KR`, Goa `GO`, Telangana `TE`, Uttarakhand `UK`,
  Odisha `OD`. Do not map them with an ISO table.

**Trap:** `account user-parties --category BEVERAGES` silently ignores the
filter and returns the OIL rows. The identical parameter works correctly on
`account party-products`. A silently-dropped filter is worse than a rejected
one.

### `orders` — the sales-order lifecycle

The spine of OMS. Orders move through 11 statuses (`orders status` lists them)
and a configurable approval flow (`orders flow-config`, `orders
party-flow-config`).

**`orders list` is not the order book.** Bare, it returns 263 of 2,163 orders.
See MIGRATION for the three filter traps (`--status` is comma-separated and has
11 values; `--billing` discards `--status`; `--approval-pending` alone does
nothing).

`orders detail <id>` is the full order — header, line items, addresses and rate
approvals. Its `sap_doc_number` is **`null` on every order**, including ones
that provably have SAP documents; use `quotations overview` for that instead.

`orders parties` / `products` / `staff-products` returning `[]` is an
**assignment** fact, not an empty system: the calling user has no parties
assigned. `account user-parties <your-id>` will confirm it. Being an admin does
not bypass the assignment table.

Sizes worth knowing: `orders stock-check` is 1,900 rows / 1.06 MB and
`orders dashboard-charts` is 268 KB, both unpaginated. Use `--compact` or
`--csv`.

### `quotations` — quotation overview and SAP status

`quotations overview` carries 1,898 rows with real SAP document numbers —
sampled `(doc_num, doc_entry)` pairs resolve exactly to SAP `OQUT` quotations.

⚠ `doc_num` is **not unique across companies**: the same number exists in Oil
and Beverages. Always pair it with the branch.

Every row currently reads `quotation_status: UNKNOWN`, because
`orders quotation-status` is broken upstream (it returns HTTP 200 with
`success: false` and an arity error). That is a backend defect, not missing
data.

### `sap` — the SAP Business One mirror inside OMS

A synced copy of SAP master data: parties, products, addresses, branches, and
the sync log. Row counts match SAP HANA **exactly** at the same hour (parties
1172/1247/939 for Oil/Bev/Mart against `OCRD CardType='C'`), so the mirror is
trustworthy for master data.

**The mirror covers all three SAP companies. The transactional path does not.**
OMS raises orders only into Oil and Beverages: Mart `OQUT` has zero rows
all-time, and OMS's own `category_sales` has no MART row at all. This is the
mirror image of ecom, where the SAP layer is Mart-only (correction C-0008).

Traps:

- `sap addresses` is **35,722 rows / 11.8 MB** unpaginated. `--card-code` cuts it
  to ~7 KB.
- Filters are inconsistent: `category` filters `products` but is silently
  ignored on `parties`; `card_code` filters `addresses` but not `parties`. An
  ignored filter returns the full body with a 200.
- An **invalid** `category` returns 200 with an empty list, not a 400. Validate
  before you trust an empty result.
- `sap product-varieties` is `U_Sub_Group`, not `U_Variety` — despite the API
  shipping both key names for the same array. Per correction **C-0003**, segment
  on `U_TYPE` / `U_Sub_Group`, never on item names. `sap products --search` is
  item-name matching, which is exactly what C-0003 forbids.
- `sap quotation-log` records a sales **order** (`ORDR`), not a quotation,
  despite the name.
- 17 sync runs are stuck in `STARTED` forever and 72 of 851 failed; the mirror
  never deletes rows, so a deleted SAP party lingers.

### `hana` — live SAP HANA reads

19 commands, **all requiring `--branch`**. This is where live stock, customers,
batches and pricing come from.

Required params, quoted from the server's own error messages:

| command | needs |
|---|---|
| `all-customers`, `fg-items`, `freight-masters`, `open-parties`, `series`, `warehouse-details`, `vendor-states`, `state-chain`, `invoice-drafts` | `--branch` |
| `address`, `customer-details`, `so` | `--branch --card-code` |
| `inventory-details`, `product-so` | `--branch --item-code` |
| `batch-details` | `--branch --item-code --whs-code` |
| `item-price` | `--branch --item-code --price-list` |
| `salesperson-details` | `--branch --slp-code` |
| `next-doc-number` | `--branch --doc-type` |

Traps:

- **Quantities are in PIECES** (single bottles/pouches), per correction
  **C-0001**. The `20 PCS` in an item name is carton configuration; multiplying
  by it inflates volume ~20×.
- **`item-price` is useless in practice.** SAP price list 1 is empty in *both*
  companies (`MAX(Price) = 0`) and ~99.6% of parties are on it, so this returns
  0 or null for virtually every customer. JIVO's real rates are not in SAP
  pricing.
- `hana so` returns **open orders only** (one party: 55 open vs 668 closed).
- Two date formats in one domain — `batch-details` returns
  `2026-05-02T00:00:00`, `so` returns `2026-08-01 00:00:00`. Do not write one
  parser.
- A valid item/warehouse pair with no stock returns `[]` with a 200, not a 404.
- `next-doc-number` does **not** reserve a number (verified against the HANA
  series counters), but the number it returns is a placeholder — the lowest
  unlocked series, not what the invoice will actually get.
- `product-stock` and `product-so` are **broken upstream** (502 / 500).

### `invoices` — the review-and-approval queue

`invoices logs` is the spine: every invoice submitted for review, with
`so_number`, `party_name`, `total_amount`, `branch`, `warehouse`, `status`,
`sap_doc_num` and the full `invoice_payload`.

Status values: `PENDING`, `APPROVED`, `POSTED_TO_SAP`, `REJECTED`, `EDITED`,
`ERROR`, `CL_RAISED`.

⚠ **`--status ALL` returns zero rows.** `ALL` is a UI sentinel, not a server
value — omit the flag to get everything. And a *misspelled parameter name*
returns the full table with a 200, so a typo looks like success.

`invoices credit-limit-cards` carries per-customer `balance`, `debtLine` and
`creditLine` for 1,172 customers. Its `company` param takes `1` (Oil) or `2`
(Beverages) — a third numbering scheme for the same idea as `branch` and
`category`.

`invoices all` and `invoices skus-pending` are broken upstream.

### `legal` — FSSAI food-label compliance

Upload a pack's artwork PDF against an item; the backend converts pages to
images, reads the label and reports each statutory declaration as ok / missing /
mismatch with a confidence. Reads only here — the upload is a write and is not
wrapped. One product configured so far (Kachi Ghani Mustard Oil Pouch); the uom
and nutrition masters are still empty.

### `einvoice` — GST e-invoicing (reads only)

`einvoice health`, `companies` (the enrolled legal entities and their GSTINs),
`invoices` (with IRN status) and `logs` (generation attempts and failures — the
place to look when an e-invoice fails). Every IRN write — generate, cancel,
retry, e-way bill — is deliberately excluded.

### `tracker` — the invoice tracker

15 commands, and **all of them return HTTP 403** unless you hold a tracker
grant, which is separate from your OMS role. Two distinct gates:

- `"Tracker administration is restricted to tracker admins."` — `admin-stages`,
  `admin-tracker-users`, `admin-users`, `all-invoices`, `all-invoices-export`
- `"You do not have access to this tracker page."` — `alerts`, `invoices`,
  `lookups`, `my-queue`, `reports`, `stage-advanced`, `vendors`

They are published because the endpoints demonstrably exist — a bogus tracker
path returns 404 while these return 403, so the 403 is decisive evidence of
existence. **Their response shapes are marked UNVERIFIED**: they were read out
of the web app's own source because no credential available could produce a
payload. Treat field names as indicative until someone with a grant confirms
them.

`tracker invoice-jsap` is a cross-system read into JSAP (JIVO's separate
`jsap-cli` system); its `doc_entry` is the SAP B1 **draft** DocEntry.

⚠ The OMS web app shows every `admin` the tracker menu, and the server then
refuses every page in it. That is a live bug, not your setup.

---

## Cross-cutting

**Three different names for "which company".** `branch` (`OIL`/`BEVERAGE`),
`category` (`OIL`/`BEVERAGES`/`MART`), and `company` (`1`/`2`) all mean roughly
the same thing in different corners of this API, with different vocabularies and
different coverage. Check which one the command takes.

**A 0-row 200 is a data fact, not a scoping fact.** Several endpoints return `[]`
because *this user* has nothing assigned. Do not report it as "the system has
none".

**Everything is a Django trailing-slash route.** Every path ends in `/`.

**RULE 0 — this CLI is read-only.** OMS carries order creation, invoice posting
into SAP Business One, approvals, and GST IRN generation. None of them is
wrapped, and the MCP surface refuses non-GET methods by construction in both
execution paths. `auth login` is the sole exception: it exchanges credentials
for a session token and mutates no business data.

---

## Where the evidence is

- `research/API-FACTS-2026-08.md` — what was proven, and how
- `research/studies/` — one study per domain, plus three adversarial refutations
- `research/harvest/` — the endpoint inventory from four independent lenses
- `research/evidence/` — every probe response
- `research/FINDINGS-FOR-OMS-TEAM-2026-08-04.md` — the defects, with repros
