---
name: jivo-service-contractor-invoice
description: Use when a LABOUR / SERVICE CONTRACTOR's monthly bill arrives and must be entered in SAP B1 as an A/P invoice draft — "labour supply", "casual labour", "packing of Canola/Blowing/Wheat Grass/Jivo Mart", "12 hours labour", "X days @ rate", a contractor's own letterhead or handwritten slip with PAN and no GSTIN, cold-store / space rent, or a month-end tray of many such bills at once. Triggers: "make the draft for this contractor", "contractor entry", "labour bill entry", "yeh contractor ki entry karo". The DESCRIPTION line routes the book — oil/canola/blowing → Oil, wheat grass/water → Beverages, "Jivo Mart" → Mart. NOT for a bill with a GRPO behind it (jivo-ap-draft / jivo-consumables-direct-indirect-expense), NOT for transporter freight (jivo-*-freight-grpo), NOT for fuel or petrol-pump bills (jivo-ap-service-draft), NOT for employee reimbursements (jivo-service-vehicle-expense).
---

# Labour / service contractor bill → A/P invoice draft (JIVO, all three books)

Internal skill. Built from the live batch of **2026-09-08**: 19 bills off five
scans → **16 drafts** (Oil 56568-56577, Mart 40297, Bev 16041-16045),
₹10,69,925 billed / ₹10,15,675 payable after 194C TDS, all attached and
verified. Daman named this its own category that day: "these are contracter
entry … fetch data from SAP of latest last invoice and pick up GL from them
along with budget, variety and effective month, and routed as per unit-wise".

Shared rules (dates, duplicate gate, hard stops, delete) live in
`jivo-ap-draft`. The GL-entry spine and the "book the full billed amount"
rule live in `jivo-loading-unloading-ap` — **read that one first**; this
skill is its generalisation to every contractor on the tray.

## The method Daman named — the vendor's last invoice IS the spec

Four things come off the last posted invoice **of that vendor in that book**,
never from theory and never from another book:

| His word | SAP field | Where it comes from |
|---|---|---|
| **GL** | line `AccountCode` | the vendor's last posted line |
| **variety** | `CostingCode` (Dim1) | the BOOK, not the bill's wording |
| **budget** | `CostingCode3` (Dim3) | the ACCOUNT (see the table below) |
| **effective month** | `CostingCode2` (Dim2) | **the month WORKED, not the bill date** |

`CostingCode2` is the one that catches people. Measured across 2026 on these
vendors: a bill dated **03-08** for July work carries `07-2026`; one dated
**17-08** for 1-16 Aug work carries `08-2026`. It tracks the bill PERIOD.
(This is the opposite of the freight/A-P rule in
[[effective-month-is-the-invoice-date]] — that memo is about a different
document class. For contractor bills, read the period line.)

## Route the book off the DESCRIPTION line (C-0066 generalised)

Every one of these bills is addressed to **JIVO WELLNESS (P) LIMITED**, GSTIN
06AACCJ4223F1Z0 — Oil and Beverages are the same legal entity and share it,
so the letterhead proves nothing. Read the work description:

| Description says | Book | Dim1 |
|---|---|---|
| oil · canola · blowing · oil plant | **Oil** | `CANOLA` |
| wheat grass · water | **Beverages** | `WATER` |
| "Jivo Mart" · packing of Jivo Mart | **Mart** | `CANOLA` |

There is **no BLOWING and no WHEATGRASS dimension** in either chart of
accounts (checked live). Blowing rides Oil's `CANOLA`; wheat grass rides
Bev's `WATER`. Put the real section in `Comments`, not in Dim1.

## The account, and the budget that follows it

| Bill is | `AccountCode` | Dim3 (Oil) | Dim3 (Bev) | Dim3 (Mart) |
|---|---|---|---|---|
| labour supply / packing / days × rate | **5100008** CASUAL LABOUR | `Factory` | `Factory` | `SUPPLY-C` + Dim4 `SC-BHKR` |
| "finish goods loading of …" (no. = amount) | **5670002** UNLOADING/LOADING-INDIRECT | `Del Bkhp` | `Del Bkhp` | `SUPPLY-C` |
| small Oil casual/misc loading | **5100004** UNLOADING/LOADING-DIRECT | `Factory` | — | — |
| cold-store / space rent | **5660003** STORAGE CHARGES INDIRECT | — | `Factory` | — |

