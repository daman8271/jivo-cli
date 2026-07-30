# SAP GROUND TRUTH — what SAP actually holds, and what it does not

**Probe:** `sap-surface` · **Run:** 2026-07-30 ~02:30–03:10 IST · **Agent:** sapmap
**Purpose:** the reference other agents cite when they need to know what SAP exposes, so an
`N` (native, non-SAP) ruling can be made or refuted with evidence instead of vibes.

> **Read the negatives first.** If a domain appears in §1, no app can be an "M" (mirror) for it,
> because there is nothing in SAP to mirror. That is the highest-value section of this file.

---

## 0. ACCESS — CORRECTIONS TO THE LAUNCH BRIEFING (read this before you query anything)

Two corrections to what the fleet was told at launch. Both are live-verified.

### 0.1 `hana-sql` needs `-env connections/hana-tunnel.env` — the default env points at a dead host

`connections/hana.env` has `HANA_HOST=103.89.45.192 / HANA_PORT=30015` — the **direct** box address,
which is IP-whitelisted to the office and **hangs from home** (my first call timed out at 90s).
The tunnel config is a *separate* file.

```bash
cd /Users/damanpreetsingh/jivo-cli
./hana-sql/hana-sql -env connections/hana-tunnel.env "SELECT CURRENT_USER FROM DUMMY"
# → ZIA        (verified live, 2026-07-30)
```
`hana-tunnel.env` = `127.0.0.1:13015`, which is the `ssh -L` tunnel that is currently up
(`ssh` PID 50628 listening on 13015). **If your HANA query hangs, this is why.**

### 0.2 The SAP Service Layer IS REACHABLE — the briefing said it was down. It is not.

`sapb1 doctor` fails against the configured host, but that is only the *direct* route.
A second SSH tunnel is already up on **127.0.0.1:15000 → SAP box :50000** (`ssh` PID 52631).

```bash
cd /Users/damanpreetsingh/jivo-cli/sap-b1/cli
SAPB1_HOST=localhost SAPB1_PORT=15000 ./sapb1 doctor
# ✓ configuration  ✓ network  ✓ login — connected to JIVO_OIL_HANADB as manager
SAPB1_HOST=localhost SAPB1_PORT=15000 ./sapb1 query BusinessPartners --count   # → 3390
```
Also note: `sapb1` reads `.env` **from the current directory**, not from the binary's directory
(README claims otherwise — README is wrong). Running `./sap-b1/cli/sapb1 doctor` from the repo root
gives a bogus "missing config" error. `cd sap-b1/cli` first.

### 0.3 The Service Layer is a *thin façade over the same HANA tables* — not a second store

Live, same minute, both doors, Oil company:

| Entity (Service Layer) | SL `--count` | HANA table | HANA `RECORD_COUNT` | Match |
|---|---:|---|---:|---|
| BusinessPartners | 3,390 | `OCRD` | 3,390 | exact |
| Invoices | 30,477 | `OINV` | 30,477 | exact |
| Orders | 14,736 | `ORDR` | 14,736 | exact |
| Items | 2,269 | `OITM` | 2,269 | exact |
| PurchaseInvoices | 15,934 | `OPCH` | 15,934 | exact |

**Consequence for lineage:** "is it in SAP?" is ONE question, not two. There is no lag, no
subset, no separate SL store. HANA SQL and the Service Layer are interchangeable for existence
checks; use HANA for aggregates (`SUM`/`GROUP BY` server-side), SL for typed field names.

---

## 1. WHAT SAP DOES **NOT** HOLD — the candidate `N` buckets

Every row below is a live `RECORD_COUNT` from `M_TABLES` across **all three** company schemas.
Zero in all three companies. These modules are installed (the tables exist, the Service Layer
answers GETs) but **JIVO never uses them**. An endpoint that returns 200-with-0-rows is not
coverage.

