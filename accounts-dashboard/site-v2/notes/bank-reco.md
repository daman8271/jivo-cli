# bank-reco — bank reconciliation from inside SAP only

**Section id:** `bank-reco`
**SQL:** `pipeline/sql/bank-reco.sql` (summary, 50 cols) + `pipeline/sql/bank-reco-detail.sql` (event log, 16 cols)
**Raw output:** `pipeline/raw/bank-reco.{oil,mart,bev}.tsv`, `pipeline/raw/bank-reco-detail.{oil,mart,bev}.tsv`
**As-of used for every number below:** 2026-08-21. Everything here was pulled live from HANA on 2026-08-21 unless marked INFERRED.
**Money unit:** every `_L` column is **INR lakhs**. Counts end `_N`. `_PCT` is a percentage.

---

## The headline answer

**A real bank reconciliation cannot be done from SAP alone, and at JIVO it largely is not being done at all.** (VERIFIED)

Three separate facts, each checked in all three company books:

1. **No bank statement has ever entered SAP.** `BNK1` = **0 rows** and `BNK2` = **0 rows** in Oil, Mart and Beverages. There is not one statement line in the system to match anything against.
2. **`OBNK` is not a statement table here — it is a reconciliation *log*.** It holds exactly **one row per reconciliation event**: `COUNT(*)` equals `COUNT(DISTINCT "BankMatch")` on **every** account in **every** book. Each row carries a single lump bank-side figure for that month. SAP records the *conclusion* of a reconciliation, never the statement it was reconciled against.
3. **Coverage is thin and lopsided.** Of 132 bank / cash / bank-facility G/L accounts across the three books, **23 have ever been reconciled**: Oil 19 of 70, Mart **2 of 44**, Beverages **2 of 18**. Mart has **7 reconciliation events in almost two years of trading**, on a book that has pushed ₹765 crore of gross movement through its bank accounts.

And there is nothing to age as an "uncleared cheque": **there are no cheques in SAP at all.** `RCT1`, `VPM1`, `OCHO`, `OCHH`, `ODPS`, `DPS1` are all **0 rows** in all three books, and `"CheckSum" <> 0` on **zero** uncancelled receipts or payments. Payment means split, uncancelled (VERIFIED):

| Book | receipts | by transfer | by cash | by cheque | payments | by transfer | by cash | by cheque |
|---|---|---|---|---|---|---|---|---|
| Oil  | 13,628 | 12,401 | 1,227 | **0** | 13,846 | 13,770 | 10 | **0** |
| Mart | 11,128 |  8,720 | 2,408 | **0** |  2,064 |  2,060 |  4 | **0** |
| Bev  |  4,035 |  2,704 | 1,331 | **0** |  1,779 |  1,769 | 10 | **0** |

JIVO banks 100% by transfer plus a little cash. So the query ages **unreconciled bank ledger items** instead, which is the correct equivalent, and carries `CO_CHEQUE_DOCS_N` = 0 on every row so nobody mistakes one for the other.

**What IS possible from SAP alone, and is what this section delivers:** which accounts are reconciled and how current that is; how much of each book balance the bank has agreed; and the size and age of everything the bank has not agreed. That is a reconciliation **status** report. It is not a reconciliation, and it should never be presented as one.

**One genuinely good finding:** where JIVO *does* reconcile, the work is clean. Across all three books only **one** account (Oil 2201105) has any unreconciled item dated on or before its own last statement date — 2 items, and they are a ₹70 lakh journal entry and its exact reversal, netting to zero. **Zero** reconciled items anywhere are dated after their statement date. So `GAP_AT_LAST_RECON_L` printing 0.00 on all 23 reconciled accounts is real, not an artifact. The problem is coverage and currency, not quality.

---

## Tables and columns chosen, and why

| Table | Used for | Why |
|---|---|---|
| `JDT1."ExtrMatch"` | **the ground truth for "has this bank item cleared"** | The external-reconciliation number stamped on a G/L line when it is agreed with the bank. 0 = not agreed. VERIFIED Oil: 24,118 of 526,820 lines carry `ExtrMatch > 0`, and the per-account counts sum to **exactly 24,118** — i.e. every last one sits on one of the 19 reconciled bank accounts. External reconciliation is used at JIVO for bank accounts and nothing else. Mart 6,084 / 344,144; Bev 4,262 / 86,414. |
| `OBNK` | reconciliation events: how many, when, the bank-side figure | `"AcctCode"` + `"BankMatch"` (**not** `"Sequence"` — see T2) + `"DueDate"` (statement cut-off, always a month-end) + `"CreateDate"` (when it was keyed) + `"DebAmount"`/`"CredAmnt"`. |
| `OACT` | the account universe, names, drawer, `"CurrTotal"` cross-check | `"FatherNum"` walk, not name or code prefix (see T5). `"ExtrMatch"` = last recon number used, **not** a count (see T2). |
| `DSC1` | `IS_HOUSE_BANK` flag only | 5 rows Oil, 3 Bev, 1 Mart against 13-30 live bank accounts per book. Too sparse and too wrong to define anything; used purely as a marker. |
| `BNK1`, `BNK2` | proof of the negative | 0 rows everywhere → `CO_STMT_IMPORT_ROWS_N`. |
| `RCT1`, `VPM1`, `OCHO`, `ORCT/OVPM."CheckSum"` | proof of the negative | 0 everywhere → `CO_CHEQUE_DOCS_N`. |
| `OITR` / `ITR1` | proof that internal reconciliation is the wrong table here | → `CO_INTERNAL_RECONS_N`, `CO_INTRECON_ON_BANK_N`. See T1. |

**Deliberately NOT used:**

- **`ORCT` / `OVPM` reconciliation flags — there aren't any.** VERIFIED by listing every ORCT column matching `%atch%`, `%econ%`, `%lear%`, `%Bank%`, `%Status%`. What exists is `"Status"` (document open/closed), `"BoeStatus"` (bills of exchange — unused), `"BankCode"`/`"BankAcct"` (the *counterparty's* bank), `"DPPStatus"`/`"WddStatus"`/`"ElCoStatus"` (localisation/withholding), and `"OpenBal"`. **None of them is a bank-clearing flag.** Clearing state exists only on the journal line. Anyone looking for a "reconciled" tick on the payment document will not find one.
- **`ORCT."OpenBal"`** — 2,906 of Oil's 11,419 uncancelled customer receipts carry a non-zero `OpenBal` totalling **₹71.32 crore**. That is money banked and never knocked off an invoice. It is a *receivables* diagnostic and belongs to the ageing sections; it is **not** a bank-reconciliation item, because the money is in the bank either way.
- **`"DocStatus"` / open-item logic** — has no place here at all. Bank clearing state lives in `"ExtrMatch"` only.

