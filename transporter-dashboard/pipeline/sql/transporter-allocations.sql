-- ============================================================================
-- transporter-allocations.sql   —   THE MAPPING TABLE
-- ----------------------------------------------------------------------------
-- One row per VPM2 allocation line, for every non-cancelled Outgoing Payment
-- (OVPM) made to a TRANSPORTER vendor (OCRD.GroupCode = 102, CardType = 'S')
-- with payment DocDate >= 2025-04-01.  This is the dataset that draws the
-- payment -> invoice diagram, so it is complete: no InvType is dropped.
--
-- Run once per book.  Replace {{SCHEMA}} with exactly one of:
--   JIVO_OIL_HANADB | JIVO_MART_HANADB | JIVO_BEVERAGES_HANADB
-- NEVER union the three books together (FACTS §8.7).
--
-- HOW TO RUN (this bit matters):
--   cd hana-sql && ./hana-sql -env ../connections/hana-tunnel.env -f <file>
-- Use -f (or stdin).  Passing the file's text as the positional argument
-- FAILS: the first line begins with "--" and the Go flag parser eats it as a
-- flag ("flag provided but not defined: -").  The SQL itself is fine.
--
-- ---------------------------------------------------------------------------
-- THE JOIN (FACTS §2) — VPM2's two key columns are named backwards:
--     VPM2."DocNum"   = the PAYMENT's  OVPM."DocEntry"
--     VPM2."DocEntry" = the TARGET document's DocEntry
-- Getting this the other way round silently returns plausible-looking wrong
-- rows.  Verified live on Oil payment DocNum 826466599 -> exactly 3 lines
-- (11,518 + 3,760 + 9,378 = 24,656) and 826466786 -> exactly 2 lines
-- (110,749 + 57,648 = 168,397).
--
-- Cancelled flags are spelled differently per table and are three-valued
-- (C-0021): OVPM."Canceled" / OPCH."CANCELED" / ORPC."CANCELED".  Always
-- compare = 'N', never <> 'Y' (that keeps the 'C' system mirrors).
--
-- ---------------------------------------------------------------------------
-- TSV CONTRACT for whoever loads this:
--   * hana-sql prints a SQL NULL as the four-character token  NULL .
--     Every TGT_* column is deliberately NULL when the target document was not
--     resolved, so the loader MUST treat the literal string "NULL" as missing
--     and render "(document outside window)" — never as 0 and never as blank.
--   * Amounts are plain rupees, 2 decimal places, no grouping, no symbol.
--     Formatting to Indian digit grouping is the UI's job.
--   * Dates are 'YYYY-MM-DD' strings.
--   * SUM_APPLIED is NEGATIVE for InvType 46 (an on-account outgoing payment
--     applied later) and can be negative for InvType 30.  That is real; do
--     not abs() it.
--   * ONE ROW = ONE VPM2 LINE.  (PAY_DOC_ENTRY, INV_TYPE, TGT_DOC_ENTRY) is
--     NOT unique: a payment can settle several LINES of one Journal Entry
--     (InvType 30), and each is its own VPM2 row with its own amount — they
--     differ only by VPM2."DocLine", which is not in this column contract.
--     Verified live: Oil payment DocEntry 15875 -> JE 148423 on JE lines
--     2, 5, 6, 7, 8 (five rows, five amounts).  NEVER dedupe on that key;
--     keep every row, or the totals stop tying to OVPM."DocTotal".
--
-- ---------------------------------------------------------------------------
-- IN_WINDOW: 'Y' = the target document was resolved and will also be present
-- in the invoice dataset.  'N' = the LEFT JOIN found nothing, because either
--   (a) the target is dated before the 2025-04-01 fetch window (FACTS §6 —
--       real: in-scope payments settle A/P invoices back to 2024-09-30 in Oil,
--       2025-01-01 in Mart, 2024-10-01 in Beverages), or
--   (b) the InvType is one we do not resolve to a document (30 Journal Entry,
--       46 Outgoing Payment, 24/13/14 contra).
-- The row still carries TGT_DOC_ENTRY so the operator can go and look it up.
--
-- ---------------------------------------------------------------------------
-- VERIFIED LIVE 2026-08-22 (all three schemas, via -f):
--   Oil  478 rows / 232 payments   Mart 367 / 179   Beverages 137 / 90
--   Row counts and SUM_APPLIED totals equal a raw VPM2 count/sum for the same
--   payments with no invoice joins — the LEFT JOINs neither fan out nor drop.
--   InvTypes seen: 18, 19, 30, 46.  The ELSE branch below stays regardless.
--   WT_APPLD and DCNT_SUM are 0.00 on every row (FACTS §4).
--
-- Read-only.  This file must never be edited into anything but a SELECT.
-- ============================================================================

