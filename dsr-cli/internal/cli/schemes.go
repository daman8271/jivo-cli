package cli

// Domain commands for trade schemes & gifts — see domain.go for conventions.
//
// Data model (from study/vault/field-sales-entry.md):
//   - tbl_SchemeProductsSold : scheme/offer line items of a visit (combo packs).
//     Fans off the visit header by salesId; soft-deleted via `deleted`.
//   - tbl_Gift               : gift/scheme catalog — gift tiers by sale range.
//     Active rows have giftAllow = 1 (no soft-delete column).
//   - tbl_saveGift           : gift actually issued at a visit. `active` (int,
//     1=live) doubles as the soft-delete flag; personId→SO, retailerId→shop,
//     giftId→tbl_Gift.
//   - tbl_GiftMapwithRetailer: which gift a retailer qualifies for (eligibility).

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newSchemesCmd) }

func newSchemesCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "schemes",
		Short:   "Trade schemes & gifts — scheme lines, gift catalog, gifts issued",
		Aliases: []string{"scheme", "gifts"},
	}
	c.AddCommand(
		schemesListSoldCmd(app),
		schemesGiftsCmd(app),
		schemesIssuedCmd(app),
		schemesGetCmd(app),
		schemesCountCmd(app),
	)
	return c
}

// schemesSoldCols is the friendly column set for scheme line-item output.
const schemesSoldCols = "Id, salesId, productId, productName, pieces, productQuantity, " +
	"totalQuantity, cost, totalCost, UOM, itemType, CreatedBy, CreatedOn"

func schemesSoldWhere(f *domFilters) string {
	return fWhere(
		fEqInt("productId", f.Item),
		fDateGE("CreatedOn", f.From),
		fDateLT("CreatedOn", f.To),
		fLive("", f.IncludeDeleted),
	)
}

func schemesListSoldCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "list-sold",
		Short:   "List scheme/offer products sold at visits (tbl_SchemeProductsSold)",
		Example: "  dsr schemes list-sold --from 2026-07-01 --to 2026-08-01\n  dsr schemes list-sold --item 4211 -n 50 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_SchemeProductsSold%s ORDER BY Id DESC",
				topN(app, 100), schemesSoldCols, schemesSoldWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "item", "deleted")
	return c
}

func schemesGiftsCmd(app *App) *cobra.Command {
	var includeInactive bool
	c := &cobra.Command{
		Use:     "gifts",
		Short:   "List the gift/scheme catalog (tbl_Gift), active tiers first",
		Example: "  dsr schemes gifts\n  dsr schemes gifts --include-inactive --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			where := ""
			if !includeInactive {
				where = " WHERE giftAllow = 1"
			}
			q := fmt.Sprintf("SELECT TOP %d giftId, giftName, giftRange, giftStartRange, "+
				"giftEndRange, giftShowRange, giftAllow, createdDate, createBy "+
				"FROM tbl_Gift%s ORDER BY giftStartRange ASC",
				topN(app, 100), where)
			return runSelect(app, q)
		},
	}
	c.Flags().BoolVar(&includeInactive, "include-inactive", false, "include gifts with giftAllow <> 1")
	return c
}

// schemesIssuedLive filters out soft-deleted rows for tbl_saveGift, which uses
// the `active` int flag (1 = live) instead of a `deleted` column.
func schemesIssuedLive(includeDeleted bool) string {
	if includeDeleted {
		return ""
	}
	return "active = 1"
}

func schemesIssuedWhere(f *domFilters) string {
	return fWhere(
		fEqInt("personId", f.Person),
		fEqInt("retailerId", f.Retailer),
		fDateGE("createdDate", f.From),
		fDateLT("createdDate", f.To),
		schemesIssuedLive(f.IncludeDeleted),
	)
}

func schemesIssuedCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "issued",
		Short:   "List gifts issued in the field (tbl_saveGift)",
		Example: "  dsr schemes issued --from 2026-07-01 --to 2026-08-01\n  dsr schemes issued --salesperson 812 --retailer 10432 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d Id, salesId, personId, retailerId, giftId, giftName, "+
				"giftrange, QtyProduct, totalQty, active, remark, createdDate "+
				"FROM tbl_saveGift%s ORDER BY Id DESC",
				topN(app, 100), schemesIssuedWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "retailer", "deleted")
	return c
}

func schemesGetCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "get <giftId>",
		Short:   "Show one gift tier and its per-retailer eligibility count",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr schemes get 7 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("giftId must be an integer, got %q", args[0])
			}
			q := fmt.Sprintf("SELECT g.giftId, g.giftName, g.giftRange, g.giftStartRange, "+
				"g.giftEndRange, g.giftAllow, g.createdDate, "+
				"(SELECT COUNT(*) FROM tbl_GiftMapwithRetailer m "+
				"WHERE m.giftId = g.giftId AND ISNULL(m.isActive, 0) = 1) AS eligibleRetailers "+
				"FROM tbl_Gift g WHERE g.giftId = %d", id)
			return runSelect(app, q)
		},
	}
}

func schemesCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "count",
		Short: "Count scheme line items (tbl_SchemeProductsSold) matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS schemeLines FROM tbl_SchemeProductsSold" + schemesSoldWhere(&f)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "item", "deleted")
	return c
}
