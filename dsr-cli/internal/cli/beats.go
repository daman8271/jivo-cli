package cli

// Domain commands for beats / daily routes (tbl_beats + tbl_BeatShopMap +
// tbl_BeatAssign). A beat is a named walking route owned by one salesperson
// (tbl_beats.personId -> tbl_salesperson.ID); its shops come from
// tbl_BeatShopMap.shopId -> tbl_retailers.Id, and its calendar from
// tbl_BeatAssign.beatDate. See study/vault/beats-and-routes.md for the joins.
//
// Traps applied here: beatName is not unique (never key on it); orphan beatIds
// are common (INNER JOIN to masters); tbl_BeatAssign has duplicate
// (beatId, beatDate) pairs (dedupe); shopId can be 0/duplicated (COUNT DISTINCT
// + shopId > 0); retailer key is tbl_retailers.Id, not retailerId.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newBeatsCmd) }

func newBeatsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "beats",
		Short:   "Beats / daily routes — list, shops, assignments, count (tbl_beats)",
		Aliases: []string{"beat", "routes"},
	}
	c.AddCommand(
		beatsListCmd(app),
		beatsShopsCmd(app),
		beatsAssignmentsCmd(app),
		beatsCountCmd(app),
	)
	return c
}

// beatsWhere builds the live/salesperson filter over an aliased tbl_beats "b".
func beatsWhere(f *domFilters) string {
	return fWhere(
		fEqInt("b.personId", f.Person),
		fLive("b.", f.IncludeDeleted),
	)
}

func beatsListCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "list",
		Short:   "List beats (newest first) with owner + live shop count; filter by --salesperson",
		Example: "  dsr beats list --salesperson 28\n  dsr beats list -n 20 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf(
				"SELECT TOP %d b.beatId, b.beatName, b.personId, s.PERSONNAME, s.PERSONTYPE, "+
					"COUNT(DISTINCT CASE WHEN m.shopId > 0 THEN m.shopId END) AS shops "+
					"FROM tbl_beats b "+
					"LEFT JOIN tbl_salesperson s ON s.ID = b.personId "+
					"LEFT JOIN tbl_BeatShopMap m ON m.beatId = b.beatId AND ISNULL(m.deleted, 0) = 0%s "+
					"GROUP BY b.beatId, b.beatName, b.personId, s.PERSONNAME, s.PERSONTYPE "+
					"ORDER BY b.beatId DESC",
				topN(app, 100), beatsWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "person", "deleted")
	return c
}

func beatsShopsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "shops <beatId>",
		Short:   "List the retailers mapped to a beat (BeatShopMap join tbl_retailers)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr beats shops 192\n  dsr beats shops 192 --state 5 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			beatID, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("beatId must be an integer, got %q", args[0])
			}
			where := fWhere(
				fEqInt("m.beatId", beatID),
				"m.shopId > 0",
				fEqStr("r.state", f.State),
				fEqStr("r.zone", f.Zone),
				fLive("m.", f.IncludeDeleted),
				fLive("r.", f.IncludeDeleted),
			)
			q := fmt.Sprintf(
				"SELECT TOP %d r.Id AS shopId, r.retailerName, r.type, r.state, r.zone, r.area, r.subArea, "+
					"m.createdOn AS addedOn "+
					"FROM tbl_BeatShopMap m "+
					"JOIN tbl_retailers r ON r.Id = m.shopId "+
					"%s ORDER BY r.retailerName",
				topN(app, 200), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "state", "zone", "deleted")
	return c
}

func beatsAssignmentsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "assignments",
		Short:   "Beat calendar — which beats are scheduled on which dates (tbl_BeatAssign)",
		Example: "  dsr beats assignments --from 2026-07-01 --to 2026-07-30\n  dsr beats assignments --salesperson 28 --from 2026-07-28 --to 2026-07-29",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			where := fWhere(
				fEqInt("b.personId", f.Person),
				fDateGE("a.beatDate", f.From),
				fDateLT("a.beatDate", f.To),
				fLive("b.", f.IncludeDeleted),
			)
			// Dedupe the 2,514 duplicate (beatId, beatDate) pairs before counting.
			q := fmt.Sprintf(
				"SELECT TOP %d a.beatDate, b.beatId, b.beatName, s.PERSONNAME, s.PERSONTYPE, "+
					"COUNT(DISTINCT CASE WHEN m.shopId > 0 THEN m.shopId END) AS planned_shops "+
					"FROM (SELECT DISTINCT beatId, beatDate FROM tbl_BeatAssign) a "+
					"JOIN tbl_beats b ON b.beatId = a.beatId "+
					"LEFT JOIN tbl_salesperson s ON s.ID = b.personId "+
					"LEFT JOIN tbl_BeatShopMap m ON m.beatId = b.beatId AND ISNULL(m.deleted, 0) = 0 "+
					"%s "+
					"GROUP BY a.beatDate, b.beatId, b.beatName, s.PERSONNAME, s.PERSONTYPE "+
					"ORDER BY a.beatDate DESC, b.beatId",
				topN(app, 200), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "deleted")
	return c
}

func beatsCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "count",
		Short: "Count live beats matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS beats FROM tbl_beats b" + beatsWhere(&f)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "person", "deleted")
	return c
}
