# GST portal ↔ SAP B1 — comparison spec (v0.1, 2026-08-21)

**Purpose.** Define what Accounts will compare between the GST portal (services/return/payment.gst.gov.in) and SAP B1, so the read-only `gst` CLI emits records in the shape a later reconciliation script can diff against a HANA query. This document specifies **what to pull and in what shape**; it does not write the reconciliation.

**Rules inherited.** CLAUDE.md RULE 0: the CLI is read-only — it never calls any portal endpoint whose path contains `save`, `submit`, `file`, `offset`, `reset`, `proceed`, `amend`, `setoff`, `challan/create` or similar; it reads views, downloads and ledgers only. Credentials stay in `portals/gst/.env` (gitignored) and are never written into output files or logs. SAP is queried through `hana-sql` (CLI or MCP `hana_query`), read-only by construction.

**Evidence status.** Every SAP fact below marked **[live]** was pulled from HANA on 2026-08-21 17:18–17:40 IST over the VPS bridge (`connections/sap-home-bridge.sh`, env `hana-office-bridge.env`, user ZIA). Portal facts come from `RECON.md` (live 2026-08-21) or, where marked **[schema]**, from GSTN's published JSON formats and still need confirming in discovery items D4/D5/D7/D8. Inferences are marked **[inferred]** with a confidence.

---

## 1. The GSTIN universe — who maps to what

Portal logins in `.env` (8, all PAN `AACCJ4223F` = JIVO Wellness Pvt Ltd). SAP side: a GSTIN lives on a **branch** (`OBPL.TaxIdNum`) and is stamped on every document in the tax-extension table (`INV12/RIN12/PCH12/RPC12.LocGSTN`). The two agree on 2,704 / 2,704 FY26-27 Oil A/R invoices **[live]**.

| # | GSTIN | State | SAP Oil branch (`OBPL.BPLId`) | SAP Bev branch | A/R invoices FY26-27 Oil / Bev [live] | Status |
|---|---|---|---|---|---|---|
| 1 | `06AACCJ4223F1Z0` | Haryana | 2 FACTORY, 5 HARYANA SALES, 8 HARYANA INFO | yes | 2,633 / 1,714 | main registration |
| 2 | `07AACCJ4223F1ZY` | Delhi | 1 DELHI, 7 DELHI INFO | yes | 28 / 105 | active |
| 3 | `03AACCJ4223F1Z6` | Punjab | 3 PUNJAB | yes | 43 / 1 | active, thin |
| 4 | `02AACCJ4223F1Z8` | Himachal | 4 HIMACHAL PRADESH | yes | 0 / 0 (no A/R invoice ever) | dormant in SAP |
| 5 | `07AACCJ4223F2ZX` | Delhi ISD | 6 DELHI ISD | yes | n/a (ISD files GSTR-6, not 1/3B) | ISD |
| 6 | `08AACCJ4223F1ZW` | Rajasthan | **none** | none | 0 | no SAP counterpart |
| 7 | `09AACCJ4223F1ZU` | Uttar Pradesh | **none** | none | 0 | no SAP counterpart |
| 8 | `27AACCJ4223F2ZV` | Maharashtra | **none** | none | 0 | no SAP counterpart |

Three consequences the CLI and the reconciliation must be built around:

1. **A portal GSTIN = Oil ∪ Beverages books.** `JIVO_BEVERAGES_HANADB` carries the *same* AACCJ4223F GSTINs (Bev HR alone has 1,714 FY26-27 invoices, ₹5.40 Cr gross) **[live]**. Every SAP-side query in this spec is a `UNION ALL` over the Oil and Beverages schemas. Mart (`AAFCJ4102J…`, 7 GSTINs incl. RJ/UP/KT) is a different PAN and is **not** in the portal credential set — out of scope until its logins are added.
2. **GSTINs 6–8 have no SAP side at all.** The CLI still pulls them; the expected SAP figure is zero. Any non-zero liability, ITC, cash-ledger balance or an unfiled (`NF`) return there is a finding in itself (late fee accrues on nil returns too).
3. **Key = GSTIN, never branch name or location code.** Three Oil branches share the Haryana GSTIN; SAP's own GSTR-1 procedures take `LOCATION = OBPL.BPLId`, so a per-branch run under-reports a GSTIN. Always group SAP by `OBPL.TaxIdNum` (or equivalently `*12.LocGSTN`).

---

## 2. SAP-side anchors (verified live, 2026-08-21)

### 2.1 Tables and keys