| SAP table | Module SAP intended it for | OIL | MART | BEV | Which JIVO app owns this instead (hypothesis for other agents) |
|---|---|---:|---:|---:|---|
| `OCLG` | **Activities / calls / meetings / follow-ups (CRM)** | **0** | **0** | **0** | JSAP tasks+tickets+MoMs; DSR field visits |
| `OOPR` | **Sales opportunities / pipeline** | **0** | **0** | **0** | nothing in SAP at all |
| `OSCL` | **Service calls** | **0** | **0** | **0** | `CRM` Postgres DB (`complaints_complaint`) |
| `OCTR` | **Service contracts** | **0** | **0** | **0** | — |
| `OPRQ` | **Purchase requests / requisitions** | **0** | **0** | **0** | JSAP / control-panel approval flow, `po_db` |
| `OPRJ` | **Projects** | **0** | **0** | **0** | — |
| `OPMG` | Project management | **0** | **0** | **0** | — |
| `OSRN` | Serial numbers | **0** | **0** | **0** | Factory barcode tables |
| `ODPI`/`ODPO`/`ODPS` | Down payments | **0** | **0** | **0** | — |
| `OINS` | Customer equipment cards | **0** | **0** | **0** | — |
| `OQUE` | Queues | **0** | **0** | **0** | — |
| `ORCM`/`ORCR` | Recurring transactions | **0** | **0** | **0** | — |
| `OCLS`/`OBOT`/`OWKO`/`OVTG`/`OSCN` | misc modules | **0** | **0** | **0** | — |

### 1.1 HR / payroll / attendance — SAP holds the money, NOT the people

- `OHEM` (employee master): **17 rows in Oil, 1 in Mart, 15 in Bev.** Sampled live: 17 names,
  `startDate` NULL, `status` NULL on every row. It is a stub used to attach a few sales/owner
  users to documents — **not an HR master.** JIVO's real headcount is in TankhaPay (297-command CLI).
- There is **no attendance table, no payroll-run table, no leave table** anywhere in the SAP schema.
- What SAP *does* hold is the **aggregate GL side**: `SALARY EXPENSE` (5630001), `SALARY PAYABLE`
  + a payable account per month (2161001…2161012), `EPF PAYABLE`, `EPF ADMIN CHARGES`,
  `TDS ON SALARY`, `GRATUITY`, `PROVISION FOR GRATUITY`, `EMPLOYEE BONUS PAYABLE`, and even a
  handful of **named-person salary accounts** (`2163001 GURPREET SINGH SALARY`).
- **Ruling guidance for the TankhaPay agent:** employee-level attendance/salary/payout detail is
  `N` or at most `F`-with-total-loss-of-detail. SAP receives a **monthly journal total**, never a
  person-day. Do not call TankhaPay an `M`.

### 1.2 Field-sales hierarchy — the fields exist and are **100% empty**

`OCRD` carries a full sales-org UDF block from the `UNE_` add-on:
`U_UNE_ASM`, `U_UNE_RSM`, `U_UNE_SO`, `U_UNE_SR`, `U_UNE_ZONE`, `U_UNE_AREA`, `U_UNE_SBAR`,
`U_UNE_BRCH`, `U_UNE_CITY`, `U_UNE_STAT`, `U_UNE_CTRY`, `U_UNE_PRMT`, `U_UNE_CNHD`, `U_UNE_GRP1-3`.

Live, Oil, 3,390 business partners:
```sql
SUM(CASE WHEN IFNULL("U_UNE_ASM",'')<>'' THEN 1 ELSE 0 END)   -- 0
SUM(CASE WHEN IFNULL("U_UNE_ZONE",'')<>'' THEN 1 ELSE 0 END)  -- 0
SUM(CASE WHEN IFNULL("U_UNE_STAT",'')<>'' THEN 1 ELSE 0 END)  -- 0
```
**Zero non-blank on every one.** This is a trap: a schema-only agent grepping SAP columns will
see "SAP has ASM/RSM/territory" and wrongly rule DSR an `M`. It does not. **SAP holds no
salesman→retailer→beat hierarchy.** DSR (`DSR_V6`, SQL Server, separate box) is `N` on that.

### 1.3 The historical floor — SAP's books start **September/October 2024**

