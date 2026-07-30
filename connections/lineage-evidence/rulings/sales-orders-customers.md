# FINAL RULINGS — domain: sales-orders-customers

Adjudicator: sales-orders-customers. Date: 2026-07-30. All SAP evidence is live SQL through
`./hana-sql/hana-sql -env connections/hana-tunnel.env` (127.0.0.1:13015). All DSR evidence is live
TDS SELECT through a freshly built `dsr` binary against `DSR_V6` @ 103.89.45.75:1433. All Postgres
evidence is live `./postsql/postsql`. Every statement was read-only.

---

## HEADLINE

**Three "orders" are three different things and only one of them is the commercial document.**

- An **OMS order** is a *pre-SAP* order raised by a salesman; it reaches SAP as a **Sales
  Quotation (OQUT)**, never as a sales order. A human in SAP then converts it. → **F**
- A **DSR "primary sale"** is *not* an order at all. Since 2026-05 it is a **hand-keyed,
  carton-level copy of a SAP A/R invoice that already exists**, carrying the SAP DocNum in
  `bill_number`. → **M** (this reverses the phase-1 ruling of N)
- A **SAP ORDR** is the real sales order. Everything else in the fleet either feeds it, copies
  it, or has nothing to do with it.

And the single most operationally urgent fact I found: **the OMS→SAP quotation feed has written
nothing to SAP since 2026-07-23 (Oil) / 2026-07-24 (Beverages)** — six days of silence against a
prior run-rate of 8–30/day — while SAP sales orders continue at 32–46/day, keyed by hand.

---

## 1. THE CENTRAL TENSION, RESOLVED

### 1a. How to tell an OMS order, a DSR order and a SAP order apart (the operator test)

| | OMS order | DSR "primary sale" | SAP sales order |
|---|---|---|---|
| Identifier | `ORD-YYYYMMDD-NNNN` (string) | DSR row `id`, no doc number of its own | `ORDR.DocNum` e.g. `1726076913` |
| Lands in SAP as | `OQUT` quotation (DocEntry/DocNum read back) | nothing — it is a *copy of* `OINV` | itself |
| Unit | pieces (per OMS line: pcs/boxes/ltrs) | **cartons/cases** | **pieces/bottles** |
| Value | yes (UnitPrice per line) | **none** — `price` is 0 on 12,553 of 12,560 rows | yes |
| Who keys it | field salesman in the OMS app | a back-office human (`uploaded_by` = "NANCY BIJJI") *after* SAP billed | SAP user (MANSI/HARPREET/SUMIT/manager) |
| Direction | OMS → SAP | **SAP → DSR** | — |
| Join key | `sales_quotation_logs.sap_doc_entry` → `OQUT.DocEntry` | `tbl_primary_sales.bill_number` → `OINV.DocNum` (2026-05 onward only) | — |

**Rule of thumb for Daman:** if the thing has a rupee value and a `DocNum` in the 6/7-series, it is
SAP's. If it has an `ORD-` number and an approval stage, it is OMS's and SAP has never seen the
approval. If it has a carton quantity and no money, it is DSR re-typing a SAP invoice.

### 1b. Live proof of the OMS→SAP path (F), and of its current outage

```sql
-- who creates quotations in SAP
SELECT U."U_NAME", COUNT(*), MIN(Q."DocDate"), MAX(Q."DocDate")
FROM JIVO_OIL_HANADB.OQUT Q LEFT JOIN JIVO_OIL_HANADB.OUSR U ON U."USERID"=Q."UserSign" GROUP BY 1;
```
→ Oil: **B1i 1,351** (2026-02-10 → 2026-07-25), manager 330, SUMIT 6, others 4.
→ Bev: **B1i 731** (2026-05-12 → 2026-07-24), SUMIT MEHTA 2.
→ Mart: `OQUT` = **0 rows**. No OMS quotation has ever landed in the Mart company.

```sql
-- who creates sales ORDERS in SAP (all time, Oil)
```
→ MANSI 6,690 · HARPREET 4,387 · SUMIT 2,243 · KARANPREET 648 · PRESHIT 481 · LOVPREET 168 ·
manager 88 · … · **B1i 1** (one order, ever).

