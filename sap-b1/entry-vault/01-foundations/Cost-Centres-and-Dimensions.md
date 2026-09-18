---
type: foundation
sap_tables: [OPRC, ODIM, PCH1, PDN1, POR1, RPC1, RIN1, INV1, DRF1, JDT1, BTF1, VPM4, OACT, tbl_Draft_Approvals]
objtype: [13, 14, 15, 16, 18, 19, 20, 21, 22, 30, 46, 112]
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Cost centres and dimensions — the five codes on every expense line

> SAP calls them dimensions. At JIVO they are the five little columns at the right of
> every document line, and on an **expense** line three of the five are compulsory, a
> fourth is conditional and the fifth is customary. Get one wrong and the document
> either bounces at Add with a red message, or posts and quietly lands in the wrong
> manager's budget — waiting on a signature from someone who never expected it.

## The short version

1. JIVO uses **all five** SAP dimensions and has renamed every one. In order:
   **1 Variety · 2 Effective Month · 3 Budget · 4 Sub Budget · 5 State.**
   Same five names, same order, in all three books — *measured*, `ODIM` in each schema.
2. They matter **only on lines posted to a 5xxxxxx expense account** (`OACT.GroupMask=5`).
   Every mandatory check in SAP's own validation procedure is gated on exactly that join.
   On a stock, GST or creditor line the columns are decoration.
3. On an expense line: **Variety, Effective Month and Budget are mandatory. State is
   customary (86–99%). Sub Budget is required only under certain Budget codes.**
4. **Budget is the one that routes approval.** `OPRC.CCOwner` carries a budget owner for
   15 of Oil's 17 Budget codes — no other dimension has an owner. On an *indirect*
   expense the document is refused until that named owner has signed that line.
5. The picklists are **not the same in the three books.** Mart's live Budget list
   (`SUPPLY-C`, `ECOM`, `SERVICES`, `FACTORY`) has almost nothing in common with Oil's
   and Bev's (`Factory`, `FACT_COM`, `Del Bkhp`, `BackOff`). Beverages has 32 of its 80
   Variety codes switched **off**.

Everything below is measured from the live books on 2026-08-24 unless it says *inferred*.

---

## 1. What each dimension is called, and where the value lives

| Dim | JIVO name (`ODIM.DimDesc`) | Document line (HANA) | Journal line (`JDT1`) | Service Layer / `sapb1` | Codes in `OPRC` (Oil/Mart/Bev) |
|---:|---|---|---|---|---|
| 1 | **Variety** | `OcrCode` | `ProfitCode` | `CostingCode` | 88 / 77 / 80 |
| 2 | **Effective Month** | `OcrCode2` | `OcrCode2` | `CostingCode2` | 37 / 37 / 37 |
| 3 | **Budget** | `OcrCode3` | `OcrCode3` | `CostingCode3` | 17 / 19 / 16 |
| 4 | **Sub Budget** | `OcrCode4` | `OcrCode4` | `CostingCode4` | 29 / 31 / 21 |
| 5 | **State** | `OcrCode5` | `OcrCode5` | `CostingCode5` | 28 / 26 / 23 |

*Measured*: `ODIM` (5 rows per book, all `DimActive='Y'`, identical `DimDesc` in all three);
`OPRC` counts from the master pull below. Dimension **1 changes column name in the
journal** — `JDT1.ProfitCode`, not `OcrCode` — which is why a ledger query written
against `OcrCode` silently returns nothing for Variety. The Service Layer / CLI names
are the `CostingCode*` family (*measured* from the working payloads in
[[ap-rm-pm]] / `.claude/skills/ap-rm-pm/`).

`OPRC` also carries `ValidFrom` / `ValidTo` / `Active` / `Locked`. Five rows —
`Centr_z`, `Centr_z2` … `Centr_z5`, "General Center *n*" — are SAP's own placeholders,
`Locked='Y'`, one per dimension. **Never pick a `Centr_z*` code.** Subtracting those and
the inactive rows gives the real picklist size: Oil 193, Mart 183, Bev 140.

---

## 2. Mandatory or not — measured, per document type

### 2a. The rule SAP actually enforces

Every "Please select …" check in `SBO_SP_TRANSACTIONNOTIFICATION` (read live from
`SYS.PROCEDURES`, 4.78 lakh characters in Oil) has the same shape:

```
Inner Join OACT B On A."AcctCode" = B."AcctCode"  Where B."GroupMask" = 5
```

`GroupMask=5` is the **expenditure** block of the chart of accounts — all 264 postable
`5xxxxxx` accounts in Oil. So: *dimensions are compulsory on expense lines and on
nothing else.* This is a code reading, and the books agree with it exactly.

**Oil A/P invoice lines, last 365 days, by account group** — the fill rates that prove it:

| Account group (`GroupMask`) | Lines | Variety | Eff. Month | Budget | Sub Budget | State |
|---|---:|---:|---:|---:|---:|---:|
| **5 — expenditure** | 13,910 | **100%** | **100%** | **100%** | 32% | 86% |
| 2 — liabilities (creditors, GST) | 3,397 | 100% | 19% | 16% | <1% | 5% |
| 1 — assets (stock, prepaid) | 1,598 | 99% | 49% | 32% | 3% | 44% |
| 4 — revenue (branch transfer) | 624 | 100% | 1% | <1% | 0% | 1% |

Same cut, other two books:

| Book | Expense lines | Variety | Eff. Month | Budget | Sub Budget | State |
|---|---:|---:|---:|---:|---:|---:|
| Oil | 13,910 | 100% | 100% | 100% | 32% | 86% |
| Mart | 4,325 | 100% | 100% | **95%** | 68% | 74% |
| Bev | 4,981 | 100% | 100% | 100% | **4%** | 99% |

**Variety is ~100% on every account group**, not just expense — in practice it is
mandatory on every A/P line whatever the account.

### 2b. Which document types carry dimensions at all

Fill rate on the line table, all history / last 120 days, from the corpus profiles
(`_data/profile-*.md`). Dash = never used in that book.

