## Accounts — AR aging, open payments, claims, credit

*AI-facing decoder for JIVO's Control Panel (the sales team's "god software") as it re-expresses SAP B1 receivables. Every number below was pulled **live 2026-08-25** via the Control Panel CLI (`control-panel/cli/jivo/jivo`, user `preshit`, base `http://138.252.101.118:9080`) and cross-checked against **live SAP B1** (host `138.252.101.222:50000`, login `manager`) through the `sapb1` MCP. Read-only throughout.*

> **Money-gating note:** `preshit`'s login blanks the *revenue/expense/salary/COGS* panels, but **every A/R panel in this domain returned real ₹** — aging, open-payments, credit and claims are all fully visible to this login. Nothing in this section is "money-gated".

---

### The one thing to get right: "Outstanding" is TWO different numbers

The sales team says **"outstanding"** on three screens and means two incompatible things. Conflating them is the classic error.

| Flavour | Where | What it really is | SAP source | Oil book, live 2026-08-25 |
|---|---|---|---|---|
| **Gross open-invoice balance** | Customer-Aging "Total Outstanding" / "Balance Due", the `bal` column | Σ of the *unpaid residual of each open invoice*, before netting advances/on-account cash/credit notes | `OINV` open docs, balance from `JDT1` reconciliation | **₹82.31 Cr** (Σ `bal`, 4,843 invoices, 336 parties) |
| **Net party ledger** | Credit page `ledger`; Oil-aging `outstanding` column; the accounts team's "ledger balance" | `BusinessPartners.CurrentAccountBalance` — the whole account netted (positive = debit/owes JIVO, negative = advance/credit) | `OCRD.CurrentAccountBalance` / `JDT1` | **₹32.45 Cr** (net, credit-page `total.ledger`) |

The ₹82.31 Cr vs ₹32.45 Cr gap is **not an error** — it is C-0019 made visible. SAP marks invoices `Open` that are already covered by an unapplied on-account receipt or a manual JE, so the gross open-invoice pile is far larger than the netted ledger. **When a salesperson says "party X owes us," ask which screen: aging (gross) or ledger/credit (net).**

---

### Term table