WITH pay AS (
    -- Non-cancelled outgoing payments to transporter vendors, FY25 start onward.
    SELECT
        p."DocEntry"   AS PAY_DOC_ENTRY,
        p."DocNum"     AS PAY_DOC_NUM,
        p."DocDate"    AS PAY_DATE_RAW,
        p."CardCode"   AS CARD_CODE,
        p."CardName"   AS CARD_NAME
    FROM {{SCHEMA}}.OVPM p
    JOIN {{SCHEMA}}.OCRD c
      ON  c."CardCode"  = p."CardCode"
      AND c."CardType"  = 'S'
      AND c."GroupCode" = 102
    WHERE p."Canceled" = 'N'
      AND p."DocDate" >= '2025-04-01'
)
SELECT
    pay.PAY_DOC_ENTRY                                        AS PAY_DOC_ENTRY,
    pay.PAY_DOC_NUM                                          AS PAY_DOC_NUM,
    TO_VARCHAR(pay.PAY_DATE_RAW, 'YYYY-MM-DD')               AS PAY_DATE,
    pay.CARD_CODE                                            AS CARD_CODE,
    pay.CARD_NAME                                            AS CARD_NAME,

    l."InvType"                                              AS INV_TYPE,
    CASE l."InvType"
        WHEN '18' THEN 'A/P Invoice'
        WHEN '19' THEN 'A/P Credit Note'
        WHEN '30' THEN 'Journal Entry'
        WHEN '46' THEN 'Outgoing Payment'
        WHEN '24' THEN 'Incoming Payment'
        WHEN '13' THEN 'A/R Invoice'
        WHEN '14' THEN 'A/R Credit Note'
        ELSE 'Other (' || IFNULL(l."InvType", '?') || ')'
    END                                                      AS INV_TYPE_LABEL,

    -- Always present, even when the document itself could not be resolved.
    l."DocEntry"                                             AS TGT_DOC_ENTRY,

    COALESCE(i."DocNum", r."DocNum")                         AS TGT_DOC_NUM,
    TO_VARCHAR(COALESCE(i."DocDate", r."DocDate"),
               'YYYY-MM-DD')                                 AS TGT_DATE,
    -- Vendor's own bill number: A/P invoices only.  Blank (NULL) for every
    -- other type — a credit note has no vendor bill to show here.
    i."NumAtCard"                                            AS TGT_VENDOR_BILL,
    CAST(ROUND(COALESCE(i."DocTotal", r."DocTotal"), 2)
         AS DECIMAL(19, 2))                                  AS TGT_GROSS,
    -- TDS lives on the INVOICE, not the payment (FACTS §4).
    CAST(ROUND(COALESCE(i."WTSum", r."WTSum"), 2)
         AS DECIMAL(19, 2))                                  AS TGT_TDS,

    CAST(ROUND(l."SumApplied", 2) AS DECIMAL(19, 2))         AS SUM_APPLIED,
    -- WtAppld / DcntSum are 0.00 across the board today (FACTS §4).  Kept as
    -- real columns so the day one of them stops being zero, the board shows it.
    CAST(ROUND(l."WtAppld",    2) AS DECIMAL(19, 2))         AS WT_APPLD,
    CAST(ROUND(l."DcntSum",    2) AS DECIMAL(19, 2))         AS DCNT_SUM,

    CASE
        WHEN i."DocEntry" IS NOT NULL OR r."DocEntry" IS NOT NULL THEN 'Y'
        ELSE 'N'
    END                                                      AS IN_WINDOW

FROM pay
-- payment -> its allocation lines.  VPM2."DocNum" IS the payment's DocEntry.
JOIN {{SCHEMA}}.VPM2 l
  ON l."DocNum" = pay.PAY_DOC_ENTRY

-- InvType 18 -> A/P Invoice.  VPM2."DocEntry" IS the invoice's DocEntry.
LEFT JOIN {{SCHEMA}}.OPCH i
  ON  l."InvType"  = '18'
  AND i."DocEntry" = l."DocEntry"
  AND i."CANCELED" = 'N'
  AND i."DocDate" >= '2025-04-01'

-- InvType 19 -> A/P Credit Note.
LEFT JOIN {{SCHEMA}}.ORPC r
  ON  l."InvType"  = '19'
  AND r."DocEntry" = l."DocEntry"
  AND r."CANCELED" = 'N'
  AND r."DocDate" >= '2025-04-01'

ORDER BY
    PAY_DATE      DESC,
    PAY_DOC_NUM   DESC,
    INV_TYPE      ASC,
    TGT_DOC_NUM   ASC,   -- HANA sorts NULL FIRST in ASC, so the unresolved
                         -- targets lead each payment group.  Verified, stable.
    TGT_DOC_ENTRY ASC    -- tiebreaker only: keeps the file byte-stable run to run
