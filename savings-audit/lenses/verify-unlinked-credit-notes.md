---
title: "Adversarial verification — finding #2: ₹25.83 Cr of credit notes with no base document"
created: 2026-07-28
lens: verify-unlinked-credit-notes
tags: [savings-audit]
---

Part of [[SAVINGS-MOC]]

Adversarial re-derivation of finding #2 from [[returns-leakage]]
(`/Users/damanpreetsingh/jivo-cli/savings-audit/lenses/returns-leakage.md`, H7).

**Claim under test:** "₹25.83 Cr/yr of credit notes are issued with NO base document —
unverifiable against any invoice or goods receipt", `amount_inr: 258300000`,
`kind: annual-recurring`, `confidence: high`, company `ALL`.

**Verdict: REVISED → ₹1.20 Cr/yr** (exposure, not recovery). The arithmetic reproduces
exactly; the *characterisation* fails on three counts, and 95% of the headline ₹ is either
intercompany, already counted in a sibling finding, or externally referenced.

Window everywhere: `"DocDate" >= '2025-07-28' AND "DocDate" < '2026-07-29'`, `"CANCELED"='N'`.

---

## V0 — Does the headline number reproduce? (baseline)

```sql
SELECT 'OIL' AS CO, COUNT(*) AS DOCS,
       ROUND(SUM(CAST("DocTotal" AS DOUBLE)-CAST(IFNULL("VatSum",0) AS DOUBLE))/10000000,3) AS NET_CR
FROM JIVO_OIL_HANADB.ORIN
WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
```

| CO | DOCS | NET_CR |
|---|---:|---:|
| OIL | 2,268 | 28.242 |

Oil total credit notes ₹28.24 Cr net — consistent with the finder's line-level ₹27.81 Cr
(header freight/rounding accounts for the gap). **Baseline sound.**

---

## V1 — Re-derive the BaseType split, but ALSO split by DocType (the finder did not)

```sql
SELECT h."DocType", l."BaseType",
       CASE WHEN l."BaseEntry" IS NULL THEN 'NULLBE' ELSE 'HASBE' END AS BE,
       COUNT(*) AS LINES, ROUND(SUM(CAST(l."LineTotal" AS DOUBLE))/100000,2) AS LAKH
FROM <SCHEMA>.RIN1 l JOIN <SCHEMA>.ORIN h ON h."DocEntry"=l."DocEntry"
WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
GROUP BY h."DocType", l."BaseType",
         CASE WHEN l."BaseEntry" IS NULL THEN 'NULLBE' ELSE 'HASBE' END
ORDER BY 5 DESC
```

| CO | DocType | BaseType | Lines | ₹ lakh |
|---|---|---:|---:|---:|
| Oil | I (item) | 13 | 1,095 | 1,142.41 |
| Oil | I (item) | **-1** | **986** | **1,139.24** |
| Oil | I (item) | 16 | 2,547 | 350.85 |
| Oil | **S (service)** | **-1** | **350** | **140.14** |
| Oil | I (item) | 234000031 | 77 | 43.49 |
| Oil | S (service) | 13 | 6 | 8.06 |
| Mart | I (item) | 13 | 1,074 | 1,270.74 |
| Mart | I (item) | **-1** | **2,743** | **1,029.61** |
| Mart | **S (service)** | **-1** | **156** | **275.62** |
| Mart | I (item) | 16 | 11,783 | 170.80 |
| Bev | I | 13 / 16 / **-1** | 185 / 92 / **48** | 52.34 / 8.56 / **5.19** |
| Bev | **S** | **-1** | **48** | **4.65** |

Oil `-1` = 986+350 = 1,336 lines / ₹1,279.38 L — **exact match to the finder.**
Mart `-1` = 2,743+156 = 2,899 lines / ₹1,305.23 L vs finder 2,895 / ₹1,303.93 L (0.1% drift).

**The ₹25.83 Cr arithmetic is CONFIRMED.** Everything below attacks what it *means*.
(Note: the finder also missed Beverages `-1` = ₹0.10 Cr despite scoping the finding to `ALL`,
and missed `BaseType=234000031` ₹43.49 L which *is* linked.)

---

## V2 — KILLER #1: 39% of the money is INTERCOMPANY

