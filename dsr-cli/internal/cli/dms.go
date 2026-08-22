package cli

// `dsr dms` — the ARY Distributor-Management System (database FR8HODBNEW on
// 138.252.101.118) expressed as business commands instead of a SQL shell.
//
// Why it lives inside dsr-cli rather than being a new CLI: dsr's db layer is
// already the only working SQL Server client in this repo and it is read-only by
// construction — every statement passes GuardReadOnly (single SELECT/WITH only)
// and runs inside a transaction that is ALWAYS rolled back. Adding a new client
// would mean a second read-only guard to keep correct and a second auth surface.
// This file adds no client, no credential path and no write verb: it only builds
// SELECT text and hands it to runSelect().
//
// -------------------------------------------------------------------- schema
// Verified live 2026-08-22 against FR8HODBNEW (290 tables). Column lists came
// from sys.columns, not from documentation.
//
//   SaleHeader   one row per bill. SerialNumber (decimal) is the bill id and the
//                join key. VoucherDate (smalldatetime). BillAmount = final,
//                tax-inclusive bill value. SubTotal / TaxTotal / QtyTotal.
//                Status = 2 for live sales. LocationID.
//   SaleDetail   bill lines, SaleDetail.SerialNumber = SaleHeader.SerialNumber.
//                FinalSaleAmount = line value. **WarehouseID lives on the LINE,
//                not the header** — a warehouse split must group off SaleDetail.
//                ProductID, Quantity, SaleRate, MRP.
//   WarehouseMaster  12 rows, WarehouseID -> WarehouseName.
//   ProductMaster    21,466 rows. ProductID, ProductName, BrandID.
//   BrandMaster      1,195 rows. BrandID, PrincipalCompanyID.
//   PrincipalCompanyMaster  5 rows: [None], J.L Enterprises, Vanesa Care
//                (Denver & Envy), Honasa Consumer, Unicorn Infosolutions.
//
// ------------------------------------------------------------------- the trap
// **Sales-by-principal reaches the principal through BrandMaster, not
// ProductMaster.** ProductMaster has no PrincipalCompanyID column at all; the
// path is SaleDetail.ProductID -> ProductMaster.BrandID -> BrandMaster
// .PrincipalCompanyID -> PrincipalCompanyMaster. And that mapping is almost
// entirely unpopulated: 1,183 of 1,195 brands carry PrincipalCompanyID <= 1
// (i.e. none), so on the last seven days of data ~99.8% of value lands in the
// `[None]` bucket:
//
//     [None]                                 5833 bills   983,340.27
//     Vanesa Care Pvt. Ltd. - Denver & Envy     6 bills         650.00
//     Unicorn Infosolutions Pvt. Ltd.           8 bills         580.00
//     J.L Enterprises                           2 bills         249.00
//
// `dms sales-by-principal` therefore prints an explicit unmapped share instead
// of quietly reporting a principal split that represents 0.2% of the business.
// Treating that output as a principal breakdown is the wrong-by-default reading
// this command exists to prevent.
//
// ---------------------------------------------------------------- date window
// Every command takes --from/--to (inclusive/exclusive). With neither, the
// window is the latest DAY THAT HAS DATA, not today: the feed lags, and a
// "today" default silently returns zero rows and reads as "no sales".

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/spf13/cobra"
)

func init() { register(newDMSCmd) }

const dmsDB = "FR8HODBNEW"

func newDMSCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "dms",
		Short: "ARY Distributor-Management System (FR8HODBNEW) — sales, warehouses, principals, product movement",
		Long: "ARY DMS reads against database " + dmsDB + " on the ARY SQL Server.\n\n" +
			"Read-only: every command builds one SELECT and runs it through dsr's\n" +
			"SELECT-only guard inside an always-rolled-back transaction.\n\n" +
			"With no --from/--to the window is the latest day that HAS data, not\n" +
			"today — the feed lags and a today-default returns zero rows.",
		Aliases: []string{"ary"},
	}
	c.AddCommand(
		dmsSalesCmd(app),
		dmsByWarehouseCmd(app),
		dmsByPrincipalCmd(app),
		dmsBillsCmd(app),
		dmsProductMovementCmd(app),
		dmsWarehousesCmd(app),
		dmsPrincipalsCmd(app),
		dmsFreshnessCmd(app),
	)
	return c
}

