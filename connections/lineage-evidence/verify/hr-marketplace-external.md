# ADVERSARIAL VERIFICATION — domain `hr-marketplace-external`

Refuter pass, 2026-07-30. Every number below was pulled live by me, not inherited.

Tools actually used:
```
/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql -env /Users/damanpreetsingh/jivo-cli/connections/hana-tunnel.env "<SQL>"
/Users/damanpreetsingh/jivo-cli/postsql/postsql query -d <db> "<SQL>"
```
HANA tunnel `127.0.0.1:13015` — OPEN, used throughout. Postgres cluster — OPEN.
TankhaPay portal — NOT reached (no built binary, OTP login required). The SAP side of every
HR ruling is live; the app side is inherited. Said plainly rather than dressed up.

---

## HEADLINE IS WRONG — and it contradicts its own ruling body

> "JIVO's SAP does not sell to Blinkit, Zepto, Swiggy or BigBasket at all"

**REFUTED.** BigBasket's legal entity is INNOVATIVE RETAIL CONCEPTS PVT LTD and it is a
JIVO SAP customer, tagged `U_Chain='BIG BASKET'`, `U_Main_Group='E-COMMERCE'`:

| Company | CardCode | Invoices (not cancelled) | Net of GST | Span |
|---|---|---|---|---|
| Oil | CUSTA000496 | **206** | **Rs 2.61 cr** | 2024-09-30 → 2026-02-28 |
| Mart | CUSTA000496 | **65** | **Rs 1.39 cr** | 2024-12-31 → 2026-01-13 |
| Mart | CUSTA000722 KIRANAKART (Zepto) | **237** | **Rs 4.91 cr** | 2024-12-31 → 2026-06-18 |
| Bev | CUSTA001135 BLINK | 6 | Rs 0.39 L | 2026-04-02 → 2026-07-16 |

Oil's BigBasket A/R since 2025-04-01 alone is 86 invoices / Rs 121.93 lakh. Only **Swiggy**
(BUNDL / SWIGGY INSTAMART, vendor-only) matches the headline. The ruling body's own
marketplace-ledger entity lists KIRANAKART 237 and BIGBASKET 65 — the headline contradicts it.

```sql
SELECT C."CardCode",C."CardName",COUNT(*),SUM(I."DocTotal"-I."VatSum")
FROM "JIVO_OIL_HANADB"."OINV" I JOIN "JIVO_OIL_HANADB"."OCRD" C ON I."CardCode"=C."CardCode"
WHERE UPPER(C."CardName") LIKE '%INNOVATIVE RETAIL%' AND I."CANCELED"='N' GROUP BY 1,2;
```

Second headline error: "40,977 q-commerce POs are raised on seven distributor companies."
Live grouping of `test_supabase.total_po_zbs` by `vendor_name` shows **3,635 of 40,977 (8.9%)
name JIVO MART PRIVATE LIMITED itself** — a JIVO company, not a distributor.

---

## THE THREE REAL REFUTATIONS

### 1. SAP holds the imprest/reimbursement APPLICATION and its APPROVER — as attachments

The brief warned about the ~202k-attachment vector. Nobody in phase 2 checked it. I did.

`ATC1` attachment-name sweep, by company:

| Keyword | Oil | Mart | Bev |
|---|---|---|---|
| IMPREST | **239** | 45 | 97 |
| SALAR* | **139** | 14 | 41 |
| ATTEND* | 26 | 20 | 11 |
| JWPL#### | 72 | 5 | 5 |
| CLAIM | **785** | 132 | 27 |
| EXPENSE | **1,766** | 801 | 48 |
| CONVEY* | 171 | 5 | 43 |
| TRAVEL | 106 | 1 | 2 |
| REIMB* | 38 | 2 | 2 |
| AADHA* | 25 | – | – |

Where they hang (Oil): **OVPM (outgoing payments) 274**, ODRF 58, OJDT 5. Joining employee
BP cards to their payments:

```sql
SELECT COUNT(*) , COUNT(V."AtcEntry") FROM "JIVO_OIL_HANADB"."OVPM" V
JOIN "JIVO_OIL_HANADB"."OCRD" C ON V."CardCode"=C."CardCode"
WHERE C."U_Emp_Code" IS NOT NULL AND C."U_Emp_Code"<>'';
-- 3,138 employee payments, 1,923 of them carry an attachment
-- 2,458 ATC1 lines across 263 distinct employees
```

Actual filenames (Oil, most recent first):
- `Jivo Wellness Mail - Re_ Request for Advance Salary Approval – Hardeep (Driver) 5.5.26`
- `Jivo Wellness Mail - Re_ Advance of Rs. 15000 to Tanjim against Salary Arrear (Jan-2026)`
- `Jivo Wellness Mail - Fwd_ Request for Approval of Attendance Arrears – November`
- `Jivo Wellness Mail - Fwd_ PRABJOT (RONAK ) ATTENDANCE`
- `Neha April Conveyance` · `Sachin Stephen april conveyance` · `CLOSING CONVEYANCE OF TANNU OF APRIL MONTH`
- `Jivo Wellness Mail - Approval Request for AAHAR Expenses Reimbursement`

So the ruling's claim that SAP holds "only the netted balance, never the application, the
approver or the rejection" is **false**. The requested amount, the purpose, the named employee
and the approving manager are in SAP — as PDF documents attached to the payment, not as
queryable columns. **Caveat the reader must keep:** the file bytes live on the Windows share;
HANA holds the metadata row + link. And the threads are Gmail print-outs, so I cannot prove
they originate in TankhaPay rather than a parallel email process. That is why I put these at
F/~70 and not higher.

### 2. Employee BANK details ARE in SAP

The employee-master ruling lists "bank account" under `fields_sap_lacks`. Wrong:

```sql
SELECT COUNT(*), COUNT("U_Account_Number"), COUNT("U_Bank_Name"), COUNT("U_IFSC")
FROM "JIVO_OIL_HANADB"."OACT" WHERE "U_Emp_Code" IS NOT NULL AND "U_Emp_Code"<>'';
-- 402 employee GL accounts | 242 account numbers | 231 bank names | 242 IFSC codes
```

What SAP genuinely lacks on those 510 employee BP cards: PAN/GSTIN 0/510, e-mail 0/510,
phone 2/510. So the *bucket* N for the employee master survives — but "SAP has no bank
details for your staff" would have been a wrong statement to act on.

Also: the ruling says "HEM1–HEM10 all 0". **HEM10 = 46 rows (Oil), 36 (Bev)** — it is the
employee-to-branch map (`empID, BPLId`). Trivial, but it was asserted as zero and is not.

### 3. The "Rs 60 lakh Amazon gap" does not exist — it is a text-sort artifact

`amazon_mp.invoice_date` is **text**, in `dd/MM/yy HH:mm` (plus 1,623 rows in ISO form). A
`>= '2026-05-01'` filter matches nothing and `MIN/MAX` sorts lexically, which is how the whole
table's 6,506 invoices / Rs 81.05 L got attributed to May-2026.

Parsed properly:

```sql
SELECT split_part(split_part(invoice_date,'/',3),' ',1) yy, split_part(invoice_date,'/',2) mm,
       COUNT(DISTINCT invoice_number) inv, ROUND(SUM(NULLIF(invoice_amount,'')::numeric),0) amt
FROM amazon_mp GROUP BY 1,2 ORDER BY 1,2;
```

| Month | amazon_mp invoices | amazon_mp value | SAP CUSTA000912 invoices | SAP gross |
|---|---|---|---|---|
| Apr-26 | 1,257 (ISO-format bucket) | Rs 15.38 L | 98 | Rs 15.17 L |
| **May-26** | **1,558** | **Rs 20.95 L** | **187** | **Rs 20.52 L** |
| Jun-26 | 2,017 | Rs 25.93 L | 341 | Rs 39.45 L |
| Jul-26 | 1,700 | Rs 19.05 L | 91 | Rs 12.67 L |

