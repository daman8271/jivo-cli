-- ============================================================================
-- transporter-invoices.sql   —   ONE ROW PER A/P INVOICE (OPCH)
-- ----------------------------------------------------------------------------
-- Scope   : invoices of TRANSPORTER vendors (OCRD."CardType"='S' AND
--           OCRD."GroupCode"=102 — same code in all three books, FACTS §1),
--           OPCH."CANCELED"='N', DocDate >= 2025-04-01 (FY25 start, so every
--           FY26 payment can resolve the invoice it settles — FACTS §6).
-- Books   : {{SCHEMA}} is substituted per company with exactly one of
--             JIVO_OIL_HANADB | JIVO_MART_HANADB | JIVO_BEVERAGES_HANADB
--           The three books are SEPARATE. Never union or sum them (FACTS §8.7).
-- Read-only: a single WITH...SELECT. This file must never contain DML.
--
-- Verified live 2026-08-22 against all three schemas: FY26 rows = 194 / 145 / 86
-- with gross 97,00,557 / 81,55,440 / 34,71,531 — exactly FACTS §1 — and the four
-- FACTS §4 invoices (626074214 / 626074300 / 626074292 / 626074367) reproduce
-- to the rupee.
--
-- ---------------------------------------------------------------------------
-- THE JOIN (FACTS §2 — VPM2's two key columns are named backwards):
--     VPM2."DocNum"   = the PAYMENT's  OVPM."DocEntry"     <- payment -> lines
--     VPM2."DocEntry" = the TARGET document's DocEntry     <- line -> invoice
-- and the InvType='18' filter is MANDATORY on that second join: VPM2."DocEntry"
-- keys a DIFFERENT table for every InvType (18->OPCH, 19->ORPC, 30->OJDT,
-- 46->OVPM ...). Proved live 2026-08-22 on Oil: all 2,041 non-cancelled
-- InvType='30' lines resolve to an OJDT.TransId that carries a JDT1 line on the
-- payment's own vendor; 52 of them merely collide numerically with some OPCH
-- DocEntry and NONE of those is the same vendor. Across the three books, every
-- non-'18' line whose DocEntry equals a transporter-invoice DocEntry
-- (Oil 1x30 + 2x46, Mart 1x46, Bev 2x46) belongs to ANOTHER vendor, i.e. is a
-- collision, not a settlement. So SETTLED_BY below can only ever hold '18'
-- (paid by outgoing-payment lines) or '' (no payment line) — VPM2 cannot
-- express "settled by journal" per invoice. Where that signal really lives is
-- documented under PAID_TO_DATE.
--
-- Cancelled flags are spelled differently per table and are three-valued
-- (C-0021): OPCH."CANCELED" (upper) / OVPM."Canceled" (mixed).
-- Always = 'N'. Never <> 'Y' — that keeps the 'C' system mirrors.
--
-- TDS lives on the INVOICE, not the payment (FACTS §4): VPM2."WtAppld" and
-- VPM2."DcntSum" are 0.00 across the board. TDS = OPCH."WTSum" (headline);
-- TDS_APPLIED = OPCH."WTApplied" (cross-check only — differs on most rows).
-- OPCH."DiscSum" is 0 on every row today; the column is kept because the
-- reconciliation line needs it.
--
-- ---------------------------------------------------------------------------
-- THE RECONCILIATION LINE (FACTS §4), per row:
--     GROSS − TDS − DISCOUNT − OTHER_DEDUCTION = NET_PAID
-- OTHER_DEDUCTION is the RESIDUAL, not a known deduction. Render it as
-- "unexplained — shortage/damage claim or settled by journal", never as a
-- verified figure. It is NULL (never 0) when PAY_CNT = 0, because a balancing
-- figure against no payment is meaningless.
--
-- RESIDUAL_FLAG (evaluated in this order — see FACTS.md §9):
--   UNPAID      PAY_CNT = 0 (no non-cancelled payment line at all)
--   OK          |OTHER_DEDUCTION| <= 1           paid net of TDS, reconciles
--   GROSS_PAID  |NET_PAID − GROSS| <= 1          paid in full; TDS on the bill was NOT
--                                               deducted at payment (WTApplied = 0 on
--                                               100% of these rows in all three books)
--   SHORT       OTHER_DEDUCTION > 1              paid less than gross−TDS; gap unexplained
--   OVER        NET_PAID > GROSS + 1             genuinely paid above the bill (0 rows 2026-08-22)
--   PART_TDS    anything else                    deducted something, but less than the TDS
-- Read OVER with FACTS §4 in mind: in 93–96% of OVER rows the residual equals
-- −TDS exactly, i.e. the FULL GROSS was paid and TDS was not withheld at
-- payment. The renderer can tell the two TDS behaviours apart per row:
--     NET_PAID ≈ GROSS − TDS  -> TDS withheld from the payment
--     NET_PAID ≈ GROSS        -> TDS not withheld (handled elsewhere)
--
-- PAID_TO_DATE is OPCH."PaidToDate" — SAP's own "how much of this invoice is
-- settled", which is updated by ANY settlement: payment lines AND internal
-- reconciliation (ITR1) against a journal, an A/P credit note, or an
-- on-account payment matched later. Verified 2026-08-22 in all three books:
-- every invoice with PaidToDate > 0 appears in ITR1 (SrcObjTyp='18'), and
-- every PaidToDate = 0 invoice does not. So:
--     PAY_CNT = 0 AND PAID_TO_DATE > 0  -> settled WITHOUT a payment line
--                                          (reconciliation / JE / CN) — NOT
--                                          "unpaid" in the cash sense.
--                                          Oil 116 / Mart 58 / Bev 118 rows.
--     PAY_CNT = 0 AND PAID_TO_DATE = 0  -> truly untouched.
--                                          Oil 54 / Mart 119 / Bev 38 rows.
--     PAY_CNT > 0 AND PAID_TO_DATE > NET_PAID -> the gap was closed by
--                                          something other than a payment.
-- The UNPAID bucket must therefore be shown split on PAID_TO_DATE, never as
-- one "unpaid" number.
--
-- DOC_STATUS ('O'/'C') is UNRELIABLE at JIVO (C-0019): passed through raw.
-- Never headline "open" from it alone — age from the money, and say so.
--
-- ---------------------------------------------------------------------------
-- TSV CONTRACT for the loader (hana-sql output, header line first):
--   * a SQL NULL prints as the literal four-character token  NULL .
--     OTHER_DEDUCTION is NULL on every PAY_CNT=0 row — treat "NULL" as
--     missing, never parse it as 0.
--   * PAY_NUMS and SETTLED_BY are '' (empty field) when there is no payment.
--   * VENDOR_BILL is never empty: '(none)' when OPCH."NumAtCard" is blank.
--   * BRANCH is the OBPL."BPLName" for OPCH."BPLId"; if the id has no OBPL
--     row it prints 'BPLId <n>' (the raw id, no invented name); '(no branch)'
--     when BPLId is NULL. Live today every row resolves
--     (Oil: FACTORY/DELHI, Mart: DELHI/HARYANA, Bev: FACTORY).
--   * dates are 'YYYY-MM-DD'; money is plain rupees with exactly 2dp, no
--     grouping — Indian grouping / lakhs / crores are the renderer's job.
--   * PAY_CNT counts DISTINCT non-cancelled payments (one payment with several
--     lines on the same invoice counts once). PAY_NUMS lists their OVPM DocNums
--     ascending, capped at ~200 chars (longest today is 40).
--   * ordered by DOC_DATE desc, DOC_NUM desc.
-- ============================================================================

WITH tvendor AS (
    -- Transporter vendor cards (FACTS §1).
    SELECT "CardCode"
    FROM {{SCHEMA}}.OCRD
    WHERE "CardType"  = 'S'
      AND "GroupCode" = 102
),

inv AS (
    -- The invoice population. One row per OPCH document.
    SELECT
        i."DocEntry",
        i."DocNum",
        i."CardCode",
        i."CardName",
        i."DocDate",
        i."TaxDate",
        i."DocDueDate",
        i."NumAtCard",
        i."BPLId",
        i."DocTotal",
        i."VatSum",
        i."WTSum",
        i."WTApplied",
        i."DiscSum",
        i."PaidToDate",
        i."DocStatus"
    FROM {{SCHEMA}}.OPCH i
    INNER JOIN tvendor v
            ON v."CardCode" = i."CardCode"
    WHERE i."CANCELED" = 'N'
      AND i."DocDate" >= '2025-04-01'
),

alloc AS (
    -- Every A/P-invoice allocation line (InvType='18') from a NON-CANCELLED
    -- outgoing payment whose target is one of our invoices. No payment-date
    -- filter on purpose: a payment of any date that touched the invoice counts.
    -- The InvType filter sits on the join itself — see THE JOIN above for why
    -- it is not optional.
    SELECT
        l."DocEntry"    AS INV_ENTRY,
        l."InvType"     AS INV_TYPE,
        l."SumApplied"  AS SUM_APPLIED,
        p."DocEntry"    AS PAY_ENTRY,
        p."DocNum"      AS PAY_NUM
    FROM {{SCHEMA}}.VPM2 l
    INNER JOIN {{SCHEMA}}.OVPM p
            ON p."DocEntry" = l."DocNum"      -- FACTS §2: payment -> its lines
    INNER JOIN inv
            ON inv."DocEntry" = l."DocEntry"  -- FACTS §2: line -> the invoice
           AND l."InvType"   = '18'
    WHERE p."Canceled" = 'N'
),

pay_per_doc AS (
    -- Collapse to one row per (invoice, payment) so PAY_CNT counts DISTINCT
    -- payments even when one payment carries several lines against one invoice.
    SELECT
        INV_ENTRY,
        PAY_ENTRY,
        MAX(PAY_NUM)     AS PAY_NUM,
        SUM(SUM_APPLIED) AS SUM_APPLIED
    FROM alloc
    GROUP BY INV_ENTRY, PAY_ENTRY
),

pay AS (
    SELECT
        INV_ENTRY,
        SUM(SUM_APPLIED) AS NET_PAID,
        COUNT(*)         AS PAY_CNT,
        STRING_AGG(TO_VARCHAR(PAY_NUM), ',' ORDER BY PAY_NUM) AS PAY_NUMS_RAW
    FROM pay_per_doc
    GROUP BY INV_ENTRY
),

settle AS (
    -- Distinct VPM2 InvType codes genuinely linked to this invoice. Because the
    -- link is only defined for InvType='18' (see header), this is '18' whenever
    -- a payment line exists. Kept as an aggregation so a future, verified
    -- cross-type link can be added here without touching the output shape.
    SELECT
        INV_ENTRY,
        STRING_AGG(INV_TYPE, ',' ORDER BY INV_TYPE) AS SETTLED_BY
    FROM (
        SELECT DISTINCT INV_ENTRY, INV_TYPE
        FROM alloc
    ) s
    GROUP BY INV_ENTRY
),

row_calc AS (
    SELECT
        i."DocEntry" AS DOC_ENTRY,
        i."DocNum"   AS DOC_NUM,
        i."CardCode" AS CARD_CODE,
        i."CardName" AS CARD_NAME,
        TO_VARCHAR(i."DocDate",    'YYYY-MM-DD') AS DOC_DATE,
        TO_VARCHAR(i."TaxDate",    'YYYY-MM-DD') AS TAX_DATE,
        TO_VARCHAR(i."DocDueDate", 'YYYY-MM-DD') AS DUE_DATE,

        -- The operator searches by the transporter's own bill number, so this
        -- must never come back null or blank.
        CASE
            WHEN i."NumAtCard" IS NULL OR TRIM(i."NumAtCard") = '' THEN '(none)'
            ELSE TRIM(i."NumAtCard")
        END AS VENDOR_BILL,

        -- Branch resolved to its name via OBPL; falls back to the raw id as
        -- text rather than inventing a name.
        COALESCE(
            b."BPLName",
            'BPLId ' || TO_VARCHAR(i."BPLId"),
            '(no branch)'
        ) AS BRANCH,

        ROUND(i."DocTotal",  2)                     AS GROSS,
        ROUND(i."VatSum",    2)                     AS VAT,
        ROUND(i."DocTotal" - i."VatSum", 2)         AS BASE,
        ROUND(i."WTSum",     2)                     AS TDS,
        ROUND(i."WTApplied", 2)                     AS TDS_APPLIED,
        ROUND(i."DiscSum",   2)                     AS DISCOUNT,

        ROUND(COALESCE(pay.NET_PAID, 0), 2)         AS NET_PAID,
        COALESCE(pay.PAY_CNT, 0)                    AS PAY_CNT,

        -- Residual. Meaningless with no payment -> NULL, never a confident zero.
        CASE
            WHEN COALESCE(pay.PAY_CNT, 0) = 0 THEN NULL
            ELSE ROUND(i."DocTotal" - i."WTSum" - i."DiscSum"
                       - COALESCE(pay.NET_PAID, 0), 2)
        END AS OTHER_DEDUCTION,

        ROUND(i."PaidToDate", 2)                    AS PAID_TO_DATE,

        -- 'O'/'C' is unreliable at JIVO (C-0019). Passed through raw.
        i."DocStatus"                               AS DOC_STATUS,

        CASE
            WHEN pay.PAY_NUMS_RAW IS NULL THEN ''
            WHEN LENGTH(pay.PAY_NUMS_RAW) > 200
                THEN SUBSTRING(pay.PAY_NUMS_RAW, 1, 197) || '...'
            ELSE pay.PAY_NUMS_RAW
        END AS PAY_NUMS,

        COALESCE(settle.SETTLED_BY, '')             AS SETTLED_BY

    FROM inv i
    LEFT JOIN {{SCHEMA}}.OBPL b ON b."BPLId" = i."BPLId"
    LEFT JOIN pay              ON pay.INV_ENTRY    = i."DocEntry"
    LEFT JOIN settle           ON settle.INV_ENTRY = i."DocEntry"
)

SELECT
    DOC_ENTRY,
    DOC_NUM,
    CARD_CODE,
    CARD_NAME,
    DOC_DATE,
    TAX_DATE,
    DUE_DATE,
    VENDOR_BILL,
    BRANCH,
    TO_DECIMAL(GROSS,           19, 2) AS GROSS,
    TO_DECIMAL(VAT,             19, 2) AS VAT,
    TO_DECIMAL(BASE,            19, 2) AS BASE,
    TO_DECIMAL(TDS,             19, 2) AS TDS,
    TO_DECIMAL(TDS_APPLIED,     19, 2) AS TDS_APPLIED,
    TO_DECIMAL(DISCOUNT,        19, 2) AS DISCOUNT,
    TO_DECIMAL(NET_PAID,        19, 2) AS NET_PAID,
    TO_DECIMAL(OTHER_DEDUCTION, 19, 2) AS OTHER_DEDUCTION,
    CASE
        WHEN PAY_CNT = 0                  THEN 'UNPAID'
        WHEN ABS(OTHER_DEDUCTION) <= 1    THEN 'OK'          -- paid gross - TDS - disc
        WHEN ABS(NET_PAID - GROSS) <= 1   THEN 'GROSS_PAID'  -- paid in full; TDS on bill NOT deducted (WTApplied=0)
        WHEN OTHER_DEDUCTION > 1          THEN 'SHORT'       -- paid less than gross - TDS; gap unexplained
        WHEN NET_PAID > GROSS + 1         THEN 'OVER'        -- genuinely paid above the bill
        ELSE                                   'PART_TDS'    -- deducted something, but less than the TDS
    END                                AS RESIDUAL_FLAG,
    TO_DECIMAL(PAID_TO_DATE,    19, 2) AS PAID_TO_DATE,
    DOC_STATUS,
    PAY_CNT,
    PAY_NUMS,
    SETTLED_BY
FROM row_calc
ORDER BY DOC_DATE DESC, DOC_NUM DESC;
