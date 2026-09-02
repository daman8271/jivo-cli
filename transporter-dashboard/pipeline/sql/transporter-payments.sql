-- transporter-payments.sql
-- ONE ROW PER OUTGOING PAYMENT (OVPM) made to a transporter vendor.
--
-- Scope        : OCRD."CardType" = 'S' AND OCRD."GroupCode" = 102 (TRANSPORTER - the
--                same code in all three books, FACTS sec.1). Live check 2026-08-22:
--                every GroupCode=102 card is CardType='S' (97 Oil / 95 Mart / 96 Bev),
--                so the CardType filter changes nothing today; it is kept so this file
--                defines "transporter vendor" exactly as FACTS sec.1 and the sibling
--                datasets (transporter-invoices / -master / -allocations) do.
-- Not cancelled: OVPM."Canceled" = 'N'  (mixed case on OVPM; three-valued 'N'/'Y'/'C',
--                so "= 'N'", NEVER "<> 'Y'" - FACTS sec.2 / C-0021).
-- Window       : DocDate >= 2025-04-01 (FY25 start) so FY26 payments can resolve the
--                prior-year invoices they settle - FACTS sec.6. The board's default
--                view (FY26, >= 2026-04-01) is a filter the loader applies, not this file.
--
-- THE JOIN (FACTS sec.2 - the single most important fact in this build):
--   VPM2."DocNum"   = the PAYMENT's OVPM."DocEntry"   <- payment -> its lines
--   VPM2."DocEntry" = the TARGET DOCUMENT's DocEntry  <- line -> the invoice/CN/JE
-- They are named backwards from what you would assume. Getting it wrong returns
-- plausible-looking wrong rows. Verified here on Oil payment DocNum 826466599:
-- PAY_TOTAL 24,656.00 -> ALLOC_CNT 3, INV_CNT 3, INV_APPLIED 24,656.00, MATCHED.
--
-- Replace {{SCHEMA}} with JIVO_OIL_HANADB | JIVO_MART_HANADB | JIVO_BEVERAGES_HANADB.
-- The three books are separate. NEVER sum them together.
--
-- READ-ONLY. This file contains a single SELECT and nothing else.
--
-- ---------------------------------------------------------------------------
-- HOW TO RUN IT (hana-sql gotcha): the binary's flag parser treats a query whose
-- first character is '-' as a command-line flag, so a comment-led file like this one
-- must be passed after a '--' separator (verified 2026-08-22):
--     ./hana-sql -env ../connections/hana-tunnel.env -- "$(sed 's/{{SCHEMA}}/JIVO_OIL_HANADB/g' transporter-payments.sql)"
-- A trailing ';' is accepted. Output is TSV, first line = header.
--
-- TSV CONTRACT for whoever loads this:
--   * Amounts are plain rupees, 2 decimal places, no grouping, no symbol. Indian
--     digit grouping is the renderer's job.
--   * Dates are 'YYYY-MM-DD' strings. TRSFR_DATE is '' when SAP left it NULL (it is
--     filled on every transporter payment today, but the guard stays).
--   * No column in this file is ever NULL - every nullable source is COALESCEd - so
--     the literal token "NULL" should never appear. If it does, the query changed.
--   * TRSFR_REF is '' on EVERY transporter payment in all three books (probed
--     2026-08-22: 0 of 312 Oil / 218 Mart / 94 Bev filled). Render "not recorded",
--     never a blank cell and never "NULL".
--   * REMARKS has tabs / CR / LF replaced by spaces (two Mart comments carry them and
--     would otherwise break the TSV), is trimmed, and is capped at 150 characters.
--     Longest live comment is 72 chars, so the cap never truncates today.
--
-- ALLOCATION BUCKETS (FACTS sec.3): VPM2."InvType"
--   '18' A/P invoice (OPCH)      -> INV_CNT / INV_APPLIED
--   '19' A/P credit note (ORPC)  -> CN_APPLIED
--   '30' journal entry (OJDT)    -> JE_APPLIED
--   anything else ('46' on-account outgoing payment applied later, '24'/'13'/'14'
--   contra, an InvType never seen before, or NULL) -> OTHER_APPLIED. Nothing is
--   silently dropped, which is what keeps
--        INV_APPLIED + CN_APPLIED + JE_APPLIED + OTHER_APPLIED = ALLOC_TOTAL
--   exactly, on every row (verified on all 624 rows across the three books).
--
-- SIGNS - read before you reconcile from these columns:
--   * InvType '46' lines carry a NEGATIVE SumApplied (a prior on-account payment
--     being consumed). Real; not abs()'d. 11 Oil + 6 Mart payments, all MATCHED.
--   * InvType '30' lines can be negative too (3 Oil, 2 Mart, 2 Bev rows). Real.
--   * InvType '19' (credit note) SumApplied is stored POSITIVE by SAP even though the
--     CN REDUCES what the payment covers. Consequence under the board's contract
--     (ALLOC_TOTAL = plain SUM of all lines, UNALLOCATED = PAY_TOTAL - ALLOC_TOTAL):
--     every payment with a CN line shows MATCH_FLAG='PARTIAL' and
--     UNALLOCATED = -2 x CN_APPLIED, although the money nets exactly:
--         INV_APPLIED - CN_APPLIED + JE_APPLIED + OTHER_APPLIED = PAY_TOTAL
--     holds to the paisa on all four such rows (Oil 726466986 / 226466542 /
--     126466786, Mart 625466578). The contract is implemented as written; the
--     renderer can recover the netted view from the columns above. Do not treat
--     those four PARTIALs as money the operator must chase.
--
-- MATCH_FLAG (FACTS sec.5):
--   'ON_ACCOUNT' = no VPM2 line at all. Money paid against no document. This is the
--                  bucket that causes repeated searching; it must be shown, with the
--                  amount. Live: Oil FY26 16 of 96 payments (FACTS sec.5 agrees).
--   'MATCHED'    = ABS(UNALLOCATED) <= 1 rupee.
--   'PARTIAL'    = everything else (see the CN note above before reading it as a gap).
--
-- OVPM."DocTotal" is the headline and splits across CashSum / CheckSum / TrsfrSum;
-- the split ties to DocTotal on every transporter payment in all three books
-- (0 mismatches, probed 2026-08-22).