// dmsDBName forces FR8HODBNEW unless the operator overrode --db explicitly.
func dmsDBName(app *App) string {
	if app.Flags.Database != "" {
		return app.Flags.Database
	}
	return dmsDB
}

func dmsRun(app *App, query string) error {
	ctx, cancel := app.Ctx()
	defer cancel()
	res, err := app.DB.Query(ctx, dmsDBName(app), query)
	if err != nil {
		return err
	}
	return app.Render(res)
}

// dmsDate validates a YYYY-MM-DD literal before it reaches the SQL text.
// Values are interpolated, so anything not matching this shape is rejected
// rather than escaped — a narrow allowlist is the only safe interpolation.
func dmsDate(flag, v string) (string, error) {
	if v == "" {
		return "", nil
	}
	if len(v) != 10 || v[4] != '-' || v[7] != '-' {
		return "", Usagef("--%s must be YYYY-MM-DD, got %q", flag, v)
	}
	for i, ch := range v {
		if i == 4 || i == 7 {
			continue
		}
		if ch < '0' || ch > '9' {
			return "", Usagef("--%s must be YYYY-MM-DD, got %q", flag, v)
		}
	}
	return v, nil
}

// dmsWindow returns the CTE that defines the date window plus the WHERE clause
// that uses it. With no bounds the window is the latest day that has data.
func dmsWindow(from, to string) (cte string, where string) {
	switch {
	case from != "" && to != "":
		cte = fmt.Sprintf("w AS (SELECT CONVERT(date,'%s') lo, CONVERT(date,'%s') hi)", from, to)
	case from != "":
		cte = fmt.Sprintf("w AS (SELECT CONVERT(date,'%s') lo, DATEADD(day,1,(SELECT MAX(CONVERT(date,VoucherDate)) FROM SaleHeader WHERE Status=2)) hi)", from)
	case to != "":
		cte = fmt.Sprintf("w AS (SELECT CONVERT(date,'%s') lo, CONVERT(date,'%s') hi)", to, to)
	default:
		cte = "w AS (SELECT (SELECT MAX(CONVERT(date,VoucherDate)) FROM SaleHeader WHERE Status=2) lo, " +
			"DATEADD(day,1,(SELECT MAX(CONVERT(date,VoucherDate)) FROM SaleHeader WHERE Status=2)) hi)"
	}
	where = "h.Status = 2 AND h.VoucherDate >= w.lo AND h.VoucherDate < w.hi"
	return
}

type dmsFlags struct {
	From, To  string
	Warehouse int
	Principal string
	Product   string
	Top       int
}

func addDMSDates(c *cobra.Command, f *dmsFlags) {
	fl := c.Flags()
	fl.StringVar(&f.From, "from", "", "window start, inclusive, YYYY-MM-DD (default: latest day with data)")
	fl.StringVar(&f.To, "to", "", "window end, EXCLUSIVE, YYYY-MM-DD")
}

func (f *dmsFlags) window() (string, string, error) {
	from, err := dmsDate("from", f.From)
	if err != nil {
		return "", "", err
	}
	to, err := dmsDate("to", f.To)
	if err != nil {
		return "", "", err
	}
	cte, where := dmsWindow(from, to)
	return cte, where, nil
}

// ---------------------------------------------------------------- dms sales

