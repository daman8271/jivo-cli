# Spec — `dsr items` command group (Product Master)

Read-only subcommands for the SKU catalogue (`Masters > Item`).
Study doc: [`study/vault/product-master.md`](../vault/product-master.md).

## Ergonomics (mirror the existing CLI)

- Group lives under `dsr items …`, alongside `query` / `count` / `peek` / `schema`.
- Inherits the global flags: `--json`, `--compact`, `--csv`, `--select`, `-n/--limit`,
  `-q/--quiet`, `-d/--db`, `--timeout`.
- Default output is the aligned table renderer with the `(N rows)` footer; `--json` for machines.
- Every subcommand is a single parameterised `SELECT` behind the SELECT-only guard.
- Shared defaults applied unless overridden:
  - live rows only (`tbl_item.deleted = 0`) — `--include-deleted` to lift it,
  - names trimmed (`LTRIM(RTRIM(itemName))`),
  - date sentinels excluded (`> '1900-01-01'`),
  - sales joins drop `productId <= 0` sentinels and use `ISNULL(ps.deleted,0)=0`.

Common flags reused across subcommands:

| Flag | Meaning |
|---|---|
| `--search <text>` | case-insensitive `itemName` / `itemCode` substring |
| `--type <name\|id>` | filter by `tbl_itemType` (accepts `MUSTARD` or `4`) |
| `--group <name>` | pack-size group (`1 LTR`, `5 LTR`, …) — matches `tbl_item.itemGroup` text |
| `--visible so\|promoter\|retailer` | filter by the matching visibility bit |
| `--scheme` / `--redeemable` | only `isScheme = 1` / `isRedeemable = 1` |
| `--include-deleted` | include soft-deleted SKUs and show `deletionDate`/`deleteReason` |
| `--from` / `--to` (YYYY-MM-DD) | date window (creation date, or sale date for `items sales`) |
| `--state <name\|id>` | restrict via `tbl_itemStates` → `tbl_states` |

---

## 1. `dsr items list`

List the live SKU catalogue with variant, pack group, UOM, pieces-per-case, GST and visibility.

Flags: `--search`, `--type`, `--group`, `--visible`, `--scheme`, `--redeemable`,
`--include-deleted`, `--from/--to` (on `CreatedOn`), `-n`.

```sql
SELECT i.Id,
       LTRIM(RTRIM(i.itemName))               AS itemName,
       i.itemCode,
       t.typeName                             AS variant,
       COALESCE(g.ItemGroupName, i.itemGroup) AS packGroup,
       u.UOMName                              AS uom,
       i.piecesPerCase,
       i.quantity                             AS packSize,
       i.gst,
       i.visibleToSo, i.visibleToPromoter, i.isVisibleToRetailer,
       i.isScheme, i.isRedeemable,
       i.CreatedBy, i.CreatedOn
FROM tbl_item i
LEFT JOIN tbl_itemType      t ON t.Id = i.itemType
LEFT JOIN tbl_UOMMaster     u ON u.ID = i.UOM
LEFT JOIN tbl_ItemGroupName g ON g.ItemGroupName = i.itemGroup
WHERE (@includeDeleted = 1 OR i.deleted = 0)
  AND (@search  IS NULL OR i.itemName LIKE '%' + @search + '%' OR i.itemCode LIKE '%' + @search + '%')
  AND (@typeId  IS NULL OR i.itemType = @typeId)
  AND (@group   IS NULL OR i.itemGroup = @group)
  AND (@visSo   = 0 OR i.visibleToSo = 1)
  AND (@visProm = 0 OR i.visibleToPromoter = 1)
  AND (@visRet  = 0 OR i.isVisibleToRetailer = 1)
  AND (@scheme  = 0 OR i.isScheme = 1)
  AND (@redeem  = 0 OR i.isRedeemable = 1)
  AND (@from IS NULL OR i.CreatedOn >= @from)
  AND (@to   IS NULL OR i.CreatedOn <  DATEADD(day, 1, @to))
ORDER BY t.typeName, i.itemName;
```

## 2. `dsr items show <id|name>`

Full detail for one SKU: all master fields decoded, plus its images, flavour row and state mapping.