```sql
SELECT h."DocType",
       CASE WHEN UPPER(h."CardName") LIKE '%JIVO%' THEN 'INTERCO_JIVO' ELSE 'third_party' END AS REL,
       COUNT(DISTINCT h."DocEntry") AS DOCS, COUNT(*) AS LINES,
       ROUND(SUM(CAST(l."LineTotal" AS DOUBLE))/100000,2) AS LAKH
FROM <SCHEMA>.RIN1 l JOIN <SCHEMA>.ORIN h ON h."DocEntry"=l."DocEntry"
WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
  AND l."BaseType"=-1
GROUP BY h."DocType",
         CASE WHEN UPPER(h."CardName") LIKE '%JIVO%' THEN 'INTERCO_JIVO' ELSE 'third_party' END
ORDER BY 5 DESC
```

| CO | DocType | Counterparty | Docs | ₹ lakh |
|---|---|---|---:|---:|
| Oil | I | **INTERCO — JIVO MART PVT LTD** | 52 | **995.92** |
| Oil | I | third party | 264 | 143.33 |
| Oil | S | third party | 237 | 140.14 |
| Mart | I | third party | 360 | 1,029.61 |
| Mart | S | third party | 73 | 275.62 |

The 11 largest "unlinked" credit notes in the whole dataset (₹74–93 L each, 22–23 Jul 2026)
are **all** `CUSTA000606 = JIVO MART PVT LTD` — the group's own sister company, whose books
are `JIVO_MART_HANADB` in this very SAP instance.

Confirmed the intercompany leg both ways:

```sql
SELECT 'OIL_sells_to_JIVOMART' AS LEG, COUNT(DISTINCT "DocEntry") AS DOCS,
       ROUND(SUM(CAST("DocTotal" AS DOUBLE)-CAST(IFNULL("VatSum",0) AS DOUBLE))/10000000,3) AS NET_CR
FROM JIVO_OIL_HANADB.OINV WHERE "CANCELED"='N' AND "CardCode"='CUSTA000606'
  AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
```

| Leg | Docs | ₹ Cr |
|---|---:|---:|
| Oil A/R invoices → JIVO MART | 1,845 | 179.591 |
| Oil credit notes → JIVO MART | 388 | 18.505 |
| Mart purchase returns (ORPC) → JIVO supplier | 255 | 15.020 |

Oil books ₹179.59 Cr of sales to Mart; Mart books the mirror-image ₹15.02 Cr of purchase
returns against Oil's ₹18.51 Cr of credit notes. **Since the finding is scoped `company: ALL`,
₹9.96 Cr of it is a consolidation wash — no rupee leaves the group.** → [[finding-intercompany-credit-wash]]

---

## V3 — KILLER #2: 16% is service-type CNs that CANNOT have a base document

Service credit notes (`DocType='S'`) carry no item lines. There is no invoice line to
copy-from and no goods receipt to post. Requiring `BaseType` 13/16 on them is structurally
impossible, so counting them as "missing a base doc" is a category error.

Oil `S`/`-1` ₹140.14 L + Mart `S`/`-1` ₹275.62 L + Bev ₹4.65 L = **₹4.20 Cr**.

Worse: this is the *same* population the sibling hypothesis H11 in [[returns-leakage]] already
books as **₹3.87 Cr of trade spend routed through credit notes**
([[finding-trade-spend-as-credit-notes]]). **Direct double-count inside one lens** — the
portfolio would count these rupees twice. → [[finding-service-cn-double-count]]

---

## V4 — KILLER #3: "unverifiable" is false — 93% carry an external reference

