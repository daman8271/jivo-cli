# HAVE-vs-NEED rebuild — the queries behind every number (2026-08-31)

Snapshot pulled live from FusionERP8 / FR8HODBNEW via `./ary query` (read-only,
SELECT-guarded). Window: **2025-08-31 ≤ VoucherDate < 2026-08-31** (last full data
day 2026-08-30). Retail always excludes customer `002CM` (Hunger Heroes NGO wholesale).

## The four extracts (joined into one master snapshot on ProductID)

Products (21,479 rows):
```sql
SELECT p.ProductID, p.ProductName, g.ProductGroupName, s.SubGroupName, b.BrandName,
       CAST(p.IsActive AS int), p.MaxRetailPrice
FROM ProductMaster p
LEFT JOIN ProductGroupMaster g ON g.ProductGroupID=p.ProductGroupID
LEFT JOIN SubGroupMaster s ON s.SubGroupID=p.SubGroupID
LEFT JOIN BrandMaster b ON b.BrandID=p.BrandID
```

12-month retail sales per product (6,138 rows; ₹6.99 Cr total — reconciles with the
verified ₹6.96 Cr on the 9-day-earlier window):
```sql
SELECT d.ProductID, SUM(d.Quantity), SUM(d.FinalSaleAmount),
       COUNT(DISTINCT CONVERT(date,h.VoucherDate)), MAX(h.VoucherDate)
FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber=d.SerialNumber
WHERE h.VoucherDate >= '2025-08-31' AND h.VoucherDate < '2026-08-31'
  AND h.CustomerID <> '002CM'
GROUP BY d.ProductID
```

Bills per product (same window/filters): `COUNT(DISTINCT d.SerialNumber)`.

Stock now (`Stock.Quantity` is the system's own on-hand — verified identity holds on
104,221/104,221 rows; `ProductMaster.QuantityOnHand` is dead):
```sql
SELECT ProductID, SUM(Quantity) FROM Stock GROUP BY ProductID
```

12-month purchases per product:
```sql
SELECT d.ProductID, SUM(d.Quantity), MAX(h.VoucherDate)
FROM PurchaseDetail d JOIN PurchaseHeader h ON h.SerialNumber=d.SerialNumber
WHERE h.IsDeleted=0 AND d.IsDeleted=0
  AND h.VoucherDate >= '2025-08-31' AND h.VoucherDate < '2026-08-31'
GROUP BY d.ProductID
```

## Classification method

1. Wide-recall mechanical matcher: token stems (full + 5-char prefix) from each demand
   line's `line` + `examples`, substring over punctuation-normalized names, plus fuzzy
   (difflib ≥0.80) at vocabulary level. Up to 14 candidates/line with sales+stock attached.
2. One judgment agent per category read the candidate names (never the category tree)
   and classified each line HAVE / LISTED_DEAD / MISSING; every MISSING required
   documented alternate-stem searches first.
3. Adversarial verifiers re-attacked every MISSING call (alternate spellings, short
   stems, Hindi names, generic-drug brands) and sampled HAVE calls for false positives.
   Corrections in `_verifier-corrections.json`; per-category calls in `<category>.json`.

## Status definitions

- **HAVE** — a genuine matching product sold in the window (retail, qty > 0)
- **LISTED_DEAD** — genuine match exists in the catalogue; none sold in 12m
- **MISSING** — nothing in the catalogue is genuinely this product
- Out-of-stock flags exclude fresh produce groups (Fruits/Vegetable — day-stocked)
  and service lines (never purchased, deeply negative stock, e.g. stitching charges)

Priority = essentiality × cohort reach × margin × ease (drug licence / cold chain
penalised), owner's pilot picks (male grooming, cosmetics, sunblock) ×1.3.
₹/month estimates are planning figures benchmarked to the ₹14,600–46,300/yr a
performing ARY line actually earns (Owner-Brief arithmetic). ESTIMATED, not verified.