| Table | rows (Oil) | earliest date | latest date |
|---|---:|---|---|
| `OJDT` journal | 132,621 | **2024-08-01** | 2026-07-29 |
| `OINV` A/R invoice | 30,477 | **2024-09-30** | 2026-07-29 |
| `ORDR` sales order | 14,736 | **2024-10-01** | 2026-07-29 |
| `OPCH` A/P invoice | 15,934 | **2024-09-30** | 2026-07-25 |
| `OWOR` production order | 7,858 | **2024-10-01** | 2026-07-29 |
| `ODLN` delivery | 2,830 | 2024-10-04 | 2026-07-19 |
| `ORCT` incoming payment | 13,861 | 2024-09-30 | 2026-07-29 |

Posting periods (`OFPR`) are defined from FY2425-01 (2024-04-01) but the first real documents are
Sep/Oct 2024, with the 2024-08-01 journal entries being migration/opening balances.
**SAP went live ~Oct 2024.** Any app holding pre-Oct-2024 history holds data SAP will never have,
*even for domains SAP otherwise covers.* Check the app's own earliest date before ruling `M`.

### 1.4 No SAP mirror exists in the Postgres cluster

`postsql dbs` → 15 databases, all application DBs (`factory_flow`, `order_management`, `jivo_ecom`,
`Ecommerce`, `CRM`, `po_db`, `task`, `jivo_site`, `fs`, `test_*`, `oms_backup`, `OMS_TEST`, `postgres`).
**None is a HANA replica.** The HANA→Postgres mirror discussed in `chats/2026-07-30.md` is a *plan*,
not a running system. Anything you find in Postgres got there by an application writing it, not by
replication.

Exception worth knowing (this is a *pull-cache*, not replication) — `order_management`:

| Postgres table | rows | SAP counterpart | SAP rows (Oil) |
|---|---:|---|---:|
| `sap_parties` | 3,350 | `OCRD` | 3,390 |
| `sap_party_addresses` | 35,664 | `CRD1` | — |
| `sap_products` | 4,155 | `OITM` | 2,269 (Oil only; likely multi-company) |
| `sap_sync_logs` | 310 | — | (log of the pull) |
| `sap_sync_schedules` | — | — | (cron for the pull) |

`sap_parties` at 3,350 vs SAP's 3,390 is a **cached copy running 40 rows behind** → the OMS party
list is `M` (mirror), with staleness. Confidence 80 — I read counts, not the sync code; the OMS
agent should read the sync job to confirm direction (SAP→PG, not PG→SAP).

---

## 2. WHAT SAP **DOES** HOLD — populated, live, per company

`SELECT TABLE_NAME, RECORD_COUNT FROM M_TABLES WHERE SCHEMA_NAME='...'`, run 2026-07-30.

| Domain | SAP tables | OIL | MART | BEV |
|---|---|---:|---:|---:|
| **Sales A/R** | `OQUT` quotation | 1,691 | 0 | 733 |
| | `ORDR` sales order | 14,736 | 7,374 | 5,275 |
| | `ODLN` delivery | 2,830 | 6,084 | 303 |
| | `OINV` A/R invoice | 30,477 | 25,063 | 5,246 |
| | `ORIN` A/R credit note (returns) | 6,377 | 4,439 | 427 |
| | `ORDN` returns | 1,990 | 1,820 | 184 |
| **Purchasing** | `OPOR` purchase order | 4,191 | 2,131 | 1,113 |
| | `OPDN` GRPO | 11,248 | 3,023 | 4,533 |
| | `OPCH` A/P invoice | 15,934 | 4,569 | 3,068 |
| | `ORPC` A/P credit note | 1,530 | 759 | 231 |
| | `ORPD` goods return | 110 | 59 | 31 |
| | `OIPF` landed costs | 525 | 0 | 6 |
| **Inventory** | `OITM` item master | 2,269 | 1,349 | 2,192 |
| | `OITW` item-per-warehouse | 127,211 | 47,908 | 95,351 |
| | `OIGN` goods receipt | 8,065 | 74 | 1,436 |
| | `OIGE` goods issue | 7,939 | 72 | 1,364 |
| | `OWTR` stock transfer | 11,800 | 1,683 | 2,095 |
| | `OWTQ` transfer request | 1,289 | 1,104 | 58 |
| | `OBTN` batch numbers | 17,505 | 10,076 | 2,113 |
| | `OPKL` pick lists | 3,598 | 702 | 1,310 |
| | `OWHS` warehouses | 58 | 36 | 44 |
| **Production** | `OWOR` production order | 7,858 | **27** | 1,431 |
| | `OITT` bill of materials | 622 | 467 | 543 |
| | `ORSC` resources | 7 | 2 | 1 |
| **Finance** | `OJDT` journal entry | 132,621 | 62,817 | 22,531 |
| | `OACT` chart of accounts | 1,424 | 1,104 | 764 |
| | `ORCT` incoming payment | 13,861 | 11,122 | 3,872 |
| | `OVPM` vendor payment | 14,356 | 2,170 | 1,861 |
| | `OPRC` profit centres | 198 | 190 | 177 |
| | `OBGT` budget | 164 | 0 | 175 |
| **Partners** | `OCRD` business partners | 3,390 | 2,183 | 2,930 |
| | `OCPR` contact persons | 3,131 | 1,989 | 2,723 |
| | `OCRB` BP bank accounts | 1,903 | 868 | 1,340 |
| | `OSLP` sales employees | 155 | 51 | 99 |
| **Governance** | `OWDD` approval requests | **57,741** | 14,214 | 16,515 |
| | `OATC` attachments (header) | 76,062 | 30,759 | 19,044 |
| | `ATC1` attachment lines | 128,739 | 37,441 | 36,082 |
| | `ODRF` document drafts | 47,609 | 13,975 | 13,723 |
| | `OALR` alerts | 150,413 | 29,225 | 33,855 |
| | `OUSR` SAP users | 55 | 53 | 52 |