Flags: none beyond globals (accepts a numeric `Id` or an exact/unique name fragment).

```sql
-- header
SELECT i.*, t.typeName AS variant, u.UOMName AS uom,
       COALESCE(g.ItemGroupName, i.itemGroup) AS packGroup
FROM tbl_item i
LEFT JOIN tbl_itemType      t ON t.Id = i.itemType
LEFT JOIN tbl_UOMMaster     u ON u.ID = i.UOM
LEFT JOIN tbl_ItemGroupName g ON g.ItemGroupName = i.itemGroup
WHERE i.Id = @id;

-- images
SELECT imageId, imageURL FROM tbl_ItemImages WHERE productId = @id AND deleted = 0;

-- flavour / packaging (beverages)
SELECT f.flavours, f.options AS packaging, ft.typeName AS flavourItemType
FROM tbl_flavours f
LEFT JOIN tbl_itemType ft ON ft.Id = TRY_CAST(f.itemtype AS int)
WHERE f.itemid = @id;

-- states this SKU is enabled in
SELECT s.stateId, s.state
FROM tbl_itemStates ist
JOIN tbl_states s ON s.stateId = ist.stateId
WHERE ist.itemId = @id
ORDER BY s.state;
```

## 3. `dsr items types`

List the lookup masters: item types, UOMs and pack-size groups, each with live SKU counts.

Flags: `--kind type|uom|group` (default: print all three sections), `--include-deleted`.

```sql
-- item types
SELECT t.Id, t.typeName,
       SUM(CASE WHEN i.deleted = 0 THEN 1 ELSE 0 END) AS liveSkus,
       COUNT(i.Id)                                    AS allSkus
FROM tbl_itemType t
LEFT JOIN tbl_item i ON i.itemType = t.Id
WHERE (@includeDeleted = 1 OR t.deleted = 0)
GROUP BY t.Id, t.typeName
ORDER BY liveSkus DESC, t.typeName;

-- UOMs
SELECT u.ID, u.UOMName,
       SUM(CASE WHEN i.deleted = 0 THEN 1 ELSE 0 END) AS liveSkus
FROM tbl_UOMMaster u
LEFT JOIN tbl_item i ON i.UOM = u.ID
WHERE (@includeDeleted = 1 OR u.deleted = 0)
GROUP BY u.ID, u.UOMName ORDER BY u.ID;

-- pack-size groups (NOTE: tbl_item.itemGroup stores the NAME, not the Id)
SELECT g.Id, g.ItemGroupName,
       SUM(CASE WHEN i.deleted = 0 THEN 1 ELSE 0 END) AS liveSkus
FROM tbl_ItemGroupName g
LEFT JOIN tbl_item i ON i.itemGroup = g.ItemGroupName
GROUP BY g.Id, g.ItemGroupName ORDER BY g.Id;
```

## 4. `dsr items visibility`

Matrix of how many SKUs each app can see, by variant — the quickest way to answer
"why can't the SO see this SKU?".

Flags: `--type`, `--by type|group` (grouping dimension, default `type`), `--missing`
(list the individual SKUs hidden from all three apps instead of the summary).

```sql
-- summary (--by type)
SELECT t.typeName                                                       AS variant,
       COUNT(*)                                                         AS skus,
       SUM(CASE WHEN i.visibleToSo = 1 THEN 1 ELSE 0 END)               AS inSoApp,
       SUM(CASE WHEN i.visibleToPromoter = 1 THEN 1 ELSE 0 END)         AS inPromoterApp,
       SUM(CASE WHEN i.isVisibleToRetailer = 1 THEN 1 ELSE 0 END)       AS inRetailerApp,
       SUM(CASE WHEN ISNULL(i.visibleToSo,0) = 0
                 AND ISNULL(i.visibleToPromoter,0) = 0
                 AND ISNULL(i.isVisibleToRetailer,0) = 0 THEN 1 ELSE 0 END) AS hiddenEverywhere
FROM tbl_item i
LEFT JOIN tbl_itemType t ON t.Id = i.itemType
WHERE i.deleted = 0 AND (@typeId IS NULL OR i.itemType = @typeId)
GROUP BY t.typeName
ORDER BY skus DESC;

-- --missing
SELECT i.Id, LTRIM(RTRIM(i.itemName)) AS itemName, t.typeName, i.CreatedBy, i.CreatedOn
FROM tbl_item i
LEFT JOIN tbl_itemType t ON t.Id = i.itemType
WHERE i.deleted = 0
  AND ISNULL(i.visibleToSo,0) = 0
  AND ISNULL(i.visibleToPromoter,0) = 0
  AND ISNULL(i.isVisibleToRetailer,0) = 0
ORDER BY i.CreatedOn DESC;
```