---

## Traps found, and how they are handled

**T1 — "Internal reconciliation is unused at JIVO" is true of the FIELD and false as a CONCLUSION.**
`JDT1."IntrnMatch"` is 0 on 100% of lines and `JDT1."Closed"` is 'N' on 100% — verified over **all** 526,820 / 344,144 / 86,414 lines, not a sample. But internal reconciliation is *heavily* used: SAP 9.x/10 keeps it in `OITR`/`ITR1` and leaves the legacy `JDT1` field at 0. Oil has **29,994 OITR headers / 122,801 ITR1 rows**, dated 2024-10-01 through today (2026-08-21). Mart 12,930 uncancelled, Bev 6,112.
It is simply the wrong table for *this* section: only **2** of Oil's 122,801 ITR1 rows sit on an account OBNK reconciles. The rest are debtor / creditor control accounts (1101005 SUNDRY DEBTORS E-COM, 2110004 SUNDRY CREDITOR SERVICE …), WIP and GRNI.
**Handled:** the query keys on `"ExtrMatch"`, never `"IntrnMatch"`, and carries `CO_INTERNAL_RECONS_N` / `CO_INTRECON_ON_BANK_N` so the dashboard can state the distinction rather than repeat the wrong conclusion.
**This is a correction to a session-level "settled truth" and should be propagated** — a downstream analysis that concludes "JIVO does no internal reconciliation" from `IntrnMatch = 0` is wrong.

**T2 — `OBNK."Sequence"` is NOT the reconciliation number, and `OACT."ExtrMatch"` is NOT a count.**
They coincide on most accounts, which is exactly what makes this dangerous. Oil **2201104 LOAN TERM INDIAN BANK 8021303333** has 9 OBNK rows with `"Sequence"` **1..9** but `"BankMatch"` **5..13**, and `OACT."ExtrMatch"` = **13**. The naive reading reports 13 statements where there are 9, and joins ledger line `ExtrMatch=5` to the wrong statement date.
**Handled:** reconciliations counted as `COUNT(DISTINCT "BankMatch")`; the detail query joins on `("AcctCode", "BankMatch")`.
Why the numbering starts at 5 there is **INFERRED**, not verified: most likely four earlier reconciliations were removed (SAP does not reset the per-account counter when you undo one). Not checked against a change log.

**T3 — `RECON_TIEOUT_DIFF_L = 0.00` is a structural invariant, NOT evidence of a good reconciliation.**
SAP will not let you close an external reconciliation unless the book side and the bank side balance, so `SUM(reconciled JDT1 net) = -SUM(OBNK "DebAmount"-"CredAmnt")` is guaranteed by the software. It printed exactly **0.00 on all 23 reconciled accounts and all 259 individual events** across the three books — which proves this query joins correctly and proves nothing whatever about whether the bank actually said those numbers. Kept as a query self-check, labelled as one in the SQL header. **Do not show it to an auditor as assurance.**

**T4 — picking bank accounts by name or code prefix is wrong.**
`'%BANK%'` also catches BANK CHARGES and TDS RECOVERABLE FROM BANK. The code prefix lies: Oil's 1104106/1104107 carry `1104*` codes but hang under `2201100` BANK CASH CREDIT LOAN, and 1103114/1103116/1103117 carry `1103*` codes but hang under FDR. `OACT."ActType"` and `"CashBox"` are useless as selectors — every bank account here is `ActType='N'`, `CashBox='N'`.
**Handled:** the universe is the postable balance-sheet children of eight named chart-of-accounts drawers resolved through `OACT."FatherNum"` — BANK ACCOUNTS, PAYMENT BANK ONLINE, CASH IN HAND, BANK CASH CREDIT LOAN, FDR, TERM LOAN, VEHICLE LOAN, CREDIT CARD. All eight verified present with identical spelling in all three books; postable children Oil **70**, Mart **44**, Bev **18**. This matches the sibling `bank-accounts` section exactly, so the two sections cannot disagree about what a bank account is.
**Completeness check, run live:** every G/L account ever used as `ORCT`/`OVPM` `"TrsfrAcct"`/`"CashAcct"` is inside that universe, in all three books, with exactly two exceptions in Oil — `3200003 OPENING BALANCE ACCOUNT` (2,718 documents, **all dated 2024-09-30**, the migration offset) and `5200015 EXCHANGE FLUCTUATIONS` (3 documents). Both are correctly outside. Mart and Bev: nothing outside at all.
A safety union also pulls in any account with an OBNK row or a non-null `OACT."ExtrMatch"`. Live it catches nothing — which is itself the proof the drawer list is complete.

**T5 — storno / reversal pairs inflate gross figures.** Not removed: both legs post to the ledger and both belong in the balance; dropping one would break the tie-out to `OACT."CurrTotal"`. Concrete case: Oil 2201105's two `STALE_PRE_RECON` items are TransId 219567 (₹70,00,000 Dr, memo "BEING PAYMENT FROM HSBC BANK(Reversal)") and TransId 220018 (₹70,00,000 Cr), both `TransType=30`, both dated 2026-04-07. `STALE_PRE_RECON_L` shows **140** lakh gross; the net is **zero**. Noted, never silently dropped.
**Now measured across the whole 90-day-plus bucket** (a journal is a storno pair if its `TransId` is either side of an `OJDT."StornoToTr"` link): **Oil 209 lines / 2,881.31 L of 19,464.41 L = 14.8%**, **Mart 284 / 598.08 L of 7,383.00 L = 8.1%**, **Beverages 44 / 27.86 L of 811.11 L = 3.4%**. Every pair nets to zero, so `UNRECONCILED_DIFF_L` is untouched; only the gross ageing is inflated, by up to a seventh. (VERIFIED)

**T6 — ageing values are gross movement, not net exposure.** `UNREC_0_30_L` and friends sum Debit **+** Credit of the unreconciled lines in that bucket, so a busy current account shows a month of throughput, not an amount at risk. Deliberate — an uncleared item has a size whichever way it points, and a Dr/Cr pair netting to zero is still two uncleared items. Read `UNRECONCILED_DIFF_L` for the net position and `UNREC_90PLUS_PAYMENTS_L` for the stale money-out figure.

