---
type: foundation
sap_tables: [OWHT, WHT1, CRD4, OCRD, PCH5, DRF5, RPC5, PCH1, DRF1, PDN1, OPCH, ORPC, JDT1, OJDT, OACT]
objtype: 18
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# TDS / withholding — the one number on the bill that nobody else can give you

> TDS is money JIVO keeps back from the vendor and pays to the government instead.
> It is one of the five things an A/P entry **never inherits** — not from the GRPO,
> not from the PO, not from the vendor's last bill. Somebody has to decide it on
> every single bill, and on **43 % of Oil bills, 82 % of Mart bills and 29 % of
> Beverages bills** the answer is yes. This note is that decision, end to end.
>
> Referenced from [[Chart-of-Accounts]] as `[[TDS-on-Purchases]]` and from
> [[Purchase-to-Pay]] as `[[TDS-Withholding]]`. This file is both.

## The short version

1. **TDS lives on exactly two documents: the [[AP-Invoice]] and the
   [[AP-Credit-Memo]]** (and their [[Document-Drafts]]). Every other withholding
   table SAP ships — sales invoices, deliveries, incoming payments, outgoing
   payments, payment drafts, journal vouchers — has **zero rows in all three
   books**. *Measured.*
2. **It is deducted at invoice time, never at payment time.** `VPM6` (the
   outgoing-payment withholding table) is empty in Oil, Mart and Beverages, and
   `OPCH.PostPmntWT` is `N` on 100 % of 16,334 Oil bills. When you pay the vendor
   the TDS is already gone. *Measured.*
3. **The vendor card is a hard gate.** In the last 365 days **every single**
   A/P bill carrying TDS — 3,164 Oil, 2,639 Mart, 420 Bev — belongs to a vendor
   whose `OCRD.WTLiable` is `Y`. Not one exception. If the flag is off you cannot
   withhold until master data is changed.
4. **But the flag does not tell you the answer.** Of 231 Oil vendors that are
   flagged *and* carry a TDS code and were billed this year, 150 always had TDS
   deducted, **63 sometimes and 18 never**. The vendor's own posted precedent beats
   the master flag — that is the `jivo-ap-draft` rule, and it is measured here.
5. **Two decisions, not one.** Tick which *lines* are in the TDS base
   (`PCH1.WtLiable`), and pick the *section code* for the document
   (`PCH5.WTCode`). Ticking lines alone produces no TDS — 67 hand-keyed Oil drafts
   since 2026-06-01 prove it.