| Document | Line table | Variety (O/M/B) | Eff. Month | Budget | Sub Budget | State |
|---|---|---|---|---|---|---|
| [[AP-Invoice]] | `PCH1` | 96/99/99% | 74/35/90% | 70/34/89% | 21/14/4% | 66/24/90% |
| [[GRPO]] | `PDN1` | 95/100/98% | 59/3/84% | 57/3/84% | 10/1/<1% | 51/1/83% |
| [[Purchase-Order]] | `POR1` | 79/98/88% | 63/1/81% | 61/1/81% | 16/<1/<1% | 51/—/78% |
| [[AP-Credit-Memo]] | `RPC1` | 99/95/98% | 92/34/95% | 90/34/95% | 23/11/<1% | 66/19/96% |
| [[Document-Drafts]] (any type) | `DRF1` | 79/94/82% | 24/10/36% | 23/9/35% | 6/4/1% | 22/6/35% |
| [[Journal-Entry]] (manual + auto) | `JDT1` | 29/45/26% | 10/3/9% | 8/2/8% | 5/<1/2% | 6/1/7% |
| [[Journal-Voucher]] | `BTF1` | 75/56/59% | 76/58/60% | 69/42/56% | 50/17/30% | 60/22/52% |
| [[AR-Credit-Memo]] | `RIN1` | 91/99/89% | 13/4/19% | 11/<1/19% | 10/<1/18% | 8/<1/<1% |
| [[AR-Invoice]] | `INV1` | 89/100/98% | <1/<1/1% | — | — | — |
| [[Delivery]] | `DLN1` | 100/100/96% | —/<1/23% | — | — | — |
| [[Sales-Order]] | `RDR1` | 100/100/98% | <1/—/— | — | — | — |
| [[AR-Return]] | `RDN1` | 99/100/99% | 2/—/3% | —/—/<1% | —/—/<1% | —/—/<1% |
| [[Stock-Transfer]] | `WTR1` | 50/68/22% | <1% | <1% | — | <1% |
| [[Goods-Receipt]] | `IGN1` | 51/5/12% | <1% | <1% | — | <1% |
| [[Goods-Issue]] | `IGE1` | 72/9/2% | <1% | <1% | — | <1% |
| [[Production-Order]] | `WOR1` | 5/6/<1% | <1% | <1% | — | <1% |
| [[Landed-Costs]] | `IPF1` | 97% (Oil) | 58% | 54% | — | 32% |

Read it as: **sales-side documents carry Variety only.** Purchase-side and journal
documents carry all five. Stock movements and production carry almost nothing.

### 2c. What reaches the ledger

Dimensions are copied to `JDT1` only for the lines that had them, so the journal of an
A/P invoice shows them on roughly the expense quarter of its lines. From the corpus
`gl-*.md` files ("Dimensions carried on the lines", 365-day window):

| Journal origin | Book | Variety | Eff. Month | Budget | Sub Budget | State |
|---|---|---:|---:|---:|---:|---:|
| 18 A/P Invoice | Oil | 26% | 25% | 25% | 8% | 23% |
| 18 A/P Invoice | Mart | 15% | 15% | 15% | 11% | 9% |
| 18 A/P Invoice | Bev | 29% | 28% | 28% | 3% | 28% |
| **30 Manual JE** | **Oil** | **69%** | **66%** | **55%** | **35%** | **40%** |
| 30 Manual JE | Mart | 31% | 50% | 37% | 23% | 11% |
| 30 Manual JE | Bev | 55% | 52% | 48% | 14% | 33% |
| 19 A/P Credit Memo | Oil | 33% | 27% | 27% | 3% | 17% |
| 13 A/R Invoice | Oil | 41% | — | — | — | — |
| 20 GRPO | Oil | 44% | 5% | 5% | — | 1% |
| 46 Outgoing Payment | Oil | 24% | 24% | 13% | 12% | — |
| 24 Incoming Payment | Oil | 9% | 9% | — | — | — |
| 67 Stock Transfer | Oil | 5% | — | — | — | — |
| 59/60 Goods Receipt/Issue | Oil | 1% | — | — | — | — |

The **manual journal entry is the most dimension-dense entry at JIVO** — 69% of Oil's
manual-JE lines carry a Variety. That is where a wrong code does the most damage per
line, because there is no base document to check it against.

---

## 3. Every rule SAP will refuse you for

All *measured* by reading `SBO_SP_TRANSACTIONNOTIFICATION` in each schema. The number is
the error code the client shows. `1120xxx` codes fire on a **draft**; the others fire on
the posted document at **Add**.

| Code | Message | Fires when | Objects |
|---|---|---|---|
| `1120008` / `180009` / `200007` / `220003` / `190010` | Please select Variety | expense line, `OcrCode` blank | draft 14/15/18/20 · A/P · GRPO · PO · A/P CN |
| `1120001` / `1800001` / `200001` / `220001` | Please select Expense Effective Month | expense line, `OcrCode2` blank | same |
| **`1120009`** / `180011` / `200009` / `220004` / `190011` / `300004` | **Please select Budget** | expense line, `OcrCode3` blank | draft **14/15/18/19/20** · A/P · GRPO · PO · A/P CN · manual JE |
| `1120010`–`1120013` / `180013`–`1800155` | Please select Sub Budget | Budget is one of four codes and Sub Budget is not in that Budget's allowed list (§5) | draft · A/P · GRPO · PO · A/P CN · JE · JV · payment |
| `200015` / `220010` / `190017` / `210017` / `14000327` / `460012` | Please Select Branch Factory to enter data in "Factory" Budget | `OcrCode3` in (`Factory`,`FACT_COM`) but the header branch `BPLId` ≠ 2 | GRPO · PO · A/P CN · goods return · A/R CN · payment — **not** A/P invoice |
| `1810035` | You are not allowed to select DEl Mayapuri budget | `OcrCode3='Del Mayp'` on an A/P invoice dated after 2025-05-31 | A/P (Oil, Bev) |
| `180047` / `200026` | Select correct G/L for Vehicle | a vehicle Variety code on a service A/P line whose account is not one of `5650002`, `5650015`, `5660005`, `2202201`, `1109002`, `5680002` | A/P · GRPO |
| `1713266` / `150033` / `160015` | Please select the correct Variety | on a sales line the item's `OITM.U_Sub_Group` ≠ `OPRC.PrcName` of the chosen Variety (items in series 389/393/392, account ≠ `1102007`) | SO · Delivery · A/R Return |
| `130024` / `150022` / `200021` | Please Select "BST" in Variety column for Sale Branch Transfer | branch-transfer line (account `1102007`) whose Variety isn't `BST` | A/R Inv (disabled in Oil) · Delivery · GRPO |
| `131002` / `141002` / `181002` | Approval is pending from Budget Owner *<name>* | **indirect** expense line with no signature row — see §6 | A/R Inv · A/R CN · A/P CN (Oil, Bev only) |
| `131529`…`181579` | You Cannot Change Variety / Budget / SUB Budget / State / Effective Month After Approval | any of the five edited after the draft was approved | **Oil only**, objects 13/18/20 |