**T7 — a reconciliation is not date-sequential.** An old item can be swept into a much later batch, so "everything before LAST_RECON_DATE is clear" is false in general. Live evidence: Oil 2201101 batch #24 (statement 2026-05-31) reached back **156 days** to 2025-12-26; Mart 1104108 batch #4 reached back **360 days**. **Handled:** `STALE_PRE_RECON_N`/`_L` report exactly the items still unreconciled although dated on or before the last reconciled statement date, and `MAX_ITEM_AGE_AT_STMT_N` in the detail shows the reach of each batch.

**T8 — a back-dated run must not count a line as reconciled because of a reconciliation that had not happened yet. FOUND BY TESTING, NOT BY READING.**
Batches reach backwards (T7). Testing `j."ExtrMatch" > 0` on its own calls Oil 2201101's 2025-12-26 items "reconciled" on an as-of of 2025-12-31 — five months before the batch that cleared them existed. Caught because the back-dated run broke the tie-out: at `{{ASOF}}` = 2025-12-31 Oil printed `RECON_TIEOUT_DIFF_L` = **-42.09 lakh** instead of 0.00.
**Fixed:** a line counts as reconciled only when its `("Account", "ExtrMatch")` matches an OBNK reconciliation whose own `"DueDate"` is `<= {{ASOF}}` (CTE `reckey`). Re-verified after the fix: at `{{ASOF}}` = today all three companies' output is **byte-identical** to before the patch (every ExtrMatch value has an OBNK row, so nothing moves), and at `{{ASOF}}` = 2025-12-31 the tie-out is **0 in all three books**. Oil's reconciled coverage at that date reads 83.6% against 78.1% today, which is the correct as-of answer.

**T9 — `RECONCILED_LINES_PCT` needed a `CAST(... AS DOUBLE)`.** HANA's decimal division printed `78.100000000000000000000` from a `ROUND(100.0 * a / b, 1)`. Fixed; it now prints `78.1`.

**T10 — branch / intercompany. THE ORIGINAL CLAIM HERE WAS WRONG AND HAS BEEN REPLACED.**
It used to read *"does not apply — these are G/L accounts, not business partners."* That is false on the facts, and it was a hand-wave rather than a measurement.

