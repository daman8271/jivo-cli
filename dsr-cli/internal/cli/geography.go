package cli

// Domain commands for the territory hierarchy: State -> Zone -> Area -> SubArea.
// See domain.go for the shared conventions and geography-and-scoping.md for the
// study notes.
//
// Notes that shape this file:
//   - The one real FK in the whole DB is tbl_zones.stateId -> tbl_states.stateId.
//     areas.zoneId and subArea.areaId link by convention (a few ids dangle).
//   - NONE of the four hierarchy tables has a `deleted` column — geography is
//     hard-deleted — so fLive / --include-deleted do NOT apply here.
//   - The FK columns (stateId, zoneId, areaId) are real INT columns on these
//     master tables (only tbl_retailers stores them as text). Filter by integer.

import (
	"fmt"

	"github.com/spf13/cobra"
)

func init() { register(newGeographyCmd) }

func newGeographyCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "geography",
		Short:   "Territory hierarchy — states, zones, areas, sub-areas",
		Aliases: []string{"geo", "territory"},
	}
	c.AddCommand(
		geographyStatesCmd(app),
		geographyZonesCmd(app),
		geographyAreasCmd(app),
		geographySubAreasCmd(app),
	)
	return c
}

// geographyStatesCmd lists the 21 marketing states (top of the hierarchy).
func geographyStatesCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "states",
		Short:   "List states (stateId, name, short code)",
		Args:    cobra.NoArgs,
		Example: "  dsr geography states\n  dsr geography states --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d stateId, state, short, Latitude, Longitude "+
				"FROM tbl_states ORDER BY stateId", topN(app, 100))
			return runSelect(app, q)
		},
	}
}

// geographyZonesCmd lists zones (city/district), optionally scoped to a state.
func geographyZonesCmd(app *App) *cobra.Command {
	var state int
	c := &cobra.Command{
		Use:     "zones",
		Short:   "List zones under a state; filter with --state <stateId>",
		Args:    cobra.NoArgs,
		Example: "  dsr geography zones --state 2\n  dsr geography zones --state 1 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d z.zoneId, z.zone, z.stateId, s.state, s.short "+
				"FROM tbl_zones z LEFT JOIN tbl_states s ON s.stateId = z.stateId%s "+
				"ORDER BY s.state, z.zone",
				topN(app, 200), fWhere(fEqInt("z.stateId", state)))
			return runSelect(app, q)
		},
	}
	c.Flags().IntVar(&state, "state", 0, "filter by state id (tbl_states.stateId)")
	return c
}

// geographyAreasCmd lists areas (beat-sized localities), optionally scoped to a zone.
func geographyAreasCmd(app *App) *cobra.Command {
	var zone int
	c := &cobra.Command{
		Use:     "areas",
		Short:   "List areas under a zone; filter with --zone <zoneId>",
		Args:    cobra.NoArgs,
		Example: "  dsr geography areas --zone 116\n  dsr geography areas --zone 116 -n 50 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d a.areaId, a.area, a.zoneId, z.zone "+
				"FROM tbl_areas a LEFT JOIN tbl_zones z ON z.zoneId = a.zoneId%s "+
				"ORDER BY z.zone, a.area",
				topN(app, 200), fWhere(fEqInt("a.zoneId", zone)))
			return runSelect(app, q)
		},
	}
	c.Flags().IntVar(&zone, "zone", 0, "filter by zone id (tbl_zones.zoneId)")
	return c
}

// geographySubAreasCmd lists sub-areas (the mostly-unused 4th level), scoped to an area.
func geographySubAreasCmd(app *App) *cobra.Command {
	var area int
	c := &cobra.Command{
		Use:     "subareas",
		Short:   "List sub-areas under an area; filter with --area <areaId>",
		Args:    cobra.NoArgs,
		Example: "  dsr geography subareas --area 793\n  dsr geography subareas --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d sa.subAreaId, sa.subArea, sa.areaId, a.area "+
				"FROM tbl_subArea sa LEFT JOIN tbl_areas a ON a.areaId = sa.areaId%s "+
				"ORDER BY sa.subAreaId",
				topN(app, 200), fWhere(fEqInt("sa.areaId", area)))
			return runSelect(app, q)
		},
	}
	c.Flags().IntVar(&area, "area", 0, "filter by area id (tbl_areas.areaId)")
	return c
}