**Account exemptions from the Budget check** — narrow, and different in each book and at
each stage:

| Where | Exempt accounts |
|---|---|
| Oil **draft** (`1120009`) | `5100018` LAB & TESTING DIRECT EXPENSE |
| Bev **draft** | `5100019` LAB & TESTING DIRECT EXPENSE (also exempt from Effective Month) |
| Mart **draft** | none |
| **Posted A/P invoice**, all three books | **none** |
| Manual JE (`JDT1`), all three books | `5500002` CUSTOM DUTY-IMPORT, `2131002`, `5200012` INTEREST/PENALTY ON CUSTOM DUTY, `2201403` |
| Journal voucher (`BTF1`) | `5500002`, `2131002`, `5200012` |

⚠️ **The draft exemption is a trap.** An Oil draft on `5100018` with no Budget saves
cleanly and then fails when a human presses Add, because `180011` has no exemption.
*Measured from the two procedure bodies; not yet reproduced against a live draft.*

---

## 4. The picklists

`O`/`M`/`B` = the code exists in Oil / Mart / Beverages. `·` = it does not exist in that
book at all. Source: full `OPRC` pull, all three schemas, 566 rows.

### Dim 1 — Variety (the widest, and the worst named)

"Variety" only means an oil variety on a **goods** line. On an expense line the same
column is used for whatever the money is about: a vehicle, a packaging material, a trade
fair. Four families:

**a. Oil / product varieties** — the real ones, used on goods lines and as the default on
indirect expenses:
`BLENDED` `CANOLA` `COCONUT` `COTTONSD` `GHEE` `GROUNDNT` `MUSTARD` `OLIVE` `PAIN OIL`
`PALM OIL` `RICEBRAN` `SESAME`(OM·) `SlICEDOL` `SOYABEAN` `SUNFLOWR` `VEGOIL`(O··)
— all `OMB` unless marked. **In Beverages 32 of these are `Active='N'`** (every oil and
grocery code); Bev's live set is `WATER` `DRINKS` `POWDER` `PULP` `RDY SRP` `READYUNT`
`CAPSULES` plus packaging and vehicles.

**b. Mart / Beverages grocery categories:** `ATTA`(OM·) `CAPSULES`(·MB) `COFFEE` `COINS`
`COSMETIC` `DRINKS`(·MB) `DRY FRTS`(OM·) `DRY FRUT`(·M·) `FLAKES` `GADGETS` `GIFT PK`
`GIFTPK`(··B) `HONEY` `INFINITE` `KITCHEN` `POWDER`(··B) `PULP`(··B) `RDY SRP`(··B)
`READYUNT`(··B) `RICE` `SANITIZR` `SEEDS` `SNACKS` `SOYA CHK` `SPICES` `TEA`(OM·)
`TROLLYBG` `VITAMINS` `WATER`(·MB) `WATRCMPR`

**c. Packaging, WIP and process codes (Oil):** `CAP`(O·B) `CARTON`(OM·) `CLOTHING`(O··)
`COLOR` `LABEL`(O·B) `POUCH`(O··) `TIKKI`(O··) `TIN`(O··) `UNIT TRF`(O··) `WIP`(O··)
`BST` (Sale Branch Transfer — **compulsory** on any line hitting `1102007`)
`2S-4350`(O··)

**d. Vehicles — 35 codes, registration number as the code.** These are the Variety you
pick on a fuel, toll, insurance or vehicle-repair bill:
`CH-7322` `CH-9484` `DL-0939` `DL-1403` `DL-3373` `DL-3721` `DL-4411` `DL-4511`(··B)
`Dl-4511`(OM·) `DL-4708` `DL-6692` `DL-6922` `DL-7501` `DL-7526` `DL-8826` `DL-8873`
`DL-8893` `HP 3568` `HP-2216`(OM·) `HP-3360`(··B) `HP-3659` `HP-3660`(OM·) `HP-4857`(O··)
`HP-8468` `HP-9693`(O··) `HR- 0901`(OM·) `HR-0901`(··B) `HR-3620` `HR-4326` `HR-4548`
`HR-4618` `HR-6098` `HR-7125` `HR-9627` `HR-9959` `HR6791` `PB-0868` `PB-7888`

**e. Events (Oil/Bev):** `AHAAR 25` `AHAAR 26` `SAMAGAM`

**Which Variety do you pick on an expense line?** *Measured*, Oil A/P expense lines,
365 days: `CANOLA` 9,660 of 13,910 (69%) spread over **68 different accounts** including
LEGAL AND PROFESSIONAL, HOUSE KEEPING, TELEPHONE and REFRESHMENT. So in Oil, **`CANOLA`
is the house default for an indirect expense that belongs to no product** — that is an
*inference* from the spread, and the strongest one in this note. Bev's equivalent default
is `WATER` (4,063 of 4,981). Mart's is `CANOLA` (1,832) then `OLIVE`.

### Dim 2 — Effective Month (the easy one)

36 codes, format **`MM-YYYY`**, identical in all three books: `04-2024` through
`03-2027` continuously, plus the locked `Centr_z2`.

**The picklist ends at `03-2027`.** A provision dated in FY 2027-28 has no code to pick
until someone adds one. *Measured* — `MAX(PrcCode)` where `DimCode=2` is `03-2027` in
every book.

Which month? *Measured* on Oil A/P expense lines, 365 days:

| Effective Month equals… | Lines |
|---|---:|
| the month of the posting date (`DocDate`) | 6,974 |
| the **previous** month | 4,379 |
| something else | 2,001 |
| the vendor's invoice month (`TaxDate`) | 556 |

**Rule:** the month the *expense belongs to*, not the month you key it. A September
electricity bill received in October is `09-2026`. That is why "previous month" is the
second-biggest bucket — it is the normal case for a service bill, not an error.

### Dim 3 — Budget — the complete list

All 22 codes that exist anywhere, with a live Oil expense volume (A/P invoice lines,
expense accounts, 365 days) and the owner `empID` from `OPRC.CCOwner`:

| Code | `PrcName` | Books | Oil A/P expense lines | Oil A/P expense ₹ | Owner / co-owner (`empID`) |
|---|---|---|---:|---:|---|
| `Factory` | Factory | O·B | 2,769 | ₹11.19 Cr | 9 / 3 |
| `Sales RE` | Sales Realise | OMB | 742 | ₹8.14 Cr | 18 / 7 |
| `Del Bkhp` | Delivery Bhakharpur | OMB | 4,886 | ₹3.48 Cr | 9 / 18 |
| `BackOff` | Back Office | OMB | 2,627 | ₹1.23 Cr | 12 / 11 |
| `Sales` | Sales | OMB | 707 | ₹1.08 Cr | 7 / — |
| **`FACT_COM`** | **FACTORY COMMON** | OMB | 1,267 | **₹89.04 L** | **9 / —** |
| `OTE` | ONE TIME EXPENSE / One Time Expenses | OMB | 218 | ₹63.18 L | 11 / 17 |
| `NPD2` | NPD2 | OMB | 61 | ₹50.30 L | 2 / 17 |
| `Med MKT` | Media Marketing | OMB | 299 | ₹46.73 L | 6 / 17 |
| `NPD1` | NPD1 | OMB | 87 | ₹24.09 L | 2 / 17 |
| `Transprt` | Transport | O·B | 239 | ₹9.93 L | 22 / — |
| `R & D` | *(name blank)* | O·· | 2 | ₹3.00 L | — / — |
| `Interest` | Interest | OMB | 5 | ₹90,300 | 2 / 5 |
| `Sal CF` | Salary Confidential | OMB | 1 | ₹30,968 | 20 / 17 |
| `NPD3` | NPD3 | OMB | 0 | — | 2 / 17 |
| `Del Mayp` | Delivery Mayapuri | OMB | 0 | — | 4 / 19 — **blocked on A/P after 2025-05-31** |
| `Centr_z3` | General Center 3 | OMB | 0 | — | locked, never pick |
| `FACTORY` | FACTORY | ·M· | Mart: 2 | ₹20,700 | — |
| `ECOM` | ECOM | ·M· | Mart: 992 | ₹2.32 Cr | — |
| `SUPPLY-C` | SUPPLY CHAIN | ·M· | Mart: 2,492 | ₹1.96 Cr | — |
| `SERVICES` | SERVICES | ·M· | Mart: 208 | ₹20.62 L | — |
| `HR/ADMIN` | *(name blank)* | ·M· | 0 | — | — |

Oil counts and amounts are Oil A/P expense lines (`GroupMask=5`), 365 days; the four
Mart-only rows are the same cut in Mart, where `Sales` is the largest bucket at ₹8.35 Cr
over 429 lines and 194 expense lines carry **no** Budget at all (₹4.16 Cr).

Owner IDs, not names — this repo is public. `OPRC` carries an owner on **15 of Oil's 17**
Budget codes and on **none** of dims 1, 2 or 5.

### Dim 4 — Sub Budget

Optional in general (4–68% on expense lines), **compulsory under four Budget codes**
(§5). Full list, `O`/`M`/`B`:

`Accounts`(OMB) `Admin`(OMB) `BankChgs`(OMB) `CAL CNTR`(OM·) `CC Limit`(OMB)
`CIVIL`(O·B) `CSD`(OMB) `DIG MKT`(··B) `DIGTAL M`(OM·) `E-COM`(OMB) `EXPORT`(OMB)
`GP-GDWN`(OM·, GUPTA GODOWN) `GT`(OMB) `HORECA`(OMB) `HR_DEPT`(OMB) `IMPORT`(OMB)
`IT`(OMB) `Legal`(OMB) `MIS`(OM·) `MT`(OMB) `PLANT`(OM·) `POP`(OM·, PAPER MEDIA)
`PPR MED`(··B, PAPER MEDIA) `PVT LOAN`(OM·) `ROI`(OMB) `SC-BHKR`(·M·) `SC-FCTRY`(·M·,
inactive) `SC-WARH`(·M·) `SOCIAL M`(OM·) `TAXATION`(OM·) `TV ADD`(OM·) `Trm Loan`(OMB)
`VHCLLOAN`(OMB) · plus locked `Centr_z4`

### Dim 5 — State

Two-letter code, `PrcName` is the state. 30 codes exist across the books:

| Code | State | Books | | Code | State | Books |
|---|---|---|---|---|---|---|
| `AP` | Andhra Pradesh | OMB | | `KT` | Karnataka | **··B** |
| `AR` | Arunachal Pradesh | OM· | | `MH` | Maharashtra | OMB |
| `AS` | Assam | OMB | | `MP` | Madhya Pradesh | OMB |
| `BH` | Bihar | OMB | | `NG` | Nagaland | O·· |
| `CD` | Chandigarh | OM· | | `OR` | Odisha | OM· |
| `CH` | **Chhattisgarh** | OM· | | `PB` | Punjab | OMB |
| `CN` | Chandigarh | **··B** | | `RJ` | Rajasthan | OMB |
| `DL` | Delhi | OMB | | `TE` | Telangana | OMB |
| `GJ` | Gujarat | OMB | | `TN` | Tamil Nadu | OMB |
| `GO` | Goa | OMB | | `UK` | Uttarakhand | OMB |
| `HP` | Himachal Pradesh | OMB | | `UP` | Uttar Pradesh | OMB |
| `HR` | Haryana | OMB | | `WB` | West Bengal | OMB |
| `JH` | Jharkhand | OMB | | `KN` | Karnataka | OM· |
| `JK` | Jammu & Kashmir | OMB | | `KR` | Karnataka | O·· **inactive** |
| `KE` | Kerala | OMB | | `Centr_z5` | General Center 5 | locked |