So: **OMS writes quotations, humans write orders.** The SAP sales order is a human act on top of
the OMS document. Confirmed downstream by `RDR1.BaseType=23` (order sourced from quotation):

| Month (Oil) | SAP sales orders | of which from a quotation |
|---|---|---|
| 2026-01 | 718 | 0 |
| 2026-02 | 584 | 63 |
| 2026-03 | 477 | 98 |
| 2026-04 | 487 | 79 |
| 2026-05 | 533 | **375 (70%)** |
| 2026-06 | 454 | **301 (66%)** |
| 2026-07 | 418 | 201 (48%) |

Daily, late July (Oil):

| Date | orders | from quotation |
|---|---|---|
| 2026-07-22 | 36 | 25 |
| 2026-07-23 | 30 | 20 |
| **2026-07-24** | 12 | **0** |
| 2026-07-25 | 19 | 1 |
| **2026-07-27** | 32 | **0** |
| **2026-07-28** | 46 | **0** |
| **2026-07-29** | 42 | **0** |

Last `OQUT` row in the whole database: Oil DocEntry 15737 / DocNum 232607217 / 2026-07-25;
Beverages 2026-07-24. Prior daily volume was 8–30 (Oil) and 10–21 (Bev). **The feeder is dark.**

I tested the obvious alternative — that OMS switched to pushing sales orders directly under a
different SAP login. It did not: the `manager` login spiked to 84 orders in those six days, but
those rows carry `U_SALES_PERSON` NULL or `'ECOM'` with `NumAtCard` = a Mart intercompany PO
number (e.g. 726224597), i.e. intercompany/e-com order entry, not OMS traffic.

**I do not know why it stopped.** Outage, posting-period lock, or a deliberate workflow change are
all consistent with what I can see. That is a question for the OMS team, not for SQL.

### 1c. The trap everybody must stop falling into: `U_OMS_Order_No`

`JIVO_OIL_HANADB.OINV` and `ORDR` carry columns literally named `U_OMS_Order_No` and `U_OMS_REF`.
They are **not** the OMS join key. Per the sap-custom probe (which I accept — it is a live count):
6,253 of 14,736 Oil orders populated but only **746 distinct values**, dominated by keyboard mash
(`4563` ×750, `1234` ×639, `4653` ×623, `123` ×225, `1111` ×161), and `U_OMS_REF` populated on
exactly **1** invoice ever. The `hana-census` probe read the decay of this field as "the OMS
integration collapsed". **That inference is wrong** — the field was always junk; the real feed runs
through `OQUT` and was healthy through 2026-07-23. The two probes are reconciled: both facts are
true, they are about different things.

**The only defensible OMS↔SAP joins:** `orders.id → sales_quotation_logs.sap_doc_entry →
OQUT.DocEntry` (plus company), and `card_code → OCRD.CardCode`.

### 1d. THE BIG REVERSAL — DSR `primary` is a SAP mirror, not native data

Phase 1 ruled `tbl_primary_sales` **N** at 78% and specifically said `bill_number` "holds 3-digit
numbers (748, 769, 771) — a bill book, **not** a SAP DocNum." That was true of the old rows and
false of the current ones. Live:

```sql
-- DSR: bill_number population by month
SELECT FORMAT(date,'yyyy-MM'), COUNT(*), SUM(CASE WHEN bill_number<>'' THEN 1 ELSE 0 END) …
```
→ **zero** `bill_number` on every month from 2024-06 to 2026-04. Then 2026-05: 323/540,
2026-06: 568/598, 2026-07: 326/338.

I took the 185 distinct ≥8-digit numeric bill numbers from 2026-05 onward and looked them up in SAP:

```sql
SELECT COUNT(DISTINCT "DocNum") FROM JIVO_OIL_HANADB.OINV WHERE "DocNum" IN (<185 values>);
```
→ **Oil 184 · Mart 0 · Bev 0.** 184/185 = 99.5% resolve to SAP Oil A/R invoice numbers.

