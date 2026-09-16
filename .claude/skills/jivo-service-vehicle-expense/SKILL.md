---
name: jivo-service-vehicle-expense
description: Use when an employee's expense claim or reimbursement voucher arrives for JIVO and must be entered in SAP B1 — vehicle service, repair, fuel, CNG, toll, Fastag, puncture, scooty/Activa/Bullet costs, conveyance, Rapido/parking, refreshment, staff medicine, mobile recharge, courier, stationery, nut-bolt hardware. Triggers on "Expenses <name>" sheets, "I have incurred the following expenditure" vouchers, IMPREST claims, and any handwritten expense table signed off by an approver. Also use to check whether a claim is already keyed. NOT for a vendor's own tax invoice (jivo-ap-draft / jivo-ap-service-draft), labour loading bills (jivo-loading-unloading-ap) or freight (Transport-Bill-Playbook).
---

# Employee expense claim → service A/P draft (JIVO)

> 🔴 **ATTACHMENT RULE — COPY TO TARGET DOCUMENT = YES, on every file (Daman, 16 Sept 2026 · C-0090).**
> Whatever this skill attaches — to a draft, GRPO, A/P, credit memo, payment, JV, A/R, anything —
> every `Attachments2` line gets **`CopyToTargetDoc = "tYES"`** (the "Copy to Target Document"
> tick). An API upload lands **`tNO`** by default, so the scan does NOT follow the document when
> it is copied onward (GRPO → A/P, draft → posted). Set it in the SAME PATCH as the Approve stamp,
> **in all three books**, before pointing the document at the row:
> - Oil / Bev: `{"AbsoluteEntry":N,"LineNum":1,"U_CHK":<KB>,"U_CHK2":"OK","CopyToTargetDoc":"tYES"}`
> - Mart (no `U_CHK` columns): `{"AbsoluteEntry":N,"LineNum":1,"CopyToTargetDoc":"tYES"}`
>
> One object per line (line 2, 3 … too). Read back `Attachments2(N)`: every line must show
> `"CopyToTargetDoc": "tYES"` — if any shows `tNO`, the entry is not done. Proven live 16 Sept on
> Oil 177765/177767, Mart 59273, Bev 43223 (HTTP 204, stamp kept).

Internal skill. Daman named this class **"service"** and taught it over one
long session, 2026-09-01/02, correcting five drafts line by line. Every rule
below cost him a correction — follow it rather than re-deriving it. Shared
rules live in `jivo-ap-draft`; RULE 0 in `CLAUDE.md` governs the write.

**What this class is:** a `dDocument_Service` A/P invoice against the
employee's **IMPREST** account. No GRPO, no items, **no TDS** — it reduces
the float JIVO already advanced them. It is not a vendor bill.

**The five settled rules, in one place:**

| | |
|---|---|
| **C-0067** | Every two-wheeler cost is **CONVEYANCE 5690002** — service, repair, puncture, fuel alike |
| **C-0070** | A **CONVEYANCE line never carries a vehicle code** — Dim1 is `CANOLA`, always |
| **C-0071** | Every printed row gets a **real GL head**; `5680000 GENERAL EXPENSES` is not a bucket |
| **C-0072** | The **dates come from the expense**, never the approver's signature |
| (house) | **One draft line per printed row** — merging rows destroys the effective month |

---

## 1 · Whose imprest — there is usually a decoy

Fetch `BusinessPartners --all` and match the name **in code, not by filter**
(`toupper` is unsupported; C-0036 forbids name-matching a vendor). Expect
**two cards for the same person**:

| | Use? | How to tell |
|---|---|---|
| `ORGV…` NAME … **IMPREST** JWPL#### | ✅ **this one** | dozens of past claims; non-zero balance = float held |
| `VENDA…` NAME (plain) | ❌ decoy | zero invoices, zero balance |

Measured: `ORGV000029 ARSHDEEP SINGH SO GT DL 15000 IMPREST JWPL0007`
(58 claims, bal ₹17,148.90) vs `VENDA001428 ARSHDEEP SINGH` (0 claims).
Booking the decoy hides the claim from the float reconciliation. Same trap on
Gurwinder: `ORGV000033 … DRIVER 5000 IMPREST` is live, `ORGV000146` is empty.

**When the paper names two people** — a routing note ("<Name> — entry in")
**beats** the form's "Expenses Detail" name. Say whose imprest you used out
loud; the other person usually has one too, and a human may move it later
(they moved draft 55800 from Arshdeep to Gurditt in the client).

## 2 · Read the marks — they are dimensions, not doodles

| On the paper | Field | Meaning |
|---|---|---|
| **TR** | `CostingCode3` (Budget) | `Transprt` |
| **BO** | `CostingCode3` | `BackOff` |
| **F** | `CostingCode3` | `FACT_COM` |
| "Common" | `CostingCode3` | `FACT_COM` (C-0027) |
| vehicle no. (4857, 8826) | `CostingCode` (Dim1) | match the last 4 digits to an active Dim1 — **but only on a four-wheeler head**, see §4 |
| each row's date | `CostingCode2` (**effective month**) | that row's own `MM-YYYY` |

