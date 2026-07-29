package cli

// Domain commands for the Travel-Allowance (TA) subsystem. TA reimburses field
// staff for the distance covered on their daily beats: a per-person ₹/km rate
// (tbl_TA_PersonRate), the home↔shop km lookup (tbl_TA_PersonRetailerKm), a
// fixed area-to-area km matrix (tbl_TA_PlaceKm) and the legacy saved daily TA
// report (TAReprotSave — note the misspelling, all money/number/date cols are
// nvarchar strings so cast with TRY_CONVERT before comparing).
//
// These tables carry no `deleted` column — they use IsActive (bit) instead — so
// the "live" filter here is IsActive = 1, toggled with --include-deleted.
// TAReprotSave has neither, so it is never IsActive-filtered.

import (
	"fmt"

	"github.com/spf13/cobra"
)

func init() { register(newTravelCmd) }

func newTravelCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "travel",
		Short:   "Travel allowance (TA) — rates, km, reports (tbl_TA_*, TAReprotSave)",
		Aliases: []string{"ta"},
	}
	c.AddCommand(
		travelRatesCmd(app),
		travelKmCmd(app),
		travelPlaceCmd(app),
		travelReportsCmd(app),
		travelCountCmd(app),
	)
	return c
}

// travelActive returns the IsActive="live" fragment for the tbl_TA_* masters
// (prefix is "" or "alias."). --include-deleted disables it.
func travelActive(prefix string, includeDeleted bool) string {
	if includeDeleted {
		return ""
	}
	return prefix + "IsActive = 1"
}

func travelRatesCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "rates",
		Short:   "Per-salesperson ₹/km rates (tbl_TA_PersonRate); --salesperson to filter",
		Example: "  dsr travel rates --salesperson 42\n  dsr travel rates --include-deleted --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d Id, PersonId, Rate, EffectiveFrom, EffectiveTo, IsActive "+
				"FROM tbl_TA_PersonRate%s ORDER BY PersonId, EffectiveFrom DESC",
				topN(app, 100),
				fWhere(fEqInt("PersonId", f.Person), travelActive("", f.IncludeDeleted)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "person", "deleted")
	return c
}

func travelKmCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "km",
		Short:   "Home↔shop distance lookup (tbl_TA_PersonRetailerKm); --salesperson/--retailer",
		Example: "  dsr travel km --salesperson 42\n  dsr travel km --retailer 10432 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d Id, PersonId, RetailerId, HomeToShopKm, ShopToHomeKm, TravelModeId, IsActive "+
				"FROM tbl_TA_PersonRetailerKm%s ORDER BY PersonId, RetailerId",
				topN(app, 200),
				fWhere(
					fEqInt("PersonId", f.Person),
					fEqInt("RetailerId", f.Retailer),
					travelActive("", f.IncludeDeleted),
				))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "person", "retailer", "deleted")
	return c
}

func travelPlaceCmd(app *App) *cobra.Command {
	var f domFilters
	var fromArea, toArea int
	c := &cobra.Command{
		Use:     "place",
		Short:   "Fixed area-to-area km matrix (tbl_TA_PlaceKm); --from-area/--to-area",
		Example: "  dsr travel place\n  dsr travel place --from-area 839 --to-area 839",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d Id, FromAreaId, ToAreaId, FixedKm, IsActive "+
				"FROM tbl_TA_PlaceKm%s ORDER BY FromAreaId, ToAreaId",
				topN(app, 100),
				fWhere(
					fEqInt("FromAreaId", fromArea),
					fEqInt("ToAreaId", toArea),
					travelActive("", f.IncludeDeleted),
				))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "deleted")
	c.Flags().IntVar(&fromArea, "from-area", 0, "filter by FromAreaId")
	c.Flags().IntVar(&toArea, "to-area", 0, "filter by ToAreaId")
	return c
}

func travelReportsCmd(app *App) *cobra.Command {
	var f domFilters
	var status int
	c := &cobra.Command{
		Use:   "reports",
		Short: "Legacy saved daily TA reports (TAReprotSave); --salesperson/--from/--to/--status",
		Example: "  dsr travel reports --salesperson 42 --from 2022-01-01 --to 2022-07-01\n" +
			"  dsr travel reports --status 0 --json",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			// Date/number cols are nvarchar strings — TRY_CONVERT before comparing.
			parts := []string{
				fEqInt("personid", f.Person),
				fDateGE("TRY_CONVERT(datetime, Date)", f.From),
				fDateLT("TRY_CONVERT(datetime, Date)", f.To),
			}
			if cmd.Flags().Changed("status") {
				parts = append(parts, fmt.Sprintf("status = %d", status))
			}
			q := fmt.Sprintf("SELECT TOP %d Id, personid, Date, Area, distance, Rate, Amount, TotalAmount, "+
				"ApproveAmount, TotalShops, FromAreaId, ToAreaId, status, ApprovedBy, ApprovedOn "+
				"FROM TAReprotSave%s ORDER BY TRY_CONVERT(datetime, Date) DESC",
				topN(app, 100), fWhere(parts...))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "person", "date")
	c.Flags().IntVar(&status, "status", 0, "filter by approval status (e.g. 0 = pending)")
	return c
}

func travelCountCmd(app *App) *cobra.Command {
	var f domFilters
	var status int
	c := &cobra.Command{
		Use:   "count",
		Short: "Count saved daily TA reports (TAReprotSave) matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			parts := []string{
				fEqInt("personid", f.Person),
				fDateGE("TRY_CONVERT(datetime, Date)", f.From),
				fDateLT("TRY_CONVERT(datetime, Date)", f.To),
			}
			if cmd.Flags().Changed("status") {
				parts = append(parts, fmt.Sprintf("status = %d", status))
			}
			q := "SELECT COUNT(*) AS ta_reports FROM TAReprotSave" + fWhere(parts...)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "person", "date")
	c.Flags().IntVar(&status, "status", 0, "filter by approval status (e.g. 0 = pending)")
	return c
}
