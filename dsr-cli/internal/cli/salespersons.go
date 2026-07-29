package cli

// Domain commands for the field-workforce master (tbl_salesperson) and its
// lookups (tbl_PersonType, tbl_PersonGroupMaster, tbl_hierarchy).
//
// Notes that shape these commands (see study/vault/sales-person-master.md):
//   - PK is ID (uppercase). `deleted` (int, 0/1) is the soft-delete flag — 89%
//     of rows are deleted, so fLive matters a lot here.
//   - PERSONTYPE and personGroup are stored as TEXT labels, joined to the
//     lookups BY NAME (tbl_PersonType.PersonType / tbl_PersonGroupMaster.GroupCode).
//   - parent (int) is the reports-to → tbl_salesperson.ID (self-ref).
//   - distributor (nvarchar) holds tbl_retailers.Id as a string ('-1' = none).
//   - STATE column is dead (empty on every row) — kept only so --state works
//     on the literal column; the real territory map is tbl_PersonState.
//   - NEVER select the `password` column (encrypted) or tbl_hierarchy.passcode.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newSalespersonsCmd) }

func newSalespersonsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "salespersons",
		Short:   "Field workforce — list, get, count, subordinates (tbl_salesperson)",
		Aliases: []string{"salesperson", "people", "workforce", "sp"},
	}
	c.AddCommand(
		salespersonsListCmd(app),
		salespersonsGetCmd(app),
		salespersonsCountCmd(app),
		salespersonsSubordinatesCmd(app),
	)
	return c
}

// salespersonsSelectCols is the friendly column set for list output (no password).
const salespersonsSelectCols = "ID, PERSONNAME, PERSONTYPE, personGroup, parentType, parent, " +
	"CONTACTNO, EMAIL, employeeId, distributor, dateOfJoining, lastLoginDate, approvedStatus"

func salespersonsWhere(f *domFilters, typ string) string {
	return fWhere(
		fEqStr("PERSONTYPE", typ),
		fEqStr("STATE", f.State),
		fLive("", f.IncludeDeleted),
	)
}

func salespersonsListCmd(app *App) *cobra.Command {
	var f domFilters
	var typ string
	c := &cobra.Command{
		Use:     "list",
		Short:   "List salespersons (newest first); filter by --type (PERSONTYPE)/--state",
		Example: "  dsr salespersons list --type SO\n  dsr salespersons list --type ASM -n 20 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_salesperson%s ORDER BY ID DESC",
				topN(app, 100), salespersonsSelectCols, salespersonsWhere(&f, typ))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "state", "deleted")
	c.Flags().StringVar(&typ, "type", "", "filter by PERSONTYPE label (e.g. SO, ASM, RSM, PROMOTER(MT))")
	return c
}

func salespersonsCountCmd(app *App) *cobra.Command {
	var f domFilters
	var typ string
	c := &cobra.Command{
		Use:   "count",
		Short: "Count salespersons matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS salespersons FROM tbl_salesperson" + salespersonsWhere(&f, typ)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "state", "deleted")
	c.Flags().StringVar(&typ, "type", "", "filter by PERSONTYPE label (e.g. SO, ASM, RSM, PROMOTER(MT))")
	return c
}

func salespersonsGetCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "get <id>",
		Short:   "Show a single salesperson by ID (excludes the password column)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr salespersons get 55 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("salesperson id must be an integer, got %q", args[0])
			}
			// Explicit column list — never select `password`.
			q := fmt.Sprintf("SELECT ID, PERSONNAME, PERSONTYPE, personGroup, parentType, parent, "+
				"CONTACTNO, EMAIL, ADDRESS, STATE, employeeId, userName, distributor, distributorRequired, "+
				"homeState, homeZone, homeArea, headState, headZone, weekOff, distanceAllowed, "+
				"startTime, endTime, lockOffBeat, gender, maritalStatus, DOB, dateOfJoining, dateOfExit, "+
				"exitReason, sourceOfHire, fatherName, lastLoginDate, appVersion, "+
				"CreatedBy, CreatedOn, approvedStatus, approvedBy, approvedOn, deleted "+
				"FROM tbl_salesperson WHERE ID = %d", id)
			return runSelect(app, q)
		},
	}
}

func salespersonsSubordinatesCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "subordinates <managerId>",
		Short:   "List the people who report to a manager (WHERE parent = managerId)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr salespersons subordinates 55\n  dsr salespersons subordinates 55 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			mgr, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("manager id must be an integer, got %q", args[0])
			}
			where := fWhere(
				fEqInt("parent", mgr),
				fLive("", f.IncludeDeleted),
			)
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_salesperson%s ORDER BY PERSONNAME",
				topN(app, 200), salespersonsSelectCols, where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "deleted")
	return c
}