| Need | SAP source | Notes |
|---|---|---|
| Our GSTIN on a document | `INV12.LocGSTN` / `RIN12` / `PCH12` / `RPC12`; `OBPL.TaxIdNum` via `O*.BPLId` | identical on all 2,704 FY26-27 Oil invoices |
| Buyer GSTIN | `INV12.BpGSTN` (15 chars) — corrections C-0014 | 2,263 B2B / 443 B2C FY26-27 Oil; agrees with bill-to `CRD1.GSTRegnNo` on 2,262 of 2,263 (1 differs) **[live]** — use `INV12.BpGSTN` as truth |
| Vendor GSTIN | `PCH12.BpGSTN` | 1,414 of 1,417 taxed A/P invoices FY26-27 carry one **[live]** (the 36 % blank in the ITC finding was the *address master*, not the document) |
| Invoice number as filed | `OINV.DocNum` (numeric; series encode state+YYMM: `6`=HR, `7`=DL, `3`=PB, `2`=HP, e.g. `624082001`) | SAP's GSTR-1 procs emit `LEFT(DocNum,16)` |
| Invoice date | `OINV.DocDate` (= `TaxDate` on all 2,704 FY26-27 Oil invoices **[live]**) | period = month of `DocDate` |
| Tax by head per line | `INV4` / `RIN4` / `PCH4` / `RPC4`: `staType` **-120 IGST, -110 SGST, -100 CGST, -130 CESS**; `TaxRate`, `TaxSum`, `BaseSum`; `RelateType` 1 = item line, 3 = freight line; `RvsChrgTax` ≠ 0 = reverse charge | FY26-27 Oil: IGST 4,496 lines ₹4.08 Cr, CGST/SGST 1,959 each ₹2.71 Cr **[live]** |
| Rate | CGST `TaxRate`×2, else IGST `TaxRate` | as SAP's own procs do |
| HSN / SAC | `INV1.HsnEntry → OCHP.ChapterID` (dots stripped), `INV1.SacEntry → OSAC.ServCode`; mutually exclusive (C-0013) | quantity is **bottles** (C-0001); UQC = `OITM.SalUnitMsr` |
| Credit-note ↔ original invoice | `ORIN.RevRefNo` / `RevRefDate` | filled on 525 of 529 B2B credit notes FY26-27 Oil; `RIN1.BaseEntry` is the fallback |
| Vendor invoice number | `OPCH.NumAtCard` | filled on 1,417 / 1,417 |
| e-invoice IRN | `@UTL_MDEXTH`: `U_UTL_BaseEntry` = DocEntry, `U_UTL_DocType` `13` invoice / `14` credit note, `U_UTL_IRN` (64 hex), `U_UTL_AckNo`, `U_UTL_IRNGENDT`, `U_UTL_CANDT` | FY26-27 Oil B2B: 2,226 invoices with IRN, **36 without (₹1.01 Cr)** **[live]** — these will be absent from the portal's auto-populated GSTR-1 |
| SAP's own GSTR worksheets | procs `GSTR1_B2B/B2CL/B2CS/CDNR/CDNUR(_B2CS)`, `GSTR2_APINV*/APCDN*`, `GST_HSN_SUMMERY(_BTOB/_BTOC/_CN/_NET)`, `GST_SERIES_SUMMERY` — all `(FROMDATE, TODATE, LOCATION=BPLId)` | read their definitions, do not `CALL` them (hana-sql refuses CALL); they restrict item lines to revenue accounts under `OACT.FatherNum` 4110000–4170000 and **`GSTR1_CDNR` has its BPLId filter commented out** (every state's run returns all states' credit notes) |

### 2.2 GST general-ledger map (Oil; balances as of 2026-08-21 [live])

| Role | Accounts | Balance / behaviour |
|---|---|---|
| Output tax | `2132001–2132021` OUTPUT IGST/CGST/SGST/CESS @ rate | e.g. 2132002 OUTPUT IGST @5 % = −₹23.26 Cr; **accumulates, never cleared** in FY26-27 |
| Input tax | `2131001–2131022` INPUT … @ rate | 2131002 INPUT IGST @5 % = ₹34.70 Cr; **accumulates, never cleared** |
| Input parked | `2131018` GST NOT ON PORTAL (−₹89,086), `2131019` GST INPUT UNCLAIMED A/C (2A) (₹52.10 L, frozen since 30-Sep-2024), `2131020` Inter-branch ITC Clearing |  |
| RCM | `2137001` GST PAYABLE ON RCM, `2137101–2137112` input RCM, `2137501–2137512` output RCM |  |
| "Credit ledger" | `2139101–2139104` IGST/CGST/SGST/CESS CREDIT LEDGER; `2139105–2139113` per-state (HR/PB/DL) all **0.00** | 2139101 ₹1.82 Cr with **zero movement in FY26-27**; 2139102/2139103 **−₹5,14,190.67 each** |
| Payable / cash | `2136001` GST PAYABLE (−₹6.22 Cr), `1111002` GST CASH BALANCE ON PORTAL (**₹4,06,901.26, one migration line on 30-Sep-2024, no movement since**), `1111001` GST REFUNDABLE | cash paid to the portal posts **Dr 2136001 / Cr bank** (FY26-27: ICICI 1104107, Indian Bank CC 2201101) |
| P&L | `5660008` GST EXPENSE/INELIGIBLE CREDIT (₹71.46 L), `5660012` INTEREST ON GST (₹9,846), `5680005` PENALTY CHARGES, `5660006` GSTR-9 RECONCILIATION |  |

Two facts that decide exact-vs-approximate for the ledger comparisons:

- **SAP does not post the monthly GSTR-3B set-off.** Output and input accounts grow month on month and the credit-ledger accounts do not move (FY26-27, [live]). So SAP **balances** cannot be tied to portal ledger balances; only **period movements** (tax on documents) can be tied to GSTR-1/3B, and cash challans to bank entries.
- **Account codes are not aligned across companies.** In Beverages `2139102` is "IGST CREDIT LEDGER - HR" (in Oil it is CGST) and `2131019` is the inter-branch clearing account **[live]**. Any cross-company GL query must select by `AcctName` pattern, never by code.

### 2.3 Period semantics

Portal period = `MMYYYY` of the return (`rolestatus?rtn_prd=072026`). SAP period = calendar month of `DocDate` (`RefDate` for journals). GSTR-1 and 3B are monthly for all 8 registrations (filing snapshot shows monthly GSTR-1 on the 11th, 3B on the 20th/30th). Financial year key = `2026-27` (portal `dropdown` API).

---

## 3. Common record envelope

Every record the CLI emits is one JSON object per line (`.jsonl`), with this envelope. Amounts are INR numbers with two decimals (never strings, never lakh/crore-formatted). Dates are ISO `YYYY-MM-DD`. Nulls are explicit.

```json
{
  "src": "gst-portal",
  "gstin": "06AACCJ4223F1Z0",
  "state_code": "06",
  "period": "072026",
  "fy": "2026-27",
  "form": "GSTR1",
  "section": "B2B",
  "record_kind": "document",
  "pulled_at": "2026-08-21T17:05:12+05:30",
  "filing": { "status": "FIL", "arn": "AA0607260000000", "filed_on": "2026-08-11", "due_on": "2026-08-11" },
  "portal_ref": { "endpoint": "…/returns/auth/api/…", "raw_id": null }
}
```

- `form` ∈ `GSTR1 | GSTR3B | GSTR2B | GSTR2A | LEDGER_CREDIT | LEDGER_CASH | LEDGER_LIABILITY | FILING`
- `record_kind` ∈ `document | summary | ledger_entry | balance | status`
- `filing` is present on return data (from D4 filed-returns list / `rolestatus`), `null` on ledgers.
- Suggested layout: `out/<gstin>/<period>/<form>.<section>.jsonl` plus `out/<gstin>/manifest.json` (what was pulled, when, from which endpoint, filing status at pull time). Raw portal JSON is kept alongside as `…raw.json` so a field-mapping bug can be re-run without a new login.
- Tax amounts always use the same five keys: `taxable_value, igst, cgst, sgst, cess`; invoice gross is `inv_value`.

---

## 4. The six comparisons

### C1 · GSTR-1 registered outward supplies — B2B invoices and CDNR credit/debit notes (document level)

**Question.** Did every B2B invoice and credit note in SAP reach the filed GSTR-1 for that GSTIN and period, with the same buyer GSTIN, taxable value and tax — and is there anything on the portal that SAP does not have?

**Portal artefact.** GSTR-1 tables **4A/4B (B2B)**, **9B (CDNR)**; view/download of the *filed* return (D8). Expected keys **[schema]**: B2B `b2b[].ctin`, `inv[].inum, idt, val, pos, rchrg, inv_typ (R/SEWP/SEWOP/DE), etin, itms[].itm_det{rt, txval, iamt, camt, samt, csamt}`, plus the auto-population flag (`srctyp`/`irn`, `irngendate`) where the view exposes it. CDNR `cdnr[].ctin`, `nt[].ntty (C/D), nt_num, nt_dt, val, pos, rchrg, inv_typ, itms[]`. Amendments arrive under `b2ba`/`cdnra` with `oinum/oidt` (original) — capture them as `amended: true` with `orig_period`.

**Grain.** One record per document per rate line; `totals` rolled up per document.

**SAP counterpart.** `OINV` (+`INV12`, `INV4`, `INV1`) and `ORIN` (+`RIN12`, `RIN4`) for Oil ∪ Bev, `CANCELED='N'`, `DocDate` in period, `LocGSTN = gstin`, `LENGTH(BpGSTN)=15`. Also `@UTL_MDEXTH` for IRN presence.

**Join key.** `(gstin, buyer_gstin, inv_num)` ↔ `(INV12.LocGSTN, INV12.BpGSTN, CAST(OINV.DocNum AS VARCHAR))`. Tiebreak/secondary: `inv_date = OINV.DocDate`. For CDNR: `(gstin, buyer_gstin, note_num)` ↔ `(RIN12.LocGSTN, RIN12.BpGSTN, ORIN.DocNum)`, `note_type` = `C` if `ORIN.DocTotal > 0` else `D`; `orig_inv_num/orig_inv_date` ↔ `ORIN.RevRefNo/RevRefDate` (informational — the portal de-linked CDNR from the original invoice, so the join must not require it).