Notable shape facts:
- **Mart barely manufactures** (`OWOR` = 27) but **out-delivers Oil** (`ODLN` 6,084 vs 2,830). Mart
  is a distribution book; Oil is the factory book. Beverages is small on documents but has a
  near-Oil-sized item master (2,192).
- **Mart writes zero quotations and zero landed costs.**
- Physical volume: Oil = 69.1 M rows across 746 populated tables; Mart = 8.0 M / 617;
  Bev = 3.4 M / 659. The schemas have **3,111 / 3,046 / 3,087 tables defined** — so **~76% of every
  SAP schema is empty**. "The table exists in SAP" proves nothing.

### 2.1 SAP DOES hold an approval trail — this narrows the `F` bucket

`OWDD` = 57,741 approval requests in Oil alone, Oct-2024 → 29-Jul-2026, still live. By `ObjType`
(mapping is the standard SAP B1 object list — *inferred*, not read from a JIVO doc):

| ObjType | Standard meaning (inferred) | count (Oil) |
|---:|---|---:|
| 67 | Inventory / stock transfer | 17,250 |
| 18 | A/P invoice | 14,839 |
| 13 | A/R invoice | 10,008 |
| 20 | Goods receipt PO (GRPO) | 5,080 |
| 22 | Purchase order | 2,235 |
| 19 | A/P credit memo | 1,722 |
| 15 | Delivery | 1,655 |
| 14 | A/R credit memo | 1,525 |
| 46 | Outgoing payment | 1,442 |
| 16 | Returns | 1,206 |
| **1250000001** | **custom UDO** | **668** |
| 21 | Goods return | 96 |
| **17** | **Sales order** | **7** |

**Sales orders are essentially never approved inside SAP (7 requests in 22 months).** That is
consistent with sales orders arriving from OMS already approved — the pre-SAP approval trail for
*orders* lives in OMS/JSAP, and is `F`-material. But **purchase and inventory approvals DO live in
SAP** — before claiming JSAP/control-panel approvals are `N`, check whether they are the same
approval or a *second, earlier* one.

### 2.2 Marketplace / q-commerce counterparties ARE in SAP (as money, not as operations)

All the platforms exist as SAP business partners with live balances:

| SAP CardCode | CardName | Type |
|---|---|---|
| `VENDA000849` | BLINK COMMERCE PRIVATE LIMITED (Blinkit) | Vendor |
| `CUSTA000722` | KIRANAKART TECHNOLOGIES PVT LTD (Zepto) | Customer |
| `CUSTA000130` | SUPERMARKET GROCERY SUPPLIES PVT LTD (BigBasket) | Customer |
| `CUSTA000496` / `VENDA000396` | INNOVATIVE RETAIL CONCEPTS PVT LTD (BigBasket) | Cust + Vend |
| `VENDA000401` | AMAZON SELLER SERVICES PRIVATE LIMITED | Vendor |
| `VENDA001202` | AMAZON ADVERTISING A/R | Vendor |
| `CUSTA001075` | AMAZON RETAIL INDIA PRIVATE LIMITED | Customer |
| `VENDA000120` | FLIPKART INTERNET PVT LTD | Vendor |
| `VENDA000373` | RELIANCE RETAIL LIMITED JIOMART | Vendor |
| `VENDA000729` | BUNDL TECHNOLOGIES PRIVATE LTD (Swiggy) | Vendor |

BP split, Oil: 2,220 vendors (`S`) / 1,170 customers (`C`).

**So:** marketplace **invoices, credit notes and ledger balances** are in SAP (`M`/`F`-side).
Marketplace **listings, SOH/DOH, ads spend detail, DRR, appointments, scorecards, PO-line
fill-rate, offers, assortment** have **no SAP object of any kind** → those are `X`
(external, platform-originated). The presence of an Amazon *ledger* does not make ecom-cli an `M`.

---

## 3. CUSTOM EXTENSIONS — the `@` user tables and `U_` user fields

### 3.1 User-defined tables (UDTs). 5,572 UDFs across 278 tables; ~180 `@` tables.

Careful: `@A<NAME>` tables are SAP's **auto-generated archive/log twins** of `@<NAME>`, not separate
data. Read only the non-`A` ones.

**JIVO's own product taxonomy (this is real, JIVO-authored master data, and it is `M`-source
for anything downstream):**

| UDT | OIL | MART | BEV | What |
|---|---:|---:|---:|---|
| `@MAIN_GROUP` | 60 | 50 | 54 | top-level product group |
| `@ITEM_SUBGRP` | 51 | 51 | 69 | sub-group |
| `@ITEM_VARIETY` | 196 | 131 | 214 | variety |
| `@ITEM_SKU` | 50 | 35 | 17 | SKU class |
| `@BRAND` | 3 | 3 | 3 | brand |
| `@ITEM_UNIT` | 4 | 4 | 5 | unit |
| `@CHAIN` | 46 | 47 | 46 | **retail chain master** (modern trade) |
| `@QC_I` / `@QC_O` | 19 / 6 | 0 | 0 | tiny QC in/out — NOT the factory QC system |
| `@ZIA_DL_LIMIT` / `@ZIA_DL_OLIMIT` | 12 / 3 | 0 | 11 / 2 | delivery/credit limits (consultant-built) |
| `@BUDGET` / `@BUDGET1` | 1 | 0 | 0 | stub, unused |
| `@ZIA_ASSET_ISSUE_I/O` | **0** | — | — | asset-issue module built, **never used** |

**Third-party add-on tables (NOT JIVO data — statutory/e-compliance middleware):**
- `@UTL_*` — the **e-Way bill / e-Invoice** add-on. `@UTL_MDEXTH` 17,695 (Oil) / 8,972 (Mart) /
  4,608 (Bev); `@UTL_ST_EWAYDT` 1,333 / 2,560 / 279. **SAP therefore DOES hold e-Way bill and
  e-invoice records** — check this before ruling any logistics/e-way app `N`.
- `@UNE_*` — a sales/distribution add-on. `@UNE_USERSEL` 2,449/1,373/1,666 (user selections),
  `@UNE_USERSELTAX` 884/528/43. Its **sales-hierarchy fields on `OCRD` are 100% empty** (§1.2) —
  the add-on is installed but its distribution module is not in use.

### 3.2 The `U_` fields that matter for cross-system joins

`OITM` (items) — 30 UDFs. Populated counts, Oil (2,269 items):

