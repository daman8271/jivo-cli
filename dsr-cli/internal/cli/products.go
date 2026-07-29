package cli

// Domain commands for the product master / SKU catalogue (tbl_item). See
// domain.go for the shared helpers and conventions all domain files follow.
//
// Notes (from study/vault/product-master.md, verified live 2026-07-29):
//   - tbl_item.Id is the PK and the productId/itemId used everywhere downstream.
//   - itemType -> tbl_itemType.Id (oil/beverage variant).
//   - UOM -> tbl_UOMMaster.ID (capital D — every live row = 1 = PCS).
//   - itemGroup stores the group NAME as text; it joins tbl_ItemGroupName by
//     .ItemGroupName, NOT by .Id.
//   - SAPID is 100% NULL — there is no SAP item bridge in DSR.
//   - itemName has trailing/double spaces; LTRIM(RTRIM()) it for display.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newProductsCmd) }

func newProductsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "products",
		Short:   "Product master / SKU catalogue — list, get, count (tbl_item)",
		Aliases: []string{"product", "items", "skus", "sku"},
	}
	c.AddCommand(productsListCmd(app), productsGetCmd(app), productsCountCmd(app))
	return c
}

// productsWhere builds the WHERE clause for the SKU list/count, applied to the
// tbl_item alias "i". --type filters by itemType (tbl_itemType.Id).
func productsWhere(f *domFilters, typ int) string {
	return fWhere(
		fEqInt("i.itemType", typ),
		fLive("i.", f.IncludeDeleted),
	)
}

func productsListCmd(app *App) *cobra.Command {
	var f domFilters
	var typ int
	c := &cobra.Command{
		Use:     "list",
		Short:   "List SKUs (decoded variant/pack/uom); filter by --type/--include-deleted",
		Example: "  dsr products list --type 4\n  dsr products list -n 200 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d i.Id, LTRIM(RTRIM(i.itemName)) AS itemName, "+
				"t.typeName AS variant, COALESCE(g.ItemGroupName, i.itemGroup) AS packGroup, "+
				"u.UOMName AS uom, i.piecesPerCase, i.quantity, i.gst, i.MRP, "+
				"i.visibleToSo, i.visibleToPromoter, i.isVisibleToRetailer, i.isScheme, "+
				"i.CreatedBy, i.CreatedOn "+
				"FROM tbl_item i "+
				"LEFT JOIN tbl_itemType t ON t.Id = i.itemType "+
				"LEFT JOIN tbl_UOMMaster u ON u.ID = i.UOM "+
				"LEFT JOIN tbl_ItemGroupName g ON g.ItemGroupName = i.itemGroup%s "+
				"ORDER BY i.Id DESC",
				topN(app, 200), productsWhere(&f, typ))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "deleted")
	c.Flags().IntVar(&typ, "type", 0, "filter by itemType id (tbl_itemType.Id, e.g. 4=MUSTARD)")
	return c
}

func productsCountCmd(app *App) *cobra.Command {
	var f domFilters
	var typ int
	c := &cobra.Command{
		Use:   "count",
		Short: "Count SKUs matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS skus FROM tbl_item i" + productsWhere(&f, typ)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "deleted")
	c.Flags().IntVar(&typ, "type", 0, "filter by itemType id (tbl_itemType.Id, e.g. 4=MUSTARD)")
	return c
}

func productsGetCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "get <id>",
		Short:   "Show a single SKU by Id, fully decoded (variant/pack/uom)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr products get 42 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("item id must be an integer, got %q", args[0])
			}
			q := fmt.Sprintf("SELECT i.Id, LTRIM(RTRIM(i.itemName)) AS itemName, "+
				"t.typeName AS variant, i.itemType, COALESCE(g.ItemGroupName, i.itemGroup) AS packGroup, "+
				"u.UOMName AS uom, i.UOM, i.piecesPerCase, i.quantity, i.itemCode, i.SAPID, "+
				"i.gst, i.HSNCode, i.MRP, i.price, "+
				"i.visibleToSo, i.visibleToPromoter, i.isVisibleToRetailer, "+
				"i.isScheme, i.isRedeemable, i.isCashback, i.cashRate, i.status, "+
				"i.shortDescription, i.CreatedBy, i.CreatedOn, i.deleted "+
				"FROM tbl_item i "+
				"LEFT JOIN tbl_itemType t ON t.Id = i.itemType "+
				"LEFT JOIN tbl_UOMMaster u ON u.ID = i.UOM "+
				"LEFT JOIN tbl_ItemGroupName g ON g.ItemGroupName = i.itemGroup "+
				"WHERE i.Id = %d", id)
			return runSelect(app, q)
		},
	}
}