| Term | Meaning (sales-team lens) | SAP lineage (entity · column · filter) | Differs-from-accounts / raw SAP | Gotchas & corrections |
|---|---|---|---|---|
| **Customer Aging** | A/R book split into overdue buckets, per company. Oil = flat per-open-invoice feed the client buckets; Mart/Bev = server pre-bucketed pivots. | `OINV` (open A/R) + `JDT1` (reconciliation) per company DB. Django adds only a `remark` overlay column. | Accounts would read the netted ledger; the aging shows **gross** open-invoice residuals, so its headline is bigger than the ledger. | CP Oil aging = **4,843 rows** but SAP has **13,082** open Oil invoices (`bost_Open`,`tNO`) — CP ages the *reconciled* balance, not SAP's unreliable open flag (**C-0019**, **C-0023** ledger-from-JDT1). |
| **`bal` (Oil)** | Open balance still owed on that one invoice. | Per-`OINV` open residual. | This is the *gross* number the aging totals. | Always ≥ 0 in Oil (0 negative rows on 4,843). Advances/CNs never appear here — they live in `outstanding`. Σ `bal` = the "Total Outstanding" KPI. |
| **`outstanding` (Oil row)** | *Not* the invoice's outstanding — it is the **party's whole net ledger**, printed identically on every one of that party's invoice rows. | `BusinessPartners.CurrentAccountBalance` for the row's `code`. | Same as the accounts "ledger balance"; positive = debit, negative = advance/credit. | **NEVER sum this column** — it repeats per invoice, so Σ over 4,843 rows = ₹6,134 Cr of nonsense. Verified equal to `CurrentAccountBalance` on 4 parties to the paisa (see recon). |
| **`total` (Oil row)** | Original invoice value. | `OINV.DocTotal` (GST-incl). | — | Gross of GST. |
| **Balance Due (Mart/Bev)** | Net open balance of the customer, split into buckets that sum to it. | Customer's `BusinessPartners.CurrentAccountBalance`, bucketed by invoice age. | Here the pivot **is** the net ledger (buckets can go negative for advances/CNs). | Σ of the five buckets = `balance_due`. Bucket `b61_90` etc. can be **negative** (Mart total `b61_90` = −₹63.4 L live). |
| **Aging buckets** `b0_30 / b31_60 / b61_90 / b91_120 / b121` | Balance by overdue age: 0–30 = current, 121+ = seriously overdue. | Age computed from invoice/due date vs `as_of`. | — | Oil buckets are derived **client-side from `days`**; Mart/Bev arrive pre-bucketed from the server. |
| **`days` / `tdd` / `ltd` (Oil)** | `days` = invoice age (doc-date → as_of); `ltd` = last-txn / due date; `tdd` = days past that due date. | Derived from `OINV.DocDate` / due date. | — | Oil main-view buckets key off `days` (invoice age), not strict due-date aging. |
| **Format** | The grouping band in the aging table. | Oil/Mart = channel `U_Main_Group`-style band (`E-COMMERCE, BRANCH, PARENT, ROI, GT, CORPORATE, CALL CENTER, STAFF, REFERENCE, WEBSITE`); **Bev = salesperson name** (`OSLP`). | Accounts groups by GL/party, not by sales "Format". | **C-0015**: `U_Main_Group` differs across company books — a Format band is company-specific, never compare across companies. |
| **B2B / B2C (Mart only)** | B2B = customer has a GSTIN on file; B2C = none. | `OCRD` GSTIN present/absent. | Sales segmentation, not an accounts field. | Only Mart exposes `segment`/`gstin`; Oil & Bev do not. |
| **Open Payments / "Payment on Account"** | Customer receipts **received but not yet applied** to invoices, in a date window. | SAP `ORCT` (IncomingPayments, `DocType rCustomer`); `amount` = `CashSum + TransferSum`. | Accounts sees the same receipts in the ledger; sales isolates the *unapplied* slice. | **`open_bal` is CP's own recomputation, NOT `ORCT.OpenBal`** — sourcemap proved CP `open_bal` 1,132,770 vs SAP `ORCT.OpenBal` 20,104.42 on the same receipt. Do **not** conflate. `amount` *does* tie to `ORCT` exactly (recon below). |
| **Contact Person (Open Payments)** | Assigned territory owner. | **Derived in-browser** from `main_group × state`, not a SAP field. | — | Exists as a filter/drill dimension only; never in the API payload. |
| **Claims** | Hand-keyed register of customer claims (NSO/TOT/LOTS/QPS/FIXED-BONUS/support/advertisement/FOC etc.) with a pass/hold workflow. | **None — Django-only.** Not a SAP feed. | Accounts has no equivalent object; the `ref_inv_no` values resolve in **no** SAP company. | Live: **31 rows, ₹12.72 L, every row on hold, `claim_passed`=0, all `main_group MT`.** `hold_amount = claim_amount − claim_passed`. Grew from 6 rows/₹2.67 L at last recon — it is a living manual ledger. |
| **Required Credit Limit** | How high a party's SAP credit limit must be so pending orders release without a credit block. | `total.value.required_limit`. | A **management target**, not read back from SAP. | `Required Limit = Total Outstanding × 1.02`; verified to the paisa (₹70.96 Cr × 1.02 = ₹72.38 Cr live). |
| **Total Outstanding (Credit page)** | Ledger dues **plus** open-order value. | `ledger (CurrentAccountBalance) + OIH revenue`. | Accounts would never fold un-invoiced orders (OIH) into "outstanding". | Live: ₹32.45 Cr ledger + ₹38.51 Cr OIH = ₹70.96 Cr. OIH = Order-In-Hand (open uninvoiced SOs). |
| **Payment Done / Remaining (Credit)** | `payment_done` = bank receipts (`ORCT`) dated on the as-of day; `remaining` = Total Outstanding − Payment Done. | `ORCT` on `as_of`. | — | Live: payment_done ₹1.99 Cr, remaining ₹68.97 Cr. |
| **Credit Lock** | Manager freezes *Total Outstanding* & *Required Limit* for N days (default 30). | **Django-only** flag. | **Not** SAP's `OCRD` freeze / `frozenFor`. | Live `lock: null` (no freeze active). Ledger/Payment/Remaining stay live even while locked — by design. |
| **Aging Remark / Special Price** | Per-invoice note/price overlay in the Oil & Bev RAW workspaces. | **Django overlay** (`aging-remark*`). SAP untouched. | Invisible to accounts/SAP. | WRITE endpoints — never executed. Overlay is **~0% populated** in practice. Mart has no remark overlay. |
| **Credit Terms / Payment Terms** | How long a party may take to pay (14 values: `ADVANCE/CASH/0 DAYS, COD, CAD, 20% ADVANCE, 45 % ADV, LC 60, NET-01…NET-30`). | `OCRD` payment terms (`customer-master.payment_terms`). | Same field accounts uses. | Drives what counts as "overdue". |

---

### Reconciliations (live Control Panel ↔ live SAP, 2026-08-25)

