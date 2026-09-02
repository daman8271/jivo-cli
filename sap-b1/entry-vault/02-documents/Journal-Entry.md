---
type: document
sap_tables: [OJDT, JDT1]
objtype: 30
companies: [OIL, MART, BEV]
mined: 2026-08-25
confidence: high
---

# Journal Entry — the entry with no rules

> Everything else in this vault is a document with a shape. A manual journal is a blank
> page: any accounts, any amounts, as long as it balances. **8,090 of them** across the
> books, and the reason they need documenting is precisely that nothing constrains them.

## At a glance

| | |
|---|---|
| SAP tables | `OJDT` header · `JDT1` lines |
| Key | **`TransId`** — not `DocEntry`. A journal is not a document |
| Manual (`TransType` 30) | Oil 5,235 · Mart 1,491 · Bev 1,364 · **8,090** |
| All journals | 224,982 — so manual is **3.6%** of the ledger |
| Dated by | `RefDate`, **not** `DocDate` |
| Drafted? | Never. No entry in `ODRF` |
| Approval? | None |
| **How most of them arrive** | **59% posted from a parked [[Journal-Voucher]]** |

## Most manual journals are not keyed as journals

Oil's 5,235 manual journals split by how they got there:

| Route | Journals | Share |
|---|---:|---:|
| Posted from a parked [[Journal-Voucher]] (`OJDT."BatchNum"` set) | **3,102** | **59%** |
| Keyed directly | 2,133 | 41% |

So the normal path is *park it, get it reviewed, post it* — which means there **is** a
control on the uncontrolled entry, just not one SAP calls approval. → [[Journal-Voucher]]

## The taxonomy — what manual journals are actually for

Clustered from `JDT1."LineMemo"` and the account pairs, Oil, all history.

### 1. Payroll and statutory — by far the largest

| Account | Name | Lines | JEs | Dr |
|---|---|---:|---:|---:|
| `5630001` | Salary expense | 1,725 | 276 | **₹31.23 Cr** |
| `2163016` | ESIC payable | 671 | 145 | |
| `2163015` | EPF payable | 634 | 193 | |
| `5630012` / `5630011` | ESIC employer / employee contribution | 618 / 616 | | |
| `5630015` / `5630010` | EPF employer / employee contribution | 572 / 567 | | |
| `5630007` | EPF admin charges | 562 | 131 | |

The memos decode the structure — salary is split by **cost centre and by "above/below"**:

| Memo | Lines | JEs |
|---|---:|---:|
| `SALES BELOW` | 1,627 | 18 |
| `HO BELOW` | 706 | 18 |
| `FACTORY BELOW` | 455 | 41 |
| `ABOVE` | 267 | 4 |
| `HO ABOVE` | 240 | 12 |
| `SALES AND HO SALARY FOR THE …` | 312 | 1 |

Note the shape: **1,627 lines in 18 journals** — about 90 lines each, one per employee. A
payroll journal is a single entry with a line per person, which is why line counts dwarf
journal counts here.

*Inferred:* "above" / "below" is the payroll split above and below a statutory threshold
(PF/ESI ceiling) or above/below-the-line staff. **Not confirmed** — ask HR or Accounts; it
is the single most-used word in the memo vocabulary and nobody has written down what it
means.

### 2. Staff imprest and expense settlement

`2110003` SUNDRY CREDITOR STAFF — **3,074 lines across 1,294 journals**, the highest journal
count of any account. Small amounts, very many entries (Dr ₹1.45 Cr / Cr ₹3.32 Cr).

Memo examples: `BHUPINDER SINGH GINNI IMPRES…` (166 lines / 68 JEs),
`BEING EXPENSE PAYABLE OF M/O…` (160 lines / 44 JEs, ₹3.77 Cr).

### 3. Intercompany

`1110109` **JIVO WELLNESS BEVERAGES INTERNAL** — 719 lines / 532 journals, **Dr ₹63.92 Cr**.
This is the "OIL TO BEVERAGE" transfer `acc/INVENTORY.md` mentions. Also `2121002` SUNDRY
CREDITORS JIVO MART on the payable side. → C-0005, C-0020, [[Business-Partner-Master]]