Line-level proof, ANAND ENTERPRISES (DSR) = `CUSTA000171` (SAP), July 2026:

| DSR line (cartons) | qty | bill_number | SAP `OINV` DocNum 626070520 line | SAP qty (pcs) | ratio |
|---|---|---|---|---|---|
| 5LTR Sunflower | 10 | 626070520 | FG0000053 COLD PRESS SUNFLOWER 5 LTR **4 PCS** | 40 | **×4** |
| 1LTR SUNFLOWER | 100 | 626070520 | FG0000081 COLD PRESS SUNFLOWER 1 LTR **20 PCS** | 2,000 | **×20** |
| 1LTR Mustard (20 pack) | 40 | 626070520 | FG0000030 MUSTARD KACHI GHANI 1 LTR **20 PCS** | 800 | **×20** |
| 700 GM SOYA OIL | 498 | 626070329 | FG0000299 SOYABEAN 700 GMS POUCH **12 PCS** | 5,976 | **×12** |
| 700 GM SOYA OIL | 499 | 626070362 | FG0000299 | 5,988 | **×12** |
| 700 GM SOYA OIL | 1 | 626070370 | FG0000299 | 12 | **×12** |

Every ratio is exactly the case pack printed in the SAP item name. **DSR quantity = cartons; SAP
quantity = pieces.** This is a hand re-key of a SAP invoice, not an independent record of a sale.

Coverage is partial: July 2026 — SAP Oil issued **542** invoices; DSR captured **157** distinct
bills (~29%). Aggregate quantity for the same distributor/month is therefore 5–11% of SAP's when
you (wrongly) compare cartons to pieces:

| Distributor | DSR Jul qty (cartons) | SAP Jul qty (pcs) |
|---|---|---|
| ANAND ENTERPRISES | 1,423 | 16,340 |
| RAJESHWAR KISHORE MAHINDER PAL | 859 | 10,671 |
| DWARKA DAS NARINDER KUMAR | 464 | 9,012 |
| RAJ MATA TRADERS | 573 | 5,502 |

**Ruling: M for 2026-05 onward** (same facts, coarser unit, incomplete, days-late, no money).
**U for 2024-06 → 2026-04** (~10,000 rows with no SAP reference at all — I could not establish
whether those too were re-keys or independent field entries; there is no key to test with).

---

## 2. THE MANDATORY "COULD SAP HOLD THIS?" CHECK

Before every **N** below I ran, myself, on all three schemas:

```sql
SELECT SCHEMA_NAME, TABLE_NAME, RECORD_COUNT FROM M_TABLES WHERE SCHEMA_NAME LIKE 'JIVO%'
AND (UPPER(TABLE_NAME) LIKE '%TARGET%' OR '%BEAT%' OR '%RETAIL%' OR '%VISIT%'
  OR '%SCHEME%' OR '%OUTLET%' OR '%JOURNEY%' OR '%ROUTE%');
```
→ **only** `TMP_InsertInto_NewItemsInTargetITM/ITW`, 0 rows, SAP-internal temp tables.

```sql
SELECT SCHEMA_NAME, TABLE_NAME, RECORD_COUNT FROM M_TABLES
WHERE SCHEMA_NAME LIKE 'JIVO%' AND TABLE_NAME LIKE '@%' AND TABLE_NAME NOT LIKE '@A%' AND RECORD_COUNT>0;
```
→ every populated UDT across all three companies is either the Uneecops/UTL e-invoice+e-way add-on
(`@UTL_*`, `@UNE_*`), the ZIA consultant add-on (`@ZIA_*`, `@OZIA*`), a QC stub (`@QC_I` 19 /
`@QC_O` 6), a budget stub (`@BUDGET` 1), or **JIVO's product/customer taxonomy**: `@ITEM_VARIETY`
(196/131/214), `@MAIN_GROUP` (60/50/54), `@ITEM_SUBGRP` (51/51/69), `@ITEM_SKU` (50/35/17),
`@CHAIN` (46/47/46), `@ITEM_UNIT`, `@BRAND` (3). **No UDT anywhere holds an order, a target, a
beat, a retailer, a visit, a scheme, an approval or a rate agreement.**

