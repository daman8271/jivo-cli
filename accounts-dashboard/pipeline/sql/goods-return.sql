-- goods-return.sql  --  GOODS RETURN SUMMARY (purchase returns to vendors)
--
-- Source: {{SCHEMA}}.ORPD / RPD1 (goods return, ObjType 21) measured against
--         {{SCHEMA}}.OPDN (GRPO, ObjType 20) and {{SCHEMA}}.ORPC (A/P credit note).
-- Everything is dated on or before {{ASOF}} and counts LIVE documents only
-- ("CANCELED" = 'N' -- see the trap note below).
--
-- ONE ROW PER (SCOPE, GRP_KEY).  Five stacked scopes in one bounded result:
--   SCOPE = 'TOTAL'       1 row   -- company grand total
--   SCOPE = 'CLASS'       <=4     -- EXTERNAL / BRANCH / INTERCOMPANY / INTERNAL_ADJ
--   SCOPE = 'CREDIT_NOTE' 2 rows  -- HAS_CREDIT_NOTE / NO_CREDIT_NOTE
--   SCOPE = 'MONTH'       <=36    -- every month that has a return or a GRPO
--   SCOPE = 'VENDOR'      <=~40   -- every party that has a return, biggest first
-- Expected size: ~30-65 rows per company (Oil 61, Mart 28, Bev 38 at 2026-08-21).
-- Hard-capped at 200 rows; the cap bites the smallest VENDOR rows first.
--
-- *** NEVER SUM ACROSS SCOPES.  Every scope re-partitions the SAME documents, so
-- *** a total over the whole table is ~5x the truth.  Filter to one SCOPE first.
-- *** Within a scope the partition is exact: CLASS, MONTH, VENDOR and CREDIT_NOTE
-- *** each add back to the TOTAL row (verified on all three books).
--
-- Columns:
--   SCOPE, GRP_KEY, GRP_LABEL, SORT_KEY,
--   RET_DOCS, RET_NET, RET_GST, RET_GROSS,
--   RET_DOCS_OPEN, RET_DOCS_NO_CN, RET_GROSS_NO_CN,
--   GRPO_DOCS, GRPO_NET, RET_PCT_OF_GRPO,
--   RET_NOCN_EXT_DOCS, RET_NOCN_EXT_GROSS
-- Amounts are raw INR (no _L / _CR suffix anywhere -- nothing is scaled).
-- RET_NET / GRPO_NET are net of GST ("DocTotal"-"VatSum").
-- RET_PCT_OF_GRPO = RET_NET / GRPO_NET * 100  -- the headline Accounts number.
--
-- Traps handled (full write-up in notes/goods-return.md):
--   1. "CANCELED" on ORPD/OPDN/ORPC has THREE values, not two: 'N' live, 'Y' the
--      cancelled original, 'C' the auto-generated cancellation mirror.  'Y' and 'C'
--      mirror each other exactly, so filtering on <> 'Y' alone double-counts;
--      this query keeps only 'N', on every one of the three tables.
--   2. Most of these documents are NOT vendor returns.  In Mart 46 of 49 live
--      returns are the Oil company as a vendor (intercompany), and JIVO's own
--      branch GST registrations appear as BRANCH VENDOR group cards.  PARTY_CLASS
--      splits them, and the ratio is computed against GRPO of the SAME class.
--   3. 'STOCK GOODS ISSUE' is a dummy vendor used to write off physical
--      shortages -- INTERNAL_ADJ, never a recoverable claim on a supplier.  It is
--      the reason RET_NOCN_EXT_* exists: in Beverages 92% of the "returned but
--      never credited" money is this write-off, which by design never attracts a
--      supplier credit note.  RET_GROSS_NO_CN keeps everything; RET_NOCN_EXT_GROSS
--      is the part a supplier could actually still be billed for.
--   4. A goods return can point at more than one A/P credit note, and a linked
--      credit note can itself be cancelled; credit notes are de-duplicated and
--      cancelled ones are ignored, so NO_CREDIT_NOTE means genuinely unrecovered.
--      The credit note must also be dated on or before {{ASOF}} -- without that
--      bound a month-end position silently borrows a credit note raised later
--      (1 Oil return at 2025-12-31, 1 Mart return at 2026-06-30).
--   5. Vendor codes differ per company (VENDA000942 is a real supplier in Oil and
--      JIVO MART - DL in Mart), so classification is by card group + name, never
--      by a hard-coded code list.
--   6. The GRPO denominator is restricted to item receipts ("DocType" = 'I').
--      Every goods return ever raised in all three books is an item document, but
--      OPDN also carries SERVICE receipts (freight, job work, imprest) that can
--      never be returned on an ORPD: 3,864 of Oil's 10,640 GRPOs, 3,270 of
--      Beverages' 4,563.  Leaving them in inflated Beverages' denominator by 10%
--      and its GRPO document count by 3.5x.
WITH RET AS (
  SELECT h."DocEntry"   AS DOC_ENTRY,
         h."DocDate"    AS DOC_DATE,
         h."DocStatus"  AS DOC_STATUS,
         h."CardCode"   AS CARD_CODE,
         IFNULL(c."CardName", h."CardName") AS CARD_NAME,
         CASE WHEN UPPER(IFNULL(g."GroupName",'')) LIKE '%BRANCH%'          THEN 'BRANCH'
              WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE '%JIVO%'   THEN 'INTERCOMPANY'
              WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE 'STOCK GOODS%' THEN 'INTERNAL_ADJ'
              ELSE 'EXTERNAL' END AS PARTY_CLASS,
         CAST(h."DocTotal" AS DOUBLE) AS GROSS_AMT,
         CAST(h."VatSum"   AS DOUBLE) AS GST_AMT
  FROM {{SCHEMA}}.ORPD h
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode"  = h."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode"
                             AND g."GroupType" = c."CardType"
  WHERE h."CANCELED" = 'N' AND h."DocDate" <= DATE'{{ASOF}}'
),
HASCN AS (
  SELECT DISTINCT l."DocEntry" AS DOC_ENTRY
  FROM {{SCHEMA}}.RPD1 l
  JOIN {{SCHEMA}}.ORPC n ON n."DocEntry" = l."TrgetEntry"
  WHERE l."TargetType" = 19 AND n."CANCELED" = 'N'
    AND n."DocDate" <= DATE'{{ASOF}}'
),
R AS (
  SELECT r.*, CASE WHEN k.DOC_ENTRY IS NULL THEN 0 ELSE 1 END AS HAS_CN
  FROM RET r LEFT JOIN HASCN k ON k.DOC_ENTRY = r.DOC_ENTRY
),
GR AS (
  SELECT h."DocEntry" AS DOC_ENTRY,
         h."DocDate"  AS DOC_DATE,
         h."CardCode" AS CARD_CODE,
         CASE WHEN UPPER(IFNULL(g."GroupName",'')) LIKE '%BRANCH%'          THEN 'BRANCH'
              WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE '%JIVO%'   THEN 'INTERCOMPANY'
              WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE 'STOCK GOODS%' THEN 'INTERNAL_ADJ'
              ELSE 'EXTERNAL' END AS PARTY_CLASS,
         CAST(h."DocTotal" AS DOUBLE) - CAST(h."VatSum" AS DOUBLE) AS NET_AMT
  FROM {{SCHEMA}}.OPDN h
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode"  = h."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode"
                             AND g."GroupType" = c."CardType"
  WHERE h."CANCELED" = 'N' AND h."DocDate" <= DATE'{{ASOF}}'
    AND h."DocType" = 'I'
),
-- ---- aggregates -------------------------------------------------------
R_TOT AS (
  SELECT COUNT(*) D, IFNULL(SUM(GROSS_AMT-GST_AMT),0) NET, IFNULL(SUM(GST_AMT),0) GST,
         IFNULL(SUM(GROSS_AMT),0) GRS,
         SUM(CASE WHEN DOC_STATUS='O' THEN 1 ELSE 0 END) DOPEN,
         SUM(CASE WHEN HAS_CN=0 THEN 1 ELSE 0 END) DNOCN,
         IFNULL(SUM(CASE WHEN HAS_CN=0 THEN GROSS_AMT ELSE 0 END),0) GNOCN,
         SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN 1 ELSE 0 END) DNOCNX,
         IFNULL(SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN GROSS_AMT ELSE 0 END),0) GNOCNX
  FROM R
),
G_TOT AS (SELECT COUNT(*) D, IFNULL(SUM(NET_AMT),0) NET FROM GR),
R_CLS AS (
  SELECT PARTY_CLASS K, COUNT(*) D, SUM(GROSS_AMT-GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(CASE WHEN DOC_STATUS='O' THEN 1 ELSE 0 END) DOPEN,
         SUM(CASE WHEN HAS_CN=0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN=0 THEN GROSS_AMT ELSE 0 END) GNOCN,
         SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN 1 ELSE 0 END) DNOCNX,
         SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN GROSS_AMT ELSE 0 END) GNOCNX
  FROM R GROUP BY PARTY_CLASS
),
G_CLS AS (SELECT PARTY_CLASS K, COUNT(*) D, SUM(NET_AMT) NET FROM GR GROUP BY PARTY_CLASS),
R_MTH AS (
  SELECT TO_VARCHAR(DOC_DATE,'YYYY-MM') K, COUNT(*) D, SUM(GROSS_AMT-GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(CASE WHEN DOC_STATUS='O' THEN 1 ELSE 0 END) DOPEN,
         SUM(CASE WHEN HAS_CN=0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN=0 THEN GROSS_AMT ELSE 0 END) GNOCN,
         SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN 1 ELSE 0 END) DNOCNX,
         SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN GROSS_AMT ELSE 0 END) GNOCNX
  FROM R GROUP BY TO_VARCHAR(DOC_DATE,'YYYY-MM')
),
G_MTH AS (SELECT TO_VARCHAR(DOC_DATE,'YYYY-MM') K, COUNT(*) D, SUM(NET_AMT) NET FROM GR GROUP BY TO_VARCHAR(DOC_DATE,'YYYY-MM')),
R_VEN AS (
  SELECT CARD_CODE K, MAX(CARD_NAME) LBL, MAX(PARTY_CLASS) CLS,
         COUNT(*) D, SUM(GROSS_AMT-GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(CASE WHEN DOC_STATUS='O' THEN 1 ELSE 0 END) DOPEN,
         SUM(CASE WHEN HAS_CN=0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN=0 THEN GROSS_AMT ELSE 0 END) GNOCN,
         SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN 1 ELSE 0 END) DNOCNX,
         SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN GROSS_AMT ELSE 0 END) GNOCNX
  FROM R GROUP BY CARD_CODE
),
G_VEN AS (SELECT CARD_CODE K, COUNT(*) D, SUM(NET_AMT) NET FROM GR GROUP BY CARD_CODE),
R_CN AS (
  SELECT CASE WHEN HAS_CN=1 THEN 'HAS_CREDIT_NOTE' ELSE 'NO_CREDIT_NOTE' END K,
         COUNT(*) D, SUM(GROSS_AMT-GST_AMT) NET, SUM(GST_AMT) GST, SUM(GROSS_AMT) GRS,
         SUM(CASE WHEN DOC_STATUS='O' THEN 1 ELSE 0 END) DOPEN,
         SUM(CASE WHEN HAS_CN=0 THEN 1 ELSE 0 END) DNOCN,
         SUM(CASE WHEN HAS_CN=0 THEN GROSS_AMT ELSE 0 END) GNOCN,
         SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN 1 ELSE 0 END) DNOCNX,
         SUM(CASE WHEN HAS_CN=0 AND PARTY_CLASS='EXTERNAL' THEN GROSS_AMT ELSE 0 END) GNOCNX
  FROM R GROUP BY CASE WHEN HAS_CN=1 THEN 'HAS_CREDIT_NOTE' ELSE 'NO_CREDIT_NOTE' END
)
SELECT * FROM (
  SELECT 'TOTAL' AS SCOPE, 'ALL' AS GRP_KEY, 'All goods returns' AS GRP_LABEL, '1' AS SORT_KEY,
         t.D AS RET_DOCS, ROUND(t.NET,2) AS RET_NET, ROUND(t.GST,2) AS RET_GST, ROUND(t.GRS,2) AS RET_GROSS,
         t.DOPEN AS RET_DOCS_OPEN, t.DNOCN AS RET_DOCS_NO_CN, ROUND(t.GNOCN,2) AS RET_GROSS_NO_CN,
         g.D AS GRPO_DOCS, ROUND(g.NET,2) AS GRPO_NET,
         CASE WHEN g.NET > 0 THEN ROUND(t.NET/g.NET*100,4) ELSE NULL END AS RET_PCT_OF_GRPO,
         t.DNOCNX AS RET_NOCN_EXT_DOCS, ROUND(t.GNOCNX,2) AS RET_NOCN_EXT_GROSS
  FROM R_TOT t CROSS JOIN G_TOT g

  UNION ALL
  SELECT 'CLASS', IFNULL(r.K,g.K), IFNULL(r.K,g.K), '2'||IFNULL(r.K,g.K),
         IFNULL(r.D,0), ROUND(IFNULL(r.NET,0),2), ROUND(IFNULL(r.GST,0),2), ROUND(IFNULL(r.GRS,0),2),
         IFNULL(r.DOPEN,0), IFNULL(r.DNOCN,0), ROUND(IFNULL(r.GNOCN,0),2),
         IFNULL(g.D,0), ROUND(IFNULL(g.NET,0),2),
         CASE WHEN g.NET > 0 THEN ROUND(IFNULL(r.NET,0)/g.NET*100,4) ELSE NULL END,
         IFNULL(r.DNOCNX,0), ROUND(IFNULL(r.GNOCNX,0),2)
  FROM R_CLS r FULL OUTER JOIN G_CLS g ON g.K = r.K

  UNION ALL
  SELECT 'CREDIT_NOTE', r.K, r.K, '3'||r.K,
         r.D, ROUND(r.NET,2), ROUND(r.GST,2), ROUND(r.GRS,2),
         r.DOPEN, r.DNOCN, ROUND(r.GNOCN,2),
         NULL, NULL, NULL,
         r.DNOCNX, ROUND(r.GNOCNX,2)
  FROM R_CN r

  UNION ALL
  SELECT 'MONTH', IFNULL(r.K,g.K), IFNULL(r.K,g.K), '4'||IFNULL(r.K,g.K),
         IFNULL(r.D,0), ROUND(IFNULL(r.NET,0),2), ROUND(IFNULL(r.GST,0),2), ROUND(IFNULL(r.GRS,0),2),
         IFNULL(r.DOPEN,0), IFNULL(r.DNOCN,0), ROUND(IFNULL(r.GNOCN,0),2),
         IFNULL(g.D,0), ROUND(IFNULL(g.NET,0),2),
         CASE WHEN g.NET > 0 THEN ROUND(IFNULL(r.NET,0)/g.NET*100,4) ELSE NULL END,
         IFNULL(r.DNOCNX,0), ROUND(IFNULL(r.GNOCNX,0),2)
  FROM R_MTH r FULL OUTER JOIN G_MTH g ON g.K = r.K

  UNION ALL
  SELECT 'VENDOR', r.K, r.LBL||' ['||r.CLS||']', '5',
         r.D, ROUND(r.NET,2), ROUND(r.GST,2), ROUND(r.GRS,2),
         r.DOPEN, r.DNOCN, ROUND(r.GNOCN,2),
         IFNULL(g.D,0), ROUND(IFNULL(g.NET,0),2),
         CASE WHEN g.NET > 0 THEN ROUND(r.NET/g.NET*100,4) ELSE NULL END,
         r.DNOCNX, ROUND(r.GNOCNX,2)
  FROM R_VEN r LEFT JOIN G_VEN g ON g.K = r.K
)
ORDER BY SORT_KEY, RET_GROSS DESC
LIMIT 200