## 5. `dsr items audit`

Catalogue-hygiene report: live SKUs missing an image, HSN code, pieces-per-case, pack group or
GST, plus orphan image rows. Intended as the "clean up the Item master" checklist.

Flags: `--gap image|hsn|pcs|group|gst|orphan` (repeatable; default = all), `--type`.

```sql
SELECT i.Id, LTRIM(RTRIM(i.itemName)) AS itemName, t.typeName,
       CASE WHEN im.productId IS NULL THEN 1 ELSE 0 END                                  AS noImage,
       CASE WHEN i.HSNCode IS NULL OR i.HSNCode IN ('', '0') THEN 1 ELSE 0 END           AS noHsn,
       CASE WHEN ISNULL(i.piecesPerCase, 0) = 0 THEN 1 ELSE 0 END                        AS noPiecesPerCase,
       CASE WHEN i.itemGroup IS NULL
              OR NOT EXISTS (SELECT 1 FROM tbl_ItemGroupName g
                             WHERE g.ItemGroupName = i.itemGroup) THEN 1 ELSE 0 END      AS badPackGroup,
       CASE WHEN i.gst IS NULL THEN 1 ELSE 0 END                                          AS noGst
FROM tbl_item i
LEFT JOIN tbl_itemType t ON t.Id = i.itemType
LEFT JOIN (SELECT DISTINCT productId FROM tbl_ItemImages WHERE deleted = 0) im
       ON im.productId = i.Id
WHERE i.deleted = 0
  AND (@typeId IS NULL OR i.itemType = @typeId)
ORDER BY i.Id;

-- --gap orphan : image rows whose SKU no longer exists
SELECT im.imageId, im.productId, im.imageURL
FROM tbl_ItemImages im
LEFT JOIN tbl_item i ON i.Id = im.productId
WHERE im.deleted = 0 AND i.Id IS NULL;
```

## 6. `dsr items sales`

Secondary-sales volume per SKU over a window, in **pieces and cases** (cases = pieces ÷
`piecesPerCase`) — the join most people get wrong.

Flags: `--from`, `--to` (default: last 90 days), `--type`, `--group`, `--salesperson <personId>`,
`--retailer <retailerId>`, `--zone <zoneId>`, `--beat <beatId>`, `--state`, `--distributor <distId>`,
`--top N`, `--promoter` (read `tbl_ProductsSoldPromoter`/`tbl_SalesReportPromoter` instead),
`--include-scheme` (also count `tbl_SchemeProductsSold` free-goods lines).