`CostingCode5` = `HR` on every line of this class. `LocationCode` = **2**
(Bhakharpur factory). `Dim4` only exists in Mart. `U_Recvd_Qty` stays **0** —
precedent keys no quantity here (unlike fuel bills / C-0025); the day/hour
detail goes in `Comments`.

## TDS — 194C, and it is company-specific

Labour contractors are individuals/HUF (4th PAN char `P`) → **194C 1%**.
The WTCode differs per book for the SAME vendor and must be explicit or it
lands 0:

| Book | WTCode |
|---|---|
| Oil | `1023` |
| Beverages | `1230` |
| Mart | **none** — precedent carries `WTSum 0`, `WTLiable tNO` |

```json
"WithholdingTaxDataCollection": [{"WTCode":"1023","TaxableAmount":87337,"WTAmount":873}]
```
`DocTotal` comes back **billed − TDS**. That is correct.

**Storage/space rent takes no TDS** in this class (Shanti CA Cold precedent:
`WTSum 0`).

**⚠️ The BP card can switch TDS off and SAP will say nothing.** `OCRD.WTLiable`
is per book. NAHIM is `Y` in Oil and **`N` in Bev** — the Bev draft came back
with ₹0 TDS instead of ₹10 and no error. **Check
`OCRD.WTLiable` for every vendor before you send**, and report a card that is
`N` while its class-mates are `Y`; fixing the card is master data and the
operator's call.

## C-0085 is mandatory here too

Run the ₹50 lakh 194Q sweep before building, aggregated on PAN across every
card, and say the number out loud. On 2026-09-08 the top of this tray was
PRABHAKAR SHUKLA at ₹29.63 L (Oil ₹27.01 L + Bev ₹2.62 L, same PAN
MNNPS2203M, same legal entity) — under, so 194C 1% only, no 194Q. Fuel is
goods and is the one that can cross; labour is a service under 194C.

## Never name-match the vendor — use PAN, then the BANK ACCOUNT

The tray had `ANJALI GAURAV CONTRACTOR`, `GAURAV CONTRACTOR`,
`KIRTI (GAURAV) LABOUR CONTRACTOR`, two `ANJALI … IMPREST` employee cards, and
`ANOOP/ASHUTOSH SHUKLA LABOUR CONTRACTOR` alongside `PRABHAKAR SHUKLA`. A
name match picks the wrong one.
- PAN first (`CRD7.TaxId0`), and expect the scan to disagree by a digit —
  SHAHID's bill reads `BTFPA6461R`, SAP holds `BTFPA5461E`.
- **No PAN on the paper → match `OCRD.DflAccount` to the A/C number printed
  on the bill.** That settled ANJALI (`3902500100676301` → VENDA000378, while
  GAURAV CONTRACTOR holds a different account) and KIRTI (`36911628934`).
- **CardCodes differ per book.** PRABHAKAR is `VENDA001564` Oil /
  `VENDA001034` Mart / `VENDA001252` Bev — and `VENDA001034` is
  *BHARTI MACHINERY TOOLS* in Bev. Always resolve per book.

## Handwritten "Total less duty … = ₹X" — book the FULL amount anyway

Six of the ten Oil bills carried a circled recomputation
("Total less duty 12day 8hrs 36min × 500 = 6358.3"). **It is not a deduction
to the draft.** Same rule as the BHORIA "Debit ₹X" cut
(`jivo-loading-unloading-ap`, Daman 2026-09-01): book the billed figure, then
raise an A/P **credit memo based on the posted invoice** via
`jivo-ap-credit-memo`. A credit memo cannot be based on a draft.
List every such cut in the report so the credit memos get raised.

Where the vendor's OWN paper already nets a deduction (ANJALI printed
"LESS TIME 14.5 Hrs 677" and totalled ₹17,243), the **printed total is the
billed amount** — 17,243, not 17,920.

## Series and dates

`Series` = the **HR_B flavour of the DocDate's month** (Bill of Supply —
unregistered labour, no GST). Look it up, never carry last month's:

| | Aug-26 | Sep-26 |
|---|---|---|
| Oil `HR_B` | 3324 | **3325** |
| Mart `HR_B` | 2862 | **2863** |
| Bev `HR_B` | 2678 | **2679** |

