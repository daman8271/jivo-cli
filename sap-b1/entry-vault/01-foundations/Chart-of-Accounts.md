---
type: foundation
sap_tables: [OACT, OCRD, OCRG, OPCH, PCH1, JDT1, OJDT, ODIM, OADM]
objtype: 1
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Chart of Accounts — which GL you type, and which ones SAP types for you

> Every A/P line, every journal, every payment ends in a seven-digit account code.
> Roughly **44 % of A/P invoices are standalone service bills keyed off paper**
> (1,327 in 90 days — `acc/INVENTORY.md`), and on those the GL is *the one field
> nobody can copy from anywhere*. This note is the picklist, plus the list of
> accounts you must never type because SAP already fills them.

## The short version

1. **The first digit is the drawer.** `1`=assets, `2`=liabilities, `3`=equity,
   `4`=revenue, `5`=expenditure. Measured from `OACT.GroupMask`, which matches the
   first digit on 1,423 of 1,429 Oil accounts (the 6 exceptions are `1xxxxxx`
   codes filed in the liability and revenue drawers).
2. **You only ever type a `5xxxxxx` expense account** (or occasionally `1109xxx`
   prepaid / `12xxxxx` fixed-asset WIP). The vendor line, GRNI, GST, RCM, TDS and
   the rounding line are all chosen by SAP from master data — see
   [What SAP fills in by itself](#what-sap-fills-in-by-itself).
3. **Oil has 1,313 postable accounts. Only 126 have appeared on an A/P line in the
   last year** (Mart 49, Bev 63). The real picklist is small — it is in
   [The expense GL picklist](#the-expense-gl-picklist).
4. **A code is NOT portable across the three books.** Of Oil's 1,313 postable
   accounts, only 437 (33 %) exist in Mart *and* Bev under the same name; 162 exist
   in all three with a **different** name; 400 are Oil-only. `5400002` is
   `PURCHASE OLIVE` in Oil and Mart and `PURCHASE GST @ 40 %` in Beverages.
5. **Since 2026-06-01 the TDS accounts changed.** The old `194x` block is closed;
   bills from June 2026 use the section-`393(1)` block — and **those codes are
   different numbers in each book.**

---

## 1. What the number means

Measured from `OACT` in all three books, 2026-08-24. Only 7-character codes counted
(the ten 15-character rows are SAP's invisible drawer roots, and 230 8-character
codes are the per-employee advance accounts under `1113000`).

| Range | Drawer (`Levels`=1 name) | Oil | Mart | Bev | Postable (Oil) | `ActType` |
|---|---|---:|---:|---:|---:|---|
| `1xxxxxx` | ASSET | 485 | 406 | 267 | 446 | `N` (balance sheet) |
| `2xxxxxx` | LIABILITY | 313 | 294 | 245 | 275 | `N` (balance sheet) |
| `3xxxxxx` | EQUITY | 8 | 9 | 7 | 6 | `N` |
| `4xxxxxx` | REVENUE | 102 | 99 | 39 | 92 | `I` = income, 92 of 102 |
| `5xxxxxx` | EXPENDITURE | 281 | 284 | 197 | 264 | `E` = expense, 235 of 281 |

The drawer names come from the accounts themselves, not from an assumption:
`100000000000000 ASSET`, `200000000000000 LIABILITY`, `300000000000000 EQUITY`,
`400000000000000 REVENUE`, `500000000000000 EXPENDITURE`. Drawers 6–10 exist but are
empty placeholders named `#6`…`#10` in every book.

### The second and third digits — the group you are actually looking for

| Code | Oil | Mart | Bev |
|---|---|---|---|
| `1100000` | CURRENT ASSETS | same | same |
| `1200000` | FIXED ASSETS | same | same |
| `2100000` | CURRENT LIABILITES *(SAP's spelling)* | same | same |
| `2200000` | LOANS LIABILITY | same | same |
| `4100000` | DIRECT INCOME | same | same |
| `4200000` | INDIRECT INCOME | same | same |
| `5000000` | COST OF GOODS SOLD | same | same |
| `5100000` | DIRECT EXPENSE | same | same |
| `5200000` | IMPORT EXPENSE | same | same |
| `5300000` | EXPORT EXPENSE | same | same |
| `5400000` | **COST OF PURCHASE** | **PURCHASE ACCOUNT** | **PURCHASE ACCOUNT** |
| `5500000` | LANDED COST | same | same |
| `5600000` | INDIRECT EXPENSE | same | same |
| `5700000` | **PURCHASE ACCOUNT** | *does not exist* | *does not exist* |

The `5400000` / `5700000` split is the first cross-book difference an operator hits:
Oil keeps two purchase drawers, Mart and Beverages keep one.

Inside `5600000` the sub-groups are stable across all three books:
`5610000` finance · `5620000` depreciation · `5630000` employee benefit ·
`5640000` selling · `5650000` repair & maintenance · `5660000` rents, rates & taxes ·
`5670000` delivery · `5680000` general · `5690000` travelling.

### Postable vs title, and the four flags that decide whether SAP will accept it

| Field | What it means for you | Oil values |
|---|---|---|
| `Postable` | `N` = a heading. You cannot post to it, it only totals. | `Y` 1,313 / `N` 116 |
| `Levels` | Depth in the tree, 1–6. **Not** a postable test — 199 accounts are postable at level 3. | 4×883, 3×256, 5×239, 6×24, 2×17, 1×10 |
| `FatherNum` | The parent account. 99 % filled; blank only on the ten drawer roots. | 109 distinct parents |
| `ActType` | `E` expense / `I` income / `N` other. Drives which report it lands in. | `N` 1,100, `E` 235, `I` 94 |
| `ValidFor` / `FrozenFor` | `N` / `Y` = closed. SAP refuses it. | 184 invalid, 70 frozen |
| `BlocManPos` | `Y` = **blocked for manual journal entry** — document postings only. | 142 accounts, incl. 67 revenue accounts |

**Measured:** in Oil only **two** expense accounts are frozen/invalid — `5000014
COGS PM & RM` and `5680026 TELEPHONE MOBILE AND INTERNET`. The second one matters:
it is a **duplicate** of the live `5680003 TELEPHONE MOBILE AND INTERNET`. It is the
only duplicate name in Oil's and Mart's expense+liability tree. Beverages has its own
pair — `5100002` and `5100013` are both named `COST OF GOODS SOLD`.

**Inferred, not measured:** the 46 accounts in Oil's `5xxxxxx` range carrying
`ActType='N'` instead of `'E'` are almost all accounts added after go-live
(`5000044`–`5000051`, `5300017`–`5300021`, `5400058`–`5400064`, `5500006`,
`5100018`–`5100021`). The pattern says whoever created them left Account Type at its
default. What would confirm it: compare `OACT.CreateDate` and `UserSign` for
`ActType='N'` vs `'E'` in the `5xxxxxx` range.

---

## 2. Control accounts — the vendor/customer line you never type

The credit side of an A/P invoice is `OPCH.CtlAccount`, and **it is copied straight
off the vendor card**: `OCRD.DebPayAcct`. Measured in Oil — on **16,285 of 16,334**
A/P invoices (99.7 %) `OPCH.CtlAccount` equals the vendor's current `DebPayAcct`. The
49 that differ are invoices posted before someone edited the vendor card.

So the answer to "what selects the control account" is: **the vendor, not the bill,
not the expense, and not you.** The vendor *group* is only a default — Accounts
overrides it per vendor, and you can see the overrides:

| Vendor group (Oil) | Control account it usually gets | Vendors | Overridden to |
|---|---|---:|---|
| SERVICE | `2110004` SUNDRY CREDITOR SERVICE | 793 | 11 → `2110006` foreign service, 5 → `2110005`, 5 → `2110008` |
| STAFF VENDOR | `2110003` SUNDRY CREDITOR STAFF | 478 | — |
| PURCHASE | `2110005` SUNDRY CREDITOR DOMESTIC PURCHASE | 398 | 7 → `2110004` |
| FIXED ASSETS | `2110004` | 115 | 35 → `2110005` |
| TRANSPORTER | `2110004` | 97 | — |
| PURCHASE OIL | `2110001` SUNDRY CREDITOR DOMESTIC OIL | 90 | 26 → `2110005`, 10 → `2110002` foreign oil |
| PLANT & MACHINERY / CIVIL / IT / E-COMMERCE / BSU / FUEL | `2110004` | 46/45/14/10/10/4 | a few to `2110006` |
| IMPORT & EXPORT | `2110001` | 15 | 2 → `2110002` |
| BRANCH VENDOR | `2120xxx` / `2121xxx` (one account per sister entity/state) | 7 | — |

That explains the 14 values `profile-OPCH.md` sees in `CtlAccount` and their order —
`2110004` 6,800 docs, `2110005` 3,661, `2110003` 2,911, `2110001` 1,545, then the
intercompany accounts. It is a vendor-population ranking, nothing more: SERVICE is the
biggest vendor group, so SERVICE is the biggest control account.

**Beware the money vs the count.** In the last 365 days Oil credited
`2110001 DOMESTIC OIL` **₹198.04 Cr** across only 633 documents, while
`2110004 SERVICE` took ₹14.29 Cr across 3,166. Small-count accounts carry the value.

### The debtor side

Customers work the same way, but the control account encodes the **sales channel**:
`1101001 SUNDRY DEBTORS GT` (715 customers), `1101008 CALL CENTRE` (132),
`1101005 E-COM` (100), `1101006 ROI`, `1101015 STAFF`, `1101007 HORECA`,
`1101012 SANGAT`, `1101004 MT`, `1101009 CORPORATE`, `1101011 TRANSPORT`,
`1101010 BULK OIL`, `1101013 CSD`, `1101002 FOREIGN`, `1101014 CASH SALE`,
`1101003 EVENTS`, `1101016 JOB WORK`, plus `1102xxx` for the group companies.
On A/R invoices `1101005 E-COM` leads with 15,988 documents. Related: **[C-0015]** —
the `U_Main_Group` channel tag disagrees across books, so if you need channel, the
control account is the more reliable field. See [[Business-Partner-Master]].

---

## 3. What SAP fills in by itself

None of these is ever typed by an operator. If one is missing, something upstream is
wrong; if one is there and you did not expect it, read this table before "fixing" it.

| Account | Name | Appears when | Evidence (Oil, 365 d, TransType 18) |
|---|---|---|---|
| `2110xxx`/`212xxxx`/`2121xxx` | creditor control | always, from the vendor card | 7,420 lines, one per invoice |
| `2140001` | GOODS RECEIVED BUT NOT INVOICED (**GRNI**) | the A/P was copied from a GRPO | 1,796 docs, Dr ₹336.82 Cr |
| `2140002` | FIXED ASSETS RECEIVED BUT NOT INVOICED | same, for an asset GRPO | 99 docs, Dr ₹1.01 Cr |
| `2131xxx` | INPUT IGST/CGST/SGST | the tax code on the line | 7,972 GST lines |
| `21371xx` + `21375xx` | INPUT + OUTPUT RCM, **as a pair** | reverse-charge tax code | e.g. 302 docs Dr ₹33.89 L / Cr ₹33.89 L |
| `2133xxx` | TDS | the vendor's withholding-tax setup | 3,179 lines |
| `5680014` | SHORT AND EXCESS | **rounding**, see below | 3,921 docs |

### GRNI `2140001` — the account that proves a bill came from a receipt

The factory's GRPO **credits** `2140001` and debits stock (`1103xxx`) or a purchase
account (`5400xxx`). The A/P invoice then **debits** `2140001` and credits the vendor.
Measured over 365 days in Oil: GRPO credited ₹356.57 Cr, A/P debited ₹336.82 Cr. What
is left sitting there is goods received and still not billed:

| Book | `2140001` balance (all-time, `OACT.CurrTotal` = Σ`JDT1`) |
|---|---:|
| Oil | **₹7,16,71,876 credit** |
| Mart | ₹1,88,784 credit |
| Bev | **₹3,16,22,361 credit** |

If you are keying a bill against a GRPO and `2140001` does *not* appear in the
journal, the copy-from did not happen and you have just booked the cost twice.
→ [[GRPO]], [[AP-Invoice]]

### `5680014 SHORT AND EXCESS` — it is the rounding account, nothing else

This is the single most confusing line on a JIVO A/P journal: it lands on **1,749 of
the standalone bills and 2,172 of the GRPO-based ones** in Oil. It is not a stock
shortage and not a claim. **Measured, and it is exact:**

- On all **3,921** `5680014` lines in Oil A/P over 365 days, the line amount equals
  `|OPCH.RoundDif|` to the paisa — 3,921 of 3,921.
- **3,904 of 3,921 are under ₹1.** The largest in a year is ₹58.88.
- The number of A/P invoices with `RoundDif <> 0` is **3,921** — the same number.
  One-to-one. `RoundDif = 0` never produces the line.
- **Zero** of those lines came from an operator: no `PCH1` line in a year carries
  `AcctCode = '5680014'`.
- All-time net: Oil ₹5,776 **credit**, Mart ₹901 debit, Bev ₹63,861 debit. A year of
  rounding on ₹447 Cr of purchases.

The header `Rounding` flag is *not* the trigger — 1,130 documents have `Rounding='N'`
and still carry the line, because a non-zero `RoundDif` is what SAP acts on.

**Do not confuse it with `5000048 STOCK SHORT AND EXCESS`** (Oil only, under COGS,
103 GRPO lines in a year) — *that* one is a real inventory quantity variance. In Mart
`5000048` is `COGS TEA`; in Beverages it does not exist.

---

## 4. The expense GL picklist

**This is the deliverable.** Ranked by how many *standalone* A/P invoices (no GRPO
behind them) hit each account in Oil over the last 365 days, because that is exactly
the situation where a person has to choose. `TDS` and `RCM` columns are measured
incidence on the same window, so they tell you what the finished journal should look
like.

| # | Account | Name (Oil) | Standalone | From GRPO | Net ₹ | TDS on it | RCM |
|---:|---|---|---:|---:|---:|---|---|
| 1 | `5640003` | MARKET COMISSION AND BROKERAGE | 523 | 0 | 25,35,219 | **75 %** — 194H `2133007` | — |
| 2 | `5670001` | FREIGHT AND CARTAGE OUTWARD-INDIRECT EXP | 327 | 462 | 3,10,23,504 | **90 %** — 194C `2133006` (2 %) or `2133003` (1 %, HUF/individual) | **300 docs** IGST 5 % |

> `5670001` is the transporter account: **98.5 % of every transport A/P line** lands here
> (1,077 of 1,093, Oil FY26-27). Since 2026-06-01 the live TDS codes on it are **`1024`**
> (2 %, → `2133018`) and **`1023`** (1 %, → `2133016`), not the 194x pair. Dimensions on
> these lines are Dim1 = variety, Dim2 = **dispatch month**, Dim3 = `Del Bkhp` (Oil/Bev) or
> `SUPPLY-C` (Mart), Dim5 = destination state. → [[Transport-Bill-Playbook]]

| 3 | `5690002` | CONVEYANCE | 265 | 0 | 16,86,811 | never | — |
| 4 | `5640001` | ADVERTISEMENT | 259 | 0 | 8,43,20,222 | **92 %** — 194C `2133006` | — |
| 5 | `5630004` | REFRESHMENT | 214 | 235 | 23,17,851 | never | — |
| 6 | `5670002` | UNLOADING/LOADING CHARGES-INDIRECT EXPENSE | 196 | 0 | 21,63,201 | 13 % — 194C HUF `2133003` | — |
| 7 | `5680003` | TELEPHONE MOBILE AND INTERNET | 169 | 0 | 4,56,118 | never | — |
| 8 | `5680025` | LEGAL AND PROFESSIONAL | 167 | 0 | 1,08,53,672 | **70 %** — 194JB `2133005` (10 %) | 19 docs |
| 9 | `5650015` | FUEL - VEHICLES | 141 | 0 | 31,98,212 | never | — |
| 10 | `5500003` | JOB WORK FOR REFINING | 137 | 0 | 1,30,28,839 | check the bill | — |
| 11 | `5660005` | TOLL EXPENSE - VEHICLES | 123 | 0 | 5,92,353 | never | — |
| 12 | `5650002` | REPAIR & MAINTENANCE VEHICLE | 119 | 0 | 3,96,682 | never | — |
| 13 | `5660002` | RENT | 109 | 0 | 1,09,47,011 | **57 %** — 194I `2133001` (10 %) | **35 docs** (unregistered landlord) |
| 14 | `5680012` | PRINTING AND STATIONERY | 105 | 71 | 4,35,037 | never | — |
| 15 | `5630002` | INCENTIVE TO EMPLOYEES | 92 | 0 | 17,73,764 | never | — |
| 16 | `5680011` | ELECTRICITY | 91 | 0 | 65,70,835 | never | 11 docs |
| 17 | `5100008` | CASUAL LABOUR | 81 | 0 | 1,20,66,691 | check the bill | — |
| 18 | `5100002` | FREIGHT INWARD CHARGES-DIRECT | 75 | 6 | 3,01,17,593 | check the bill | — |
| 19 | `5650001` | REPAIR & MAINTENANCE OFFICE & BUILDING | 70 | 217 | 21,58,333 | 6 % — 194C HUF `2133003` | — |
| 20 | `5630005` | TA AND DA | 64 | 0 | 31,98,781 | never | — |
| 21 | `5630003` | STAFF WELFARE | 64 | 98 | 1,99,424 | never | — |
| 22 | `5500001` | FREIGHT EXPENSE-IMPORT | 63 | 0 | 2,84,97,740 | — | — |
| 23 | `5640002` | BUSINESS PROMOTION | 61 | 3 | 11,63,968 | **70 %** — 194C `2133006` | — |
| 24 | `5680023` | POSTAGE & COURIER | 58 | 0 | 71,610 | never | — |
| 25 | `5200003` | TAXES/DUTIES/FSSAI AND FEES IMPORT | 54 | 0 | 10,79,907 | — | — |
| 26 | `5650016` | REPAIR AND MAINTENANCE PLANT & MACHINERY | 52 | 137 | 17,58,239 | 2 % | — |
| 27 | `5680008` | FEES AND SUBSCRIPTION | 51 | 0 | 7,11,006 | **55 %** — s.195 `2133012` (20 %, foreign) | **24 docs** |
| 28 | `5690003` | FOREIGN TOUR AND TRAVELLING | 50 | 0 | 29,20,629 | never | — |
| 29 | `5680002` | INSURANCE INDIRECT | 46 | 0 | 12,97,642 | never | — |
| 30 | `5680004` | SOFTWARE AND TECHNOLOGY | 38 | 0 | 6,69,699 | **53 %** — 194JA `2133009` (2 %) | 2 docs |
| 31 | `5690001` | NATIONAL TOUR AND TRAVELLING | 36 | 0 | 5,70,699 | never | — |
| 32 | `5100018` | LAB & TESTING DIRECT EXPENSE | 34 | 6 | 6,03,469 | — | — |
| 33 | `5680022` | COMPUTER AND HARDWARE | 30 | 34 | 2,64,440 | never | — |
| 34 | `5680015` | HOUSE KEEPING | 28 | 132 | 5,37,740 | 1 % | — |
| 35 | `5640004` | SAMPLING EXPENSES | 25 | 0 | 73,618 | never | — |
| 36 | `5660003` | STORAGE CHARGES INDIRECT | 17 | 0 | 3,12,418 | **always** — 194C `2133006` | — |
| 37 | `5680001` | GENERATOR INDIRECT | 22 | 0 | 5,18,632 | rare | — |
| 38 | `5680016` | SECURITY EXPENSES | 13 | 0 | 17,02,049 | **always** — 194C `2133006` | — |
| 39 | `5680028` | FREIGHT INWARD-INDIRECT | 11 | 1 | 18,378 | never | **always** |
| 40 | `5660004` | SPACE ON RENT | 3 | 0 | 18,69,120 | **always** — 194I | — |

Import and export bills have their own drawers and are keyed by the import desk:
`5200001` agency/broker · `5200006` rent/storage/CFS · `5200010` professional ·
`5200011` local shipping line · `5200007` detention & demurrage · `5300004` CHA ·
`5300008` license fees. → [[Landed-Costs]], [[Import-Purchase-Flow]]

**Not an expense — the two accounts people reach for by mistake:**

| Account | Name | When it is right |
|---|---|---|
| `1109002` | PREPAID EXPENSES MISC. | 80 standalone Oil bills, ₹54.46 L — an annual policy/AMC/licence paid up front. It is an **asset**; the expense hits later by journal. |
| `1212013` / `1212003` | BUILDING WIP CONSTRUCTION | 131 lines, ₹1.22 Cr — civil work that will be capitalised, not repaired. |
| `2163003`…`2163027` | EXPENSES PAYABLE / EXPENSE CLEARING | month-end accruals via [[Journal-Entry]], **not** an A/P line. |

### The same picklist in Mart and Beverages

The account codes are mostly the same but **the traffic is completely different** —
do not carry Oil's habits across.

| Account | Oil standalone | Mart standalone | Bev standalone | Note |
|---|---:|---:|---:|---|
| `5670001` freight & cartage | 327 (+462 GRPO) | **412** (+29) | **1** (+219) | Bev's freight arrives as a service GRPO; Mart's is nearly all keyed by hand |
| `5670002` loading/unloading | 196 | 51 | **212** | Bev's most-keyed expense account |
| `5640001` advertisement | 259 | 241 | 71 | Mart's net ₹8.66 Cr ≈ Oil's ₹8.43 Cr on a fifth of the turnover |
| `5650016` R&M plant & machinery | 52 (+137) | 0 | 70 (+202) | a Beverages/factory account |
| `5100008` casual labour | 81 | 0 | 49 | never used in Mart |
| `5680030`/`5680032`/`5680033` | *different accounts* | FIXED FEE 34 · PICK AND PACK FEE 10 · CUSTOMER ADD ON RECOVERY 16 | — | **marketplace deduction accounts, Mart only** |
| `5680029` | FIXED ASSET WRITTEN OFF | **TECHNOLOGY FEES** 11 | FIXED ASSET WRITTEN OFF | same code, different account |

---

## 5. GST, RCM and TDS — the three families

### INPUT and OUTPUT GST

`2131001`–`2131018` (input) and `2132001`–`2132017` (output) are **identical in all
three books**: one account per rate per head — IGST 0/5/12/18/28, CGST+SGST
0/2.5/6/9/14, CESS 12, plus `2131017 INPUT EXEMPT` and `2131018 GST NOT ON PORTAL`.
An A/P invoice **debits** the input account; you never type it, the tax code does.

**Divergence starts at the tail of the family** — the accounts added later:

| Code | Oil | Mart | Bev |
|---|---|---|---|
| `2131019` | GST INPUT UNCLAIMED A/C (2A) | GST INPUT UNCLAIMED A/C (2A) | **Inter-branch ITC Clearing** |
| `2131020` | Inter-branch ITC Clearing | INTER BRANCH ITC CLEARING | **INPUT IGST @40 %** |
| `2131021` | INPUT IGST @40 % | **TDS ON CONTRACTOR @ 0.25 % 194C** | INPUT CGST @20 % |
| `2131022` | INPUT IGST @0.1 % | INPUT IGST@40 % | INPUT SGST @20 % |
| `2132018` | OUTPUT CGST @20 % | **OUTPUT IGST @ 40 %** | OUTPUT CGST @20 % |
| `2132020` | OUTPUT IGST @40 % | OUTPUT CGST@20 % | OUTPUT IGST @40 % |

The 40 % slab is live in Beverages: `2131020 INPUT IGST @40%` carried 11 lines /
₹3,02,778 in the last year. → [[GST-on-Purchases]]

### Reverse charge — always a pair, always equal

`2137101`–`2137112` (input RCM) and `2137501`–`2137512` (output RCM) are **identical
in all three books**, and they always post together in the same amount:

| Pair | Oil docs | Debit | Credit | What it is |
|---|---:|---:|---:|---|
| `2137109` / `2137509` IGST 5 % RCM | 302 / 302 | ₹33,89,354 | ₹33,89,354 | **GTA road freight** — the transporter does not charge GST, JIVO self-invoices |
| `2137101`+`2137102` / `2137501`+`2137502` CGST+SGST 2.5 % RCM | 133 each | ₹2,59,194 each | ₹2,59,194 each | intra-state freight |
| `2137105`/`2137505`, `2137106`/`2137506` @9 % | Mart 19 | ₹32,645 | ₹32,645 | rent, legal from an unregistered supplier |
| `2137111` / `2137511` IGST 18 % RCM | Mart 23 | ₹43,395 | ₹43,395 | imported service |

The RCM lines net to zero on the P&L; they exist so the liability and the credit both
appear in GSTR-3B. **If you see only one of the pair, the tax code is wrong.**

### TDS `2133xxx` — and the 2026-06-01 cutover

`2133001`–`2133011` is the original block. **From 2026-06-01 JIVO switched to a new
block named after Income-tax Act section `393(1)` codes.** Measured in Oil `JDT1`:

| Family | First used | Last used | Lines |
|---|---|---|---:|
| old `194x` names | 2024-09-30 | 2026-08-07 | 6,164 |
| new `393(1)` names | **2026-06-01** | 2026-08-19 | 473 |

Same cutover date in all three books (Mart 387 new lines, Bev 80). After 2026-07-01
the only old-family accounts still moving in Oil are the housekeeping ones —
`2133004 TDS ON SALARY`, `2133011 TDS PAYABLE`, `2133008` interest — plus a single
stray `2133006` line dated 2026-07-01.

**The new codes are different numbers in each book. This is the worst trap in the
chart.**

| TDS nature | Oil | Mart | Bev |
|---|---|---|---|
| Contractor others 2 % | `2133018` | `2133021` | `2133016` |
| Contractor HUF/individual 1 % | `2133016` | `2133019` | `2133014` |
| Commission/brokerage 2 % | `2133019` | `2133022` | `2133017` |
| Professional 10 % | `2133017` | `2133020` | `2133015` |
| Rent land/building 10 % | `2133014` | `2133017` | `2133012` |
| 0.1 % (the 194Q successor) | `2133022` | `2133025` | `2133020` |

And in the **old** block the same code already meant different things:
`2133009` is `TDS ON TECHNICAL SERVICES @2 % 194JA` in Oil and Beverages but
`TDS ON @ 0.05 % 194C` in Mart. `2133002` is rent on plant/machinery in Oil,
`TDS @ 0.20 % 194H` in Mart. `2133012` is s.195 20 % in Oil, `194C 0.01 %` in Mart,
and a `393(1)` rent account in Beverages.

Which TDS account pairs with which expense (Oil, measured, ≥5 docs):

| Expense | TDS account used |
|---|---|
| `5670001` freight | `2133006` 457 · `2133003` 130 · `2133018` 111 · `2133016` 16 |
| `5640001` advertisement | `2133006` 206 · `2133018` 22 · `2133003` 9 |
| `5640003` commission | `2133007` 325 · `2133019` 67 |
| `5680025` legal & professional | `2133005` 104 · `2133017` 11 |
| `5660002` rent | `2133001` 52 · `2133014` 10 |
| `5680004` software | `2133009` 16 |
| `5680008` fees & subscription | `2133012` 21 (foreign, 20 %) |

**Remember [C-0018]:** `sapb1 draft purchase-invoice` comes out with **TDS = 0**
(`WTLiable = tNO`). Check `WTAmount` before anyone presses Add. → [[TDS-on-Purchases]]

---

## 6. Is a code portable across the three books? Mostly no.

Measured over Oil's 1,313 postable accounts, 2026-08-24:

| Verdict | Accounts |
|---|---:|
| exists in all three books, **identical name** | **437** (33 %) |
| exists in all three, **name DIFFERS** | **162** |
| Oil + Mart only | 269 |
| Oil + Beverages only | 45 |
| Oil only | 400 |

Two kinds of "differs", and they are not the same problem:

**(a) Wording only — same account, safe.** All 16 differences in the `5xxxxxx` range
that SAP's own map flags are spelling: `FREIGHT AND CARTAGE OUTWARD-EXPORT` vs
`… OUTWARD - EXPORT`, `DONATION - CSR` vs `DONATION`, `SECURITY EXPENSES` vs
`SECURITY`, `PUMPING` vs `PUMING` (SAP's typo, in Beverages). Also
`5670001`/`5670002`/`5650001` read differently in Mart but mean the same thing.

**(b) A different account behind the same number — dangerous.**

| Code | Oil | Mart | Bev |
|---|---|---|---|
| `5400002` | PURCHASE OLIVE | PURCHASE OLIVE | **PURCHASE GST @ 40 %** |
| `5400051` | PURCHASE EXEMPT | PURCHASE DRINKS | **PURCHASE GLUE** |
| `5400052` | PURCHASE DRINKS | PURCHASE GST @ 40 % | **PURCHASE SPOON** |
| `5100002` | FREIGHT INWARD CHARGES-DIRECT | FREIGHT INWARD CHARGES-DIRECT | **COST OF GOODS SOLD** |
| `5100016` | PLATE & DIE CHARGES | PLATE & DIE CHARGES | **FREIGHT INWARD CHARGES - DIRECT** |
| `5000002` | COGS OLIVE | COGS OLIVE | **COGS DRINK** |
| `5680029` | FIXED ASSET WRITTEN OFF | **TECHNOLOGY FEES** | FIXED ASSET WRITTEN OFF |
| `5680031` | LOSS IN TRANSIT | **REMOVAL FEE** | **PENALTY FOR NON STOCK SUPPLY** |
| `4200005` | technical/analyst services income | architect/analyst services income | **PROFIT/LOSS ON SALE OF FIXED ASSETS** |
| `2110008` | SUNDRY CREDITORS CLEARING | SUNDRY CREDITORS CLEARING | SUNDRY CREDITORS **PAYABLE** CLEARING |
| `2131019` | GST INPUT UNCLAIMED (2A) | same | **Inter-branch ITC Clearing** |
| `2120002` | JIVO WELLNESS PVT. LTD HARYANA | JIVO WELLNESS PVT. LTD HARYANA | **JIVO BEVERAGES HARYANA** |
| `2121002` | SUNDRY CREDITORS JIVO MART | **SUNDRY CREDITORS JIVO WELLNESS** | SUNDRY CREDITORS JIVO MART |

The `212xxxx` family needs care even where the name matches. Oil's book *is* JIVO
WELLNESS PVT LTD, so in Oil `2120002 JIVO WELLNESS HARYANA` is an **inter-branch**
creditor. The identical row in Mart's book (`JIVO MART PVT LTD`) is an
**inter-company** creditor for the Oil entity. Mart's own branches start at
`2120007`. Beverages' book is `(BEVERAGE UNIT) JIVO WELLNESS PVT LTD`, so its
`2120007` is `JIVO OIL (JIVO WELLNESS UNIT)`. Same shape, three different meanings.
→ [[Intercompany-and-Branch-Accounts]], **[C-0005]**, **[C-0020]**

### There is a machine-readable map, and almost nobody knows it

**`OACT.U_WG_GLNO` in the Oil book holds the Beverages account code for the same
account.** Not documented anywhere, and it is a UDF, so it never appears in SAP's
help. Verified:

- Filled on **494 of Oil's 1,429 accounts** (35 %); empty in Mart and Beverages.
- All 494 targets exist in the Beverages book.
- **462 of 494 (94 %)** have the identical name in Beverages; 435 in Mart.
- On 472 it is simply the same number; on 22 it points at a **different** number —
  and those 22 are exactly the risky ones. `5400052 PURCHASE DRINKS` → `5400001`
  (`PURCHASE DRINKS` in Bev). `5100002 FREIGHT INWARD` → `5100016`.
  `5680032 PENALTY FOR NON STOCK SUPPLY` → `5680031`. `4200006 SCRAP SALES` →
  `4200007`. `1103003 FINISHED GOODS BEVERAGES` → `1103001`.

So before assuming a code carries over, read `U_WG_GLNO` — there is a query for it at
the bottom of this note.

---

## 7. Dimensions — part of choosing the GL, not a separate job

The five active dimensions (`ODIM`) are **1 Variety · 2 Effective Month · 3 Budget ·
4 Sub Budget · 5 State**.

**Measured on Oil A/P journals, 365 days: every real indirect-expense account carries
dimensions 1, 2, 3 on 100 % of its lines.** Every one of the 31 `56xxxxx` accounts
with ≥20 lines is at 100 % for `ProfitCode` (dim 1), `OcrCode2` and `OcrCode3`.
Dimension 5 (State) runs 78–100 %. Dimension 4 (Sub Budget) is the one that varies —
100 % on `5640003` commission, `5630005` TA/DA and `5630002` incentive; 95 % on
advertisement; 81 % legal; 0 % on `5670002` and `5650016`.

The average of "26 % of A/P lines carry a profit centre" in `_data/gl-18-OIL.md` is
misleading: **dimensions appear on the expense line only.** Measured incidence by
family — expense `5xxxxxx` 68 %, GST 0 %, TDS 0 %, creditor control 0 %. The 32 %
gap inside the expense family is almost entirely the `5680014` rounding lines (3,921
of them, 0 % dimensioned) and the `5400xxx` purchase accounts on GRPO-based bills.

So the operator rule is absolute: **if you type an indirect-expense account, you type
dimensions 1, 2, 3 as well.** `OcrCode3` (Budget) takes one of
`Del Bkhp · Factory · BackOff · FACT_COM · Sales · Sales RE · Med MKT · OTE ·
Transprt · Del Mayp · NPD1 · NPD2 · NPD3` — and **[C-0027]**: a handwritten
"Common" on a factory bill means **`FACT_COM`**, never the GRPO's `Factory`.
→ [[Dimensions-and-Cost-Centres]]

---

## 8. Pre-flight — before you pick an account

1. **Which book?** `JIVO_OIL_HANADB` / `JIVO_MART_HANADB` / `JIVO_BEVERAGES_HANADB`.
   A GRN header reading "(BEVERAGE UNIT)" is Beverages. Nothing below transfers
   between books.
2. **Is this bill already in?** Check `NumAtCard` first — Neetu pre-keys drafts
   (memory `sapb1-write-support`). Also check Document Drafts, not just posted.
3. **Is there a GRPO?** If yes, **copy from it** — do not type an expense account at
   all; the cost is already in `2140001` and you will double-book it.
   45 % of A/P invoices are item-on-GRPO and 9 % service-on-GRPO (`acc/INVENTORY.md`).
4. **Confirm the vendor, then leave the credit side alone.** The control account comes
   from the card (`OCRD.DebPayAcct`). If it looks wrong, the *vendor card* is wrong —
   fix that, do not override the line.
5. **Pick the expense account from §4**, matching the bill's wording, not its amount.
   If two candidates fit, pick the one with traffic in *this* book.
6. **Check the account is alive**: `Postable='Y'`, `ValidFor='Y'`, `FrozenFor='N'`.
   The classic miss is `5680026` (frozen telephone duplicate) instead of `5680003`.
7. **Decide TDS from §5, not from the bill.** Freight, commission, advertisement,
   rent, professional, storage and security withhold; refreshment, conveyance, fuel,
   toll, travel, telephone, printing, postage, insurance and staff welfare never do.
   Bills dated on/after 2026-06-01 use the `393(1)` account **for this book**.
8. **Set dimensions 1, 2, 3** on every expense line (and 5 unless the account never
   carries it). See **[C-0025]** and **[C-0027]**.
9. **Dates:** `DocDate` = the GRPO / gate-in date, `TaxDate` = the vendor's invoice
   date (**[C-0017]**) — and **[C-0022]**: do not read a gate-in date back off an
   existing A/P invoice.
10. **Draft it, don't post it.** 2,857 of 2,995 A/P invoices go through approval.

### After you save — the read-back

| Check | Expected |
|---|---|
| Journal line count | 4, 5 or 6 covers 4,549 of 7,420 Oil A/P journals. 2 lines = no tax, no TDS. A 9-line journal happens 52 times in 7,420 — look again. |
| Creditor control | exactly one line, credit, `= OCRD.DebPayAcct` |
| `2140001` | present **iff** the bill was copied from a GRPO |
| `5680014` | ≤ ₹1 in 99.6 % of cases, and never more than about ₹60 |
| RCM | `21371xx` and `21375xx` both present, equal amounts |
| TDS | `WTAmount` non-zero if §5 says this account withholds |
| Dimensions | filled on the expense lines, absent on GST/TDS/control lines |

---

## Traps

1. **`5680014 SHORT AND EXCESS` is rounding, not a shortage.** Verified to the paisa
   against `OPCH.RoundDif` on 3,921 of 3,921 lines. The stock-shortage account is
   `5000048 STOCK SHORT AND EXCESS`, Oil only — and in Mart that same number is
   `COGS TEA`.
2. **`5400002` is `PURCHASE OLIVE` in Oil and `PURCHASE GST @ 40 %` in Beverages.**
   Never carry a `5400xxx` code between books from memory.
3. **The `393(1)` TDS codes are renumbered per book.** Contractor-others 2 % is
   `2133018` (Oil), `2133021` (Mart), `2133016` (Bev). Reading the *name* is the only
   safe method.
4. **`2133009` already meant two different things** before the renumbering — technical
   services 2 % in Oil/Bev, 0.05 % 194C in Mart.
5. **Two live accounts named `TELEPHONE MOBILE AND INTERNET`** in Oil and Mart —
   `5680003` (live) and `5680026` (frozen). Beverages has two named
   `COST OF GOODS SOLD` (`5100002`, `5100013`), both postable.
6. **`Levels` does not tell you if an account is postable.** 199 Oil accounts post at
   level 3 and 116 accounts across all levels are titles. Read `Postable`.
7. **142 Oil accounts are `BlocManPos='Y'`** — visible, postable by a document, and
   silently refused in a manual journal entry. 67 of them are revenue accounts.
8. **The `2120xxx`/`2121xxx` name can match while the meaning flips** between
   inter-branch and inter-company, because each book is a different legal entity.
9. **`OACT` holds employee bank details.** `U_Account_Number`, `U_IFSC` and
   `U_Bank_Name` are filled on ~20 % of Oil accounts — the per-employee advance accounts under
   `1113000`, 230 of which carry an 8-digit code. Never paste an `OACT` dump into a shared document, a
   ticket, or this repo.
10. **`4200011` posted ₹1.32 Cr on the *debit* side of Mart A/P journals** (27 docs,
    `SALE OF SERVICES`). A revenue account debited on a purchase invoice is a
    contra/reversal pattern — worth asking about before copying it.
11. **`CurrTotal` is signed the SAP way** — negative = credit. Verified: for
    `2140001` in Oil it equals `Σ(JDT1.Debit − JDT1.Credit)` exactly.

## Open questions

1. **Why do 1,130 A/P invoices carry `Rounding='N'` and still post a rounding line?**
   The `RoundDif` field explains *whether* the line appears; it does not explain why
   the header flag disagrees. Closing query: compare `Series`, `DocumentSubType` and
   `UserSign` for `Rounding='N' AND RoundDif<>0` against `Rounding='Y'`.
2. **Who owns the picklist?** There is no `OACT` field marking "this is the account
   Accounts should use for X". The mapping in §4 is inferred from a year of postings,
   not from a rule anyone wrote down. Would a written expense-code sheet exist in
   Accounts on paper?
3. **Is `U_WG_GLNO` maintained or abandoned?** It covers 494 of 1,429 accounts and is
   94 % correct, but every account created after some date may be missing. Closing
   query: `U_WG_GLNO IS NULL` grouped by `CreateDate` year.
4. **Why is `U_WG_GLNO` only in the Oil book?** If it is the consolidation map, Mart
   and Beverages have no reverse map, so a Mart→Oil lookup has to scan Oil.
5. **What are the 46 `ActType='N'` accounts in Oil's expense tree doing to the P&L?**
   Unverified. It may be cosmetic or it may drop them out of a standard report.
6. **`5400054 PURCHASE OF FIXED ASSETS` in Oil (a purchase account) vs `2140002`
   (asset GRNI) vs `1208001 ACQUISITION CLEARING ACCOUNT`** — three paths for an
   asset purchase. Which one Accounts is supposed to use is not settled by the data:
   all three carry traffic.
7. **Mart `2131021` is a TDS account sitting inside the INPUT TAX block.** Almost
   certainly a keying mistake when the account was created. Unverified whether it has
   ever been posted to.

## Which documents it touches

[[AP-Invoice]] · [[AP-Credit-Memo]] · [[GRPO]] · [[Journal-Entry]] ·
[[Journal-Voucher]] · [[Outgoing-Payment]] · [[Incoming-Payment]] · [[AR-Invoice]] ·
[[Landed-Costs]] · [[Business-Partner-Master]] · [[Dimensions-and-Cost-Centres]] ·
[[GST-on-Purchases]] · [[TDS-on-Purchases]] · [[Intercompany-and-Branch-Accounts]] ·
[[Opening-Balance-and-Cutover]] · [[Entry-Types-Census]]

## Queries used

Every figure above comes from one of these, run read-only from the repo root on
2026-08-24 via `./hana-sql/hana-sql -env connections/hana-office-bridge.env`.
Swap `JIVO_OIL_HANADB` for `JIVO_MART_HANADB` / `JIVO_BEVERAGES_HANADB`.

```sql
-- the drawers and the second level
SELECT "AcctCode","AcctName","Levels","FatherNum","ActType","Postable"
FROM "JIVO_OIL_HANADB"."OACT" WHERE "Levels"<=2 ORDER BY "AcctCode";

-- accounts per range, postable vs title
SELECT LEFT("AcctCode",1) AS D, COUNT(*) AS TOTAL,
       SUM(CASE WHEN "Postable"='Y' THEN 1 ELSE 0 END) AS POSTABLE,
       SUM(CASE WHEN "ActType"='E' THEN 1 ELSE 0 END) AS ACT_E,
       SUM(CASE WHEN "ActType"='I' THEN 1 ELSE 0 END) AS ACT_I
FROM "JIVO_OIL_HANADB"."OACT" WHERE LENGTH("AcctCode")=7
GROUP BY LEFT("AcctCode",1) ORDER BY D;

-- GroupMask really is the drawer
SELECT "GroupMask", LEFT("AcctCode",1) AS D, COUNT(*) FROM "JIVO_OIL_HANADB"."OACT"
GROUP BY "GroupMask", LEFT("AcctCode",1) ORDER BY "GroupMask";

-- accounts SAP will refuse, by range
SELECT LEFT("AcctCode",1) AS D,
       SUM(CASE WHEN "FrozenFor"='Y' THEN 1 ELSE 0 END) AS FROZEN,
       SUM(CASE WHEN "ValidFor"='N' THEN 1 ELSE 0 END) AS INACTIVE,
       SUM(CASE WHEN "BlocManPos"='Y' THEN 1 ELSE 0 END) AS BLOCK_MANUAL_JE
FROM "JIVO_OIL_HANADB"."OACT" WHERE "Postable"='Y' GROUP BY LEFT("AcctCode",1);

-- duplicate account names in the ranges an operator types
SELECT "AcctName", COUNT(*), STRING_AGG("AcctCode",' + ')
FROM "JIVO_OIL_HANADB"."OACT"
WHERE "Postable"='Y' AND ("AcctCode" LIKE '5%' OR "AcctCode" LIKE '2%')
GROUP BY "AcctName" HAVING COUNT(*)>1;

-- three books side by side (repeat with '213%', '211%', '56%', "Levels"=3 …)
SELECT o."AcctCode", o."AcctName" AS OIL, m."AcctName" AS MART, b."AcctName" AS BEV
FROM "JIVO_OIL_HANADB"."OACT" o
LEFT JOIN "JIVO_MART_HANADB"."OACT" m ON m."AcctCode"=o."AcctCode"
LEFT JOIN "JIVO_BEVERAGES_HANADB"."OACT" b ON b."AcctCode"=o."AcctCode"
WHERE o."AcctCode" LIKE '213%' ORDER BY o."AcctCode";

-- portability verdict
SELECT CASE WHEN m."AcctCode" IS NULL AND b."AcctCode" IS NULL THEN 'Oil only'
            WHEN m."AcctCode" IS NULL THEN 'Oil+Bev only'
            WHEN b."AcctCode" IS NULL THEN 'Oil+Mart only'
            WHEN o."AcctName"=m."AcctName" AND o."AcctName"=b."AcctName"
                 THEN 'all 3, name identical'
            ELSE 'all 3, name DIFFERS' END AS VERDICT, COUNT(*)
FROM "JIVO_OIL_HANADB"."OACT" o
LEFT JOIN "JIVO_MART_HANADB"."OACT" m ON m."AcctCode"=o."AcctCode"
LEFT JOIN "JIVO_BEVERAGES_HANADB"."OACT" b ON b."AcctCode"=o."AcctCode"
WHERE o."Postable"='Y' GROUP BY 1 ORDER BY 2 DESC;

-- the hidden cross-book map, and whether it agrees with the Bev book
SELECT COUNT(*) AS MAPPED,
       SUM(CASE WHEN b."AcctCode" IS NULL THEN 1 ELSE 0 END) AS TARGET_MISSING,
       SUM(CASE WHEN b."AcctName"=o."AcctName" THEN 1 ELSE 0 END) AS NAME_MATCHES_BEV
FROM "JIVO_OIL_HANADB"."OACT" o
LEFT JOIN "JIVO_BEVERAGES_HANADB"."OACT" b
       ON b."AcctCode"=TO_VARCHAR(o."U_WG_GLNO")
WHERE o."U_WG_GLNO" IS NOT NULL;

-- where the control account comes from
SELECT g."GroupName", c."DebPayAcct", a."AcctName", COUNT(*) AS VENDORS
FROM "JIVO_OIL_HANADB"."OCRD" c
LEFT JOIN "JIVO_OIL_HANADB"."OCRG" g ON g."GroupCode"=c."GroupCode" AND g."GroupType"='S'
LEFT JOIN "JIVO_OIL_HANADB"."OACT" a ON a."AcctCode"=c."DebPayAcct"
WHERE c."CardType"='S' GROUP BY 1,2,3 ORDER BY VENDORS DESC;

SELECT CASE WHEN p."CtlAccount"=c."DebPayAcct" THEN 'same as vendor card'
            ELSE 'differs' END AS MATCH, COUNT(*)
FROM "JIVO_OIL_HANADB"."OPCH" p
JOIN "JIVO_OIL_HANADB"."OCRD" c ON c."CardCode"=p."CardCode" GROUP BY 1;

-- THE PICKLIST: expense accounts by standalone vs GRPO-based A/P, 365 days
SELECT l."AcctCode", a."AcctName",
       COUNT(DISTINCT CASE WHEN b."HG"=0 THEN p."DocEntry" END) AS STANDALONE,
       COUNT(DISTINCT CASE WHEN b."HG"=1 THEN p."DocEntry" END) AS FROM_GRPO
FROM "JIVO_OIL_HANADB"."OPCH" p
JOIN "JIVO_OIL_HANADB"."PCH1" l ON l."DocEntry"=p."DocEntry"
JOIN "JIVO_OIL_HANADB"."OACT" a ON a."AcctCode"=l."AcctCode"
JOIN (SELECT "DocEntry", MAX(CASE WHEN "BaseType"=20 THEN 1 ELSE 0 END) AS "HG"
      FROM "JIVO_OIL_HANADB"."PCH1" GROUP BY "DocEntry") b
  ON b."DocEntry"=p."DocEntry"
WHERE p."DocDate">=ADD_DAYS(CURRENT_DATE,-365) AND l."AcctCode" LIKE '5%'
GROUP BY l."AcctCode", a."AcctName" ORDER BY STANDALONE DESC;

-- TDS and RCM incidence per expense account
SELECT e."Account", a."AcctName", COUNT(DISTINCT e."TransId") AS DOCS,
       COUNT(DISTINCT t."TransId") AS DOCS_WITH_TDS,
       COUNT(DISTINCT r."TransId") AS DOCS_WITH_RCM
FROM "JIVO_OIL_HANADB"."JDT1" e
JOIN "JIVO_OIL_HANADB"."OJDT" h ON h."TransId"=e."TransId"
JOIN "JIVO_OIL_HANADB"."OACT" a ON a."AcctCode"=e."Account"
LEFT JOIN "JIVO_OIL_HANADB"."JDT1" t
       ON t."TransId"=e."TransId" AND t."Account" LIKE '2133%'
LEFT JOIN "JIVO_OIL_HANADB"."JDT1" r
       ON r."TransId"=e."TransId" AND r."Account" LIKE '2137%'
WHERE h."TransType"=18 AND h."RefDate">=ADD_DAYS(CURRENT_DATE,-365)
  AND e."Account" LIKE '56%' AND e."Account"<>'5680014'
GROUP BY e."Account", a."AcctName" ORDER BY DOCS DESC;

-- which TDS account pairs with which expense
SELECT e."Account" AS EXPENSE, t."Account" AS TDS, ta."AcctName",
       COUNT(DISTINCT e."TransId") AS DOCS
FROM "JIVO_OIL_HANADB"."JDT1" e
JOIN "JIVO_OIL_HANADB"."OJDT" h ON h."TransId"=e."TransId"
JOIN "JIVO_OIL_HANADB"."JDT1" t
     ON t."TransId"=e."TransId" AND t."Account" LIKE '2133%'
JOIN "JIVO_OIL_HANADB"."OACT" ta ON ta."AcctCode"=t."Account"
WHERE h."TransType"=18 AND h."RefDate">=ADD_DAYS(CURRENT_DATE,-365)
  AND e."Account" LIKE '56%'
GROUP BY e."Account", t."Account", ta."AcctName"
HAVING COUNT(DISTINCT e."TransId")>=5 ORDER BY 1, DOCS DESC;

-- proof that 5680014 is the rounding account
SELECT COUNT(*) AS LINES, MIN(ABS(j."Debit"-j."Credit")) AS MINABS,
       MAX(ABS(j."Debit"-j."Credit")) AS MAXABS,
       SUM(CASE WHEN ABS(j."Debit"-j."Credit")<1 THEN 1 ELSE 0 END) AS UNDER_1_RUPEE,
       SUM(CASE WHEN ROUND(ABS(j."Debit"-j."Credit"),2)=ROUND(ABS(p."RoundDif"),2)
                THEN 1 ELSE 0 END) AS EQUALS_ROUNDDIF
FROM "JIVO_OIL_HANADB"."OPCH" p
JOIN "JIVO_OIL_HANADB"."JDT1" j ON j."TransId"=p."TransId"
WHERE j."Account"='5680014' AND p."DocDate">=ADD_DAYS(CURRENT_DATE,-365);

SELECT SUM(CASE WHEN "RoundDif"<>0 THEN 1 ELSE 0 END) AS DOCS_ROUNDDIF_NONZERO,
       COUNT(*) AS DOCS_TOTAL
FROM "JIVO_OIL_HANADB"."OPCH" WHERE "DocDate">=ADD_DAYS(CURRENT_DATE,-365);

-- the TDS cutover date
SELECT CASE WHEN a."AcctName" LIKE '%393(1)%' THEN 'new 393(1)' ELSE 'old 194x' END,
       MIN(h."RefDate"), MAX(h."RefDate"), COUNT(*)
FROM "JIVO_OIL_HANADB"."JDT1" j
JOIN "JIVO_OIL_HANADB"."OJDT" h ON h."TransId"=j."TransId"
JOIN "JIVO_OIL_HANADB"."OACT" a ON a."AcctCode"=j."Account"
WHERE j."Account" LIKE '2133%' GROUP BY 1;

-- dimensions live on the expense line only
SELECT CASE WHEN j."Account" LIKE '5%' THEN 'expense'
            WHEN j."Account" LIKE '2131%' OR j."Account" LIKE '2137%' THEN 'GST'
            WHEN j."Account" LIKE '2133%' THEN 'TDS'
            WHEN j."Account" LIKE '211%' OR j."Account" LIKE '212%' THEN 'control'
            ELSE 'other' END AS FAMILY, COUNT(*) AS LINES,
       ROUND(100.0*SUM(CASE WHEN j."ProfitCode"<>'' THEN 1 ELSE 0 END)/COUNT(*),0) AS D1,
       ROUND(100.0*SUM(CASE WHEN j."OcrCode3"<>'' THEN 1 ELSE 0 END)/COUNT(*),0) AS D3
FROM "JIVO_OIL_HANADB"."JDT1" j
JOIN "JIVO_OIL_HANADB"."OJDT" h ON h."TransId"=j."TransId"
WHERE h."TransType"=18 AND h."RefDate">=ADD_DAYS(CURRENT_DATE,-365) GROUP BY 1;

-- how small the real picklist is
SELECT COUNT(DISTINCT l."AcctCode") FROM "JIVO_OIL_HANADB"."PCH1" l
JOIN "JIVO_OIL_HANADB"."OPCH" p ON p."DocEntry"=l."DocEntry"
WHERE p."DocDate">=ADD_DAYS(CURRENT_DATE,-365);

-- key balances (CurrTotal is signed: negative = credit; verified = Σ JDT1)
SELECT "AcctCode","AcctName",ROUND("CurrTotal",0) FROM "JIVO_OIL_HANADB"."OACT"
WHERE "AcctCode" IN ('2140001','2140002','5680014','2110004','2110005',
                     '2110003','2110001','2110008');
SELECT ROUND(SUM("Debit"-"Credit"),0) FROM "JIVO_OIL_HANADB"."JDT1"
WHERE "Account"='2140001';

-- the five dimensions
SELECT "DimCode","DimDesc","DimActive" FROM "JIVO_OIL_HANADB"."ODIM" ORDER BY "DimCode";
```

Corpus files this note also rests on: `_data/profile-OACT.md`,
`_data/profile-OPCH.md`, `_data/profile-PCH1.md`, `_data/gl-18-OIL.md`,
`_data/gl-18-MART.md`, `_data/gl-18-BEV.md`, `_data/gl-19-OIL.md`,
`_data/gl-20-OIL.md`, `_data/gl-30-OIL.md`, `00-index/Entry-Types-Census.md`,
`acc/INVENTORY.md`.