**State is not the branch's state.** *Measured* — Oil's FACTORY branch (Haryana) carries
`HR` 4,138 lines but also `DL` 1,462, `PB` 1,077, `UP` 208, `MH` 162 … So dim 5 is the
state the expense *relates to* (the market, the delivery, the office), with the branch's
own state as the modal value. Oil's overall split: `HR` and `DL` first, then `PB`.

---

## 5. Budget → Sub Budget: the machine-checked matrix

Four Budget codes force a Sub Budget, and restrict it to a list. Anything outside the
list — including blank — is refused. *Measured* from the procedure bodies; this is the
**draft** (`DRF1`, object 14/15/18/20) list, which is what a `sapb1 draft` payload hits.

| Budget | Sub Budget must be one of — Oil | Mart | Beverages |
|---|---|---|---|
| `BackOff` | Accounts · Admin · HR_DEPT · **IMPORT** · IT · Legal | Accounts · Admin · HR_DEPT · IT · Legal | Accounts · Admin · HR_DEPT · IMPORT · IT · Legal |
| `Med MKT` | DIGTAL M · POP · **PPR MED** · SOCIAL M · TV ADD | DIGTAL M · POP · SOCIAL M · TV ADD | **DIG MKT** · DIGTAL M · POP · PPR MED · SOCIAL M · TV ADD |
| `Sales`, `Sales RE` | CAL CNTR · CSD · E-COM · **EXPORT** · GT · HORECA · MIS · MT · ROI | CAL CNTR · CSD · E-COM · GT · HORECA · MIS · MT · ROI | CAL CNTR · CSD · E-COM · EXPORT · GT · HORECA · MIS · MT · ROI |
| `Interest` | BankChgs · CC Limit · Trm Loan | BankChgs · CC Limit · Trm Loan | BankChgs · CC Limit · Trm Loan |

Every other Budget code leaves Sub Budget free — which is why Oil's overall Sub Budget
fill is only 32% and Bev's 4%.

The lists **drift by document type as well as by book**: the same procedure carries
slightly different allowed sets for `PCH1`, `PDN1`, `POR1`, `RPC1`, `RIN1`, `JDT1`,
`BTF1`, `VPM4` and `PDF4`. Two examples, *measured*: the Oil `PDN1` (GRPO) `Sales` list
drops `CAL CNTR` and `MIS`; the Oil `JDT1` (manual JE) `Interest` list *adds*
`PVT LOAN`, `TAXATION` and `VHCLLOAN`. **Treat the draft list above as the safe
intersection for a new A/P entry and check the exact one if a send is refused.**

There are also two contradictory-looking `PCH1` variants in Oil (one `BackOff` list with
`IMPORT`, one without). Empirically the permissive one wins: **56 posted Oil A/P lines
carry `BackOff` + `IMPORT`** (27 in 2025, 29 in 2026), so the narrow variant is gated
behind something I did not identify. See Open questions.

---

## 6. What a wrong dimension actually costs

Three distinct costs, in increasing order of how much of your day they take.

**a. A red message at Add.** Blank Variety / Effective Month / Budget on an expense line,
a Sub Budget outside its Budget's list, a `Factory` budget on a non-factory branch, a
`Del Mayp` budget on any A/P invoice. Cheap: you fix it and Add again. On a
draft-and-approve document this costs a re-approval, not a minute.

**b. The wrong person is asked to approve, and the document stops.** This is the
expensive one, and it is code, not opinion. On an **indirect** expense — the line's
account's grandparent is `5600000 INDIRECT EXPENSE` — the procedure does, per line:

```
budget  := <line>.OcrCode3
owner   := OPRC.CCOwner  (→ OHEM.empID)  for that budget code
if no row in tbl_Draft_Approvals for (draftKey, LineNum, ObjType):
      refuse: 'Approval is pending from Budget Owner <owner name> … budget <budget>'
```

So the Budget code you type **chooses the approver**. Pick `Factory` where the paper says
Common and the request goes to `Factory`'s owner+co-owner (empIDs 9 and 3); the correct
`FACT_COM` route is owner 9 alone. The document then waits for a signature from someone
who has no reason to expect it. `tbl_Draft_Approvals` holds 2,081 signature rows over 763
documents in Oil and 7,922 over 2,218 in Beverages. **The table does not exist in Mart**
— Mart has no budget-owner guard at all, and no "cannot change after approval" freeze.

**c. The expense lands in the wrong bucket, permanently.** Dim 3 is the only cut of
JIVO's expenses that maps to a manager, so every Budget-grouped expense report is wrong
by that line's value. The buckets are wildly different sizes — `Factory` is ₹11.19 Cr of
Oil A/P expense a year and `FACT_COM` is ₹89.04 L. A factory bill misfiled from
`FACT_COM` into `Factory` disappears (0.8% of a big number); the same error the other way
would visibly inflate a small one. **And in Oil the five dimensions are frozen once the
draft is approved** (`131529`…`181579`) — after that only a credit memo or a journal
fixes it.

`OBGT`, SAP's own budget table, is **not** where this is compared: 164 rows in Oil, 175
in Bev, **0 in Mart**, keyed by account only over 8 accounts, with no `PrcCode` column at
all. Whatever budget-vs-actual JIVO runs, it is built on `OcrCode3` outside the SAP
budget module. → [[Budget-vs-Actual-Reporting]] (open)

---

## 7. Pre-flight — a factory bill, from the paper

Before you type anything:

1. **Which book?** The GRN header wording decides it ("(BEVERAGE UNIT)" = Beverages).
   Vendor `CardCode`s differ per company for the same GSTIN. → [[Company-Selection]]
2. **Is the line an expense line?** Account starts with `5`. If not, none of the
   dimensions are compulsory — do not invent values to fill them.
3. **Read the handwritten allocation note before opening SAP.** →
   `.claude/skills/ap-rm-pm/reference/handwriting.md`, [[ap-rm-pm]]
4. Then fill, in this order:

| # | Dimension | Where the value comes from |
|---:|---|---|
| 1 | **Variety** | vehicle bill → the vehicle's registration code (and the account must be one of the six vehicle G/Ls) · goods → the item's variety, which must equal `OITM.U_Sub_Group` · branch transfer → `BST` · indirect expense with no product → the book's default (`CANOLA` Oil/Mart, `WATER` Bev) |
| 2 | **Effective Month** | the month the expense *belongs to* — usually the service month on the bill, not today. `MM-YYYY`, nothing later than `03-2027` exists |
| 3 | **Budget** | **the paper's handwritten allocation.** "Common" / "For oil plant Common" → **`FACT_COM`**. Never inherit the GRPO's `Factory` (C-0027) |
| 4 | **Sub Budget** | only if the Budget is `BackOff`, `Med MKT`, `Sales`, `Sales RE` or `Interest` — then from that Budget's list in §5. Otherwise leave blank |
| 5 | **State** | the state the expense relates to, not the branch's. Watch `CH` = Chhattisgarh, and Karnataka is `KN` in Oil/Mart but `KT` in Bev |

5. **If the Budget is `Factory` or `FACT_COM`, the header branch must be FACTORY
   (`BPLId=2`)** on a GRPO, PO, A/P credit memo, goods return, A/R credit memo or
   payment. (The A/P invoice itself has no such check — *measured*: Oil A/P has 4,928
   non-Factory-budget lines on branch 2 and 50 Factory-budget lines on branch 1, all
   posted. GRPO has **zero** Factory-budget lines outside branch 2.)

### Does the GRPO's Budget carry over? Measured — and mostly yes, with one exception

Oil A/P invoice lines copied from a GRPO, last 365 days, comparing the two Budget codes:

| Relationship | Lines |
|---|---:|
| same as the GRPO | 6,790 |
| A/P line has no Budget (non-expense account) | 3,656 |
| GRPO blank, A/P filled | 227 |
| **different** | **511** |

And of those 511 differences: **`Factory` → `FACT_COM` accounts for 500.** The rest:
`BackOff`→`NPD1` 5, `FACT_COM`→`Factory` 3, `Factory`→`Del Bkhp` 3. Beverages shows the
same shape at smaller scale (`Factory`→`FACT_COM` 38 of 47 differences). Mart: 8,031 of
8,225 copied lines have no Budget at all on the A/P side.

**That is C-0027 measured in the books.** The override is not an exception someone
invented — it is the single deliberate divergence Accounts makes from the store's GRPO,
about 7% of copied expense lines, and it goes in exactly one direction.

---

## 8. How to check afterwards

```bash
# every dimension on the lines of one A/P invoice, with the account group
./hana-sql/hana-sql -env connections/hana-office-bridge.env \
'SELECT A."LineNum", A."AcctCode", B."AcctName", B."GroupMask",
        A."OcrCode" AS VARIETY, A."OcrCode2" AS EFF_MONTH, A."OcrCode3" AS BUDGET,
        A."OcrCode4" AS SUB_BUDGET, A."OcrCode5" AS STATE, A."LineTotal"
 FROM "JIVO_OIL_HANADB"."PCH1" A
 LEFT JOIN "JIVO_OIL_HANADB"."OACT" B ON B."AcctCode"=A."AcctCode"
 WHERE A."DocEntry"=<DocEntry> ORDER BY A."LineNum"'
```

Three things to look at, in order:

- any row with `GroupMask=5` and a blank `BUDGET` — it should not have posted;
- `BUDGET` = `Factory` on a bill whose paper says Common — the C-0027 miss;
- `SUB_BUDGET` blank where `BUDGET` is one of the five that require it.

And the same read on the journal it made, remembering **`ProfitCode`, not `OcrCode`**,
for Variety:

```sql
SELECT "Line_ID","Account","OrgAccName","Debit","Credit",
       "ProfitCode" AS VARIETY,"OcrCode2","OcrCode3","OcrCode4","OcrCode5"
FROM "JIVO_OIL_HANADB"."JDT1" WHERE "TransId"=<TransId> ORDER BY "Line_ID";
```

---

## 9. Traps

| # | Trap |
|---:|---|
| 1 | **Dim 1 is `ProfitCode` in the journal**, `OcrCode` on document lines, `CostingCode` in the CLI. Three names, one dimension. A ledger query on `JDT1."OcrCode"` compiles and returns nothing. |
| 2 | **The profiler's dash vs `∅`.** `JDT1` shows Budget filled on 8% of Oil lines because SAP writes `''` into 220,314 of them. A `IS NOT NULL` test would report 50%. Always test `IS NOT NULL AND <> ''`. |
| 3 | **`Factory` vs `FACTORY`.** Oil and Bev have `Factory` (mixed case); Mart has `FACTORY` (upper, 2 lines) and no `Factory`. Codes are case-sensitive strings — a cross-book script that hard-codes one gets nothing in the other book. |
| 4 | **`CH` is Chhattisgarh, not Chandigarh.** Chandigarh is `CD` in Oil/Mart and `CN` in Beverages. |
| 5 | **Karnataka has three codes**: `KN` (Oil, Mart), `KT` (Beverages only), `KR` (Oil, inactive). Aggregating states across books on the code alone under-counts Karnataka. |
| 6 | **Same meaning, different code across books**: `DIGTAL M`(O,M) = `DIG MKT`(B); `POP`(O,M) = `PPR MED`(B), both named PAPER MEDIA; `HR- 0901`(O,M) = `HR-0901`(B); `Dl-4511`(O,M) = `DL-4511`(B) — note the lower-case `l`. |
| 7 | **Beverages has 32 dead Variety codes.** `CANOLA`, `OLIVE`, `MUSTARD` etc. exist in Bev's `OPRC` with `Active='N'`. They are in the table, not in the drop-down. Do not pick one because a query found it. |
| 8 | **The Effective Month picklist stops at `03-2027`.** Year-end provisions dated into FY 27-28 (and manual JEs dated `2026-12-31` already exist — see the census) have no code. |
| 9 | **A draft can be legal and the posted document not.** Oil exempts `5100018` from the Budget check on a draft and not on the invoice; the Sub Budget allowed lists also differ between `DRF1` and `PCH1`. A clean draft is not proof it will Add. |
| 10 | **Mart is a different regime, not a smaller Oil.** No budget-owner approval, no `tbl_Draft_Approvals` table, no post-approval freeze, and a Budget vocabulary (`SUPPLY-C`, `ECOM`, `SERVICES`) that shares only `Sales`, `BackOff` and `OTE` with Oil. Never carry an Oil budget rule into Mart. |
| 11 | **In Oil the five dimensions freeze at approval.** Fixing a wrong Budget after the draft is approved means a new document, not an edit. |
| 12 | **`Del Mayp` is retired on A/P.** It is still in `OPRC`, still `Active='Y'`, and any A/P invoice dated after 2025-05-31 that uses it is refused (Oil, Bev). |
| 13 | **`Centr_z`…`Centr_z5` are SAP placeholders**, `Locked='Y'`. They appear in a raw `OPRC` pull and in nothing an operator should type. |
| 14 | **A vehicle Variety pins the account.** Only `5650002`, `5650015`, `5660005`, `2202201`, `1109002`, `5680002` accept one on a service A/P line; anything else is `180047`. |

