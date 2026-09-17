---
type: playbook
sap_tables: [OPCH, PCH1, PCH4, PCH5, OPDN, PDN1, ODRF, DRF1, OCRD, CRD4, CRD7]
objtype: 18
companies: [OIL, MART, BEV]
mined: 2026-08-27
confidence: high
---

# Transporter / freight bill — the keying sheet

> A transporter's bill is **not** the hard "no-GRPO service bill" it looks like. At JIVO
> it is the **easiest** A/P entry in the building: the factory has already keyed one
> **service GRPO per bilty**, and the bill is a copy of N of them. **98.2 % of transport
> A/P lines come off a GRPO** (1,073 of 1,093, Oil FY26-27). Get the GRPOs right and SAP
> fills everything except two things: **TDS** and the **attachment**.
>
> Sits under [[AP-Invoice-Playbook]]. Everything here is measured against the live books —
> the SQL is in [[transport-ap-evidence]].

## At a glance

| | Oil | Mart | Bev |
|---|---:|---:|---:|
| Bills FY26-27 (1 Apr → 27 Aug) | **198** | 145 | 90 |
| `DocType` | `S` **100 %** | `S` | `S` |
| Lines from a GRPO | **98.2 %** | — | — |
| GRPOs per bill | avg **3.2**, max **26** | | |
| Attachment present | **198 of 198 (100 %)** — 915 attachment rows, 917 files, all but 2 PDF | | |
| Who keys them | SATNAM 59 · NEETU 56 · HARSH 40 · ISHWENDRA 34 · LOVPREET 8 | | |
| Who raises the GRPOs | **GURCHARAN** (551 of 604) | | |
| Open GRPOs waiting for a bill | **138 · ₹21.49 L** | 29 · ₹14.15 L | 70 · ₹4.54 L |

