# What Accounts actually keys into SAP — the demand inventory

**Pulled live 2026-08-23** from HANA (all three books), window **2026-05-25 → 2026-08-23**
(90 days ≈ 77 working days). Counts are header rows by `CreateDate`, attributed to
`UserSign`. Re-run: `python3 acc/_playbook/inventory.py && python3 acc/_playbook/inventory-deep.py`
(needs the bridge: `bash connections/sap-home-bridge.sh`). Raw per-user table: `_playbook/inventory_90d.csv`.

Confidence: **high** on counts and users (straight from the tables). **Medium** on the
"who is Accounts" grouping — it is inferred from what each login creates, not from an org chart.

## 1. The Accounts desk — entries a person keys, ranked by volume

| # | Entry type | SAP table | 90-day count (Oil / Mart / Bev) | Per working day | Who keys it | Where the input comes from |
|---|---|---|---|---|---|---|
| 1 | **Incoming payment** (customer receipt) | ORCT | **3,611** (1,176 / 1,508 / 927) | ~47 | Preshit 1,276 · Shoaib 555 · Gurpreet-Mayapuri 472 · Avtar 413 · Taran 383 | bank statement / cash; 3,086 customer, 500 GL-account, **657 are cash** |
| 2 | **A/P invoice** (vendor bill) | OPCH | **2,995** (1,839 / 770 / 386) | ~39 | Neetu 807 · Satnam 584 · Harsh 428 · Ishwendra 394 · Param-Billing 378 · Lovepreet 249 · Audit 98 | split below — half from a GRPO, half from paper |
| 3 | **Outgoing payment** (vendor payment) | OVPM | **2,358** (1,742 / 421 / 195) | ~31 | **Taran 1,492** · Avtar 440 · Audit 406 | 1,644 to vendors, 704 straight to GL, 10 to customers; 99.6 % bank transfer |
| 4 | **Manual journal entry** | OJDT `TransType=30` | **897** (573 / 322 / 179 — from 26,956 JEs; the rest are auto) | ~12 | Ishwendra 247 · Avtar 178 · Navdeep 146 · Dolly 121 · manager 64 · Deepanshu 61 · Kamaljeet/HR 46 | memos: intercompany "OIL TO BEVERAGE", TDS, provisions + reversals, salary, incentives, customer↔vendor balance transfers, cheque dishonour |
| 5 | **A/R credit memo** (sales return / rate diff) | ORIN | **744** (297 / 372 / 75) | ~10 | Preshit 307 · Shoaib 193 · Gurleen 123 | returns, e-com claims |
| 6 | **Journal voucher** (parked JE) | OBTF | **527** (320 / 105 / 102) | ~7 | Dolly 115 · Navdeep 78 · Preshit 50 · Kamaljeet 47 · Taran 39 | same inputs as #4, held for review |
| 7 | **A/P credit memo** (debit note to vendor) | ORPC | **300** (209 / 70 / 21) | ~4 | Lovepreet 102 · Ishwendra 49 · Neetu 47 · Satnam 46 | short supply, rate difference, returns |
| 8 | **Payment draft** | OPDF | **172** (159 / 0 / 13) | ~2 | Avtar 105 · Taran 67 | `sapb1 draft payment` now covers this (uncommitted) |
| 9 | **Landed cost** (import) | OIPF | **66** (Oil only) | ~1 | Lovepreet 65 | BoE + freight + duty |
| 10 | **Inventory revaluation** | OMRV | 23 | — | manager 18 | month-end |

### A/P invoices — the split that decides how to automate them

| Kind | How it is built | 90-day count (Oil / Mart / Bev) | Share | Paper needed? |
|---|---|---|---|---|
| **Item bill on a GRPO** | copy-to-target from the factory's goods receipt | **1,336** (901 / 330 / 105) | 45 % | **No** — GRPO carries vendor, items, qty, rate, branch, warehouse, and the scanned bill (`AtcEntry`) |
| **Service bill on a service GRPO** (freight etc.) | copy-to-target from a service GRPO | **260** (148 / 29 / 83) | 9 % | **No** — same as above; 231 of these are TRANSPORTER |
| **Standalone service bill** (expenses, commission, ads, rent, professional fees, staff imprest) | keyed from the paper, GL chosen by hand | **1,327** (772 / 364 / 191) | 44 % | **Yes** — vendor, amount, GST split, GL all come off the bill |
| Standalone item bill | rare | 72 | 2 % | yes |

Standalone service bills by vendor group: SERVICE 483 · STAFF VENDOR 357 (expense claims) · E-COMMERCE 237 (platform fees) · TRANSPORTER 109 · PURCHASE OIL 46 · BRANCH VENDOR 27 · IT 23 · FUEL 19.
Top GLs hit: freight & cartage (438), market commission (160), advertisement (147), conveyance (102), loading/unloading (110), refreshment (76), fuel (50), legal & professional (46).

**Transporter bills** (the ones asked about): 340 in 90 days (≈4.4/day), ₹1.75 Cr. 231 arrive as a
service GRPO, 109 are keyed standalone. Top carriers: Pick & Ship 144 · Arnav 51 · Abhiman 31 ·
Delhi Punjab 29 · Mahavir 20 · Bombay Srinagar 19. Keyed by Satnam 119, Neetu 76, Ishwendra 62, Audit 27, Harsh 33.