WITH PAY AS (
    -- The transporter payments themselves, one row each.
    SELECT
        p."DocEntry",
        p."DocNum",
        p."CardCode",
        p."CardName",
        p."DocDate",
        p."DocTotal",
        p."CashSum",
        p."CheckSum",
        p."TrsfrSum",
        p."TrsfrRef",
        p."TrsfrDate",
        p."Comments"
    FROM {{SCHEMA}}.OVPM p
    JOIN {{SCHEMA}}.OCRD c
      ON c."CardCode" = p."CardCode"
    WHERE c."CardType"  = 'S'
      AND c."GroupCode" = 102
      AND p."Canceled"  = 'N'
      AND p."DocDate"  >= '2025-04-01'
),
ALLOC AS (
    -- Every VPM2 line on those payments, bucketed by InvType. Nothing is dropped.
    SELECT
        l."DocNum"                                       AS "PayEntry",   -- = OVPM."DocEntry"
        COUNT(*)                                         AS "AllocCnt",
        SUM(COALESCE(l."SumApplied", 0))                 AS "AllocTotal",
        SUM(CASE WHEN l."InvType" = '18' THEN 1 ELSE 0 END)                            AS "InvCnt",
        SUM(CASE WHEN l."InvType" = '18' THEN COALESCE(l."SumApplied", 0) ELSE 0 END)  AS "InvApplied",
        SUM(CASE WHEN l."InvType" = '19' THEN COALESCE(l."SumApplied", 0) ELSE 0 END)  AS "CnApplied",
        SUM(CASE WHEN l."InvType" = '30' THEN COALESCE(l."SumApplied", 0) ELSE 0 END)  AS "JeApplied",
        -- Written as "IN (...) THEN 0 ELSE amount" on purpose: a NULL InvType would
        -- make "NOT IN (...)" evaluate to NULL and quietly vanish from the totals.
        SUM(CASE WHEN l."InvType" IN ('18', '19', '30') THEN 0 ELSE COALESCE(l."SumApplied", 0) END) AS "OtherApplied"
    FROM {{SCHEMA}}.VPM2 l
    WHERE l."DocNum" IN (SELECT "DocEntry" FROM PAY)   -- VPM2."DocNum" = OVPM."DocEntry"
    GROUP BY l."DocNum"
)
SELECT
    p."DocEntry"                                      AS "DOC_ENTRY",
    p."DocNum"                                        AS "DOC_NUM",
    p."CardCode"                                      AS "CARD_CODE",
    COALESCE(p."CardName", '')                        AS "CARD_NAME",
    TO_VARCHAR(p."DocDate", 'YYYY-MM-DD')             AS "DOC_DATE",

    -- Headline money and its method split (ties exactly - see header).
    CAST(COALESCE(p."DocTotal",  0) AS DECIMAL(18,2))  AS "PAY_TOTAL",
    CAST(COALESCE(p."CashSum",   0) AS DECIMAL(18,2))  AS "CASH_SUM",
    CAST(COALESCE(p."CheckSum",  0) AS DECIMAL(18,2))  AS "CHECK_SUM",
    CAST(COALESCE(p."TrsfrSum",  0) AS DECIMAL(18,2))  AS "TRSFR_SUM",
    COALESCE(TRIM(p."TrsfrRef"), '')                   AS "TRSFR_REF",
    COALESCE(TO_VARCHAR(p."TrsfrDate", 'YYYY-MM-DD'), '') AS "TRSFR_DATE",

    -- Allocation. No VPM2 line at all -> genuinely 0 lines / 0.00 applied (an
    -- on-account payment, FACTS sec.5), not an uncomputable value - MATCH_FLAG
    -- says which, so the renderer never shows a bare zero for it.
    COALESCE(a."AllocCnt",   0)                              AS "ALLOC_CNT",
    CAST(COALESCE(a."AllocTotal",   0) AS DECIMAL(18,2))     AS "ALLOC_TOTAL",
    COALESCE(a."InvCnt",     0)                              AS "INV_CNT",
    CAST(COALESCE(a."InvApplied",   0) AS DECIMAL(18,2))     AS "INV_APPLIED",
    CAST(COALESCE(a."CnApplied",    0) AS DECIMAL(18,2))     AS "CN_APPLIED",
    CAST(COALESCE(a."JeApplied",    0) AS DECIMAL(18,2))     AS "JE_APPLIED",
    CAST(COALESCE(a."OtherApplied", 0) AS DECIMAL(18,2))     AS "OTHER_APPLIED",

    -- What the payment covered that no line accounts for (contract definition).
    CAST(COALESCE(p."DocTotal", 0) - COALESCE(a."AllocTotal", 0) AS DECIMAL(18,2)) AS "UNALLOCATED",

    CASE
        WHEN COALESCE(a."AllocCnt", 0) = 0 THEN 'ON_ACCOUNT'
        WHEN ABS(COALESCE(p."DocTotal", 0) - COALESCE(a."AllocTotal", 0)) <= 1 THEN 'MATCHED'
        ELSE 'PARTIAL'
    END                                                AS "MATCH_FLAG",

    -- Tabs / CR / LF -> space (two Mart comments carry them), trimmed, capped at 150.
    COALESCE(
        SUBSTRING(
            TRIM(REPLACE(REPLACE(REPLACE(p."Comments", CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')),
            1, 150),
        '')                                            AS "REMARKS"
FROM PAY p
LEFT JOIN ALLOC a
       ON a."PayEntry" = p."DocEntry"
ORDER BY p."DocDate" DESC, p."DocNum" DESC;
