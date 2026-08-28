package cli

// `ary doctor` — one command that answers "is ARY reachable, and how fresh is
// the data?". It is the first thing to run on a new box and the thing to run
// before quoting any figure.

import (
	"fmt"

	"github.com/spf13/cobra"

	"ary/internal/db"
)

func init() { register(newDoctorCmd) }

func newDoctorCmd(app *App) *cobra.Command {
	var skipFresh bool
	c := &cobra.Command{
		Use:   "doctor",
		Short: "Health check: reachability, server, privileges, and DATA FRESHNESS per module",
		Long: "Reports connectivity, the SQL Server build, the login's privilege level, and — the part\n" +
			"that matters before quoting a number — the last document date in every module.\n" +
			"A module whose last document is old is either idle or its feed has stopped; ARY's sale\n" +
			"feed pauses during a physical stock audit, so a stale sales date is not automatically a fault.",
		Example: "  ary doctor\n  ary doctor --no-freshness\n  ary doctor --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()

			res := &db.Result{Columns: []string{"check", "value"}}
			add := func(k string, v any) { res.Rows = append(res.Rows, []any{k, v}) }

			one := func(q string) (string, error) {
				r, err := app.DB.Query(ctx, app.DBName(), q)
				if err != nil {
					return "", err
				}
				if len(r.Rows) == 0 || len(r.Rows[0]) == 0 || r.Rows[0][0] == nil {
					return "", nil
				}
				return fmt.Sprintf("%v", r.Rows[0][0]), nil
			}

			add("host", fmt.Sprintf("%s:%d", app.Prof.Host, app.Prof.Port))
			add("database", app.DBName())
			add("login", app.Prof.User)

			ver, err := one("SELECT LEFT(CAST(SERVERPROPERTY('ProductVersion') AS varchar(64)),32) + ' (' + CAST(SERVERPROPERTY('Edition') AS varchar(64)) + ')'")
			if err != nil {
				add("reachable", "NO — "+err.Error())
				return app.Render(res)
			}
			add("reachable", "yes")
			add("sql server", ver)

			if v, err := one("SELECT CASE WHEN IS_SRVROLEMEMBER('sysadmin')=1 THEN 'sysadmin (OVER-PRIVILEGED — prefer a read-only login)' ELSE 'not sysadmin' END"); err == nil {
				add("privileges", v)
			}
			if v, err := one("SELECT CAST(COUNT(*) AS varchar(16)) FROM sys.tables"); err == nil {
				add("tables", v)
			}

			if skipFresh {
				return app.Render(res)
			}

			// Freshness per module: last document date + row count.
			type mod struct{ label, sql string }
			mods := []mod{
				{"sales (SaleHeader)", "SELECT CONVERT(varchar(16),MAX(VoucherDate),120) + '  ·  ' + CAST(COUNT(*) AS varchar(16)) + ' bills' FROM SaleHeader"},
				{"sale returns", "SELECT CONVERT(varchar(16),MAX(VoucherDate),120) + '  ·  ' + CAST(COUNT(*) AS varchar(16)) + ' docs' FROM SaleReturnHeader"},
				{"purchases", "SELECT CONVERT(varchar(16),MAX(VoucherDate),120) + '  ·  ' + CAST(COUNT(*) AS varchar(16)) + ' bills' FROM PurchaseHeader WHERE ISNULL(IsDeleted,0)=0"},
				{"accounting (vouchers)", "SELECT CONVERT(varchar(16),MAX(VoucherDate),120) + '  ·  ' + CAST(COUNT(*) AS varchar(16)) + ' vouchers' FROM TransactionMaster WHERE ISNULL(IsDeleted,0)=0"},
				{"stock transfers", "SELECT CONVERT(varchar(16),MAX(VoucherDate),120) + '  ·  ' + CAST(COUNT(*) AS varchar(16)) + ' docs' FROM StockTransferHeader"},
				{"stock journals", "SELECT CONVERT(varchar(16),MAX(VoucherDate),120) + '  ·  ' + CAST(COUNT(*) AS varchar(16)) + ' docs' FROM StockJournalHeader"},
				{"physical counts", "SELECT CONVERT(varchar(16),MAX(VoucherDate),120) + '  ·  ' + CAST(COUNT(*) AS varchar(16)) + ' counts' FROM PhysicalStockHeader"},
				{"products", "SELECT CAST(COUNT(*) AS varchar(16)) + ' SKUs  ·  ' + CAST(SUM(CASE WHEN ISNULL(IsActive,0)=1 THEN 1 ELSE 0 END) AS varchar(16)) + ' active' FROM ProductMaster"},
				{"customers", "SELECT CAST(COUNT(*) AS varchar(16)) + ' customers' FROM CustomerMaster"},
				{"warehouses", "SELECT CAST(COUNT(*) AS varchar(16)) + ' warehouses  ·  ' + CAST((SELECT COUNT(*) FROM LocationMaster) AS varchar(16)) + ' locations' FROM WarehouseMaster"},
			}
			for _, m := range mods {
				v, err := one(m.sql)
				if err != nil {
					v = "ERROR: " + err.Error()
				}
				add(m.label, v)
			}
			return app.Render(res)
		},
	}
	c.Flags().BoolVar(&skipFresh, "no-freshness", false, "skip the per-module freshness probes (faster)")
	return c
}