**Record shape.**
```json
{ "form":"GSTR1","section":"B2B","record_kind":"document",
  "buyer_gstin":"07AAACB1234C1ZP","buyer_name":"…",
  "inv_num":"624072001","inv_date":"2026-07-03","inv_value":118000.00,
  "pos":"07","reverse_charge":false,"inv_type":"R","ecom_gstin":null,
  "irn":"…64 hex…","irn_gen_date":"2026-07-03","auto_populated":true,
  "lines":[{"rate":5.0,"taxable_value":100000.00,"igst":5000.00,"cgst":0.00,"sgst":0.00,"cess":0.00}],
  "totals":{"taxable_value":100000.00,"igst":5000.00,"cgst":0.00,"sgst":0.00,"cess":0.00},
  "amended":false,"orig_period":null }
```
CDNR adds `"note_type":"C","note_num":"…","note_date":"…","note_value":…,"orig_inv_num":"…","orig_inv_date":"…"` and uses `section:"CDNR"`.

**Exactness.** **Exact** — every matched document should tie to the rupee on `taxable_value` and each tax head; allow ±₹1 per document for per-line rounding (portal rounds each rate line to 2 dp; SAP sums `INV4.TaxSum` which is already per line, so the tolerance rarely bites). Classify each SAP document as `MATCHED / AMOUNT_DIFF / MISSING_ON_PORTAL / PORTAL_ONLY`.

**Known legitimate differences.** (a) 36 FY26-27 Oil B2B invoices have no IRN and would be on the portal only if keyed manually; (b) documents filed in a later period (amendments, late additions) — compare cumulative FY, not just the month, before calling a miss; (c) SAP lines on non-revenue accounts (scrap, asset sales outside `FatherNum` 4110000–4170000) are excluded by SAP's own worksheet procs but appear in `INV4` — the CLI emits portal data; the reconciliation must decide which SAP population it tests against, and should test against `INV4` (what tax was actually charged), not the worksheet.

### C2 · GSTR-1 unregistered supplies and HSN summary — B2CS, B2CL, CDNUR, Table 12 (summary level)

**Question.** Does the B2C tax and the HSN-wise summary JIVO filed agree with what SAP invoiced to buyers without a GSTIN?

**Portal artefact.** Table **7 (B2CS)**: `b2cs[].sply_ty (INTRA/INTER), pos, rt, typ (OE/E), etin, txval, iamt, camt, samt, csamt`; Table **5A (B2CL)** per invoice (`b2cl[].pos, inv[].inum, idt, val, itms`); Table **9B (CDNUR)**; Table **12 (HSN)**: `hsn.data[].num, hsn_sc, desc, uqc, qty, val, txval, iamt, camt, samt, csamt` — since May-2025 split into B2B and B2C tabs (SAP has matching `GST_HSN_SUMMERY_BTOB/_BTOC` procs) **[schema]**.

**Grain.** B2CS: one record per `(pos, rate, supply_type, ecom_flag)`; B2CL/CDNUR: per document; HSN: one record per `(hsn_sc, uqc, rate, b2b_or_b2c)`.

**SAP counterpart.** Same tables as C1 with `BpGSTN` blank/short: `INV1`/`INV4` (and `RIN1`/`RIN4` netted for CDNUR) grouped by `INV12.BpStateCod` (place of supply), rate, intra/inter (`IsIGSTAct` or head), and for HSN by `OCHP.ChapterID`/`OSAC.ServCode`, `OITM.SalUnitMsr`, rate, with `SUM(INV1.Quantity)` in bottles.

**Join key.** B2CS `(gstin, period, pos, rate, supply_type)`; HSN `(gstin, period, hsn_sc, uqc, rate, b2b_flag)`.

**Record shape.**
```json
{ "form":"GSTR1","section":"B2CS","record_kind":"summary",
  "pos":"06","supply_type":"INTRA","rate":5.0,"ecom_gstin":null,
  "taxable_value":1234567.00,"igst":0.00,"cgst":30864.18,"sgst":30864.18,"cess":0.00 }

{ "form":"GSTR1","section":"HSN","record_kind":"summary",
  "hsn_sc":"15099010","description":"OLIVE OIL","uqc":"PCS","b2b":true,"rate":5.0,
  "qty":12000.0,"inv_value":1260000.00,"taxable_value":1200000.00,
  "igst":60000.00,"cgst":0.00,"sgst":0.00,"cess":0.00 }
```