- **Branch IS on these rows.** `JDT1."BPLId"` is populated on every bank ledger line. Oil spreads over **7** branches (DELHI 16,582 lines / -6,169.25 L, FACTORY 13,459 / -4,402.98 L, PUNJAB 579 / +4,571.41 L, HARYANA SALES 215, DELHI ISD 11, DELHI INFO 9, HIMACHAL PRADESH 8 — summing to the book's -5,922.53 L), Mart over 7, Beverages over 5. One physical bank account is shared by several branches. This section aggregates **across** branches deliberately: a bank account is reconciled as one account against one statement, not per branch. Branch is available in `JDT1` for a drill-down; it is not a dimension of a reconciliation. (VERIFIED)
- **Intercompany money DOES flow through these accounts, and it is large.** Bank lines sitting in a journal that also touches a JIVO-named related party: **Oil 532 lines, ₹306.75 Cr gross / +₹271.10 Cr net; Mart 486 lines, ₹336.96 Cr gross / −₹247.31 Cr net; Beverages 3 lines, ₹0.40 Cr.** The two large ones mirror each other — Oil receiving what Mart pays. (VERIFIED)
- **It is INCLUDED, on purpose, and that is the correct treatment.** The bank statement shows those transfers. A reconciliation that netted intercompany out would stop tying to the bank. So the house rule "flag it, never silently drop or include" is satisfied by flagging: it is here, it is this big, and **nothing in this section is a trade figure**, so none of it can be misread as turnover.
- The 23 group `CardCode`s and the `OCRG '%BRANCH%'` test are BP-side tests and cannot be applied to a G/L account row. Nothing is dropped on branch or intercompany grounds anywhere in this query.

**T11 — as-of correctness.** Every `JDT1` read is bounded by `"RefDate" <= {{ASOF}}` and every `OBNK` read by `"DueDate" <= {{ASOF}}`. `CURRTOTAL_XCHECK_L` (`OACT."CurrTotal"`) is lifetime-to-**today** and will legitimately differ from `GL_BAL_L` on a back-dated run — that is not a defect.

---

## Self-checks, run live on all three books

| Check | Result |
|---|---|
| `GL_BAL_L` vs `CURRTOTAL_XCHECK_L` (SAP's own stored balance) on all **132** accounts | max abs difference **0.000000** lakh — exact on every account, all three books |
| `RECON_TIEOUT_DIFF_L` on all 132 summary rows | **0** everywhere (structural — see T3) |
| `TIEOUT_DIFF_L` on all **259** detail events | **0** everywhere |
| Detail events with zero matched ledger lines | **0** (Oil 201, Mart 7, Bev 51 — every OBNK row joins to ledger lines) |
| Reconciled ledger lines dated **after** their account's last statement date | **0**, all three books |
| Unreconciled lines dated **on or before** the last statement date | **1 account only** (Oil 2201105, 2 lines, net ₹0) |
| Row counts | summary Oil 71 / Mart 45 / Bev 19 (accounts + 1 TOTAL); detail 201 / 7 / 51 |
| Back-dated run at `{{ASOF}}` = 2025-12-31, tie-out | **0** in all three books (after the T8 fix; it was -42.09 lakh in Oil before) |
| Same back-dated run vs today's run at `{{ASOF}}` = 2026-08-21 | today's output **byte-identical** before and after the T8 fix, all three books |

---

## LIVE OUTPUT — all three companies, as-of 2026-08-21

### TOTAL row, all 50 columns

| Column | Oil | Mart | Beverages |
|---|---:|---:|---:|
| ROW_TYPE | TOTAL | TOTAL | TOTAL |
| ACCT_NAME | ALL BANK / CASH / BANK-FACILITY ACCOUNTS | (same) | (same) |
| RECO_STATUS | 19_OF_70_ACCOUNTS_RECONCILED | 2_OF_44_ACCOUNTS_RECONCILED | 2_OF_18_ACCOUNTS_RECONCILED |
| RECONS_DONE_N | 201 | 7 | 51 |
| FIRST_RECON_DATE | 2024-10-30 | 2025-07-01 | 2024-12-31 |
| LAST_RECON_DATE | 2026-06-30 | 2026-05-31 | 2026-05-31 |
| DAYS_SINCE_RECON_N | 52 | 82 | 82 |
| GL_LINES_N | 30,863 | 15,579 | 6,711 |
| GL_BAL_L | -5,922.53 | 6.28 | 46.13 |
| THROUGHPUT_L | 416,632.10 | 76,583.38 | 9,489.27 |
| CURRTOTAL_XCHECK_L | -5,922.53 | 6.28 | 46.13 |
| REC_LINES_N | 24,118 | 6,084 | 4,262 |
| RECONCILED_LINES_PCT | 78.1 | 39.1 | 63.5 |
| REC_RECEIPTS_N | 9,888 | 4,297 | 2,367 |
| REC_RECEIPTS_L | 171,782.83 | 28,072.84 | 3,585.93 |
| REC_PAYMENTS_N | 14,230 | 1,787 | 1,895 |
| REC_PAYMENTS_L | 176,147.23 | 27,852.29 | 3,497.67 |
| RECONCILED_BAL_L | -4,364.41 | 220.55 | 88.26 |
| BANK_SIDE_BAL_L | -4,364.41 | 220.55 | 88.26 |
| RECON_TIEOUT_DIFF_L | 0 | 0 | 0 |
| UNREC_LINES_N | 6,745 | 9,495 | 2,449 |
| UNREC_RECEIPTS_N | 4,166 | 7,461 | 1,948 |
| UNREC_RECEIPTS_L | 33,571.96 | 10,221.99 | 1,181.77 |
| UNREC_PAYMENTS_N | 2,579 | 2,034 | 501 |
| UNREC_PAYMENTS_L | 35,130.08 | 10,436.26 | 1,223.90 |
| UNRECONCILED_DIFF_L | -1,558.13 | -214.27 | -42.13 |
| GL_BAL_AT_LAST_RECON_L | -4,364.41 | 220.55 | 88.26 |
| GAP_AT_LAST_RECON_L | 0 | 0 | 0 |
| MOVEMENT_SINCE_RECON_L | -1,558.13 | -214.27 | -42.13 |
| UNREC_0_30_N / _L | 1,011 / 24,917.74 | 641 / 5,908.33 | 442 / 544.37 |
| UNREC_31_60_N / _L | 1,133 / 17,778.61 | 816 / 3,581.02 | 403 / 715.86 |
| UNREC_61_90_N / _L | 618 / 6,541.28 | 660 / 3,785.90 | 266 / 334.32 |
| UNREC_90PLUS_N / _L | **3,983 / 19,464.41** | **7,378 / 7,383.00** | **1,338 / 811.11** |
| UNREC_90PLUS_PAYMENTS_L | 10,103.20 | 3,632.95 | 404.66 |
| OLDEST_UNREC_DATE | 2024-09-30 | 2024-12-31 | 2024-10-04 |
| STALE_PRE_RECON_N / _L | 2 / 140.00 | 0 / 0 | 0 / 0 |
| CO_STMT_IMPORT_ROWS_N | **0** | **0** | **0** |
| CO_CHEQUE_DOCS_N | **0** | **0** | **0** |
| CO_INTERNAL_RECONS_N | 29,062 | 12,930 | 6,112 |
| CO_INTRECON_ON_BANK_N | 2 | 0 | 0 |

(`DRAWER_NAME`, `ACCT_KIND`, `IS_HOUSE_BANK`, `ACCT_CODE`, `LAST_RECON_NO` are NULL on the TOTAL row by design. `DAYS_SINCE_RECON_N` on the TOTAL row is a MIN = days since the most recent reconciliation anywhere in that book.)

### Every account that has ever been reconciled — all 23, all three books

```
book acct     name                                       recons  first..last(stmt)        days  cov%   GL_BAL_L    RECONCILED_L  UNREC_DIFF_L  stale_n
oil  2201101  INDIAN BANK CC A/C 7007270527              25   2024-11-30..2026-06-30      52   94.6   -2885.59    -3028.78       143.19       0
oil  2201105  HSBC BANK A/C - 166794941001                7   2025-09-30..2026-05-31      82   80.7     806.68      107.88       698.79       2
oil  1104107  ICICI BANK- 629305042549                   25   2025-02-06..2026-05-31      82   85.2     713.40       13.46       699.94       0
oil  2201202  LOAN TERM INDIAN BANK A/C 702471101-9      13   2025-01-01..2026-05-31      82   86.6    -253.24     -349.91        96.67       0
oil  2201104  LOAN TERM INDIAN BANK A/C- 8021303333       9   2025-07-31..2026-05-31      82   84.3     -44.75      -46.69         1.94       0
oil  2201205  LOAN INDIAN BANK M/C-8031052035             8   2025-07-31..2026-05-31      82   90.8     -30.08      -31.37         1.29       0
oil  1104106  ICICI BANK-629305042322                    30   2024-10-30..2026-05-31      82   93.8     -28.81        4.59       -33.40       0
oil  2201402  LOAN INDIAN BANK M/C-7727325989             9   2025-07-31..2026-05-31      82   92.6     -23.72      -25.86         2.14       0
oil  2201204  LOAN TERM INDIAN BANK A/C- 8156038585       3   2026-03-31..2026-05-31      82   83.8     -21.20      -22.07         0.87       0
oil  2201102  ICICI BANK LTD - 629305042195              25   2024-11-29..2026-05-31      82   88.9     -14.48      -66.68        52.20       0
oil  2201404  LOAN ICICI - XL6 ZETA - LADEL00050697545    3   2026-03-31..2026-05-31      82   91.3      -8.59       -8.94         0.34       0
oil  2201207  LOAN TERM INDIAN BANK A/C- 8218758120       3   2026-03-31..2026-05-31      82   86.2      -8.39       -8.51         0.11       0
oil  2201206  LOAN TERM INDIAN BANK A/C- 8218762067       3   2026-03-31..2026-05-31      82   82.8      -5.77       -6.04         0.27       0
oil  1104104  INDIAN BANK-7121100859                     23   2024-11-30..2026-05-31      82   97.4       3.67        6.21        -2.54       0
oil  2201405  LOAN ICICI - ECCO HR42J6791-LADEL000510219  3   2026-03-31..2026-05-31      82   90.0      -2.82       -3.06         0.24       0
oil  2201403  LOAN ICICI - MARUTI SUPER CARRY - LVDEL...  3   2026-03-31..2026-05-31      82   91.7      -1.45       -1.80         0.35       0
oil  2201401  LOAN ICICI - XL6 ZETA - LADEL00048823452    3   2026-03-31..2026-05-31      82   91.7      -1.03       -1.71         0.68       0
oil  1104103  INDIAN BANK-7106652016                      2   2025-01-22..2025-08-31     355  100.0       0.26        0.26         0.00       0
oil  2201103  INDIAN BANK ADHOC-OCC A/C 7939167102        4   2025-01-17..2025-03-03     536   67.5       0.00     -895.39       895.39       0
mart 1104108  ICICI BANK 629305042079                     5   2025-07-01..2026-05-31      82   88.0      51.88      218.14      -166.26       0
mart 1104111  ICICI BANK - 629305042589                   2   2025-09-30..2025-10-31     294   43.0       1.89        2.41        -0.52       0
bev  1104106  INDIAN BANK-7051847887                     21   2024-12-31..2026-05-31      82   84.9      32.34       71.52       -39.17       0
bev  1104107  ICICI BANK- 629305042545                    30   2025-02-06..2026-05-31      82   84.9      12.06       16.74        -4.68       0
```

Note the cliff: **only 2201101 was reconciled to 2026-06-30. Every other Oil account stops at 2026-05-31** (82 days), and two stopped a year or more ago — **1104103 at 2025-08-31 (355 days)** and **2201103 INDIAN BANK ADHOC-OCC at 2025-03-03 (536 days)**. Mart's 1104111 stopped at **2025-10-31 (294 days)**.

### Never reconciled once, ranked by money that has moved through them

```
book acct     name                                     THROUGHPUT_L  GL_BAL_L   unrec_lines  90+_N   90+_L      90+payments_L  oldest
oil  2201106  TRADEPAY HSBC-41001                       12,837.44   -2,289.02      173         96    7,639.00     4,813.07     2025-07-01
oil  1104108  HSBC BANK LAI                              3,985.93        0.00       28         28    3,985.93     1,992.96     2025-08-28
oil  1104110  AXIS BANK - 926030031139627                3,000.00        0.00        4          0        0.00         0.00     2026-07-24
oil  2201211  LOAN TERM AXIS BANK 926060051726532        1,500.00   -1,500.00        1          0        0.00         0.00     2026-07-24
oil  1104102  INDIAN BANK-6994996254                       777.60        0.40       36         32      736.44       368.02     2024-09-30
oil  2201210  LOAN TERM INDIAN BANK - 8318195504           726.77     -709.23        4          0        0.00         0.00     2026-06-08
oil  1104201  PAYTM BANK (wallet, micro-entries)               —         0.10        —      1,875      412.47            —     2024-09-30
mart 1104112  HSBC BANK - 166800516001                  12,560.46      -49.43      428        189    5,503.67     2,704.30     2025-05-08
mart 1104113  HDFC BANK - 50200064548016                   819.31        1.23      177        152      681.31       339.04     2025-04-01
mart 1104201  PAYTM BANK (wallet, micro-entries)           344.82       -0.19    4,428      3,921      317.65       158.66     2025-01-16
mart 1105003  CASH SALE MAYAPURI (cash)                    292.94        0.00    2,398      2,132      271.47       135.67     2025-01-16
bev  1105001  CASH SALE (cash)                           1,021.96        0.65    1,525      1,190      781.20       390.24     2024-10-04
bev  1104108  HSBC BANK A/C- 166-794941-511 (USD)           27.01        0.00        2          2       27.01        13.50     2026-02-03
```

The two that matter most:

- **Oil `2201106` TRADEPAY HSBC-41001** — ₹128.37 crore has moved through it, it currently sits at **-₹22.89 crore** (JIVO owes), and it has **never been reconciled once**. 96 of its 173 items are over 90 days old, ₹48.13 crore of that being money out.
- **Mart `1104112` HSBC BANK - 166800516001** — ₹125.60 crore through it over 428 lines, **never reconciled**. 189 items over 90 days, ₹55.04 crore gross, ₹27.04 crore of it money out.

**Read the 90+ counts carefully.** Mart's headline 7,378 items over 90 days is dominated by wallet and cash micro-entries — 3,921 PAYTM + 2,132 CASH SALE MAYAPURI + 439 CASH SALE = 6,492 of the 7,378, worth only ₹8.62 crore between them. The **bank** items in that bucket are 189 (HSBC) + 152 (HDFC) + 142 (ICICI 1104111) + 2 = 485 items worth **₹64.80 crore**. Same shape in Oil: 1,875 of the 3,983 are PAYTM wallet entries worth ₹4.12 crore. Cash and wallet accounts are not reconciled against a bank statement at all — they need a cash count / gateway settlement report, which is a different exercise.

### Reconciliation cadence (from `bank-reco-detail.sql`)

Average lag from statement date to the day the reconciliation was keyed: **Oil 10.0 days** (max 53), **Mart 14.1 days** (max 32), **Beverages 6.6 days** (max 31). So when the team does reconcile, they do it promptly. The gaps are missed months, not slow months.

Mart, all 7 events ever — the irregular cadence is visible in one screen:

```
ACCT     RECON_NO  STMT_DATE   PERFORMED   LAG  LINES  CLEARED_NET_L  MAX_ITEM_AGE_AT_STMT
1104108      5     2026-05-31  2026-06-15   15    574      81.15            120
1104108      4     2026-03-27  2026-03-30    3   1662     117.74            360   <- catch-up sweep
1104108      3     2025-10-31  2025-11-11   11    378    -163.13             30
1104111      2     2025-10-31  2025-11-11   11     16       1.01             22
1104108      2     2025-09-30  2025-10-13   13    881     134.44            183
1104111      1     2025-09-30  2025-10-14   14    116       1.40            173
1104108      1     2025-07-01  2025-08-02   32   2457      47.94            182
```

Oil's 10 most recent events:

```
ACCT     RECON_NO  STMT_DATE   PERFORMED   LAG  LINES  CLEARED_NET_L  MAX_ITEM_AGE_AT_STMT
2201101     25     2026-06-30  2026-07-28   28    361    -354.88             84
1104104     23     2026-05-31  2026-06-06    6     25       2.72             30
1104106     30     2026-05-31  2026-06-06    6     27     124.29             30
1104107     25     2026-05-31  2026-06-06    6    411       4.39             29
2201101     24     2026-05-31  2026-06-11   11    378     273.59            156
2201102     25     2026-05-31  2026-06-06    6    132     256.22             30
2201104     13     2026-05-31  2026-06-06    6      3       0.65             30
2201105      7     2026-05-31  2026-06-06    6    115     597.28             30
2201202     13     2026-05-31  2026-06-06    6      3      23.16             30
2201204      3     2026-05-31  2026-06-06    6      3       0.29             30
```

Full dumps: `pipeline/raw/bank-reco.{oil,mart,bev}.tsv` (71 / 45 / 19 rows) and `pipeline/raw/bank-reco-detail.{oil,mart,bev}.tsv` (201 / 7 / 51 rows).

---

## Unresolved / not checked — stated plainly

1. **Whether the reconciliations that exist are correct.** Impossible from SAP: no statement lines were ever stored, and the tie-out is enforced by the software (T3). Everything here is about *whether and when* a reconciliation happened, never whether it was right. To go further you need the bank statements — the operator has confirmed there is no statement file available right now.
2. **The bank's own closing balance is not in SAP anywhere.** `OBNK."balance"` is **0.000000 on all 259 OBNK rows across all three books** (VERIFIED exhaustively, not sampled), so it carries nothing. `GAP_AT_LAST_RECON_L` therefore compares the book balance at the statement date against the *book-derived* agreed balance, not against a figure the bank supplied. It is a valid internal consistency measure and is **not** the classic "balance per bank statement vs balance per books" line. Say so when presenting it.
3. **Why Oil 2201104's reconciliation numbering starts at 5.** INFERRED as four removed reconciliations; not verified against any log.
4. **`OACT."ExtrMatch"` equals the max `BankMatch` on all 23 reconciled accounts, but only 23 accounts were available to test it on.** The relationship is not proven in general — the query does not rely on it.
5. **Cash and wallet accounts are inside the universe but are not bank-reconcilable.** PAYTM, RAZORPAY, CASH SALE, CASH SALE MAYAPURI and CASH IN HAND appear with large unreconciled item counts. They are correctly *never* externally reconciled; treating them as a bank-reco failure would be wrong. `ACCT_KIND` (`CASH`, `WALLET`) is there so the dashboard can separate them. No attempt was made to reconcile them against a gateway settlement report — that data is not in SAP.
6. **Chart-of-accounts oddity, not filtered:** Oil `1103115 R & D WHEAT GRASS` (₹134.05 lakh) sits under the FDR drawer and is therefore classified `DEPOSIT`. It is plainly not a bank account. Left in deliberately — filtering it by name would be exactly trap T4. Worth an operator raising with whoever maintains the chart.
7. **`ODSC` (65 rows) was not used.** It is SAP's generic bank *directory* (AXIS, ICICI, INDIAN BANK …), carries no JIVO account number and no balance. Nothing in this section needs it.
8. **Foreign-currency bank accounts were not treated specially.** Oil 1104109 and Bev 1104108 are USD HSBC accounts. All figures here are the local-currency (`"Debit"`/`"Credit"`) legs, so an FX revaluation difference would show as an unreconciled item. Not investigated; both accounts sit at zero balance today.
9. **`OBNK."Cleared"`, `"StatemNo"`, `"JDTID"`, `"PmntID"`, `"IdNumber"` are empty on every single one of the 259 OBNK rows** in all three books — VERIFIED exhaustively: `Cleared='Y'` count 0, and `StatemNo`/`JDTID`/`PmntID`/`IdNumber` NULL on 201/201 Oil, 7/7 Mart, 51/51 Bev. They belong to SAP's Bank Statement Processing feature, which is entirely unused here. This is further confirmation that OBNK is a hand-keyed reconciliation log, not a statement feed: nothing links an OBNK row to a journal entry or a payment document.

---

# ADVERSARIAL VERIFICATION — 2026-08-21, second pass

The section above was written by the agent that built the query. This part was
written by a second agent whose brief was to assume it is wrong and prove it.
Everything below was run live against HANA on 2026-08-21 unless marked INFERRED.
Verdict: **FIXED** — the arithmetic was sound on every axis attacked; four
contract/presentation defects were found and corrected.

## What was attacked, and what survived

| # | Attack | Method | Result |
|---|---|---|---|
| 1 | **Double counting / join fan-out** | Rebuilt the whole headline from `JDT1` with `NOT EXISTS` sub-queries instead of the `LEFT JOIN acct/stmt/reckey` chain — a structurally different query | **SURVIVED, exactly.** `GL_LINES_N` 30,863 / 15,579 / 6,711 · `GL_BAL_L` −5,922.53 / 6.28 / 46.13 · `THROUGHPUT_L` 416,632.10 / 76,583.38 / 9,489.27 · `REC_LINES_N` 24,118 / 6,084 / 4,262 · `UNREC_LINES_N` 6,745 / 9,495 / 2,449 · `UNREC_90PLUS_N/_L` 3,983 / 19,464.41, 7,378 / 7,383.00, 1,338 / 811.11 · `UNREC_90PLUS_PAYMENTS_L` 10,103.20 / 3,632.95 / 404.66. Every figure identical to the shipped TSV in all three books. |
| 2 | **Is `acct` unique?** (a duplicate would double every `JDT1` line) | `COUNT(*)` vs `COUNT(DISTINCT)` on the CTE | **SURVIVED.** 70/70, 44/44, 18/18. Also `OACT."AcctCode"` is unique (1,429 / 1,104 / 765). |
| 3 | **Does `OBNK."BankMatch"` collide across accounts?** Oil has 201 OBNK rows but only **30** distinct `BankMatch` values — if it were a global id, the `(AcctCode, BankMatch)` join could mismatch and `SUM(RECONS_DONE_N)`=201 would be ~6.7× overstated | Listed every `BankMatch` with its account count and date spread | **SURVIVED — and this is the strongest single result.** `BankMatch` is a **per-account counter**: Oil's `BankMatch`=1 appears on 18 different accounts with 10 different `DueDate`s spanning 2024-10-30 → 2026-03-31. They are 18 unrelated first-reconciliations. `(AcctCode, BankMatch)` is unique on every row (201/201, 7/7, 51/51), so the join is right, the per-account `COUNT(DISTINCT)` is right, and 201 really is 201 events. **Joining on `BankMatch` alone would have been catastrophic.** |
| 4 | **Trap T2 — is the `Sequence` ≠ `BankMatch` story real or invented?** | Compared `Sequence`, `BankMatch` and `OACT."ExtrMatch"` per account | **REAL, and correctly handled.** Exactly 1 of 23 reconciled accounts diverges: Oil **2201104** has `Sequence` 1..9 against `BankMatch` **5..13**, `OACT."ExtrMatch"`=13. The other 22 match, which is precisely what makes it a trap. The SQL joins on `BankMatch`. |
| 5 | **Cancelled documents** | Looked for a cancellation flag on every table touched | **N/A on the main path, applied everywhere it exists.** `JDT1` has no cancellation column (`Closed`, `StornoAcc`, `TransType` only); reversals are separate journals. `CANCELED='N'` is correctly applied to `ORCT`, `OVPM` and `OITR` in the `co` diagnostics. `BNK1/BNK2/RCT1/VPM1/OCHO` are 0 rows so a filter is moot. |
| 6 | **Storno / reversal inflation** | Joined `OJDT."StornoToTr"` both ways | **CONFIRMED, quantified, correctly retained** — 14.8% / 8.1% / 3.4% of the gross 90 d + bucket. See T5 above. Net effect zero. Removing them would break the tie-out to `OACT."CurrTotal"`. |
| 7 | **Branch + intercompany** | `BPLId` split; journals touching a JIVO-named party | **THE NOTE'S CLAIM WAS WRONG — corrected in the SQL header and in T10 above.** Both are present, both are material (₹306.75 Cr Oil / ₹336.96 Cr Mart gross), both are correctly **included**, and both are now flagged with a number. |
| 8 | **Unapplied money / open-item double-subtraction** | Read the query for any `OpenBal` or `DocStatus` use | **NOT VULNERABLE.** Nothing is subtracted anywhere: clearing state comes from `ExtrMatch` alone, so there is no double-subtraction to make. `ORCT."OpenBal"` is deliberately untouched (it is a receivables item — the money is in the bank either way). `DocStatus='O'` is not used, which is right: the session-level finding that `DocStatus` is unreliable at JIVO would have poisoned any open-item approach here. |
| 9 | **Migrated openings at 2024-09-30** | Split the 90 d + bucket by `RefDate = 2024-09-30` | **HANDLED, and small.** Oil: 23 items / 863.55 L of 19,464.41 L (4.4%) are go-live openings; Mart and Beverages have **none** in the bucket. They age correctly into 90 d + and are not distorting it. `OLDEST_UNREC_DATE` = 2024-09-30 in Oil is the migration, as expected. |
| 10 | **Three-schema portability** | Ran the shipped SQL against all three schemas myself, plus the drawer resolution | **SURVIVED.** All 8 drawer names exist with identical spelling **and identical account codes** in all three books (1104100, 1104200, 1105000, 2201100, 1106100, 2201200, 2201400, 2201300). Postable children sum exactly to 70 / 44 / 18. No UDF is used anywhere, so there is no Oil-only field to break Beverages. `DSC1` exists in all three. |
| 11 | **Empty / NULL** | Ran at `{{ASOF}}` = **2024-09-29**, one day before go-live, when literally nothing exists | **SURVIVED.** Returns 71 / 45 / 19 rows of clean zeros, no error, no divide-by-zero (`RECONCILED_LINES_PCT` guards `GL_LINES_N = 0` and returns NULL). The dashboard can render it. |
| 12 | **Money units** | Pulled three accounts' balances in raw INR and divided by hand | **SURVIVED — every `_L` column is genuinely lakhs.** Oil 2201101 raw **−288,559,063.03 INR** → reported **−2,885.59** `GL_BAL_L`. 1104106 −2,881,202.32 → −28.81. 2201102 −1,448,356.68 → −14.48. Throughput likewise. |
| 13 | **Money units, second route** | Classified all 50 summary + 16 detail column names against the renderer's own `scale()` / `isMoneyCol()` / `isIdCol()` regexes | **SURVIVED.** All 24 `_L` columns scale ×1e5; all `_N` counts and `RECONCILED_LINES_PCT` are correctly excluded from money formatting; `ACCT_CODE` / `LAST_RECON_NO` / `RECON_NO` are held as identifiers and not grouped as amounts. **No column name lies about its unit.** |
| 14 | **Re-derive the headline a second way** | `RECONCILED_BAL_L` (from `JDT1`) vs `BANK_SIDE_BAL_L` recomputed straight off `OBNK` | **AGREE exactly:** −4,364.41 / 220.55 / 88.26 from both routes. (Note this is the structural invariant of T3 — it proves the join, not the bank.) |
| 15 | **Back-dated as-of (trap T8)** | Ran the shipped SQL at 2025-12-31, 2024-10-01 and 2024-09-29 | **SURVIVED.** `RECON_TIEOUT_DIFF_L` = **0 in all three books at every date**. The `reckey` guard genuinely earns its keep. |
| 16 | **Does the detail query leak across the as-of date?** Its `led` CTE has **no** `{{ASOF}}` bound | Checked whether any reconciled line is dated after its own statement | **SAFE, and now documented in the SQL.** **Zero** of the 24,118 / 6,084 / 4,262 reconciled lines is dated after its statement date; they reach *backwards* by up to 547 / 360 / 166 days. So `RefDate ≤ DueDate ≤ ASOF` holds automatically. Re-tested at 2025-12-31: `TIEOUT_DIFF_L` still 0.00 on all 131 / 5 / 42 rows. Left unbounded deliberately — bounding it would understate a genuine event if the invariant ever broke, whereas leaving it makes `TIEOUT_DIFF_L` the alarm. |
| 17 | **Is `LAST_RECON_NO` = `MAX(BankMatch)` actually the latest statement?** `MAX(BankMatch)` and `MAX(DueDate)` can come from different rows | Counted accounts where they disagree | **SURVIVED.** 0 accounts in all three books. |
| 18 | **Per-account invariants** | Recomputed over the shipped TSVs | **ALL HOLD, 132 accounts:** tie-out 0 everywhere · `GL_BAL_L` = `CURRTOTAL_XCHECK_L` on **every** account (SAP's own stored balance) · `REC_LINES_N + UNREC_LINES_N = GL_LINES_N` · the four ageing buckets sum **exactly** to `UNREC_RECEIPTS_L + UNREC_PAYMENTS_L` and their counts to `UNREC_LINES_N`. |
| 19 | **Universe completeness (trap T4)** | Listed every postable account outside the universe whose name contains BANK / CASH / A/C / FDR / LOAN / PAYTM / WALLET with a non-zero balance | **SURVIVED.** Everything excluded is genuinely not a bank account: DIRECTORS LOANS, BANK CHARGES, INTEREST ON FDR, GST INPUT UNCLAIMED, SUSPENSE A/C, TDS RECEIVABLE ON FDR. Exactly the name-matching trap the drawer walk was built to avoid. The `ExtrMatch`/`OBNK` safety net catches **0** extra accounts — the drawer list is complete. |
| 20 | **Performance** | Timed each statement | **Well inside budget.** Summary **1.4 / 1.3 / 1.1 s**, detail **1.1 / 1.1 / 1.1 s**. Full section through the pipeline: **7.1 s** for all six queries. |
| 21 | **Every "zero rows" claim in the header** | Counted them all rather than trusting the comment | **ALL TRUE.** `BNK1`, `BNK2`, `RCT1`, `VPM1`, `OCHO`, `OCHH`, `ODPS`, `DPS1` = **0 rows in all three books**; uncancelled `ORCT`/`OVPM` with `CheckSum <> 0` = **0**; `JDT1."IntrnMatch" <> 0` = **0** and `"Closed" <> 'N'` = **0** over 526,820 / 344,144 / 86,414 lines. `OITR` uncancelled 29,062 / 12,930 / 6,112 matches `CO_INTERNAL_RECONS_N` exactly. |

## Defects found and fixed

**D1 — CRITICAL (contract): the SQL had been renamed out from under the dashboard.**
`site/data.json` was still serving a **previous** version of this section — 38/19/12 rows, no detail, and columns `DRAWER_CODE`, `RECONS_DONE_N`, `RECONCILED_LINES_N`. The rewrite renamed **`RECONS_DONE_N` → `RECONS_N`** (and `RECONCILED_LINES_N` → `REC_LINES_N`) but `site/index.html` still reads `T.RECONS_DONE_N`. Effect on the live page: the "Last reconciled" KPI printed *"52 days ago · **—** reconciliations on record"*, and the account table silently dropped its **recons** column entirely (the renderer filters `tc` by `c in accts[0]`, so a renamed column disappears without an error).
**Fixed in `bank-reco.sql`:** the output column is emitted as `RECONS_N AS RECONS_DONE_N`. The internal CTE alias is unchanged, the `UNION ALL` TOTAL branch inherits the name, and **all data rows are byte-identical to before the rename** — only the header line changed. Column count still 50.

**D2 — the status pill never worked, so a control failure rendered as a mild warning.**
`index.html` coloured the pill with `v === 'NEVER' ? 'bad' : v === 'CURRENT' ? 'ok' : 'warn'`. The SQL emits `DORMANT_NEVER_RECONCILED` / `NEVER_RECONCILED` / `RECONCILED_CURRENT` / `RECONCILED_LAGGING` / `RECONCILED_STALE` — and the *previous* version emitted `MIXED` / `NEVER_RECONCILED` / `RECONCILED_LAGGING` / `RECONCILED_STALE`. Neither literal has **ever** matched, so all 132 accounts across the three books rendered amber, including the **61** that have never been reconciled once.
**Fixed:** matched on substring, with dormant deliberately left neutral — an account with no ledger lines has nothing to reconcile and is not a failure. Live effect: Oil 47 red / 19 amber / 4 neutral, Mart 10 red / 2 amber / 32 neutral, Bev 4 red / 2 amber / 12 neutral.

**D3 — a KPI caption asserted something this section itself disproves.**
"Uncleared payments 90 d +" carried the sub-caption **"cheques likely stale"**, under ₹101.03 Cr. There are **no cheques in any JIVO book** — `RCT1`/`VPM1`/`OCHO` are empty and no uncancelled receipt or payment carries a `CheckSum`, which is exactly what `CO_CHEQUE_DOCS_N = 0` says on every row of this section.
**Fixed:** now reads "money out the bank has not agreed — no cheques exist in this book".

**D4 — `bank-reco-detail.sql` ran on every refresh and its output was thrown away.**
The renderer's signature was `function({summary})`, so the 201 / 7 / 51-row event log — the cadence and keying-lag analysis that is the stated reason the second query exists — was queried against production HANA three times a day and never displayed.
**Fixed:** the renderer now destructures `detail` and renders the event log beneath the account table.

## Not a defect, but the single most misreadable number on the page

`UNREC_90PLUS_L` on the TOTAL row blends two different things, and the smaller one is the one worth acting on:

| | on accounts JIVO **does** reconcile | on accounts **never** reconciled | never-reconciled share |
|---|---:|---:|---:|
| **Oil** | 15 items / **₹16.78 Cr** | 3,968 items / **₹177.86 Cr** | **91.4%** |
| **Mart** | 142 items / **₹2.91 Cr** | 7,236 items / **₹70.92 Cr** | **96.1%** |
| **Beverages** | 0 | 1,338 items / **₹8.11 Cr** | **100%** |

The first column is an **exception list** — items that should have cleared and did not. The second is a **coverage failure** — nobody has ever attempted these accounts, so every line in them is "unreconciled" by definition. Quoting the blended total as "unreconciled items" invites someone to go chasing 3,983 transactions when the actual exception list in Oil is **15**.

No columns were added for this: `RECO_STATUS` is already on every ACCOUNT row, so the split is one filter away (`RECO_STATUS LIKE 'RECONCILED%'`), and a second set of stored totals is one more thing to keep consistent. Recorded as **T13** in the SQL header, and the dashboard KPI now prints the never-reconciled share next to the figure.

**T14** was also added to the SQL header: `ROW_TYPE='ACCOUNT'` and `ROW_TYPE='TOTAL'` share one result set, so any consumer that sums a column without filtering `ROW_TYPE` gets exactly **2×** the truth (the TOTAL row is exactly additive over the account rows — verified on all 15 summable columns in all three books). The `CO_*` columns are the opposite hazard: book-level constants repeated on every row and aggregated with `MAX()`, so summing them gives **71×** in Oil.

## Still unresolved after this pass

1. Everything in "Unresolved / not checked" above still stands. In particular **nothing here verifies that any reconciliation is correct** — no bank statement has ever entered SAP, and `RECON_TIEOUT_DIFF_L = 0` is enforced by SAP, not evidence.
2. **The tie-out is a tautology and should never be shown to an auditor as assurance.** It is on the account table as **tie-out diff** with no such caveat next to it. The section's own caveat block covers the bigger point ("this is not a bank reconciliation"), but the column itself reads like a passed control. INFERRED risk, not measured.
3. **`site/index.html` is being edited by several agents at once.** All four renderer fixes above were verified present and the page's JavaScript parses clean (`node --check`), but the file changed size twice while this pass ran. Worth re-checking D1–D4 survive whoever writes last.
4. **The `co` diagnostics count `ITR1` rows without excluding cancelled `OITR` parents.** `CO_INTRECON_ON_BANK_N` is 2 / 0 / 0 so it cannot matter today; left alone rather than churned.