### 4. Party balance transfers

`1101001` SUNDRY DEBTORS GT (508 lines / 181 JEs) and `1101005` SUNDRY DEBTORS E-COM
(390 lines / 337 JEs, Dr ₹25.33 Cr). Memo: `BEING BALANCE TRANSFERED OF …` — 126 lines /
50 JEs, ₹5.41 Cr. Moving a balance between a customer and a vendor account for the same
party, or between segments.

### 5. Tax reconciliation

- `26AS RECONCILIATION PERTAINI…` — 194 lines / 3 JEs. Reconciling TDS credited to us
  against the income-tax portal's 26AS statement.
- `TCS PAYABLE FOR THE MONTH OF…` — 143 lines / 4 JEs.
- The `2133xxx` TDS family also appears here, so **some TDS is settled by journal rather
  than on the invoice**. → [[TDS-Withholding]]

### 6. Reconciliation clearing

`INTERNAL RECO OIL SAP` — 240 lines / 2 JEs, **₹6.69 Cr**. And `2110008` SUNDRY CREDITORS
CLEARING ACCOUNTS carries 604 lines / 504 JEs, nearly balanced (Dr ₹9.86 Cr / Cr ₹9.74 Cr).
→ [[Internal-Reconciliation]]

### 7. Migration — not an entry at all

`3200003` **OPENING BALANCE ACCOUNT** — 701 lines / 650 journals, **Dr ₹2,949 Cr**. These
are the go-live cutover postings, not business transactions. Any "manual journal volume"
figure that includes them is wrong by two orders of magnitude in value.
→ [[Opening-Balance-and-Cutover]]

## Future-dated entries — the exact answer

The census flagged manual journals dated **2026-12-31** sitting in the books today, and I
guessed "year-end provisions". **Wrong guess, and the real answer is tidier.**

Measured across all three books:

| Book | Manual JEs | Latest `RefDate` | **Future-dated** |
|---|---:|---|---:|
| Oil | 5,235 | 2026-08-21 | **0** |
| Mart | 1,491 | 2026-08-24 | **0** |
| Beverages | 1,364 | 2026-12-31 | **5** |

All five are in Beverages, all manual, and they are **forward-posted prepaid amortisation**:

| `TransId` | `RefDate` | Created | Memo | Dr |
|---:|---|---|---|---:|
| 39939 | 2026-08-31 | 2026-07-18 | Provision for Sidel AUG'26 | ₹3,98,006 |
| 39940 | 2026-09-30 | 2026-07-18 | Provision for Sidel SEP'26 | ₹3,98,006 |
| 39941 | 2026-10-31 | 2026-07-18 | Provision for Sidel OCT'26 | ₹3,98,006 |
| 39942 | 2026-11-30 | 2026-07-18 | Provision for Side Nov'26 | ₹3,98,006 |
| 39943 | 2026-12-31 | 2026-07-18 | Provision for Side Dec'26 | ₹3,98,006 |

Dr `5650016` REPAIR AND MAINTENANCE PLANT & MACHINERY / Cr `1109005` **PREPAID - REPAIR AND
MAINTENANCE (SIDEL)**. Total ₹19.90 lakh, all five created in **one batch on 2026-07-18** to
spread a prepaid maintenance contract over five months.

**So the effect on queries is real but small and bounded:** an "as of today" P&L for
Beverages picks up ₹3.98 lakh of expense dated 2026-08-31 that has not happened yet, and
nothing at all in Oil or Mart. Worth knowing; not worth alarm. Any period query should bound
`RefDate` at both ends, not just the lower one.

## `TransId` is the key, and there are two of them in play

| Field | What it is |
|---|---|
| `OJDT."TransId"` | The journal's own key. **This is the join key to `JDT1`** |
| `OJDT."BatchNum"` | The [[Journal-Voucher]] it came from, if any |
| `OJDT."CreatedBy"` | The source **document's** `DocEntry` for automatic journals |
| Document's `TransId` | Every document header carries the `TransId` of the journal it made |