May ties to **2.1%**, April to 1.4%. June/July swing both ways, consistent with the
deliveries-basis period cut visible in SAP's own comment (`AMAZON HARYANA 15 TO 27 JULY Based
On Deliveries`). The real finding is a **grain** difference (1,558 consumer invoices booked as
187 consolidated A/R documents), not a Rs 60 lakh hole. Also: Mart has **three** Amazon
customer cards — CUSTA000873 AMAZON (503 invoices), CUSTA000883 AMAZON B2C, CUSTA000912
AMAZON (B2C -MAY-JULY). The ruling used only the third.

---

## FOURTH FINDING — SAP's real budget module was missed entirely

The sales-targets ruling says SAP's only budget object is a 1-row `@BUDGET` UDT. It checked
the UDT and not the module:

| Table | Oil | Mart | Bev |
|---|---|---|---|
| OBGT (budget header) | **164** | 0 | **175** |
| OBGS (budget scenario) | **267** | 1 | **186** |
| BGT1 (budget lines) | **1,968** | 0 | **2,100** |
| OBGD | 1 | 3 | 3 |

Content is a **GL cost budget by financial year**: SALARY EXPENSE, FREIGHT & CARTAGE OUTWARD,
SECURITY EXPENSES, BUSINESS PROMOTION, ADVERTISEMENT, INTEREST ON BANK LOAN. FY2024-04-01 72
rows, FY2025-04-01 88 rows, FY2026-04-01 only 4 rows. Several values are obvious keyboard
mash (Rs 5,555 cr on freight, `1111111110` on security) — same junk-entry pattern as
`U_OMS_Order_No`.

Bucket verdict is unchanged (a GL cost budget is not a sales target in litres, and there is no
realisation waterfall) — but "SAP has no budget object with content" is false and would
mislead anyone building budget-vs-actual.

---

## FIFTH FINDING — the ecom shipment module is 1 row, not 58

```sql
SELECT (SELECT COUNT(*) FROM shipments), (SELECT COUNT(*) FROM shipment_items),
       (SELECT COUNT(*) FROM truck_dispatches), (SELECT COUNT(*) FROM sp_shipments),
       (SELECT COUNT(*) FROM sp_audit_log);