| Field | non-null | What it is / why lineage cares |
|---|---:|---|
| `U_TYPE` | 2,234 | product type — **use this, not name matching** (see memory `sap-sales-analysis-traps`) |
| `U_Sub_Group` (label "VARIETY") | 2,269 | full coverage |
| `U_Variety` (label "SUBGROUP") | 2,269 | **labels are swapped vs field names — do not trust the name** |
| `U_Brand` | 2,269 | full coverage |
| `U_SKU` | 1,599 | |
| `U_MRP` | 542 | maximum retail price |
| **`U_Mart_ItemCode`** | **378** | **Oil-item → Mart-item cross-company bridge, inside SAP** |
| **`U_WG_ItemCode`** | **59** | bridge to an external "WG" system — mostly unpopulated |
| `U_JRID` | 6 | near-empty |
| others | `U_Gross_Weight`, `U_Net_Weight`, `U_Qty_In_PCS`, `U_PACK_TYPE`, `U_Packing_Type`, `U_Is_CSD`, `U_Index_No`, `U_Shelflife`, `U_Is_Plastic`, `U_P_WEIGHT`, `U_Tax_Rate`, `U_Rev_tax_Rate`, `U_GL_ACCT`, `U_ITEM_LOCK`, `U_IsLitre`, `U_FA_Type`, `U_CONSUMPTION_PER_DAY`, `U_UNE_TOTB`, `U_UNE_TOTL`, `U_UTL_ST_ISSERVICE` |

`OCRD` (business partners) — 40 UDFs. Populated counts, Oil (3,390 BPs):

| Field | non-blank | What |
|---|---:|---|
| `U_Main_Group` | 3,348 | party classification — near-total coverage |
| **`U_WG_CardCode`** | **2,405** | **bridge to the external "WG" system — 71% coverage.** Worth chasing: which app is "WG"? |
| `U_Chain` | 1,477 | retail chain (joins `@CHAIN`) |
| `U_Emp_Code` | 510 | **BP → employee link** (the "IMPREST vendor account" pattern in CLAUDE.md) |
| `U_Fssai`, `U_MSME`, `U_MSME_Type`, `U_MSME_BType`, `U_CATGCODE`, `U_CMDTCODE` | — | statutory codes |
| `U_ST_GRP1..11`, `U_UNE_*` | 0 | **all empty** (§1.2) |

Document headers (`OINV`, `ORDR`, `OPCH`, `OPOR`, `ODLN`, `ODRF`, `ADOC`, …) each carry a
**uniform 65-UDF block** — that is the add-on's e-invoice/e-way payload, not per-document JIVO
customisation. Do not read meaning into "OINV has 65 user fields".

---

## 4. THE REPO'S SAP ACCESS SURFACE (verified, not just documented)

### 4.1 `sapb1` CLI — Service Layer, read-only Go binary

`/Users/damanpreetsingh/jivo-cli/sap-b1/cli/sapb1`. Commands (from `--help`, live):
`auth` (login/status/logout) · `catalog` · `doctor` · `entities` · `fields` · `invoices` ·
`items` · `mcp` · `ops` · `orders` · `partners` · `query`.
Global flags: `--company --host --port --user --json --csv --insecure --timeout`.
`query` is the universal door: `sapb1 query <EntitySet> --filter --select --top --orderby --count --all`.
An MCP server (`sapb1 mcp`) exposes the same surface to Claude; the MCP tools
`mcp__sapb1__*` are registered in this session but hit the **direct** host, so they will fail
unless re-pointed at `localhost:15000`.

### 4.2 Catalogue counts — **all three doc claims VERIFIED exactly**

Prior work claimed 498 services / ~307 readable / ~140 with live data. I checked all three
independently and they are **correct, not approximate**:

| Claim | How I verified | Result |
|---|---|---|
| 498 services | `len(json.load(api-reference/catalog/services.json))` **and** `sapb1 entities` footer | **498** ✓ |
| 1,950 operations | summed `operations` in services.json | **1,950** ✓ |
| 307 readable | `sapb1 entities \| grep -c yes` **and** `readable: true` in 498 vault frontmatters | **307** ✓ (both agree) |
| 140 with live data | `rows_oil > 0` across 498 vault frontmatters | **140** ✓ |
| 498 vault notes | `ls vault/services/ \| wc -l` | **498** ✓ |