So the route from a document to its GL side is `OPCH."TransId"` → `JDT1."TransId"`, **not**
via `CreatedBy` — a mistake that cost me a wrong result earlier in this build and returned
zero rows silently.

## C-0023 — why a party ledger must come from here

`JDT1."ShortName"` holds the business partner's `CardCode` on subledger lines. Correction
**C-0023**: build a party ledger from `JDT1` (`OCRD."CardCode"` = `JDT1."ShortName"`), never
from document extracts — 7,478 journals worth ₹3,043 Cr in Oil are invisible otherwise.

This note shows exactly why. Look at what only appears in `JDT1`:

- 3,074 staff-imprest lines that are not on any invoice
- ₹63.92 Cr of intercompany transfer with no document
- ₹5.41 Cr of party balance transfers between accounts
- ₹2,949 Cr of opening balances
- TDS and TCS settled by journal instead of on the bill

A document-based ledger misses all of it. That is not a rounding difference; for some parties
it is the whole balance.

## Dimensions on a manual journal

The `OcrCode` family runs 23–26% on A/P journals overall, but
[[Cost-Centres-and-Dimensions]] establishes that GST, TDS and control-account lines carry
**none by design** — the dimensions live on the expense line.

The same logic applies here, and the payroll memos confirm it: salary is split `SALES` /
`HO` / `FACTORY` **in the memo and in the dimensions**, because that split is the whole point
of the entry. So on a manual journal: **the expense line carries the dimensions; the
balancing payable or control line does not.**

*Confidence medium* — inferred from the payroll pattern and the A/P rule, not measured
line-type by line-type on manual journals specifically. Worth one query.

## Can the CLI make one?

**No.** `sapb1` has four write commands — `draft`, `post`, `patch`, `delete draft`. `draft`
covers document types held in `ODRF`, and a journal entry is never drafted (0 rows in `ODRF`
for it). `post` takes a bare catalogued entity set and is for master data.

This is a statement about the code, not a policy: **nobody has written a write path for
journal entries or for [[Journal-Voucher]].** If Accounts needs one it would have to be
built — and given a journal has no approval step and no draft, it would be the least
guarded write in the toolkit. Worth saying out loud before anyone builds it.

Reading them is fine: the Service Layer's `JournalEntries` entity is keyed on `TransId` and
dated by `ReferenceDate` (not `DocDate`).

## When a manual journal is the right answer

Use one when there is **no document that fits**:

- Payroll and statutory contributions (no vendor bill per employee)
- Moving a balance between two accounts for the same party
- Intercompany transfers
- Provisions and their reversals, prepaid amortisation
- Reconciling an external statement (26AS)
- Correcting something a posted document got wrong that cannot be cancelled

Do **not** use one to fix a vendor bill — that is an [[AP-Credit-Memo]], which keeps the GST
trail. A journal that adjusts a party balance leaves the document open forever and is exactly
what makes `DocStatus` unreliable. **(C-0019)**

## Traps

1. **Dated by `RefDate`, not `DocDate`.** A period filter on the wrong column silently
   returns nothing.
2. **`TransId` is the key.** There is no `DocEntry`, no `DocNum`, no series, no branch on the
   journal header.
3. **A document reaches its journal via the document's own `TransId`**, not via
   `OJDT."CreatedBy"`.
4. **59% come from a [[Journal-Voucher]]** — if you are looking for who authorised an entry,
   look at the voucher, not the journal.
5. **`3200003` OPENING BALANCE ACCOUNT is migration, not activity** — ₹2,949 Cr of it.
   Exclude it from any analysis of what people actually key.
6. **Payroll journals have ~90 lines each.** Line counts and journal counts tell completely
   different stories; say which you mean.
7. **A party ledger built from documents is wrong.** **(C-0023)**
8. **5 Beverages journals are dated in the future.** Bound `RefDate` at both ends.
9. **No approval, no draft, no CLI path.** A manual journal is the least-controlled entry in
   SAP, and 41% of them are keyed with no voucher review either.