-- shipments 1 | shipment_items 58 | truck_dispatches 1 | sp_shipments 0 | sp_audit_log 0
```
The "58 shipment rows" is `shipment_items`. There is exactly **one** shipment header in the
whole module and the audit log is empty. N@92 is not supportable on one row.

---

## WHAT SURVIVED — the N-hunt came up empty everywhere else

Independent sweeps I ran (not inherited), all three schemas, `M_TABLES` incl. `@`UDTs:

- **Wide HR sweep** (`%EMP% %HR% %STAFF% %SAL% %PAY% %MUSTER% %OVERTIME% %HOLIDAY% %APPRAIS%
  %CANDID% %RECRUIT% %TRAIN% %CLAIM% %REIMB% %TRAVEL% %VISITOR% %TICKET% %IMPREST% %AADHA%
  %UAN% %GRATUITY%`) → every hit is a SAP/Crystal temp table at **0 rows**, plus the unrelated
  SALES_ANALYSIS cache. **No HR object exists.**
- **SAP standard HR objects**: OHEM 17/1/15 · HEM1–HEM7 all 0 · HEM10 46/0/36 · OHTR 0 ·
  OHPS 1/0/0 · OHST 0 · ODPT 0 · OPOS 0 · OCLG 0 · OSCL 0 (all three companies).
- **Marketplace sweep** (`%COUPON% %CAMPAIGN% %MARKETPLACE% %DARKSTORE% %APPOINT% %SCRAPE%
  %ASIN% %LISTING% %BRANDFUND% %SOH% %BLINK% %ZEPTO% %SWIGGY% %AMAZON% %FLIPKART%`) →
  **zero rows returned.** Every X ruling survives on the SAP-absence leg.
- **Pincode sweep** (`%PIN% %ZIP% %POSTAL% %CITY% %GEO%`) → nothing but ES metadata.
- **Full populated-custom-table census** → 53 tables, all approval/WhatsApp/portal/report-cache.
  Nothing HR, nothing marketplace.

Payroll grain, re-derived independently:
```sql
SELECT COUNT(*), COUNT(DISTINCT "ShortName"), MIN("RefDate"), MAX("RefDate")
FROM "JIVO_OIL_HANADB"."JDT1" WHERE "Account"='5630001';
-- 1,648 lines | 1 distinct ShortName (the account itself) | 2024-09-30 → 2026-06-30
```
Only **25 of 1,648** salary lines carry an employee-keyed contra account (15 employees). The
employee dimension lives on the *advance* side, not payroll: **2,041 JDT1 lines against 317
named employee GL accounts, live to 2026-07-23**. The ruling's own falsifier is technically
tripped but at a scale that does not move the bucket.

Verified exactly, digit for digit:
- OACT 1,424 / 402 `U_Emp_Code`; OCRD 3,390 / 510 `U_Emp_Code`; `REPORT_EMP_IMP` exists
  (Oil schema only — the ruling called it "cross-company", the *procedure* is not).
- `@ZIA_ASSET_ISSUE_I` and `_O` both exist, both **0 rows**.
- Mart OWHS = 36 warehouses, every one JIVO's own. DL-EC 98 items/34,250 units · GP-ECM
  6/7,125 · FBF-HR 27/3,257 · KT-FBF 23/307.
- oitm_master 2,014 rows, created_at min 2026-01-07 12:19:40.738793 max 12:19:42.357158 —
  one 1.6-second batch, dead 204 days.
- sustain_dist 42 rows, all 2026-06-01, Rs 2,58,93,571.63 vs SAP Sustainquest Jun-26
  24 invoices / Rs 4,05,68,157.20 net = 63.8%. The U@55 downgrade is correct.
- blinkit_inventory 37,933 · zepto_inventory 47,781 · swiggy_inventory 93,487 ·
  amazon_ads 85,985 · blinkit_brandfund 1,521 · amazon_coupon 2,171 ·
  master_sheet 834 · total_po 8,848 · total_po_zbs 40,977 · Mapping_skumapping 587.
- Ad/platform A/P (my counts vs ruling's): AMAZON SELLER SERVICES 213 vs 207 · FLIPKART
  INTERNET 164 vs 162 · ZEPTO 38 vs 36 · SWIGGY 28 vs 26 · BLINK 19 vs 19 · FACEBOOK 268 Oil
  **+ 58 Mart** (ruling missed the Mart leg) · GOOGLE 21 Oil + 2 Mart. Bucket M confirmed.
- TankhaPay CLI `config.go`: four backends, all `*.tankhapay.com`. Zero SAP/HANA/OINV/OCRD
  references in the CLI source. No push path exists on the app side.

One number I could not reproduce: the ruling's "R K WORLDINFOCOM Rs 31.0 cr across 505
invoices" for FY2026. I measure **1,296 invoices / Rs 93.6 cr gross** since 2025-04-01
(1,399 / Rs 100.8 cr all-time). Bucket unaffected; the figure is not one to quote.

---

## Unreachable / not attempted

- TankhaPay portal (no binary, OTP). Every HR ruling's app half stays inherited.
- Blinkit / Zepto seller portals (OTP). Their SAP halves I verified independently.
- The VPS scrape files behind the price-scrape ruling. SAP-absence leg verified; freshness not.
- `product-identity` released map — I did no work on it at all.
