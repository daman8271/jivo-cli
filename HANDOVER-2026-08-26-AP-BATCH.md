# Handover — 22-scan A/P batch, Oil, 2026-08-26

**For Satnam.** Read this first, then
`.claude/skills/jivo-ap-draft/reference/matching-and-batches.md`.

## What is already done — do NOT redo any of it

**20 A/P invoice drafts, ₹51,05,435, all with BHAWANI (USER03) awaiting approval.**
All Oil, branch 2 FACTORY, series 3684, login USER39, every one drawn from its
GRPO, every one with the bill attached (2 files: the scan + the GRPO's own copy),
every line carrying Effective Month `08-2026`.

| Draft | Vendor | Vendor ref | DocTotal ₹ | TDS ₹ | Request |
|---|---|---|---|---|---|
| 55327 | BR Agrotech | 2633100542 | 3,61,250 | — | 73113 |
| 55328 | Echo Plast India | 499/26-27 | 1,29,864 | 110 | 73114 |
| 55311 | BR Agrotech | 2633100573 | 3,50,059 | — | 73098 |
| 55312 | BR Agrotech | 2633100569 | 4,88,350 | — | 73099 |
| 55329 | TPAC Packaging II | 2606000921 | 2,53,110 | **see below** | 73115 |
| 55313 | TPAC Packaging II | 2606000894 | 1,50,960 | **see below** | 73100 |
| 55314 | TPAC Packaging II | 2606000893 | 1,44,503 | **see below** | 73101 |
| 55315 | Kuber Paper & Pack | KPP/2026-27/1832 | 2,75,875 | — | 73102 |
| 55316 | Babaji Udyog | 3231/2026-27 | 1,89,036 | — | 73103 |
| 55317 | Raj Technopack | SNP-0712/26-27 | 2,01,211 | 171 | 73104 |
| 55318 | Raj Technopack | SNP-0720/26-27 | 2,01,211 | 171 | 73105 |
| 55319 | Pioneer Pet | PP/R/26-27/1183 | 9,35,236 | — | 73106 |
| 55320 | Royal Prime Labels | RPL/1216/2026-27 | 33,453 | — | 73096 |
| 55321 | Echo Plast India | 506/26-27 | 2,34,524 | 199 | 73107 |
| 55322 | Raj Technopack | SNP-0703/26-27 | 2,41,453 | 205 | 73108 |
| 55323 | BR Agrotech | 2633100557 | 3,77,714 | — | 73109 |
| 55324 | TPAC Packaging II | 2606000855 | 68,570 | **see below** | 73110 |
| 55325 | Raj Technopack | SNP-0697/26-27 | 2,01,211 | 171 | 73111 |
| 55326 | Multilayer Industries | 919 | 84,482 | — | 73112 |
| 55302 | SSY Containers | 26-27/1489 | 1,83,363 | 175 | 73097 |

Nothing is in the ledger. Approval does **not** post them — a person presses Add
a second time after Bhawani approves.

## The one job left: TDS on the four TPAC drafts

**Daman's call — Satnam does this.**

TPAC has **two Oil cards on one PAN `AAGCT4816J`**:
`VENDA000937` (Uttarakhand, ₹28,73,033 FY26-27) + `VENDA000939` (Haridwar II,
₹37,26,273). Each is under ₹50 lakh; **together ₹65,99,306, over the 194Q
threshold since 2026-07-13**. 194Q counts the *seller* = the PAN, so TPAC IS
liable this year and these four need TDS:

| Draft | Vendor ref | Taxable ₹ | TDS @0.1% ₹ | DocTotal becomes ₹ |
|---|---|---|---|---|
| 55313 | 2606000894 | 1,27,932 | 128 | 1,50,832 |
| 55314 | 2606000893 | 1,22,460 | 122 | 1,44,381 |
| 55324 | 2606000855 | 58,110 | 58 | 68,512 |
| 55329 | 2606000921 | 2,14,500 | 215 | 2,52,895 |

Set the code only and let SAP compute (a draft in approval can still be patched —
the request, attachment and base links all survive; proven on 7 drafts):

```bash
cd sap-b1/cli && set -a && . user39-oil.env && set +a
./sapb1 patch "Drafts(55313)" --data '{"WithholdingTaxDataCollection":[{"WTCode":"1031"}]}' --dry-run
./sapb1 patch "Drafts(55313)" --data '{"WithholdingTaxDataCollection":[{"WTCode":"1031"}]}' --yes
# repeat for 55314, 55324, 55329, then verify:
```
```sql
SELECT "DocEntry","NumAtCard","DocTotal","WTSum","WddStatus"
FROM "JIVO_OIL_HANADB"."ODRF" WHERE "DocEntry" IN (55313,55314,55324,55329);
```

**Royal Prime (55320) stays at nil** — single card, ₹41,04,807 FYTD, under the
threshold.

## Four things for Accounts to look at

1. **BR Agrotech invoice `2633100542` was received into SAP twice** — GRPO
   2026086622 (`NumAtCard '.2633100542'`, 17-Aug) and 2026086714 (clean ref,
   22-Aug), both open, both ₹3,61,250, both gate 148, same UserSign. ₹3.61 lakh of
   phantom stock. Draft 55327 uses **2026086714** (its `PM0000195` "52 GMS GREEN"
   matches the paper). **2026086622 must be cancelled in the client** — no CLI can.
2. **TDS under-deducted on PAN `AAGCT4816J` (TPAC) by about ₹1,180** on already-posted
   invoices: ₹1,599 due on the ₹15,99,306 excess, ₹419 actually taken.
3. **One posted invoice looks over-deducted**: DocEntry 48981, Royal Prime
   `RPL/1051/2026-27`, ₹67 TDS taken on 31-Jul-26 while that PAN sat at ₹36,57,574
   — under the threshold. (The two TPAC ones I first flagged, 43996 and 46047, are
   **correct** — they are FY25-26 bills posted late, and TPAC did ₹1.09 Cr that year.)
4. **Two vendors are about to cross ₹50 lakh**: Pioneer Pet is ₹70,673 away,
   Babaji Udyog ₹1,56,733 away. Their next bill starts 194Q.

## Two process problems worth fixing

- **Another box wrote under the same USER39 login mid-batch.** Draft 55302 appeared
  at 15:12 between the opening duplicate check and the write; only the live
  re-check immediately before each POST caught it. **One machine per pile.**
- **Four A/P invoices were posted LIVE, unapproved, from that box today** —
  49987 (₹5,664), 50006/50007/50008 (₹9,734 / ₹12,548 / ₹19,620). That is
  `sapb1 post` where `draft` + `add-draft` belongs (C-0034). They bypassed Bhawani.

## The single change that would save the most time next batch

**Write the GRN number on the bill at the gate.** Only 5 of 18 scans carried it;
every one that did went through first time, the rest cost a whole matching phase.
Second: populate GSTIN on the vendor master — `FederalTaxID` is empty for all
2,235 Oil vendors, which is why name matching was attempted at all.
