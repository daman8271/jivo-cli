package cli

// Domain commands for GPS breadcrumb tracking (tbl_geoLocation). See domain.go
// for the shared helpers and conventions.
//
// tbl_geoLocation is ~27M rows (a ping every couple of minutes per active
// field person). It has NO soft-delete column, so fLive is not applied here.
// SAFETY: every query MUST filter by personId AND be bounded by TOP — a full
// scan of this table is never allowed. The `track` command additionally
// requires a --from/--to date window; `last` is a single-row lookup.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newGeoCmd) }

func newGeoCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "geo",
		Short:   "GPS breadcrumb trail — track, last, count (tbl_geoLocation, ~27M rows)",
		Aliases: []string{"location", "gps", "breadcrumb"},
	}
	c.AddCommand(geoTrackCmd(app), geoLastCmd(app), geoCountCmd(app))
	return c
}

// geoSelectCols is the friendly column set for breadcrumb output (no sensitive
// columns exist in this table).
const geoSelectCols = "id, personId, timeStamp, latitude, longitude, location, accuracy, speed, battery, GpsEnabled, retailerId, salesId"

// geoPersonID validates and returns the positional personId argument.
func geoPersonID(arg string) (int, error) {
	id, err := strconv.Atoi(arg)
	if err != nil || id <= 0 {
		return 0, Usagef("personId must be a positive integer, got %q", arg)
	}
	return id, nil
}

func geoTrackCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "track <personId> --from <date> --to <date>",
		Short: "Replay a person's GPS breadcrumb trail over a date window (oldest first)",
		Example: "  dsr geo track 873 --from 2026-07-28 --to 2026-07-29\n" +
			"  dsr geo track 873 --from 2026-07-28 --to 2026-07-29 -n 1000 --json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := geoPersonID(args[0])
			if err != nil {
				return err
			}
			if f.From == "" || f.To == "" {
				return Usagef("track requires both --from and --to (tbl_geoLocation is ~27M rows; a date window is mandatory)")
			}
			where := fWhere(
				fEqInt("personId", id),
				fDateGE("timeStamp", f.From),
				fDateLT("timeStamp", f.To),
			)
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_geoLocation%s ORDER BY timeStamp ASC",
				topN(app, 500), geoSelectCols, where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

func geoLastCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "last <personId>",
		Short:   "Show the single most recent GPS fix for a person",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr geo last 873 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := geoPersonID(args[0])
			if err != nil {
				return err
			}
			where := fWhere(fEqInt("personId", id))
			q := fmt.Sprintf("SELECT TOP 1 %s FROM tbl_geoLocation%s ORDER BY timeStamp DESC",
				geoSelectCols, where)
			return runSelect(app, q)
		},
	}
}

func geoCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "count <personId> --from <date> --to <date>",
		Short:   "Count GPS fixes for a person over a date window",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr geo count 873 --from 2026-07-28 --to 2026-07-29",
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := geoPersonID(args[0])
			if err != nil {
				return err
			}
			if f.From == "" || f.To == "" {
				return Usagef("count requires both --from and --to (tbl_geoLocation is ~27M rows; a date window is mandatory)")
			}
			where := fWhere(
				fEqInt("personId", id),
				fDateGE("timeStamp", f.From),
				fDateLT("timeStamp", f.To),
			)
			q := "SELECT COUNT(*) AS fixes FROM tbl_geoLocation" + where
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	return c
}