func dmsSalesCmd(app *App) *cobra.Command {
	var f dmsFlags
	c := &cobra.Command{
		Use:   "sales",
		Short: "Bill count and value for the window (SaleHeader)",
		Long: "Totals straight off SaleHeader: bills, tax-inclusive value (BillAmount),\n" +
			"sub-total, tax and unit quantity. This is the header-level truth; the\n" +
			"line-level sum in `by-warehouse` reconciles to it within rounding.",
		Example: "  dsr dms sales\n  dsr dms sales --from 2026-08-01 --to 2026-08-22 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cte, where, err := f.window()
			if err != nil {
				return err
			}
			q := "WITH " + cte + `
SELECT MIN(CONVERT(date,h.VoucherDate)) AS from_date,
       MAX(CONVERT(date,h.VoucherDate)) AS to_date,
       COUNT(*)                          AS bills,
       CAST(SUM(h.BillAmount) AS DECIMAL(18,2)) AS bill_amount,
       CAST(SUM(h.SubTotal)   AS DECIMAL(18,2)) AS sub_total,
       CAST(SUM(h.TaxTotal)   AS DECIMAL(18,2)) AS tax_total,
       CAST(SUM(h.QtyTotal)   AS DECIMAL(18,2)) AS qty_total
FROM SaleHeader h CROSS JOIN w
WHERE ` + where
			return dmsRun(app, q)
		},
	}
	addDMSDates(c, &f)
	return c
}

// ------------------------------------------------------- dms by-warehouse

func dmsByWarehouseCmd(app *App) *cobra.Command {
	var f dmsFlags
	c := &cobra.Command{
		Use:     "by-warehouse",
		Short:   "Sale split by warehouse (warehouse is on the LINE, not the bill)",
		Aliases: []string{"warehouse-sales"},
		Long: "Groups SaleDetail.FinalSaleAmount by WarehouseMaster.\n\n" +
			"WarehouseID lives on SaleDetail, so one bill can span warehouses; the\n" +
			"bill count here is COUNT(DISTINCT SerialNumber) per warehouse and the\n" +
			"column total can therefore exceed `dms sales` bills.",
		Example: "  dsr dms by-warehouse\n  dsr dms by-warehouse --from 2026-08-01 --to 2026-08-22 --csv",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cte, where, err := f.window()
			if err != nil {
				return err
			}
			extra := ""
			if f.Warehouse > 0 {
				extra = " AND sd.WarehouseID = " + strconv.Itoa(f.Warehouse)
			}
			q := "WITH " + cte + `
SELECT COALESCE(wm.WarehouseName, CONCAT('WarehouseID ', sd.WarehouseID)) AS warehouse,
       sd.WarehouseID                                   AS warehouse_id,
       COUNT(DISTINCT h.SerialNumber)                    AS bills,
       CAST(SUM(sd.FinalSaleAmount) AS DECIMAL(18,2))     AS sale,
       CAST(SUM(sd.Quantity)        AS DECIMAL(18,2))     AS qty
FROM SaleHeader h
JOIN SaleDetail sd        ON sd.SerialNumber = h.SerialNumber
LEFT JOIN WarehouseMaster wm ON wm.WarehouseID = sd.WarehouseID
CROSS JOIN w
WHERE ` + where + extra + `
GROUP BY sd.WarehouseID, wm.WarehouseName
ORDER BY sale DESC`
			return dmsRun(app, q)
		},
	}
	addDMSDates(c, &f)
	c.Flags().IntVar(&f.Warehouse, "warehouse", 0, "restrict to one WarehouseID (see `dsr dms warehouses`)")
	return c
}

// ------------------------------------------------------- dms sales-by-principal

