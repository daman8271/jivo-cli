-- return-note-detail.sql  --  RETURN NOTE REGISTER (customer returns coming back INTO JIVO)
--
-- Source: {{SCHEMA}}.ORDN (header, ObjType 16) + {{SCHEMA}}.RDN1 (lines), enriched with
--         the base delivery ({{SCHEMA}}.ODLN), whether that delivery was invoiced
--         ({{SCHEMA}}.INV1/OINV), the follow-on A/R credit notes ({{SCHEMA}}.RIN1/ORIN)
--         and the stock value the return pushed back into inventory ({{SCHEMA}}.JDT1).
--
-- ONE ROW PER RETURN NOTE DOCUMENT, dated on or before {{ASOF}}.
-- EXCEPTION-FIRST, NOT NEWEST-FIRST.  The population is too big for a full register
-- (Oil 2031 / Mart 1844 / Bev 184 documents at 2026-08-21), so rows are ranked by
-- EXC_RANK and hard-capped at 500.  The cap therefore bites the ordinary, fully
-- credited returns first and never hides a work-list row:
--   EXC_RANK 1 = LIVE, no live credit note, base delivery WAS invoiced
--                -> customer was billed, goods came back, no credit raised.  ACT.
--   EXC_RANK 2 = LIVE, no live credit note, NO base link at all
--                -> unanswerable from structure; check by hand.  THE WORK LIST.
--   EXC_RANK 3 = LIVE, no live credit note, base delivery never invoiced
--                -> no credit is due.  Shown so nobody double-counts it as an exception.
--   EXC_RANK 4 = everything else (credited returns, cancelled docs, cancellation mirrors)
-- Within a rank: biggest stock cost first, then newest.
-- Measured 2026-08-21 (verified against return-note.sql, which agrees exactly):
--   rank 1/2/3/4 = Oil 212/115/94/1610 (2031) . Mart 912/72/385/475 (1844)
--                . Bev 3/39/17/125 (184)
-- So Oil returns all 421 exceptions plus 79 filler rows, and Bev returns its whole
-- 184-document book.  MART OVERFLOWS: rank 1 alone is 912 rows, so the 500-cap
-- truncates INSIDE rank 1 and Mart shows no rank 2/3/4 at all.  For Mart, take the
-- counts from return-note.sql (exhaustive) and treat this file as the top-500 sample.
-- Raise the LIMIT if Accounts wants the whole Mart list.
--
-- Columns (35, in this order):
--   DOC_ENTRY, DOC_NUM, DOC_DATE, DOC_MONTH, AGE_DAYS,
--   CANCEL_STATUS (LIVE|CANCELLED|CANCELLATION_DOC), DOC_STATUS (O|C),
--   CARD_CODE, CARD_NAME, CUSTOMER_GROUP, PARTY_CLASS (EXTERNAL|BRANCH|INTERCOMPANY),
--   BRANCH_ID, BRANCH_NAME, WAREHOUSES,
--   NUM_LINES, NUM_ITEMS, QTY_PCS, QTY_OTHER_UOM,
--   NET_AMT, GST_AMT, GROSS_AMT, STOCK_COST,
--   REASON, CUSTOMER_REF,
--   BASE_DLN_COUNT, BASE_DLN_DOCNUMS, BASE_DLN_INVOICED,
--   CN_COUNT, CN_DOCNUMS, CN_FIRST_DATE, CN_NET, CN_LAG_DAYS,
--   FLAG_NO_CREDIT_NOTE, NO_CN_REASON, EXC_RANK
--
-- MONEY UNIT: raw INR RUPEES (no _L / _CR suffix), matching return-note.sql and
-- goods-return-detail.sql.  QUANTITY UNIT: PIECES.  QTY_PCS and QTY_OTHER_UOM are
-- separate because RDN1 mixes UoM (PCS/SET/KGS/NOS/LTR/MTR/DRM); NEVER add them.
--
-- Traps handled (same set as return-note.sql; full write-up in notes/return-note.md):
--   * "CANCELED" has THREE values: 'N' live, 'Y' cancelled original, 'C' the
--     system-generated cancellation mirror.  All three are kept but decoded, and
--     every flag is computed for 'N' only.
--   * Most return notes carry NO VALUE (61% of Oil's live returns have DocTotal = 0).
--     GROSS_AMT is therefore NOT the size of the return; STOCK_COST is.
--     STOCK_COST = SUM(JDT1."Debit") on the return's own journal, which lands entirely
--     on 1103xxx inventory accounts against 5000xxx COGS.  A return with no journal
--     entry shows STOCK_COST = 0 (Oil 85, Mart 152, BEV 132 OF 160 -- Bev's column is
--     not usable).
--   * The credit-note link is taken from the CREDIT-NOTE side (RIN1."BaseType"=16),
--     never RDN1."TargetType"=14: 5 live Oil returns and 3 live Bev returns still
--     point at a CANCELLED credit note and the return side would call them credited.
--     Verified: 0 live returns with a LIVE credit note are missed by this direction.
--   * The link is MANY-TO-MANY (one Oil return has 82 credit notes), so credit notes
--     are de-duplicated and aggregated, never joined row-to-row.  CN_DOCNUMS is
--     truncated to 200 characters.
--   * "BaseType"=13 (invoice) is ZERO rows in all three books -- returns never point at
--     an invoice.  Only BaseType 15 (delivery) exists, and only on ~17% of Oil returns.
--     The invoice number is typed into free text instead (414 Oil returns say "INVOICE"
--     in "Comments", in at least three incompatible formats); REASON carries "Comments"
--     VERBATIM and is deliberately NOT parsed.
--   * PARTY_CLASS is group-name THEN card-name.  A group test alone finds NOTHING:
--     0 Oil returns sit in a '%BRANCH%' group, yet CUSTA000606 "JIVO MART PVT LTD"
--     (group "DELHI") is 477 returns and 92.5% of Oil's header value.
--   * "DocStatus"='O' is not reliable at JIVO; DOC_STATUS is a diagnostic only.
WITH RET AS (
  SELECT h."DocEntry"                       AS DOC_ENTRY,
         h."DocNum"                         AS DOC_NUM,
         h."DocDate"                        AS DOC_DATE,
         h."DocStatus"                      AS DOC_STATUS,
         h."CANCELED"                       AS CANCEL_FLAG,
         h."CardCode"                       AS CARD_CODE,
         IFNULL(c."CardName", h."CardName") AS CARD_NAME,
         IFNULL(g."GroupName", '')          AS CUSTOMER_GROUP,
         h."BPLId"                          AS BRANCH_ID,
         h."BPLName"                        AS BRANCH_NAME,
         CAST(h."DocTotal" AS DOUBLE)       AS GROSS_AMT,
         CAST(h."VatSum"   AS DOUBLE)       AS GST_AMT,
         h."Comments"                       AS REASON,
         h."NumAtCard"                      AS CUSTOMER_REF,
         h."TransId"                        AS TRANS_ID
  FROM {{SCHEMA}}.ORDN h
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode"  = h."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode"
                             AND g."GroupType" = c."CardType"
  WHERE h."DocDate" <= DATE'{{ASOF}}'
),
LINE AS (
  SELECT l."DocEntry"                     AS DOC_ENTRY,
         COUNT(*)                         AS NUM_LINES,
         COUNT(DISTINCT l."ItemCode")     AS NUM_ITEMS,
         SUM(CASE WHEN IFNULL(l."unitMsr",'PCS') = 'PCS'
                  THEN CAST(l."Quantity" AS DOUBLE) ELSE 0 END) AS QTY_PCS,
         SUM(CASE WHEN IFNULL(l."unitMsr",'PCS') = 'PCS'
                  THEN 0 ELSE CAST(l."Quantity" AS DOUBLE) END) AS QTY_OTHER
  FROM {{SCHEMA}}.RDN1 l
  GROUP BY l."DocEntry"
),
WHS AS (
  SELECT DOC_ENTRY, STRING_AGG(W, ',' ORDER BY W) AS WAREHOUSES
  FROM (SELECT DISTINCT l."DocEntry" AS DOC_ENTRY, l."WhsCode" AS W
        FROM {{SCHEMA}}.RDN1 l WHERE l."WhsCode" IS NOT NULL)
  GROUP BY DOC_ENTRY
),
-- deliveries that were invoiced (INV1 "BaseType"=15 on a live invoice)
DLVINV AS (
  SELECT DISTINCT l."BaseEntry" AS DLN
  FROM {{SCHEMA}}.INV1 l
  JOIN {{SCHEMA}}.OINV n ON n."DocEntry" = l."DocEntry"
  WHERE l."BaseType" = 15 AND n."CANCELED" = 'N' AND n."DocDate" <= DATE'{{ASOF}}'
),
-- base delivery of the return ("BaseType"=15; "BaseType"=13 is 0 rows everywhere)
DLV AS (
  SELECT b.DOC_ENTRY,
         COUNT(*)                                                                AS BASE_DLN_COUNT,
         STRING_AGG(CAST(b.DLN_NUM AS NVARCHAR(20)), ',' ORDER BY b.DLN_NUM)     AS BASE_DLN_DOCNUMS,
         MAX(b.INVOICED)                                                         AS BASE_DLN_INVOICED
  FROM (SELECT DISTINCT l."DocEntry" AS DOC_ENTRY,
                        d."DocNum"   AS DLN_NUM,
                        CASE WHEN i.DLN IS NULL THEN 0 ELSE 1 END AS INVOICED
        FROM {{SCHEMA}}.RDN1 l
        JOIN {{SCHEMA}}.ODLN d ON d."DocEntry" = l."BaseEntry"
        LEFT JOIN DLVINV i ON i.DLN = l."BaseEntry"
        WHERE l."BaseType" = 15) b
  GROUP BY b.DOC_ENTRY
),
-- follow-on A/R credit notes, taken from the CREDIT-NOTE side only
CN AS (
  SELECT x.DOC_ENTRY,
         COUNT(*)                                                            AS CN_COUNT,
         LEFT(STRING_AGG(CAST(x.CN_NUM AS NVARCHAR(20)), ',' ORDER BY x.CN_NUM), 200) AS CN_DOCNUMS,
         MIN(x.CN_DATE)                                                      AS CN_FIRST_DATE,
         SUM(x.CN_NET)                                                       AS CN_NET
  FROM (SELECT l."BaseEntry" AS DOC_ENTRY,
               n."DocNum"    AS CN_NUM,
               MIN(n."DocDate") AS CN_DATE,
               SUM(CAST(l."LineTotal" AS DOUBLE)) AS CN_NET
        FROM {{SCHEMA}}.RIN1 l
        JOIN {{SCHEMA}}.ORIN n ON n."DocEntry" = l."DocEntry"
        WHERE l."BaseType" = 16 AND n."CANCELED" = 'N' AND n."DocDate" <= DATE'{{ASOF}}'
        GROUP BY l."BaseEntry", n."DocNum") x
  GROUP BY x.DOC_ENTRY
),
-- stock value pushed back into inventory by the return's own journal entry
COST AS (
  SELECT j."TransId" AS TRANS_ID, SUM(CAST(j."Debit" AS DOUBLE)) AS STOCK_COST
  FROM {{SCHEMA}}.JDT1 j
  WHERE j."TransId" IN (SELECT "TransId" FROM {{SCHEMA}}.ORDN
                        WHERE "TransId" IS NOT NULL AND "DocDate" <= DATE'{{ASOF}}')
  GROUP BY j."TransId"
)
SELECT * FROM (
  SELECT r.DOC_ENTRY,
         r.DOC_NUM,
         TO_VARCHAR(r.DOC_DATE, 'YYYY-MM-DD')                    AS DOC_DATE,
         TO_VARCHAR(r.DOC_DATE, 'YYYY-MM')                       AS DOC_MONTH,
         DAYS_BETWEEN(r.DOC_DATE, DATE'{{ASOF}}')                AS AGE_DAYS,
         CASE r.CANCEL_FLAG WHEN 'N' THEN 'LIVE'
                            WHEN 'Y' THEN 'CANCELLED'
                            WHEN 'C' THEN 'CANCELLATION_DOC'
                            ELSE r.CANCEL_FLAG END               AS CANCEL_STATUS,
         r.DOC_STATUS,
         r.CARD_CODE,
         r.CARD_NAME,
         r.CUSTOMER_GROUP,
         CASE WHEN UPPER(r.CUSTOMER_GROUP) LIKE '%BRANCH%' THEN 'BRANCH'
              WHEN UPPER(r.CARD_NAME)       LIKE '%JIVO%'  THEN 'INTERCOMPANY'
              ELSE 'EXTERNAL' END                                AS PARTY_CLASS,
         r.BRANCH_ID,
         IFNULL(r.BRANCH_NAME, '')                               AS BRANCH_NAME,
         IFNULL(w.WAREHOUSES, '')                                AS WAREHOUSES,
         IFNULL(li.NUM_LINES, 0)                                 AS NUM_LINES,
         IFNULL(li.NUM_ITEMS, 0)                                 AS NUM_ITEMS,
         ROUND(IFNULL(li.QTY_PCS, 0), 3)                         AS QTY_PCS,
         ROUND(IFNULL(li.QTY_OTHER, 0), 3)                       AS QTY_OTHER_UOM,
         ROUND(r.GROSS_AMT - r.GST_AMT, 2)                       AS NET_AMT,
         ROUND(r.GST_AMT, 2)                                     AS GST_AMT,
         ROUND(r.GROSS_AMT, 2)                                   AS GROSS_AMT,
         ROUND(IFNULL(k.STOCK_COST, 0), 2)                       AS STOCK_COST,
         IFNULL(r.REASON, '')                                    AS REASON,
         IFNULL(r.CUSTOMER_REF, '')                              AS CUSTOMER_REF,
         IFNULL(d.BASE_DLN_COUNT, 0)                             AS BASE_DLN_COUNT,
         IFNULL(d.BASE_DLN_DOCNUMS, '')                          AS BASE_DLN_DOCNUMS,
         IFNULL(d.BASE_DLN_INVOICED, 0)                          AS BASE_DLN_INVOICED,
         IFNULL(cn.CN_COUNT, 0)                                  AS CN_COUNT,
         IFNULL(cn.CN_DOCNUMS, '')                               AS CN_DOCNUMS,
         IFNULL(TO_VARCHAR(cn.CN_FIRST_DATE, 'YYYY-MM-DD'), '')  AS CN_FIRST_DATE,
         ROUND(IFNULL(cn.CN_NET, 0), 2)                          AS CN_NET,
         CASE WHEN cn.CN_FIRST_DATE IS NULL THEN NULL
              ELSE DAYS_BETWEEN(r.DOC_DATE, cn.CN_FIRST_DATE) END AS CN_LAG_DAYS,
         CASE WHEN r.CANCEL_FLAG = 'N' AND cn.DOC_ENTRY IS NULL THEN 'Y' ELSE 'N' END
                                                                 AS FLAG_NO_CREDIT_NOTE,
         CASE WHEN r.CANCEL_FLAG <> 'N' OR cn.DOC_ENTRY IS NOT NULL THEN ''
              WHEN d.DOC_ENTRY IS NULL          THEN 'STANDALONE_NO_LINK'
              WHEN d.BASE_DLN_INVOICED = 1      THEN 'FROM_DELIVERY_INVOICED'
              ELSE 'FROM_DELIVERY_UNBILLED' END                  AS NO_CN_REASON,
         CASE WHEN r.CANCEL_FLAG <> 'N' OR cn.DOC_ENTRY IS NOT NULL THEN 4
              WHEN d.DOC_ENTRY IS NULL          THEN 2
              WHEN d.BASE_DLN_INVOICED = 1      THEN 1
              ELSE 3 END                                         AS EXC_RANK
  FROM RET r
  LEFT JOIN LINE li ON li.DOC_ENTRY = r.DOC_ENTRY
  LEFT JOIN WHS  w  ON w.DOC_ENTRY  = r.DOC_ENTRY
  LEFT JOIN DLV  d  ON d.DOC_ENTRY  = r.DOC_ENTRY
  LEFT JOIN CN   cn ON cn.DOC_ENTRY = r.DOC_ENTRY
  LEFT JOIN COST k  ON k.TRANS_ID   = r.TRANS_ID
)
ORDER BY EXC_RANK, STOCK_COST DESC, DOC_DATE DESC, DOC_ENTRY DESC
LIMIT 500