Dates: **`DocDate` = the JIVO gate-stamp date** (C-0017), **`TaxDate` = the
bill date**, `DocDueDate` = DocDate. The gate stamp is the blue
"JIVO WELLNESS PVT. LTD. / G.No … / Date …" box — record its number in
`Comments`. **Exception: BHORIA loading bills take all three = the bill date**
(its own precedent, and it carries no gate stamp).
A bill dated the 4th of a month for a period starting then keeps that month's
series even if you key it later — Shanti's 04-08 bill went on Aug 2678.

## Header spec (measured on Oil 50897, Mart draft 40210, Bev 13938)

```json
{"CardCode":"…","NumAtCard":"<bill no exactly as printed>",
 "DocDate":"<gate>","TaxDate":"<bill>","DocDueDate":"<gate>",
 "DocType":"dDocument_Service","DocumentSubType":"bod_None",
 "GSTTransactionType":"gsttrantyp_BillOfSupply",
 "Series":<month HR_B>,"BPL_IDAssignedToInvoice":2,
 "ControlAccount":"2110004","SalesPersonCode":<the BP card's SlpCode>,
 "Comments":"BEING EXPENSE BOOKED AGAINST CASUAL LABOUR, INVOICE NO. <n>, DATED <d>, PERIOD <a> TO <b> | <work> <qty> @ <rate> | GATE ENTRY NO <g> DT <d>",
 "DocumentLines":[{"AccountCode":"5100008","LineTotal":X,"UnitPrice":X,
   "TaxCode":"Exampt","TaxLiable":"tYES","LocationCode":2,
   "CostingCode":"CANOLA","CostingCode2":"08-2026","CostingCode3":"Factory",
   "CostingCode5":"HR","SalesPersonCode":<slp>,"WTLiable":"tYES"}]}
```
`SalesPersonCode` = `OCRD.SlpCode` of that card — it matched every precedent
exactly (Oil 43/29, Mart 51, Bev 3/19/22). Cold-store rent splits into **one
line per effective month, pro-rated by days** (Shanti 04-08→04-09: 28 days
`08-2026` ₹12,194 + 3 days `09-2026` ₹1,306 = ₹13,500).

## Run it

```bash
ACC_ENV=user07.env acc/_playbook/sap draft purchase-invoice --dry-run --data-file <p.json>
ACC_ENV=user07.env acc/_playbook/sap draft purchase-invoice --data-file <p.json> --yes
```
(`user07-mart.env` / `user07-bev.env` for the other books.) Then attach ONE
page per draft — split the tray scan first — per
`jivo-ap-draft/reference/attachments-upload.md`; `-H "Expect:"` is
load-bearing. **`ATC1` carries `U_CHK`/`U_CHK2` in Oil AND Beverages but NOT
in Mart** — stamp `U_CHK2 OK` in Oil/Bev, skip it in Mart or the PATCH fails
on an unknown field.

## Then STOP unless the login is on an Always-terms template

`sapb1 add-draft` refuses (exit 9) for any login SAP's Always-terms A/P
template does not name — verified live 2026-09-08: the only ones are
**Oil 103 / Mart 48 / Bev 68, each naming USER39 (MUQEEM) and USER08 (DIVJOT)** (Divjot added 2026-09-10). USER07
(HARSH) *is* on the condition-based template "USER03 AP" (Oil 40 / Mart 17 /
Bev 1), but **SAP skips condition-based templates for API documents and would
post the invoice LIVE**, past Bhawani. So from USER07 these finish as drafts
and **a person presses Add in Document Drafts** — that route does consult the
condition template, so Bhawani gets them. Say this out loud; do not go
hunting for another route.

## Pre-flight

- [ ] description line read → book chosen; Dim1 from the BOOK not the wording
- [ ] vendor resolved per book by PAN or printed bank A/C, never by name
- [ ] duplicate gate: `NumAtCard` clean in `Drafts` + posted, per CardCode, and the vendor's month swept
- [ ] C-0085 ₹50 L PAN sweep run and the figure stated
- [ ] `OCRD.WTLiable` checked per card; WTCode right for the book (Oil 1023 / Bev 1230 / Mart none)
- [ ] `CostingCode2` = the month WORKED; Dim3 matches the account; Dim4 only in Mart
- [ ] Series = the DocDate month's HR_B; DocDate = gate, TaxDate = bill
- [ ] full billed amount booked; every handwritten cut listed for a post-posting credit memo
- [ ] read-back: `DocTotal` = billed − TDS, one attachment per draft, `U_CHK2 OK` (Oil/Bev)
- [ ] said whether it is submitted or waiting for a human to press Add
