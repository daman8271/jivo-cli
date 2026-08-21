# ARY — access + queries (Microsoft SQL Server)

**"ARY"** is a **Microsoft SQL Server 2017** host at **`138.252.101.118:1433`**
(JOY SERVICES range `138.252.101.0/24` — the same vendor as the new SAP HANA box
`.222`). Login handed over 2026-08-21. It hosts **72 databases**, including the
two that matter:

| Database | What it is |
|---|---|
| **`FR8HODBNEW`** | **LIVE Distributor-Management System (DMS)** — the "ARY" sales data. ~290 tables, ~10 GB. Bills for principals J.L Enterprises, Vanesa Care (Denver & Envy), Honasa/Mamaearth, Unicorn Infosolutions (Apple). |
| `ARY_BSU` | SAP B1 **SQL-version** company *"Akal Rozgar Yojana A Unit Of Jivo Wellness Pvt Ltd (BSU)"*. Journals through FY24-25 (2025-03-31). |

Others on the box: `SBO-COMMON` (SAP B1 SQL install), `JIVO_SAP_RECOVERED_DATA`,
`Jivo_All_Branches_Live`, `jsap`/`jsaplive3`, many `BusyComp000N_db*` (Busy
accounting), the DSR family. (The **live DSR portal** DB is a *different* box —
`103.89.45.75`.)

## Reachability

**Reachable from home / VPS / anywhere** (TCP 1433 + ICMP open) — unlike the
office-IP-filtered SAP HANA box `.222` (see `SAP-HOME-ACCESS.md`). No tunnel
needed.

## How to query (read-only)

`sa` is the **login**, not a database — connect to `master`, pick a DB with
`--db`. There is no `pymssql`/`pyodbc`/`sqlcmd` on the Macs; the repo's
`dsr-cli/dsr` Go binary is the working SQL Server client (SELECT-only guard +
always-rolled-back transaction — it cannot write).

Credentials live in **`connections/ary.env`** (gitignored — this repo is
PUBLIC; ask IT for the password, never commit it):

```bash
set -a; . connections/ary.env; set +a          # or export DSR_HOST/PORT/USER/PASSWORD/DATABASE
./dsr-cli/dsr doctor                             # server 2017, sysadmin=yes, 72 user DBs
echo "SELECT name FROM sys.databases WHERE database_id>4 ORDER BY name;" | ./dsr-cli/dsr query
```

## FR8HODBNEW — the sales schema (verified)

- **`SaleHeader`** — one row per bill. `VoucherDate` (smalldatetime), `BillAmount`
  (final bill value, tax-inclusive; ≈ `SubTotal`), `TaxTotal`, `QtyTotal`,
  `Status` (all live sales = **2**), `SerialNumber` (bill id / join key),
  `LocationID`.
- **`SaleDetail`** — bill lines. Join `SaleDetail.SerialNumber = SaleHeader.SerialNumber`.
  `FinalSaleAmount` (line value), **`WarehouseID`** (warehouse is at the LINE
  level, not the header), `ProductID`, `SaleRate`.
- **`WarehouseMaster`** (12 rows) — `WarehouseID` → `WarehouseName`
  (Ary Pos, Ary Clothing, Fruits & Vegetables, …).
- **`PrincipalCompanyMaster`** — the brands billed.

### Today's sale
```sql
SELECT COUNT(*) bills, SUM(BillAmount) sale
FROM SaleHeader
WHERE VoucherDate >= CONVERT(date, GETDATE())
  AND VoucherDate <  DATEADD(day, 1, CONVERT(date, GETDATE()));
```

### Sales per warehouse (today)
```sql
SELECT w.WarehouseName,
       COUNT(DISTINCT h.SerialNumber) bills,
       CAST(SUM(d.FinalSaleAmount) AS DECIMAL(18,2)) sale
FROM SaleHeader h
JOIN SaleDetail d ON d.SerialNumber = h.SerialNumber
JOIN WarehouseMaster w ON w.WarehouseID = d.WarehouseID
WHERE h.VoucherDate >= CONVERT(date, GETDATE())
  AND h.VoucherDate <  DATEADD(day, 1, CONVERT(date, GETDATE()))
GROUP BY w.WarehouseName
ORDER BY sale DESC;
```
Line totals reconcile to the header `BillAmount` (~₹5 rounding across a day).

## Notes / cautions
- `sa` is a **sysadmin** and the box runs **no host firewall** — `dsr`'s
  read-only guard is the only thing preventing writes. Never bypass it.
- Keep the password out of every tracked file. Repo is public
  (see the env-vault leak history).