func dmsByPrincipalCmd(app *App) *cobra.Command {
	var f dmsFlags
	c := &cobra.Command{
		Use:     "sales-by-principal",
		Short:   "Sale split by principal company — READ THE UNMAPPED SHARE FIRST",
		Aliases: []string{"by-principal"},
		Long: "Joins SaleDetail -> ProductMaster -> BrandMaster -> PrincipalCompanyMaster.\n\n" +
			"ProductMaster has NO principal column; the only path to a principal is\n" +
			"through BrandMaster.PrincipalCompanyID, and that mapping is almost\n" +
			"entirely unpopulated — 1,183 of 1,195 brands have no principal. On a\n" +
			"recent week ~99.8% of value fell in the [None] bucket.\n\n" +
			"So the output leads with unmapped_pct. If that is ~100, this is not a\n" +
			"principal breakdown and must not be reported as one; the fix is master\n" +
			"data in BrandMaster, not a different query.",
		Example: "  dsr dms sales-by-principal\n  dsr dms sales-by-principal --from 2026-07-01 --to 2026-08-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cte, where, err := f.window()
			if err != nil {
				return err
			}
			q := "WITH " + cte + `,
lines AS (
  SELECT p.PrincipalCompanyName AS principal,
         CASE WHEN b.PrincipalCompanyID IS NULL OR b.PrincipalCompanyID <= 1
              THEN 1 ELSE 0 END AS unmapped,
         h.SerialNumber, sd.FinalSaleAmount
  FROM SaleHeader h
  JOIN SaleDetail sd            ON sd.SerialNumber = h.SerialNumber
  LEFT JOIN ProductMaster pm    ON pm.ProductID = sd.ProductID
  LEFT JOIN BrandMaster b       ON b.BrandID = pm.BrandID
  LEFT JOIN PrincipalCompanyMaster p ON p.PrincipalCompanyID = b.PrincipalCompanyID
  CROSS JOIN w
  WHERE ` + where + `
)
SELECT COALESCE(principal,'(no brand->principal mapping)') AS principal,
       CASE WHEN unmapped = 1 THEN 'UNMAPPED' ELSE 'mapped' END AS mapping,
       COUNT(DISTINCT SerialNumber)                       AS bills,
       CAST(SUM(FinalSaleAmount) AS DECIMAL(18,2))         AS sale,
       CAST(100.0 * SUM(FinalSaleAmount)
            / NULLIF((SELECT SUM(FinalSaleAmount) FROM lines),0) AS DECIMAL(6,2)) AS pct_of_total
FROM lines
GROUP BY principal, unmapped
ORDER BY sale DESC`
			return dmsRun(app, q)
		},
	}
	addDMSDates(c, &f)
	return c
}

// ---------------------------------------------------------------- dms bills

func dmsBillsCmd(app *App) *cobra.Command {
	var f dmsFlags
	c := &cobra.Command{
		Use:     "bills",
		Short:   "Individual bills in the window (SaleHeader rows)",
		Aliases: []string{"daily-bills"},
		Example: "  dsr dms bills\n  dsr dms bills --from 2026-08-20 --to 2026-08-22 -n 50",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cte, where, err := f.window()
			if err != nil {
				return err
			}
			q := fmt.Sprintf("WITH %s\nSELECT TOP %d\n", cte, topN(app, 100)) + `       h.SerialNumber                        AS bill_id,
       CONVERT(date,h.VoucherDate)           AS bill_date,
       h.VchIDPrefix + h.VchIDYMD            AS voucher_ref,
       h.CustomerID                          AS customer_id,
       h.CompanyName                         AS customer,
       CAST(h.QtyTotal   AS DECIMAL(18,2))   AS qty,
       CAST(h.SubTotal   AS DECIMAL(18,2))   AS sub_total,
       CAST(h.TaxTotal   AS DECIMAL(18,2))   AS tax,
       CAST(h.BillAmount AS DECIMAL(18,2))   AS bill_amount,
       h.LocationID                          AS location_id
FROM SaleHeader h CROSS JOIN w
WHERE ` + where + `
ORDER BY h.VoucherDate DESC, h.SerialNumber DESC`
			return dmsRun(app, q)
		},
	}
	addDMSDates(c, &f)
	return c
}

// ------------------------------------------------------ dms product-movement

