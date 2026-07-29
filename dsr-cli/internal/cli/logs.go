package cli

// Domain commands for the platform diagnostics layer (tbl_apiexceptions, hslog).
// See study/vault/logs-and-exceptions.md and domain.go for the conventions.
//
// IMPORTANT — these two tables are NOT business data:
//   - tbl_apiexceptions is the mobile/API firehose: ~8.5M rows, 4 columns
//     (id, personid, exception, timestamp). 99.9% of rows are GetShopsData
//     breadcrumbs ("Starting …"/"Returning …"); only ~7.6K rows are real
//     errors. It has NO `deleted` column, so the soft-delete filter does not
//     apply. `id` increases monotonically → a safe chronological proxy.
//     ALWAYS bound with TOP + date; a GROUP BY over the whole table is a full
//     scan (~2–4 min).
//   - hslog is a single-column heap (Text nvarchar(max)) with no id, no
//     timestamp and no key — a bag of forensic breadcrumbs. The report screens
//     archive their full SQL here (rows with LEN(Text) > 500).
//
// `personid` in tbl_apiexceptions is a salesperson id stored as text, but 7,080
// error rows hold a truncated JSON body instead — always TRY_CAST it to int.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newLogsCmd) }

func newLogsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "logs",
		Short:   "Platform diagnostics — API exceptions & report-SQL log (read-only)",
		Aliases: []string{"log", "diagnostics", "exceptions"},
	}
	c.AddCommand(
		logsRecentCmd(app),
		logsCountCmd(app),
		logsErrorsCmd(app),
		logsReportsCmd(app),
	)
	return c
}

// logsExcCols is the friendly column set for tbl_apiexceptions list output.
// `timestamp` is a reserved word → always bracketed.
const logsExcCols = "id, personid, [timestamp] AS ts, LEFT(exception, 200) AS message"

// logsExcWhere builds the WHERE clause for tbl_apiexceptions. realOnly drops the
// 8.5M GetShopsData breadcrumbs so only genuine errors remain. This table has no
// `deleted` column, so fLive is intentionally not applied.
func logsExcWhere(f *domFilters, realOnly bool) string {
	parts := []string{
		fDateGE("[timestamp]", f.From),
		fDateLT("[timestamp]", f.To),
	}
	if f.Person > 0 {
		// personid is varchar; compare against the numeric id as text.
		parts = append(parts, fEqStr("personid", strconv.Itoa(f.Person)))
	}
	if realOnly {
		parts = append(parts,
			"exception NOT LIKE 'Starting %'",
			"exception NOT LIKE 'Returning %'")
	}
	return fWhere(parts...)
}

func logsRecentCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "recent",
		Short: "Newest API exceptions (breadcrumbs + errors), most recent first",
		Long: "Lists the most recent rows of tbl_apiexceptions by id (a safe chronological\n" +
			"proxy). Bounded by TOP and, optionally, --from/--to. Includes GetShopsData\n" +
			"sync breadcrumbs — use `logs errors` for genuine errors only.",
		Example: "  dsr logs recent\n  dsr logs recent --from 2026-07-01 --to 2026-08-01 -n 50\n  dsr logs recent --salesperson 2607 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_apiexceptions%s ORDER BY id DESC",
				topN(app, 100), logsExcCols, logsExcWhere(&f, false))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person")
	return c
}

func logsErrorsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "errors",
		Short: "Real errors only (drops the GetShopsData sync breadcrumbs), newest first",
		Long: "Same as `recent` but filters out the 'Starting …'/'Returning …' GetShopsData\n" +
			"breadcrumbs, leaving only genuine catch-block exceptions (~7.6K of 8.5M rows).",
		Example: "  dsr logs errors --from 2026-05-01\n  dsr logs errors --salesperson 2607 -n 100 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_apiexceptions%s ORDER BY id DESC",
				topN(app, 100), logsExcCols, logsExcWhere(&f, true))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person")
	return c
}

func logsCountCmd(app *App) *cobra.Command {
	var f domFilters
	var realOnly bool
	c := &cobra.Command{
		Use:   "count",
		Short: "Count API exceptions in a date window (--from/--to required to avoid a full scan)",
		Long: "Counts rows of tbl_apiexceptions. A date bound is REQUIRED: at 8.5M rows an\n" +
			"unbounded COUNT is a full-table scan. Pass --errors to count genuine errors only.",
		Example: "  dsr logs count --from 2026-07-01 --to 2026-08-01\n  dsr logs count --from 2026-07-01 --errors",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if f.From == "" && f.To == "" {
				return Usagef("logs count needs a date bound — pass --from and/or --to (the table has 8.5M rows)")
			}
			q := "SELECT COUNT(*) AS exceptions FROM tbl_apiexceptions" + logsExcWhere(&f, realOnly)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person")
	c.Flags().BoolVar(&realOnly, "errors", false, "count only genuine errors (drop GetShopsData breadcrumbs)")
	return c
}

func logsReportsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "reports",
		Short: "Report-SQL texts archived in hslog (MIS / All-Sales & Attendance audit)",
		Long: "hslog is a keyless single-column heap; the two big report screens log their\n" +
			"full generated SQL here (rows with LEN(Text) > 500). This classifies each and\n" +
			"shows the first embedded date literal (the period the user asked for). Bounded\n" +
			"by TOP; hslog has no timestamp, so ordering is by SQL length, not time.",
		Example: "  dsr logs reports\n  dsr logs reports -n 50 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d "+
				"CASE WHEN Text LIKE '%%/*%%IDENTITY%%*/%%' THEN 'MIS / All-Sales dashboard' "+
				"WHEN Text LIKE '%%tbl_attendanceaudit%%' THEN 'Attendance audit' "+
				"ELSE 'other report' END AS report, "+
				"LEN(Text) AS sqlLength, "+
				"CASE WHEN CHARINDEX('''20', Text) > 0 "+
				"THEN SUBSTRING(Text, CHARINDEX('''20', Text) + 1, 10) END AS firstDateLiteral, "+
				"LEFT(Text, 120) AS head "+
				"FROM hslog WHERE LEN(Text) > 500 ORDER BY sqlLength DESC",
				topN(app, 100))
			return runSelect(app, q)
		},
	}
	return c
}
