package cli

// Product master / SKU catalogue (ProductMaster + ProductChildMaster).
//
// Notes (verified live 2026-08-27):
//   - ProductMaster.ProductID is an nvarchar code (e.g. "0CU7"), not an int.
//   - ProductChildMaster is the per-location price/batch child: the real key is
//     ProductID + ChildID + LocationCode, concatenated into ProductChildID.
//   - ProductCodeSAP exists on all 21,466 rows and is EMPTY in every one —
//     there is no ARY<->SAP item bridge yet. `ary products sap-gap` proves it.
//   - QuantityOnHand is dead: non-zero on exactly ONE SKU. Never use it for
//     stock; use `ary stock` (Stock.Quantity).
//   - BrandID -> BrandMaster -> PrincipalCompanyID is the distribution lineage.

import (
	"fmt"

	"github.com/spf13/cobra"

	"ary/internal/db"
)

func init() { register(newProductsCmd) }

func newProductsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "products",
		Short:   "SKU catalogue — list, get, count, price children, SAP-mapping gap",
		Aliases: []string{"product", "items", "skus", "sku"},
	}
	c.AddCommand(productsListCmd(app), productsGetCmd(app), productsCountCmd(app),
		productsChildrenCmd(app), productsSAPGapCmd(app), productsExpiringCmd(app))
	return c
}

// productsJoins is the shared decode join set for the SKU master.
const productsJoins = " FROM ProductMaster p " +
	"LEFT JOIN BrandMaster b ON b.BrandID = p.BrandID " +
	"LEFT JOIN PrincipalCompanyMaster pc ON pc.PrincipalCompanyID = b.PrincipalCompanyID " +
	"LEFT JOIN SubGroupMaster sg ON sg.SubGroupID = p.SubGroupID " +
	"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID " +
	"LEFT JOIN UnitMaster u ON u.UnitID = p.UnitID " +
	"LEFT JOIN HSNSACMaster h ON h.HSNSACID = p.HSNSACID " +
	"LEFT JOIN TaxMaster t ON t.TaxID = p.TaxIDSale"

func productsWhere(f *domFilters, group, brand int, barcode string) string {
	return fWhere(
		fLike("p.ProductName", f.Search),
		fEqInt("p.ProductGroupID", group),
		fEqInt("p.BrandID", brand),
		productsBarcodeMatch(barcode),
		fActive("p.", f.ActiveOnly),
	)
}

// productsBarcodeMatch matches any of the five barcode columns FusionERP8 keeps.
func productsBarcodeMatch(bc string) string {
	if bc == "" {
		return ""
	}
	l := db.Lit(bc)
	return "(p.UPCEAN = " + l + " OR p.UPCEAN1 = " + l + " OR p.UPCEAN2 = " + l +
		" OR p.UPCEAN3 = " + l + " OR p.UPCEAN4 = " + l + " OR p.UserDefinedCode = " + l + ")"
}

func productsListCmd(app *App) *cobra.Command {
	var f domFilters
	var group, brand int
	var barcode string
	c := &cobra.Command{
		Use:   "list",
		Short: "List SKUs with brand, principal, group, HSN, MRP and tax",
		Example: "  ary products list --search \"maggi\"\n" +
			"  ary products list --brand 12 -n 50\n" +
			"  ary products list --barcode 8901058851298",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d p.ProductID AS id, p.ProductName AS product, b.BrandName AS brand, "+
				"pc.PrincipalCompanyName AS principal, g.ProductGroupName AS product_group, sg.SubGroupName AS sub_group, "+
				"u.UnitName AS unit, h.HSNSACCode AS hsn, CAST(t.TaxValue AS decimal(9,2)) AS tax_pct, "+
				"CAST(p.MaxRetailPrice AS decimal(18,2)) AS mrp, CAST(p.StandardSalePrice AS decimal(18,2)) AS sale_price, "+
				"CAST(p.StandardCostPrice AS decimal(18,2)) AS cost_price, p.UPCEAN AS barcode, p.IsActive AS active%s%s "+
				"ORDER BY p.ProductName", topN(app, 100), productsJoins, productsWhere(&f, group, brand, barcode))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "search", "active")
	c.Flags().IntVar(&group, "group", 0, "filter by ProductGroupID (see `ary masters product-groups`)")
	c.Flags().IntVar(&brand, "brand", 0, "filter by BrandID (see `ary masters brands`)")
	c.Flags().StringVar(&barcode, "barcode", "", "exact match on any barcode / user code column")
	return c
}