Standard-table negatives I re-verified myself (all three companies):
`OCLG` 0/0/0 (activities) · `OOPR` 0/0/0 (opportunities) · `OSCL` 0/0/0 (service calls) ·
`OEDG` 0/0/0 · `OTER` **1/1/1** (the default territory row only) · `OSPP` **22/0/0** (BP special
prices) · `SPP1` 12/0/0 · `SPP2` 0.

And the field-sales hierarchy fields on `OCRD`, counted non-blank by me (not just non-null):

```sql
SELECT COUNT(*), SUM(CASE WHEN IFNULL("U_UNE_ASM",'')<>'' THEN 1 ELSE 0 END), … FROM JIVO_OIL_HANADB.OCRD;
```
→ TOT **3,390** · U_UNE_ASM **0** · U_UNE_RSM **0** · U_UNE_SO **0** · U_UNE_SR **0** ·
U_UNE_AREA **0** · U_Chain 1,477 · U_Main_Group 3,348.

**The columns exist and are 100% empty.** A schema-only reader would wrongly conclude SAP holds the
ASM/RSM/SO/SR territory tree. It does not.

Also relevant and *populated*, so it is NOT a free N: `OPLN` **10 price lists** with `ITM1`
**22,710 / 13,490 / 21,920** item-price rows. SAP does have list pricing. What it does not have is
per-party negotiated rates (`OSPP` 22 rows in Oil, 0 elsewhere).

---

## 3. MARKETPLACE / CHANNEL — where SAP stops

SAP holds the marketplace **counterparty and the batched settlement invoice**, nothing finer.

`JIVO_MART_HANADB.OINV` by marketplace customer:

| CardCode | CardName | invoices | span |
|---|---|---|---|
| CUSTA000910 | FLIPKART (B2C-MAY-JULY) | 6,883 | 2025-05-23 → 2026-07-27 |
| CUSTA000912 | AMAZON (B2C -MAY-JULY) | 2,611 | 2025-05-22 → 2026-07-29 |
| CUSTA000722 | KIRANAKART (Zepto) | 237 | → 2026-06-18 |
| CUSTA000496 | INNOVATIVE RETAIL (BigBasket) | 71 | → 2026-01-13 |

`JIVO_BEVERAGES_HANADB`: `CUSTA001135 BLINK` — **6 invoices**, total. `JIVO_OIL_HANADB`: Amazon
3,061 invoices all dated 2024-09-30 (a migration batch), JioMart live to 2026-07-16.

Grain check — July 2026, Mart, Flipkart+Amazon B2C: **218 invoices / 2,932 lines / ₹61.9 lakh**,
averaging 13.4 lines each, `Comments` = *"AMAZON HARYANA 15 TO 27 JULY Based On Deliveries
1507264731."* These are **period-batched dispatch invoices**, not consumer orders.

Against that, the fleet holds: 2,116 Flipkart + 42 Amazon **individual consumer orders** with
buyer name, pincode and tracking id in `factory_flow.marketplace_marketplaceorder` (2026-06-26 →
2026-07-28); 8,597 Amazon consumer GST invoices in `test_supabase.amazon_mp`; 634,208 rows of
Swiggy dark-store sell-out in `test_supabase."swiggySec"`. **None of that grain exists in SAP and
never will.**

---

## 4. UNRESOLVED / DOWNGRADED

### 4a. `test_supabase.sustain_dist` — I downgrade the ecom mapper's **M@90 to U@55**

The ecom mapper called this a SAP→ecom aggregate of distributor primary offtake. It does not
reconcile. Live, SUSTAINQUEST = `JIVO_MART_HANADB.OCRD` `CUSTA000907` (the only SUSTAINQUEST card
in any company). June 2026:

- SAP: 24 invoices / 49 lines / qty **138,814** / **₹4.06 Cr**
- ecom `sustain_dist`: 42 rows / qty **71,880** / **₹2.59 Cr**

