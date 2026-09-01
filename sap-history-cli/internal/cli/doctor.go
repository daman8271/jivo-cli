package cli

// `saphist doctor` — "is the old-books server reachable, and what period does
// each book actually cover?". First thing to run on a new box, and the thing to
// run before quoting any figure out of the closed books.

import (
	"fmt"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newDoctorCmd) }

// doctorCoverageSQL returns, for one book, the row count and date span of every
// module in a single round trip.
const doctorCoverageSQL = `
SELECT 'A/R invoices' AS module, COUNT(*) AS docs, CONVERT(varchar(10),MIN(DocDate),120) AS first_doc, CONVERT(varchar(10),MAX(DocDate),120) AS last_doc FROM OINV
UNION ALL SELECT 'A/R credit notes', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM ORIN
UNION ALL SELECT 'A/P invoices', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM OPCH
UNION ALL SELECT 'A/P credit notes', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM ORPC
UNION ALL SELECT 'sales orders', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM ORDR
UNION ALL SELECT 'purchase orders', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM OPOR
UNION ALL SELECT 'deliveries', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM ODLN
UNION ALL SELECT 'goods receipt PO', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM OPDN
UNION ALL SELECT 'incoming payments', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM ORCT
UNION ALL SELECT 'outgoing payments', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM OVPM
UNION ALL SELECT 'journal entries', COUNT(*), CONVERT(varchar(10),MIN(RefDate),120), CONVERT(varchar(10),MAX(RefDate),120) FROM OJDT
UNION ALL SELECT 'goods receipts', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM OIGN
UNION ALL SELECT 'goods issues', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM OIGE
UNION ALL SELECT 'stock transfers', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM OWTR
UNION ALL SELECT 'production orders', COUNT(*), CONVERT(varchar(10),MIN(PostDate),120), CONVERT(varchar(10),MAX(PostDate),120) FROM OWOR
UNION ALL SELECT 'drafts', COUNT(*), CONVERT(varchar(10),MIN(DocDate),120), CONVERT(varchar(10),MAX(DocDate),120) FROM ODRF
UNION ALL SELECT 'business partners', COUNT(*), NULL, NULL FROM OCRD
UNION ALL SELECT 'items', COUNT(*), NULL, NULL FROM OITM
UNION ALL SELECT 'G/L accounts', COUNT(*), NULL, NULL FROM OACT
UNION ALL SELECT 'branches', COUNT(*), NULL, NULL FROM OBPL
UNION ALL SELECT 'warehouses', COUNT(*), NULL, NULL FROM OWHS`

func newDoctorCmd(app *App) *cobra.Command {
	var skipCoverage bool
	c := &cobra.Command{
		Use:   "doctor",
		Short: "Health check: reachability, server, privileges, and what period each book covers",
		Long: "Reports connectivity, the SQL Server build, the login's privilege level, and — the part\n" +
			"that matters before quoting a number — the row count and date span of every module in\n" +
			"every book. These are CLOSED books: the spans should not move. If they do, someone is\n" +
			"still posting into a database everyone believes is frozen.",
		Example: "  saphist doctor\n  saphist doctor --book new\n  saphist doctor --no-coverage",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()

			head := &db.Result{Columns: []string{"check", "value"}}
			add := func(k string, v any) { head.Rows = append(head.Rows, []any{k, v}) }

			one := func(dbName, q string) (string, error) {
				r, err := app.DB.Query(ctx, dbName, q)
				if err != nil {
					return "", err
				}
				if len(r.Rows) == 0 || len(r.Rows[0]) == 0 || r.Rows[0][0] == nil {
					return "", nil
				}
				return fmt.Sprintf("%v", r.Rows[0][0]), nil
			}

			add("host", fmt.Sprintf("%s:%d", app.Prof.Host, app.Prof.Port))
			add("login", app.Prof.User)

			ver, err := one("master", "SELECT LEFT(CAST(SERVERPROPERTY('ProductVersion') AS varchar(64)),32) + ' (' + CAST(SERVERPROPERTY('Edition') AS varchar(64)) + ')'")
			if err != nil {
				add("reachable", "NO — "+err.Error())
				return app.Render(head)
			}
			add("reachable", "yes")
			add("sql server", ver)
			if v, err := one("master", "SELECT CASE WHEN IS_SRVROLEMEMBER('sysadmin')=1 THEN 'sysadmin (OVER-PRIVILEGED — saphist''s read-only guard is what protects the books)' ELSE 'not sysadmin' END"); err == nil {
				add("privileges", v)
			}
			add("writes", "impossible from this tool (SELECT-only guard + always-rolled-back transaction)")
			add("after Oct-2024", "NOT here — that is the live SAP HANA system, use the `sapb1` CLI")

			bks, err := app.Resolve("", "")
			if err != nil {
				return err
			}
			if app.Flags.Book == "" && app.Flags.Database == "" {
				bks = books // doctor always reports every book, BSU included
			}
			for _, b := range bks {
				v, err := one(b.DB, "SELECT TOP 1 CompnyName FROM OADM")
				if err != nil {
					v = "UNREACHABLE: " + err.Error()
				}
				add("book "+b.Key+" ("+b.DB+")", v)
			}

			if skipCoverage {
				return app.Render(head)
			}

			if err := app.Render(head); err != nil {
				return err
			}
			for _, b := range bks {
				fmt.Println()
				if !app.Flags.Quiet && !app.Flags.CSV {
					fmt.Printf("== book %s — %s (%s .. %s) ==\n", b.Key, b.DB, b.First, b.Last)
				}
				res, err := app.DB.Query(ctx, b.DB, doctorCoverageSQL)
				if err != nil {
					fmt.Println("ERROR:", err)
					continue
				}
				if err := app.Render(res); err != nil {
					return err
				}
			}
			return nil
		},
	}
	c.Flags().BoolVar(&skipCoverage, "no-coverage", false, "skip the per-book coverage tables (faster)")
	return c
}