Dim3 also seen: `Sales` (paired with `CostingCode4` `E-COM`).

## 3 · One line per printed row

**The safe default is one draft line per row on the sheet** — and the totals
then reconcile to the printed subtotals by themselves.

Merging rows that share an account is what destroys the effective month: on
the first build of draft 55798 seven heads were each collapsed to one line
and all of them inherited `08-2026`, burying **₹481 of July spend** in
August. Daman's words: *"effective months mean the months in which the
kharcha actually is."*

A sheet legitimately mixes months — July and August rows in one claim are
normal, each keeping its own `CostingCode2`. If you must merge, merge **only
within one month and one head**, and put the paper's date in
`ItemDescription` so the split stays auditable.

**A "Miscellaneous ₹1,899" subtotal is the employee's grouping, not an
account.** Give every row underneath it a real head (C-0071).

## 4 · The expense-head map, and which heads take a vehicle

| Head | Account | What lands here | Dim1 |
|---|---|---|---|
| **CONVEYANCE** | **5690002** | Rapido/taxi/parking **and EVERY two-wheeler cost** (C-0067) | **`CANOLA` always (C-0070)** |
| REPAIR & MAINT. VEHICLE | 5650002 | **four-wheelers only** | the vehicle code |
| FUEL - VEHICLES | 5650015 | four-wheeler fuel/CNG; litres in `U_Recvd_Qty` | the vehicle code |
| TOLL EXPENSE - VEHICLES | 5660005 | Fastag, toll | vehicle or `CANOLA` |
| REFRESHMENT | 5630004 | meals, snacks, cold drinks, travel meals | `CANOLA` |
| STAFF WELFARE | 5630003 | medicine **and staff electronics — charger adapter, aux cable** | `CANOLA` |
| TELEPHONE MOBILE AND INTERNET | 5680003 | recharges | `CANOLA` |
| POSTAGE & COURIER | 5680023 | parcels | `CANOLA` |
| REPAIR & MAINT. OFFICE & BUILDING | 5650001 | **hardware and fittings — nut bolt, nut tool** | `CANOLA` |
| PRINTING AND STATIONERY | 5680012 | | `CANOLA` |
| GENERAL EXPENSES | 5680000 | **last resort only (C-0071)** | `CANOLA` |

**C-0067 — two-wheelers are CONVEYANCE, always.** Scooty, Activa, Bullet:
every cost, whatever the paper calls it. "Service" or "repair" on the sheet
does **not** move it to 5650002 — that head is four-wheelers only. On one
voucher the Rumion bumper repair stayed 5650002 while the Activa mudguard
went 5690002.

**C-0070 — a car number is not eligible on CONVEYANCE.** 5690002 takes
`CANOLA` even when the row plainly names a vehicle; because two-wheeler costs
are all conveyance, a scooter loses its vehicle dimension with them. Every
5690002 line in the posted precedents carries CANOLA, none a vehicle.

**A vehicle with no Dim1 code at all** (the Bullet; Swift, Grand Vitara and
New XL6 2819 are also missing) → `CANOLA`. Say so; never invent a code.

## 5 · The five dimensions

| Dim | Field | Value |
|---|---|---|
| 1 Variety | `CostingCode` | vehicle code on four-wheeler heads; **`CANOLA` everywhere else** |
| 2 Effective month | `CostingCode2` | that row's own expense month, `MM-YYYY` |
| 3 Budget | `CostingCode3` | `BackOff` · `Transprt` · `FACT_COM` · `Sales` — from the TR/BO/F mark |
| 4 **Sub-budget** | `CostingCode4` | **`Admin`** by default · **`IT`** for telecom & electronics (mobile recharge) · `E-COM` with `Sales` |
| 5 | `CostingCode5` | `DL` |

## 6 · Header and dates

`DocType dDocument_Service` · `DocumentSubType bod_None` ·
`BPL_IDAssignedToInvoice` **1 = DELHI** · line `LocationCode` **1** ·
`GSTTransactionType gsttrantyp_BillOfSupply` · `TaxCode Exampt` ·
**`WTLiable tNO`, and no `WithholdingTaxDataCollection` at all.**

### C-0072 — the dates come from the EXPENSE, never the signature

| Field | Value |
|---|---|
| `NumAtCard` | **`<EXPENSE MONTH> YY/<total>`** — `JUL 26/8890` for a 27-07 expense even if approved in August. Two numbers (`JUN 26/33885/32451`) = claimed/approved; the second is `DocTotal`. |
| `TaxDate` (document date) | **the latest expense date printed on the sheet** |
| `DocDate` (posting date) | **the same latest expense date** — *"because the latest kharcha is of this date"*. Roll to the **1st of the next open month only when that expense month is already CLOSED**. |
| `DocDueDate` | same as `DocDate` |
| `Series` | whichever month `DocDate` lands in |

Dating by the approver's signature is the original mistake: draft 55799 was
keyed `AUG 26/8890` dated 31-08 when it was a 27-07 Bullet service. It is
also the one sheet that rolls forward — July is closed, so it posts
**01-08-2026** with document date 27-07-2026. Its August siblings post on
their own last row (23-08, 29-08, 31-08). Precedent shows the roll-forward
too: `MAY 26/14551` posts 2026-06-01 with TaxDate 2026-05-31.