**1. Open-payment receipt → SAP `ORCT` — RECONCILES (exact on doc/party/amount).**
CP `open-payments 2026-08-20` row `{doc_no 826246676, code CUSTA000352, AT OVERSEAS, amount 656250}` → SAP Oil `IncomingPayments DocNum 826246676` = `CUSTA000352 / AT OVERSEAS / DocDate 2026-08-20 / TransferSum 656250 / DocType rCustomer / Cancelled tNO`. Amount exact. **Caveat:** CP `open_bal` is CP's own figure, **not** `ORCT.OpenBal` (documented mismatch in the sourcemap).

**2. Mart aging top customer → SAP `OCRD` — RECONCILES to the paisa (and flags intercompany).**
CP Mart aging `top_customer = "JIVO MART PVT LTD - DL", value 102,172,535.28` (50.8% of the whole Mart book) → SAP Mart `BusinessPartners CUSTA000874 CurrentAccountBalance = 102172535.28`. Exact. **This is intercompany** (a JIVO group company; note the twin vendor card `VENDA000942`, −₹3.87 Cr) — Mart's single biggest "receivable" is from a sister entity (relate to **C-0005**).

**3. Oil `outstanding` column = SAP net ledger — RECONCILES on 4/4 parties.**
| Party | CP Oil `outstanding` | SAP `CurrentAccountBalance` | CP Σ `bal` (gross open) |
|---|---|---|---|
| CUSTA000352 AT OVERSEAS | −2,592 | −2,592 | 656,250 |
| CUSTA000851 MAHAVIR TRADING | 2 | 2 | 2,127,342 |
| CUSTA000510 SUBHASH CHANDER | −1,214.07 | −1,214.0715 | 2,665,644.93 |
| CUSTA000116 HARINDER SINGH | −289,015.31 | −289,015.31 | 1,143,060 |
Proves `outstanding` = net ledger (repeated per row) while `bal` = gross invoice residual. AT OVERSEAS is the archetype: one ₹6.56 L invoice sits "open" in aging, a ₹6.56 L on-account receipt sits "unapplied" in open-payments (same day, same amount, receipt #2 above), and the net ledger is ≈ 0 — three of this domain's screens describing one settled trade (**C-0019**).

**4. Credit-page `ledger` = SAP net ledger — RECONCILES on 3/3 parties; 2% rule to the paisa.**
`CUSTA000979 SAGAR TRADERS` ledger 11,377 = SAP 11,377 (Required Limit 11,377×1.02 = 11,604.54 ✓); `CUSTA000808 VIRCHAND KHIMJI` 2,327.14 = SAP 2,327.1378; `CUSTA001068 KAILIAN FOODS` 275 = SAP 275. Book-level: `outstanding 709,589,860.20 = ledger 324,521,638.92 + OIH 385,068,221.30`; `required_limit 723,781,657.37 = outstanding × 1.02`; `remaining 689,715,086.22 = outstanding − payment_done 19,874,774`. All internal arithmetic ties.

**5. Oil aging row count ↔ SAP open-invoice count — DOES NOT TIE, by design.**
CP Oil aging = **4,843** open-balance rows; SAP Oil `Invoices` with `DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO'` = **13,082**. Expected mismatch: CP ages the reconciled ledger (invoices with a real remaining balance), SAP's `Open` flag is unreliable at JIVO (**C-0019** settled-by-JE / unapplied-on-account stay open; **C-0023** balance from JDT1).

**Live headline book (for reference):** Oil A/R gross ₹82.31 Cr (4,843 inv / 336 parties) · Mart Total Outstanding ₹20.12 Cr (58 cust, current 8.2%, >90d 75.4%) · Bev Total Outstanding ₹58.56 L (358 cust, current 38.7%) · Open-payments 2026-08-20 ₹1.915 Cr on 10 receipts · Claims ₹12.72 L, all held.

---

### Open questions

- **Is `credit` / `open-payments` strictly Oil-only?** Every sampled party resolved in the Oil DB and OIH is an oil-product concept (litres split premium/commodity/canola/olive), so I read both as the **Oil** book — but I did not find a company toggle to prove Mart/Bev are excluded. (Confidence ~85%.)
- **What exactly is CP `open_bal`?** Proven *not* `ORCT.OpenBal`; it appears to be CP's own JDT1-based unapplied-portion calc (sometimes = full receipt, sometimes a fraction). The precise formula is unconfirmed.
- **Oil bucket boundary field.** Oil main-view buckets derive from `days` (invoice age); whether the server pivot instead uses due-date/`tdd` for the boundary is unverified (the default Oil pivot is embedded in a `<script id="aging-data">`, not in the flat API I sampled).
- **Mart/Bev `original` vs `balance_due`.** `original` (e.g. Mart total ₹35.20 Cr) is the pre-payment document value; its exact SAP derivation (Σ `OINV.DocTotal` vs opening ledger) was not separately reconciled.