---

## Open questions

1. **Which two `PCH1` Sub Budget variants are live?** Oil's procedure carries both a
   `BackOff` list with `IMPORT` and one without; 56 posted lines use `BackOff`+`IMPORT`,
   so the narrow one is gated behind a condition I did not isolate. Closing it needs the
   surrounding `IF :object_type = … AND :transaction_type = …` header of each block read
   in full, not just the block body.
2. **What actually reads `OcrCode3` for budget-vs-actual?** `OBGT` is empty in Mart and
   account-only elsewhere, so the comparison lives outside SAP. Candidate:
   `bud.jsBudgetTable` in JSAP — but memory notes its `DocEntry` is an `ODRF` **draft**
   key, so a naive join gives garbage. Not verified here. → [[Budget-vs-Actual-Reporting]]
3. **Is `CANOLA`-as-default a written convention or a habit?** 69% of Oil expense lines
   across 68 accounts is the evidence for it; nobody has confirmed it is the instruction.
   One question to Accounts closes this.
4. **`R & D` and `HR/ADMIN` have a blank `PrcName`.** Two Budget codes with no
   description and no owner; `R & D` has 2 posted lines (₹3.00 L). Live or abandoned?
5. **`OPRC.U_Co_Owner`** — a UDF holding a second `empID` on 12 of Oil's 17 Budget codes.
   The approval procedure only reads `CCOwner`. What consumes the co-owner?
6. **`JDT1.U_OcrCode5`** — a separate UDF ("Salary Category": `PROMOTER`, `SO/SR`, `ASM`,
   `RSM`, `CALLER`, `MIS`) on 1,062+455+262 Oil lines, required by the disabled guard
   `3000015` for salary accounts under `SALES`. Currently commented out in the
   procedure — is that intentional?
7. **The `BPLId=5` half of the Factory-branch rule looks like a typo.** The document
   guards read `OcrCode3 not in ('Factory','FACT_COM') and BPLId = 5`, while the payment
   version uses `BPLId = 2` in both directions. As written, a branch-5 GRPO line can
   satisfy neither half. Oil has no branch-5 GRPOs so it never fires — but Oil A/P *does*
   have 942 branch-5 lines. Worth showing whoever maintains the procedure.

---

## Queries used

