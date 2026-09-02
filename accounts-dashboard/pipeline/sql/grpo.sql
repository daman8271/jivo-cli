-- grpo.sql  --  GOODS RECEIPT PO (GRPO) REGISTER + GR/IR UNBILLED LIABILITY
--
-- Source: {{SCHEMA}}.OPDN (header, ObjType 20) + {{SCHEMA}}.PDN1 (lines), matched
--         against {{SCHEMA}}.OPCH / PCH1 (A/P invoice, ObjType 18) and
--         {{SCHEMA}}.ORPD / RPD1 (goods return, ObjType 21).
-- Everything is dated on or before {{ASOF}} and counts LIVE documents only
-- ("CANCELED" = 'N' -- three-valued, see trap 1).
--
-- ONE ROW PER (SCOPE, GRP_KEY).  Seven stacked scopes in one bounded result:
--   SCOPE = 'TOTAL'            1 row  -- company grand total (read the reconciliation here)
--   SCOPE = 'CLASS'            <=4    -- EXTERNAL / BRANCH / INTERCOMPANY / INTERNAL_ADJ
--   SCOPE = 'MONTH'            <=60   -- every month that has a GRPO (24 live at 2026-08-21)
--   SCOPE = 'BRANCH'           <=20   -- OPDN."BPLId" / "BPLName" (GST branch)
--   SCOPE = 'VENDOR'           <=60   -- biggest GRPO volume first  (the volume register)
--   SCOPE = 'VENDOR_UNBILLED'  <=60   -- biggest UNBILLED value first (the chase list)
--   SCOPE = 'WAREHOUSE'        <=60   -- PDN1."WhsCode"  (the only LINE-level scope)
-- Actual size at 2026-08-21: Oil 185 rows, Mart 95, Bev 149.  Hard-capped at 300.
--
-- WHAT "UNBILLED" MEANS -- the GR/IR number Accounts wants
--   A GRPO line is UNBILLED when PDN1."LineStatus" = 'O' AND no LIVE A/P invoice
--   line draws it: no PCH1 row with "BaseType"=20, "BaseEntry"=PDN1."DocEntry",
--   "BaseLine"=PDN1."LineNum" whose parent OPCH has "CANCELED"='N'.
--   Goods are in, the vendor bill is not booked -> unrecorded liability.
--   Ageing is on the GRPO's own "DocDate", which at JIVO IS the gate-in date
--   (correction C-0017).  A GRPO unbilled for 90+ days is a missing vendor bill.
--
-- SISTER BUCKET -- CLOSED_NOBILL_*
--   Lines with "LineStatus"='C', no live A/P invoice and no live goods return:
--   a GRPO that someone CLOSED without ever booking the vendor bill.  Not a live
--   liability, but it is an audit item and it is where the money quietly leaves.
--   Mart's 41.52 L is 7 lines over 3 GRPOs, but 40.23 L of it is ONE line:
--   GRPO 224 / DocNum 125206556, 2025-01-22, PALAK ENTERPRISES, RM0000030,
--   closed with no target.  (Verified 2026-08-21.)
--
-- MONEY UNITS: every money column is RAW INR RUPEES -- no lakh, no crore, no
--   suffix.  The dashboard divides by 1e5 / 1e7 for display.  Amounts are
--   LINE-level: NET = PDN1."LineTotal", GROSS = PDN1."GTotal", GST = GROSS-NET.
--
-- COLUMN LIST (exact, in order) -- 46 columns:
--   SCOPE, GRP_KEY, GRP_LABEL, SORT_KEY,
--   GRPO_DOCS, GRPO_LINES, GRPO_NET, GRPO_GST, GRPO_GROSS,
--   UNBILLED_DOCS, UNBILLED_LINES, UNBILLED_NET, UNBILLED_GST, UNBILLED_GROSS,
--   UB_0_30, UB_31_60, UB_61_90, UB_91_180, UB_181_365, UB_365PLUS,
--   UB_90PLUS_DOCS, UB_90PLUS_GROSS, UB_ZEROQTY_LINES, UB_ZEROQTY_GROSS,
--   OLDEST_UB_DATE, OLDEST_UB_DAYS,
--   CLOSED_NOBILL_DOCS, CLOSED_NOBILL_LINES, CLOSED_NOBILL_GROSS,
--   RETURNED_DOCS, RETURNED_LINES, RETURNED_GROSS,
--   INVOICED_DOCS, NOINV_DOCS, NOINV_GROSS,
--   INV_PAIR_DOCS, INV_SAMEDAY_DOCS, INV_SAMEDAY_PCT, INV_LAG_AVG_DAYS, INV_LAG_MED_DAYS,
--   EXT_GRPO_DOCS, EXT_GRPO_GROSS, EXT_UNBILLED_DOCS, EXT_UNBILLED_GROSS,
--   EXT_UB_90PLUS_DOCS, EXT_UB_90PLUS_GROSS
--
-- EXACT IDENTITIES (hold on every row; use them as the self-test)
--   UB_0_30 + UB_31_60 + UB_61_90 + UB_91_180 + UB_181_365 + UB_365PLUS
--       = UNBILLED_GROSS
--   UB_90PLUS_GROSS = UB_91_180 + UB_181_365 + UB_365PLUS
--   INVOICED_DOCS + NOINV_DOCS = GRPO_DOCS
--   on SCOPE='TOTAL': EXT_* equals the SCOPE='CLASS' / GRP_KEY='EXTERNAL' row
--   every scope re-totals to SCOPE='TOTAL' (CLASS, MONTH, BRANCH and WAREHOUSE all
--       verified to the paisa on all three books, 2026-08-21).  VENDOR and
--       VENDOR_UNBILLED are TOP-N (cap 60) and deliberately do NOT re-total.
--
-- Traps found and handled (full write-up in notes/grpo.md):
--   1. OPDN."CANCELED" has THREE values: 'N' live, 'Y' the cancelled original,
--      'C' the system-generated cancellation mirror.  Oil has 473 'Y' and 473 'C'
--      worth 94.63 Cr EACH; a <>'Y' filter silently double-counts them.  Only
--      'N' is kept, everywhere, including on the linked OPCH / ORPD.
--   2. PDN1."OpenQty" IS BROKEN AT JIVO.  It still equals "Quantity" on fully
--      invoiced, closed lines (Oil closed lines: Qty 101,650,373 vs OpenQty
--      101,388,812 -- 99.7%).  NEVER use it.  "OpenInvQty" IS maintained (0 on
--      closed lines) but is stated in the BASE UoM while "Quantity" is in the
--      DOCUMENT UoM -- oil RM lines read Quantity 39.04 MTS / OpenInvQty
--      42,901.056 L, factor 1098.9 -- so the two cannot be compared directly.
--      This query decides open-ness from "LineStatus" plus the live-invoice
--      link and needs no quantity arithmetic at all.
--   3. ZERO-QUANTITY LINES NEVER CLOSE.  Freight / expense GRPO lines carrying
--      "Quantity"=0 keep "LineStatus"='O' forever even after the A/P invoice is
--      booked -- verified: Oil GRPO 5956 line 0 -> live A/P invoice 625034387,
--      closed, yet the GRPO line still reads 'O'.  A naive "LineStatus"='O'
--      count therefore overstates the Oil GR/IR position by 18 documents.  The
--      live-invoice link removes them; genuinely unbilled zero-qty lines are
--      still reported separately as UB_ZEROQTY_LINES / UB_ZEROQTY_GROSS
--      (Oil 165 lines / 15.73 L, Mart 67 / 15.15 L, Bev 205 / 12.20 L -- these
--      will never self-close and need a human).
--   4. A drawn A/P invoice can itself be CANCELLED, which legitimately re-opens
--      the GRPO line (Oil GRPO 8586 -> invoice 625054210, "CANCELED"='Y').  The
--      link is therefore filtered on OPCH."CANCELED"='N', never on existence.
--   5. Header "DocStatus" is NOT used as the open test.  It disagrees with the
--      lines in BOTH directions: Oil has 3 open-header docs whose every line is
--      billed and 2 closed-header docs still carrying an open line; Bev has 3
--      such docs.  Open-ness is decided line by line.  (Different failure from
--      the OINV/OPCH one -- GRPO status is driven by document copy, not by
--      payment -- but wrong all the same.)
--   6. Branch transfers are NOT trade purchases.  JIVO's own state GST
--      registrations arrive as BRANCH vendor-group cards (Oil 759 GRPOs,
--      61.26 Cr) and sister companies appear by NAME inside ordinary purchase
--      groups (the JIVO WELLNESS / JIVO MART case).  PARTY_CLASS splits both by
--      group AND by name; nothing is dropped, everything is flagged.
--   7. HEADER "DocTotal" AND LINE "GTotal" DISAGREE, IN BOTH DIRECTIONS, AND THE
--      LINES ARE THE BETTER NUMBER.  On 2,809 of 10,640 live Oil GRPOs (26%) and
--      3,053 of 4,563 Bev GRPOs (67%) the header carries "VatSum" = 0 while the
--      lines DO carry tax, so "DocTotal" is the NET value and understates the
--      tax-inclusive receipt (Oil by 20.99 L, Bev 9.80 L, Mart 1.41 L).  Going
--      the other way, header freight (OPDN."TotalExpns", Oil 9.50 L) never
--      reaches the lines.  Net effect in Oil: lines 784.74 Cr vs header 784.64 Cr
--      (0.013%).  Money here is therefore LINE-level throughout -- which is also
--      what makes the WAREHOUSE scope comparable with the rest.
--   8. Goods returned to the vendor are not an unbilled bill.  Lines drawn to a
--      LIVE goods return (RPD1 "BaseType"=20) are excluded from both unbilled
--      buckets and counted as RETURNED_* instead.
--      BUT READ THIS BEFORE YOU USE RETURNED_*: at JIVO almost every goods
--      return is raised STANDALONE, with RPD1."BaseType" = -1 and no GRPO link
--      at all.  Live return lines by link type, 2026-08-21:
--          Oil  3 linked / 155 standalone   (4.69 L of 74.61 L)
--          Mart 1 linked / 416 standalone   (0.72 L of 125.50 L)
--          Bev  0 linked /  81 standalone   (0    of 48.73 L)
--      So RETURNED_* measures "GRPO lines a return was COPIED FROM", not "goods
--      sent back", and it is near-empty by construction.  The dashboard does not
--      render it.  Consequence for UNBILLED: a standalone return does not close
--      the GRPO line, so goods received and then sent back on a standalone
--      return stay in the GR/IR bucket.  Upper bound measured by vendor overlap
--      -- Oil 43.50 L (13 vendors), Bev 0.83 L, Mart intercompany only.  Not
--      attributable line-by-line from SAP; stated, not silently fixed.
--   9. SAP go-live 2024-09-30: 1 Oil GRPO (2.82 L) and 1 Bev GRPO (9,404) carry
--      that date -- migrated openings.  Left in, immaterial (Oil 0.004%), and
--      NEITHER is still unbilled, so the 365+ ageing bucket is not distorted by
--      the migration.  Verified 2026-08-21.
--  10. WAREHOUSE is a line attribute while an invoice lag is a document
--      property, so INV_PAIR_DOCS / INV_SAMEDAY_DOCS / INV_SAMEDAY_PCT /
--      INV_LAG_* are returned as NULL on WAREHOUSE rows instead of a wrong zero.
--  11. AS-OF CONSISTENCY.  The A/P-invoice and goods-return links are capped at
--      {{ASOF}} too, not just the GRPO.  Without it a month-end run is settled by
--      bills booked afterwards: at ASOF 2026-05-31 Oil read 3.39 L unbilled with
--      the link uncapped versus 3.74 L capped (-9.3%).  At ASOF = today the fix
--      is a no-op -- no live OPCH or ORPD in any book carries a future DocDate.
--      STILL NOT FIXED, AND NOT FIXABLE FROM THESE TABLES: PDN1."LineStatus" is
--      a CURRENT-STATE flag with no history, so a line that was open at a past
--      as-of and has since been billed reads 'C' and vanishes.  Measured at
--      ASOF 2026-05-31: Oil 67.69 L / 282 lines, Bev 8.81 L / 189 lines invisible
--      that way.  TREAT THIS SECTION AS A TODAY DASHBOARD.  A historical
--      --as-of run understates GR/IR and must not be used for a month-end
--      provision without saying so.
--  12. THE HEADLINE IS CONTAMINATED BY JIVO'S OWN CARDS, so every headline figure
--      now ships an EXTERNAL-only twin (EXT_*).  At 2026-08-21 the plain totals
--      are: Bev UNBILLED_GROSS 4.19 Cr of which 2.85 Cr (68%) is the internal
--      card VENDA001306 "STOCK GOODS RECEIPTS" -- 2.82 Cr of it a single line,
--      GRPO 2026078243 / RM0000199, which will never receive a vendor bill;
--      Mart UNBILLED_GROSS 84.19 L of which 67.37 L (80%) is VENDA000001
--      "JIVO WELLNESS PVT LTD" (intercompany, sitting in group 106 PURCHASE, so
--      only the NAME test catches it).  Oil is clean (2,016 non-external).
--      Nothing is dropped: UNBILLED_* still totals everything, EXT_UNBILLED_*
--      is the trade number, and CLASS shows the split.
WITH
BILLED AS (
  -- every GRPO line drawn by a LIVE A/P invoice.  Trap 4: cancelled ones excluded.
  SELECT DISTINCT p."BaseEntry" AS DOC_ENTRY, p."BaseLine" AS LINE_NUM
  FROM {{SCHEMA}}.PCH1 p
  JOIN {{SCHEMA}}.OPCH i ON i."DocEntry" = p."DocEntry"
  WHERE p."BaseType" = 20 AND i."CANCELED" = 'N'
    AND i."DocDate" <= DATE'{{ASOF}}'          -- trap 11: as-of consistency
),
RETURNED AS (
  -- every GRPO line sent back to the vendor on a LIVE goods return (trap 8)
  SELECT DISTINCT r."BaseEntry" AS DOC_ENTRY, r."BaseLine" AS LINE_NUM
  FROM {{SCHEMA}}.RPD1 r
  JOIN {{SCHEMA}}.ORPD rh ON rh."DocEntry" = r."DocEntry"
  WHERE r."BaseType" = 20 AND rh."CANCELED" = 'N'
    AND rh."DocDate" <= DATE'{{ASOF}}'         -- trap 11
),
INVLINK AS (
  -- doc level: how many live A/P invoices a GRPO fed, and the FIRST one's dates.
  -- FIRST_INV_DATE is the C-0017 test: is it the GRPO's own DocDate?
  SELECT p."BaseEntry"                  AS DOC_ENTRY,
         COUNT(DISTINCT i."DocEntry")   AS INV_COUNT,
         MIN(i."DocDate")               AS FIRST_INV_DATE
  FROM {{SCHEMA}}.PCH1 p
  JOIN {{SCHEMA}}.OPCH i ON i."DocEntry" = p."DocEntry"
  WHERE p."BaseType" = 20 AND i."CANCELED" = 'N'
    AND i."DocDate" <= DATE'{{ASOF}}'          -- trap 11
  GROUP BY p."BaseEntry"
),
HDR AS (
  SELECT h."DocEntry"                          AS DOC_ENTRY,
         h."DocDate"                           AS DOC_DATE,
         h."DocStatus"                         AS DOC_STATUS,
         h."CardCode"                          AS CARD_CODE,
         IFNULL(c."CardName", h."CardName")    AS CARD_NAME,
         CASE WHEN UPPER(IFNULL(g."GroupName",''))            LIKE '%BRANCH%'      THEN 'BRANCH'
              WHEN UPPER(IFNULL(c."CardName",h."CardName"))   LIKE '%JIVO%'        THEN 'INTERCOMPANY'
              WHEN UPPER(IFNULL(c."CardName",h."CardName"))   LIKE 'STOCK GOODS%'  THEN 'INTERNAL_ADJ'
              ELSE 'EXTERNAL' END              AS PARTY_CLASS,
         IFNULL(TO_VARCHAR(h."BPLId"),'?')     AS BPL_ID,
         IFNULL(h."BPLName",'(no branch)')     AS BPL_NAME,
         DAYS_BETWEEN(h."DocDate", DATE'{{ASOF}}') AS AGE_DAYS
  FROM {{SCHEMA}}.OPDN h
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode"  = h."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode"
                             AND g."GroupType" = c."CardType"
  WHERE h."CANCELED" = 'N' AND h."DocDate" <= DATE'{{ASOF}}'
),
L AS (   -- raw line fact: one row per GRPO line, header attributes denormalised on
  SELECT hd.DOC_ENTRY, hd.DOC_DATE, hd.DOC_STATUS, hd.CARD_CODE, hd.CARD_NAME,
         hd.PARTY_CLASS, hd.BPL_ID, hd.BPL_NAME, hd.AGE_DAYS,
         IFNULL(l."WhsCode",'(none)')                                  AS WHS,
         CAST(l."LineTotal" AS DOUBLE)                                 AS NET,
         CAST(l."GTotal" AS DOUBLE) - CAST(l."LineTotal" AS DOUBLE)    AS GST,
         CAST(l."GTotal" AS DOUBLE)                                    AS GROSS,
         CASE WHEN CAST(l."Quantity" AS DOUBLE) = 0 THEN 1 ELSE 0 END  AS ZERO_QTY,
         CASE WHEN rt.DOC_ENTRY IS NOT NULL                       THEN 1 ELSE 0 END AS RETURNED,
         CASE WHEN rt.DOC_ENTRY IS NULL AND b.DOC_ENTRY IS NULL
               AND l."LineStatus" = 'O'                            THEN 1 ELSE 0 END AS UB,
         CASE WHEN rt.DOC_ENTRY IS NULL AND b.DOC_ENTRY IS NULL
               AND l."LineStatus" = 'C'                            THEN 1 ELSE 0 END AS CNB,
         iv.INV_COUNT, iv.FIRST_INV_DATE
  FROM HDR hd
  JOIN {{SCHEMA}}.PDN1 l ON l."DocEntry" = hd.DOC_ENTRY
  LEFT JOIN BILLED   b  ON b.DOC_ENTRY  = l."DocEntry" AND b.LINE_NUM  = l."LineNum"
  LEFT JOIN RETURNED rt ON rt.DOC_ENTRY = l."DocEntry" AND rt.LINE_NUM = l."LineNum"
  LEFT JOIN INVLINK  iv ON iv.DOC_ENTRY = hd.DOC_ENTRY
),
LF AS (  -- line fact with every per-row measure spelled out once
  SELECT DOC_ENTRY, DOC_DATE, DOC_STATUS, CARD_CODE, CARD_NAME, PARTY_CLASS,
         BPL_ID, BPL_NAME, AGE_DAYS, WHS, NET, GST, GROSS,
         1                          AS N_LINES,
         UB                         AS UB_LINES,
         UB * NET                   AS UB_NET,
         UB * GST                   AS UB_GST,
         UB * GROSS                 AS UB_GROSS,
         UB * ZERO_QTY              AS UB_ZQ_LINES,
         UB * ZERO_QTY * GROSS      AS UB_ZQ_GROSS,
         CNB                        AS CNB_LINES,
         CNB * GROSS                AS CNB_GROSS,
         RETURNED                   AS RET_LINES,
         RETURNED * GROSS           AS RET_GROSS,
         CASE WHEN UB  = 1 THEN DOC_DATE  END                       AS UB_DATE,
         CASE WHEN UB  = 1 THEN DOC_ENTRY END                       AS UB_DOC,
         CASE WHEN CNB = 1 THEN DOC_ENTRY END                       AS CNB_DOC,
         CASE WHEN RETURNED = 1 THEN DOC_ENTRY END                  AS RET_DOC,
         CASE WHEN UB = 1 AND AGE_DAYS <=  30              THEN GROSS ELSE 0 END AS UB_0_30,
         CASE WHEN UB = 1 AND AGE_DAYS BETWEEN  31 AND  60 THEN GROSS ELSE 0 END AS UB_31_60,
         CASE WHEN UB = 1 AND AGE_DAYS BETWEEN  61 AND  90 THEN GROSS ELSE 0 END AS UB_61_90,
         CASE WHEN UB = 1 AND AGE_DAYS BETWEEN  91 AND 180 THEN GROSS ELSE 0 END AS UB_91_180,
         CASE WHEN UB = 1 AND AGE_DAYS BETWEEN 181 AND 365 THEN GROSS ELSE 0 END AS UB_181_365,
         CASE WHEN UB = 1 AND AGE_DAYS >  365              THEN GROSS ELSE 0 END AS UB_365PLUS,
         CASE WHEN UB = 1 AND AGE_DAYS >   90              THEN GROSS ELSE 0 END AS UB_90P_GROSS,
         CASE WHEN UB = 1 AND AGE_DAYS >   90 THEN DOC_ENTRY END                 AS UB_90P_DOC,
         CASE WHEN INV_COUNT > 0     THEN DOC_ENTRY END                          AS INV_DOC,
         CASE WHEN INV_COUNT IS NULL THEN DOC_ENTRY END                          AS NOINV_DOC,
         CASE WHEN INV_COUNT IS NULL THEN GROSS ELSE 0 END                       AS NOINV_GROSS,
         INV_COUNT, FIRST_INV_DATE
  FROM L
),
DF AS (  -- DOCUMENT-level fact: the SAME measure vocabulary, one row per GRPO.
         -- Only this level carries the C-0017 invoice-lag numbers, because a lag
         -- is a property of the document and not of any one line (trap 10).
  SELECT DOC_ENTRY,
         MIN(DOC_DATE) AS DOC_DATE, MIN(CARD_CODE) AS CARD_CODE, MIN(CARD_NAME) AS CARD_NAME,
         MIN(PARTY_CLASS) AS PARTY_CLASS, MIN(BPL_ID) AS BPL_ID, MIN(BPL_NAME) AS BPL_NAME,
         SUM(N_LINES) AS N_LINES, SUM(NET) AS NET, SUM(GST) AS GST, SUM(GROSS) AS GROSS,
         SUM(UB_LINES) AS UB_LINES, SUM(UB_NET) AS UB_NET, SUM(UB_GST) AS UB_GST,
         SUM(UB_GROSS) AS UB_GROSS, SUM(UB_ZQ_LINES) AS UB_ZQ_LINES, SUM(UB_ZQ_GROSS) AS UB_ZQ_GROSS,
         SUM(CNB_LINES) AS CNB_LINES, SUM(CNB_GROSS) AS CNB_GROSS,
         SUM(RET_LINES) AS RET_LINES, SUM(RET_GROSS) AS RET_GROSS,
         MIN(UB_DATE) AS UB_DATE, MIN(UB_DOC) AS UB_DOC, MIN(CNB_DOC) AS CNB_DOC, MIN(RET_DOC) AS RET_DOC,
         SUM(UB_0_30) AS UB_0_30, SUM(UB_31_60) AS UB_31_60, SUM(UB_61_90) AS UB_61_90,
         SUM(UB_91_180) AS UB_91_180, SUM(UB_181_365) AS UB_181_365, SUM(UB_365PLUS) AS UB_365PLUS,
         SUM(UB_90P_GROSS) AS UB_90P_GROSS, MIN(UB_90P_DOC) AS UB_90P_DOC,
         MIN(INV_DOC) AS INV_DOC, MIN(NOINV_DOC) AS NOINV_DOC, SUM(NOINV_GROSS) AS NOINV_GROSS,
         MIN(CASE WHEN INV_COUNT > 0 THEN DAYS_BETWEEN(DOC_DATE, FIRST_INV_DATE) END) AS INV_LAG,
         MIN(CASE WHEN INV_COUNT > 0 AND DAYS_BETWEEN(DOC_DATE, FIRST_INV_DATE) = 0
                  THEN DOC_ENTRY END) AS SAMEDAY_DOC
  FROM LF
  GROUP BY DOC_ENTRY
),
SCOPES AS (
  -- six DOCUMENT-level scopes, stacked; WAREHOUSE is added from the line fact below
              SELECT 'TOTAL'           AS S, '1' AS SK FROM DUMMY
  UNION ALL   SELECT 'CLASS',               '2'        FROM DUMMY
  UNION ALL   SELECT 'MONTH',               '3'        FROM DUMMY
  UNION ALL   SELECT 'BRANCH',              '4'        FROM DUMMY
  UNION ALL   SELECT 'VENDOR',              '5'        FROM DUMMY
  UNION ALL   SELECT 'VENDOR_UNBILLED',     '6'        FROM DUMMY
),
KEYED AS (
  SELECT s.S AS SCOPE,
         CASE s.S WHEN 'TOTAL'  THEN 'ALL'
                  WHEN 'CLASS'  THEN d.PARTY_CLASS
                  WHEN 'MONTH'  THEN TO_VARCHAR(d.DOC_DATE,'YYYY-MM')
                  WHEN 'BRANCH' THEN d.BPL_ID
                  ELSE d.CARD_CODE END                                  AS GRP_KEY,
         CASE s.S WHEN 'TOTAL'  THEN 'All GRPOs'
                  WHEN 'CLASS'  THEN d.PARTY_CLASS
                  WHEN 'MONTH'  THEN TO_VARCHAR(d.DOC_DATE,'YYYY-MM')
                  WHEN 'BRANCH' THEN UPPER(d.BPL_NAME)   -- OPDN."BPLName" is stored per DOCUMENT and its
                                                         -- capitalisation drifted ('FACTORY' vs 'Factory'),
                                                         -- which split branch 2 into two rows until upper-cased
                  ELSE d.CARD_NAME || ' [' || d.PARTY_CLASS || ']' END  AS GRP_LABEL,
         s.SK AS SORT_KEY,
         d.DOC_ENTRY, d.N_LINES, d.NET, d.GST, d.GROSS,
         d.UB_LINES, d.UB_NET, d.UB_GST, d.UB_GROSS, d.UB_ZQ_LINES, d.UB_ZQ_GROSS,
         d.CNB_LINES, d.CNB_GROSS, d.RET_LINES, d.RET_GROSS,
         d.UB_DATE, d.UB_DOC, d.CNB_DOC, d.RET_DOC,
         d.UB_0_30, d.UB_31_60, d.UB_61_90, d.UB_91_180, d.UB_181_365, d.UB_365PLUS,
         d.UB_90P_GROSS, d.UB_90P_DOC, d.INV_DOC, d.NOINV_DOC, d.NOINV_GROSS,
         d.INV_LAG, d.SAMEDAY_DOC, d.PARTY_CLASS AS PCLASS
  FROM DF d CROSS JOIN SCOPES s
),
KEYED_W AS (   -- WAREHOUSE: line-level, invoice-lag columns deliberately NULL (trap 10)
  SELECT 'WAREHOUSE' AS SCOPE, f.WHS AS GRP_KEY, f.WHS AS GRP_LABEL, '7' AS SORT_KEY,
         f.DOC_ENTRY, f.N_LINES, f.NET, f.GST, f.GROSS,
         f.UB_LINES, f.UB_NET, f.UB_GST, f.UB_GROSS, f.UB_ZQ_LINES, f.UB_ZQ_GROSS,
         f.CNB_LINES, f.CNB_GROSS, f.RET_LINES, f.RET_GROSS,
         f.UB_DATE, f.UB_DOC, f.CNB_DOC, f.RET_DOC,
         f.UB_0_30, f.UB_31_60, f.UB_61_90, f.UB_91_180, f.UB_181_365, f.UB_365PLUS,
         f.UB_90P_GROSS, f.UB_90P_DOC, f.INV_DOC, f.NOINV_DOC, f.NOINV_GROSS,
         CAST(NULL AS INTEGER) AS INV_LAG, CAST(NULL AS INTEGER) AS SAMEDAY_DOC,
         f.PARTY_CLASS AS PCLASS
  FROM LF f
),
AGG AS (
  SELECT SCOPE, GRP_KEY, GRP_LABEL, SORT_KEY,
         COUNT(DISTINCT DOC_ENTRY)                  AS GRPO_DOCS,
         SUM(N_LINES)                               AS GRPO_LINES,
         ROUND(SUM(NET),2)                          AS GRPO_NET,
         ROUND(SUM(GST),2)                          AS GRPO_GST,
         ROUND(SUM(GROSS),2)                        AS GRPO_GROSS,
         COUNT(DISTINCT UB_DOC)                     AS UNBILLED_DOCS,
         SUM(UB_LINES)                              AS UNBILLED_LINES,
         ROUND(SUM(UB_NET),2)                       AS UNBILLED_NET,
         ROUND(SUM(UB_GST),2)                       AS UNBILLED_GST,
         ROUND(SUM(UB_GROSS),2)                     AS UNBILLED_GROSS,
         ROUND(SUM(UB_0_30),2)                      AS UB_0_30,
         ROUND(SUM(UB_31_60),2)                     AS UB_31_60,
         ROUND(SUM(UB_61_90),2)                     AS UB_61_90,
         ROUND(SUM(UB_91_180),2)                    AS UB_91_180,
         ROUND(SUM(UB_181_365),2)                   AS UB_181_365,
         ROUND(SUM(UB_365PLUS),2)                   AS UB_365PLUS,
         COUNT(DISTINCT UB_90P_DOC)                 AS UB_90PLUS_DOCS,
         ROUND(SUM(UB_90P_GROSS),2)                 AS UB_90PLUS_GROSS,
         SUM(UB_ZQ_LINES)                           AS UB_ZEROQTY_LINES,
         ROUND(SUM(UB_ZQ_GROSS),2)                  AS UB_ZEROQTY_GROSS,
         TO_VARCHAR(MIN(UB_DATE),'YYYY-MM-DD')      AS OLDEST_UB_DATE,
         DAYS_BETWEEN(MIN(UB_DATE), DATE'{{ASOF}}') AS OLDEST_UB_DAYS,
         COUNT(DISTINCT CNB_DOC)                    AS CLOSED_NOBILL_DOCS,
         SUM(CNB_LINES)                             AS CLOSED_NOBILL_LINES,
         ROUND(SUM(CNB_GROSS),2)                    AS CLOSED_NOBILL_GROSS,
         COUNT(DISTINCT RET_DOC)                    AS RETURNED_DOCS,
         SUM(RET_LINES)                             AS RETURNED_LINES,
         ROUND(SUM(RET_GROSS),2)                    AS RETURNED_GROSS,
         COUNT(DISTINCT INV_DOC)                    AS INVOICED_DOCS,
         COUNT(DISTINCT NOINV_DOC)                  AS NOINV_DOCS,
         ROUND(SUM(NOINV_GROSS),2)                  AS NOINV_GROSS,
         CASE WHEN SCOPE <> 'WAREHOUSE' THEN COUNT(INV_LAG) END           AS INV_PAIR_DOCS,
         CASE WHEN SCOPE <> 'WAREHOUSE' THEN COUNT(DISTINCT SAMEDAY_DOC) END AS INV_SAMEDAY_DOCS,
         CASE WHEN SCOPE <> 'WAREHOUSE' AND COUNT(INV_LAG) > 0
              THEN ROUND(100.0 * COUNT(DISTINCT SAMEDAY_DOC) / COUNT(INV_LAG), 2) END AS INV_SAMEDAY_PCT,
         ROUND(AVG(CAST(INV_LAG AS DOUBLE)),2)      AS INV_LAG_AVG_DAYS,
         ROUND(MEDIAN(CAST(INV_LAG AS DOUBLE)),2)   AS INV_LAG_MED_DAYS,
         -- EXTERNAL-ONLY TWINS (trap 12).  The five headline figures with JIVO's
         -- own branch / sister-company / stock-adjustment cards taken out, so a
         -- KPI can quote a real trade number instead of one that is 68% internal.
         COUNT(DISTINCT CASE WHEN PCLASS = 'EXTERNAL' THEN DOC_ENTRY END)          AS EXT_GRPO_DOCS,
         ROUND(SUM(CASE WHEN PCLASS = 'EXTERNAL' THEN GROSS        ELSE 0 END),2)  AS EXT_GRPO_GROSS,
         COUNT(DISTINCT CASE WHEN PCLASS = 'EXTERNAL' THEN UB_DOC END)             AS EXT_UNBILLED_DOCS,
         ROUND(SUM(CASE WHEN PCLASS = 'EXTERNAL' THEN UB_GROSS     ELSE 0 END),2)  AS EXT_UNBILLED_GROSS,
         COUNT(DISTINCT CASE WHEN PCLASS = 'EXTERNAL' THEN UB_90P_DOC END)         AS EXT_UB_90PLUS_DOCS,
         ROUND(SUM(CASE WHEN PCLASS = 'EXTERNAL' THEN UB_90P_GROSS ELSE 0 END),2)  AS EXT_UB_90PLUS_GROSS
  FROM (SELECT * FROM KEYED UNION ALL SELECT * FROM KEYED_W) Z
  GROUP BY SCOPE, GRP_KEY, GRP_LABEL, SORT_KEY
),
RANKED AS (
  -- cap each scope independently, so a long vendor tail can never crowd out the
  -- BRANCH / WAREHOUSE rows that sort after it
  SELECT a.*,
         ROW_NUMBER() OVER (PARTITION BY SCOPE
             ORDER BY CASE WHEN SCOPE = 'VENDOR_UNBILLED' THEN IFNULL(UNBILLED_GROSS,0)
                           WHEN SCOPE = 'MONTH'           THEN 0
                           ELSE IFNULL(GRPO_GROSS,0) END DESC,
                      GRP_KEY ASC) AS RN
  FROM AGG a
)
SELECT SCOPE, GRP_KEY, GRP_LABEL, SORT_KEY,
       GRPO_DOCS, GRPO_LINES, GRPO_NET, GRPO_GST, GRPO_GROSS,
       UNBILLED_DOCS, UNBILLED_LINES, UNBILLED_NET, UNBILLED_GST, UNBILLED_GROSS,
       UB_0_30, UB_31_60, UB_61_90, UB_91_180, UB_181_365, UB_365PLUS,
       UB_90PLUS_DOCS, UB_90PLUS_GROSS, UB_ZEROQTY_LINES, UB_ZEROQTY_GROSS,
       OLDEST_UB_DATE, OLDEST_UB_DAYS,
       CLOSED_NOBILL_DOCS, CLOSED_NOBILL_LINES, CLOSED_NOBILL_GROSS,
       RETURNED_DOCS, RETURNED_LINES, RETURNED_GROSS,
       INVOICED_DOCS, NOINV_DOCS, NOINV_GROSS,
       INV_PAIR_DOCS, INV_SAMEDAY_DOCS, INV_SAMEDAY_PCT, INV_LAG_AVG_DAYS, INV_LAG_MED_DAYS,
       EXT_GRPO_DOCS, EXT_GRPO_GROSS, EXT_UNBILLED_DOCS, EXT_UNBILLED_GROSS,
       EXT_UB_90PLUS_DOCS, EXT_UB_90PLUS_GROSS
FROM RANKED
WHERE RN <= CASE SCOPE WHEN 'TOTAL'  THEN  1
                       WHEN 'CLASS'  THEN 10
                       WHEN 'MONTH'  THEN 60
                       WHEN 'BRANCH' THEN 20
                       ELSE 60 END
  AND NOT (SCOPE = 'VENDOR_UNBILLED' AND IFNULL(UNBILLED_GROSS,0) = 0)
ORDER BY SORT_KEY,
         CASE WHEN SCOPE = 'MONTH' THEN GRP_KEY END ASC,
         CASE WHEN SCOPE = 'VENDOR_UNBILLED' THEN UNBILLED_GROSS ELSE GRPO_GROSS END DESC,
         GRP_KEY
LIMIT 300
