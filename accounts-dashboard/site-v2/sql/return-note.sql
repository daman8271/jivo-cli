-- return-note.sql  --  RETURN NOTE SUMMARY (customer returns coming back INTO JIVO)
--
-- Source: {{SCHEMA}}.ORDN / RDN1 (A/R Return, ObjType 16) measured against
--         {{SCHEMA}}.OINV / INV1 (A/R invoice) and {{SCHEMA}}.ORIN / RIN1 (A/R credit
--         note), and valued through {{SCHEMA}}.JDT1 (the return's own journal entry).
-- Everything is dated on or before {{ASOF}} and counts LIVE documents only
-- ("CANCELED" = 'N' -- see trap 1).
--
-- ONE ROW PER (SCOPE, GRP_KEY).  Six stacked scopes in one bounded result:
--   SCOPE = 'TOTAL'        1 row   -- company grand total
--   SCOPE = 'CLASS'        3 rows  -- EXTERNAL / BRANCH / INTERCOMPANY
--   SCOPE = 'CREDIT_NOTE'  2 rows  -- HAS_CREDIT_NOTE / NO_CREDIT_NOTE
--   SCOPE = 'NO_CN_REASON' <=3     -- why the uncredited returns are uncredited
--   SCOPE = 'MONTH'        <=36    -- every month with a return or an invoice
--   SCOPE = 'CUSTOMER'     <=40    -- biggest returning customers by stock cost
-- Measured 2026-08-21: Oil 72 rows, Mart 70, Bev 72 (the month count is the only
-- thing that moves: Oil 23, Mart 21, Bev 23).  Hard-capped at 200 rows.
--
-- Columns (23, in this order):
--   SCOPE, GRP_KEY, GRP_LABEL, SORT_KEY,
--   RET_DOCS, RET_DOCS_ZERO_VALUE, RET_DOCS_OPEN, RET_DOCS_FROM_DELIVERY,
--   RET_QTY_PCS, RET_QTY_OTHER_UOM,
--   RET_NET, RET_GST, RET_GROSS, RET_STOCK_COST,
--   RET_DOCS_NO_CN, RET_DOCS_NO_CN_BILLED, RET_QTY_PCS_NO_CN, RET_STOCK_COST_NO_CN,
--   CN_DOCS, CN_NET, SALES_NET,
--   CN_PCT_OF_SALES, RET_COST_PCT_OF_SALES
--
-- MONEY UNIT: every amount is RAW INR RUPEES (no _L / _CR suffix) -- the same
-- convention as goods-return.sql, so the two sections render alike.
-- QUANTITY UNIT: PIECES (single bottles), never cartons.  NO tonnage conversion is
-- applied: the lines mix UoM (trap 3), so piece lines and non-piece lines are two
-- separate columns and must never be added together.
--
-- THE HEADLINE THE SECTION EXISTS FOR
--   RET_DOCS_NO_CN        = live returns with NO live credit note linked to them.
--   RET_DOCS_NO_CN_BILLED = the subset whose base delivery WAS invoiced, i.e. the
--                           customer was definitely billed for goods that came back
--                           and no credit note was ever raised against the return.
--   SCOPE='NO_CN_REASON'  splits the uncredited population three ways so nobody reads
--                           an unbilled shipment as a missing credit.
--   HONEST LIMIT: "no credit note" means no credit note LINKED IN SAP.  2723 of Oil's
--   6147 live credit notes carry no base document on any line, so a customer may have
--   been credited by a standalone note this query cannot attribute.  Treat these as a
--   WORK LIST to check, not as a proven loss.  See notes/return-note.md.
--
-- Traps handled (full write-up in notes/return-note.md):
--   1. "CANCELED" on ORDN has THREE values, not two: 'N' live, 'Y' the cancelled
--      original, 'C' the auto-generated cancellation mirror.  Oil holds 1817 'N',
--      107 'Y' and 107 'C' (2031 total); Mart 1792 / 26 / 26; Bev 160 / 12 / 12.
--      Filtering on <> 'Y' alone double-counts; only 'N' is kept.
--   2. THE BIG ONE -- most return notes carry NO VALUE.  1104 of Oil's 1817 live
--      returns (61%) have "DocTotal" = 0; Mart 600/1792, Bev 133/160.  The note is
--      used purely as a stock-movement document and the money is settled on a separate
--      credit note.  Since 2026-05 this is now universal: 185 of Oil's last 187
--      returns are value-blind.  Reading RET_GROSS as "value returned" understates the
--      position ~2.5x.  RET_STOCK_COST is the reliable size measure: the debit SAP
--      posted back into inventory, reached via ORDN."TransId" -> JDT1.  VERIFIED by
--      account: every debit on those journals lands on 1103xxx FINISHED GOODS / RAW
--      MATERIAL / PACKAGING and every credit on 5000xxx COGS, so SUM("Debit") is the
--      stock value returned.  (One impurity: account 5100001 PRICE DIFFERENCE takes
--      Rs 8,613 Dr / Rs 3,452 Cr over 15 Oil lines -- 0.01% of the total, left in.)
--  2b. THE ZERO-VALUATION BLIND SPOT -- corrected 2026-08-21 by adversarial review.
--      An earlier version of this header said returns with no journal entry make
--      RET_STOCK_COST "a floor, not a total" and that Bev's column "must NOT be
--      presented as Bev's return cost".  THAT WAS WRONG and is retracted.  The
--      documents with no journal entry DO have inventory receipts in OINM, and SAP
--      valued every one of them at EXACTLY zero:
--          OINM "TransType"=16, live returns, split by whether ORDN."TransId" is null
--          OIL   has-journal 1732 docs TransValue 87,066,172.66 | no-journal  85 docs 0.00
--          MART  has-journal 1640 docs TransValue 39,938,969.34 | no-journal 152 docs 0.00
--          BEV   has-journal   28 docs TransValue    259,426.65 | no-journal 132 docs 0.00
--      RET_STOCK_COST therefore reproduces SAP's inventory posting COMPLETELY, and was
--      verified three independent ways (JDT1 debit by account, OINM "TransValue" +
--      "PriceDiff", and the section's own aggregate) -- all three agree to the paisa.
--      The real caveat is different, and it is about ECONOMICS, not missing data: SAP
--      costs those receipts at nil because the item's moving-average cost in that
--      warehouse is nil (verified on OINM."CalcPrice" = 0 and OITW."AvgPrice" = 0 for
--      inventory items, "InvntItem" = 'Y').  So real goods come back and land in stock
--      at book value zero.  Measure the blind spot in PIECES, not documents:
--          live returns with RET_STOCK_COST = 0   docs      pieces  % of pieces  their DocTotal
--          OIL                                     85       8,931        2.3%     Rs   14.82 L
--          MART                                   152      36,805       26.8%     Rs   79.23 L
--          BEV                                    132     148,870       87.3%     Rs    2.92 L
--      Read RET_STOCK_COST as "what SAP put back into inventory" -- always true -- and
--      never as "what the returned goods were worth" in Mart or Bev.  RET_QTY_PCS sits
--      beside it in every scope precisely so the divergence is visible on the page.
--   3. RDN1 mixes units of measure: of Oil's 7540 live lines, 6730 are PCS and 424 are
--      blank (blank behaves as PCS), leaving 386 on SET / KGS / NOS / LTR / MTR / DRM.
--      Adding them yields a meaningless number, so PCS + blank go to RET_QTY_PCS and
--      everything else to RET_QTY_OTHER_UOM.  Verified: 391267.21 + 3964 = 395231.21
--      = RET_QTY_PCS exactly, and the six other UoMs sum to RET_QTY_OTHER_UOM exactly.
--   4. THE ORDN <-> ORIN LINK: NEITHER DIRECTION IS A SUBSET OF THE OTHER, so the
--      choice matters and was made on evidence.  Going from the credit-note side
--      (RIN1."BaseType"=16 -> live ORIN) finds 1396 credited Oil returns; going from
--      the return side (RDN1."TargetType"=14) finds 1398.  5 Oil returns are return-
--      side-only and 3 are credit-note-side-only; Bev is 3 and 0; Mart agrees exactly.
--      All 5 Oil return-side-only cases are LIVE returns whose linked credit note was
--      CANCELLED -- SAP leaves "TrgetEntry" pointing at the dead note -- so the return
--      side would wrongly mark them credited.  The decisive test: the number of live
--      returns that have a LIVE credit note but are missed by the credit-note-side
--      join is 0 in all three books.  This query therefore joins RIN1, never RDN1.
--   5. The relationship is MANY-TO-MANY in both directions.  One Oil return (DocEntry
--      4732, AVENUE SUPERMARTS) is credited by 82 separate credit notes, and one Oil
--      credit note can cover up to 3 returns.  So CN_NET is summed from RIN1.
--      "LineTotal" (net of GST) at LINE level rather than from the ORIN header, and
--      CN_DOCS is a COUNT(DISTINCT credit note) computed at the scope level rather
--      than a sum of per-return counts.  Cross-checked: Oil CN_NET = 84,567,730.63
--      and CN_DOCS = 2517 = COUNT(DISTINCT live ORIN with a BaseType=16 line).
--   6. Branch / intercompany is NOT trade, and A GROUP-NAME TEST ALONE FINDS NOTHING
--      HERE.  Exactly 0 Oil returns sit in a card group whose name contains 'BRANCH',
--      yet CUSTA000606 "JIVO MART PVT LTD" -- card group "DELHI" -- is 477 of Oil's
--      1817 returns and Rs 3.19 Cr of the Rs 3.45 Cr header value (92.5%).  All 23
--      JIVO group cards carry 'JIVO' in the name, so classification is group-name THEN
--      card-name, never a hard-coded code list (the same code is a different party in
--      a different book).  BRANCH and INTERCOMPANY get their own rows -- never
--      silently dropped, never silently folded into EXTERNAL.
--   7. "DocStatus" = 'O' is not reliable at JIVO.  RET_DOCS_OPEN is a diagnostic only;
--      it measures nothing outstanding.  (Oil: 40 of 1817 open, 38 of them uncredited.)
--   8. Returns are almost never linked to the invoice they reverse.  Only 306 of Oil's
--      1817 live returns have any base document (RDN1."BaseType"=15, a DELIVERY; 311
--      including cancelled returns), and "BaseType"=13 (invoice) is ZERO rows in all
--      three books.  The invoice number is typed into the free-text "Comments" field
--      instead -- 414 of Oil's 1817 live returns say "INVOICE" in "Comments", in at
--      least three incompatible formats ("GR Against Invoice No. 624121160", the
--      customer's own series "RTV Against Invoice No DL/SL/2279/24-25", and
--      "Invoice Number : 624101247").  RET_DOCS_FROM_DELIVERY
--      counts the structured links honestly; the prose reference is carried to
--      return-note-detail.sql, never parsed here.
--   9. Delivery-linked and credit-noted are MUTUALLY EXCLUSIVE at JIVO: all 306 Oil
--      delivery-based returns land in NO_CREDIT_NOTE and the HAS_CREDIT_NOTE row shows
--      RET_DOCS_FROM_DELIVERY = 0.  That is why NO_CN_REASON exists.  Of Oil's 421
--      uncredited returns: 212 reverse an INVOICED delivery (credit IS due, Rs 3.18 L
--      at stock cost), 94 reverse a delivery that was NEVER INVOICED (no credit due,
--      Rs 64.08 L), and 115 have no base link at all so the question is unanswerable
--      from structure (Rs 84.91 L -- the real work list).  Counting all 421 as missing
--      credits overstates the exception roughly 2x.
--  10. The sales denominator EXCLUDES go-live migration documents.  Oil carries 11,078
--      invoices dated exactly 2024-09-30 worth Rs 74.74 Cr of migrated opening balance;
--      leaving them in inflates SALES_NET ~8% and silently shrinks every ratio.  Mart
--      and Bev have none.  The same filter is applied to ORDN as a safety belt, but no
--      return note is dated 2024-09-30 in any of the three books, so it is a no-op.
--  11. SALES_NET is invoices net of GST, ex-cancelled, ex-migration, BEFORE deducting
--      credit notes, so the ratio reads "returns per rupee invoiced".  It is
--      deliberately NOT JIVO turnover (already net of credit notes) -- that would be
--      circular.  BOTH RATIOS ARE NARROWER THAN THEY SOUND, so read the names literally:
--        * CN_PCT_OF_SALES counts ONLY credit notes raised against a RETURN NOTE.  It is
--          NOT "all sales returns as a % of sales".  Oil's live credit notes are
--          Rs 8.46 Cr on returns (BaseType 16), Rs 21.91 Cr on invoices (BaseType 13)
--          and Rs 16.32 Cr standalone (BaseType -1); all credit notes together are
--          about 5.1% of Oil sales, against the 0.92% this column shows.
--        * RET_COST_PCT_OF_SALES is inventory COST over sales REVENUE -- unlike over
--          unlike.  It is the right way to size the stock coming back, and the wrong
--          number to quote as "x% of our sales came back", which would be a revenue
--          ratio and larger by the gross margin.  It also inherits trap 2b.
--
-- ---------------------------------------------------------------------------------
-- ADVERSARIAL REVIEW 2026-08-21 -- what was attacked, and what it left standing.
-- Every figure in this section was re-derived by a second, independently written
-- query before this line was added.  Findings that survived, in the order they bite:
--
--  12. CN_DOCS IS NOT ADDITIVE ACROSS SCOPES, by design.  It is COUNT(DISTINCT credit
--      note) computed inside each group, which is the right answer for that group and
--      the wrong thing to add up.  Oil: the 23 MONTH rows sum to 2518 against a TOTAL
--      of 2517, because one credit note credits returns dated in two different months
--      and is correctly counted in both.  Every other measure IS additive and was
--      checked: MONTH and CLASS both sum to TOTAL exactly for RET_DOCS, RET_STOCK_COST
--      and CN_NET in all three books.  Never sum CN_DOCS across rows.
--
--  13. "NO CREDIT NOTE" HAS A MEASURED FALSE-POSITIVE RATE, and it is small.  Chasing
--      the full structural chain return -> base delivery -> the invoice that consumed
--      that delivery -> a credit note raised against THAT invoice (RIN1."BaseType"=13)
--      finds 4 of Oil's 212 and 3 of Mart's 912 "billed but never credited" returns
--      already credited that way; Bev 0 of 3.  They are deliberately still counted as
--      uncredited: a credit note against the invoice does not prove the RETURNED line
--      was the line credited, so the honest structural test is the one this query
--      uses.  Budget ~2% noise on Oil's work list and ~0.3% on Mart's.  The bigger,
--      unmeasurable route stays the standalone note (trap: HONEST LIMIT, above).
--
--  14. RET_DOCS_NO_CN_BILLED rounds 3 Mart documents the generous way.  A return can
--      cite more than one base delivery (Oil 2, Mart 8, Bev 0 of them do).  When those
--      deliveries disagree about whether they were invoiced, DLV_INVOICED takes MAX, so
--      the return counts as BILLED.  Exactly 3 Mart returns are affected; Oil and Bev
--      have none.  Immaterial, but it is a choice, not an accident.
--
--  15. AN EMPTY BOOK RETURNS A ROW, NOT AN ERROR.  Run against a date before any
--      return exists (tested at {{ASOF}} = 2024-10-01 on all three schemas) the query
--      still emits the TOTAL row with RET_DOCS = 0 and NULL in every SUM-derived
--      column, plus whatever CLASS/MONTH rows the sales side produces.  The dashboard
--      renders NULL as an em dash, so the page reads "no returns" rather than "zero
--      rupees".  Nothing throws.
--
--  Also confirmed, so nobody re-attacks them: ORDN."TransId" is unique per live return
--  in all three books (1732 / 1640 / 28 rows, 1732 / 1640 / 28 distinct), so the JDT1
--  join cannot fan; every journal reached this way is OJDT."TransType" = 16, so no
--  foreign entry leaks into RET_STOCK_COST; no JDT1 line on them carries a negative
--  debit or credit, and "IntrnMatch" = 0 / "Closed" = 'N' on 100% of them, so SAP's
--  internal reconciliation is unused here as it is elsewhere at JIVO; the section reads
--  no ORCT / OVPM / "OpenBal" column at all, so the unapplied-money double-subtraction
--  trap does not apply to it; and the whole statement runs in about 1.7 s per company.
-- ---------------------------------------------------------------------------------
WITH RET AS (
  SELECT h."DocEntry"   AS DOC_ENTRY,
         h."DocDate"    AS DOC_DATE,
         h."DocStatus"  AS DOC_STATUS,
         h."CardCode"   AS CARD_CODE,
         IFNULL(c."CardName", h."CardName") AS CARD_NAME,
         CASE WHEN UPPER(IFNULL(g."GroupName",'')) LIKE '%BRANCH%'        THEN 'BRANCH'
              WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE '%JIVO%' THEN 'INTERCOMPANY'
              ELSE 'EXTERNAL' END AS PARTY_CLASS,
         CAST(h."DocTotal" AS DOUBLE) AS GROSS_AMT,
         CAST(h."VatSum"   AS DOUBLE) AS GST_AMT,
         h."TransId"    AS TRANS_ID
  FROM {{SCHEMA}}.ORDN h
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode"  = h."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode"
                             AND g."GroupType" = c."CardType"
  WHERE h."CANCELED" = 'N'
    AND h."DocDate" <= DATE'{{ASOF}}'
    AND h."DocDate" <> DATE'2024-09-30'          -- trap 10; no return note lands here anyway
),
-- quantity split by unit of measure (trap 3)
QTY AS (
  SELECT l."DocEntry" AS DOC_ENTRY,
         SUM(CASE WHEN IFNULL(l."unitMsr",'PCS') = 'PCS'
                  THEN CAST(l."Quantity" AS DOUBLE) ELSE 0 END) AS QTY_PCS,
         SUM(CASE WHEN IFNULL(l."unitMsr",'PCS') = 'PCS'
                  THEN 0 ELSE CAST(l."Quantity" AS DOUBLE) END) AS QTY_OTHER
  FROM {{SCHEMA}}.RDN1 l
  GROUP BY l."DocEntry"
),
-- base delivery, and whether that delivery was ever invoiced (traps 8 and 9)
DLVBASE AS (
  SELECT DISTINCT l."DocEntry" AS DOC_ENTRY, l."BaseEntry" AS DLN
  FROM {{SCHEMA}}.RDN1 l WHERE l."BaseType" = 15
),
DLVINV AS (
  SELECT DISTINCT l."BaseEntry" AS DLN
  FROM {{SCHEMA}}.INV1 l
  JOIN {{SCHEMA}}.OINV n ON n."DocEntry" = l."DocEntry"
  WHERE l."BaseType" = 15 AND n."CANCELED" = 'N' AND n."DocDate" <= DATE'{{ASOF}}'
),
RDLV AS (
  SELECT d.DOC_ENTRY, 1 AS FROM_DELIVERY,
         MAX(CASE WHEN i.DLN IS NULL THEN 0 ELSE 1 END) AS DLV_INVOICED
  FROM DLVBASE d LEFT JOIN DLVINV i ON i.DLN = d.DLN
  GROUP BY d.DOC_ENTRY
),
-- stock value pushed back into inventory by the return's own journal entry (trap 2)
COST AS (
  SELECT j."TransId" AS TRANS_ID, SUM(CAST(j."Debit" AS DOUBLE)) AS STOCK_COST
  FROM {{SCHEMA}}.JDT1 j
  WHERE j."TransId" IN (SELECT "TransId" FROM {{SCHEMA}}.ORDN
                        WHERE "CANCELED" = 'N' AND "TransId" IS NOT NULL
                          AND "DocDate" <= DATE'{{ASOF}}')
  GROUP BY j."TransId"
),
-- every live return -> live credit note link (traps 4 and 5)
RCN AS (
  SELECT DISTINCT l."BaseEntry" AS DOC_ENTRY, l."DocEntry" AS CN_ENTRY
  FROM {{SCHEMA}}.RIN1 l
  JOIN {{SCHEMA}}.ORIN n ON n."DocEntry" = l."DocEntry"
  WHERE l."BaseType" = 16 AND n."CANCELED" = 'N' AND n."DocDate" <= DATE'{{ASOF}}'
),
-- credit-note value allocated at LINE level, never from the ORIN header (trap 5)
CN AS (
  SELECT l."BaseEntry" AS DOC_ENTRY, SUM(CAST(l."LineTotal" AS DOUBLE)) AS CN_NET
  FROM {{SCHEMA}}.RIN1 l
  JOIN {{SCHEMA}}.ORIN n ON n."DocEntry" = l."DocEntry"
  WHERE l."BaseType" = 16 AND n."CANCELED" = 'N' AND n."DocDate" <= DATE'{{ASOF}}'
  GROUP BY l."BaseEntry"
),
R AS (
  SELECT r.DOC_ENTRY, r.DOC_DATE, r.DOC_STATUS, r.CARD_CODE, r.CARD_NAME, r.PARTY_CLASS,
         r.GROSS_AMT, r.GST_AMT,
         IFNULL(q.QTY_PCS, 0)       AS QTY_PCS,
         IFNULL(q.QTY_OTHER, 0)     AS QTY_OTHER,
         IFNULL(d.FROM_DELIVERY, 0) AS FROM_DELIVERY,
         IFNULL(d.DLV_INVOICED, 0)  AS DLV_INVOICED,
         IFNULL(k.STOCK_COST, 0)    AS STOCK_COST,
         IFNULL(cn.CN_NET, 0)       AS CN_NET,
         CASE WHEN cn.DOC_ENTRY IS NULL THEN 0 ELSE 1 END AS HAS_CN
  FROM RET r
  LEFT JOIN QTY  q  ON q.DOC_ENTRY  = r.DOC_ENTRY
  LEFT JOIN RDLV d  ON d.DOC_ENTRY  = r.DOC_ENTRY
  LEFT JOIN COST k  ON k.TRANS_ID   = r.TRANS_ID
  LEFT JOIN CN   cn ON cn.DOC_ENTRY = r.DOC_ENTRY
),
-- credit-note links carrying the scope keys, for an exact COUNT(DISTINCT) (trap 5)
RCNK AS (
  SELECT x.CN_ENTRY, r.PARTY_CLASS, TO_VARCHAR(r.DOC_DATE,'YYYY-MM') AS MTH, r.CARD_CODE
  FROM RCN x JOIN RET r ON r.DOC_ENTRY = x.DOC_ENTRY
),
-- sales denominator: invoices net of GST, ex-cancelled, ex-migration (traps 10, 11)
SAL AS (
  SELECT h."DocDate"  AS DOC_DATE,
         h."CardCode" AS CARD_CODE,
         CASE WHEN UPPER(IFNULL(g."GroupName",'')) LIKE '%BRANCH%'        THEN 'BRANCH'
              WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE '%JIVO%' THEN 'INTERCOMPANY'
              ELSE 'EXTERNAL' END AS PARTY_CLASS,
         CAST(h."DocTotal" AS DOUBLE) - CAST(h."VatSum" AS DOUBLE) AS NET_AMT
  FROM {{SCHEMA}}.OINV h
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode"  = h."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode"
                             AND g."GroupType" = c."CardType"
  WHERE h."CANCELED" = 'N'
    AND h."DocDate" <= DATE'{{ASOF}}'
    AND h."DocDate" <> DATE'2024-09-30'
),
S_TOT AS (SELECT SUM(NET_AMT) NET FROM SAL),
S_CLS AS (SELECT PARTY_CLASS K, SUM(NET_AMT) NET FROM SAL GROUP BY PARTY_CLASS),
S_MTH AS (SELECT TO_VARCHAR(DOC_DATE,'YYYY-MM') K, SUM(NET_AMT) NET FROM SAL GROUP BY TO_VARCHAR(DOC_DATE,'YYYY-MM')),
S_CUS AS (SELECT CARD_CODE K, SUM(NET_AMT) NET FROM SAL GROUP BY CARD_CODE),
C_TOT AS (SELECT COUNT(DISTINCT CN_ENTRY) CND FROM RCNK),
C_CLS AS (SELECT PARTY_CLASS K, COUNT(DISTINCT CN_ENTRY) CND FROM RCNK GROUP BY PARTY_CLASS),
C_MTH AS (SELECT MTH K, COUNT(DISTINCT CN_ENTRY) CND FROM RCNK GROUP BY MTH),
C_CUS AS (SELECT CARD_CODE K, COUNT(DISTINCT CN_ENTRY) CND FROM RCNK GROUP BY CARD_CODE),
-- ---- aggregates (one shared measure list, see the generator note in notes/) --------
R_TOT AS (
  SELECT
         COUNT(*) D,
         SUM(CASE WHEN GROSS_AMT = 0 THEN 1 ELSE 0 END) DZERO,
         SUM(CASE WHEN DOC_STATUS = 'O' THEN 1 ELSE 0 END) DOPEN,
         SUM(FROM_DELIVERY) DDLN,
         SUM(QTY_PCS) QP, SUM(QTY_OTHER) QO,
         SUM(GROSS_AMT - GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(STOCK_COST) CST,
         SUM(CASE WHEN HAS_CN = 0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN = 0 AND DLV_INVOICED = 1 THEN 1 ELSE 0 END) DNOCNB,
         SUM(CASE WHEN HAS_CN = 0 THEN QTY_PCS ELSE 0 END) QPNOCN,
         SUM(CASE WHEN HAS_CN = 0 THEN STOCK_COST ELSE 0 END) CSTNOCN,
         SUM(CN_NET) CNN
  FROM R
),
R_CLS AS (
  SELECT
         PARTY_CLASS K,
         COUNT(*) D,
         SUM(CASE WHEN GROSS_AMT = 0 THEN 1 ELSE 0 END) DZERO,
         SUM(CASE WHEN DOC_STATUS = 'O' THEN 1 ELSE 0 END) DOPEN,
         SUM(FROM_DELIVERY) DDLN,
         SUM(QTY_PCS) QP, SUM(QTY_OTHER) QO,
         SUM(GROSS_AMT - GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(STOCK_COST) CST,
         SUM(CASE WHEN HAS_CN = 0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN = 0 AND DLV_INVOICED = 1 THEN 1 ELSE 0 END) DNOCNB,
         SUM(CASE WHEN HAS_CN = 0 THEN QTY_PCS ELSE 0 END) QPNOCN,
         SUM(CASE WHEN HAS_CN = 0 THEN STOCK_COST ELSE 0 END) CSTNOCN,
         SUM(CN_NET) CNN
  FROM R
  GROUP BY PARTY_CLASS
),
R_MTH AS (
  SELECT
         TO_VARCHAR(DOC_DATE,'YYYY-MM') K,
         COUNT(*) D,
         SUM(CASE WHEN GROSS_AMT = 0 THEN 1 ELSE 0 END) DZERO,
         SUM(CASE WHEN DOC_STATUS = 'O' THEN 1 ELSE 0 END) DOPEN,
         SUM(FROM_DELIVERY) DDLN,
         SUM(QTY_PCS) QP, SUM(QTY_OTHER) QO,
         SUM(GROSS_AMT - GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(STOCK_COST) CST,
         SUM(CASE WHEN HAS_CN = 0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN = 0 AND DLV_INVOICED = 1 THEN 1 ELSE 0 END) DNOCNB,
         SUM(CASE WHEN HAS_CN = 0 THEN QTY_PCS ELSE 0 END) QPNOCN,
         SUM(CASE WHEN HAS_CN = 0 THEN STOCK_COST ELSE 0 END) CSTNOCN,
         SUM(CN_NET) CNN
  FROM R
  GROUP BY TO_VARCHAR(DOC_DATE,'YYYY-MM')
),
R_CUS AS (
  SELECT
         CARD_CODE K,
         COUNT(*) D,
         SUM(CASE WHEN GROSS_AMT = 0 THEN 1 ELSE 0 END) DZERO,
         SUM(CASE WHEN DOC_STATUS = 'O' THEN 1 ELSE 0 END) DOPEN,
         SUM(FROM_DELIVERY) DDLN,
         SUM(QTY_PCS) QP, SUM(QTY_OTHER) QO,
         SUM(GROSS_AMT - GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(STOCK_COST) CST,
         SUM(CASE WHEN HAS_CN = 0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN = 0 AND DLV_INVOICED = 1 THEN 1 ELSE 0 END) DNOCNB,
         SUM(CASE WHEN HAS_CN = 0 THEN QTY_PCS ELSE 0 END) QPNOCN,
         SUM(CASE WHEN HAS_CN = 0 THEN STOCK_COST ELSE 0 END) CSTNOCN,
         SUM(CN_NET) CNN
         , MAX(CARD_NAME) LBL, MAX(PARTY_CLASS) CLS
  FROM R
  GROUP BY CARD_CODE
),
R_CN AS (
  SELECT
         CASE WHEN HAS_CN = 1 THEN 'HAS_CREDIT_NOTE' ELSE 'NO_CREDIT_NOTE' END K,
         COUNT(*) D,
         SUM(CASE WHEN GROSS_AMT = 0 THEN 1 ELSE 0 END) DZERO,
         SUM(CASE WHEN DOC_STATUS = 'O' THEN 1 ELSE 0 END) DOPEN,
         SUM(FROM_DELIVERY) DDLN,
         SUM(QTY_PCS) QP, SUM(QTY_OTHER) QO,
         SUM(GROSS_AMT - GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(STOCK_COST) CST,
         SUM(CASE WHEN HAS_CN = 0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN = 0 AND DLV_INVOICED = 1 THEN 1 ELSE 0 END) DNOCNB,
         SUM(CASE WHEN HAS_CN = 0 THEN QTY_PCS ELSE 0 END) QPNOCN,
         SUM(CASE WHEN HAS_CN = 0 THEN STOCK_COST ELSE 0 END) CSTNOCN,
         SUM(CN_NET) CNN
         , MAX(HAS_CN) HC
  FROM R
  GROUP BY CASE WHEN HAS_CN = 1 THEN 'HAS_CREDIT_NOTE' ELSE 'NO_CREDIT_NOTE' END
),
R_WHY AS (
  SELECT
         CASE WHEN FROM_DELIVERY = 0 THEN 'STANDALONE_NO_LINK'
              WHEN DLV_INVOICED = 1 THEN 'FROM_DELIVERY_INVOICED'
              ELSE 'FROM_DELIVERY_UNBILLED' END K,
         COUNT(*) D,
         SUM(CASE WHEN GROSS_AMT = 0 THEN 1 ELSE 0 END) DZERO,
         SUM(CASE WHEN DOC_STATUS = 'O' THEN 1 ELSE 0 END) DOPEN,
         SUM(FROM_DELIVERY) DDLN,
         SUM(QTY_PCS) QP, SUM(QTY_OTHER) QO,
         SUM(GROSS_AMT - GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(STOCK_COST) CST,
         SUM(CASE WHEN HAS_CN = 0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN = 0 AND DLV_INVOICED = 1 THEN 1 ELSE 0 END) DNOCNB,
         SUM(CASE WHEN HAS_CN = 0 THEN QTY_PCS ELSE 0 END) QPNOCN,
         SUM(CASE WHEN HAS_CN = 0 THEN STOCK_COST ELSE 0 END) CSTNOCN,
         SUM(CN_NET) CNN
  FROM R WHERE HAS_CN = 0
  GROUP BY CASE WHEN FROM_DELIVERY = 0 THEN 'STANDALONE_NO_LINK'
              WHEN DLV_INVOICED = 1 THEN 'FROM_DELIVERY_INVOICED'
              ELSE 'FROM_DELIVERY_UNBILLED' END
),
R_CUS_TOP AS (
  SELECT * FROM (SELECT x.*, ROW_NUMBER() OVER (ORDER BY x.CST DESC, x.D DESC, x.K) RN FROM R_CUS x)
  WHERE RN <= 40
)
SELECT * FROM (
  SELECT 'TOTAL' AS SCOPE, 'ALL' AS GRP_KEY, 'All customer returns' AS GRP_LABEL, '1' AS SORT_KEY,
         t.D AS RET_DOCS, t.DZERO AS RET_DOCS_ZERO_VALUE, t.DOPEN AS RET_DOCS_OPEN,
         t.DDLN AS RET_DOCS_FROM_DELIVERY,
         ROUND(t.QP,3) AS RET_QTY_PCS, ROUND(t.QO,3) AS RET_QTY_OTHER_UOM,
         ROUND(t.NET,2) AS RET_NET, ROUND(t.GST,2) AS RET_GST, ROUND(t.GRS,2) AS RET_GROSS,
         ROUND(t.CST,2) AS RET_STOCK_COST,
         t.DNOCN AS RET_DOCS_NO_CN, t.DNOCNB AS RET_DOCS_NO_CN_BILLED,
         ROUND(t.QPNOCN,3) AS RET_QTY_PCS_NO_CN, ROUND(t.CSTNOCN,2) AS RET_STOCK_COST_NO_CN,
         c.CND AS CN_DOCS, ROUND(t.CNN,2) AS CN_NET, ROUND(s.NET,2) AS SALES_NET,
         CASE WHEN s.NET > 0 THEN ROUND(t.CNN/s.NET*100,4) ELSE NULL END AS CN_PCT_OF_SALES,
         CASE WHEN s.NET > 0 THEN ROUND(t.CST/s.NET*100,4) ELSE NULL END AS RET_COST_PCT_OF_SALES
  FROM R_TOT t CROSS JOIN S_TOT s CROSS JOIN C_TOT c

  UNION ALL
  SELECT 'CLASS', IFNULL(r.K,s.K), IFNULL(r.K,s.K), '2'||IFNULL(r.K,s.K),
         IFNULL(r.D,0), IFNULL(r.DZERO,0), IFNULL(r.DOPEN,0), IFNULL(r.DDLN,0),
         ROUND(IFNULL(r.QP,0),3), ROUND(IFNULL(r.QO,0),3),
         ROUND(IFNULL(r.NET,0),2), ROUND(IFNULL(r.GST,0),2), ROUND(IFNULL(r.GRS,0),2),
         ROUND(IFNULL(r.CST,0),2),
         IFNULL(r.DNOCN,0), IFNULL(r.DNOCNB,0),
         ROUND(IFNULL(r.QPNOCN,0),3), ROUND(IFNULL(r.CSTNOCN,0),2),
         IFNULL(c.CND,0), ROUND(IFNULL(r.CNN,0),2), ROUND(IFNULL(s.NET,0),2),
         CASE WHEN s.NET > 0 THEN ROUND(IFNULL(r.CNN,0)/s.NET*100,4) ELSE NULL END,
         CASE WHEN s.NET > 0 THEN ROUND(IFNULL(r.CST,0)/s.NET*100,4) ELSE NULL END
  FROM R_CLS r FULL OUTER JOIN S_CLS s ON s.K = r.K
              LEFT JOIN C_CLS c ON c.K = IFNULL(r.K,s.K)

  UNION ALL
  SELECT 'CREDIT_NOTE', r.K, r.K, '3'||r.K,
         r.D, r.DZERO, r.DOPEN, r.DDLN,
         ROUND(r.QP,3), ROUND(r.QO,3),
         ROUND(r.NET,2), ROUND(r.GST,2), ROUND(r.GRS,2), ROUND(r.CST,2),
         r.DNOCN, r.DNOCNB, ROUND(r.QPNOCN,3), ROUND(r.CSTNOCN,2),
         CASE WHEN r.HC = 1 THEN c.CND ELSE 0 END, ROUND(r.CNN,2), NULL, NULL, NULL
  FROM R_CN r CROSS JOIN C_TOT c

  UNION ALL
  SELECT 'NO_CN_REASON', r.K, r.K, '4'||r.K,
         r.D, r.DZERO, r.DOPEN, r.DDLN,
         ROUND(r.QP,3), ROUND(r.QO,3),
         ROUND(r.NET,2), ROUND(r.GST,2), ROUND(r.GRS,2), ROUND(r.CST,2),
         r.DNOCN, r.DNOCNB, ROUND(r.QPNOCN,3), ROUND(r.CSTNOCN,2),
         0, ROUND(r.CNN,2), NULL, NULL, NULL
  FROM R_WHY r

  UNION ALL
  SELECT 'MONTH', IFNULL(r.K,s.K), IFNULL(r.K,s.K), '5'||IFNULL(r.K,s.K),
         IFNULL(r.D,0), IFNULL(r.DZERO,0), IFNULL(r.DOPEN,0), IFNULL(r.DDLN,0),
         ROUND(IFNULL(r.QP,0),3), ROUND(IFNULL(r.QO,0),3),
         ROUND(IFNULL(r.NET,0),2), ROUND(IFNULL(r.GST,0),2), ROUND(IFNULL(r.GRS,0),2),
         ROUND(IFNULL(r.CST,0),2),
         IFNULL(r.DNOCN,0), IFNULL(r.DNOCNB,0),
         ROUND(IFNULL(r.QPNOCN,0),3), ROUND(IFNULL(r.CSTNOCN,0),2),
         IFNULL(c.CND,0), ROUND(IFNULL(r.CNN,0),2), ROUND(IFNULL(s.NET,0),2),
         CASE WHEN s.NET > 0 THEN ROUND(IFNULL(r.CNN,0)/s.NET*100,4) ELSE NULL END,
         CASE WHEN s.NET > 0 THEN ROUND(IFNULL(r.CST,0)/s.NET*100,4) ELSE NULL END
  FROM R_MTH r FULL OUTER JOIN S_MTH s ON s.K = r.K
              LEFT JOIN C_MTH c ON c.K = IFNULL(r.K,s.K)

  UNION ALL
  SELECT 'CUSTOMER', r.K, r.LBL||' ['||r.CLS||']', '6',
         r.D, r.DZERO, r.DOPEN, r.DDLN,
         ROUND(r.QP,3), ROUND(r.QO,3),
         ROUND(r.NET,2), ROUND(r.GST,2), ROUND(r.GRS,2), ROUND(r.CST,2),
         r.DNOCN, r.DNOCNB, ROUND(r.QPNOCN,3), ROUND(r.CSTNOCN,2),
         IFNULL(c.CND,0), ROUND(r.CNN,2), ROUND(IFNULL(s.NET,0),2),
         CASE WHEN s.NET > 0 THEN ROUND(r.CNN/s.NET*100,4) ELSE NULL END,
         CASE WHEN s.NET > 0 THEN ROUND(r.CST/s.NET*100,4) ELSE NULL END
  FROM R_CUS_TOP r LEFT JOIN S_CUS s ON s.K = r.K
                   LEFT JOIN C_CUS c ON c.K = r.K
)
ORDER BY SORT_KEY, RET_STOCK_COST DESC
LIMIT 200