Per-unit **rates match SAP almost exactly** (FG0000151 SAP ₹1,238 vs ecom ₹1,246.19; FG0000150 SAP
₹247.6 vs ecom ₹247.16; FG0000032 SAP ₹214.3 vs ecom ₹214.35; FG0000008 SAP ₹1,952.4 vs ecom
₹1,949.02) but **quantities do not** (FG0000030 SAP 30,200 vs ecom 6,680; FG0000150 SAP 29,488 vs
ecom 5,488 — ratios 4.5×, 2.9×, 5.4×, 8.8×, i.e. not a unit conversion either). The table holds
exactly **one month** (2026-06-01, 42 rows). Priced off SAP, quantified from somewhere else.
Honest answer: **I do not know what it is.** Do not quote it as SAP primary offtake.

### 4b. ecom `sap sales-invoices` / `sales-analysis` — M, but not proven live

I could not settle this the way I would like. `jivo-ecom-pp-cli doctor` → `Credentials: invalid
(HTTP 401)`; the token is expired and I had no way to refresh it without a login I do not own. The
M ruling rests on: (a) the endpoints take `DocEntry` and `CardCode` directly as path parameters;
(b) the ecom Postgres has no invoice table, no `cardcode` column anywhere, no FDW and 0 foreign
tables. That is strong negative-space evidence, not a live row. **88.**

### 4c. Control-panel

Reachable (`http://103.89.45.75:9080/` → 302 to login) but I have no credential and login is a
session write, so I made **zero app calls**. My M rulings there rest on the phase-1 agent's
value-for-value HANA matches (which I spot-re-verified — e.g. the `OINV` freight user fields
`U_BilltyNumber` / `U_TransporterName` / `U_VehicleNoM` came back identically in EXIM's live
`get-open-ar` payload, independently confirming they are SAP columns) plus my own UDT/table
negatives for the N layer.

### 4d. Things I did not check, stated plainly

- I did **not** reconcile control-panel's headline realise aggregates to a `SUM(INV1)`. The
  phase-1 agent tried and failed (OLIVE 76.2M SAP vs 53.0M app). The *inputs* are provably SAP;
  the *filter rules* are not reproducible from outside.
- I did **not** determine whether JSAP's Sales H1–H4 hierarchy is the same population as DSR's
  `tbl_salesperson`. If it is, JSAP may be mirroring DSR rather than originating — that would not
  change the bucket (both are N relative to SAP) but it would change "which CLI to ask".
- I did **not** locate the production OMS Postgres. The `order_management` DB on the shared
  cluster is a different deployment (its `orders` reach id 107; production reaches 2038).
- I did **not** establish why the OMS→SAP quotation feed stopped on 2026-07-23.
- I did **not** test DSR primary rows dated before 2026-05 against SAP — there is no key to test
  with, which is exactly why I ruled that slice **U** rather than guessing.

---

## 5. WHAT DAMAN SHOULD ACTUALLY DO

**Ask SAP (`sapb1` / `hana-sql`), not the app, for:** every rupee figure, invoiced quantity,
customer master field, ledger balance, open order backlog, credit note, price list, the
quotation→order→invoice chain, and anything that has to tie to the books. Also ask SAP rather than
OMS/EXIM/JSAP for the customer and item master — every app copy is a stale, filtered subset
(OMS `sap_parties` 3,350 vs `OCRD` 3,351 for customers, last synced **manually** 2026-07-16;
EXIM `parties` **137 of 3,390**, last synced 2026-06-12).