This is a routine, high-volume flow — **433 bills in the first five months of FY26-27**
across the three books — and it has never once been keyed through this CLI. See [[Transport-Bill-Playbook#What we have actually done]].

## 0 · The one thing that decides the whole entry

**Find the GRPOs. The bilty numbers on the bill are the key.**

The factory raises a service GRPO for each bilty and puts the **bilty number in the
GRPO's `NumAtCard`** — filled on 603 of 604 Oil transporter GRPOs. So:

```sql
-- every open GRPO for this transporter, with its bilty number
SELECT "DocEntry","DocNum","DocDate","NumAtCard" AS BILTY,"DocTotal","Comments"
FROM "JIVO_OIL_HANADB"."OPDN"
WHERE "CardCode"='VENDA000636' AND "CANCELED"='N' AND "DocStatus"='O'
ORDER BY "DocDate";
```

Match the bill's bilty list against that. What you get back is the whole document —
accounts, all five dimensions, location, SAC, amounts. Do **not** hand-key a transport
bill because the GRPO was hard to find; find it.

**If there genuinely is no GRPO** (20 of 1,093 Oil lines, 1.8 %), you are in
[[AP-Invoice-Playbook]] territory and keying from scratch — and the values below are
what you are keying *to*.

## 1 · Read the paper

| On the bill | Goes to | Note |
|---|---|---|
| Transporter's bill / invoice no. | `NumAtCard` | **The duplicate key.** 100 % filled on all 198 |
| Bill date | `TaxDate` | |
| Bilty / LR / GR numbers (usually several) | matched to `OPDN.NumAtCard` → the GRPO list | and repeated in `Comments` |
| Destination(s) | Dim5 `OcrCode5` — the **destination state** | 23 distinct in Oil: PB 316 · DL 267 · HR 145 · MH 51 · UP 44 … |
| Freight amount per bilty | one line each | |
| GST charged, or "tax payable by recipient" | decides the tax code — see §4 | **this is the big fork** |

`U_BilltyNumber`, `U_TransporterName`, `U_VehicleNoM` exist on `OPCH` but are filled on
only **9, 9 and 7** of 198 bills. **Nobody uses them for this document** — the bilty
lives in `Comments`. Do not start a new convention. → [[Field-Name-Rosetta]]

## 2 · Header

| Field | Value | Measured |
|---|---|---|
| `DocType` | **`dDocument_Service`** | 198 of 198. **Omit it on an API copy and SAP answers `[SAP -5002] Base document type and target document type do not match`** — that is exactly how draft 39828 failed on 2026-08-25 |
| `CardCode` | look it up **in that book** | see the trap in §6 |
| `NumAtCard` | the transporter's bill number | 100 % |
| `DocDate` | **the bill date, not the gate date** | `DocDate = TaxDate` on **151 of 198 (76 %)**; the lag from the last GRPO to the bill is avg **19.4 days**, max 109, same-day on only 4. **C-0017's gate-date rule does not describe this class** — it is the item-GRPO rule. Consistent with C-0022 |
| `TaxDate` | the bill date | |
| `DocDueDate` | leave to payment terms | |
| `BPLId` | Oil **2 FACTORY** (197 of 198). **Mart splits: 1 DELHI 85 · 2 HARYANA 60** | read it off the GRPO, do not default it in Mart |
| `Series` | see §3 | |
| `CtlAccount` | `2110004` SUNDRY CREDITOR SERVICE | 1 value, automatic |
| `Comments` | `BILTY NO <n>` + SAP's own `Based On Goods Receipt PO <DocNum>. …` | 197 of 198 filled. Spelled `BILTY NO`, `BILLTY NO.`, `BILLTY NO. ` in the wild — pick `BILTY NO` |
| `JrnlMemo` | leave it | SAP writes `A/P Invoices - <CardCode>` |

## 3 · Series — book-local, month-local, flavour-local

Two flavours only: **`_G` GST** (`DocSubType` `GA` / `bod_GSTTaxInvoice`) and **`_B`
bill-of-supply** (`--` / `bod_None`). Aug-26, measured on posted transport bills:

| Book | GST series | Non-GST series |
|---|---|---|
| Oil | **3684** `HR_G0826` | **3324** `HR_B0826` |
| Mart | **2766** `HR_G0826` · **2754** `DL_G0826` | (Jul used 2873 `DL_B0726`) |
| Beverages | **2777** `HR_G0826` | **2678** `HR_B0826` |

Wrong series = `-10`. Wrong sub-type = `-4002`. → [[Numbering-Series]]

**A GTA bill still uses the `_G` GST series** even though the vendor charged no GST —
the tax exists, it is just payable by us. Only genuinely tax-free vendors (ARNAV,
CHOUDHARY) sit on `_B`.

## 4 · Tax — three shapes, and RCM is the normal one

Measured on Oil transport lines, FY26-27 (`PCH4`):

| Shape | Tax code(s) | Lines | Account | What the bill says |
|---|---|---:|---|---|
| **GTA, inter-state** | `RIGST@5` | 412 | `2137109` INPUT IGST @5 % RCM | "GST payable by recipient" / no GST |
| **GTA, intra-state** | `RCGS@2.5` + `RSGS@2.5` | 470 each | `2137102` / `2137101` | same |
| **Forward charge** | `IGST@18` (or `CGST@9`+`SGST@9`) | 204 | `2131004` | the transporter charged 18 % |
| Exempt | `Exampt` | 6 | `2131017` | |

**The arithmetic that catches errors:** on a GTA bill the header `VatSum` is **0** — the
5 % sits on the lines and on `PCH4`, never in what we owe. So

> **`DocTotal` = freight − TDS.** Not freight + GST.

Golden example: BOMBAY SRINAGAR bill `018` — freight ₹58,825, TDS ₹1,177, `DocTotal`
**₹57,648**, header `VatSum` 0, four `RIGST@5` rows totalling ₹2,941 of RCM credit.
The vendor's paper says ₹58,825; SAP will say ₹57,648. That is correct, not a mistake.

On a forward-charge bill (PICK & SHIP) the header `VatSum` **equals** the line GST and
`DocTotal` = freight + 18 % − TDS. → [[GST-Tax-Codes]]

## 5 · TDS — the only number the GRPO cannot give you

> **2026-09-17 (Daman + Divjot) — this rule wins over everything below.** TDS on a
> transport bill is set by `jivo-tds` (`.claude/skills/jivo-tds/bin/tds.py apply`
> before sending, `check` after). **AIR TRANS, BHARGAVE ROAD CARRIER, DELHI PUNJAB
> (both cards) and PICK & SHIP: no TDS** — declaration received. **Every other
> transporter: 2% from the first rupee**, company or not. Do not pick a code by hand.

**This is the whole job.** Everything else copies; this does not. → [[TDS-Withholding]]

**Which code:** it is on the vendor card (`CRD4`), and it follows the **4th character of
the PAN** — `P` (individual) or `H` (HUF) → 1 %, everything else (`C` company, `F` firm,
`A`, `T` …) → 2 %.

| Code | Rate | What | Oil GL | Bev uses |
|---|---:|---|---|---|
| **`1024`** | 2 % | contractor — company / firm | `2133018` | `1024` |
| **`1023`** | 1 % | contractor — individual / HUF | `2133016` | **`1230`** (Bev's duplicate) |
| `C194` / `194C` | 2 % / 1 % | **legacy, closed to new bills after 2026-06-25** | `2133006` / `2133003` | |

**Verified on 25 transporter cards: the PAN rule predicted the card's code 24 times.**
The one miss is `ABC TRANSPORT COMPANY PRIVATE LIMITED`, PAN `ANKPP8181E` — a `P` PAN on
a company name, carrying `1024`. Its master data is wrong one way or the other; do not
copy the pattern.

**Through the CLI you must send it explicitly** — a draft built from GRPO lines comes out
with `WTSum = 0` (C-0018). Our own draft 39829 proves it: field-perfect, TDS zero.

```jsonc
"WithholdingTaxDataCollection": [ { "WTCode": "1024" } ]   // header; SAP computes rate, base, account
```

and every line that is in the base needs `"WTLiable": "tYES"` — 834 of 1,093 Oil lines
carry it, and the operator flips it on **32 lines the GRPO said `N`**.

### The gap this measurement found

**27 Oil transport bills of TDS-liable vendors, ₹14.19 L, carry zero TDS** (1 Apr–4 Aug).
It is **not** a threshold: for PICK & SHIP the average bill *with* TDS is ₹18,112 and
*without* is ₹18,137, and the largest untaxed bill (₹56,297) is 22× the smallest taxed one.
Separately, **ARNAV is `WTLiable = N` in Oil and Beverages but `Y` with code `1023` in
Mart — same PAN `ACBPY4022H`** — and its 22 Mart bills still carry no TDS.
*Measured; whether these are misses or a documented exemption is for Accounts to say.*

## 6 · Dimensions, account, location — copy, then check

| Field | Value | Fill rate (Oil lines) |
|---|---|---:|
| `AcctCode` | **`5670001`** FREIGHT AND CARTAGE OUTWARD-INDIRECT | 1,077 of 1,093 (98.5 %). Others: `5100002` freight inward-direct 8 · `1212013` building WIP 6 · `5680028` 1 · `5500001` import 1 |
| Dim1 `OcrCode` | **the variety** — MUSTARD, OLIVE, CANOLA, SOYABEAN, GROUNDNT … | 100 %, 20 distinct |
| Dim2 `OcrCode2` | **Effective Month `MM-YYYY` — the DISPATCH month, per line, not the bill's month** | 100 %. One July bill carried 05-2026, 06-2026 and 07-2026 lines. → C-0033, C-0035 |
| Dim3 `OcrCode3` | **book-local**: Oil `Del Bkhp` (1,077) · Mart `SUPPLY-C` (530) · Bev `Del Bkhp` (815) | 100 %. **Never `FACT_COM`** — that is the factory-bill code (C-0027) |
| Dim4 `OcrCode4` | **Oil: empty. Mart: always set** — `SC-BHKR` 305 · `SC-WARH` 225 | Oil 0 of 1,093; Mart 530 of 530 |
| Dim5 `OcrCode5` | **destination state** | 1,085 of 1,093 |
| `LocCode` | **2** | 100 % (C-0025) |
| `SacEntry` | Oil **2** (`9967` Freight) · Bev **3** (`996812`) · Mart mostly **-426** | 1,077 of 1,093 |
| `U_Recvd_Qty` | **0 — never used on transport** | 0 of 1,093. C-0025's "put the qty here" is the *fuel*-bill rule, not this one |
| `Quantity` | 0 | service lines have none |

**A service GRPO hands over all five dimensions, not just Dim1.** Verified on our own
CLI draft 39829: every line came back with Dim1, Dim2, Dim3, Dim5, `LocCode` and
`SacEntry` identical to the source GRPO. **C-0035 ("lines inherit only Dim1") is the
item-GRPO behaviour — it does not apply to freight GRPOs.** Still read them back; the
one thing that does drift is the amount (42 of 1,073 lines differ from the GRPO) and
`WtLiable` (40).

### Trap — Mart's SAC is "Freight **insurance**"

Mart's dominant SAC on transport lines is `-426` = `00997136` *Freight insurance services
& Travel insurance services*, 387 lines, ahead of the correct `00996511` road-transport
code (81 lines). Beverages and Oil use freight codes. *Measured. Flagged, not fixed —
GST reporting reads this.*

## 7 · The vendor card — look it up, never assume

**The same transporter has a different `CardCode` in each book — but not always.**

| Transporter | Oil | Mart | Bev | PAN | Code |
|---|---|---|---|---|---|
| ABHIMAN EXPRESS | `VENDA001676` | `VENDA001019` | `VENDA001362` | ACLF**A**8846M | 1024 |
| PICK & SHIP LOGISTICS | `VENDA001661` | `VENDA001018` | `VENDA001346` | AAQ**C**P4145A | 1024 |
| ARNAV TRANSPORT | `VENDA000956` | `VENDA000935` | `VENDA000948` | ACB**P**Y4022H | Oil/Bev **N** · Mart 1023 |
| **DELHI PUNJAB TRANSPORT** | `VENDA000636` | `VENDA000636` | `VENDA000636` | AAN**F**D7642N | 1024 (Mart card carries both) |
| SMARTSHIFT / AIR TRANS / MAHADEV | `VENDA000531` / `000400` / `000269` | same | same | | |
| BOMBAY SRINAGAR | `VENDA000972` | `VENDA000579` | — | AAX**F**B9863D | 1024 |
| MAHAVIR TRANSPORT | `VENDA001523` | `VENDA001010` | `VENDA001214` | AOU**P**J8083N | 1023 / Bev 1230 |

Some codes are shared across books and some are not, so **there is no shortcut — query
it.** `OCRD.LicTradNum` is empty for all of them, so match on name + PAN (`CRD7.TaxId0`),
never on the GSTIN column (C-0014). → [[Business-Partner-Master]]

## 8 · Attach, then submit

- **Every single posted transport bill has an attachment** — 198 of 198, 915 PDFs. A
  transport bill without the scan is not finished. → [[Attachments]], C-0026
- **Then `sapb1 add-draft <DocEntry>` and verify `ODRF.WddStatus = 'W'` — Oil only.** In Mart and
  Beverages `OADM.EnbApprDI = 'N'` (measured 2026-09-02), so an API Add skips every template
  and **posts live**; there the job ends at the attached draft and a person presses Add.
  A draft at
  `'-'` never reaches Bhawani (C-0034) — which is exactly where our only transport draft
  has been sitting since 2026-08-25. → the `jivo-add-and-new` skill

## What we have actually done

| | |
|---|---|
| Posted through this CLI | **none, ever** |
| Drafted through this CLI | **one** — Mart `39829`, ABHIMAN `DEL/260313`, ₹7,37,988, 19 lines off 7 GRPOs, 2026-08-25 by USER39 |
| **Oil `55904`** (DocNum 626084291) | DELHI PUNJAB bill `118` dt 11-08-2026, ₹2,29,188, **24 lines off 15 GRPOs**, series 3684, USER39, 2026-09-02 — attachment row 174251 (bill + 15 bilty files, all `U_CHK2 OK`). **Held unsubmitted** on Daman's "drafts first". TDS 0 per the vendor's 4 posted precedents (card says 1024). ₹2,000 debit (bilty 13091 hold) owed as a credit memo after posting |
| **2026-09-02** | Oil **55899** (DocNum 626084291), DELHI PUNJAB `119` dt 11-08-26, ₹1,83,195, **40 lines off 13 GRPOs**, USER39, attachment row 174246 (bill + 13 bilty PDFs), **submitted via add-draft** — first transport bill ever sent to the approver from here. Same bill row GR 13008 (₹13,783) was **Beverages**: Bev draft **15837** as `manager` (no USER39 Bev login on this Mac), attachment 41619, **HELD unsubmitted** — add-draft as manager would post live (template 68 is USER39-only). TDS left 0 to match every posted bill of this vendor since 08-08 (14 of 20 FY bills before that carried 1024 @2 %; card unchanged since 2024) |
| **2026-09-02** | Oil **55902** (DocNum 626084291 shown while draft), PICK & SHIP `NCR-358` dt 20-08-26, bilty NCR-3864, ₹53,044 gross → **₹51,983** after TDS 1024 @2 % (₹1,061), **4 lines off GRPO 2026086707 (DocEntry 25894)**, USER39, series 3684 `HR_G0826`, DocDate = bill date, attachment row 174247 (scan + the GRPO's 7-page bilty file, both `U_CHK2 OK`), **add-draft → `WddStatus W`, request 73820, template 103, approver USER03** — second transport bill sent to the approver from here, ~14 min of work. Two things to know from it: (1) this vendor's 58 FY bills were all forward-charge `IGST@18`, but NCR-358 carried **no GST** (`Remark: NISHA ROADLINE`, "tax payable by billing party") and GURCHARAN's GRPO was keyed `RIGST@5` — **the GRPO decides the tax shape; the paper agreed**; header `VatSum` 0, still on the `_G` series like BHARGAVE 626084140. (2) TDS was applied from the card (CRD4 `1024`, PAN AAQCP4145A → C → 2 %, single bill > ₹30k) even though USER39's last 9 bills of this vendor since 22-07 carried 0 — 42 of 58 FY bills carry it; flagged to Daman, Bhawani can strike it |
| Its state today | `WddStatus = '-'` — **never submitted, never posted** |
| Its defect | field-perfect on dimensions, **`WTSum = 0`** — the 2 % TDS (≈ ₹15 k on ₹7.53 L) is missing |
| The twin | `39828`, same bill, created by `manager` 11 minutes earlier, since removed |
| First failure | `DocType` omitted → `[SAP -5002] Base document type and target document type do not match` |

**Clear 39829 before the next ABHIMAN bill** — it will trip the duplicate gate.

## Pre-flight — tick before `--yes`

- [ ] every bilty on the paper matched to an open GRPO (`OPDN.NumAtCard`); count agrees
- [ ] `NumAtCard` clean in `Drafts` **and** posted `PurchaseInvoices` for that vendor
- [ ] `DocType: dDocument_Service`
- [ ] right book, right `CardCode` **for that book**, right `BPLId` (Mart: 1 or 2)
- [ ] this month's series, right flavour (`_G` vs `_B`)
- [ ] tax shape read off the paper: RCM (header `VatSum` 0) vs forward charge
- [ ] TDS written by `jivo-tds apply`; `jivo-tds check` passed after sending
- [ ] `DocTotal` = freight − TDS (GTA) reconciles to the bill
- [ ] read back Dim2 per line = the **dispatch** month; Dim3 = the book's code; Dim5 = destination
- [ ] scan attached, `U_CHK2 = OK`
- [ ] **`add-draft`, then `WddStatus = 'W'`**

---

Evidence and SQL: [[transport-ap-evidence]] · Related: [[AP-Invoice]] · [[GRPO]] ·
[[TDS-Withholding]] · [[Chart-of-Accounts]] · [[GST-Tax-Codes]] · [[Numbering-Series]] ·
[[Cost-Centres-and-Dimensions]] · [[Business-Partner-Master]] · [[Purchase-to-Pay]]
