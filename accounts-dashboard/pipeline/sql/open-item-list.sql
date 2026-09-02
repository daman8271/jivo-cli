-- ============================================================================
-- open-item-list.sql   (section: open-item-list)   as-of {{ASOF}}
-- The document-level drill-down that sits behind customer-ageing and
-- vendor-ageing: EVERY open item on BOTH sides of the ledger, one row per
-- document, UNIONed with a DOCTYPE discriminator and a debit/credit SIGN so
-- the list nets correctly.
--
-- ONE ROW PER: one open SAP document (or one unapplied payment).
--   AR_INV  OINV  DocStatus='O'                  SGN +1  debit  (customer owes)
--   AR_CN   ORIN  DocStatus='O'                  SGN -1  credit (JIVO owes)
--   AR_RCT  ORCT  OpenBal>0   money in, unapplied SGN -1  credit
--   AP_INV  OPCH  DocStatus='O'                  SGN -1  credit (JIVO owes)
--   AP_CN   ORPC  DocStatus='O'                  SGN +1  debit
--   AP_PMT  OVPM  OpenBal>0   money out,unapplied SGN +1  debit
--
-- DOCTYPE vs SIDE - they are NOT the same axis and must not be conflated.
--   DOCTYPE names the SAP DOCUMENT (which table, which money direction).
--   SIDE    names the PARTY's ledger side, read off the document's own card:
--           'AR' = the counterparty is a customer, 'AP' = a vendor.
--   For invoices and credit notes the two always agree.  For PAYMENTS they do
--   not: ORCT (money in) can be a refund FROM a vendor and OVPM (money out) a
--   refund TO a customer, so SIDE is derived from "DocType" - see the raw CTE.
--   SGN is a pure debit/credit sign and is correct for all six regardless.
--
-- ORDER OF MAGNITUDE (live 2026-08-21, uncapped): Oil 23,230 items /
--   Rs 2,582.42 Cr gross; Mart 10,017 / Rs 649.43 Cr; Bev 2,206 / Rs 14.27 Cr.
--   The cap keeps at most (1500 by size) UNION (400 per DOCTYPE) rows per
--   company - live that is Oil 2,162 / Mart 2,191 / Bev 1,090 (see CAPPING).
--
-- MONEY UNIT: every money column is INR **RUPEES** (DOUBLE, 2 dp). No _L, no
--   _CR suffix anywhere, on purpose - the reconciliation identities below hold
--   to the rupee. The dashboard divides by 1e5 / 1e7 for display.
--
-- ---------------------------------------------------------------------------
-- TRAP 1 - "DocStatus"='O' IS NOT THE TRUTH AT JIVO.  Bills and invoices are
--   settled by manual journal entries and by on-account payments that were
--   never internally reconciled, so the document stays OPEN long after the
--   money moved.  Oil, live 2026-08-21: raw open A/P = Rs 309.20 Cr against a
--   net OCRD vendor-card credit of Rs 93.65 Cr (2,231 CardType='S' cards) - the
--   documents overstate by 3.3x.  Handled, NOT hidden:
--     - every row carries CARD_BALANCE (OCRD."Balance", the ground truth),
--       CARD_OPEN_NET (this card's netted open items), CARD_STALE_GAP
--       (= CARD_OPEN_NET - CARD_BALANCE) and CARD_REAL_PCT.
--     - ITEM_REAL_EST = OPEN_AMT * CARD_REAL_PCT/100 is a PRO-RATA ESTIMATE of
--       the part of this document that the ledger actually supports.  It is
--       INFERRED, not a SAP figure.  OPEN_AMT stays untouched next to it.
--   Do NOT sum OPEN_AMT and call it the receivable/payable - use the ageings.
--
-- TRAP 2 - MIGRATION OPENINGS.  SAP go-live was 2024-09-30; documents dated
--   EXACTLY that day are migrated opening balances, not transactions.  For
--   OVPM they are catastrophic if summed blind: 77 migrated unapplied vendor
--   payments carry Rs 1,874.81 Cr of the Rs 2,017.37 Cr total "unapplied
--   payments" in Oil - e.g. 7 payments to AL GHURAIR (USD 41.3 M each-ish,
--   Rs 341 Cr) whose vendor card balance today is Rs 2.35 L.  IS_MIGRATED
--   flags them per row; CO_MIGRATED_OPEN totals them (Oil Rs 1,982.49 Cr
--   across all six types).  Their DocDueDate is the TRUE original date, so
--   DAYS_OVERDUE is still meaningful.
--   THE DATE IS OIL'S, and that is correct for all three books, checked: Mart's
--   books open 2024-10-03 (OINV) / 2025-01-01 (the rest) and Bev's 2024-10-01,
--   with NO migration cohort worth the name - Mart's whole 2025-01-01 opening
--   day leaves Rs 1,800 of open A/P and Rs 1.69 L of open payments, Bev's
--   first days leave nothing open at all.  So CO_MIGRATED_OPEN = 0 for Mart
--   and Bev is the truth, not a missed go-live date.
--
-- TRAP 3 - FOREIGN CURRENCY.  "DocTotal"/"OpenBal" are LOCAL (INR); the FC
--   figure is in "DocTotalFC"/"OpenBalFc".  118 open items in Oil are non-INR
--   (107 USD, 9 EUR, 2 AUD) and they are the biggest rows in the book: USD
--   alone is Rs 2,022.94 Cr of the Rs 2,582.42 Cr.  OPEN_AMT is ALWAYS INR;
--   OPEN_AMT_FC carries the foreign figure and CURRENCY the code.
--
-- TRAP 4 - "CANCELED" is spelled with ONE l on OINV/ORIN/OPCH/ORPC and takes
--   THREE values (N live, Y was-cancelled, C is-the-cancelling-doc); on
--   ORCT/OVPM the column is "Canceled" (mixed case) with N/Y.  Both are
--   filtered to the live value.  Cancelled docs are all DocStatus='C' anyway.
--
-- TRAP 5 - BRANCH / INTERCOMPANY IS NOT TRADE.  Flagged, never dropped:
--   ACCT_KIND = BRANCH (OCRG."GroupName" LIKE '%BRANCH%' = JIVO's own state
--   GST registrations) / INTERCO (the other JIVO + Akal entities) / STAFF
--   (employee imprest cards) / TRADE (real outside parties), and IS_GROUP=1
--   for BRANCH+INTERCO.  A group-code test alone is NOT enough: Mart's
--   VENDA000001 "JIVO WELLNESS PVT LTD" sits in group 106 PURCHASE and Oil's
--   VENDA000483 "JIVO MART PVT LTD" in group 103 E-COMMERCE, so the NAME is
--   tested too.  Verified live in all 3 books: no card contains 'JIVO' without
--   starting with it, so UPPER(name) LIKE 'JIVO%' is exact.
--   KNOWN LIMIT, measured and left alone: STAFF is a GROUP-name test only, so
--   employee imprest cards filed under a geography group (ORGC000031 "ARVINDER
--   SINGH IMPREST JWPL0115", group DELHI) come out TRADE.  Live cost: 11 items
--   / Rs 1.27 L in Oil, 2 / Rs 1,957 in Mart, 6 / Rs 11,562 in Bev.  Immaterial
--   against Rs 2,582 Cr - not worth widening the test and risking a real
--   trading party whose name happens to contain JWPL.
--
-- TRAP 6 - PAYMENTS HAVE NO DUE DATE.  For AR_RCT/AP_PMT, DUE_DATE is the
--   payment's own DocDueDate, so DAYS_OVERDUE reads as "days this money has sat
--   unapplied", not "days late".  AGE_DAYS (from DOC_DATE) is the honest field
--   for those two types.
--
-- TRAP 7 - SIDE IS NOT THE TABLE.  See the DOCTYPE vs SIDE note at the top: a
--   payment's ledger side comes from its own "DocType", never from ORCT-vs-OVPM.
--
-- TRAP 8 - "AS-OF" IS ONLY HALF AS-OF.  {{ASOF}} filters DocDate, but
--   "PaidToDate", "OpenBal" and OCRD."Balance" are all LIVE values with no
--   history in these tables.  Back-dating the run therefore gives "documents
--   that existed on that date, with today's settlement state" - NOT the open
--   position as it stood that day.  Reconstructing that needs JDT1 by
--   RefDate; out of scope here.  For the daily refresh (ASOF = today) it is exact.
--
-- TRAP 9 - ROTTEN EXCHANGE RATES.  A handful of payments were keyed with
--   "DocRate" = 0.0001, so their LOCAL amount is ~87,000x too small: Oil OVPM
--   DocEntry 26317 (DocNum 726466747, AL GHURAIR) is USD 44.34 L booked as
--   Rs 443.40.  OPEN_AMT reports the local figure SAP holds, so such rows sink
--   below the Rs 10,000 floor and vanish.  This is SAP data entry, not a query
--   bug, and it is NOT corrected here - OPEN_AMT_FC + CURRENCY expose it.
--
-- TRAP 10 - NEGATIVE "OpenBal".  A few over-applied payments carry OpenBal < 0
--   (Oil 2 rows -Rs 0.91, Mart 1 -Rs 25 + 1 -Rs 1,000, Bev none).  The > 0
--   filter drops them.  Total effect across all three books: Rs 1,025.91.
--
-- ---------------------------------------------------------------------------
-- DOES SAP'S OWN RECONCILIATION GIVE A BETTER "OPEN"?  NO - checked, it does
-- not, and the columns prove it rather than assert it.
--   * JDT1."IntrnMatch" <> 0 : 0 rows.  JDT1."Closed"='Y' : 0 rows.  Re-checked
--     2026-08-21 in ALL THREE books (Oil 526,820 / Mart 344,144 / Bev 86,414
--     JDT1 rows) - not one matched or closed line anywhere.  The journal-level
--     match state is simply not maintained, so "open" cannot be derived from
--     the ledger lines.
--   * OITR/ITR1 IS populated (live, uncancelled: Oil 29,062 reconciliations /
--     114,855 lines, 4,115 manual; Mart 12,930 / 52,703 / 1,351; Bev 6,112 /
--     20,409 / 1,415).  But it only touches a slice of the open book: of the
--     23,230 open Oil items, 3,903 have an ITR1 row at all.  And where rows do
--     exist SAP never pushed the result back into PaidToDate/DocStatus, so the
--     two disagree.  ITR1 is an account-level (control-account) record, not a
--     document-level one.
--   * The signed-line trap is documented on the oitr CTE below: one settlement
--     can be written twice, once as a system account reconciliation and once as
--     a manual BP one, on OPPOSITE "IsCredit" sides.  RECON_AMT therefore takes
--     GREATEST(D-side, C-side), never the sum of both.
--   Verdict: OITR is a DIAGNOSTIC, not a definition.  It is exposed as
--   OITR_RECON_AMT / OITR_LINES / RECON_STATE ('NONE' | 'PARTIAL' |
--   'FULL_PER_OITR' = SAP's own reconciliation says settled while the document
--   still reads open - the cleanest stale-open smoking gun in the row set).
--   Live FULL_PER_OITR counts after the fix: Oil 436, Mart 60, Bev 76.
--   OCRD."Balance" remains the ground truth for what a party owes.
--
-- ---------------------------------------------------------------------------
-- CAPPING.  Two stages, and the uncapped truth is returned alongside:
--   (1) materiality floor  OPEN_AMT >= 10,000  (OPEN_AMT is >0 by construction,
--       so this is an absolute floor; it holds 99.86% of Oil value)
--   (2) hard cap SIZE_RANK <= 1500 OR DT_SIZE_RANK <= 400, ranked by OPEN_AMT
--       DESC so the cut can only ever drop the SMALLEST items.
--   Presentation order is worst-overdue-first (DAYS_OVERDUE DESC, then size).
--   CO_ITEMS_ALL / CO_ITEMS_SHOWN and CO_OPEN_ALL / CO_OPEN_SHOWN let the
--   dashboard say "showing N of M (Rs X of Rs Y)".  DT_ITEMS_ALL / DT_OPEN_ALL
--   give the same per DOCTYPE.  All the CO_/DT_ columns are UNCAPPED and
--   UNFILTERED by the materiality floor.
--
-- RECONCILIATION IDENTITIES (verified live on all 3 books, 2026-08-21):
--   * CO_STALE_GAP = CO_OPEN_NET - CO_OCRD_NET   exactly, on every row.
--   * SIGNED_OPEN  = SGN * OPEN_AMT              exactly, on every row.
--   * CARD_STALE_GAP = CARD_OPEN_NET - CARD_BALANCE  exactly, on every row.
--   * DOC_TOTAL - APPLIED = OPEN_AMT   on the four DOCUMENT types (for AR_RCT /
--     AP_PMT, APPLIED is back-solved as DocTotal - OpenBal, same identity).
--   * SUM over the UNCAPPED set of SIGNED_OPEN per card = CARD_OPEN_NET.
--   * ITEM_REAL_EST is computed from the UNROUNDED CARD_REAL_PCT, so it will not
--     re-derive exactly from the printed 4-dp percentage.  Trust ITEM_REAL_EST.
--
-- CONSUMER HAZARD - the CARD_*, DT_* and CO_* columns are PER-CARD / PER-DOCTYPE
--   / PER-COMPANY totals repeated on every row they describe.  Read them off ONE
--   row.  SUMming any of them down the table multiplies the figure by the row
--   count.  Only DOC_TOTAL / APPLIED / OPEN_AMT / SIGNED_OPEN / OPEN_AMT_FC /
--   ITEM_REAL_EST / OITR_RECON_AMT are per-row and safe to add up.
--
-- COLUMN LIST (exact, in order):
--   DOCTYPE, SIDE, SGN, OBJ_TYPE, DOC_ENTRY, DOC_NUM, EXT_REF,
--   CARD_CODE, CARD_NAME, CARD_TYPE, BP_GROUP, ACCT_KIND, IS_GROUP,
--   BPL_ID, BPL_NAME,
--   DOC_DATE, DUE_DATE, DAYS_OVERDUE, AGE_DAYS, AGE_BUCKET, IS_MIGRATED,
--   DOC_TOTAL, APPLIED, OPEN_AMT, SIGNED_OPEN, CURRENCY, OPEN_AMT_FC,
--   OITR_RECON_AMT, OITR_LINES, RECON_STATE,
--   CARD_BALANCE, CARD_OPEN_NET, CARD_OPEN_GROSS, CARD_STALE_GAP,
--   CARD_REAL_PCT, ITEM_REAL_EST,
--   SIZE_RANK, DT_SIZE_RANK, DT_ITEMS_ALL, DT_OPEN_ALL,
--   DT_ITEMS_SHOWN, DT_OPEN_SHOWN,
--   CO_ITEMS_ALL, CO_ITEMS_SHOWN, CO_OPEN_ALL, CO_OPEN_SHOWN, CO_OPEN_NET,
--   CO_OCRD_NET, CO_STALE_GAP, CO_MIGRATED_OPEN, AS_OF     (51 columns)
-- ============================================================================
WITH bp AS (
  SELECT c."CardCode"                        AS CARD_CODE,
         c."CardName"                        AS CARD_NAME,
         c."CardType"                        AS CARD_TYPE,
         CAST(c."Balance" AS DOUBLE)         AS CARD_BALANCE,
         IFNULL(g."GroupName",'(no group)')  AS BP_GROUP,
         CASE
           WHEN IFNULL(g."GroupName",'') LIKE '%BRANCH%' THEN 'BRANCH'
           WHEN UPPER(c."CardName") LIKE 'JIVO%'
             OR UPPER(c."CardName") LIKE '%A U O JWPL%'
             OR UPPER(c."CardName") LIKE '%AKAL ROZGAR%'
             OR UPPER(c."CardName") LIKE '%AKAL INFO%'
             OR IFNULL(g."GroupName",'') IN ('PARENT COMPANY',
                                             'COMPANY UNIT CUSTOMER',
                                             'COMPANY UNIT VENDOR')
             THEN 'INTERCO'
           WHEN IFNULL(g."GroupName",'') LIKE '%STAFF%' THEN 'STAFF'
           ELSE 'TRADE'
         END                                 AS ACCT_KIND
  FROM {{SCHEMA}}.OCRD c
  LEFT JOIN {{SCHEMA}}.OCRG g
         ON g."GroupCode" = c."GroupCode" AND g."GroupType" = c."CardType"
),
-- SAP's own internal reconciliation, one row per source document.
-- SrcObjTyp: 13=OINV 14=ORIN 24=ORCT 18=OPCH 19=ORPC 46=OVPM.
-- ITR1 lines are SIGNED ("IsCredit" = 'D' | 'C') and one document can appear on
-- BOTH sides (Oil: 104 of the open set) because SAP writes an account-level
-- system reconciliation AND a BP-level manual one for the same settlement -
-- e.g. OPCH DocEntry 42554, Rs 5.93 Cr, has ReconNum 40148 (IsCredit D, acct
-- 2140001, IsSystem Y) and ReconNum 41914 (IsCredit C, acct 2110002, manual).
-- Summing both sides blind counted that document TWICE and produced a
-- "reconciled" amount larger than the document itself - arithmetically
-- impossible - on 128 Oil / 47 Mart / 15 Bev open documents (Rs 18.2 Cr of
-- phantom excess in Oil alone), which in turn fired RECON_STATE='FULL_PER_OITR'
-- on 35 Oil / 33 Mart / 12 Bev documents SAP has NOT fully reconciled.
-- GREATEST of the two side-totals is the right read: one settlement, counted
-- once, whichever way SAP happened to book it.  Impossible rows fall to
-- 87 / 14 / 1 (Rs 0.95 Cr excess in Oil).  The survivors are SAP's own data and
-- are NOT corrected here: they are ACCOUNT-level system reconciliations that
-- stamp the reconciliation's whole total on each participant line.  Worked
-- example - Oil OPCH DocEntry 15558 (Rs 15.73 L) carries ONE ITR1 line of
-- Rs 23.51 L from ReconNum 13511, a system recon on account 1102007 clearing a
-- GRPO (SrcObjTyp 20, DocEntry 6450) worth Rs 23.51 L against it.  The invoice
-- really was reconciled, so FULL_PER_OITR still reads true; only the AMOUNT is
-- the reconciliation's, not the document's.  One more reason OITR_RECON_AMT is
-- a diagnostic and never a settlement figure.
oitr AS (
  SELECT i."SrcObjTyp"                        AS OBJ_TYPE,
         i."SrcObjAbs"                        AS DOC_ENTRY,
         GREATEST(
           SUM(CASE WHEN i."IsCredit" = 'D' THEN CAST(i."ReconSum" AS DOUBLE) ELSE 0 END),
           SUM(CASE WHEN i."IsCredit" = 'C' THEN CAST(i."ReconSum" AS DOUBLE) ELSE 0 END)
         )                                    AS RECON_AMT,
         COUNT(*)                             AS RECON_LINES
  FROM {{SCHEMA}}.ITR1 i
  JOIN {{SCHEMA}}.OITR o ON o."ReconNum" = i."ReconNum"
  WHERE o."Canceled" = 'N'
    AND i."SrcObjTyp" IN ('13','14','24','18','19','46')
    AND CAST(o."ReconDate" AS DATE) <= DATE'{{ASOF}}'
  GROUP BY i."SrcObjTyp", i."SrcObjAbs"
),
raw AS (
  SELECT 'AR_INV' AS DOCTYPE, 'AR' AS SIDE, 1 AS SGN, '13' AS OBJ_TYPE,
         "DocEntry" AS DOC_ENTRY, "DocNum" AS DOC_NUM,
         CAST(IFNULL("NumAtCard",'') AS NVARCHAR(100)) AS EXT_REF,
         "CardCode" AS CARD_CODE, "BPLId" AS BPL_ID,
         CAST(IFNULL("BPLName",'') AS NVARCHAR(200)) AS BPL_NAME,
         CAST("DocDate" AS DATE) AS DOC_DATE, CAST("DocDueDate" AS DATE) AS DUE_DATE,
         CAST("DocTotal" AS DOUBLE) AS DOC_TOTAL,
         CAST("PaidToDate" AS DOUBLE) AS APPLIED,
         CAST("DocTotal" - "PaidToDate" AS DOUBLE) AS OPEN_AMT,
         CAST("DocCur" AS NVARCHAR(3)) AS CURRENCY,
         CAST(IFNULL("DocTotalFC",0) - IFNULL("PaidFC",0) AS DOUBLE) AS OPEN_AMT_FC
  FROM {{SCHEMA}}.OINV
  WHERE "CANCELED" = 'N' AND "DocStatus" = 'O'
    AND CAST("DocTotal" - "PaidToDate" AS DOUBLE) > 0
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
  UNION ALL
  SELECT 'AR_CN', 'AR', -1, '14',
         "DocEntry", "DocNum", CAST(IFNULL("NumAtCard",'') AS NVARCHAR(100)),
         "CardCode", "BPLId", CAST(IFNULL("BPLName",'') AS NVARCHAR(200)),
         CAST("DocDate" AS DATE), CAST("DocDueDate" AS DATE),
         CAST("DocTotal" AS DOUBLE), CAST("PaidToDate" AS DOUBLE),
         CAST("DocTotal" - "PaidToDate" AS DOUBLE),
         CAST("DocCur" AS NVARCHAR(3)),
         CAST(IFNULL("DocTotalFC",0) - IFNULL("PaidFC",0) AS DOUBLE)
  FROM {{SCHEMA}}.ORIN
  WHERE "CANCELED" = 'N' AND "DocStatus" = 'O'
    AND CAST("DocTotal" - "PaidToDate" AS DOUBLE) > 0
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
  UNION ALL
  -- SIDE comes from the PAYMENT'S OWN "DocType", not from the table it sits in.
  -- ORCT is "money in", which is USUALLY a customer receipt - but 146 open Oil
  -- rows (Rs 2.25 Cr), 6 Mart and 18 Bev are DocType='S': cash received back
  -- FROM A VENDOR.  Calling those AR put a vendor refund in the customer bucket.
  SELECT 'AR_RCT',
         CAST(CASE WHEN "DocType" = 'C' THEN 'AR' WHEN "DocType" = 'S' THEN 'AP'
                   ELSE 'AR' END AS NVARCHAR(2)), -1, '24',
         "DocEntry", "DocNum", CAST('' AS NVARCHAR(100)),
         "CardCode", "BPLId", CAST(IFNULL("BPLName",'') AS NVARCHAR(200)),
         CAST("DocDate" AS DATE), CAST("DocDueDate" AS DATE),
         CAST("DocTotal" AS DOUBLE),
         CAST("DocTotal" - "OpenBal" AS DOUBLE),
         CAST("OpenBal" AS DOUBLE),
         CAST("DocCurr" AS NVARCHAR(3)),
         CAST(IFNULL("OpenBalFc",0) AS DOUBLE)
  FROM {{SCHEMA}}.ORCT
  WHERE "Canceled" = 'N'
    AND CAST(IFNULL("OpenBal",0) AS DOUBLE) > 0
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
  UNION ALL
  SELECT 'AP_INV', 'AP', -1, '18',
         "DocEntry", "DocNum", CAST(IFNULL("NumAtCard",'') AS NVARCHAR(100)),
         "CardCode", "BPLId", CAST(IFNULL("BPLName",'') AS NVARCHAR(200)),
         CAST("DocDate" AS DATE), CAST("DocDueDate" AS DATE),
         CAST("DocTotal" AS DOUBLE), CAST("PaidToDate" AS DOUBLE),
         CAST("DocTotal" - "PaidToDate" AS DOUBLE),
         CAST("DocCur" AS NVARCHAR(3)),
         CAST(IFNULL("DocTotalFC",0) - IFNULL("PaidFC",0) AS DOUBLE)
  FROM {{SCHEMA}}.OPCH
  WHERE "CANCELED" = 'N' AND "DocStatus" = 'O'
    AND CAST("DocTotal" - "PaidToDate" AS DOUBLE) > 0
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
  UNION ALL
  SELECT 'AP_CN', 'AP', 1, '19',
         "DocEntry", "DocNum", CAST(IFNULL("NumAtCard",'') AS NVARCHAR(100)),
         "CardCode", "BPLId", CAST(IFNULL("BPLName",'') AS NVARCHAR(200)),
         CAST("DocDate" AS DATE), CAST("DocDueDate" AS DATE),
         CAST("DocTotal" AS DOUBLE), CAST("PaidToDate" AS DOUBLE),
         CAST("DocTotal" - "PaidToDate" AS DOUBLE),
         CAST("DocCur" AS NVARCHAR(3)),
         CAST(IFNULL("DocTotalFC",0) - IFNULL("PaidFC",0) AS DOUBLE)
  FROM {{SCHEMA}}.ORPC
  WHERE "CANCELED" = 'N' AND "DocStatus" = 'O'
    AND CAST("DocTotal" - "PaidToDate" AS DOUBLE) > 0
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
  UNION ALL
  -- Same mirror-image trap: OVPM is "money out", usually to a vendor, but 26
  -- open Oil rows (Rs 25.9 L) and 2 Bev are DocType='C' - a refund PAID TO A
  -- CUSTOMER.  The party is a customer, so the row belongs on the AR side.
  SELECT 'AP_PMT',
         CAST(CASE WHEN "DocType" = 'C' THEN 'AR' WHEN "DocType" = 'S' THEN 'AP'
                   ELSE 'AP' END AS NVARCHAR(2)), 1, '46',
         "DocEntry", "DocNum", CAST('' AS NVARCHAR(100)),
         "CardCode", "BPLId", CAST(IFNULL("BPLName",'') AS NVARCHAR(200)),
         CAST("DocDate" AS DATE), CAST("DocDueDate" AS DATE),
         CAST("DocTotal" AS DOUBLE),
         CAST("DocTotal" - "OpenBal" AS DOUBLE),
         CAST("OpenBal" AS DOUBLE),
         CAST("DocCurr" AS NVARCHAR(3)),
         CAST(IFNULL("OpenBalFc",0) AS DOUBLE)
  FROM {{SCHEMA}}.OVPM
  WHERE "Canceled" = 'N'
    AND CAST(IFNULL("OpenBal",0) AS DOUBLE) > 0
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
),
item AS (
  SELECT r.*,
         r.SGN * r.OPEN_AMT                                  AS SIGNED_OPEN,
         DAYS_BETWEEN(r.DUE_DATE, DATE'{{ASOF}}')            AS DAYS_OVERDUE,
         DAYS_BETWEEN(r.DOC_DATE, DATE'{{ASOF}}')            AS AGE_DAYS,
         CASE WHEN r.DOC_DATE = DATE'2024-09-30' THEN 1 ELSE 0 END AS IS_MIGRATED
  FROM raw r
),
-- card-level reality check, computed on the UNCAPPED set
card AS (
  SELECT CARD_CODE,
         SUM(SIGNED_OPEN) AS CARD_OPEN_NET,
         SUM(OPEN_AMT)    AS CARD_OPEN_GROSS
  FROM item GROUP BY CARD_CODE
),
-- uncapped per-DOCTYPE totals
dt AS (
  SELECT DOCTYPE, COUNT(*) AS DT_ITEMS_ALL, SUM(OPEN_AMT) AS DT_OPEN_ALL
  FROM item GROUP BY DOCTYPE
),
-- uncapped company totals ("of M" for the dashboard)
co AS (
  SELECT COUNT(*)          AS CO_ITEMS_ALL,
         SUM(i.OPEN_AMT)   AS CO_OPEN_ALL,
         SUM(i.SIGNED_OPEN) AS CO_OPEN_NET,
         SUM(CASE WHEN i.IS_MIGRATED = 1 THEN i.OPEN_AMT ELSE 0 END) AS CO_MIGRATED_OPEN
  FROM item i
),
-- OCRD ground truth over exactly the cards that carry an open item
co_bal AS (
  SELECT SUM(b.CARD_BALANCE) AS CO_OCRD_NET
  FROM bp b WHERE b.CARD_CODE IN (SELECT CARD_CODE FROM card)
),
enriched AS (
  SELECT i.DOCTYPE, i.SIDE, i.SGN, i.OBJ_TYPE, i.DOC_ENTRY, i.DOC_NUM, i.EXT_REF,
         i.CARD_CODE,
         IFNULL(b.CARD_NAME,'(card not in OCRD)')       AS CARD_NAME,
         IFNULL(b.CARD_TYPE, CASE WHEN i.SIDE='AR' THEN 'C' ELSE 'S' END) AS CARD_TYPE,
         IFNULL(b.BP_GROUP,'(no group)')                AS BP_GROUP,
         IFNULL(b.ACCT_KIND,'TRADE')                    AS ACCT_KIND,
         CASE WHEN IFNULL(b.ACCT_KIND,'TRADE') IN ('BRANCH','INTERCO') THEN 1 ELSE 0 END AS IS_GROUP,
         i.BPL_ID, i.BPL_NAME,
         i.DOC_DATE, i.DUE_DATE, i.DAYS_OVERDUE, i.AGE_DAYS,
         CASE WHEN i.DAYS_OVERDUE <=   0 THEN '0_NOTDUE'
              WHEN i.DAYS_OVERDUE <=  30 THEN '1_1-30'
              WHEN i.DAYS_OVERDUE <=  60 THEN '2_31-60'
              WHEN i.DAYS_OVERDUE <=  90 THEN '3_61-90'
              WHEN i.DAYS_OVERDUE <= 180 THEN '4_91-180'
              WHEN i.DAYS_OVERDUE <= 365 THEN '5_181-365'
              ELSE '6_365+' END                          AS AGE_BUCKET,
         i.IS_MIGRATED,
         i.DOC_TOTAL, i.APPLIED, i.OPEN_AMT, i.SIGNED_OPEN, i.CURRENCY, i.OPEN_AMT_FC,
         IFNULL(o.RECON_AMT,0)                           AS OITR_RECON_AMT,
         IFNULL(o.RECON_LINES,0)                         AS OITR_LINES,
         CASE WHEN o.DOC_ENTRY IS NULL             THEN 'NONE'
              WHEN o.RECON_AMT >= i.DOC_TOTAL - 1  THEN 'FULL_PER_OITR'
              ELSE 'PARTIAL' END                         AS RECON_STATE,
         IFNULL(b.CARD_BALANCE,0)                        AS CARD_BALANCE,
         c.CARD_OPEN_NET, c.CARD_OPEN_GROSS,
         c.CARD_OPEN_NET - IFNULL(b.CARD_BALANCE,0)      AS CARD_STALE_GAP,
         CASE WHEN ABS(c.CARD_OPEN_NET) < 0.005 THEN 100.0
              ELSE 100.0 * LEAST(1.0, ABS(IFNULL(b.CARD_BALANCE,0)) / ABS(c.CARD_OPEN_NET))
         END                                             AS CARD_REAL_PCT,
         ROW_NUMBER() OVER (ORDER BY i.OPEN_AMT DESC, i.DOCTYPE, i.DOC_ENTRY) AS SIZE_RANK,
         ROW_NUMBER() OVER (PARTITION BY i.DOCTYPE
                            ORDER BY i.OPEN_AMT DESC, i.DOC_ENTRY)              AS DT_SIZE_RANK
  FROM item i
  LEFT JOIN bp   b ON b.CARD_CODE = i.CARD_CODE
  LEFT JOIN card c ON c.CARD_CODE = i.CARD_CODE
  LEFT JOIN oitr o ON o.OBJ_TYPE  = i.OBJ_TYPE AND o.DOC_ENTRY = i.DOC_ENTRY
  WHERE i.OPEN_AMT >= 10000
),
-- THE CAP.  Keep an item if it is in the company's 1500 biggest OR in its own
-- DOCTYPE's 400 biggest.  The doctype leg exists because a pure size cut wipes
-- out both credit-note types (Oil AR_CN totals only Rs 0.97 Cr, every row of it
-- below the global cut-off) and the list would silently become one-sided.
kept AS (
  SELECT * FROM enriched WHERE SIZE_RANK <= 1500 OR DT_SIZE_RANK <= 400
),
shown_dt AS (
  SELECT DOCTYPE, COUNT(*) AS DT_ITEMS_SHOWN, SUM(OPEN_AMT) AS DT_OPEN_SHOWN
  FROM kept GROUP BY DOCTYPE
),
shown_co AS (
  SELECT COUNT(*) AS CO_ITEMS_SHOWN, SUM(OPEN_AMT) AS CO_OPEN_SHOWN FROM kept
)
SELECT e.DOCTYPE, e.SIDE, e.SGN, e.OBJ_TYPE, e.DOC_ENTRY, e.DOC_NUM, e.EXT_REF,
       e.CARD_CODE, e.CARD_NAME, e.CARD_TYPE, e.BP_GROUP, e.ACCT_KIND, e.IS_GROUP,
       e.BPL_ID, e.BPL_NAME,
       e.DOC_DATE, e.DUE_DATE, e.DAYS_OVERDUE, e.AGE_DAYS, e.AGE_BUCKET, e.IS_MIGRATED,
       ROUND(e.DOC_TOTAL,2)       AS DOC_TOTAL,
       ROUND(e.APPLIED,2)         AS APPLIED,
       ROUND(e.OPEN_AMT,2)        AS OPEN_AMT,
       ROUND(e.SIGNED_OPEN,2)     AS SIGNED_OPEN,
       e.CURRENCY,
       ROUND(e.OPEN_AMT_FC,2)     AS OPEN_AMT_FC,
       ROUND(e.OITR_RECON_AMT,2)  AS OITR_RECON_AMT,
       e.OITR_LINES, e.RECON_STATE,
       ROUND(e.CARD_BALANCE,2)    AS CARD_BALANCE,
       ROUND(e.CARD_OPEN_NET,2)   AS CARD_OPEN_NET,
       ROUND(e.CARD_OPEN_GROSS,2) AS CARD_OPEN_GROSS,
       ROUND(e.CARD_STALE_GAP,2)  AS CARD_STALE_GAP,
       -- 4 dp, not 2: Oil's AL GHURAIR card carries Rs 1,741.69 Cr of open items
       -- against a Rs 2.35 L ledger balance, i.e. 0.0014% real.  Rounded to 2 dp
       -- that prints 0.00 next to a non-zero ITEM_REAL_EST, which reads as a bug.
       ROUND(e.CARD_REAL_PCT,4)   AS CARD_REAL_PCT,
       ROUND(e.OPEN_AMT * e.CARD_REAL_PCT / 100.0, 2) AS ITEM_REAL_EST,
       e.SIZE_RANK, e.DT_SIZE_RANK,
       d.DT_ITEMS_ALL,
       ROUND(d.DT_OPEN_ALL,2)     AS DT_OPEN_ALL,
       sd.DT_ITEMS_SHOWN,
       ROUND(sd.DT_OPEN_SHOWN,2)  AS DT_OPEN_SHOWN,
       co.CO_ITEMS_ALL,
       sc.CO_ITEMS_SHOWN,
       ROUND(co.CO_OPEN_ALL,2)    AS CO_OPEN_ALL,
       ROUND(sc.CO_OPEN_SHOWN,2)  AS CO_OPEN_SHOWN,
       ROUND(co.CO_OPEN_NET,2)    AS CO_OPEN_NET,
       ROUND(cb.CO_OCRD_NET,2)    AS CO_OCRD_NET,
       ROUND(co.CO_OPEN_NET - cb.CO_OCRD_NET,2) AS CO_STALE_GAP,
       ROUND(co.CO_MIGRATED_OPEN,2) AS CO_MIGRATED_OPEN,
       DATE'{{ASOF}}'             AS AS_OF
FROM kept e
CROSS JOIN co
CROSS JOIN co_bal cb
CROSS JOIN shown_co sc
JOIN dt       d  ON d.DOCTYPE  = e.DOCTYPE
JOIN shown_dt sd ON sd.DOCTYPE = e.DOCTYPE
ORDER BY e.DAYS_OVERDUE DESC, e.OPEN_AMT DESC, e.DOCTYPE, e.DOC_ENTRY