Caveat on the "140": it is **Oil-only** and it is a **cached** frontmatter value from 2026-07-23.
Mart and Beverages were censused only for the big 8. So "SAP has no data for X" based on the
census is an **Oil-only** statement — several entities are non-zero in Bev/Mart and zero in Oil
(e.g. `OBGT` budgets: Oil 164, Mart 0, Bev 175). **Always check all three schemas.** The
authoritative, current, all-three-companies source is `M_TABLES`, not the vault.

Also note the vault's 140 counts **Service-Layer entities**, while HANA has **746 populated tables**
in Oil. Different granularity — the SL exposes roughly a fifth of the populated tables. If an
entity is missing from the SL catalogue, that does **not** mean SAP lacks the data; check `M_TABLES`.

### 4.3 A 4th schema exists: `TEST_OIL_15122025`

3,112 tables — a **copy of the Oil company taken 2025-12-15**. Not one of the three production
books. Never quote figures from it; never let a "SAP has X" ruling rest on it.

### 4.4 Data volume (for the mirror discussion)

Oil 69.1 M rows / 746 populated tables · Mart 8.0 M / 617 · Bev 3.4 M / 659.
Attachments are **not** in the DB — `ATC1` (128,739 rows in Oil) is only a *registry*; the ~306k
files / ~105 GB live on the Windows box `JIVO-APP` (20.20.45.25) SMB shares
(`chats/2026-07-30.md`, evidence_type=doc, measured by a prior session).

---

## 5. CLAIMS THE REPO ALREADY MAKES ABOUT SAP — all `evidence_type=doc`, ALL UNVERIFIED

