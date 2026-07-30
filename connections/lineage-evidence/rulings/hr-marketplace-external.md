# FINAL RULINGS — domain: hr-marketplace-external

Adjudicator: hr-marketplace-external · 2026-07-30
Scope: TankhaPay (payroll / attendance / leave / payouts / employee master / biometric
punches) + all marketplace & portal data (Blinkit, Zepto, Amazon, Flipkart, Swiggy,
BigBasket, Zomato, JioMart, CityMall): channel sales, ads, coupons, brand fund,
DOH/SOH, appointments, pincode/geography, scraped price & availability.

All SAP evidence below was re-run by me tonight against live HANA through the tunnel
(`./hana-sql/hana-sql -env connections/hana-tunnel.env`). All Postgres evidence was
re-run through `postsql`. TankhaPay was re-read live. I did not accept any phase-1
bucket that rested on doc evidence.

---

## HEADLINE

**HR is the cleanest N in the entire estate, and the marketplace layer is the most
misunderstood.**

SAP has no employee. It has 33 hollow `OHEM` stubs across three companies against
TankhaPay's 1,795 people, and there is not one attendance / payroll / leave / shift /
wage table anywhere in 3,111 tables or 100+ user-defined tables. What SAP *does* hold
is the **money**: 402 employee-named GL advance accounts, 510 employee imprest business
partners, a purpose-built cross-company `REPORT_EMP_IMP` ledger procedure, and salary
cost split by department per month. Person-level HR: TankhaPay. Employee money:
SAP. They meet nowhere automatically.

The marketplace finding is bigger and it changes how Daman should read every e-com
number. **JIVO's SAP does not sell to Blinkit, Zepto, Swiggy or BigBasket.** It sells
to seven distributor companies — SUSTAINQUEST, KNOWTABLE, ANTIZE FOODS, CHIRAG
ENTERPRISES, EVARA, BABA LOKENATH, R K WORLDINFOCOM — who then sell onward to the
platforms. 40,977 Zepto/Blinkit/Swiggy POs in the ecom warehouse are raised on those
distributors, not on JIVO. So the marketplace layer is not "SAP data with extra
columns"; it is **the leg of the value chain that starts where SAP's books end.**
The two exceptions are Amazon B2C and Flipkart B2C, which JIVO Mart invoices directly
under its own GSTIN — and even there the platform's own invoice feed and SAP disagree
by roughly ₹60 lakh in a single month.

---

## PART 1 — SAP GROUND TRUTH I ESTABLISHED MYSELF (Rule 3 compliance)

Before ruling N on anything I ran these. Every N ruling in this document cites them.

### 1.1 There is no HR object in SAP, standard or custom

```sql
SELECT SCHEMA_NAME, TABLE_NAME FROM SYS.TABLES
WHERE SCHEMA_NAME LIKE 'JIVO%'
  AND (UPPER(TABLE_NAME) LIKE '%ATTEND%' OR '%PAYROL%' OR '%SALAR%' OR '%LEAVE%'
    OR '%PUNCH%' OR '%BIOMET%' OR '%SHIFT%' OR '%ROSTER%' OR '%WAGE%'
    OR '%PAYOUT%' OR '%IMPREST%' OR '%ESIC%' OR '%TANKHA%')
→ ZERO ROWS.
```
`SYS.TABLES` covers `@`-prefixed UDTs, so this is simultaneously the standard-table
check and the user-table check. I additionally listed every non-archive UDT in all
three schemas (54 Bev / 47 Mart / 18 Oil non-add-on). The complete Oil set is:
`@BRAND @BUDGET @BUDGET1 @CHAIN @ITEM_SKU @ITEM_SUBGRP @ITEM_UNIT @ITEM_VARIETY
@MAIN_GROUP @OZIA @OZIAR @QC_I @QC_O @SERVER @ZIA_ASSET_ISSUE_I @ZIA_ASSET_ISSUE_O
@ZIA_DL_LIMIT @ZIA_DL_OLIMIT`. **Not one is HR.** The rest are the Uneecops/UTL
e-way-bill and e-invoice add-on.