func dmsProductMovementCmd(app *App) *cobra.Command {
	var f dmsFlags
	c := &cobra.Command{
		Use:     "product-movement",
		Short:   "Quantity and value moved per product in the window",
		Aliases: []string{"movement", "products"},
		Long: "Groups SaleDetail by product. --product filters on ProductName with a\n" +
			"LIKE; the pattern is validated to letters, digits, space, . - _ & / ( )\n" +
			"and % so it can be interpolated without opening an injection path.",
		Example: "  dsr dms product-movement -n 25\n  dsr dms product-movement --product 'MAMAEARTH%' --from 2026-08-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cte, where, err := f.window()
			if err != nil {
				return err
			}
			extra := ""
			if f.Product != "" {
				if !dmsSafeLike(f.Product) {
					return Usagef("--product may contain only letters, digits, space and . - _ & / ( ) %%, got %q", f.Product)
				}
				extra = " AND pm.ProductName LIKE '" + f.Product + "'"
			}
			if f.Warehouse > 0 {
				extra += " AND sd.WarehouseID = " + strconv.Itoa(f.Warehouse)
			}
			q := fmt.Sprintf("WITH %s\nSELECT TOP %d\n", cte, topN(app, 50)) + `       sd.ProductID                                  AS product_id,
       COALESCE(pm.ProductName,'(unknown product)')  AS product,
       COUNT(DISTINCT h.SerialNumber)                AS bills,
       CAST(SUM(sd.Quantity)        AS DECIMAL(18,3)) AS qty,
       CAST(SUM(sd.FinalSaleAmount) AS DECIMAL(18,2)) AS sale,
       CAST(AVG(sd.SaleRate)        AS DECIMAL(18,2)) AS avg_rate
FROM SaleHeader h
JOIN SaleDetail sd         ON sd.SerialNumber = h.SerialNumber
LEFT JOIN ProductMaster pm ON pm.ProductID = sd.ProductID
CROSS JOIN w
WHERE ` + where + extra + `
GROUP BY sd.ProductID, pm.ProductName
ORDER BY sale DESC`
			return dmsRun(app, q)
		},
	}
	addDMSDates(c, &f)
	c.Flags().StringVar(&f.Product, "product", "", "filter on ProductName (SQL LIKE pattern, e.g. 'MAMAEARTH%')")
	c.Flags().IntVar(&f.Warehouse, "warehouse", 0, "restrict to one WarehouseID")
	return c
}

// dmsSafeLike allows only characters that cannot terminate a SQL string literal
// or start a comment or a second statement.
func dmsSafeLike(s string) bool {
	if s == "" || len(s) > 120 {
		return false
	}
	const ok = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .-_&/()%"
	for _, ch := range s {
		if !strings.ContainsRune(ok, ch) {
			return false
		}
	}
	return true
}

// ------------------------------------------------- masters and freshness

func dmsWarehousesCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "warehouses",
		Short:   "WarehouseMaster — the WarehouseID values --warehouse accepts",
		Args:    cobra.NoArgs,
		Example: "  dsr dms warehouses",
		RunE: func(cmd *cobra.Command, args []string) error {
			return dmsRun(app, "SELECT WarehouseID AS warehouse_id, WarehouseName AS warehouse "+
				"FROM WarehouseMaster ORDER BY WarehouseID")
		},
	}
}

func dmsPrincipalsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "principals",
		Short: "PrincipalCompanyMaster, with how many brands actually map to each",
		Args:  cobra.NoArgs,
		Long: "brands_mapped is the number of BrandMaster rows pointing at the\n" +
			"principal. It is the ceiling on what `sales-by-principal` can attribute:\n" +
			"1,183 of 1,195 brands point at nothing, which is why that command leads\n" +
			"with its unmapped share.",
		Example: "  dsr dms principals",
		RunE: func(cmd *cobra.Command, args []string) error {
			return dmsRun(app, `SELECT p.PrincipalCompanyID AS principal_id,
       p.PrincipalCompanyName AS principal,
       p.IsActive             AS is_active,
       p.MLNumber             AS ml_number,
       COUNT(b.BrandID)       AS brands_mapped
FROM PrincipalCompanyMaster p
LEFT JOIN BrandMaster b ON b.PrincipalCompanyID = p.PrincipalCompanyID
GROUP BY p.PrincipalCompanyID, p.PrincipalCompanyName, p.IsActive, p.MLNumber
ORDER BY p.PrincipalCompanyID`)
		},
	}
}

func dmsFreshnessCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "freshness",
		Short:   "How current the DMS sales feed is — check this before quoting a number",
		Aliases: []string{"asof"},
		Args:    cobra.NoArgs,
		Example: "  dsr dms freshness",
		RunE: func(cmd *cobra.Command, args []string) error {
			return dmsRun(app, `SELECT MAX(CONVERT(date,VoucherDate))                        AS latest_bill_date,
       DATEDIFF(day, MAX(CONVERT(date,VoucherDate)), CONVERT(date,GETDATE())) AS days_behind_today,
       MIN(CONVERT(date,VoucherDate))                        AS earliest_bill_date,
       COUNT(*)                                              AS live_bills
FROM SaleHeader WHERE Status = 2`)
		},
	}
}