## Open questions

1. **What does "above" / "below" mean in the payroll memos?** The most-used term in the whole
   memo vocabulary and it is undocumented. An operator can answer in one sentence.
2. Measure the dimension rule on manual journals directly, by line type — the current
   statement is inferred from the A/P pattern.
3. How is a **reversal** recorded, and does SAP link it to the original? Not established.
   `acc/INVENTORY.md` says provisions and reversals are a use case, so the pattern exists.
4. `INTERNAL RECO OIL SAP` — 240 lines and ₹6.69 Cr in just 2 journals. What is it clearing,
   and is it a recurring process or a one-off cleanup?
5. Cheque dishonour is listed in `acc/INVENTORY.md` as a journal use case but did not surface
   in the memo clusters. Find a real example — it matters for
   [[Incoming-Payment]], which also could not see it.
6. Who keys manual journals directly (the 41% with no voucher), and is that population
   different from the voucher authors?

## Queries used

```sql
-- the taxonomy: cluster the line memos
SELECT UPPER(SUBSTRING(TRIM(L."LineMemo"),1,28)) MEMO, COUNT(*) LINES,
       COUNT(DISTINCT J."TransId") JES, ROUND(SUM(L."Debit"),0) DR
FROM "JIVO_OIL_HANADB"."OJDT" J
JOIN "JIVO_OIL_HANADB"."JDT1" L ON L."TransId"=J."TransId"
WHERE J."TransType"=30 AND L."LineMemo" IS NOT NULL AND TRIM(L."LineMemo")<>''
GROUP BY UPPER(SUBSTRING(TRIM(L."LineMemo"),1,28)) ORDER BY LINES DESC;

-- and the account pairs behind it
SELECT L."Account" AC, MAX(A."AcctName") NM, COUNT(*) LINES,
       COUNT(DISTINCT L."TransId") JES, ROUND(SUM(L."Debit"),0) DR, ROUND(SUM(L."Credit"),0) CR
FROM "JIVO_OIL_HANADB"."OJDT" J
JOIN "JIVO_OIL_HANADB"."JDT1" L ON L."TransId"=J."TransId"
LEFT JOIN "JIVO_OIL_HANADB"."OACT" A ON A."AcctCode"=L."Account"
WHERE J."TransType"=30 GROUP BY L."Account" ORDER BY LINES DESC;

-- future-dated: which book, how many
SELECT COUNT(*) JES, MAX("RefDate") LATEST,
       SUM(CASE WHEN "RefDate">CURRENT_DATE THEN 1 ELSE 0 END) FUTURE
FROM "JIVO_BEVERAGES_HANADB"."OJDT" WHERE "TransType"=30;
-- Oil 0 future | Mart 0 | Bev 5

-- and what they are
SELECT J."TransId", J."RefDate", J."CreateDate", SUBSTRING(J."Memo",1,40) MEMO,
       COUNT(*) LINES, ROUND(SUM(L."Debit"),0) DR
FROM "JIVO_BEVERAGES_HANADB"."OJDT" J
JOIN "JIVO_BEVERAGES_HANADB"."JDT1" L ON L."TransId"=J."TransId"
WHERE J."RefDate" > CURRENT_DATE
GROUP BY J."TransId",J."RefDate",J."CreateDate",SUBSTRING(J."Memo",1,40);
-- 5 Sidel prepaid amortisation entries, Aug-Dec 2026, Rs 3,98,006 each

-- how many manual journals came from a voucher
SELECT COUNT(*) JOURNALS,
       SUM(CASE WHEN "BatchNum" IS NOT NULL AND "BatchNum"<>0 THEN 1 ELSE 0 END) FROM_VOUCHER
FROM "JIVO_OIL_HANADB"."OJDT" WHERE "TransType"=30;
-- 5,235 / 3,102 = 59%
```

Profiles: `_data/profile-OJDT.md`, `profile-JDT1.md`. GL: `_data/gl-30-OIL.md` (with `--memo`).