**Oil BPL-1 series:** Jul-26 `3335` · Aug-26 `3336` · Sep-26 `3337`. There is
no readable Series entity — probe an unknown month; a wrong number is refused
with `[SAP -10] 10000521 … define the numbering series`, which is safe.
**Patching `Series` silently resets `TaxDate` to the new `DocDate`** —
re-send `TaxDate` in a second PATCH and read it back.

`Comments`: `BEING EXPENSE BOOKED AGAINST <HEADS> AMOUNT <n>/-, INVOICE NO.
<ref>, DATED <dd-mm-yyyy>` + whatever the paper says that no field can hold
(the other person's name, the vehicle, the work done).

**One draft per approved paper**, each with its own scan — never one merged
document. Each sheet carries its own signature and total.

## 7 · Attach

Follow `jivo-ap-draft/reference/attachments-upload.md` — `-H "Expect:"` is
required. Two more traps measured live:

- **The upload response is not valid JSON.** It embeds
  `\\10.10.101.52\Attachments_Oil\…` with single backslashes, so `json.load`
  dies with `Invalid \escape` and your `AbsoluteEntry` comes back empty while
  the row was created fine. Pull the id with
  `grep -o '"AbsoluteEntry" : [0-9]*'`, never a JSON parser. If you lost one,
  probe `Attachments2(N)` upward for the FileName — other operators' rows are
  interleaved, the counter is shared and moves fast.
- **`PATCH Drafts(id)` with `DocumentLines` keeps `AttachmentEntry`** — but
  send the **complete** line array with every `LineNum`; a partial collection
  rewrites what you omit.

## 8 · Editing a draft: rebuild, don't re-patch

**Changing a draft's line count by PATCH corrupts the price fields.** SAP
keeps the old `UnitPrice`/`GrossPrice` on every `LineNum` that already
existed and sets them correctly only on newly-added ones. Re-patching 7
grouped lines into 16 left rows 1–7 showing the old grouped amounts as unit
price (₹7,020 against a ₹40 nut bolt) while `LineTotal` and `DocTotal` still
read correctly — invisible unless you look at the price column.

**Do not patch the prices back.** Sending `UnitPrice`/`Price`/`GrossPrice` on
those rows made SAP recompute `LineTotal` into fractions (₹0.228, ₹20.678 …)
and dropped `DocTotal` from ₹8,919 to ₹8,874.

**Rebuild instead:** detach (`AttachmentEntry: null`) → `delete draft` →
create fresh with the final line set → re-point the same `Attachments2` row.
On a clean create you set only `LineTotal` and SAP fills `UnitPrice` to match.
Draft 55798 → rebuilt as 55888. **The DocEntry changes — tell the operator.**

## Pre-flight — tick before `--yes`

- [ ] IMPREST `ORGV…`, not the plain `VENDA…` twin; whose account, said out loud
- [ ] one line per printed row; Σ lines = the approver's total, to the rupee
- [ ] `CostingCode2` checked **row by row** against each printed date; per-month
      totals tallied and reconciled to the sheet
- [ ] every row on a real GL head — nothing parked in 5680000
- [ ] every two-wheeler line on **5690002**; 5650002 only for four-wheelers
- [ ] no vehicle code on any 5690002 line; Dim1 `CANOLA` everywhere else
- [ ] Dim3 from the TR/BO/F mark · Dim4 `Admin`, or `IT` for telecom/electronics
- [ ] `NumAtCard` = **expense** month + total; clean in Drafts **and** posted
- [ ] `TaxDate` = `DocDate` = the latest expense date (roll forward only if that
      month is closed); `Series` matches the posting month
- [ ] re-read `TaxDate` after any `Series` patch
- [ ] `LineTotal` == `UnitPrice` on every row — check after any line edit
- [ ] `WTLiable tNO`, no WT block; BPL 1, LocationCode 1, Dim5 DL
- [ ] scan attached, `U_CHK2 OK` (Oil), read back byte-identical

## The worked batch (2026-09-01/02, USER07 = HARSH, all held)

| Draft | Whose | Ref | Amount | Posting | Document |
|---|---|---|---|---|---|
| 55888 | Arshdeep `ORGV000029` | AUG 26/8919 | ₹8,919 | 23-08 | 23-08 |
| 55799 | Arshdeep | JUL 26/8890 | ₹8,890 | **01-08** | 27-07 |
| 55800 | Gurditt `ORGV000463` | AUG 26/2000 | ₹2,000 | 29-08 | 29-08 |
| 55804 | Arshdeep | AUG 26/51532 | ₹51,532 | 23-08 | 23-08 |
| 55805 | Gurwinder `ORGV000033` | AUG 26/3213 | ₹3,213 | 31-08 | 31-08 |

55805's paper carries a green **"Debit ₹40"** — booked at full value, so the
₹40 needs an A/P credit memo after posting (same house rule as the loading
bills).