### Payments — the part nobody sees

- **1,400 of 2,358 outgoing payments (59 %) are on-account** — no invoice linked at payment time.
  617 settle exactly one invoice, 303 settle 2–5, 38 settle 6+.
- They get matched later: **6,409 internal reconciliations** (OITR) in 90 days, no `UserSign` (done in the client's reconciliation screen).
- So "pay the vendor" and "which bills did that pay" are two separate keying jobs today.

### Every document goes through approval

**12,566 approval requests** (OWDD) in 90 days — A/R invoices 3,849, inventory transfers 2,891,
**A/P invoices 2,857**, GRPOs 970, POs 555, A/P credit memos 368, A/R credit memos 349, returns 326,
outgoing payments 171. An A/P bill's real path is **draft → approval → Add**, and 2,778 A/P drafts
(ODRF type 18) were created in the window — practically one per invoice. Automation must produce
*drafts*, which is exactly what the approval flow expects.

## 2. Adjacent desks (not Accounts, but they create the documents Accounts later bills or pays)

| Entry type | Table | 90-day count | Who | Desk |
|---|---|---|---|---|
| A/R invoice | OINV | 6,384 (1,886 / 3,181 / 1,317) — 95 % from an order or delivery | Gurleen 1,440 · Karanpreet 1,138 · Harpreet 967 · Jaspal 618 · Param 553 · Sumit 425 | billing |
| GRPO (goods receipt) | OPDN | 3,144 | Gurcharan 1,301 (factory gate) · B1i 491 (integration) · Vishal 405 | factory / purchase |
| Sales order | ORDR | 3,495 | Karanpreet 825 · Jaspal 738 · Mansi 674 · manager 608 | sales |
| Inventory transfer (+ request) | OWTR / OWTQ | 2,674 / 305 | Gautam 898 · Shahrukh 582 | warehouse |
| Production order + issue + receipt | OWOR / OIGE / OIGN | ~1,680 each | Gautam 976 | factory |
| Sales quotation | OQUT | 1,405 | B1i 1,403 | OMS feed |
| Purchase order | OPOR | 917 | Vishal 305 · Ravinder 185 · Jaspal 185 | purchase |
| Delivery / return / goods return | ODLN / ORDN / ORPD | 620 / 370 / 42 | Gurpreet-Mayapuri, Pankaj, Deepanshu | Mart warehouse |
| Business partners / items | OCRD / OITM | 275 / 171 | Jayeesh 215 / B1i 77 | master data |

## 3. The pile waiting right now — open (unbilled) GRPOs

| Book | Open GRPOs | of which with the bill attached | TRANSPORTER (service) | PURCHASE items | Oldest |
|---|---|---|---|---|---|
| Oil | **332** | 331 | 90 | 91 (+6 PURCHASE OIL) | Oct-2024 |
| Mart | **43** | 42 | 28 | 15 | Sep-2025 |
| Beverages | **234** | 233 | 111 | 21 | Oct-2024 |
| **All** | **609** | 607 | **229** | | |

Age: 72 ≤ 7 days · 324 at 8–30 days · 142 at 31–90 days · 71 older than 90 days.

**Correction from the first live batch scan (2026-08-24):** over half of these already have an
open A/P **draft** keyed by Accounts (Oil 168/332, Bev 160/234 — drafts sit in ODRF, not OPCH, so
the GRPO stays "open" until the draft is Added). The genuinely un-keyed pile is **75 rows**
(Oil 60 · Mart 0 · Bev 15), plus 175 service GRPOs held pending the service-payload proof.
The batch tool's duplicate check is what surfaced this; a naive count of open GRPOs overstates
the backlog ~8x.
Caveat (C-0019): `DocStatus='O'` here means "not yet copied to an A/P invoice", which is reliable for
GRPOs — but the >90-day tail is probably dead paper, not backlog. Confidence on 609 as the *live* pile: ~85 %.

## 4. What this says about automation (reading, not a plan)

1. **Half of all A/P needs no paper.** 1,596 of 2,995 bills are copies of a GRPO that already holds
   every field *and* the scanned bill. A batch that walks open GRPOs, runs the `jivo-ap-draft`
   pre-check on each, and drafts them all is the 50-at-a-time case — and 609 are waiting.
2. **The other half needs the bill read** (vendor, GSTIN, amount, GST split, GL from vendor precedent).
   Different problem: OCR/vision + precedent lookup, lower confidence, review table is mandatory.
3. **Payments are the biggest volume** (~6,000 in 90 days) and 59 % of outgoing ones are booked
   on-account then reconciled by hand — a bank-statement-to-payment-with-allocation batch would
   remove two keying jobs, not one. Needs statement access; not in SAP.
4. **Manual JEs and vouchers are recurring shapes** (intercompany, provisions + reversals, TDS,
   salary) — templates, not OCR.
5. **Nothing posts without a human**: every type above runs draft → approval → Add. Batch output
   must be drafts with the attachment pointer set, or the approvers will reject them.