```sql
SELECT i.Id,
       LTRIM(RTRIM(i.itemName))                                            AS itemName,
       t.typeName                                                          AS variant,
       COUNT(DISTINCT sr.salesId)                                          AS salesCalls,
       COUNT(DISTINCT sr.retailerId)                                       AS retailers,
       SUM(ps.pieces)                                                      AS pieces,
       CAST(SUM(ps.pieces) * 1.0 / NULLIF(i.piecesPerCase, 0) AS decimal(18,2)) AS cases
FROM tbl_ProductsSold ps
JOIN tbl_SalesReport sr ON sr.salesId = ps.salesId AND sr.deleted = 0
JOIN tbl_item        i  ON i.Id = ps.productId
LEFT JOIN tbl_itemType t ON t.Id = i.itemType
WHERE ISNULL(ps.deleted, 0) = 0          -- live rows have deleted = NULL, not 0
  AND ps.productId > 0                   -- drop the 0 / -1 sentinels (~34k rows)
  AND sr.date > '1900-01-01'             -- 1899-12-30 empty-date sentinel
  AND sr.date >= @from AND sr.date <= @to
  AND (@typeId   IS NULL OR i.itemType   = @typeId)
  AND (@group    IS NULL OR i.itemGroup  = @group)
  AND (@personId IS NULL OR sr.personId  = @personId)
  AND (@retailer IS NULL OR sr.retailerId= @retailer)
  AND (@zoneId   IS NULL OR sr.zoneId    = @zoneId)
  AND (@stateId  IS NULL OR sr.stateId   = @stateId)
  AND (@distId   IS NULL OR sr.distId    = @distId)
GROUP BY i.Id, i.itemName, t.typeName, i.piecesPerCase
ORDER BY pieces DESC;
```
*Verified live: top rows over the last 90 days are `500 ml ArshNaturalWater(24PCS)` 224 844 pcs /
9 368.50 cases, `1LTR Coldpress (20 pack)` 110 117 pcs / 5 505.85 cases.*

## 7. `dsr items unsold`

Live, SO-visible SKUs with **zero** secondary sales in the window — dead catalogue entries or
distribution gaps.

Flags: `--from`, `--to` (default last 90 days), `--type`, `--zone`, `--state`, `--visible`.

```sql
SELECT i.Id, LTRIM(RTRIM(i.itemName)) AS itemName, t.typeName, i.CreatedOn
FROM tbl_item i
LEFT JOIN tbl_itemType t ON t.Id = i.itemType
WHERE i.deleted = 0
  AND (@visSo = 0 OR i.visibleToSo = 1)
  AND (@typeId IS NULL OR i.itemType = @typeId)
  AND NOT EXISTS (
        SELECT 1
        FROM tbl_ProductsSold ps
        JOIN tbl_SalesReport sr ON sr.salesId = ps.salesId AND sr.deleted = 0
        WHERE ps.productId = i.Id
          AND ISNULL(ps.deleted, 0) = 0
          AND sr.date >= @from AND sr.date <= @to
          AND (@zoneId  IS NULL OR sr.zoneId  = @zoneId)
          AND (@stateId IS NULL OR sr.stateId = @stateId))
ORDER BY i.CreatedOn DESC;
```

## 8. `dsr items states`

Which SKUs are enabled in which state (`tbl_itemStates`), and the reverse.

Flags: `--state <name|id>` (SKUs enabled there), `--item <id>` (states for one SKU),
`--unmapped` (live SKUs with no state row at all).

```sql
-- default: coverage summary
SELECT s.stateId, s.state, COUNT(*) AS liveSkus
FROM tbl_itemStates ist
JOIN tbl_item   i ON i.Id = ist.itemId AND i.deleted = 0
JOIN tbl_states s ON s.stateId = ist.stateId
GROUP BY s.stateId, s.state
ORDER BY liveSkus DESC;

-- --unmapped
SELECT i.Id, LTRIM(RTRIM(i.itemName)) AS itemName, t.typeName
FROM tbl_item i
LEFT JOIN tbl_itemType t ON t.Id = i.itemType
WHERE i.deleted = 0
  AND NOT EXISTS (SELECT 1 FROM tbl_itemStates ist WHERE ist.itemId = i.Id)
ORDER BY i.Id;
```

---

## Implementation notes

1. `--type` accepts a name → resolve via `SELECT Id FROM tbl_itemType WHERE LTRIM(RTRIM(typeName)) = @name`
   (note `'SESAME OIL '` has a trailing space).
2. `--group` matches the **text** in `tbl_item.itemGroup`, not `tbl_ItemGroupName.Id`.
3. Never emit `SAPID` as a SAP bridge — it is NULL on all 333 rows; if a SAP cross-walk is ever
   needed it has to be name-based against SAP B1 `Items`.
4. `MRP`, `price`, `cashRate`, `isCashback` are effectively unpopulated; keep them out of default
   output and expose only under `items show`.
5. Case conversion always uses `piecesPerCase` (reliable), never `quantity` (unreliable pack size).
6. All statements are `SELECT`-only and pass the existing guard; the group adds no write path.
