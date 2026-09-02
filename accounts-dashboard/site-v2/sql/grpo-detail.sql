-- grpo-detail.sql  --  THE GR/IR CHASE LIST (one row per problem GRPO)
--
-- Companion to grpo.sql.  grpo.sql aggregates; this one names the documents, and
-- that is why it is a second file: the aggregate cannot carry DocNum, vendor ref,
-- warehouse list and linked-invoice numbers without stopping being an aggregate.
--
-- Source: {{SCHEMA}}.OPDN / PDN1, matched against {{SCHEMA}}.OPCH / PCH1 (A/P
--         invoice, ObjType 18), {{SCHEMA}}.ORPD / RPD1 (goods return, ObjType 21)
--         and {{SCHEMA}}.OPOR (purchase order, ObjType 22).
-- Dated on or before {{ASOF}}, live documents only (OPDN."CANCELED" = 'N').
--
-- ONE ROW PER GRPO DOCUMENT that still owes a vendor bill.  Two kinds, in one list:
--   ROW_KIND = 'UNBILLED'      -- has >=1 line with "LineStatus"='O' and no live
--                                 A/P invoice line drawing it.  LIVE liability.
--   ROW_KIND = 'CLOSED_NOBILL' -- every such line is "LineStatus"='C' but still
--                                 has no live A/P invoice and no live goods
--                                 return: somebody CLOSED the GRPO without ever
--                                 booking the bill.  Audit item, not a liability.
-- Fully-invoiced GRPOs are not returned at all.
-- Size at 2026-08-21: Oil 436 rows (294 + 142), Mart 44 (41 + 3), Bev 282
-- (231 + 51).  Hard-capped at 1000, worst (largest open value) first.
--
-- MONEY UNITS: RAW INR RUPEES, no suffix, 2 dp.  DOC_* are the header's own
--   figures (OPDN."DocTotal" / "VatSum"); OPEN_* are summed from the offending
--   lines only (PDN1."GTotal" / "LineTotal").
--
-- OPEN_GROSS CAN EXCEED DOC_GROSS -- that is not a bug.  On a quarter of Oil
--   GRPOs and two thirds of Bev GRPOs the header carries "VatSum" = 0 while the
--   lines carry tax, so "DocTotal" is the NET receipt value (Oil GRPO 2026076885:
--   DocTotal 106,920, VatSum 0, lines 112,266 gross / 106,920 net).  162 Oil,
--   31 Mart and 212 Bev rows here are affected; the largest single gap is 8,043.60
--   (Mart 2007264574).  OPEN_* (the lines) is the number to chase, DOC_* is what
--   the SAP header screen will show.
--
-- COLUMN LIST (exact, in order) -- 30 columns:
--   ROW_KIND, DOC_ENTRY, DOC_NUM, DOC_DATE, DOC_MONTH, DAYS_OPEN, AGE_BUCKET,
--   DOC_STATUS, CARD_CODE, CARD_NAME, VENDOR_GROUP, PARTY_CLASS,
--   BRANCH_ID, BRANCH_NAME, WAREHOUSES, VENDOR_REF, PO_DOCNUMS,
--   NUM_LINES, NUM_UNBILLED_LINES, NUM_ZEROQTY_UNBILLED_LINES,
--   DOC_NET, DOC_GST, DOC_GROSS, OPEN_NET, OPEN_GST, OPEN_GROSS,
--   HAS_AP_INVOICE, AP_INVOICE_COUNT, AP_INVOICE_DOCNUMS, AP_LAG_DAYS
--
-- DAYS_OPEN is days from the GRPO's own "DocDate" (= gate-in date, C-0017) to
--   {{ASOF}}.  On a CLOSED_NOBILL row it is days since the goods came in, not
--   days the document has been open.
--
-- HAS_AP_INVOICE is 'Y' only when a LIVE (non-cancelled) A/P invoice draws SOME
--   line of this GRPO.  'Y' together with ROW_KIND='UNBILLED' means the GRPO was
--   only PARTLY billed -- goods on some lines are still unpaid-for.
--
-- Traps handled -- identical to grpo.sql, see notes/grpo.md.  In short:
--   * "CANCELED" is three-valued ('N' live / 'Y' cancelled / 'C' mirror); only
--     'N' counts, on the GRPO and on every linked invoice and return.
--   * PDN1."OpenQty" is broken at JIVO (equals "Quantity" on closed lines) and
--     "OpenInvQty" is in a different UoM from "Quantity"; neither is used.
--     Open-ness comes from "LineStatus" plus the live A/P invoice link
--     (PCH1 "BaseType"=20 / "BaseEntry" / "BaseLine").
--   * Zero-quantity freight lines never close by themselves, so they are counted
--     but called out in NUM_ZEROQTY_UNBILLED_LINES -- those will never self-clear.
--   * A GRPO can feed several A/P invoices; they are de-duplicated and listed.
--   * The A/P-invoice and goods-return links are themselves capped at {{ASOF}}, so a
--     month-end run is not silently settled by a bill booked after that date.  (At
--     ASOF = today this is a no-op: no live OPCH/ORPD carries a future date.)
--   * Goods returns raised STANDALONE (RPD1."BaseType" = -1, which is how JIVO
--     raises 96%+ of them) carry no GRPO link, so they neither close nor exclude a
--     GRPO line.  A returned-but-never-invoiced receipt therefore still appears
--     here as UNBILLED.  Upper bound on that contamination: notes/grpo.md.
--   * Branch / intercompany receipts are flagged in PARTY_CLASS, never dropped.
WITH
BILLED AS (
  SELECT DISTINCT p."BaseEntry" AS DOC_ENTRY, p."BaseLine" AS LINE_NUM
  FROM {{SCHEMA}}.PCH1 p
  JOIN {{SCHEMA}}.OPCH i ON i."DocEntry" = p."DocEntry"
  WHERE p."BaseType" = 20 AND i."CANCELED" = 'N'
    AND i."DocDate" <= DATE'{{ASOF}}'          -- as-of consistency, see notes/grpo.md trap 11
),
RETURNED AS (
  SELECT DISTINCT r."BaseEntry" AS DOC_ENTRY, r."BaseLine" AS LINE_NUM
  FROM {{SCHEMA}}.RPD1 r
  JOIN {{SCHEMA}}.ORPD rh ON rh."DocEntry" = r."DocEntry"
  WHERE r."BaseType" = 20 AND rh."CANCELED" = 'N'
    AND rh."DocDate" <= DATE'{{ASOF}}'         -- as-of consistency
),
BAD AS (   -- the offending lines only
  SELECT l."DocEntry"                        AS DOC_ENTRY,
         l."LineStatus"                      AS LINE_STATUS,
         CAST(l."LineTotal" AS DOUBLE)       AS NET,
         CAST(l."GTotal"    AS DOUBLE)       AS GROSS,
         CASE WHEN CAST(l."Quantity" AS DOUBLE) = 0 THEN 1 ELSE 0 END AS ZERO_QTY
  FROM {{SCHEMA}}.PDN1 l
  LEFT JOIN BILLED   b  ON b.DOC_ENTRY  = l."DocEntry" AND b.LINE_NUM  = l."LineNum"
  LEFT JOIN RETURNED rt ON rt.DOC_ENTRY = l."DocEntry" AND rt.LINE_NUM = l."LineNum"
  WHERE b.DOC_ENTRY IS NULL AND rt.DOC_ENTRY IS NULL
),
BADAGG AS (
  SELECT DOC_ENTRY,
         MAX(CASE WHEN LINE_STATUS = 'O' THEN 1 ELSE 0 END)             AS ANY_OPEN,
         COUNT(*)                                                       AS N_BAD_LINES,
         SUM(ZERO_QTY)                                                  AS N_ZQ_BAD,
         SUM(NET)                                                       AS OPEN_NET,
         SUM(GROSS)                                                     AS OPEN_GROSS
  FROM BAD GROUP BY DOC_ENTRY
),
LINES AS (
  SELECT l."DocEntry" AS DOC_ENTRY, COUNT(*) AS NUM_LINES
  FROM {{SCHEMA}}.PDN1 l GROUP BY l."DocEntry"
),
WHS AS (
  SELECT DOC_ENTRY, STRING_AGG(W, ',' ORDER BY W) AS WAREHOUSES
  FROM (SELECT DISTINCT l."DocEntry" AS DOC_ENTRY, IFNULL(l."WhsCode",'(none)') AS W
        FROM {{SCHEMA}}.PDN1 l)
  GROUP BY DOC_ENTRY
),
POS AS (   -- the purchase order(s) this GRPO came from, so the paperwork is findable
  SELECT DOC_ENTRY, STRING_AGG(TO_VARCHAR(PN), ',' ORDER BY PN) AS PO_DOCNUMS
  FROM (SELECT DISTINCT l."DocEntry" AS DOC_ENTRY, o."DocNum" AS PN
        FROM {{SCHEMA}}.PDN1 l
        JOIN {{SCHEMA}}.OPOR o ON o."DocEntry" = l."BaseEntry"
        WHERE l."BaseType" = 22)
  GROUP BY DOC_ENTRY
),
INV AS (
  SELECT DOC_ENTRY, COUNT(*) AS AP_INVOICE_COUNT,
         STRING_AGG(TO_VARCHAR(IN_NUM), ',' ORDER BY IN_NUM) AS AP_INVOICE_DOCNUMS,
         MIN(IN_DATE) AS FIRST_INV_DATE
  FROM (SELECT DISTINCT p."BaseEntry" AS DOC_ENTRY, i."DocNum" AS IN_NUM, i."DocDate" AS IN_DATE
        FROM {{SCHEMA}}.PCH1 p
        JOIN {{SCHEMA}}.OPCH i ON i."DocEntry" = p."DocEntry"
        WHERE p."BaseType" = 20 AND i."CANCELED" = 'N'
          AND i."DocDate" <= DATE'{{ASOF}}')
  GROUP BY DOC_ENTRY
)
SELECT CASE WHEN a.ANY_OPEN = 1 THEN 'UNBILLED' ELSE 'CLOSED_NOBILL' END       AS ROW_KIND,
       h."DocEntry"                                                            AS DOC_ENTRY,
       h."DocNum"                                                              AS DOC_NUM,
       TO_VARCHAR(h."DocDate",'YYYY-MM-DD')                                    AS DOC_DATE,
       TO_VARCHAR(h."DocDate",'YYYY-MM')                                       AS DOC_MONTH,
       DAYS_BETWEEN(h."DocDate", DATE'{{ASOF}}')                               AS DAYS_OPEN,
       CASE WHEN DAYS_BETWEEN(h."DocDate", DATE'{{ASOF}}') <=  30 THEN '0-30'
            WHEN DAYS_BETWEEN(h."DocDate", DATE'{{ASOF}}') <=  60 THEN '31-60'
            WHEN DAYS_BETWEEN(h."DocDate", DATE'{{ASOF}}') <=  90 THEN '61-90'
            WHEN DAYS_BETWEEN(h."DocDate", DATE'{{ASOF}}') <= 180 THEN '91-180'
            WHEN DAYS_BETWEEN(h."DocDate", DATE'{{ASOF}}') <= 365 THEN '181-365'
            ELSE '365+' END                                                    AS AGE_BUCKET,
       h."DocStatus"                                                           AS DOC_STATUS,
       h."CardCode"                                                            AS CARD_CODE,
       IFNULL(c."CardName", h."CardName")                                      AS CARD_NAME,
       IFNULL(g."GroupName",'')                                                AS VENDOR_GROUP,
       CASE WHEN UPPER(IFNULL(g."GroupName",''))          LIKE '%BRANCH%'      THEN 'BRANCH'
            WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE '%JIVO%'        THEN 'INTERCOMPANY'
            WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE 'STOCK GOODS%'  THEN 'INTERNAL_ADJ'
            ELSE 'EXTERNAL' END                                                AS PARTY_CLASS,
       h."BPLId"                                                               AS BRANCH_ID,
       h."BPLName"                                                             AS BRANCH_NAME,
       w.WAREHOUSES                                                            AS WAREHOUSES,
       h."NumAtCard"                                                           AS VENDOR_REF,
       po.PO_DOCNUMS                                                           AS PO_DOCNUMS,
       IFNULL(ln.NUM_LINES,0)                                                  AS NUM_LINES,
       a.N_BAD_LINES                                                           AS NUM_UNBILLED_LINES,
       a.N_ZQ_BAD                                                              AS NUM_ZEROQTY_UNBILLED_LINES,
       ROUND(CAST(h."DocTotal" AS DOUBLE) - CAST(h."VatSum" AS DOUBLE),2)      AS DOC_NET,
       ROUND(CAST(h."VatSum"   AS DOUBLE),2)                                   AS DOC_GST,
       ROUND(CAST(h."DocTotal" AS DOUBLE),2)                                   AS DOC_GROSS,
       ROUND(a.OPEN_NET,2)                                                     AS OPEN_NET,
       ROUND(a.OPEN_GROSS - a.OPEN_NET,2)                                      AS OPEN_GST,
       ROUND(a.OPEN_GROSS,2)                                                   AS OPEN_GROSS,
       CASE WHEN iv.DOC_ENTRY IS NULL THEN 'N' ELSE 'Y' END                    AS HAS_AP_INVOICE,
       IFNULL(iv.AP_INVOICE_COUNT,0)                                           AS AP_INVOICE_COUNT,
       iv.AP_INVOICE_DOCNUMS                                                   AS AP_INVOICE_DOCNUMS,
       DAYS_BETWEEN(h."DocDate", iv.FIRST_INV_DATE)                            AS AP_LAG_DAYS
FROM {{SCHEMA}}.OPDN h
JOIN      BADAGG a  ON a.DOC_ENTRY  = h."DocEntry"
LEFT JOIN LINES  ln ON ln.DOC_ENTRY = h."DocEntry"
LEFT JOIN WHS    w  ON w.DOC_ENTRY  = h."DocEntry"
LEFT JOIN POS    po ON po.DOC_ENTRY = h."DocEntry"
LEFT JOIN INV    iv ON iv.DOC_ENTRY = h."DocEntry"
LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode"  = h."CardCode"
LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode"
                           AND g."GroupType" = c."CardType"
WHERE h."CANCELED" = 'N' AND h."DocDate" <= DATE'{{ASOF}}'
ORDER BY CASE WHEN a.ANY_OPEN = 1 THEN 0 ELSE 1 END,
         a.OPEN_GROSS DESC,
         h."DocEntry"
LIMIT 1000
