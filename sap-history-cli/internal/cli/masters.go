package cli

// Master data an operator needs to make sense of the numbers: branches,
// warehouses, salespeople and item groups.

import (
	"fmt"

	"github.com/spf13/cobra"
)

func init() {
	register(newBranchesCmd)
	register(newWarehousesCmd)
	register(newSalespeopleCmd)
	register(newGroupsCmd)
}

func newBranchesCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "branches",
		Short:   "Branches / business places (OBPL) — the 'new' book has 6, the 'old' book has none",
		Aliases: []string{"branch", "bpl"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runBooks(app, "", "", func(b Book) string {
				return `SELECT BPLId, BPLName, State, Street, City, ZipCode, TaxIdNum AS gstin,
  VATRegNum AS vat_reg, MainBPL AS is_main, Disabled AS disabled, DflWhs AS default_warehouse
FROM OBPL ORDER BY BPLId`
			})
		},
	}
}

func newWarehousesCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "warehouses",
		Short:   "Warehouses (OWHS), with the branch each belongs to",
		Aliases: []string{"warehouse", "whs"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runBooks(app, "", "", func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d w.WhsCode, w.WhsName, w.BPLid AS branch_id, w.City, w.State,
  w.Locked, CAST((SELECT ISNULL(SUM(t.OnHand * t.AvgPrice),0) FROM OITW t WHERE t.WhsCode = w.WhsCode) AS decimal(19,2)) AS stock_value
FROM OWHS w%s ORDER BY w.WhsCode`, topN(app, 200), fWhere(fLike("w.WhsName", f.Search)))
			})
		},
	}
	addDomFilters(c, &f, "search")
	return c
}

func newSalespeopleCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "salespeople",
		Short:   "Sales employees (OSLP)",
		Aliases: []string{"slp", "sales-staff"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runBooks(app, "", "", func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d SlpCode, SlpName, Active, Telephone, Mobil AS mobile, Email, Memo
FROM OSLP%s ORDER BY SlpName`, topN(app, 200), fWhere(fLike("SlpName", f.Search)))
			})
		},
	}
	addDomFilters(c, &f, "search")
	return c
}

func newGroupsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "item-groups",
		Short:   "Item groups (OITB) with the number of items in each",
		Aliases: []string{"groups"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runBooks(app, "", "", func(b Book) string {
				return `SELECT g.ItmsGrpCod AS group_code, g.ItmsGrpNam AS group_name,
  (SELECT COUNT(*) FROM OITM i WHERE i.ItmsGrpCod = g.ItmsGrpCod) AS items
FROM OITB g ORDER BY items DESC`
			})
		},
	}
	return c
}