func productsCountCmd(app *App) *cobra.Command {
	var f domFilters
	var group, brand int
	c := &cobra.Command{
		Use:   "count",
		Short: "Count SKUs matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS skus, SUM(CASE WHEN ISNULL(p.IsActive,0)=1 THEN 1 ELSE 0 END) AS active" +
				productsJoins + productsWhere(&f, group, brand, "")
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "search", "active")
	c.Flags().IntVar(&group, "group", 0, "filter by ProductGroupID")
	c.Flags().IntVar(&brand, "brand", 0, "filter by BrandID")
	return c
}

func productsGetCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "get <ProductID>",
		Short:   "One SKU in full: master row, price children, and stock by warehouse",
		Example: "  ary products get 0CU7",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := db.Lit(args[0])
			return runSections(app, []section{
				{"master", "SELECT p.ProductID AS id, p.ProductName AS product, p.PrintName AS print_name, " +
					"b.BrandName AS brand, pc.PrincipalCompanyName AS principal, g.ProductGroupName AS product_group, " +
					"sg.SubGroupName AS sub_group, u.UnitName AS unit, h.HSNSACCode AS hsn, " +
					"CAST(t.TaxValue AS decimal(9,2)) AS tax_pct, CAST(p.MaxRetailPrice AS decimal(18,2)) AS mrp, " +
					"CAST(p.StandardSalePrice AS decimal(18,2)) AS sale_price, CAST(p.StandardCostPrice AS decimal(18,2)) AS cost_price, " +
					"p.UPCEAN AS barcode, CAST(p.ReorderLevel AS decimal(18,2)) AS reorder_level, p.BinLocation AS bin, " +
					"p.IsActive AS active, CONVERT(varchar(16), p.RecordDateTime, 120) AS created" +
					productsJoins + " WHERE p.ProductID = " + id},
				{"price children", "SELECT c.ChildID AS child, c.LocationCode AS loc, CAST(c.PurchaseCost AS decimal(18,2)) AS purchase_cost, " +
					"CAST(c.MRP AS decimal(18,2)) AS mrp, CAST(c.SellingPrice AS decimal(18,2)) AS selling_price, " +
					"CAST(c.Margin AS decimal(9,2)) AS margin_pct, CONVERT(varchar(10), c.ExpDate, 120) AS expiry " +
					"FROM ProductChildMaster c WHERE c.ProductID = " + id + " ORDER BY c.LocationCode, c.ChildID"},
				{"stock by warehouse", "SELECT w.WarehouseName AS warehouse, CAST(SUM(s.Quantity) AS decimal(18,2)) AS book_qty, " +
					"CAST(SUM(s.OP) AS decimal(18,2)) AS opening, CAST(SUM(s.Pur) AS decimal(18,2)) AS purchased, " +
					"CAST(SUM(s.Sal) AS decimal(18,2)) AS sold, CAST(SUM(s.TrIn-s.TrOut) AS decimal(18,2)) AS net_transfer, " +
					"CAST(SUM(s.Sho) AS decimal(18,2)) AS shortage, CAST(SUM(s.Was) AS decimal(18,2)) AS wastage " +
					"FROM Stock s LEFT JOIN WarehouseMaster w ON w.WarehouseID = s.WarehouseID " +
					"WHERE s.ProductID = " + id + " GROUP BY w.WarehouseName ORDER BY book_qty DESC"},
			})
		},
	}
}

func productsChildrenCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "children",
		Short:   "Price/batch children (per-location cost, MRP, selling price, margin, expiry)",
		Aliases: []string{"prices"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d c.ProductID AS id, p.ProductName AS product, c.ChildID AS child, "+
				"c.LocationCode AS loc, CAST(c.PurchaseCost AS decimal(18,2)) AS purchase_cost, "+
				"CAST(c.MRP AS decimal(18,2)) AS mrp, CAST(c.SellingPrice AS decimal(18,2)) AS selling_price, "+
				"CAST(c.Margin AS decimal(9,2)) AS margin_pct, CONVERT(varchar(10), c.MfgDate, 120) AS mfg, "+
				"CONVERT(varchar(10), c.ExpDate, 120) AS expiry "+
				"FROM ProductChildMaster c LEFT JOIN ProductMaster p ON p.ProductID = c.ProductID%s "+
				"ORDER BY c.ProductID, c.LocationCode", topN(app, 100),
				fWhere(fEqStr("c.ProductID", f.Product), fLike("p.ProductName", f.Search)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "product", "search")
	return c
}

func productsSAPGapCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "sap-gap",
		Short: "How many SKUs carry a SAP item code (the ARY<->SAP bridge that does not exist yet)",
		Long: "ProductMaster has a ProductCodeSAP column. If it is empty, ARY stock and sales cannot be\n" +
			"tied to SAP items, and any cross-system reconciliation has to match on name — which is\n" +
			"exactly how wrong vendors get picked (see correction C-0044 territory). This command is\n" +
			"the one-line proof of where that stands today.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS skus, " +
				"SUM(CASE WHEN ProductCodeSAP IS NOT NULL AND LTRIM(RTRIM(ProductCodeSAP)) <> '' THEN 1 ELSE 0 END) AS with_sap_code, " +
				"SUM(CASE WHEN ProductCodeSAP IS NULL OR LTRIM(RTRIM(ProductCodeSAP)) = '' THEN 1 ELSE 0 END) AS without_sap_code, " +
				"SUM(CASE WHEN ISNULL(IsActive,0)=1 AND (ProductCodeSAP IS NULL OR LTRIM(RTRIM(ProductCodeSAP))='') THEN 1 ELSE 0 END) AS active_without_code " +
				"FROM ProductMaster"
			return runSelect(app, q)
		},
	}
}

func productsExpiringCmd(app *App) *cobra.Command {
	var days int
	c := &cobra.Command{
		Use:   "expiring",
		Short: "Price children with an expiry date inside the next N days that still show stock",
		Long: "Joins the batch child's ExpDate to live book stock, so it lists only what is both expiring\n" +
			"AND on the shelf. Sentinel dates (1900-01-01) are excluded.",
		Example: "  ary products expiring --days 60",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d c.ProductID AS id, p.ProductName AS product, c.ChildID AS child, "+
				"CONVERT(varchar(10), c.ExpDate, 120) AS expiry, DATEDIFF(day, GETDATE(), c.ExpDate) AS days_left, "+
				"CAST(SUM(s.Quantity) AS decimal(18,2)) AS book_qty, CAST(MAX(c.SellingPrice) AS decimal(18,2)) AS selling_price "+
				"FROM ProductChildMaster c "+
				"JOIN ProductMaster p ON p.ProductID = c.ProductID "+
				"JOIN Stock s ON s.ProductID = c.ProductID AND s.ChildID = c.ChildID "+
				"WHERE c.ExpDate > '1901-01-01' AND c.ExpDate <= DATEADD(day, %d, GETDATE()) "+
				"GROUP BY c.ProductID, p.ProductName, c.ChildID, c.ExpDate "+
				"HAVING SUM(s.Quantity) > 0 ORDER BY c.ExpDate", topN(app, 100), days)
			return runSelect(app, q)
		},
	}
	c.Flags().IntVar(&days, "days", 90, "look-ahead window in days")
	return c
}