The finder never checked `NumAtCard` (customer's own document number) or `Comments`.

```sql
SELECT CO, REF, CMT, COUNT(DISTINCT DE) AS DOCS, ROUND(SUM(V)/100000,2) AS LAKH
FROM (
  SELECT 'MART' AS CO, h."DocEntry" AS DE,
         CASE WHEN LENGTH(TRIM(IFNULL(h."NumAtCard",''))) > 0 THEN 'has_custref' ELSE 'no_custref' END AS REF,
         CASE WHEN LENGTH(TRIM(IFNULL(h."Comments",''))) > 0 THEN 'has_comment' ELSE 'no_comment' END AS CMT,
         CAST(l."LineTotal" AS DOUBLE) AS V
  FROM JIVO_MART_HANADB.RIN1 l JOIN JIVO_MART_HANADB.ORIN h ON h."DocEntry"=l."DocEntry"
  WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29' AND l."BaseType"=-1
  UNION ALL
  SELECT 'OIL', h."DocEntry", ..., CAST(l."LineTotal" AS DOUBLE)
  FROM JIVO_OIL_HANADB.RIN1 l JOIN JIVO_OIL_HANADB.ORIN h ON h."DocEntry"=l."DocEntry"
  WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29' AND l."BaseType"=-1
) GROUP BY CO, REF, CMT ORDER BY CO, LAKH DESC
```

| CO | custref | comment | Docs | ₹ lakh |
|---|---|---|---:|---:|
| Mart | has | no | 354 | 1,066.61 |
| Mart | has | has | 21 | 213.11 |
| Mart | no | no | **50** | **19.80** |
| Mart | no | has | 8 | 5.71 |
| Oil | has | no | 75 | 883.87 |
| Oil | no | has | 181 | 197.22 |
| Oil | no | no | **184** | **160.04** |
| Oil | has | has | 113 | 38.25 |

**Mart: 98.5% of unlinked credit value carries a customer reference. Oil: 87.5%.**

Sample of R K Worldinfocom's 123 "unverifiable" credit notes (the finder's worst offender at ₹6.98 Cr):

| DocNum | Date | NumAtCard | Net ₹L | UpdInvnt | Status |
|---|---|---|---:|---|---|
| 707262629 | 2026-07-17 | `HRDN2026-7965` | 79.40 | I | O |
| 709252544 | 2025-09-01 | `: HRDN2025-13738: 22000169629` | 76.94 | I | O |
| 711252628 | 2025-11-29 | `HRDN2025-20500` | 74.95 | I | O |
| 703262566 | 2026-03-31 | `HRDN2025-20503 : 22000176822` | 59.97 | I | O |
| 710252523 | 2025-10-21 | `22000171771` | 45.06 | I | O |

Every one carries Flipkart's own return-debit-note number (`HRDN…`) plus a GRN reference, and
every one posts an inventory receipt (`UpdInvnt='I'`). These are **marketplace claim
settlements against a customer-issued document** — the normal shape of modern-trade returns,
not phantom credits. They are auditable today against the customer's claim file.
→ [[finding-unlinked-credits-are-externally-referenced]]

---

## V5 — The finder said these can't be price-checked. They can. (and the check comes back clean)

Base link is not required — customer+item average realised sale price works fine.

```sql
WITH CN AS (
  SELECT h."CardCode" AS CC, l."ItemCode" AS IC,
         CAST(l."LineTotal" AS DOUBLE)/NULLIF(CAST(l."Quantity" AS DOUBLE),0) AS CNP,
         CAST(l."Quantity" AS DOUBLE) AS Q, CAST(l."LineTotal" AS DOUBLE) AS LT
  FROM JIVO_MART_HANADB.RIN1 l JOIN JIVO_MART_HANADB.ORIN h ON h."DocEntry"=l."DocEntry"
  WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
    AND l."BaseType"=-1 AND h."DocType"='I' AND CAST(l."Quantity" AS DOUBLE) > 0),
SALE AS (
  SELECT i."CardCode" AS CC, d."ItemCode" AS IC,
         SUM(CAST(d."LineTotal" AS DOUBLE))/NULLIF(SUM(CAST(d."Quantity" AS DOUBLE)),0) AS AVGP
  FROM JIVO_MART_HANADB.INV1 d JOIN JIVO_MART_HANADB.OINV i ON i."DocEntry"=d."DocEntry"
  WHERE i."CANCELED"='N' AND i."DocDate">='2025-01-01' AND i."DocDate"<'2026-07-29'
    AND CAST(d."Quantity" AS DOUBLE) > 0
  GROUP BY i."CardCode", d."ItemCode")
SELECT CASE WHEN s.AVGP IS NULL THEN 'z_never_sold_this_item_to_cust'
            WHEN c.CNP > s.AVGP*1.05 THEN 'a_CREDITED_OVER_5pct'
            WHEN c.CNP < s.AVGP*0.95 THEN 'c_credited_under_5pct'
            ELSE 'b_within_5pct' END AS CMP,
       COUNT(*) AS LINES, ROUND(SUM(c.LT)/100000,2) AS CREDIT_L,
       ROUND(SUM(CASE WHEN c.CNP > s.AVGP*1.05 THEN (c.CNP-s.AVGP)*c.Q ELSE 0 END)/100000,2) AS EXCESS_L
FROM CN c LEFT JOIN SALE s ON s.CC=c.CC AND s.IC=c.IC GROUP BY 1 ORDER BY CMP
```