**Exactness.** **Approximate.** B2CS should tie within ±₹10 per `(pos, rate)` cell once CDNUR-B2CS netting is applied the same way on both sides; HSN will differ on UQC mapping (SAP `SalUnitMsr` vs GST UQC codes), free-issue lines (`Price = 0` — SAP's proc flags them `FREE`), and rounding of the HSN taxable value across thousands of lines. Report cell-level deltas; treat >₹100 per HSN×rate cell or any missing HSN as a break.

### C3 · GSTR-3B — tax liability declared and ITC claimed vs SAP's monthly tax movements

**Question.** For each GSTIN and month, does the liability JIVO *declared* in 3B equal the output tax SAP charged (and equal its own GSTR-1), and does the ITC it *claimed* equal the input tax SAP booked — head by head?

**Portal artefact.** Filed GSTR-3B (D8) **[schema]**: `sup_details.osup_det / osup_zero / osup_nil_exmp / isup_rev / osup_nongst {txval, iamt, camt, samt, csamt}` (Table 3.1 a–e), `inter_sup` (3.2), `itc_elg.itc_avl[ty ∈ IMPG, IMPS, ISRC, ISD, OTH]`, `itc_rev[ty ∈ RUL, OTH]`, `itc_net`, `itc_inelg[ty ∈ RUL, OTH]` (Table 4), `inward_sup.isup_details` (Table 5), `intr_ltfee.intr_details / ltfee_details` (5.1), and the payment table 6.1 (tax payable, paid through ITC by head, paid in cash, interest, late fee). Also the portal's own **"Tax liabilities & ITC comparison"** page (D7, `return.gst.gov.in/returns/auth/comparison`) which already tabulates GSTR-1 vs 3B liability and 2B vs 3B ITC per period — pull it verbatim as `section:"PORTAL_COMPARISON"`.

**Grain.** One record per `(gstin, period, table_row)` with the five amount keys.

**SAP counterpart.**
- 3.1(a) outward taxable ↔ `Σ INV4.TaxSum by staType` over `OINV` in period **minus** `Σ RIN4` over `ORIN`, Oil ∪ Bev, by `LocGSTN`; taxable = `Σ BaseSum`. Self-check: equals the period credits−debits on `2132xxx` by head (both SAP).
- 3.1(d) inward RCM ↔ `Σ PCH4.RvsChrgTax` / period credits on `2137501–2137512`.
- 4(A)(5) all-other ITC ↔ `Σ PCH4.TaxSum by staType` over `OPCH` in period minus `RPC4` over `ORPC`; 4(A)(1) import IGST ↔ `PCH12.ImpORExp='Y'` lines; 4(A)(3) RCM ITC ↔ `2137101–2137112`; 4(A)(4) ISD ↔ credit distributed from `07AACCJ4223F2ZX` (`2131020`).
- 4(B) reversals ↔ period debits on `5660008` and movements on `2131019`/`2131018`.
- 6.1 paid-in-cash ↔ `2136001` debits against bank in period; interest/late fee ↔ `5660012`, `5680005`.

**Join key.** `(gstin, period, table_row, head)`.

**Record shape.**
```json
{ "form":"GSTR3B","section":"3.1","record_kind":"summary","row":"a_outward_taxable",
  "taxable_value":45678901.00,"igst":1234567.00,"cgst":456789.00,"sgst":456789.00,"cess":0.00 }
{ "form":"GSTR3B","section":"4","record_kind":"summary","row":"A5_all_other_itc",
  "igst":…, "cgst":…, "sgst":…, "cess":… }
{ "form":"GSTR3B","section":"6.1","record_kind":"summary","row":"payment",
  "head":"IGST","tax_payable":…,"paid_itc_igst":…,"paid_itc_cgst":…,"paid_itc_sgst":…,
  "paid_cash":…,"interest_paid":…,"late_fee_paid":… }
```

**Exactness.** 3.1(a) vs SAP output movement: **approximate, should be near-exact** (±₹10 per head) — differences are genuine events (late-filed invoices, amendments, credit notes booked in a different month, non-revenue lines). 4(A) ITC vs SAP input movement: **approximate by design** — 3B ITC is claimed on a 2B basis (supplier-filing month), SAP books on receipt; the delta per month should net to ~0 over a quarter and the running gap is what `2131018`/`2131019` are supposed to hold. 6.1 cash/interest/late fee: **exact** per period against the cash ledger (C6).

### C4 · GSTR-2B — ITC available from suppliers' filings vs SAP purchase invoices

**Question.** Which of JIVO's booked purchase invoices have the supplier actually filed (so the ITC is safe), which have not (the ₹52.10 L unclaimed-2A lesson), and which 2B entries has SAP never booked?

**Portal artefact.** GSTR-2B for the period (generated on the 14th; D8) **[schema]**: `data.docdata.b2b[].ctin, trdnm, supfildt, supprd, inv[].inum, idt, val, pos, rev (Y/N), itcavl (Y/N), rsn, typ, txval, igst, cgst, sgst, cess, diffprcnt`; `b2ba`, `cdnr[].nt[]` (`ntnum, ntdt, typ C/D, …`), `cdnra`, `isd`, `impg`, `impgsez`; and `itcsumm` (ITC available / not-available totals per section). GSTR-2A is the dynamic sibling — pull it only when asked; 2B is the legal basis.

**Grain.** One record per supplier document.

**SAP counterpart.** `OPCH` + `PCH12` + `PCH4` (invoices) and `ORPC` + `RPC12` + `RPC4` (vendor credit notes), Oil ∪ Bev, `CANCELED='N'`, `PCH12.LocGSTN = gstin`. Import lines via `PCH12.ImpExpNo/ImpExpDate` (bill of entry) join `impg`.

**Join key.** `(gstin, supplier_gstin, inv_num_norm)` ↔ `(PCH12.LocGSTN, PCH12.BpGSTN, norm(OPCH.NumAtCard))`, tiebreak `inv_date` vs `OPCH.DocDate` (±7 days) and `inv_value` vs `OPCH.DocTotal`. `norm()` = uppercase, strip whitespace, collapse `/ \ - _` to `/`, strip leading zeros in each numeric segment. The CLI emits both `inv_num` (as filed) and `inv_num_norm`.

**Record shape.**
```json
{ "form":"GSTR2B","section":"B2B","record_kind":"document",
  "supplier_gstin":"24AAACV1234D1ZQ","supplier_name":"VAISHNODEVI OIL SEEDS …",
  "supplier_filing_period":"072026","supplier_filed_on":"2026-08-10",
  "inv_num":"VD/26-27/0412","inv_num_norm":"VD/26-27/412","inv_date":"2026-07-18","inv_value":10500000.00,
  "pos":"06","reverse_charge":false,"doc_type":"R",
  "taxable_value":10000000.00,"igst":500000.00,"cgst":0.00,"sgst":0.00,"cess":0.00,
  "itc_available":true,"itc_unavailable_reason":null,"diff_pct":null,"amended":false }
```

**Exactness.** **Exact per matched document** on the five amounts (±₹1). The match itself is **approximate** because the invoice number is free text on both sides; expect a residue that needs `(supplier_gstin, inv_date, inv_value)` matching. Outcome classes: `MATCHED / AMOUNT_DIFF / IN_2B_NOT_IN_SAP / IN_SAP_NOT_IN_2B (supplier not filed) / ITC_BLOCKED (itcavl=N)`. The `IN_SAP_NOT_IN_2B` list, aged by `OPCH.DocDate`, is the forward-looking control the ITC finding asked for (payment gate).

### C5 · Electronic credit ledger vs SAP's ITC accounts

**Question.** What does the portal say JIVO's unutilised ITC is, per GSTIN and head, and how does it move each month — against a SAP that holds one consolidated, never-settled set of input/output/credit-ledger accounts (and two that are negative)?

**Portal artefact.** Live balance `return.gst.gov.in/returns/auth/api/itcbalance` → `{igstTaxBal, cgstTaxBal, sgstTaxBal, cessTaxBal, blockTotBal, op_tot}` (RECON, HR = ₹4,33,72,582 on 2026-08-21; ignore its `dt` field). Date-range statement (D5): expected per entry `date, ref_no (ARN / DRC-03 / order no), description, txn_type (Dr/Cr), igst, cgst, sgst, cess, balance_after {…}` **[schema — D5]**.

**Grain.** `balance` snapshot per `(gstin, as_of)`; `ledger_entry` per line; plus a per-period roll-up `(gstin, period) → opening, credits, debits_utilisation, debits_reversal, closing` by head.

**SAP counterpart.**
- Credits (ITC availed via 3B) ↔ period debits on `2131001–2131022` + `2137101–2137112` (Oil ∪ Bev, name-matched). *Approximate* (2B-timing, see C3).
- Debits tagged utilisation (ref = GSTR-3B ARN) ↔ **nothing** — SAP posts no set-off (FY26-27: `2139101` zero movement; `2132002`/`2131002` only accumulate **[live]**). Emit them; the reconciliation treats them as the portal's view of what the set-off JE *should* have been.
- Debits tagged reversal (DRC-03, GSTR-9, order) ↔ `5660008` lines (16 in FY25-26, ties to the paisa per the ITC finding) and `2131019` write-offs. **Exact per event** (amount + date ±2 days).
- Balance ↔ no direct SAP mirror. The SAP "expected balance" is a derived figure Accounts must define (migration opening + Σ input − Σ output set off − reversals − refunds, per GSTIN, Oil ∪ Bev). Until the set-off entries are posted in SAP, this is **approximate** and will not tie.

**Join key.** `(gstin, head)` for balances; `(gstin, ref_no)` / `(gstin, date, amount)` for entries.

**Record shape.**
```json
{ "form":"LEDGER_CREDIT","record_kind":"balance","as_of":"2026-08-21",
  "igst":10867113.00,"cgst":13174558.00,"sgst":19262335.00,"cess":71937.00,"blocked":0.00,"total":43372582.27 }
{ "form":"LEDGER_CREDIT","record_kind":"ledger_entry","entry_date":"2026-07-20","ref_no":"AA060726…","ref_type":"GSTR3B",
  "description":"Credit utilised for GSTR-3B 062026","txn_type":"DR","entry_class":"UTILISATION",
  "igst":1234567.00,"cgst":0.00,"sgst":0.00,"cess":0.00,
  "balance_after":{"igst":…,"cgst":…,"sgst":…,"cess":…} }
```
`entry_class` ∈ `AVAILED | UTILISATION | REVERSAL | REFUND | TRANSITION | OTHER`, derived from `ref_type`/description by the CLI with the raw text kept.

**Exactness.** Balance: **approximate** (structural — SAP does not keep a per-GSTIN credit ledger; the portal is the truth). Reversal entries: **exact**. Standing checks the record shape must support: a portal credit-ledger head can never be negative, so `2139102/2139103 = −₹5,14,190.67` in SAP is a books error to locate (the ITC finding's ₹42,976 + ₹9,010 double-booking candidate, TransIds 181706/7 vs 200235/6).

### C6 · Electronic cash ledger, late fee / interest, and filing status

**Question.** What has JIVO actually paid into the portal (challans), what sits unused under which head, and how much of it is late fee, interest and penalty — against bank payments and the penalty accounts in SAP?

**Portal artefact.** Live balance `payment.gst.gov.in/payment/auth/api/cashbalance` → per head `{tx, intr, pen, fee, oth, tot}` + `tot_rng_bal` (RECON, HR = ₹44,201, almost all under `pen`); detailed statement (D5): per entry `date, ref (CPIN/CIN for deposits, ARN/DRC for debits), description, deposit/debit by head × minor head, balance` **[schema — D5]**. Filing status from `filingsnapshot` / `rolestatus?rtn_prd=` (`return_ty, status FIL/NF, due_dt, filingDate`) and the filed-returns list (D4, gives ARN + filing date per form per period). Electronic **liability** ledger (`…/ledger/taxledger`, D5) per period: liability by head, paid via ITC, paid via cash, interest, late fee.

**Grain.** `balance` per `(gstin, as_of, head, minor_head)`; `ledger_entry` per challan/debit; `status` per `(gstin, period, form)`.

**SAP counterpart.**
- Deposits (CIN) ↔ `Dr 2136001 GST PAYABLE / Cr bank` (FY26-27 Oil: ICICI `1104107`, Indian Bank CC `2201101`) — **exact per challan** on amount and date (±2 banking days); CIN/CPIN is not in SAP, match on `(amount, date, gstin)`.
- Late fee / interest / penalty debits (minor heads `fee`, `intr`, `pen`) ↔ `5660012 INTEREST ON GST`, `5680005 PENALTY CHARGES` (GST subset; the FY25-26 ₹1,39,821 on the Delhi GSTIN), Mart `5660012` "GSTR9/9C PENALTY" — **exact per event**; a portal debit with no SAP line is an unbooked cost, and the split by period answers the statutory-penalties finding's open question (routine late filing vs the FY2020-24 audit settlement).
- Balance ↔ `1111002 GST CASH BALANCE ON PORTAL` = ₹4,06,901.26 **frozen since 30-Sep-2024** **[live]**. There is no live SAP mirror; the spec's position is that the portal balance is the truth and the delta is, by itself, the reconciliation item (it should be re-stated in SAP).
- Filing status ↔ no SAP counterpart; used to compute `days_late` and expected late fee (₹50/day, ₹20/day for nil) and to flag `NF` on any of the 8 registrations — especially RJ/UP/MH where nobody is watching.

**Join key.** `(gstin, cin)` / `(gstin, date, amount)` for deposits; `(gstin, period, form)` for status; `(gstin, period, minor_head)` for fee/interest.

**Record shape.**
```json
{ "form":"LEDGER_CASH","record_kind":"balance","as_of":"2026-08-21",
  "heads":{"igst":{"tax":0,"interest":1,"penalty":0,"fee":0,"other":0,"total":1},
           "cgst":{"tax":0,"interest":3,"penalty":21791,"fee":600,"other":0,"total":43022},
           "sgst":{"tax":0,"interest":3,"penalty":21791,"fee":600,"other":0,"total":43022},
           "cess":{"tax":0,"interest":0,"penalty":0,"fee":0,"other":0,"total":0}},
  "total":44201.00 }
{ "form":"LEDGER_CASH","record_kind":"ledger_entry","entry_date":"2026-01-31","ref_no":"CIN 26…","ref_type":"CHALLAN",
  "txn_type":"CR","entry_class":"DEPOSIT","bank_mode":"NEFT",
  "heads":{"cgst":{"penalty":69910.50},"sgst":{"penalty":69910.50}},"amount":139821.00,
  "balance_after":{…} }
{ "form":"FILING","record_kind":"status","return_type":"GSTR3B","status":"FIL","due_on":"2026-08-20",
  "filed_on":"2026-08-20","arn":"AB06…","days_late":0,"nil_return":false }
{ "form":"LEDGER_LIABILITY","record_kind":"summary","return_type":"GSTR3B",
  "liability":{"igst":…,"cgst":…,"sgst":…,"cess":…},"paid_itc":{…},"paid_cash":{…},
  "interest":{…},"late_fee":{"cgst":…,"sgst":…} }
```

**Exactness.** Challans, late fee, interest: **exact**. Cash balance: **exact on the portal side, no SAP side** (report, do not reconcile). Filing status: exact (dates).

---

## 5. Exact vs approximate — summary

| # | Comparison | Grain | Join key | Ties to the rupee? | Tolerance | Why not exact |
|---|---|---|---|---|---|---|
| C1 | GSTR-1 B2B + CDNR vs OINV/ORIN | document × rate | gstin + buyer_gstin + inv_num | **Exact** | ±₹1/doc | — |
| C2 | GSTR-1 B2CS/B2CL/CDNUR + HSN vs INV1/INV4 | pos×rate / hsn×uqc×rate | gstin + period + cell | Approximate | ±₹10/cell B2CS; ±₹100/cell HSN | UQC mapping, free goods, rounding, CDNUR netting |
| C3 | GSTR-3B 3.1 / 4 / 6.1 vs SAP tax movements | gstin × period × row × head | gstin + period + row | 3.1(a) near-exact; 4(A) approximate; 6.1 exact | ±₹10/head | 2B-timing of ITC, amendments, self-declared summary |
| C4 | GSTR-2B vs OPCH/ORPC | document | gstin + supplier_gstin + inv_num_norm | Exact once matched | ±₹1/doc | free-text invoice numbers; supplier filing lag |
| C5 | Credit ledger vs 2131xxx/2139xxx/5660008 | balance; entry | gstin + head; gstin + ref_no | Reversals exact; balance approximate | event ±₹1; balance n/a | SAP posts no set-off, one consolidated ledger, negative CGST/SGST |
| C6 | Cash ledger, late fee, filing status vs 2136001/bank/5660012/5680005 | entry; status | gstin + (date, amount); gstin + period + form | **Exact** | ±₹1, ±2 days | 1111002 frozen — balance has no SAP side |

---

## 6. What Phase-2 discovery must confirm for this spec

| Item | Needed by | What to capture |
|---|---|---|
| **D8** GSTR-1 / 3B / 2B view + download JSON | C1–C4 | actual key names vs the `[schema]` names above; whether the B2B view carries `irn`/`srctyp`; amendment tables; the async generate-then-download flow |
| **D7** comparison page API | C3 | the portal's own GSTR-1 vs 3B and 2B vs 3B tables per period — cheapest cross-check, emit verbatim |
| **D5** ledger statements (cash / credit / liability) | C5, C6 | field names for `ref_no`, minor heads, `balance_after`; max date range per call; whether debits carry the 3B ARN |
| **D4** filed-returns search | envelope `filing`, C6 | ARN + filing date per form per period, frequency handling |
| ISD (`07…2ZX`) | scope | GSTR-6 / 6A shape if Accounts wants ISD distribution checked against `2131020` |
| RJ / UP / MH | C6 | confirm nil-filer status and zero ledgers; if non-zero, flag before building anything else for them |

Also confirm with Accounts (not discoverable from data): which SAP population the filed GSTR-1 was prepared from (IRP auto-population + SAP worksheets is the likely pipeline — **[inferred, ~70 %]**), and whether they want the monthly set-off JE posted in SAP going forward (without it, C5 stays approximate forever).

---

## 7. Live evidence log (HANA, 2026-08-21, read-only)

All via `hana-sql -env connections/hana-office-bridge.env`, user ZIA, after `connections/sap-home-bridge.sh`.

- GST GL chart: `SELECT "AcctCode","AcctName","CurrTotal" FROM "JIVO_OIL_HANADB"."OACT" WHERE "AcctCode" LIKE '213%' OR UPPER("AcctName") LIKE '%GST%' OR "AcctCode" IN ('5660008','5660012','5680005')` — 2131xxx input, 2132xxx output, 2137xxx RCM, 2139101–2139113 credit ledgers, 2136001 payable, 1111002 cash on portal.
- Locations/branches: `SELECT "Code","Location","State","GSTRegnNo","GSTType" FROM OLCT` (Oil 5, Bev 5, Mart 7); `SELECT "BPLId","BPLName","TaxIdNum","State" FROM OBPL` (Oil 8 branches, 5 GSTINs).
- GSTIN per company: `OINV ⋈ INV12` grouped by `LocGSTN`, FY26-27 and all-time, Oil/Mart/Bev — Bev shares AACCJ4223F; no 08/09/27 ever.
- Key agreement: `INV12.LocGSTN = OBPL.TaxIdNum` on 2,704/2,704; `TaxDate = DocDate` on 2,704/2,704; `INV12.BpGSTN = CRD1.GSTRegnNo (bill-to)` on 2,262/2,263 B2B.
- Tax heads: `INV4."staType"` ∈ {-120, -110, -100} FY26-27 (`OSTT` names sys_IGST/sys_SGST/sys_CGST); -130 CESS per procedure text.
- Procedures: `SYS.PROCEDURES` / `SYS.PROCEDURE_PARAMETERS` for `GSTR1_*`, `GSTR2_*`, `GST_HSN_SUMMERY*` (all `(FROMDATE, TODATE, LOCATION INT)`); definitions read for `GSTR1_B2B`, `GSTR1_B2CS`, `GSTR1_CDNR`, `GSTR2_APINVP`, `GST_HSN_SUMMERY`.
- No set-off posted: monthly DR/CR on `2132002`, `2131002`, `2139101`, `2136001` for Apr–Aug 2026 (`2139101` absent; `2136001` only 6 bank-side entries ₹4.38 L / ₹4.83 L).
- `1111002` history: single line 2024-09-30 ₹4,06,901.
- IRN coverage: `@UTL_MDEXTH` (`U_UTL_DocType` 13/14, `U_UTL_BaseEntry`) vs FY26-27 Oil B2B invoices: 2,226 with IRN, 36 without (₹1,01,49,568).
- A/P side: `OPCH.NumAtCard` filled 1,417/1,417; `PCH12.BpGSTN` 15-char on 1,414/1,417 taxed invoices FY26-27.
- Credit notes: `ORIN ⋈ RIN12` FY26-27 Oil — B2B 529 (525 with `RevRefNo`), B2C 107.

Portal figures quoted (HR credit ₹4,33,72,582; cash ₹44,201; filings Mar–Jul 2026) are from `RECON.md`, captured live 2026-08-21 ~17:05 IST.