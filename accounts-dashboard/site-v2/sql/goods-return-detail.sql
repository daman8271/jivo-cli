-- goods-return-detail.sql  --  GOODS RETURN REGISTER (purchase returns to vendors)
--
-- Source: {{SCHEMA}}.ORPD (header, ObjType 21) + {{SCHEMA}}.RPD1 (lines).
-- ONE ROW PER GOODS RETURN DOCUMENT, newest first, dated on or before {{ASOF}}.
-- Volume is tiny: Oil 117 / Mart 59 / Bev 33 documents at 2026-08-21, so this is
-- the full register, not a sample.  Hard-capped at 500 rows as a guard.
--
-- Columns:
--   DOC_ENTRY, DOC_NUM, DOC_DATE, DOC_MONTH, AGE_DAYS,
--   CANCEL_STATUS (LIVE | CANCELLED | CANCELLATION_DOC), DOC_STATUS (O|C),
--   CARD_CODE, CARD_NAME, VENDOR_GROUP, PARTY_CLASS,
--   BRANCH_ID, BRANCH_NAME, WAREHOUSES,
--   NUM_LINES, NUM_ITEMS, TOTAL_QTY,
--   NET_AMT, GST_AMT, GROSS_AMT,
--   REASON, VENDOR_REF,
--   BASE_GRPO_COUNT, BASE_GRPO_DOCNUMS,
--   CN_COUNT, CN_DOCNUMS, CN_FIRST_DATE, CN_GROSS, CN_LAG_DAYS,
--   FLAG_NO_CREDIT_NOTE (Y only for LIVE returns with no live A/P credit note)
--
-- Traps handled (see notes/goods-return.md):
--   * "CANCELED" has THREE values here: 'N' live, 'Y' cancelled original,
--     'C' the system-generated cancellation mirror.  All three are kept but
--     decoded, and every flag/total is computed for 'N' only.
--   * PARTY_CLASS separates real vendor returns from branch / intercompany /
--     internal stock-adjustment postings (Mart is ~94% intercompany by value).
--   * A return can point at more than one A/P credit note (1 case in Oil), so
--     credit notes are de-duplicated and aggregated, never joined row-to-row.
--   * A linked credit note that is itself cancelled does NOT count as recovered,
--     and neither does one dated after {{ASOF}} -- at a month-end position a
--     credit note raised later has not happened yet.
--   * The base-GRPO link (BaseType 20) is NOT filtered on "CANCELED": it names the
--     document the return was copied from, which stays a fact even if that GRPO was
--     later cancelled.  No cancelled base exists today (Oil 3 / Mart 1 / Bev 0 links,
--     all live, all item-type), so the count is currently unaffected either way.
--   * TOTAL_QTY sums RPD1."Quantity" across lines: PIECES (single bottles), never
--     cartons -- and it adds up mixed units of measure, so it is a size hint, not a
--     tonnage.  Use the money columns for anything that has to foot.
WITH RET AS (
  SELECT h."DocEntry"                                   AS DOC_ENTRY,
         h."DocNum"                                     AS DOC_NUM,
         h."DocDate"                                    AS DOC_DATE,
         h."DocStatus"                                  AS DOC_STATUS,
         h."CANCELED"                                   AS CANCEL_FLAG,
         h."CardCode"                                   AS CARD_CODE,
         IFNULL(c."CardName", h."CardName")             AS CARD_NAME,
         IFNULL(g."GroupName", '')                      AS VENDOR_GROUP,
         h."BPLId"                                      AS BRANCH_ID,
         h."BPLName"                                    AS BRANCH_NAME,
         CAST(h."DocTotal" AS DOUBLE)                   AS GROSS_AMT,
         CAST(h."VatSum"   AS DOUBLE)                   AS GST_AMT,
         h."Comments"                                   AS REASON,
         h."NumAtCard"                                  AS VENDOR_REF
  FROM {{SCHEMA}}.ORPD h
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode" = h."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode"
                             AND g."GroupType" = c."CardType"
  WHERE h."DocDate" <= DATE'{{ASOF}}'
),
LINE AS (
  SELECT l."DocEntry"                        AS DOC_ENTRY,
         COUNT(*)                            AS NUM_LINES,
         COUNT(DISTINCT l."ItemCode")        AS NUM_ITEMS,
         SUM(CAST(l."Quantity" AS DOUBLE))   AS TOTAL_QTY
  FROM {{SCHEMA}}.RPD1 l
  GROUP BY l."DocEntry"
),
WHS AS (
  SELECT DOC_ENTRY, STRING_AGG(W, ',' ORDER BY W) AS WAREHOUSES
  FROM (SELECT DISTINCT l."DocEntry" AS DOC_ENTRY, l."WhsCode" AS W
        FROM {{SCHEMA}}.RPD1 l WHERE l."WhsCode" IS NOT NULL)
  GROUP BY DOC_ENTRY
),
-- base GRPO (BaseType 20 = Goods Receipt PO).  Almost never used at JIVO.
GRPO AS (
  SELECT b.DOC_ENTRY,
         COUNT(*)                                   AS BASE_GRPO_COUNT,
         STRING_AGG(CAST(b.GRPO_NUM AS NVARCHAR(20)), ',' ORDER BY b.GRPO_NUM) AS BASE_GRPO_DOCNUMS
  FROM (SELECT DISTINCT l."DocEntry" AS DOC_ENTRY, p."DocNum" AS GRPO_NUM
        FROM {{SCHEMA}}.RPD1 l
        JOIN {{SCHEMA}}.OPDN p ON p."DocEntry" = l."BaseEntry"
        WHERE l."BaseType" = 20) b
  GROUP BY b.DOC_ENTRY
),
-- follow-on A/P credit note (TargetType 19 = ORPC).  Cancelled CNs excluded.
CN AS (
  SELECT x.DOC_ENTRY,
         COUNT(*)                                                       AS CN_COUNT,
         STRING_AGG(CAST(x.CN_NUM AS NVARCHAR(20)), ',' ORDER BY x.CN_NUM) AS CN_DOCNUMS,
         MIN(x.CN_DATE)                                                 AS CN_FIRST_DATE,
         SUM(x.CN_GROSS)                                                AS CN_GROSS
  FROM (SELECT DISTINCT l."DocEntry" AS DOC_ENTRY,
                        n."DocNum"   AS CN_NUM,
                        n."DocDate"  AS CN_DATE,
                        CAST(n."DocTotal" AS DOUBLE) AS CN_GROSS
        FROM {{SCHEMA}}.RPD1 l
        JOIN {{SCHEMA}}.ORPC n ON n."DocEntry" = l."TrgetEntry"
        WHERE l."TargetType" = 19 AND n."CANCELED" = 'N'
          AND n."DocDate" <= DATE'{{ASOF}}') x
  GROUP BY x.DOC_ENTRY
)
SELECT r.DOC_ENTRY,
       r.DOC_NUM,
       TO_VARCHAR(r.DOC_DATE, 'YYYY-MM-DD')                     AS DOC_DATE,
       TO_VARCHAR(r.DOC_DATE, 'YYYY-MM')                        AS DOC_MONTH,
       DAYS_BETWEEN(r.DOC_DATE, DATE'{{ASOF}}')                 AS AGE_DAYS,
       CASE r.CANCEL_FLAG WHEN 'N' THEN 'LIVE'
                          WHEN 'Y' THEN 'CANCELLED'
                          WHEN 'C' THEN 'CANCELLATION_DOC'
                          ELSE r.CANCEL_FLAG END                AS CANCEL_STATUS,
       r.DOC_STATUS,
       r.CARD_CODE,
       r.CARD_NAME,
       r.VENDOR_GROUP,
       CASE WHEN UPPER(r.VENDOR_GROUP) LIKE '%BRANCH%'   THEN 'BRANCH'
            WHEN UPPER(r.CARD_NAME)    LIKE '%JIVO%'     THEN 'INTERCOMPANY'
            WHEN UPPER(r.CARD_NAME)    LIKE 'STOCK GOODS%' THEN 'INTERNAL_ADJ'
            ELSE 'EXTERNAL' END                               AS PARTY_CLASS,
       r.BRANCH_ID,
       r.BRANCH_NAME,
       IFNULL(w.WAREHOUSES, '')                                AS WAREHOUSES,
       IFNULL(li.NUM_LINES, 0)                                 AS NUM_LINES,
       IFNULL(li.NUM_ITEMS, 0)                                 AS NUM_ITEMS,
       ROUND(IFNULL(li.TOTAL_QTY, 0), 3)                       AS TOTAL_QTY,
       ROUND(r.GROSS_AMT - r.GST_AMT, 2)                       AS NET_AMT,
       ROUND(r.GST_AMT, 2)                                     AS GST_AMT,
       ROUND(r.GROSS_AMT, 2)                                   AS GROSS_AMT,
       IFNULL(r.REASON, '')                                    AS REASON,
       IFNULL(r.VENDOR_REF, '')                                AS VENDOR_REF,
       IFNULL(gr.BASE_GRPO_COUNT, 0)                           AS BASE_GRPO_COUNT,
       IFNULL(gr.BASE_GRPO_DOCNUMS, '')                        AS BASE_GRPO_DOCNUMS,
       IFNULL(cn.CN_COUNT, 0)                                  AS CN_COUNT,
       IFNULL(cn.CN_DOCNUMS, '')                               AS CN_DOCNUMS,
       IFNULL(TO_VARCHAR(cn.CN_FIRST_DATE, 'YYYY-MM-DD'), '')  AS CN_FIRST_DATE,
       ROUND(IFNULL(cn.CN_GROSS, 0), 2)                        AS CN_GROSS,
       CASE WHEN cn.CN_FIRST_DATE IS NULL THEN NULL
            ELSE DAYS_BETWEEN(r.DOC_DATE, cn.CN_FIRST_DATE) END AS CN_LAG_DAYS,
       CASE WHEN r.CANCEL_FLAG = 'N' AND cn.DOC_ENTRY IS NULL THEN 'Y' ELSE 'N' END
                                                               AS FLAG_NO_CREDIT_NOTE
FROM RET r
LEFT JOIN LINE li ON li.DOC_ENTRY = r.DOC_ENTRY
LEFT JOIN WHS  w  ON w.DOC_ENTRY  = r.DOC_ENTRY
LEFT JOIN GRPO gr ON gr.DOC_ENTRY = r.DOC_ENTRY
LEFT JOIN CN   cn ON cn.DOC_ENTRY = r.DOC_ENTRY
ORDER BY r.DOC_DATE DESC, r.DOC_ENTRY DESC
LIMIT 500