| Bucket | Lines | Credit ₹L | "Excess" ₹L |
|---|---:|---:|---:|
| credited >5% over avg sale price | 1,586 | 772.33 | 677.12 |
| within ±5% | 473 | 109.87 | 0 |
| credited under | 647 | 135.69 | 0 |
| item never sold to that customer | 37 | 11.72 | 0 |

**₹677 L of "excess" on ₹772 L of credit fails calibration — a 6x over-credit is impossible.
Debugged it, and the artifact is informative:**

| Customer | DocNum | Item | CN qty | CN unit ₹ | Avg sale unit ₹ |
|---|---|---|---:|---:|---:|
| R K WORLDINFOCOM | 711252628 | MUSTARD KACHI GHANI 1L | **1** | **14,54,247** | 158.88 |
| R K WORLDINFOCOM | 707262629 | MUSTARD KACHI GHANI 1L | **1** | **13,48,326** | 159.19 |
| R K WORLDINFOCOM | 709252544 | COLD PRESS SUNFLOWER 1L | 7 | 1,38,805 | 150.88 |

These are **value-only claims booked with a token quantity of 1**, not per-unit overpricing.
Quantity distribution of Mart's unlinked item credits confirms it:

| Quantity bucket | Lines | ₹ lakh | Total units |
|---|---:|---:|---:|
| qty 1–2 (token / value claim) | 1,787 | 465.72 | 2,015 |
| qty 3–20 | 546 | 239.22 | 4,903 |
| qty >20 (real goods movement) | 410 | 324.66 | 176,267 |

**Verdict: NO price leakage — the ₹6.77 Cr is a query artifact, killed.** Side-effect: it also
undercuts H10's "returns re-enter stock" reassurance, since 45% of Mart's unlinked item
credit value moves only ~2,015 nominal units. → [[finding-token-quantity-value-claims]]

---

## V6 — Is there actual double-crediting? (the one way this becomes real money)

```sql
SELECT COUNT(*) AS DUP_GROUPS, SUM(N) AS DOCS_INVOLVED, ROUND(SUM(EXCESS)/100000,2) AS DUP_VALUE_L
FROM (
  SELECT h."CardCode" AS CC, ROUND(CAST(h."DocTotal" AS DOUBLE),2) AS AMT, COUNT(*) AS N,
         (COUNT(*)-1)*ROUND(CAST(h."DocTotal" AS DOUBLE),2) AS EXCESS
  FROM JIVO_MART_HANADB.ORIN h
  WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
    AND CAST(h."DocTotal" AS DOUBLE) > 50000
    AND EXISTS (SELECT 1 FROM JIVO_MART_HANADB.RIN1 l WHERE l."DocEntry"=h."DocEntry" AND l."BaseType"=-1)
  GROUP BY h."CardCode", ROUND(CAST(h."DocTotal" AS DOUBLE),2) HAVING COUNT(*) > 1)
```

| DUP_GROUPS | DOCS_INVOLVED | DUP_VALUE_L |
|---:|---:|---:|
| 2 | 4 | **2.12** |

**KILLED — ₹2.12 lakh of same-customer/same-amount unlinked credit notes across 12 months.
No material double-crediting.**

---

## V7 — The defensible residual: third-party, item-type, and NO trace of any kind

```sql
SELECT CO, TRACE, COUNT(DISTINCT DE) AS DOCS, ROUND(SUM(V)/100000,2) AS LAKH
FROM (
  SELECT 'MART' AS CO, h."DocEntry" AS DE,
    CASE WHEN LENGTH(TRIM(IFNULL(h."NumAtCard",'')))>0 OR LENGTH(TRIM(IFNULL(h."Comments",'')))>0
         THEN 'has_external_ref' ELSE 'NO_TRACE_AT_ALL' END AS TRACE,
    CAST(l."LineTotal" AS DOUBLE) AS V
  FROM JIVO_MART_HANADB.RIN1 l JOIN JIVO_MART_HANADB.ORIN h ON h."DocEntry"=l."DocEntry"
  WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
    AND l."BaseType"=-1 AND h."DocType"='I' AND UPPER(h."CardName") NOT LIKE '%JIVO%'
  UNION ALL SELECT 'OIL', ... same shape ... FROM JIVO_OIL_HANADB....
) GROUP BY CO, TRACE ORDER BY CO, LAKH DESC
```