6. **C-0018 is now solved, and it was the payload, not the API path.** Send
   `WithholdingTaxDataCollection: [{WTCode: "…"}]` on the header and SAP computes
   the rate, the base and the account by itself. Proven live on two drafts today.
   → [The CLI question](#the-cli-question-c-0018-resolved)
7. **`DocTotal` is net of TDS.** The vendor is credited the amount *after*
   withholding. Any figure you quote off `DocTotal` is already net.

---

## What you decide, and what SAP does by itself

The operator's actual question, answered in one table. *Measured on live documents
unless marked.*

| # | Field | Who fills it | What it means | Where the value comes from |
|---:|---|---|---|---|
| 1 | `OCRD.WTLiable` (vendor card) | **master data — set before the bill** | is this vendor subject to TDS at all | the vendor's PAN / status. Off = you cannot withhold. Oil 548 of 2,235 vendors are `Y` |
| 2 | `CRD4` (vendor's TDS code list) | **master data** | which sections apply to this vendor | Oil 389 of the 548 liable vendors have one; **159 do not** |
| 3 | `PCH1.WtLiable` per line | **you, on every bill** | is this line's amount in the TDS base | the nature of the expense — see [the decode table](#every-section-jivo-deducts-under) |
| 4 | `PCH5.WTCode` (document) | **you, on every bill** | which section / rate | the vendor's code list, narrowed by what the bill is for |
| 5 | `PCH5.TdsRate` | **SAP** | the % | `WHT1.Rate` for that code, by `EffecDate` |
| 6 | `PCH5.TdsBAmt` | **SAP** | the base | sum of the liable lines, **excluding GST** |
| 7 | `PCH5.WTAmnt` | **SAP** | the rupees withheld | base × rate, rounded (`RoundType` = `C`, commercial) |
| 8 | `PCH5.TdsAcc` | **SAP** | the GL credited | `OWHT.ApTdsAcc` for that code — **a different number in each book** |
| 9 | `OPCH.WTSum` | **SAP** | document total TDS | sum of the `PCH5` rows |
| 10 | `OPCH.DocTotal` | **SAP** | what the vendor is owed | taxable + GST − TDS |
| 11 | the journal line | **SAP** | Cr `2133xxx`, vendor credited net | posted at Add |
| 12 | dimensions on the TDS line | **nobody — always empty** | — | 0 of 3,179 Oil TDS journal lines carry a profit centre or any of dimensions 2–5 |

**Nothing about TDS is inherited.** Measured on lines copied from a GRPO in the last
365 days:

| Book | Copied A/P lines | GRPO said no → bill says **yes** | GRPO said yes → bill says **no** | Agreed |
|---|---:|---:|---:|---:|
| Oil | 10,626 | **2,025** (19 %) | 37 | 8,513 |
| Mart | 8,216 | **7,605** (93 %) | 10 | 601 |
| Bev | 3,400 | 150 | 93 | 3,157 |

In Mart the GRPO essentially never carries the flag and the operator sets it on the
bill 93 % of the time. `PDN5` — the GRPO's own withholding-tax table — is **empty in
all three books**, so a GRPO's `WtLiable` tick is a label with no tax behind it and
never posts to a `2133xxx` account (confirmed: no TDS account appears in the
`TransType 20` GL fingerprint, `_data/gl-20-OIL.md`).

---

> **Freight is the biggest single TDS population, and the leakiest.** 27 Oil transporter
> bills of `WTLiable='Y'` vendors carry zero TDS in FY26-27 (₹14.19 L), and it is not a
> threshold effect. The section code follows the **4th character of the vendor's PAN**
> (`P`/`H` → 1 %, otherwise 2 %) on 24 of 25 transporter cards →
> [[Transport-Bill-Playbook]], [[transport-ap-evidence]].

## Every section JIVO deducts under

The live sections, with the rate SAP applies and the GL it credits **in each book**.
Volumes are all-history `PCH5` rows joined to their invoice. *Measured.*

### The current block — section `393(1)`, live from 2026-06-01

| Code | What it is | Rate | Official section | Oil GL | Mart GL | Bev GL | Bills (Oil / Mart / Bev) |
|---|---|---:|---|---|---|---|---|
| `1031` | Purchase of goods | 0.1 % | `393(1)[8(ii)]` | `2133022` | `2133025` | `2133020` | 169 / 234 / 8 |
| `1024` | Contractors (others) | 2 % | `393(1)[6(ii)]` | `2133018` | `2133021` | `2133016` | 161 / 98 / 39 |
| `1023` | Contractors (individual/HUF) | 1 % | `393(1)[6(i)]` | `2133016` | `2133019` | `2133014` | 41 / 14 / 2 |
| `1230` | Contractors (ind/HUF) — **Bev duplicate of `1023`** | 1 % | `393(1)[6(i)]` | — | — | `2133014` | — / — / 24 |
| `1027` | Professional fees | 10 % | `393(1)[6(iii)]` | `2133017` | `2133020` | `2133015` | 13 / 9 / — |
| `1006` | Commission / brokerage | 2 % | `393(1)[1(ii)]` | `2133019` | `2133022` | `2133017` | 67 / 28 / 5 |
| `1026` | Technical fees / royalty | 2 % | `393(1)[6(ii)]` | `2133021` | `2133030` | `2133019` | 10 / 2 / 2 |
| `1009` | Rent — land / building | 10 % | `393(1)[2(ii)]` * | `2133014` | `2133017` | `2133012` | 10 / 4 / — |
| `1008` | Rent — plant & machinery | 2 % | `393(1)[2(i)]` | `2133015` | *not set up* | `2133013` | never used |
| `1019` | Interest on securities | 10 % | `393(1)[5(iii)]` | `2133020` | `2133023` (`1042`) | `2133018` | never used on a bill |
| `1041` | Payment to non-resident | 20 % | `393(2)` | `2133023` | `2133027` | *not set up* | 2 / — / — |
| `1010` | Purchase of property | 1 % | `393(1)[3(i)]` | `2133024` | *not set up* | *not set up* | never used |
| `1002` | Salary | 0 % | `392(1)` | `2133004` | `2133004` | `2133004` | never on a bill — salary TDS is a manual JE |

\* **Oil's `1009` is mis-tagged**: its `OffclCode` is `393(1)[1(ii)]` and `Section`
`26` — the *commission* section — while Mart and Beverages carry `393(1)[2(ii)]`.
Oil's own GL name says `393(1)[2(ii)]`. ₹1,65,570 of rent TDS on 10 Oil bills is
therefore filed under the commission section in the withholding report.
*Measured; the reporting consequence is inferred.*

**Mart alone has six extra "low-rate" contractor and commission codes** —
`1043` 0.2 %, `1044` 0.05 %, `1045` 0.01 %, `1046` 0.02 %, `1047` 0.2 %, plus
`1042` interest — with their own accounts `2133018/24/26/28/29/23`. Only `1045`
has ever been used (one bill, ₹7). Mart's `2133018` is **commission @0.20 %**;
Oil's `2133018` is **contractor @2 %**. Same number, different section, different
book.

### The old block — sections `194x`, closed to new bills after 2026-06-25

Still needed to read anything dated before then, and still the block the housekeeping
accounts live in.

| Code | What it is | Rate | Oil GL | Mart GL | Bev GL | Bills (Oil / Mart / Bev) |
|---|---|---:|---|---|---|---|
| `TDS` | 194Q purchase of goods | 0.1 % | `2133010` | `2133010` | `2133010` | 1,922 / 2,322 / 86 |
| `C194` | 194C contractor — company | 2 % | `2133006` | `2133006` | `2133006` | 1,844 / 674 / 203 |
| `194H` | 194H commission / brokerage | 2 % | `2133007` | `2133007` | `2133007` | 802 / 148 / 1 |
| `194C` | 194C contractor — individual/HUF | 1 % | `2133003` | `2133003` | `2133003` | 712 / 155 / 273 |
| `94JB` | 194J professional | 10 % | `2133005` | `2133005` | `2133005` | 189 / 37 / 20 |
| `94JA` | 194J technical | 2 % | `2133009` | `2133009` (**inactive**) | `2133009` | 153 / — / 32 |
| `94IB` | 194I rent land/building | 10 % | `2133001` | `2133001` | `2133001` | 133 / 35 / 35 |
| `195` | s.195 foreign service | 20 % | `2133012` | `2133013` * | *not set up* | 49 / 21 / — |
| `94IA` | 194I rent plant/machinery | 2 % | `2133002` | `2133002` * | `2133002` | 4 / — / — |
| `94I1` | 194IA purchase of property | 1 % | `2133013` | — | — | 1 / — / — |
| `194` `1C94` `19C4` `94_C` `C19` `H194` `194A` | Mart-only low-rate 194C/194H variants | 0.01–0.25 % | — | `2133015/14/12/09/`**`2131021`**`/02/16` | — | — / 95 / — |

\* Mart master-data mismatches, measured: code `195` has `Rate` **0** in `OWHT` and
`WHT1` (only `ItrNCRate`/`PanNCRate` are 20) yet all 21 Mart bills applied 20 % —
*inferred*: they picked up the no-PAN rate. Code `94IA` ("rent of plant") points at
an account named `TDS @ 0.20% 194H`, and `94JA` ("technical") at
`TDS ON @ 0.05% 194C`. **Mart's `C19` credits `2131021`, which sits inside the INPUT
GST block** — the trap [[Chart-of-Accounts]] already flags, here confirmed with
6 bills and ₹6,718.

### Configured vs actually used

| Book | Codes configured (`OWHT`) | Inactive | Ever used on a bill | Never used |
|---|---:|---:|---:|---:|
| Oil | 22 | 0 | 18 | 4 (`1002`, `1008`, `1010`, `1019`) |
| Mart | 31 | 1 (`94JA`) | 22 | 9 |
| Bev | 19 | 0 | 13 | 6 |

**Thresholds are configured but are not a per-bill gate.** `OWHT.Threshold` holds
real numbers (`1031` ₹50,00,000 · `1023` ₹1,00,000 · `1027`/`1008`/`1009`/`1026`
₹50,000 · `1006` ₹20,000 · `1024`/`1019` ₹10,000) and `NoDedThrsh` is `N` on every
code. Measured: TDS was deducted on 98 of 161 Oil `1024` bills whose base was below
₹10,000 — the smallest base deducted from was **₹75** under a ₹10,000 threshold, and
₹60 under `1006`'s ₹20,000. *Inference*: SAP is applying the threshold cumulatively
per vendor per year, so once a vendor crosses it every later bill withholds. **Do not
expect a small bill to escape.**

---

## Which vendors are liable

*Measured 2026-08-24 from `OCRD` and `CRD4`.*

| Book | Vendors (`CardType='S'`) | Flagged `WTLiable='Y'` | Share | With a TDS code list (`CRD4`) | **Flagged but no code** |
|---|---:|---:|---:|---:|---:|
| Oil | 2,235 | 548 | 25 % | 389 | **159** |
| Mart | 1,248 | 338 | 27 % | 87 | **251** |
| Bev | 1,699 | 376 | 22 % | 148 | **228** |

A flagged vendor with no code in `CRD4` will produce **no TDS by itself** — the
operator has to name the section. That gap is the majority of flagged vendors in
Mart and Beverages.

`OCRD.WTCode` — the single default-code field — is effectively unused (9 Oil rows,
all `TDS`; empty in Mart). The real list is the `CRD4` child table, which the
Service Layer exposes as `BPWithholdingTaxCollection`. Codes assigned today are
almost entirely the new `393(1)` block; the old codes were stripped off the cards at
the cutover.

**Four customers are flagged liable in Oil and four in Beverages, and it has never
mattered**: `INV5`, `RIN5`, `RDN5`, `RDR5`, `DLN5`, `QUT5` and `RCT6` are empty in
all three books. JIVO has never withheld on the sales side, and the `ArTdsAcc` /
`ArSurAcc` / `ArCessAcc` / `ArHscAcc` half of every `OWHT` row is configured and
dead.

---

## How the deduction reaches the ledger

Traced on a real posted Oil bill, **DocEntry 49820 / DocNum 626084154**,
2026-08-19, vendor `VENDA000224`, `TransId 228422`. Goods purchase, code `1031`.

| | Account | Name | Debit ₹ | Credit ₹ |
|---|---|---|---:|---:|
| 0 | `2110001` | SUNDRY CREDITOR DOMESTIC OIL | | **60,87,924** |
| 1 | `2133022` | TDS @ 0.1 % 393(1)[8(ii)] code 1031 | | **5,804** |
| 2 | `2131002` | INPUT IGST @ 5 % | 2,90,177.50 | |
| 3 | `2140001` | GOODS RECEIVED BUT NOT INVOICED | 58,03,550 | |
| 4 | `5680014` | SHORT AND EXCESS | 0.50 | |

Read it as: base ₹58,03,550 + IGST ₹2,90,177.50 = ₹60,93,727.50 gross; TDS 0.1 % of
the base = ₹5,804 credited to `2133022`; the vendor is credited the **remainder**,
₹60,87,924 — which is exactly `OPCH.DocTotal`. The base **excludes GST**.

A service bill behaves identically — DocEntry 49732, code `1027`, professional
fees: expense ₹55,000 Dr, CGST+SGST ₹4,950 each Dr, TDS ₹5,500 Cr to `2133017`,
vendor ₹59,400 Cr.

Two things about that journal matter when you go looking for TDS later:

- **`JDT1.WTLine` and `JDT1.WTLiable` are `N` on the TDS line itself** — `N` on all
  528,538 Oil journal lines, in fact. You cannot find TDS postings by those flags.
  Match on `Account LIKE '2133%'`, or read `PCH5`.
- **The TDS line carries no dimensions.** 0 of 3,179 Oil TDS lines have a profit
  centre or any of dimensions 2–5, while the expense line next to it usually does.
  → [[Cost-Centres-and-Dimensions]]

### And where the money goes afterwards

*Measured, all history, Oil.* The section accounts are credited and then **almost
never cleared per account**. The challan is paid out of `2133011 TDS PAYABLE`, which
has been debited ₹1,81,86,349 (₹1,61,54,192 of it by outgoing payments) against only
₹34,49,430 of credits. Not one of the new `393(1)` accounts
(`2133014/16/18/19/21/22`) has **ever** been debited.

| Book | Section accounts (credit balances) | `2133011 TDS PAYABLE` | Family net (`2133%`) |
|---|---:|---:|---:|
| Oil | ₹1,44,45,262 Cr across 20 accounts | ₹1,47,36,919 **Dr** | ₹2,91,657 Dr |
| Mart | 23 accounts in credit | ₹67,10,273 **Dr** | ₹3,37,250 Dr |
| Bev | 14 accounts in credit | ₹29,306 Dr — **no outgoing payment ever** | **₹7,02,551 Cr** (₹9,85,290 Cr − ₹2,82,739 Dr) |

So **a single `2133xxx` balance never means "TDS still owed under that section"** —
only the family nets. And Beverages has never made an *outgoing payment* against any
TDS account in its whole history — ₹9,85,290 credited, only ₹2,82,739 ever debited
(₹29,306 of it on `2133011`). Its ₹7,02,551 is unreconciled inside SAP, wherever the
challan was actually paid from. → open question.

---

## Invoice or a separate journal entry? Measured.

The claim tested: *"TDS is more often handled by a separate manual journal entry than
on the invoice itself."* **It is not.** `2133xxx` journal lines by posting origin,
last 365 days:

| Origin (`OJDT.TransType`) | Oil lines | Mart lines | Bev lines | Oil credit ₹ | Mart credit ₹ | Bev credit ₹ |
|---|---:|---:|---:|---:|---:|---:|
| **18 A/P invoice** | **3,179** | **2,660** | **424** | 78,61,372 | 38,38,398 | 4,06,822 |
| 30 manual journal entry | 108 | 118 | 22 | 28,92,378 | 33,49,158 | 1,36,677 |
| 46 outgoing payment (challan) | 29 | 3 | 0 | 0 | 0 | 0 |
| 19 A/P credit memo | 2 | 10 | 0 | 0 | 0 | 0 |
| 24 incoming payment | 1 | 0 | 0 | 21,963 | 0 | 0 |

**96 % of TDS lines are on the invoice** in every book. But by *amount* the manual
journal is not a rounding error — **27 % of Oil TDS credits, 47 % of Mart's** — and
it is doing a different job, not the same job by hand. Oil's manual-JE TDS is:

| What | Account | Lines |
|---|---|---:|
| Interest to NBFCs (monthly, no vendor bill exists) | `2133008` | 40 |
| Salary TDS | `2133004` | 26 |
| Year-end provisions, their reversals and vendor-side adjustments ("MARCH 2026 PROVISION", "PROVISION REVERSAL") | `2133005/03/06/01/07/10` | 32 |
| Corrections ("TDS REVERSAL") | `2133017` | 2 |
| Moving the liability to `TDS PAYABLE` before the challan | `2133011` | 2 |

**Rule:** if a vendor invoice exists, TDS goes on the invoice. The manual journal is
for interest, salary, provisions and fixing mistakes. → [[Journal-Entry]]

## Never at payment time

*Confirmed, and stronger than the 2026-08-23 memory note claimed.* It is not "mostly
not withheld at payment" — it is **never**:

| Table | What it would hold | Oil | Mart | Bev |
|---|---|---:|---:|---:|
| `VPM6` | withholding on an outgoing payment | **0** | **0** | **0** |
| `PDF6` | withholding on a payment draft | 0 | 0 | 0 |
| `RCT6` | withholding on an incoming payment | 0 | 0 | 0 |
| `OPCH.PostPmntWT` | "post withholding at payment" flag | `N` ×16,334 | `N` | `N` |
| `OVPM.PmntWTCert` | payment carries a TDS certificate | `N` ×14,851 | `N` | `N` |

The 29 Oil `TransType 46` lines that touch a `2133xxx` account are **debits** — the
challan going out, not a deduction going in.

## The A/P credit memo barely reverses it

`RPC5` has 319 rows in Oil, 138 Mart, 57 Bev — but the row usually carries base 0 and
tax 0. Only **4 of 1,595 Oil credit memos** have a non-zero `WTSum` (₹6, ₹140,
₹1,992, ₹3,839). **Reducing a bill with a debit note does not give the TDS back**;
the deduction stays where it was posted. → [[AP-Credit-Memo]]

---

## The CLI question — C-0018 resolved

**C-0018** (2026-08-21) recorded that `sapb1 draft purchase-invoice` produces
`WTLiable tNO` and TDS 0 even when the vendor is liable, and said the fix was *not
yet verified*. It is verified now, and the answer is:

> **It is the payload, not the API path.** The Service Layer computes TDS perfectly
> well. The earlier drafts sent no withholding block at all.

*Evidence — the shared write log `queries/*/sap-writes.jsonl`, 2026-08-24, and a
HANA read-back:*

| Draft | Book | What the payload sent | What SAP produced |
|---|---|---|---|
| **54937** (2026-08-21, C-0018) | Oil | no withholding block; no `WTLiable` on lines | `WTSum` 0, no `DRF5` row, 0 liable lines — although the vendor is `WTLiable='Y'` |
| **55177** (2026-08-24 19:25) | Oil | `WithholdingTaxDataCollection: [{"WTCode":"1027"}]` + line `WTLiable: tYES` — **code only, no rate, no amounts** | `DRF5` row: rate **10 %**, base **₹1,00,000**, TDS **₹10,000**, account **`2133017`**; header `WTSum` ₹10,000; `DocTotal` ₹1,08,000 = 1,00,000 + 18,000 GST − 10,000 |
| **39790** (2026-08-24 18:56) | Mart | same, plus explicit `Rate: 10`, `TaxableAmount: 25000`, `WTAmount: 2500` | `DRF5` row: TDS **₹2,500**, account **`2133020`**; `DocTotal` ₹27,000 |

So the recipe is:

1. **Header:** `WithholdingTaxDataCollection: [{"WTCode": "<code>"}]`. Sending only
   the code is enough — SAP looks the rate and the account up from `WHT1`/`OWHT` and
   computes the base from the liable lines. Sending the rate and amounts as well also
   works.
2. **Every line that is in the base:** `WTLiable: "tYES"`.
3. **The line flag alone does nothing.** Measured on hand-keyed drafts too: since
   2026-06-01, 67 Oil A/P drafts have `DRF1.WtLiable='Y'` on some line and **no
   `DRF5` tax row at all** (USER07 19, USER09 23, USER08 23, USER06 1, USER34 1).
   Ticking the row in the client without a code in the withholding window produces
   the same nothing the CLI did.
4. **Read it back before Add** — `WTAmount`, and `WTSum` in HANA. `readback.py`
   already flags "TDS 0 but the vendor is TDS-liable".

**Correction candidate (not yet filed):** *"An A/P draft made through the Service
Layer gets TDS only if the header carries `WithholdingTaxDataCollection` with the
`WTCode`; the per-line `WTLiable: tYES` alone yields `WTAmount` 0. Send the code and
SAP computes rate, base and account."* This **refines C-0018** rather than
contradicting it, and it **does contradict** the sentence in [[AP-Invoice]] that
calls the zero "a property of the *API path*".

---

## Pre-flight — before you press Add, or send `--yes`

- [ ] **Vendor card**: `OCRD.WTLiable = 'Y'`. If not, TDS is impossible on this bill
      — 100 % of TDS bills in all three books are on flagged vendors. Master data
      first, entry second.
- [ ] **Section code**: is there a `CRD4` entry (`BPWithholdingTaxCollection`)? If
      the list is empty — as it is for 159 flagged Oil vendors, 251 Mart, 228 Bev —
      **you** must name the section.
- [ ] **Precedent**: pull the vendor's last three posted bills and look at `WTAmount`
      / line `WtLiable`. 18 flagged-and-coded Oil vendors have never had TDS
      deducted and 63 only sometimes — the precedent is the house rule, not the flag.
- [ ] **Right book**: the same section is a **different GL number** in Oil, Mart and
      Beverages, and the *same* number means different sections. Never carry a
      `2133xxx` code across books.
- [ ] **Right block**: bills dated on or after 2026-06-01 use the `393(1)` codes
      (`10xx`/`1230`), not `194x`. The old codes stop at 2026-06-25.
- [ ] **Which lines**: tick only the lines whose nature is covered by the section.
      GST is never in the base; SAP excludes it.
- [ ] **Don't wait for a threshold**: a ₹75 base withheld under a ₹10,000-threshold
      code. If the vendor is past the annual limit, small bills withhold too.
- [ ] **Don't inherit**: the GRPO's tick means nothing — 93 % of Mart's copied lines
      have to be flipped on.

## How to check afterwards

**In the client:** Purchasing – A/P → the invoice → *Withholding Tax* window
(header) shows the code, base and amount; the row tick is *WTax Liable* on each line.
For a draft: Document Drafts Report → open the draft → tick *WTax Liable* on every
row **and** confirm the withholding window carries the code → Add.

**From here (read-only):**

```bash
# one document, everything about its TDS
./hana-sql/hana-sql -env connections/hana-office-bridge.env "
SELECT h.\"DocNum\", h.\"DocDate\", h.\"CardCode\",
       ROUND(h.\"DocTotal\",2) \"DOCTOTAL\", ROUND(h.\"WTSum\",2) \"TDS\",
       p.\"WTCode\", p.\"TdsRate\", ROUND(p.\"TdsBAmt\",2) \"BASE\", p.\"TdsAcc\"
FROM \"JIVO_OIL_HANADB\".\"OPCH\" h
LEFT JOIN \"JIVO_OIL_HANADB\".\"PCH5\" p ON p.\"AbsEntry\"=h.\"DocEntry\"
WHERE h.\"DocEntry\"=<n>"
```

Three things to compare, in this order: **`WTSum` non-zero** if the vendor is liable ·
**`PCH5.TdsAcc`** is the account for *this* book · **`DocTotal`** = taxable + GST − TDS.
A draft's equivalent is `ODRF`/`DRF5`/`DRF1` on the same keys.

## Traps

1. **The same GL number is a different section in each book.** Contractor-others 2 %
   is `2133018` Oil, `2133021` Mart, `2133016` Bev. Mart's `2133018` is
   commission @0.2 %. **Identify a TDS account by its name, never its number.**
2. **`2133xxx` balances do not read as "TDS owed".** The challan is paid from
   `2133011 TDS PAYABLE`, which is ₹1.47 Cr in **debit** in Oil while the section
   accounts sit in credit. Only the family net (₹2,91,657 Dr Oil) means anything.
3. **The GRPO's `WtLiable` tick is decorative.** `PDN5` is empty in all three books;
   no GRPO has ever posted TDS.
4. **`JDT1.WTLine`/`WTLiable` are always `N`.** Any report that finds TDS lines by
   those flags finds nothing. Use the account prefix.
5. **Ticking rows without a code produces no TDS** — in the client and through the
   API alike. 67 hand-keyed Oil drafts prove it.
6. **A debit note does not give TDS back** — 4 of 1,595 Oil credit memos reversed any.
7. **Mart's master data has three wrong pairings**: `C19` credits an *input GST*
   account (`2131021`); `94IA` (rent of plant) points at an account named
   *0.20 % 194H*; `94JA` (technical) at *0.05 % 194C*. Oil's `1009` (rent) carries the
   *commission* official section.
8. **Beverages has no `195`, no `1041` and no `1010`** — a foreign-service or
   non-resident payment in the Beverages book has no code to use. Mart has no `1008`.
9. **`1230` is a duplicate of `1023`** in Beverages (identical rate and account) and
   it is the one actually in use (24 bills vs 2). Two codes, one meaning.
10. **`OCRD.WTCode` is not the vendor's TDS code.** It has 9 rows in Oil and none in
    Mart. The list is `CRD4`.
11. **`DocTotal` is already net of TDS.** Adding TDS back to a `DocTotal` sum to get
    "what we bought" double-counts nothing, but treating `DocTotal` as the vendor's
    gross bill understates it by the TDS.

## Open questions

- **Where does Beverages pay its TDS challan?** No `TransType 46` (outgoing payment)
  line has ever touched a Beverages `2133xxx` account — ₹9,85,290 credited all-time
  against ₹2,82,739 of journal debits, leaving ₹7,02,551 outstanding. Either the
  challan is paid from another book or it happens outside SAP. Ask Accounts.
- **Is Oil's `1009` official-section tag a real reporting defect?** The `OffclCode`
  says commission, the account name says rent. Confirming it needs the actual
  withholding-tax report / 26Q output, which is not in these tables.
- **Does the header collection work without the line flag?** Not tested. Both live
  proofs sent `WTLiable: tYES` as well.
- **Does `WithholdingTaxDataCollection` survive `SaveDraftToDocument`** (a human
  pressing Add on a CLI-made draft)? Not observed end-to-end yet — drafts 55177 and
  39790 are still drafts.
- **Are thresholds cumulative-per-vendor as inferred?** Measured: deduction happens
  far below the per-document threshold. The mechanism is not proven from these tables.
- **What are `OPCH.WTApplied` / `PCH5.ApplAmnt`?** Non-zero on 4 Oil rows only
  (₹6 / ₹140 / ₹1,992 / ₹3,839). Probably TDS applied from an A/P down payment —
  but JIVO has no down-payment documents (`ODPO` is empty), so unexplained.
- **Why is Mart's TDS incidence 82 % against Oil's 43 %?** Partly explained (Mart
  buys goods, and 0.1 % `TDS`/`1031` is 2,556 of its 3,877 withholding rows) — but
  Mart also flips the flag on 93 % of GRPO-copied lines, which Oil does not. Worth
  asking whether one of the two books is wrong.

## Related

[[AP-Invoice]] · [[AP-Credit-Memo]] · [[Document-Drafts]] · [[GRPO]] ·
[[Purchase-to-Pay]] · [[Chart-of-Accounts]] · [[Cost-Centres-and-Dimensions]] ·
[[Journal-Entry]] · [[Outgoing-Payment]] · [[GST-on-Purchases]] ·
[[Business-Partner-Master]] · [[Vendor-Master-Data-Gaps]]

## Queries used

```sql
-- the whole TDS code table, with the account it credits, per book
SELECT w."WTCode", w."WTName", w."Rate", w."OffclCode", w."Section", w."Threshold",
       w."EffecDate", w."ApTdsAcc", a."AcctName"
FROM "JIVO_OIL_HANADB"."OWHT" w
LEFT JOIN "JIVO_OIL_HANADB"."OACT" a ON a."AcctCode" = w."ApTdsAcc"
ORDER BY w."EffecDate", w."WTCode";

-- the rate actually in force (child of OWHT)
SELECT "WTCode","EffecDate","Rate","TdsRate","ItrNCRate","PanNCRate","FixedAmnt"
FROM "JIVO_MART_HANADB"."WHT1" ORDER BY "WTCode";

-- which tables hold withholding at all (this is how PCH5/DRF5/RPC5 were found)
SELECT c.TABLE_NAME, m.RECORD_COUNT
FROM SYS.TABLE_COLUMNS c
JOIN SYS.M_TABLES m ON m.SCHEMA_NAME=c.SCHEMA_NAME AND m.TABLE_NAME=c.TABLE_NAME
WHERE c.SCHEMA_NAME='JIVO_MART_HANADB' AND c.COLUMN_NAME='WTCode'
ORDER BY m.RECORD_COUNT DESC;

-- every section used on a real bill, with volume and money
SELECT p."WTCode", p."TdsRate", p."TdsAcc", COUNT(*) "ROWS",
       ROUND(SUM(p."TdsBAmt"),0) "BASE", ROUND(SUM(p."WTAmnt"),0) "TDS",
       MIN(h."DocDate") "FIRST", MAX(h."DocDate") "LAST"
FROM "JIVO_OIL_HANADB"."PCH5" p
JOIN "JIVO_OIL_HANADB"."OPCH" h ON h."DocEntry" = p."AbsEntry"
GROUP BY p."WTCode", p."TdsRate", p."TdsAcc" ORDER BY 4 DESC;

-- TDS incidence, documents and lines, per book
SELECT COUNT(*) "AP_DOCS", SUM(CASE WHEN "WTSum">0 THEN 1 ELSE 0 END) "WITH_TDS",
       ROUND(SUM("WTSum"),0) "TDS_TOTAL"
FROM "JIVO_OIL_HANADB"."OPCH"
WHERE "DocDate" >= ADD_DAYS(CURRENT_DATE,-365) AND "CANCELED"='N';

SELECT COUNT(*) "LINES", SUM(CASE WHEN "WtLiable"='Y' THEN 1 ELSE 0 END) "LIABLE"
FROM "JIVO_OIL_HANADB"."PCH1" WHERE "DocDate" >= ADD_DAYS(CURRENT_DATE,-365);

-- vendor liability, and the flagged-but-uncoded gap
SELECT CASE WHEN b."WTLiable"='Y' THEN 'liable' ELSE 'not liable' END,
       CASE WHEN c."CardCode" IS NULL THEN 'no WT code list' ELSE 'has code(s)' END,
       COUNT(*)
FROM "JIVO_OIL_HANADB"."OCRD" b
LEFT JOIN (SELECT DISTINCT "CardCode" FROM "JIVO_OIL_HANADB"."CRD4") c
       ON c."CardCode" = b."CardCode"
WHERE b."CardType"='S' GROUP BY 1,2;

-- does the master flag predict the deduction? (precedent beats the flag)
SELECT CASE WHEN t."WITHTDS"=0 THEN 'never' WHEN t."WITHTDS"=t."DOCS" THEN 'always'
            ELSE 'sometimes' END, COUNT(*) "VENDORS", SUM(t."DOCS") "BILLS"
FROM (SELECT h."CardCode", COUNT(*) "DOCS",
             SUM(CASE WHEN h."WTSum">0 THEN 1 ELSE 0 END) "WITHTDS"
      FROM "JIVO_OIL_HANADB"."OPCH" h
      JOIN "JIVO_OIL_HANADB"."OCRD" b ON b."CardCode"=h."CardCode"
      WHERE b."WTLiable"='Y'
        AND EXISTS (SELECT 1 FROM "JIVO_OIL_HANADB"."CRD4" c
                    WHERE c."CardCode"=b."CardCode")
        AND h."DocDate" >= ADD_DAYS(CURRENT_DATE,-365) AND h."CANCELED"='N'
      GROUP BY h."CardCode") t
GROUP BY 1;

-- is the flag inherited from the GRPO line?
SELECT g."WtLiable" "GRPO", p."WtLiable" "AP", COUNT(*)
FROM "JIVO_OIL_HANADB"."PCH1" p
JOIN "JIVO_OIL_HANADB"."PDN1" g
  ON g."DocEntry"=p."BaseEntry" AND g."LineNum"=p."BaseLine"
WHERE p."BaseType"=20 AND p."DocDate" >= ADD_DAYS(CURRENT_DATE,-365)
GROUP BY g."WtLiable", p."WtLiable";

-- invoice vs manual JE: every 2133xxx line by posting origin
SELECT h."TransType", COUNT(*) "LINES", COUNT(DISTINCT h."TransId") "JOURNALS",
       ROUND(SUM(l."Debit"),0) "DR", ROUND(SUM(l."Credit"),0) "CR"
FROM "JIVO_OIL_HANADB"."JDT1" l
JOIN "JIVO_OIL_HANADB"."OJDT" h ON h."TransId" = l."TransId"
WHERE l."Account" LIKE '2133%' AND h."RefDate" >= ADD_DAYS(CURRENT_DATE,-365)
GROUP BY h."TransType" ORDER BY 2 DESC;

-- the family balance, and who is in debit
SELECT COUNT(*) "ACCTS", ROUND(SUM("CurrTotal"),0) "FAMILY_NET",
       ROUND(SUM(CASE WHEN "CurrTotal">0 THEN "CurrTotal" ELSE 0 END),0) "DEBIT_SIDE"
FROM "JIVO_OIL_HANADB"."OACT" WHERE "AcctCode" LIKE '2133%';

-- dimensions on a TDS line (answer: none)
SELECT COUNT(*) "TDS_LINES",
       SUM(CASE WHEN l."ProfitCode" IS NULL OR l."ProfitCode"='' THEN 1 ELSE 0 END) "NO_PC"
FROM "JIVO_OIL_HANADB"."JDT1" l
JOIN "JIVO_OIL_HANADB"."OJDT" h ON h."TransId"=l."TransId"
WHERE l."Account" LIKE '2133%' AND h."TransType"=18
  AND h."RefDate" >= ADD_DAYS(CURRENT_DATE,-365);

-- thresholds are not a per-document gate
SELECT p."WTCode", w."Threshold", COUNT(*) "ROWS",
       SUM(CASE WHEN p."TdsBAmt" < w."Threshold" AND p."WTAmnt">0 THEN 1 ELSE 0 END) "BELOW_BUT_DEDUCTED",
       ROUND(MIN(CASE WHEN p."WTAmnt">0 THEN p."TdsBAmt" END),0) "SMALLEST_BASE"
FROM "JIVO_OIL_HANADB"."PCH5" p
JOIN "JIVO_OIL_HANADB"."OWHT" w ON w."WTCode" = p."WTCode"
WHERE w."Threshold" > 0 GROUP BY p."WTCode", w."Threshold";

-- the CLI proof: what SAP built from a WTCode-only payload
SELECT "AbsEntry","WTCode","TdsRate","TaxbleAmnt","TdsBAmt","WTAmnt","TdsAcc"
FROM "JIVO_OIL_HANADB"."DRF5" WHERE "AbsEntry" = 55177;
SELECT "DocEntry","LineNum","WtLiable","LineTotal"
FROM "JIVO_OIL_HANADB"."DRF1" WHERE "DocEntry" = 55177;

-- withholding is nowhere near a payment
SELECT TABLE_NAME, RECORD_COUNT FROM SYS.M_TABLES
WHERE SCHEMA_NAME='JIVO_OIL_HANADB'
  AND TABLE_NAME IN ('VPM6','PDF6','RCT6','INV5','RIN5','RDN5','RDR5','DLN5',
                     'QUT5','POR5','PDN5','RPD5','BTF2','JDT2');
```

Corpus files this note leans on (mined 2026-08-24, `_data/`, gitignored):
`profile-OWHT.md` · `profile-PCH5.md` (written for this note) ·
`profile-DRF5.md` (written for this note) · `profile-PCH1.md` · `profile-OPCH.md` ·
`profile-OCRD.md` · `profile-JDT1.md` · `profile-ORPC.md` · `profile-PDN1.md` ·
`gl-18-OIL/MART/BEV.md` · `gl-30-*.md` · `gl-46-*.md` · `gl-19-*.md` · `gl-20-OIL.md`.
Write-log evidence: `queries/USER36/sap-writes.jsonl`, `queries/manager/sap-writes.jsonl`.