**There is no `*__SAP.md` connection doc anywhere in `connections/`.** The vault maps 15 CLI-to-CLI
pairs and zero CLI-to-SAP pairs. Every statement below is a doc assertion that some other agent
must confirm with code or live rows. Docs in this repo have been wrong before (README's `.env`
location, §0.2's "unreachable" Service Layer) — **do not let any of these outrank code.**

| # | Claim | Source | Bucket it implies | What would verify it |
|---:|---|---|---|---|
| C1 | EXIM exposes "SAP-sourced RM/FG masters" and "SAP Business One reference data for Jivo Wellness" | `VALUE_CHAIN.md:46`, `EXIM_HUB.md:12,21` | `M` for EXIM item/party reads | trace the EXIM endpoint to a SAP call or a cached table |
| C2 | EXIM `GET /sap_sync/open-grpos/` "may refresh from SAP" — **a GET with a write side-effect**; excluded from the safe surface | `VALUE_CHAIN.md:135`, `CONNECTIONS_MOC.md:112`, `EXIM_HUB.md:14,63` | — | **DO NOT CALL IT.** Read the source only. |
| C3 | OMS is "the order-to-SAP lens … invoices, dashboard metrics, and SAP transfer/log views" | `OMS_HUB.md:12`, `VALUE_CHAIN.md:56` | `F` for OMS orders | I already found `order_management.orders.sap_created` / `sap_doc_number`, `sales_orders_logs.sap_doc_entry/sap_doc_num` — strong `F` support |
| C4 | Ecom exposes a "SAP read layer": distributors by `CardCode`, distributor orders/invoices, item master, FG inventory, stock by warehouse, sales invoices; single-invoice route id is a SAP `DocEntry` | `ECOM__JSAP.md:31`, `ECOM_HUB.md:12` | `M` for that slice of ecom-cli **only** | confirm the ecom backend reads SAP vs. its own `jivo_ecom` DB |
| C5 | Ecom's SAP rows carry **no** company/database field — "no canonical company switch proven" | `ECOM__JSAP.md:32`, `ECOM_HUB.md:59` | — | a genuine blocker; any Oil/Mart/Bev attribution from ecom is unproven |
| C6 | JSAP backends = "JSAP application database **plus SAP HANA-backed reads**" | `JSAP_HUB.md:21` | mixed `M` + `N` | the single most important thing for another agent to split |
| C7 | JSAP `DocumentManagement` returns `databaseName`, `docEntry`, `docNum`, `cardCode` | `ECOM__JSAP.md:38` | `M` for that surface | |
| C8 | JSAP `GetLastBundleId?mode=update` **mutates despite being a GET** | `ECOM__JSAP.md:76` | — | **DO NOT CALL IT.** |
| C9 | Factory records SAP `item_code` / `FG####` values; `FG0000424` has **conflicting descriptions** between EXIM and a Factory sample | `VALUE_CHAIN.md:52`, `EXIM_HUB.md:41` | shared-key candidate, **not** proof of `M` | resolve the FG0000424 collision against `OITM` |
| C10 | Factory company id `2` = Mart, JSAP company id `2` = Beverage — **the numeric ids collide** | `FACTORY_HUB.md:61`, `CONNECTIONS_MOC.md:94` | — | live trap; never join on numeric company id |
| C11 | "No pair note proves that two APIs share a database, even when both read SAP" | `CONNECTIONS_MOC.md:107` | — | the repo's own honest disclaimer — inherit it |
| C12 | `product-identity` bridges 333 platform listings ↔ 1,906 Factory FG/FB/SL items | `CLI-HUB-README.md`, `README.md:23` | — | compare its item codes to `OITM` (2,269 in Oil) |

Postgres column names I found that **corroborate** the feeder claims (evidence_type=schema, live):
`factory_flow.barcode_dispatchsapsynclog` (request/response payload, attempt_no, status,
error_message) and `barcode_dispatchsession.sap_dispatch_status`; `order_management.orders.sap_created`
+ `sap_doc_number`, `sales_orders_logs.sap_doc_entry/num`, `sales_quotation_logs.sap_doc_entry/num`,
`credit_limit_logs.jsap_doc_id`; `jivo_ecom.amazon_po.sap_sku_code/sap_sku_name`;
`Ecommerce.Mapping_skumapping.sap_code/sap_name`, `Ecommerce.Amazon_purchaseorderlines.sap_code/name`;
`fs.quc.inspection_reports.sap_code`, `fs.quc.materials.sap_code`.
`CRM`, `po_db`, `task`, `jivo_site` contain **zero** SAP-named objects.

---

## 6. RULES OF THUMB FOR EVERY OTHER AGENT

1. **Existence in SAP is a two-part test.** The table/entity existing means nothing (76% of the
   SAP schema is empty). Ask `M_TABLES` for `RECORD_COUNT > 0` **in all three schemas**.
2. **A UDF existing means nothing either.** `OCRD.U_UNE_ASM` exists and is 0/3,390 populated.
   Count non-blank, not non-existent.
3. **Nothing before Oct 2024 is in SAP.** Check the app's earliest record before ruling `M`.
4. **SL and HANA are the same store.** Don't treat "the CLI reads the Service Layer" as a
   different source from "the app reads HANA".
5. **Aggregate ≠ mirror.** SAP holds monthly salary *totals* in the GL. That does not make
   TankhaPay a mirror. Same test applies to any app whose output reaches SAP as a journal line.
6. **`M` requires a mechanism, not a matching field name.** `sap_code` in a Postgres table proves
   a shared *namespace*, not a shared *source*. Find the sync job or the API call.
7. **Two forbidden calls** live in this repo: EXIM `GET /sap_sync/open-grpos/` and JSAP
   `GetLastBundleId?mode=update`. Both are GETs that write. Read the source, never execute.

## 7. WHAT I DID NOT CHECK (so nobody assumes I did)

- I did not read the source of any app backend (EXIM/Factory/OMS/Ecom/JSAP) — every ruling about
  *how* an app gets SAP data is left to the source-map agents. My scope was the SAP side.
- I did not verify the direction of the `order_management.sap_*` sync (I inferred SAP→PG from the
  row counts and the table names; the sync job itself is unread). Confidence 80.
- The `OWDD.ObjType` → document-type mapping in §2.1 is standard SAP B1 knowledge, **not** read
  from a JIVO source. The counts are live; the labels are inferred. Confidence 85 on the labels.
- Mart/Beverages were spot-checked on ~90 named tables, not exhaustively censused entity-by-entity.
- I did not touch DSR (SQL Server), TankhaPay, or the portal APIs.
- No write of any kind was issued. Every HANA statement was a `SELECT`; every Service Layer call
  was a GET plus the CLI's own Login.
