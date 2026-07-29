package cli

import (
	"io"
	"os"
	"strconv"
	"strings"

	"github.com/spf13/cobra"
)

func init() { register(newQueryCmd) }

func newQueryCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "query [sql]",
		Short: "Run a read-only SQL query (reads from stdin if no argument)",
		Long: "Run a read-only T-SQL statement (SELECT or WITH only).\n" +
			"With no argument, SQL is read from stdin. --limit wraps the query in SELECT TOP N.",
		Example: "  dsr query \"SELECT TOP 5 * FROM tbl_retailers\" --json\n" +
			"  echo 'SELECT COUNT(*) FROM tbl_salesPersonAttendance' | dsr query",
		Args: cobra.ArbitraryArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			sql := strings.TrimSpace(strings.Join(args, " "))
			if sql == "" {
				b, _ := io.ReadAll(os.Stdin)
				sql = strings.TrimSpace(string(b))
			}
			if sql == "" {
				return Usagef("no SQL provided (pass as an argument or via stdin)")
			}
			if app.Flags.Limit > 0 && wrappable(sql) {
				sql = "SELECT TOP " + strconv.Itoa(app.Flags.Limit) +
					" * FROM (" + strings.TrimRight(sql, "; \n\t") + ") AS _dsr"
			}
			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), sql)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}

// wrappable reports whether a SELECT TOP wrapper is safe to apply.
func wrappable(sql string) bool {
	s := strings.ToLower(strings.TrimSpace(sql))
	return strings.HasPrefix(s, "select") || strings.HasPrefix(s, "with")
}
