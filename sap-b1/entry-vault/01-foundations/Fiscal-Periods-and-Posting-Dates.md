---
type: foundation
sap_tables: [OFPR, OPCH, OJDT, ODRF, OINV, OPDN, NNM1]
objtype: all
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Fiscal periods and posting dates — the field that decides whether the entry is allowed at all

> Every document you key carries four or five different dates, and only one of them
> decides which month the entry lands in. Get that one wrong and either SAP refuses the
> document, or — worse — it accepts it into the wrong month and nobody notices until the
> GST return or the audit. This note is the date half of the pre-flight list.

## The short version

1. **`DocDate` is the posting date.** It, and nothing else, picks the fiscal period. *(Measured: on all 24,368 A/P invoices in all three books, the period stamped on the document contains the `DocDate` — 0 exceptions.)*
2. **`TaxDate` is the vendor's own invoice date.** It never moves the entry. On a purchase bill it is usually *earlier* than `DocDate`; on a sales invoice it is *always* identical.
3. **A period is open or locked per company book.** Right now Oil and Mart have Sep-2026 → Mar-2027 **locked**; Beverages has Sep–Dec 2026 **open**. Same calendar, three different gates.
4. **Every historical month since April 2024 is still open** in Oil and Beverages (and in Mart except Aug–Nov 2024). Nothing at JIVO is ever "closed" after the year ends. Backdating a year is technically possible today.
5. **There is a second gate almost nobody knows about:** each period also carries a permitted `TaxDate` window and a permitted `DocDueDate` window. August 2026 will not accept a vendor bill dated before **2026-04-01** in any of the three books.
6. **The books contain the future.** Five journal entries in Beverages are dated 31-Aug through 31-Dec 2026 and were keyed on 18 July 2026. Any "as of today" figure for Beverages repair & maintenance is overstated by **₹19,90,032**.

## The dates on one document, and who fills them

Measured on Oil `OPCH`, all history unless stated. "Auto" = SAP writes it, the operator never touches it.

| Field | Plain meaning | Who fills it | Decides the period? | Notes |
|---|---|---|---|---|
| `DocDate` | **Posting date.** For a vendor bill = the gate-in date = the [[GRPO]]'s `DocDate` (**C-0017**) | **you** | **YES** | 684 distinct values |
| `TaxDate` | The date printed on the vendor's paper | **you** | no | 1,043 distinct — genuinely a different date |
| `DocDueDate` | When we must pay | auto, from payment terms → [[Payment-Terms-and-Banks]] | no | 918 distinct |
| `CreateDate` | When the row was actually written to the database | auto | no | Read-only. This is your audit trail |
| `UpdateDate` | Last time the row changed | auto | no | |
| `FinncPriod` | The period's internal key (`OFPR."AbsEntry"`) | auto, from `DocDate` | it *records* it | 24 distinct on Oil A/P |
| `PIndicator` | The period's label, e.g. `AUG-26-27` | auto | no | Same token set as [[Numbering-Series]] |
| `Indicator` | — | **nobody** | no | **NULL on 16,334 of 16,334 Oil A/P invoices.** Dead field, do not confuse with `PIndicator` |
| `AssetDate` | — | auto | no | A copy of `DocDate` (equal on 16,331 of 16,334). Ignore it |
| `VatDate` · `ClsDate` · `ReqDate` · `CancelDate` | — | **nobody** | no | NULL on all 16,334. SAP offers them, JIVO never uses them |

**On the journal, the same dates get different names.** The journal SAP writes behind the
document inherits every one of them, exactly — *measured on all 16,108 live Oil A/P
invoices, 16,108 matches, zero drift:*

| On the document (`OPCH`) | On the journal (`OJDT`) |
|---|---|
| `DocDate` | **`RefDate`** |
| `DocDueDate` | `DueDate` |
| `TaxDate` | `TaxDate` |
| `FinncPriod` | `FinncPriod` |

So when a report says "journal entries by `RefDate`", it means by posting date. `OJDT` has
no `PIndicator` — only `Indicator`, and it is a different field again.

### A real document where four dates disagree

Oil A/P invoice **DocNum 626084101**, branch FACTORY:

| | |
|---|---|
| `TaxDate` (vendor's bill is dated) | 2026-07-04 |
| `DocDate` (posted / gate-in) | 2026-08-01 |
| `DocDueDate` (payable) | 2026-08-03 |
| `CreateDate` (actually keyed) | 2026-08-06 |
| `FinncPriod` / `PIndicator` | 45 / `AUG-26-27` |

One bill, four dates, one month. That is the normal case, not an oddity — see the
divergence rates below.

### How often they diverge — all three books, 365 days, live A/P invoices

| | Oil | Mart | Bev |
|---|---:|---:|---:|
| Live A/P invoices in window | 7,380 | 3,230 | 1,447 |
| `TaxDate` ≠ `DocDate` | 3,094 (**42%**) | 1,008 (31%) | 720 (**50%**) |
| …of which `TaxDate` **before** `DocDate` | 3,083 | 1,008 | 718 |
| …of which `TaxDate` **after** `DocDate` ⚠ | **11** | 0 | **2** |
| `DocDueDate` ≠ `DocDate` | 3,436 | 997 | 811 |
| `CreateDate` **after** `DocDate` (backdated) | 7,017 (**95%**) | 2,322 (72%) | 1,403 (**97%**) |
| `CreateDate` **before** `DocDate` (forward-dated) | **0** | **0** | **0** |
| Average keying lag | **18.8 days** | 11.2 days | **21.1 days** |
| Worst keying lag | 84 days | **110 days** | 52 days |

Two things fall straight out of that:

- **A purchase bill is essentially always backdated.** Nobody keys a vendor bill on the day
  it is dated; the average bill lands about three weeks after the date it posts on. That is
  the process, not a fault — but it means the period you need open is last month's, not
  this month's.
- **The 11 Oil and 2 Bev invoices whose `TaxDate` is *after* the posting date are wrong on
  their face** — a bill cannot be dated after the goods came through the gate. Worth a look.

### Sales invoices behave completely differently

Same 365 days, live [[AR-Invoice]]s:

| | Oil | Mart | Bev |
|---|---:|---:|---:|
| Invoices | 8,849 | 13,399 | 3,317 |
| `TaxDate` = `DocDate` | **8,849 (100%)** | **13,399 (100%)** | **3,317 (100%)** |
| Keyed same day | 8,566 (97%) | 10,190 (76%) | 3,233 (97%) |
| Average keying lag | 0.14 days | 1.47 days | 0.16 days |

**`TaxDate` ≠ `DocDate` is a purchase-side phenomenon only.** On the sales side the two
dates are the same number by construction — we write the invoice, so our date *is* the tax
date. If you ever see a sales invoice where they differ, something was edited.

## The fiscal calendar at JIVO — what `OFPR` actually contains

`OFPR` is the posting-period master. **36 rows per book, 108 in the group** — matching the
[[Entry-Types-Census]]. The whole table is 18 columns wide and there is **no `Locked`
column**: `PeriodStat` is the entire status.

| | |
|---|---|
| Year start | **1 April** (`F_RefDate` of every `-01` period) |
| Years defined | `FY2425`, `FY2526`, `FY2627` — 12 periods each, in `Category` |
| Period length | one calendar month; `SubNum` 1–12 = Apr…Mar |
| Adjustment / 13th period | **none.** There is no year-end period to park closing entries in — they go into March |
| `Code` | `FY2627-05` = fifth month of FY26-27 = **August 2026** |
| `Indicator` | `AUG-26-27` — the label that also names the numbering series → [[Numbering-Series]] |
| `AbsEntry` | the internal key that lands on the document as `FinncPriod` |

### The four date windows on every period

This is the part that surprises people. A period does not just say "August"; it carries
three separate permitted-date ranges, and SAP checks all of them.

| `OFPR` pair | Gates which document field | Oil August 2026 | Mart August 2026 | Bev August 2026 |
|---|---|---|---|---|
| `F_RefDate` … `T_RefDate` | **`DocDate`** — the period's own month | 2026-08-01 → 08-31 | same | same |
| `F_TaxDate` … `T_TaxDate` | **`TaxDate`** | 2026-04-01 → 2027-03-31 | same | same |
| `F_DueDate` … `T_DueDate` | **`DocDueDate`** | 2026-04-01 → 2027-03-31 | same | same |

**Read that tax window again.** As things stand on 2026-08-24, an August posting will not
accept a vendor bill dated before **1 April 2026** in any of the three books. An old bill
has to go into a period whose window reaches back far enough — or somebody has to widen the
window.

And they do widen it. *(Measured — the current `F_TaxDate` on Oil's FY26-27 periods, and how
many bills older than the financial year each one is carrying:)*

| Oil period | `F_TaxDate` today | A/P invoices with a pre-April-2026 bill date | Oldest bill in there |
|---|---|---:|---|
| `FY2627-01` APR-26-27 | 2025-05-01 | 68 | 2025-10-31 |
| `FY2627-02` MAY-26-27 | **2024-05-13** | 25 | 2025-05-12 |
| `FY2627-03` JUN-26-27 | **2024-05-10** | 12 | 2025-10-31 |
| `FY2627-04` JUL-26-27 | 2025-01-01 | 4 | 2025-11-01 |
| `FY2627-05` AUG-26-27 | 2026-04-01 | **0** | — |

Zero in August is not a coincidence — August's window is still narrow. The other four were
pushed back to let old paper in. The most extreme edits in the group: Oil's Sep-2024 period
allows due dates from **2014-04-01** and tax dates from **2017-04-01**; Beverages' Apr-2026
period allows tax dates from **2002-06-01**.

**The window is a live gate, not a record of history.** 203 Oil A/P invoices sit in the
June-2025 period carrying vendor dates from 2025-02-28 to 2025-05-31 — outside that
period's *current* window, which now starts 2025-06-01. They were keyed in June–July 2025;
the period row was last edited 2026-06-05. The window was opened, used, then narrowed again
a year later. *(Measured. Only 203 Oil + 2 Bev documents in the whole group violate their
period's current tax window, and `DocDueDate` violates its window on **zero** of 24,368
documents.)*

### Dead columns in `OFPR`

`Free2` = `Y` and `Free3` = `N` on all 108 rows; `Free`, `Free1`, `AddNum` NULL on all;
`Addition` = `N`, `DataSource` = `N`, `UserSign` = 1. None of them mean anything at JIVO.
`WasStatChd` = `Y` marks a period whose status has been changed at least once (28 of 36 in
Oil) — useful only as a hint that somebody has been in there.

## Which periods are OPEN right now — 2026-08-24, all three books

`PeriodStat` has exactly two values in all three books: **`N` = open, `Y` = locked**.
*(Inferred from the values, then confirmed against postings: Oil's seven `Y` periods hold
**0** journal entries between them, while Beverages' `N` periods for Sep–Dec 2026 hold real
ones.)*

| Months | Oil | Mart | Beverages |
|---|---|---|---|
| Apr 2024 – Jul 2024 | open | open | open |
| **Aug 2024 – Nov 2024** | open | **LOCKED** | open |
| Dec 2024 – Mar 2026 | open | open | open |
| Apr 2026 – Jul 2026 | open | open | open |
| **Aug 2026 (current)** | **open** | **open** | **open** |
| **Sep 2026 – Dec 2026** | **LOCKED** | **LOCKED** | **open** ⚠ |
| Jan 2027 – Mar 2027 | LOCKED | LOCKED | LOCKED |
| **Locked periods, total** | **7 of 36** | **11 of 36** | **3 of 36** |

Three things worth saying out loud:

- **Nothing is ever closed after the fact.** Every FY24-25 and FY25-26 period in Oil and
  Beverages is still `PeriodStat = 'N'` today. The financial year ended on 2026-03-31 and
  April 2025 is still open for posting.
- **Mart is the only book where anyone has ever closed a historical month** — Aug, Sep, Oct
  and Nov 2024, all sealed on 2025-01-01. Oct-2024 still contains 12 postings (cancellation
  journals keyed 2024-10-03/04): **locking a period does not remove what is already in it.**
- **Beverages is four months more open than the other two.** That is not an oversight —
  see the future-dated entries below.

### Locking a period is not the same as having no series

Oil has **18 A/P numbering series defined for each of Sep-26 through Mar-27**, all sitting
ready, while those periods are locked. The reverse also happens (a branch with no series
can never bill — see [[Numbering-Series]]). **Two independent gates:** the period has to be
open *and* a series has to exist for that month, branch and sub-type.

## `FinncPriod` and `PIndicator` — what they are and when to trust them

*Measured on all 24,368 A/P invoices, all three books:*

| Check | Result |
|---|---|
| `FinncPriod` resolves to a real `OFPR."AbsEntry"` | 24,368 / 24,368 |
| `DocDate` falls inside that period's `F_RefDate…T_RefDate` | 24,368 / 24,368 |
| `PIndicator` = that period's `Indicator` | 24,368 / 24,368 |
| Document `Indicator` filled | **0 / 24,368** |

So on a **posted** document, `FinncPriod` is a reliable, derived fact: it is `DocDate`'s
month and nothing else. You never set it; SAP does.

**On a draft it is not reliable.** Of 15,352 Oil A/P drafts, `FinncPriod` matches the
draft's own `DocDate` on 14,591 (95%) — and on **761 it points at a different month**.
`FY2627-05` (August) drafts carry `DocDate` values from 2026-07-04 to 2026-08-22. The stamp
was written when the draft was created and never refreshed when the date was edited; SAP
recomputes it from `DocDate` at Add. *(The 761 do not cleanly match `CreateDate`'s period
either — 316 do, 277 match `UpdateDate`'s. Mechanism **unverified**.)* **Never read a
draft's period; read its `DocDate`.** → [[Document-Drafts]]

### `PIndicator` is not a safe key in Mart or Beverages

`OFPR."Indicator"` is supposed to be one label per period. In **both** Mart and Beverages
it is not: `FY2526-01` (April 2025) and `FY2526-02` (May 2025) are **both labelled
`Apr-25-26`**. Consequences, measured:

| | Mart | Bev |
|---|---:|---:|
| A/P invoices carrying `PIndicator = 'Apr-25-26'` | 379 | 287 |
| Distinct calendar months those cover | **2** | **2** |
| Numbering series pointing at `May-25-26`, a label no period has | **62** | **69** |
| Oil equivalents | 0 | 0 |

Oil is clean (2,800 series, zero orphan indicators). **Group anything by `FinncPriod`, never
by `PIndicator`** — and never join the label across books at all: Oil writes `JUN-25-26`
where Mart and Beverages write `June-25-26`, and FY24-25 is Title case everywhere while
FY26-27 is upper case.

## How far back a period stays open — measured, not assumed

The last time anybody wrote a posting into each month, per book. `OJDT` by `RefDate`
month, `MAX(CreateDate)`.

| Posting month | Oil — last keyed | days after month end | Mart — last keyed | Bev — last keyed |
|---|---|---:|---|---|
| 2025-04 | 2026-05-19 | **384** | 2026-05-02 | 2026-05-13 |
| 2025-06 | 2026-05-28 | 332 | 2026-05-02 | 2026-05-29 |
| 2025-12 | 2026-05-27 | 147 | 2026-06-10 | 2026-03-21 |
| 2026-03 | 2026-08-10 | 132 | 2026-08-10 | 2026-06-13 |
| 2026-04 | 2026-08-12 | 104 | 2026-08-05 | 2026-08-07 |
| 2026-07 | 2026-08-24 | 24 | 2026-08-24 | 2026-08-24 |

**A period at JIVO stays writable for as long as somebody needs it.** FY25-26 months were
still receiving postings in late May 2026, more than a year after the earliest of them
ended. And 503 Oil A/P invoices were posted into **March 2026** after 1 April 2026 (last one
2026-05-25) — Mart 151 (last 2026-06-11), Bev 81 (last 2026-04-27). That is the year-end
catch-up, and it is normal here.

**Practical consequence for the operator:** the period you want is almost certainly open.
If it is not, the block is more likely the `TaxDate` window than the period status.

### What SAP says when the period is shut

| What you did | SAP's answer |
|---|---|
| Posted into a locked period (`PeriodStat = 'Y'`) | **`-4013` "Posting period locked; specify an alt…"** — captured verbatim from a real failed Service Layer `POST` in the OMS→SAP log (`connections/lineage-evidence/sourcemaps/oms-cli.md`; the stored message is truncated there) |
| A date outside the period's permitted window | "Date deviates from permissible range" |
| No series for that month/branch/sub-type | `-10` / `-4002` "define the numbering series" → [[Numbering-Series]] |

Neither of the first two is fixable from a terminal. **A locked period is opened by an SAP
superuser in Administration → System Initialisation → Posting Periods; a date window is
widened in the same screen.** The `sapb1` CLI cannot read or change either — `OFPR` has no
entity set, and `hana-sql` is the only read path. *(The existing line in
[[Numbering-Series]] maps "Date deviates from permissible range" to `PeriodStat = 'Y'`.
On this evidence those are two different failures: `-4013` is the lock, "date deviates" is
the window. Worth correcting there.)*

## Reconciling the receipt-to-bill gap — C-0017 vs C-0022 vs 57%

Three numbers have been quoted for the same thing. They are all correct and they measure
three different things. Every figure below is `PCH1."BaseType" = 20` joined to its
[[GRPO]], comparing `OPCH."DocDate"` with `OPDN."DocDate"`.

| Basis | Oil | Mart | Bev |
|---|---:|---:|---:|
| **Document pairs, all history, dates *equal*** | **5,283 / 10,299 = 51.3%** | **2,555 / 3,035 = 84.2%** | **912 / 4,342 = 21.0%** |
| Lines, all history, equal | 12,608 / 22,125 = 57.0% | 11,945 / 14,231 = 83.9% | 2,106 / 6,418 = 32.8% |
| Lines, last 365 days, equal | 6,360 / 11,187 = 56.9% | 7,166 / 8,262 = 86.7% | 854 / 3,578 = 23.9% |
| Lines, last 365 days, same day **or earlier** | 6,360 = 56.9% | 7,214 = 87.3% | 877 = 24.5% |

**The first row is C-0022, exactly: 51% / 84% / 21%.** It counts *document pairs over all
history*. The 57% figure is the second and third rows — *lines*, and it happens to be
almost identical in both windows.

**Which is the better statement of the rule?**

- For an operator holding **one invoice** and asking "can I read the gate-in date off this?"
  → the **document-pair** number is the honest one. **51% in Oil.** A coin flip.
- For "how much of our purchase *volume* was posted on the receipt date?" → the line number,
  57% in Oil. Lines cluster: a multi-line invoice copied wholesale from one GRPO tends to be
  same-day, which is why the line view flatters the rule.

So: **quote 51/84/21 (C-0022 stands), and keep 57% as the line-weighted view.** The two do
not conflict; the earlier note in [[GRPO]] treated them as "close enough to trust both",
which is right but under-sold — they are the same underlying data cut two ways, and the
gap is a weighting effect, not measurement noise.

Three more things from the same join:

- **"Same day or earlier" and "same day" are the same statistic in Oil** — `LT` = **0**. Not
  one Oil A/P invoice in 365 days was posted *before* its own GRPO.
- **Mart and Beverages do have that anomaly**: 48 Mart and 23 Bev lines in 365 days sit on
  an invoice dated earlier than the receipt it was copied from. A bill cannot precede the
  goods; those are date errors.
- **Beverages is the book where the rule is ignored** — 21% by document. Whatever the Bev
  process is, it is not "post on the GRPO's date". Do not carry Oil's habits into that book.

**C-0017 remains the posting rule. C-0022 remains the reading rule.** Post on the GRPO's
`DocDate`; never infer a gate-in date from an A/P invoice you find in the books.

## The future is already in the books — Beverages, ₹19,90,032

*(Measured: `OJDT` where `RefDate > CURRENT_DATE`, all three books.)*

**Oil: none. Mart: none. Beverages: five.**

| `RefDate` | JE no. | Memo | Amount |
|---|---|---|---:|
| 2026-08-31 | 826880001 | Provision for Sidel AUG'26 | ₹3,98,006.46 |
| 2026-09-30 | 926880001 | Provision for Sidel SEP'26 | ₹3,98,006.46 |
| 2026-10-31 | 1026880001 | Provision for Sidel OCT'26 | ₹3,98,006.46 |
| 2026-11-30 | 1126880001 | Provision for Side Nov'26 | ₹3,98,006.46 |
| 2026-12-31 | 1226880001 | Provision for Side Dec'26 | ₹3,98,006.46 |
| | | **Total dated in the future** | **₹19,90,032.31** |

They are **not** year-end provisions. Each is a two-line monthly amortisation of a prepaid
maintenance contract on the Sidel bottling line:

| Line | Account | Name | Side | Dimensions |
|---|---|---|---|---|
| 0 | `5650016` | REPAIR AND MAINTENANCE PLANT & MACHINERY | **Dr** | `ProfitCode` = WATER, `OcrCode3` = Factory |
| 1 | `1109005` | PREPAID - REPAIR AND MAINTENANCE (SIDEL) | **Cr** | *(none — the credit line carries no dimension)* |

The whole run — Jun-26 through Dec-26, seven entries — was keyed **in one sitting on
2026-07-18** by `UserSign` 10 = `USER01` (Avtar's login; that login is shared, so the
person is not certain → [[Operators-and-Logins]]). Six of the seven were future-dated when
keyed. Each got its own month's JV series (2923–2927).

**And that is why Beverages' Sep–Dec 2026 periods are open.** The `UpdateDate` on Bev
`OFPR` rows for Aug, Sep, Oct, Nov and Dec 2026 is **2026-07-18** — the same day those
journals were created. *(Correlation is measured; the causal read — somebody opened four
future periods to key the whole contract at once — is **inferred**, but nothing else fits.)*

### What this does to an "as of now" query

| | |
|---|---|
| `5650016` current balance (Bev) | ₹1,17,37,773 |
| …of which dated after today | **₹19,90,032 (17%)** |
| `1109005` prepaid remaining | ₹4,92,645 — about 1.2 months at this rate |

**Any Beverages P&L, expense report or account balance that does not filter on the date
overstates repair & maintenance by ₹19.90 lakh.** `OACT."CurrTotal"` includes it. So does
any `SUM` over `JDT1` without a date bound.

**The fix is one clause:** `AND "RefDate" <= CURRENT_DATE` on every Beverages ledger query.
Add it by reflex — it costs nothing in the other two books, which have no future rows today.
→ [[Journal-Entry]]

### A related date trap in the same table

`TransType = -3` — the 436 Oil / 314 Mart / 202 Bev rows the [[Entry-Types-Census]] calls
the cutover — are dated **2025-03-31 and 2025-04-01** but were **created on 2026-02-09**
(Oil and Bev) and **2025-11-25** (Mart). Oil's genuinely earliest posting is `RefDate`
2024-08-01, first keyed 2024-10-01. So `-3` is the **FY24-25 → FY25-26 year-end
carry-forward**, generated ten months after the date it bears — not the go-live cutover.
The census's date is right; its label needs the nuance. → [[Opening-Balance-and-Cutover]]

## How the three books differ

The classic wrong entry in this area is measuring one book and asserting it for another.

| | Oil | Mart | Beverages |
|---|---|---|---|
| `OFPR` rows | 36 | 36 | 36 |
| Year start / period length | 1 Apr / monthly | same | same |
| Locked periods today | 7 (Sep-26→Mar-27) | **11** (+ Aug–Nov 2024) | **3** (Jan→Mar 2027 only) |
| Sep–Dec 2026 | **locked** | **locked** | **open** |
| `AbsEntry` for FY26-27 | **41–52** | 27–38 | 27–38 |
| Duplicate `Indicator` label | none | **`Apr-25-26` ×2** | **`Apr-25-26` ×2** |
| Orphan series indicators | 0 of 2,800 | 62 (`May-25-26`) | 69 (`May-25-26`) |
| `Indicator` casing, FY25-26 | `JUN-25-26` | `June-25-26` | `June-25-26` |
| Future-dated journals | none | none | **5** |
| A/P average keying lag | 18.8 d | 11.2 d | 21.1 d |
| A/P posted on the GRPO's date (doc pairs) | 51% | 84% | **21%** |

**`AbsEntry` is not comparable across books.** Oil's August 2026 is period **45**; Mart's
and Beverages' is period **31**. A `FinncPriod` value carries no meaning without its book.
*(Oil's `AbsEntry` skips 13 and 26–40; Mart and Bev skip 13 and 26. **Unverified** why —
most likely period rows created and deleted during setup.)*

## Which documents it touches

Every one. `DocDate` gates the lot, and the same `FinncPriod` / `PIndicator` pair lands on
each: [[AP-Invoice]] · [[AR-Invoice]] · [[GRPO]] · [[AP-Credit-Memo]] · [[AR-Credit-Memo]] ·
[[Journal-Entry]] · [[Journal-Voucher]] · [[Incoming-Payment]] · [[Outgoing-Payment]] ·
[[Delivery]] · [[Stock-Transfer]] · [[Goods-Receipt]] · [[Goods-Issue]] ·
[[Document-Drafts]]. It also decides which series you may use — [[Numbering-Series]].

## Pre-flight — the date questions, before the screen opens

- [ ] **Which book.** The period calendar is the same shape in all three, but the open/locked
      pattern and the `AbsEntry` numbers are not.
- [ ] **What is the posting date?** For a vendor bill: the [[GRPO]]'s `DocDate` = the gate-in
      date (**C-0017**). Not today. Not the vendor's date.
- [ ] **Is that month open in *this* book?**
      `SELECT "Code","PeriodStat" FROM "JIVO_<BOOK>_HANADB"."OFPR" WHERE <your date> BETWEEN "F_RefDate" AND "T_RefDate"`
      → `N` means go.
- [ ] **Is the vendor's invoice date inside that period's tax window?** Same row,
      `F_TaxDate`…`T_TaxDate`. **A bill older than 1 April 2026 will not go into August
      2026 in any book.** This is the check that gets skipped.
- [ ] **Does a series exist for that month + branch + sub-type?** → [[Numbering-Series]].
      A series existing does not mean the period is open, and vice versa.
- [ ] **Is it a service bill covering a period?** `U_*` from/to dates are not the posting
      date; the posting date is still one day.
- [ ] **Crossing a year end?** Anything dated 2026-03-31 or earlier lands in FY25-26 — still
      open in all three books, but it changes the series, the GST return and the audit file.
- [ ] **Do not set `FinncPriod`, `PIndicator`, `AssetDate` or `Indicator`.** SAP fills the
      first three and nobody fills the last.

## Traps

1. **`TaxDate` never moves the entry.** Operators reach for it because it is the date on the
   paper. It is the *vendor's* date; `DocDate` is *ours*, and `DocDate` alone picks the
   period. Getting them the wrong way round posts the bill in the wrong month and puts the
   wrong month on the GST return.
2. **The tax-date window is a real gate and it is invisible on the document.** August 2026
   refuses any bill dated before 2026-04-01, in all three books. The document screen does
   not show you the window; only `OFPR` does.
3. **Almost nothing is ever closed.** Every month since April 2024 is open in Oil and
   Beverages. You *can* post into April 2025 today, and 503 Oil invoices went into
   March 2026 after the year ended. Treat "the period is closed" as a claim to verify, not
   an assumption — and treat any historical figure as re-writable.
4. **A period open in Oil may be locked in Mart.** Sep–Dec 2026: locked in Oil and Mart,
   **open in Beverages**. Aug–Nov 2024: open in Oil and Bev, locked in Mart. Check the book
   you are in.
5. **Locking a period does not clean it.** Mart's locked Oct-2024 still holds 12 postings.
6. **`FinncPriod` on a draft is stale** — wrong on 761 of 15,352 Oil A/P drafts. Read the
   draft's `DocDate`. SAP recomputes the period at Add, so a draft keyed in August for a
   July date posts into July, whatever the draft row says.
7. **`PIndicator` is not a unique period key in Mart or Beverages** — `Apr-25-26` labels two
   different months in both, covering 379 Mart and 287 Bev A/P invoices. Group by
   `FinncPriod`. And never join `Indicator` text across books: the casing differs.
8. **`Indicator` on a document is not `PIndicator`.** It is NULL on every single A/P invoice
   in all three books. Two similarly named fields, one of them dead.
9. **Beverages contains ₹19.90 lakh of expense that has not happened yet.** Filter
   `RefDate <= CURRENT_DATE` on every Beverages ledger query. `OACT."CurrTotal"` already
   includes the future.
10. **The books were still being written a year after the fact.** The last posting into
    April 2025 was keyed on 2026-05-19. Any "final" figure for a past month has a shelf life
    — re-pull it rather than quoting an old extract.
11. **`CreateDate` is the only honest record of when work happened.** `DocDate` is a
    decision, not an event: 95% of Oil A/P invoices are backdated, some by 84 days
    (Mart: 110). Never use `DocDate` to measure throughput or to attribute work to a day.

## Checking afterwards that you got it right

```sql
-- 1. the period the document actually landed in, and whether that period is open
SELECT H."DocNum", TO_VARCHAR(H."DocDate",'YYYY-MM-DD') POSTED,
       TO_VARCHAR(H."TaxDate",'YYYY-MM-DD') VENDOR_BILL_DATE,
       TO_VARCHAR(H."DocDueDate",'YYYY-MM-DD') PAYABLE,
       TO_VARCHAR(H."CreateDate",'YYYY-MM-DD') KEYED,
       P."Code", P."Indicator", P."PeriodStat"
FROM "JIVO_OIL_HANADB"."OPCH" H
JOIN "JIVO_OIL_HANADB"."OFPR" P ON P."AbsEntry" = H."FinncPriod"
WHERE H."DocNum" = <your DocNum>;

-- 2. did the journal inherit the same dates? (it always should)
SELECT TO_VARCHAR(J."RefDate",'YYYY-MM-DD') JE_POSTED,
       TO_VARCHAR(J."TaxDate",'YYYY-MM-DD') JE_TAX,
       TO_VARCHAR(J."DueDate",'YYYY-MM-DD') JE_DUE, J."FinncPriod"
FROM "JIVO_OIL_HANADB"."OPCH" H
JOIN "JIVO_OIL_HANADB"."OJDT" J ON J."TransId" = H."TransId"
WHERE H."DocNum" = <your DocNum>;

-- 3. before you post: is the month open and will it take this bill date?
SELECT "Code","Indicator","PeriodStat",
       TO_VARCHAR("F_RefDate",'YYYY-MM-DD')||' → '||TO_VARCHAR("T_RefDate",'YYYY-MM-DD') DOCDATE_WINDOW,
       TO_VARCHAR("F_TaxDate",'YYYY-MM-DD')||' → '||TO_VARCHAR("T_TaxDate",'YYYY-MM-DD') TAXDATE_WINDOW,
       TO_VARCHAR("F_DueDate",'YYYY-MM-DD')||' → '||TO_VARCHAR("T_DueDate",'YYYY-MM-DD') DUEDATE_WINDOW
FROM "JIVO_OIL_HANADB"."OFPR"
WHERE '2026-08-15' BETWEEN "F_RefDate" AND "T_RefDate";
```

## Open questions

- **Who can open a locked period, and does JIVO log it?** `OFPR` records only `UserSign`
  (= 1 on all 108 rows, i.e. the row's original creator) and `UpdateDate`. There is no
  "who changed the status" column and this SAP version's `OUSR` has no superuser flag I
  could read. Would need the SAP client's authorisation screen, or `ADOC`-style change
  logging if it is switched on.
- **The exact full text of the `-4013` locked-period message.** The one live capture is
  truncated in the OMS log (`Posting period locked; specify an alt…`). Closing it means
  reading the untruncated `sales_quotation_logs.error_message` — and postsql's credential
  has been dead fleet-wide since 2026-08-06.
- **Why `AbsEntry` 13, 26 and (in Oil) 27–40 are missing.** Deleted setup rows is the
  obvious guess; not verified.
- **Why 761 Oil drafts carry a period matching neither their `DocDate` nor their
  `CreateDate` nor their `UpdateDate`.** The stamp is clearly written once and left, but
  I could not pin down at which moment.
- **Whether the four Mart months locked on 2025-01-01 were locked deliberately or as part
  of go-live tidying.** Mart's own first posting is 2024-10-03, so Aug and Sep 2024 were
  never used at all.
- **Is anyone watching the Beverages future rows?** They will become "current" month by
  month, so no correction is needed — but nothing in the books flags that ₹19.90 lakh of an
  expense account is not yet real.

## Queries used

```sql
-- the whole fiscal calendar, per book (repeat for JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB)
SELECT "AbsEntry","Code","Category","SubNum","Indicator",
       "F_RefDate","T_RefDate","F_DueDate","T_DueDate","F_TaxDate","T_TaxDate",
       "PeriodStat","WasStatChd","Free2","Free3","Addition","DataSource","UpdateDate"
FROM "JIVO_OIL_HANADB"."OFPR" ORDER BY "F_RefDate";

-- OFPR's full column list — there is no "Locked" column
SELECT COLUMN_NAME, DATA_TYPE_NAME, POSITION FROM SYS.TABLE_COLUMNS
WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND TABLE_NAME='OFPR' ORDER BY POSITION;

-- do locked periods hold anything?
SELECT P."Code",P."PeriodStat",COUNT(J."TransId")
FROM "JIVO_MART_HANADB"."OFPR" P
LEFT JOIN "JIVO_MART_HANADB"."OJDT" J ON J."FinncPriod"=P."AbsEntry"
WHERE P."PeriodStat"='Y' GROUP BY P."Code",P."PeriodStat";

-- date divergence on A/P invoices
SELECT COUNT(*),
  SUM(CASE WHEN "TaxDate"<>"DocDate" THEN 1 ELSE 0 END),
  SUM(CASE WHEN "DocDueDate"<>"DocDate" THEN 1 ELSE 0 END),
  SUM(CASE WHEN TO_DATE("CreateDate")>"DocDate" THEN 1 ELSE 0 END),
  SUM(CASE WHEN TO_DATE("CreateDate")<"DocDate" THEN 1 ELSE 0 END),
  AVG(DAYS_BETWEEN("DocDate",TO_DATE("CreateDate"))),
  MAX(DAYS_BETWEEN("DocDate",TO_DATE("CreateDate")))
FROM "JIVO_OIL_HANADB"."OPCH"
WHERE "DocDate">=ADD_DAYS(CURRENT_DATE,-365) AND "CANCELED"='N';

-- FinncPriod / PIndicator integrity, and the three windows
SELECT COUNT(*),
  SUM(CASE WHEN P."AbsEntry" IS NULL THEN 1 ELSE 0 END),
  SUM(CASE WHEN H."DocDate" BETWEEN P."F_RefDate" AND P."T_RefDate" THEN 0 ELSE 1 END),
  SUM(CASE WHEN H."PIndicator"=P."Indicator" THEN 0 ELSE 1 END),
  SUM(CASE WHEN H."Indicator" IS NULL THEN 1 ELSE 0 END),
  SUM(CASE WHEN H."TaxDate" BETWEEN P."F_TaxDate" AND P."T_TaxDate" THEN 0 ELSE 1 END),
  SUM(CASE WHEN H."DocDueDate" BETWEEN P."F_DueDate" AND P."T_DueDate" THEN 0 ELSE 1 END)
FROM "JIVO_OIL_HANADB"."OPCH" H
LEFT JOIN "JIVO_OIL_HANADB"."OFPR" P ON P."AbsEntry"=H."FinncPriod";

-- the journal inherits every date
SELECT COUNT(*),
  SUM(CASE WHEN J."RefDate"=H."DocDate" THEN 1 ELSE 0 END),
  SUM(CASE WHEN J."TaxDate"=H."TaxDate" THEN 1 ELSE 0 END),
  SUM(CASE WHEN J."DueDate"=H."DocDueDate" THEN 1 ELSE 0 END),
  SUM(CASE WHEN J."FinncPriod"=H."FinncPriod" THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."OPCH" H
JOIN "JIVO_OIL_HANADB"."OJDT" J ON J."TransId"=H."TransId" WHERE H."CANCELED"='N';

-- a draft's period stamp vs its own DocDate
SELECT COUNT(*),
  SUM(CASE WHEN D."DocDate" BETWEEN P."F_RefDate" AND P."T_RefDate" THEN 1 ELSE 0 END),
  SUM(CASE WHEN TO_DATE(D."CreateDate") BETWEEN P."F_RefDate" AND P."T_RefDate" THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."ODRF" D
JOIN "JIVO_OIL_HANADB"."OFPR" P ON P."AbsEntry"=D."FinncPriod" WHERE D."ObjType"='18';

-- how long each period kept accepting postings
SELECT TO_VARCHAR("RefDate",'YYYY-MM'), COUNT(*), MAX("CreateDate")
FROM "JIVO_OIL_HANADB"."OJDT"
WHERE "RefDate">=ADD_DAYS(CURRENT_DATE,-500) AND "RefDate"<=CURRENT_DATE
GROUP BY TO_VARCHAR("RefDate",'YYYY-MM') ORDER BY 1;

-- GRPO -> A/P gap, the four ways (lines shown; swap in DISTINCT DocEntry/BaseEntry for pairs)
SELECT COUNT(*),
  SUM(CASE WHEN PH."DocDate"=GH."DocDate" THEN 1 ELSE 0 END),
  SUM(CASE WHEN PH."DocDate"<=GH."DocDate" THEN 1 ELSE 0 END),
  SUM(CASE WHEN PH."DocDate"<GH."DocDate" THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."PCH1" P
JOIN "JIVO_OIL_HANADB"."OPCH" PH ON PH."DocEntry"=P."DocEntry"
JOIN "JIVO_OIL_HANADB"."OPDN" GH ON GH."DocEntry"=P."BaseEntry"
WHERE P."BaseType"=20;

-- everything dated in the future, all three books
SELECT TO_VARCHAR("RefDate",'YYYY-MM-DD'),"TransType",COUNT(*),MIN("CreateDate"),SUM("LocTotal")
FROM "JIVO_BEVERAGES_HANADB"."OJDT" WHERE "RefDate">CURRENT_DATE
GROUP BY "RefDate","TransType" ORDER BY 1;

-- widened tax windows carrying pre-year bills
SELECT P."Code",P."Indicator",P."F_TaxDate",COUNT(*),MIN(H."TaxDate")
FROM "JIVO_OIL_HANADB"."OPCH" H
JOIN "JIVO_OIL_HANADB"."OFPR" P ON P."AbsEntry"=H."FinncPriod"
WHERE P."Category"='FY2627' AND H."TaxDate"<'2026-04-01'
GROUP BY P."Code",P."Indicator",P."F_TaxDate" ORDER BY 1;

-- duplicate period labels, and series pointing at a label no period has
SELECT "Indicator",COUNT(*) FROM "JIVO_MART_HANADB"."OFPR" GROUP BY "Indicator" HAVING COUNT(*)>1;
SELECT N."Indicator",COUNT(*) FROM "JIVO_MART_HANADB"."NNM1" N
LEFT JOIN "JIVO_MART_HANADB"."OFPR" P ON P."Indicator"=N."Indicator"
WHERE N."Indicator"<>'Default' AND P."Indicator" IS NULL GROUP BY N."Indicator";
```

Field fill rates and value vocabularies come from the mined corpus:
`_data/profile-OFPR.md`, `_data/profile-OPCH.md`, `_data/profile-NNM1.md`,
`_data/profile-ODRF.md`. Re-run with
`python3 sap-b1/entry-vault/bin/profile.py OFPR --co OIL,MART,BEV`.
