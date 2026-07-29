package cli

// Domain commands for GPS attendance punches (tbl_salesPersonAttendance) and
// the back-office reconciled register (tbl_AttendanceAudit). See domain.go for
// the shared conventions used by every subsystem file.
//
// Notes:
//   - personId -> tbl_salesperson.personId (the field person).
//   - The real punch-time column is `timeStamp` (datetime); the audit register
//     keys on `date` (a DATE). Both tables have NO soft-delete column, so no
//     fLive filter is applied here.
//   - status "EOD" = end-of-day check-out; opening punches carry the day-start
//     status. imagePath is the attendance selfie filename.

import (
	"fmt"

	"github.com/spf13/cobra"
)

func init() { register(newAttendanceCmd) }

func newAttendanceCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "attendance",
		Short:   "GPS attendance — punches, per-person summary, register (tbl_salesPersonAttendance)",
		Aliases: []string{"att", "punches"},
	}
	c.AddCommand(
		attendanceListCmd(app),
		attendanceSummaryCmd(app),
		attendanceCountCmd(app),
		attendanceRegisterCmd(app),
	)
	return c
}

// attendanceSelectCols is the friendly column set for punch list output.
const attendanceSelectCols = "id, personId, timeStamp, status, latitude, longitude, accuracy, retailerId, imagePath, address"

// attendanceWhere builds the WHERE clause over tbl_salesPersonAttendance,
// bounding by salesperson (personId) and the timeStamp date range.
func attendanceWhere(f *domFilters) string {
	return fWhere(
		fEqInt("personId", f.Person),
		fDateGE("timeStamp", f.From),
		fDateLT("timeStamp", f.To),
	)
}

func attendanceListCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "list",
		Short:   "List attendance punches (newest first); filter by --salesperson/--from/--to",
		Example: "  dsr attendance list --salesperson 873 --from 2026-07-01 --to 2026-08-01\n  dsr attendance list --from 2026-07-28 -n 50 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_salesPersonAttendance%s ORDER BY timeStamp DESC",
				topN(app, 100), attendanceSelectCols, attendanceWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person")
	return c
}

func attendanceSummaryCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "summary",
		Short:   "Present days + punch counts per salesperson in a date range",
		Example: "  dsr attendance summary --from 2026-07-01 --to 2026-08-01\n  dsr attendance summary --salesperson 873 --from 2026-07-01 --to 2026-08-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d personId, "+
				"COUNT(DISTINCT CAST(timeStamp AS date)) AS presentDays, "+
				"COUNT(*) AS punches, "+
				"MIN(timeStamp) AS firstPunch, MAX(timeStamp) AS lastPunch "+
				"FROM tbl_salesPersonAttendance%s "+
				"GROUP BY personId ORDER BY presentDays DESC",
				topN(app, 200), attendanceWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person")
	return c
}

func attendanceCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "count",
		Short: "Count attendance punches matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS punches FROM tbl_salesPersonAttendance" + attendanceWhere(&f)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person")
	return c
}

// attendanceRegisterCmd reads the back-office reconciled half-day register.
// P/A codes: 'P'=Present, 'A'=Absent per half.
func attendanceRegisterCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "register",
		Short:   "Half-day present/absent register with reviewer notes (tbl_AttendanceAudit)",
		Example: "  dsr attendance register --from 2026-07-01 --to 2026-08-01 --salesperson 873",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			where := fWhere(
				fEqInt("personid", f.Person),
				fDateGE("date", f.From),
				fDateLT("date", f.To),
			)
			q := fmt.Sprintf("SELECT TOP %d personid, date, presentFirstHalf, presentSecondHalf, "+
				"status, comment, modifiedBy, modifiedDate "+
				"FROM tbl_AttendanceAudit%s ORDER BY personid, date DESC",
				topN(app, 200), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person")
	return c
}