I also swept stored procedures and views:
```sql
SELECT ... FROM SYS.PROCEDURES / SYS.VIEWS WHERE SCHEMA_NAME LIKE 'JIVO%'
  AND (name LIKE '%TANKHA%' OR '%PAYROLL%' OR '%SALAR%' OR '%ATTEND%' OR '%EMP%')
```
→ exactly one meaningful hit: **`JIVO_OIL_HANADB.REPORT_EMP_IMP`** (see 1.3), plus
`ES_EMPLOYEE_M_D` (SAP's own Enterprise Search view over the empty `OHEM`).

### 1.2 `OHEM` is a stub, verified row by row

```
OIL 17 · MART 1 · BEV 15  (33 total)
```
All 17 Oil rows dumped: `jobTitle` NULL on 17/17, `startDate` NULL on 17/17,
`salary` = 0 on 17/17, `dept` populated on 1/17. The names (Avtar Singh, Jasbir
Singh, Gurvinderjeet, Arshdeep, Nirmal Kaur…) are the SAP licence-holders and budget
approvers, not a workforce.

Live TankhaPay the same night:
```
tankhapay-portal dashboard tpay-dashboard-data --set action=get_employee_list
→ total_employees 593 · today_s_attendance 248 · left_count 1202
  · joining_pending 7 · cur_monthyr Jul-2026
```
**1,795 people in TankhaPay against 33 stubs in SAP.**

### 1.3 SAP's *entire* HR surface is three user fields and it is all about money

`CUFD` (the user-field dictionary) contains exactly this for HR, across all tables:

| Table | Field | Label |
|---|---|---|
| `OCRD` / `ACRD` | `U_Emp_Code` | Emp Code |
| `OACT` / `AACT` | `U_Emp_Code` | Employee Code |
| `JDT1` / `BTF1` / `AJD1` | `U_OcrCode5` | Salary Category |

Population, live:

| | total | tagged with an employee code |
|---|---:|---:|
| Oil `OCRD` business partners | 3,390 | **510** |
| Mart `OCRD` | 2,183 | 231 |
| Bev `OCRD` | 2,930 | 280 |
| Oil `OACT` GL accounts | 1,424 | **402** |
| Mart `OACT` | 1,104 | 159 |
| Bev `OACT` | 764 | 124 |

Sample of the 402 Oil GL accounts — one account per person, named for them:
```
1113001 INDERPREET SINGH ADVANCE JWPL1329   U_Emp_Code JWPL1329
1113010 GAGANDEEP SINGH ADVANCE JWPL0018    U_Emp_Code JWPL0018
1113012 RAVINDER SINGH SHUNTY ADVANCE JWPL0035
```
And `JIVO_OIL_HANADB.REPORT_EMP_IMP` is a hand-written cross-company (Oil + Beverages)
employee-imprest ledger over GL parent `2110000` / account `2110003`, computing opening
balance, movement and running balance per `CardCode` — i.e. SAP has a **purpose-built
employee advance/imprest ledger report.** This is real, current HR-adjacent data in SAP
and the phase-1 maps under-reported it.

`JDT1.U_OcrCode5` "Salary Category": 1,790 tagged lines —
`PROMOTER 1062 · SO/SR 455 · ASM 262 · RSM 6 · CALLER 4 · MIS 1`, spanning
2025-03-31 → **2026-01-31 and then it stops.** The tagging is abandoned.

### 1.4 SAP holds salary as departmental cost, never per person

`5630001 SALARY EXPENSE` by month:
```
2026-06  74 lines ₹1,19,09,761      2026-03  80 lines ₹1,13,26,733
2026-05  74 lines ₹1,16,22,767      2026-02  85 lines ₹1,14,23,236
2026-04  70 lines ₹1,16,90,732      2025-11  83 lines ₹1,29,97,254
```
~70–100 lines a month, ~₹1.15 cr. Sampled lines carry **no employee identifier at
all** — the dimensions are `OcrCode3` (budget head: `BackOff`, `Sales`, `Factory`,
`Med MKT`, `Del Mayp`), `OcrCode2` (`06-2026`), `ProfitCode` (`CANOLA`), free-text
`LineMemo` ("BACK OFFICE BELOW", "sales below june-26"). 74 lines for 593 employees
settles it: **SAP books salary by department, not by head.**

Supporting GL: `2161001..2161012 SALARY PAYABLE <MONTH>`, `2163015 EPF PAYABLE`,
`2163016 ESIC PAYABLE`, `2133004 TDS ON SALARY`, `5630007 EPF ADMIN CHARGES`,
`5630010/15 EPF EMPLOYEE/EMPLOYER`, `5630011/12 ESIC EMPLOYEE/EMPLOYER`,
`5630014 BONUS`, `5630006 GRATUITY`, `2180002 PROVISION FOR GRATUITY`,
`5630017 REVERSAL OF UNCLAIMED SALARY`. All aggregate.

### 1.5 There is no marketplace object in SAP either

```sql
SELECT ... FROM SYS.TABLES WHERE SCHEMA_NAME LIKE 'JIVO%'
 AND (name LIKE '%PINCODE%' OR '%APPOINT%' OR '%CAMPAIGN%' OR '%ADSPEND%'
   OR '%COUPON%' OR '%BRANDFUND%' OR '%DARKSTORE%' OR '%MARKETPLACE%'
   OR '%LISTING%' OR '%ASIN%' OR '%SCRAPE%' OR '%DOH%' OR '%TARGET%')
→ only SAP's own TMP_InsertInto_NewItemsInTargetITM/ITW temp tables. Nothing real.
```
No pincode master, no appointment, no campaign, no ad-spend, no coupon, no brand-fund,
no dark-store, no listing, no ASIN, no DOH, no sales-target table. In any of the three
companies.

### 1.6 What SAP *does* hold on the marketplace side — and it is more than phase 1 said

**Counterparty master.** Every platform exists as a business partner. Live scan of all
three `OCRD`s returned 25 (Oil) / 29 (Mart) / 22 (Bev) marketplace cards, e.g.
`CUSTA000873 AMAZON`, `CUSTA000722 KIRANAKART (Zepto)`, `CUSTA000496 INNOVATIVE RETAIL
(BigBasket)`, `VENDA000849 BLINK COMMERCE`, `VENDA000401 AMAZON SELLER SERVICES`,
`VENDA001202 AMAZON ADVERTISING A/R`, `VENDA000713 FACEBOOK INDIA`, `VENDA001000 GOOGLE
INDIA`, most tagged `U_Main_Group = 'E-COMMERCE'`.

**A/R — who JIVO actually invoices (Mart, the e-com book):**
```
CUSTA000910 FLIPKART (B2C)      6,787 inv  ₹10.18 cr  2025-05-23 → 2026-07-27
CUSTA000912 AMAZON (B2C)        2,575 inv  ₹ 1.57 cr  2025-05-22 → 2026-07-29
CUSTA000879 FLIPKART INDIA        660 inv  ₹11.08 cr  → 2026-02-03
CUSTA000722 KIRANAKART (Zepto)    237 inv  ₹ 5.08 cr  → 2026-06-18
CUSTA000376 ZOMATO HYPERPURE      234 inv  ₹ 9.07 cr  → 2026-07-04
CUSTA000907 SUSTAINQUEST          216 inv  ₹30.80 cr  → 2026-07-28
CUSTA000496 BIGBASKET              65 inv  ₹ 1.45 cr  → 2026-01-13
```
Oil is the legacy/GT book (JioMart 3,090 + 1,502 + 1,183, Reliance Retail 304,
BigBasket 206). **Amazon in Oil is a single 2024-09-30 migration batch of 3,061
invoices — do not read it as trading data.** Beverages has 6 Blink invoices, total.

**A/P — platform commission, logistics, ads and brand fund ARE in SAP (Mart):**
```
VENDA000401 AMAZON SELLER SERVICES  207 inv  ₹5.57 cr  → 2026-07-06
VENDA000120 FLIPKART INTERNET       162 inv  ₹2.63 cr  → 2026-07-16
VENDA000948 ZEPTO/KIRANAKART VEND    36 inv  ₹2.04 cr  → 2026-06-04
VENDA000729 SWIGGY                   26 inv  ₹2.31 cr  → 2026-03-19
VENDA000849 BLINK COMMERCE           19 inv  ₹2.46 cr  → 2026-06-09
```
and in Oil, **advertising money is in SAP too**:
```
VENDA000713 FACEBOOK INDIA          268 inv  ₹8.74 L   → 2026-06-21
VENDA001000 GOOGLE INDIA             21 inv  ₹17.97 L  → 2026-06-30
VENDA001202 AMAZON ADVERTISING       14 inv  ₹1.54 L   (Jan–Feb 2025 only)
```

**Credit notes (returns / trade spend) are in SAP (Mart `ORIN`):** Flipkart B2C 1,256 ·
Kiranakart/Zepto 163 (₹2.12 cr) · Sustainquest 77 (₹5.63 cr) · Flipkart India 164
(₹1.50 cr) · Amazon B2C 172.

**e-commerce and FBF warehouses exist in SAP with real stock (Mart `OITW`):**
`DL-EC Mayapuri E-Commerce` 98 items / 34,250 units · `FBF-HR HARYANA FBF GODOWN`
27 / 3,257 · `KT-FBF Karnataka` 23 / 307 · `GP-ECM GUPTA ECOM MART` 6 / 7,125.
Plus `BH-FK Bhakharpur Flipkart Packing` and `DP-DL/HR/PB Dropship`.

### 1.7 There is no feeder path from the marketplace stack into SAP

```
postsql --db test_supabase: information_schema.columns
  WHERE column_name ILIKE '%posted%' OR '%doc_entry%' OR '%docentry%'
     OR '%sync_status%' OR '%pushed%'
→ ONE row: public.oitm_master.docentry   (a column in a frozen SAP copy)
```
No `posted_to_sap`, no `sap_doc_entry`, no push log, anywhere in the 1.4 GB ecom
warehouse. TankhaPay likewise: `grep -riE '\bsap\b|hana|oinv|ocrd|erp_sync'` over the
whole CLI + vault returns **one** hit, and it is a prose sentence in
`vault/_meta/Read-Only-Guardrails.md`. Blinkit CLI: **0** SAP references, single host
`https://www.partnersbiz.com`. Zepto CLI: **0**, seven `*.zepto.co.in` hosts.
**F is empty for this entire domain.**

---

## PART 2 — THE MARKETPLACE → SAP HANDOFF (the double-count zone)

This is the part of the brief that mattered most and it needed live work. Here it is.

### The chain

```
  JIVO OIL  ──intercompany──▶  JIVO MART   ──A/R invoice──▶  DISTRIBUTOR  ──PO/GRN──▶  PLATFORM  ──▶ CONSUMER
  (SAP)                        (SAP)          IN SAP ✅       (own books)   NOT IN SAP    NOT IN SAP    NOT IN SAP
                                   │
                                   └──────────direct B2C A/R (Amazon, Flipkart)──────────▶ IN SAP ✅ (partial)
```

### Evidence — who the marketplace POs are actually raised on

`test_supabase.total_po` (8,848 rows, BigBasket / Flipkart Grocery / Zomato / CityMall /
DealShare) and `total_po_zbs` (40,977 rows, Zepto / Blinkit / Swiggy), grouped by
`vendor_name`:

```
SWIGGY   KNOWTABLE ONLINE SERVICES     10,044   2025-08-01 → 2026-07-29
SWIGGY   CHIRAG ENTERPRISES             6,604
SWIGGY   SUSTAINQUEST                   5,246
BLINKIT  ANTIZE FOODS PVT LTD           3,435
BLINKIT  EVARA ENTERPRISES              2,861
BLINKIT  JIVO MART PRIVATE LIMITED      2,721   ← the only JIVO-direct q-comm leg
ZEPTO    Antize Foods Private Limited   1,727
ZEPTO    CHIRAG ENTERPRISES             1,337
ZEPTO    KNOWTABLE                      1,196
BIG BASKET SUSTAINQUEST                 1,398
CITY MALL  JIVO MART PRIVATE LIMITED    1,071
```

Every one of those vendor names resolves to a **JIVO customer card in SAP**:
```
CUSTA000907 SUSTAINQUEST PRIVATE LIMITED        U_Chain DISTRIBUTOR
CUSTA000592 KNOWTABLE ONLINE SERVICES           U_Chain DISTRIBUTOR
CUSTA000927 ANTIZE FOODS PRIVATE LIMITED        U_Chain JIVOMART   U_Main_Group E-COMMERCE
CUSTA000906 EVARA ENTERPRISES                   U_Chain DISTRIBUTOR U_Main_Group E-COMMERCE
CUSTA000900 BABA LOKENATH TRADERS               U_Chain DISTRIBUTOR U_Main_Group E-COMMERCE
CUSTA000650/000354 CHIRAG ENTERPRISES           U_Chain DISTRIBUTOR
```
And JIVO Mart's top customers this financial year are exactly those companies:
```
CUSTA000048 R K WORLDINFOCOM PVT LTD  505 inv  ₹31.0 cr   E-COMMERCE
CUSTA000592 KNOWTABLE                  75 inv  ₹13.4 cr
CUSTA000907 SUSTAINQUEST              107 inv  ₹12.0 cr
CUSTA000927 ANTIZE FOODS               57 inv  ₹10.4 cr
CUSTA000354 CHIRAG ENTERPRISES MUMBAI  61 inv  ₹ 6.3 cr
CUSTA000906 EVARA ENTERPRISES          62 inv  ₹ 6.1 cr
CUSTA000910 FLIPKART (B2C)          1,181 inv  ₹ 2.98 cr
CUSTA000912 AMAZON  (B2C)             717 inv  ₹ 0.88 cr
```

### What this means, stated plainly

1. **SAP's e-commerce revenue = sales to seven distributor companies**, not sales to
   marketplaces. There is no Blinkit customer invoice in Oil or Mart at all (only 6 in
   Beverages). Blinkit/Swiggy/Zepto appear on the **vendor** side, for their
   commission and charges.
2. **The ecom-cli / Blinkit / Zepto PO, GRN, appointment, fill-rate, sell-out and
   dark-store data describes a leg of the chain JIVO's SAP never records** — mostly
   because the goods have already left JIVO's books and belong to a third party.
3. **NEVER add ecom "primary" PO litres or value to SAP turnover.** They are different
   legs of the same physical goods, and the majority of the PO value sits in a
   distributor's books, not JIVO's.
4. **The one genuine reconciliation point is the JIVO→distributor invoice**, and the
   only clean join key is `CardCode` ↔ `vendor_name` (by name — there is no code on
   the PO rows).

### The Amazon B2C exception, and its ₹60 lakh gap

`amazon_mp` (8,597 rows) carries `seller_gstin = 07AAFCJ4102J1ZS`, a **single** value.
That GSTIN is `JIVO_MART_HANADB.OBPL` BPLId 1 = **JIVO MART PVT LTD, Delhi**. So these
are JIVO's own GST invoices, generated by Amazon on JIVO's behalf.

| May 2026 | invoices | value |
|---|---:|---:|
| `amazon_mp` (Amazon's MTR feed, Mart Delhi GSTIN) | 6,506 distinct | **₹81.05 L** |
| SAP `JIVO_MART_HANADB.OINV` → `CUSTA000912 AMAZON (B2C)` | 187 | **₹20.52 L** |

For context, **JIVO Mart's entire May-2026 A/R population is 985 invoices (₹2.28 cr)** —
so the 6,506 consumer invoices cannot possibly be in SAP individually; they are 6.6×
the whole company's invoice count for the month.

Conclusion: SAP books a much smaller, differently-grained A/R representation of Amazon
B2C (sample comments read `"AMAZON HARYANA 15 TO 27 JULY Based On Deliveries …"`, and
totals range from ₹299 to ₹33,888 — a mix of consumer-sized and batched). The consumer
detail — buyer name, ship-to pincode, ASIN, IRN and filing status, TCS split, gift-wrap
— is genuinely only in the platform feed. **And the ₹60 L/month difference is
unexplained.** I did not establish whether it is a different BP, a period cut, returns,
or a real gap. Flagging it, not diagnosing it.

---

## PART 3 — THE RULINGS

Bucket key: M = SAP mirror · F = SAP feeder · N = native, never in SAP · X = external ·
U = undetermined.

### HR — TankhaPay

| # | Entity | Bucket | Conf | One-line reason |
|---|---|:--:|---:|---|
| 1 | Employee master (profile, KYC, Aadhaar/PAN, bank, UAN/ESIC, family, education, documents, exit) | **N** | 98 | 1,795 people vs 33 hollow `OHEM` stubs; no HR UDT, no HR user field beyond an emp-code tag |
| 2 | Attendance, biometric punches, shifts, breaks, GPS live-tracking & km | **N** | 99 | zero tables matching ATTEND/PUNCH/SHIFT/BIOMET in any JIVO schema |
| 3 | Leave applications, balances, policies, holidays | **N** | 98 | zero `%LEAVE%` tables; no UDT |
| 4 | Payroll run + per-employee payout, earnings/deductions, PF/ESI/TDS per head | **N** | 96 | SAP's `5630001` is 74 lines/month by department, no employee dimension |
| 5 | **Monthly salary & statutory COST by department/budget head** | **M** | 97 | this is a SAP fact (`5630001` + `2161001-12` + EPF/ESIC/TDS/gratuity accounts), not a TankhaPay one |
| 6 | **Employee imprest / advance LEDGER (balances, movements)** | **M** | 96 | 402 employee GL accounts + 510 employee BP cards + `REPORT_EMP_IMP` procedure |
| 7 | Imprest *applications & approval trail* | **N** | 92 | the request/approval side has no SAP object; only the settled balance lands in SAP |
| 8 | Reimbursement claims, travel expenses, meal vouchers, approval hierarchy | **N** | 94 | no SAP object; `OCLG`/approval-for-expense is 0 rows |
| 9 | Recruitment / ATS: candidates, offers, pre-joining docs | **N** | 97 | no SAP candidate concept |
| 10 | Training / LMS / PMS appraisal (separate `tnd` backend) | **N** | 96 | fourth backend, no SAP counterpart |
| 11 | HR masters & config (shifts, grades, designations, rates, geo-fences), org units, roles | **N** | 95 | app configuration; `OUSR` is SAP licence users, a different population |
| 12 | Contract-labour daily headcount & compliance; employee-issued assets/uniform | **N** | 90 | `@ZIA_ASSET_ISSUE_I/O` exist in SAP and hold **0 rows**; contractor *payments* land as ordinary vendor A/P |
| 13 | Employee tax regime, rent/home-loan declarations, investment proofs, Form 16 | **N** | 94 | declarations have no SAP object; `2133004 TDS ON SALARY` holds only the payable total |
| 14 | Visitor gate log, broadcasts/campaigns, help-desk tickets | **N** | 96 | `OCLG`=0, `OSCL`=0 in all three companies |
| 15 | HR reports & dashboards (46 + 7 commands) | **N** | 93 | derived from the native data above |

### Marketplace & external

| # | Entity | Bucket | Conf | One-line reason |
|---|---|:--:|---:|---|
| 16 | Marketplace secondary sell-out (dark-store/store-level: `swiggySec` 634k, `blinkitSec`, `zeptoSec` …) | **X** | 98 | platform-reported; SAP has no store dimension and stops at the distributor |
| 17 | Platform inventory SOH / DOH (179k live rows to 2026-07-29) | **X** | 96 | stock inside the platform's warehouses; SAP's `OITW` is JIVO's own 36 Mart warehouses |
| 18 | Marketplace purchase orders (BigBasket/Flipkart Grocery/Zomato/CityMall + Zepto/Blinkit/Swiggy) | **X** | 97 | 40,977 + 8,848 POs raised on JIVO's **distributors**, not on JIVO |
| 19 | Amazon Vendor Central POs (`reporting."Amazon PO"`, 470k staged rows) | **X** | 96 | Amazon-originated; `sap_sku_code` is a lookup, not provenance |
| 20 | Amazon B2C consumer GST invoices (`amazon_mp`) | **X** | 88 | Amazon-generated under JIVO Mart's own GSTIN; SAP books a smaller, coarser A/R — see the ₹60 L gap |
| 21 | Ads campaign performance & spend detail (Amazon/Flipkart/Blinkit/Zepto/Swiggy/BigBasket/Meta) | **X** | 96 | campaign/keyword/impression/ROI has no SAP object |
| 22 | **Advertising & platform-charge MONEY** | **M** | 95 | Facebook 268 A/P invoices, Google 21, Amazon Seller Services 207 (₹5.57 cr), Flipkart 162, Zepto 36, Swiggy 26, Blink 19 — all in SAP `OPCH` |
| 23 | Brand fund / trade-spend attribution by city/SKU/offer | **X** | 90 | per-SKU attribution is platform data; the net is inside the platform's A/P invoice or an `ORIN` credit note |
| 24 | Coupons & promotions (clips, redemptions, budget burn) | **X** | 93 | no SAP coupon object; net discount rides inside Amazon Seller Services A/P |
| 25 | Delivery appointments, slot booking, GRN short-supply, scorecard, fill-rate | **X** | 96 | `%APPOINT%` returns nothing in SAP; these are platform dock operations |
| 26 | Competitor & own price/availability scrapes per pincode (`jivo-desk`, 10 platforms, files fresh to Jul-29) | **X** | 97 | SAP has no price-observation object of any kind |
| 27 | Blinkit portal: PO, GRN, appointments, invoices, charges, UTR settlements, offers, assortment, SOH, scorecard | **X** | 95 | single host `partnersbiz.com`, 0 SAP references in code; no Blinkit A/R in SAP |
| 28 | Zepto portal: PO, ASN, RTV, catalog health, stock, invoicing, contracts, payments, ledger, receivables, FBZ, ads, KYC | **X** | 95 | seven `zepto.co.in` hosts, 0 SAP references |
| 29 | **Marketplace counterparty ledgers & balances (A/R + A/P with every platform and distributor)** | **M** | 98 | 25/29/22 platform BP cards with live balances; this is the book |
| 30 | Pincode ↔ city ↔ state master + platform city universe | **N** | 93 | no `%PINCODE%` table in SAP; SAP has `ZipCode` on 11,945/12,861 customer addresses but no reference master |
| 31 | Sales targets, landing rates, realisation/margin model | **N** | 95 | `@BUDGET`/`@BUDGET1` hold 1 row each and are a **cost** budget; no `%TARGET%` table |
| 32 | SKU bridge (`master_sheet`, `master.product_master`, `Ecommerce.Mapping_skumapping`) | **N** | 94 | the mapping and commercial overlay are JIVO-authored; only `ItemCode` is SAP's |
| 33 | `product-identity` released map (platform:listing_id ↔ company:schema:item_code) | **U** | 95 | not a data source — attested join-key infrastructure; M/F/N/X do not apply |
| 34 | Shipment planning, truck loads, driver/vehicle, approvals & rejections (ecom module) | **N** | 92 | no SAP transport-planning or approval object for this |
| 35 | DOH alerts, upload/validation audit trail, chatbot, ecom app users & permissions | **N** | 95 | pure workflow/app state |
| 36 | `test_supabase.oitm_master` (SAP OITM copy) | **M — DEAD** | 97 | 2,014 rows all written in a 1.6-second batch on 2026-01-07, never refreshed; its `onhand` is January stock |
| 37 | `test_supabase.sustain_dist` (primary offtake to Sustainquest) | **U** | 55 | fails reconciliation against SAP — see below |
| 38 | JIVO-owned e-commerce / FBF / dropship warehouse stock | **M** | 92 | `DL-EC`, `FBF-HR`, `KT-FBF`, `GP-ECM`, `BH-FK`, `DP-*` are real SAP warehouses with real `OITW` stock |

---

## PART 4 — DISAGREEMENTS I RESOLVED

**1. "SAP sees Amazon's settlement, never the end-consumer invoice."**
(ecom-cli mapper, X @ 96.) **Bucket stands, rationale is wrong.** SAP `JIVO_MART_HANADB`
holds 2,575 A/R invoices against `CUSTA000912 AMAZON (B2C)`, live to 2026-07-29, some
as small as ₹299 — consumer-grain. What SAP lacks is the buyer, the ASIN, the IRN and
about 75% of the value. I also proved the seller of record on `amazon_mp` is JIVO Mart's
own Delhi GSTIN, not a third party. Bucket X (Amazon originates the row); the "never
sees" claim is retired.

**2. "SAP has no ad-spend object at all… at best a lump marketing expense JE."**
(ecom-cli, X @ 97.) **Split.** Campaign detail is X. But the **money is fully in SAP as
purchase invoices**: Facebook India 268 invoices, Google India 21, Amazon Seller
Services 207 (₹5.57 cr), Flipkart Internet 162 (₹2.63 cr), Zepto 36, Swiggy 26,
Blink 19 — all live into 2026. Anyone answering "what did we spend on ads" should go to
SAP, not to `amazon_ads`.

**3. "The invoice JIVO raises against a Blinkit PO is in SAP as an OINV/ORDR row."**
(portals+postsql, stated as fact.) **False for Oil and Mart.** There is no Blink
Commerce customer invoice in either; Blink Commerce is a **vendor** (19 A/P invoices).
Only Beverages has a `BLINK` customer, with 6 invoices totalling ₹2.05 L. Blinkit POs
are raised on ANTIZE / EVARA / CHIRAG / KNOWTABLE and, for 2,721 of them, on JIVO MART —
yet even those produce no Blinkit A/R in SAP. Corrected.

**4. `sustain_dist` = M @ 90.** (ecom-cli.) **Downgraded to U @ 55.** The phase-1
argument was "sap_code values are SAP ItemCodes" — the exact join-key trap. I ran the
reconciliation: `sustain_dist` holds 42 rows, all dated 2026-06-01, totalling
**₹2,58,93,572 / 71,880 units**. SAP `JIVO_MART_HANADB` invoices to `CUSTA000907
SUSTAINQUEST` in June 2026: **24 invoices, 18 items, 49 lines, ₹4,05,68,156 net of GST,
138,814 units**. Value 64%, quantity 52%. It is either a filtered subset or an
independently-reported figure, and I could not find the loader. Do not quote it as
either JIVO's primary sales or Sustainquest's offtake.

**5. TankhaPay payouts N @ 85, "if you insist on a bucket for the monthly salary GL
total it is a manual F."** **Resolved by splitting the entity.** Employee-level payroll
is N at 96 (SAP's salary expense has a department dimension and no employee dimension —
74 lines for 593 people). The monthly departmental cost is a separate **M** entity that
lives in SAP and nowhere else. There is no F because there is no automated posting and
no reference in either direction; the accountant types it.

**6. "SAP holds employee IMPREST vendor accounts" (mentioned in passing).**
**Upgraded and quantified.** 510 `OCRD` cards + **402 named `OACT` GL advance accounts**
+ a purpose-built cross-company ledger procedure `REPORT_EMP_IMP` over account 2110003.
The employee *money* trail in SAP is substantially richer than any phase-1 map said.

---

## PART 5 — OPEN QUESTIONS

1. **The ₹60 lakh/month Amazon B2C gap.** Amazon's own invoice feed under JIVO Mart's
   Delhi GSTIN says ₹81.05 L for May 2026; SAP's Amazon B2C A/R says ₹20.52 L. Could be
   another BP, a period cut, returns netting, or a genuine under-booking. Needs an
   accountant, not another agent.
2. **`sustain_dist` provenance.** 64% of the SAP value, 52% of the quantity, one month
   only, loader unknown.
3. **Four competing employee stores.** TankhaPay 1,795 · DSR `tbl_salesperson` 1,809 ·
   JSAP `hierarchy flat` 227 (with salary and `JWPL` codes) · SAP 402 GL + 510 BP
   accounts keyed on `JWPL####`. The `JWPL` code is the natural join key and it appears
   in SAP, JSAP and (presumably) TankhaPay — nobody has reconciled them. Whoever owns
   "how many people work here" needs to.
4. **Two attendance systems.** TankhaPay biometric/geo punches for 593 employees, and
   DSR's 426,055 GPS+selfie punches for 1,809 field staff. Neither is in SAP; whether
   they overlap on the same humans is unchecked.
5. **Two SKU bridges.** `product-identity/v1` (attested, 333 listing resolutions) and
   `Ecommerce.Mapping_skumapping` (587 rows). Nothing reconciles them.
6. **`brands.blinkit.com` ads portal** is documented in `portals/blinkit/vault/ads/`
   but is **not wired into any CLI**. Blinkit ad spend has no command surface — though
   the money is in SAP as `VENDA000849` A/P.
7. **`R K WORLDINFOCOM PVT LTD` (CUSTA000048)** is JIVO Mart's largest e-commerce
   customer this FY at ₹31.0 cr / 505 invoices, and it does not appear as a vendor on
   any marketplace PO in the ecom warehouse. Unexplained.

## PART 6 — WHAT I DID NOT DO

- **Blinkit and Zepto portals: no live calls.** Both need a fresh OTP. My evidence is
  code (I grepped the base URLs and confirmed zero SAP references myself) plus the live
  SAP counterparty and A/P checks. For an X-by-definition ruling I judged that
  sufficient; if someone wants row-level proof, log in.
- **TankhaPay: `doctor` + the dashboard read succeeded live.** Six other read commands
  returned `TP-400 "Some parameters missing"` / `"Missing Customer Account Id"` — the
  CLI's auto-context does not inject `customerAccountId`. So I have live employee
  *counts* but not a live punch row or payout row. The N rulings do not depend on that:
  they rest on SAP's proven absence, which I verified myself.
- **JSAP session was expired** (`"User not logged in"`), so the 227-person hierarchy
  cross-reference is carried from the phase-1 jsap agent's live read, not mine.
- I did not attempt the SAP Service Layer. HANA direct SQL is the stronger evidence and
  the sap-surface probe already proved the two agree exactly on all five entities it
  tested.
- **Read-only compliance:** every HANA statement was a `SELECT`; every Postgres query
  ran inside `postsql`'s enforced READ ONLY transaction; every TankhaPay call was one of
  the CLI's 297 wired reads. No credential is printed anywhere in this document.