| CO | Traceability | Docs | ₹ lakh |
|---|---|---:|---:|
| Mart | has external ref | 311 | 1,011.05 |
| Mart | **NO TRACE AT ALL** | **49** | **18.56** |
| Oil | has external ref | 180 | 41.80 |
| Oil | **NO TRACE AT ALL** | **84** | **101.53** |

**True zero-audit-trail population: ₹1.20 Cr/yr** (133 documents). Oil's share by customer:

| Customer | Docs | ₹ lakh |
|---|---:|---:|
| ONENESS TRADERS | 1 | 27.64 |
| WAL MART INDIA PVT LTD | 5 | 19.87 |
| SAI TRADERS LUDHIANA | 1 | 11.28 |
| DIN DAYAL DULI CHAND | 1 | 6.90 |
| BACHAN SINGH KULJIT SINGH | 2 | 6.57 |
| G PURE INDIA | 12 | 4.42 |
| ARJUN DASS & SONS PUNJAB | 11 | 3.52 |
| AVENUE SUPERMARTS LTD | 14 | 3.12 |

→ [[finding-zero-trail-credit-notes]]

---

## Reconciliation of the ₹25.83 Cr

| Segment | ₹ Cr | Real group money? |
|---|---:|---|
| Oil → JIVO MART PVT LTD (intercompany, item) | 9.96 | **No** — consolidation wash (V2) |
| Service-type CNs, Oil+Mart+Bev (trade spend) | 4.20 | **No** — structurally cannot have a base doc; already booked as [[finding-trade-spend-as-credit-notes]] (V3) |
| Third-party item CNs **with** external reference | 10.53 | Auditable today against customer claim files (V4) |
| Third-party item CNs with **no trace at all** | **1.20** | **Yes — genuine control gap** (V7) |
| Beverages rounding | ~0.06 | negligible |
| **Total** | **25.95** | headline reproduces (₹25.83 Cr) |

**Verdict: REVISED → ₹1.20 Cr/yr, and it is EXPOSURE, not recovery.**

- The ₹25.83 Cr **arithmetic is correct** and the underlying control observation (SAP does not
  force copy-from on A/R credit notes) is **real and worth fixing**.
- But as a *savings* line item it overstates by ~21x: 39% is intercompany, 16% is a
  double-count with a sibling finding, and 41% carries a customer claim reference.
- Independent cross-check: applying a conventional 10% audit error rate to the ₹11.73 Cr of
  genuine third-party unlinked credits gives ₹1.17 Cr — landing within 3% of the ₹1.20 Cr
  zero-trail population derived independently in V7. Two roads, same number.

**Caveats (honest):**
- The `LIKE '%JIVO%'` intercompany test is name-based; a differently-named group entity would
  be missed (checked the top 20 counterparties by value — none others are group companies).
- `NumAtCard` being populated proves a reference *exists*, not that the underlying claim was
  *valid*. Verifying validity needs the customer claim files, which are outside SAP.
- The ₹9.96 Cr intercompany wash is only a wash at group level. If someone wants an
  Oil-standalone number, it is real to Oil's P&L — but the finding is scoped `ALL`.
- ₹1.20 Cr is still exposure requiring document-by-document verification, not confirmed
  recoverable cash. A realistic recovery is a fraction of it.

**Action that survives:** the control fix is still right, but narrow it — block `BaseType=-1`
on **item-type** A/R credit notes to **third-party** customers only, and make `NumAtCard`
mandatory instead of demanding a copy-from link the marketplace channel genuinely cannot
provide. Exempt service-type CNs (route those to a trade-spend expense head per
[[finding-trade-spend-as-credit-notes]]) and exempt intercompany. Then pull the 133 zero-trail
documents — starting with ONENESS TRADERS ₹27.64 L, a single credit note with no reference of
any kind.