```sql
-- 1. the five dimension names, all three books
SELECT 'OIL', "DimCode","DimName","DimDesc","DimActive" FROM "JIVO_OIL_HANADB"."ODIM"
UNION ALL SELECT 'MART', "DimCode","DimName","DimDesc","DimActive" FROM "JIVO_MART_HANADB"."ODIM"
UNION ALL SELECT 'BEV',  "DimCode","DimName","DimDesc","DimActive" FROM "JIVO_BEVERAGES_HANADB"."ODIM"
ORDER BY 1,2;

-- 2. the whole picklist master, 566 rows, pivoted per dimension in code
SELECT 'OIL', "DimCode","PrcCode","PrcName","Active","Locked" FROM "JIVO_OIL_HANADB"."OPRC"
UNION ALL SELECT 'MART', "DimCode","PrcCode","PrcName","Active","Locked" FROM "JIVO_MART_HANADB"."OPRC"
UNION ALL SELECT 'BEV',  "DimCode","PrcCode","PrcName","Active","Locked" FROM "JIVO_BEVERAGES_HANADB"."OPRC"
ORDER BY 2,3,1;

-- 3. the mandatory rule: dimension fill by account group (run per schema)
SELECT B."GroupMask", COUNT(*),
       SUM(CASE WHEN A."OcrCode"  IS NOT NULL AND A."OcrCode"  <> '' THEN 1 ELSE 0 END),
       SUM(CASE WHEN A."OcrCode2" IS NOT NULL AND A."OcrCode2" <> '' THEN 1 ELSE 0 END),
       SUM(CASE WHEN A."OcrCode3" IS NOT NULL AND A."OcrCode3" <> '' THEN 1 ELSE 0 END),
       SUM(CASE WHEN A."OcrCode4" IS NOT NULL AND A."OcrCode4" <> '' THEN 1 ELSE 0 END),
       SUM(CASE WHEN A."OcrCode5" IS NOT NULL AND A."OcrCode5" <> '' THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."PCH1" A
JOIN "JIVO_OIL_HANADB"."OPCH" H ON H."DocEntry"=A."DocEntry"
LEFT JOIN "JIVO_OIL_HANADB"."OACT" B ON B."AcctCode"=A."AcctCode"
WHERE H."DocDate">='2025-08-24' AND H."CANCELED"='N'
GROUP BY B."GroupMask" ORDER BY 2 DESC;

-- 4. Budget bucket sizes on expense accounts (run per schema)
SELECT A."OcrCode3", COUNT(*), ROUND(SUM(A."LineTotal"),0)
FROM "JIVO_OIL_HANADB"."PCH1" A
JOIN "JIVO_OIL_HANADB"."OPCH" H ON H."DocEntry"=A."DocEntry"
JOIN "JIVO_OIL_HANADB"."OACT" B ON B."AcctCode"=A."AcctCode"
WHERE H."DocDate">='2025-08-24' AND H."CANCELED"='N' AND B."GroupMask"=5
GROUP BY A."OcrCode3" ORDER BY 3 DESC;

-- 5. C-0027 measured: does the A/P line keep the GRPO's Budget? (run per schema)
SELECT CASE WHEN P."OcrCode3" IS NULL OR P."OcrCode3"=''      THEN 'AP blank'
            WHEN G."OcrCode3" IS NULL OR G."OcrCode3"=''      THEN 'GRPO blank, AP filled'
            WHEN P."OcrCode3" = G."OcrCode3"                  THEN 'same'
            ELSE 'DIFFERENT: '||G."OcrCode3"||' -> '||P."OcrCode3" END, COUNT(*)
FROM "JIVO_OIL_HANADB"."PCH1" P
JOIN "JIVO_OIL_HANADB"."OPCH" H ON H."DocEntry"=P."DocEntry"
JOIN "JIVO_OIL_HANADB"."PDN1" G
     ON G."DocEntry"=P."BaseEntry" AND G."LineNum"=P."BaseLine" AND P."BaseType"=20
WHERE H."DocDate">='2025-08-24' AND H."CANCELED"='N'
GROUP BY 1 ORDER BY 2 DESC;

-- 6. budget owners — only dims 3 and 4 have any
SELECT "DimCode", COUNT(*),
       SUM(CASE WHEN "CCOwner"    IS NOT NULL THEN 1 ELSE 0 END),
       SUM(CASE WHEN "U_Co_Owner" IS NOT NULL THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."OPRC" GROUP BY "DimCode" ORDER BY 1;

-- 7. Effective Month convention
SELECT CASE WHEN A."OcrCode2"=TO_VARCHAR(H."DocDate",'MM-YYYY')                  THEN 'same as DocDate month'
            WHEN A."OcrCode2"=TO_VARCHAR(ADD_MONTHS(H."DocDate",-1),'MM-YYYY')   THEN 'previous month'
            WHEN A."OcrCode2"=TO_VARCHAR(H."TaxDate",'MM-YYYY')                  THEN 'vendor invoice month'
            ELSE 'other' END, COUNT(*)
FROM "JIVO_OIL_HANADB"."PCH1" A
JOIN "JIVO_OIL_HANADB"."OPCH" H ON H."DocEntry"=A."DocEntry"
JOIN "JIVO_OIL_HANADB"."OACT" B ON B."AcctCode"=A."AcctCode"
WHERE H."DocDate">='2025-08-24' AND H."CANCELED"='N' AND B."GroupMask"=5
GROUP BY 1 ORDER BY 2 DESC;

-- 8. State is not the branch's state
SELECT H."BPLName", A."OcrCode5", COUNT(*) FROM "JIVO_OIL_HANADB"."PCH1" A
JOIN "JIVO_OIL_HANADB"."OPCH" H ON H."DocEntry"=A."DocEntry"
JOIN "JIVO_OIL_HANADB"."OACT" B ON B."AcctCode"=A."AcctCode"
WHERE H."DocDate">='2025-08-24' AND H."CANCELED"='N' AND B."GroupMask"=5
GROUP BY H."BPLName", A."OcrCode5" ORDER BY 1,3 DESC;

-- 9. Variety on expense lines — the CANOLA default
SELECT A."OcrCode", COUNT(*), COUNT(DISTINCT A."AcctCode") FROM "JIVO_OIL_HANADB"."PCH1" A
JOIN "JIVO_OIL_HANADB"."OPCH" H ON H."DocEntry"=A."DocEntry"
JOIN "JIVO_OIL_HANADB"."OACT" B ON B."AcctCode"=A."AcctCode"
WHERE H."DocDate">='2025-08-24' AND H."CANCELED"='N' AND B."GroupMask"=5
GROUP BY A."OcrCode" ORDER BY 2 DESC;

-- 10. the rules themselves — SAP's own validation procedure, read-only
SELECT LENGTH(DEFINITION), SCHEMA_NAME FROM SYS.PROCEDURES
WHERE PROCEDURE_NAME='SBO_SP_TRANSACTIONNOTIFICATION'
  AND SCHEMA_NAME IN ('JIVO_OIL_HANADB','JIVO_MART_HANADB','JIVO_BEVERAGES_HANADB');
-- then SELECT DEFINITION … per schema and split on END IF; keeping blocks that mention OcrCode

-- 11. GroupMask 5 = the expenditure block
SELECT "GroupMask", COUNT(*), MIN("AcctCode"), MAX("AcctCode")
FROM "JIVO_OIL_HANADB"."OACT" WHERE "Postable"='Y' GROUP BY "GroupMask" ORDER BY 1;

-- 12. the approval table the Budget code routes to
SELECT COUNT(*), COUNT(DISTINCT "DocEntry") FROM "JIVO_OIL_HANADB"."tbl_Draft_Approvals";
-- (does not exist in JIVO_MART_HANADB)
```

Corpus files this note is built on, no query re-run:
`_data/profile-ODIM.md` · `_data/profile-OPRC.md` · `_data/profile-PCH1.md` ·
`_data/profile-JDT1.md` · `_data/profile-OBGT.md` · every `_data/profile-*1.md`
line-table profile (§2b) · every `_data/gl-*.md` "Dimensions carried on the lines"
section (§2c) · `_data/flow-OPCH-OIL.md` · `00-index/Entry-Types-Census.md` ·
`acc/INVENTORY.md`.

Corrections this note implements: **C-0025** (service A/P lines need `CostingCode3`),
**C-0027** (handwritten "Common" → `FACT_COM`, never inherit the GRPO's `Factory`),
C-0003 (segment on `U_TYPE`/`U_Sub_Group` — the same `U_Sub_Group` SAP compares against
the Variety code), C-0016 (a blank is not a defect until you know where the value lives).

Related: [[AP-Invoice]] · [[GRPO]] · [[Journal-Entry]] · [[Journal-Voucher]] ·
[[Approval-Workflow]] · [[Numbering-Series]] · [[Branches-and-Business-Places]] · [[Chart-of-Accounts]] ·
[[Company-Selection]] · [[ap-rm-pm]] · [[Budget-vs-Actual-Reporting]] ·
[[Document-Status-and-Cancellation]]