**Ask the app, not SAP, for:** who approved the order and who rejected it and why (OMS); what each
distributor is entitled to buy and at what negotiated rate (OMS, 13,383 rows vs SAP's 22); which
salesman visited which of 127,395 shops with a GPS trace and a selfie (DSR); what a Swiggy dark
store actually sold yesterday (ecom); what the monthly litre target was (control-panel/ecom); what
we told Blinkit we would ship and whether the appointment slot held (portals).

**Never do:** add DSR primary volume to SAP invoice volume (different units, partial coverage, and
since May-2026 it is literally the same invoices); join anything to SAP on `U_OMS_Order_No`; quote
`sustain_dist` as SAP offtake; quote OMS `sap products.on_hand` as stock; reconcile ecom
`sap sales-analysis` against a `sapb1 --company` figure (the company is not established in the
ecom response — `connections/ECOM__JSAP.md:32`).

---

## 6. RULING TABLE (summary — full fields in the structured output)

| # | Entity | Systems | Bucket | Conf |
|---|---|---|---|---|
| 1 | OMS sales order object → SAP quotation | oms-cli | **F** | 97 |
| 2 | OMS order approval workflow / rate approvals / audit trail | oms-cli | **N** | 97 |
| 3 | OMS party↔product entitlement + negotiated basic rate | oms-cli | **N** | 96 |
| 4 | OMS schemes / free-goods | oms-cli | **N** | 90 |
| 5 | OMS quotation open/closed status read-back | oms-cli | **M** | 94 |
| 6 | Customer / business-partner master | oms, exim, jsap, cp, ecom, factory | **M** | 98 |
| 7 | Party ship-to / bill-to addresses | oms-cli | **M** | 96 |
| 8 | Branches / business places | oms-cli | **M** | 98 |
| 9 | OMS live HANA passthrough (`hana so`, `all-customers`, …) | oms-cli | **M** | 90 |
| 10 | OMS A/R invoice module (batch pick → post) | oms-cli | **F** | 78 |
| 11 | OMS SAP-sync run history | oms-cli | **N** | 97 |
| 12 | DSR primary sales, 2026-05 onward | dsr-cli | **M** | 97 |
| 13 | DSR primary sales, pre-2026-05 | dsr-cli | **U** | 55 |
| 14 | DSR retailer / outlet universe (127,395) | dsr-cli | **N** | 98 |
| 15 | DSR distributor master | dsr-cli | **N** | 90 |
| 16 | DSR salesperson master + org hierarchy | dsr, jsap | **N** | 96 |
| 17 | DSR beats / routes / beat-shop map | dsr-cli | **N** | 99 |
| 18 | DSR secondary sales visits (distributor→retailer) | dsr-cli | **N** | 97 |
| 19 | DSR promoter / merchandiser activity | dsr-cli | **N** | 97 |
| 20 | DSR + control-panel + ecom sales TARGETS | dsr, cp, ecom | **N** | 96 |
| 21 | DSR trade schemes / gift issuance | dsr-cli | **N** | 88 |
| 22 | DSR channel stock declarations | dsr-cli | **N** | 95 |
| 23 | DSR product catalogue (`tbl_item`, 333) | dsr-cli | **N** | 94 |
| 24 | DSR `sap_sales_log` (frozen 2023 extract) | dsr-cli (unexposed) | **M** | 96 |
| 25 | ecom `sap sales-invoices` / `sales-analysis` | ecom-cli | **M** | 88 |
| 26 | ecom `sap distributors` / `distributor-orders` | ecom-cli | **M** | 85 |
| 27 | Marketplace secondary sell-out (dark-store level) | ecom, portals | **X** | 97 |
| 28 | Marketplace purchase orders raised on JIVO | ecom, blinkit, zepto | **X** | 95 |
| 29 | Marketplace consumer orders + consumer invoices | factory, ecom, dsr | **X** | 94 |
| 30 | `sustain_dist` distributor offtake | ecom-cli | **U** | 55 |
| 31 | ecom SKU bridge / master_sheet + realisation model | ecom-cli | **N** | 93 |
| 32 | Control-panel sales/realise analytics | control-panel | **M** | 92 |
| 33 | Dispatch / freight fields (bilty, transporter, vehicle, driver) | cp, exim, factory | **M** | 99 |
| 34 | Order-In-Hand (open uninvoiced order value) | cp, factory | **M** | 97 |
| 35 | Credit notes / sales returns | cp, sapb1 | **M** | 95 |
| 36 | A/R open items + aging | exim, cp | **M** | 99 |
| 37 | Control-panel claims register / aging remarks / credit lock | control-panel | **N** | 94 |
| 38 | Control-panel rate-list scenarios | control-panel | **N** | 91 |
| 39 | Factory scan-to-ship dispatch sessions + dispatch plans | factory-cli | **N** | 95 |
| 40 | GST e-invoice IRN / e-way bill on sales documents | oms, SAP add-on | **M** | 96 |

---

## 7. CONFLICTS BETWEEN SOURCE-MAPPERS — RESOLVED

**C1. DSR `primary`: N (dsr-cli, 78) vs M (me, 97).** Resolved by live evidence the phase-1 agent
explicitly said he had not run. `bill_number` = SAP `OINV.DocNum` on 184 of 185 distinct values
since 2026-05, and DSR carton quantity × the SAP item's case pack equals the SAP piece quantity
exactly on every line I checked. **My ruling stands: M from 2026-05, U before.** The phase-1
statement that `bill_number` "holds 3-digit numbers … not a SAP DocNum" was true of pre-May rows
and false of current ones.

**C2. OMS→SAP: "stamping collapsed / don't rule M" (hana-census, 82) vs "F, verified row-for-row"
(oms-cli, 97) vs "U_OMS_Order_No is operator-typed garbage, no join key exists" (sap-custom, 97).**
All three are describing different objects and all three are factually right. `U_OMS_Order_No` is
and always was junk (746 distinct values over 6,253 rows) — hana-census read its decay as the
integration dying, which is an incorrect inference. The real feed is `sales_quotation_logs →
OQUT`, which I re-verified live (B1i created 1,351 Oil + 731 Bev quotations). **Ruling: F.**
**But I add a fact none of them had: that feed wrote nothing after 2026-07-23/24.**

**C3. e-invoice IRN: X (oms-cli, 88) vs M (me, 96).** The OMS mapper checked
`JIVO_OIL_HANADB."@UTL_EWAY"` and `"@AUTL_EWAY"` (0 rows) and concluded SAP is not the system of
record. **He checked the wrong table.** Live: `"@UTL_MDEXTH"` holds **17,695** rows with
`U_UTL_IRN` populated on **all 17,695** and `U_UTL_AckNo` on 15,449, spanning 2024-10-01 →
**2026-07-29**; `"@UTL_ST_EWAYDT"` holds 1,333 e-way rows. SAP *is* the IRN system of record for
JIVO's sales documents. The government IRP is the external origin (X in the world), but relative
to this fleet the data is **M** — ask SAP, not OMS, whose `einvoice_irn` holds 24 rows.

**C4. `sustain_dist`: M@90 (ecom-cli) vs U@55 (me).** Reconciliation fails on quantity by 2.9×–8.8×
per item and by ₹1.47 Cr in total for SUSTAINQUEST June 2026, while the per-unit rates match SAP.
Downgraded to U.

**C5. Factory `marketplace_*`: X@80 with an explicit handoff (factory-cli).** I take the handoff
and confirm **X@94**, adding what the factory agent could not see: SAP *does* book this revenue,
but as 218 period-batched invoices in July against 2,158 individual consumer orders in the factory
app — a ~10× grain difference, so the two can never be compared row for row.

**C6. Marketplace coverage "SAP holds only counterparty ledgers" (sap-surface) vs "marketplace
sales are in SAP" (portals+postsql).** Both partial. Resolved per channel and per company:
Flipkart/Amazon B2C are genuinely invoiced in **Mart** (6,883 + 2,611 invoices, live to
2026-07-27/29); Zepto has 237 Mart invoices but nothing since 2026-06-18; Blinkit has **6**
invoices, in **Beverages** only; Swiggy and BigBasket appear mainly on the vendor side. Never make
a blanket statement about "marketplace sales in SAP".

**STILL UNRESOLVED (I am not guessing):** why the OMS→SAP quotation feed stopped; what
`sustain_dist` actually measures; whether JSAP's sales H1–H4 hierarchy is the same population as
DSR's `tbl_salesperson`; whether ecom's `/api/sap/*` is a live proxy or reads the frozen local
copies; which SAP company the ecom SAP layer reads.
