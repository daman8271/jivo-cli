package cli

// Small, high-value master lists: locations, warehouses, staff, payment modes,
// units, taxes, brands/groups, principals. These are the decode tables every
// other command's IDs point at, so they are worth one command each.

import (
	"fmt"

	"github.com/spf13/cobra"
)

func init() {
	register(newLocationsCmd)
	register(newWarehousesCmd)
	register(newMastersCmd)
}

func newLocationsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "locations",
		Short: "The three ARY locations — name, GSTIN, state, financial year",
		Long: "ARY bills from three registrations under one PAN (AACCJ4223F), all in the name\n" +
			"'Akal Rozgar Yojana A U/O Jivo Wellness Pvt Ltd': Ary HO (Delhi), Ary Baru Sahib\n" +
			"(Himachal) and Ary Bathinda (Punjab). LocationID appears on every voucher.",
		Aliases: []string{"location", "branches"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT l.LocationID AS id, l.LocationName AS location, l.LocationCode AS code, " +
				"l.GSTINNo AS gstin, l.PanNo AS pan, s.StateName AS state, c.CityName AS city, l.Pincode AS pincode, " +
				"CONVERT(varchar(10), l.BookBegin, 120) AS books_from, l.IsActive AS active " +
				"FROM LocationMaster l " +
				"LEFT JOIN StateMaster s ON s.StateID = l.StateID " +
				"LEFT JOIN CityMaster c ON c.CityID = l.CityID " +
				"ORDER BY l.LocationID"
			return runSelect(app, q)
		},
	}
}

func newWarehousesCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "warehouses",
		Short: "Warehouses / counters, with their SKU count and current book stock",
		Long: "Warehouses are ARY's selling counters and stores (Ary Pos, Ary Clothing, the canteens,\n" +
			"Ary Warehouse, Talwandi Sabo, …). book_qty is Stock.Quantity — the system's own on-hand.\n" +
			"A NEGATIVE book_qty is real data, not a query artefact: it means the counter billed stock\n" +
			"it was never shown as receiving. See `ary stock negative`.",
		Aliases: []string{"warehouse", "counters"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT w.WarehouseID AS id, w.WarehouseName AS warehouse, w.IsActive AS active, " +
				"COUNT(DISTINCT s.ProductID) AS skus, CAST(SUM(s.Quantity) AS decimal(18,2)) AS book_qty, " +
				"CAST(SUM(s.Sho) AS decimal(18,2)) AS shortage, CAST(SUM(s.Exc) AS decimal(18,2)) AS excess, " +
				"CAST(SUM(s.Was) AS decimal(18,2)) AS wastage " +
				"FROM WarehouseMaster w LEFT JOIN Stock s ON s.WarehouseID = w.WarehouseID " +
				"GROUP BY w.WarehouseID, w.WarehouseName, w.IsActive ORDER BY w.WarehouseID"
			return runSelect(app, q)
		},
	}
}

func newMastersCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "masters",
		Short:   "Decode tables: staff, payment modes, units, taxes, brands, groups, principals, states",
		Aliases: []string{"master", "codes"},
	}
	c.AddCommand(
		mastersSimpleCmd(app, "staff", "Salespersons and their targets", []string{"salespersons", "people"},
			"SELECT SalesPersonID AS id, SalesPersonName AS name, SalesPersonInitial AS initials, "+
				"CAST(Target AS decimal(18,2)) AS target, CAST(SPCommPercent AS decimal(9,3)) AS comm_pct, IsActive AS active "+
				"FROM SalesPersonMaster ORDER BY SalesPersonID"),
		mastersSimpleCmd(app, "payment-modes", "Modes of payment (cash / card / UPI / credit …)", []string{"mop"},
			"SELECT m.MOPID AS id, m.MOPName AS mode, m.MOPTypeID AS type_id, a.AccountName AS posts_to_account, "+
				"CAST(m.CommissionPercent AS decimal(9,3)) AS commission_pct, m.IsActive AS active "+
				"FROM ModeOfPayment m LEFT JOIN AccountMaster a ON a.AccountID = m.AccountID ORDER BY m.MOPID"),
		mastersSimpleCmd(app, "units", "Units of measure", []string{"uom"},
			"SELECT UnitID AS id, UnitName AS unit, FormalName AS formal, DigitAfterDecimal AS decimals, "+
				"ConversionUnit AS conv_unit, CAST(ConversionQty AS decimal(18,4)) AS conv_qty, IsActive AS active "+
				"FROM UnitMaster ORDER BY UnitID"),
		mastersSimpleCmd(app, "taxes", "Tax codes and rates", []string{"tax"},
			"SELECT TaxID AS id, TaxName AS tax, CAST(TaxValue AS decimal(9,3)) AS rate_pct, IncludeInRate AS inclusive, "+
				"InterStateTaxID AS interstate_id, IsActive AS active FROM TaxMaster ORDER BY TaxID"),
		mastersSimpleCmd(app, "principals", "Principal companies whose brands ARY distributes", []string{"principal"},
			"SELECT p.PrincipalCompanyID AS id, p.PrincipalCompanyName AS principal, p.IsActive AS active, "+
				"(SELECT COUNT(*) FROM BrandMaster b WHERE b.PrincipalCompanyID = p.PrincipalCompanyID) AS brands "+
				"FROM PrincipalCompanyMaster p ORDER BY p.PrincipalCompanyID"),
		mastersSimpleCmd(app, "states", "State codes (GST state code)", nil,
			"SELECT StateID AS id, StateName AS state, StateCode AS gst_code, IsActive AS active FROM StateMaster ORDER BY StateID"),
		mastersSimpleCmd(app, "customer-types", "Customer categories", nil,
			"SELECT CustomerTypeID AS id, CustomerTypeName AS customer_type, IsActive AS active FROM CustomerTypeMaster ORDER BY CustomerTypeID"),
		mastersSimpleCmd(app, "voucher-types", "Voucher series (what each document type is called)", []string{"vouchers-master"},
			"SELECT v.VoucherID AS id, v.VoucherName AS voucher, t.VoucherTypeName AS type, v.Prefix AS prefix, v.IsActive AS active "+
				"FROM VoucherMaster v LEFT JOIN VoucherTypeMaster t ON t.VoucherTypeID = v.VoucherTypeID ORDER BY v.VoucherID"),
		mastersBrandsCmd(app),
		mastersGroupsCmd(app),
	)
	return c
}

// mastersSimpleCmd builds a no-flag listing sub-command from one fixed query.
func mastersSimpleCmd(app *App, use, short string, aliases []string, query string) *cobra.Command {
	return &cobra.Command{
		Use:     use,
		Short:   short,
		Aliases: aliases,
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runSelect(app, query)
		},
	}
}

func mastersBrandsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "brands",
		Short:   "Brands, with their principal and SKU count",
		Aliases: []string{"brand"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d b.BrandID AS id, b.BrandName AS brand, p.PrincipalCompanyName AS principal, "+
				"(SELECT COUNT(*) FROM ProductMaster pm WHERE pm.BrandID = b.BrandID) AS skus, b.IsActive AS active "+
				"FROM BrandMaster b LEFT JOIN PrincipalCompanyMaster p ON p.PrincipalCompanyID = b.PrincipalCompanyID%s "+
				"ORDER BY skus DESC, b.BrandName", topN(app, 100),
				fWhere(fLike("b.BrandName", f.Search), fActive("b.", f.ActiveOnly)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "search", "active")
	return c
}

func mastersGroupsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "product-groups",
		Short:   "Product groups and sub-groups, with SKU counts",
		Aliases: []string{"groups"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d g.ProductGroupID AS group_id, g.ProductGroupName AS product_group, "+
				"sg.SubGroupID AS subgroup_id, sg.SubGroupName AS sub_group, "+
				"(SELECT COUNT(*) FROM ProductMaster pm WHERE pm.SubGroupID = sg.SubGroupID) AS skus "+
				"FROM SubGroupMaster sg LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = sg.ProductGroupID%s "+
				"ORDER BY g.ProductGroupName, sg.SubGroupName", topN(app, 200),
				fWhere(fLike("sg.SubGroupName", f.Search), fActive("sg.", f.ActiveOnly)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "search", "active")
	return c
}
