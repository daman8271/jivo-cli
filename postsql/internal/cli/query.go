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
		Long: "Run a read-only SQL statement (SELECT/WITH/EXPLAIN/SHOW/TABLE/VALUES).\n" +
			"With no argument, SQL is read from stdin. --limit wraps SELECTs.",
		Example: "  postsql query \"SELECT * FROM accounts_user LIMIT 5\" --json\n" +
			"  echo 'SELECT now()' | postsql query",
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
				sql = "SELECT * FROM (" + strings.TrimRight(sql, "; \n\t") + ") AS _postsql LIMIT " +
					strconv.Itoa(app.Flags.Limit)
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

// wrappable reports whether a LIMIT subquery wrapper is safe to apply.
func wrappable(sql string) bool {
	s := strings.ToLower(strings.TrimSpace(sql))
	for _, p := range []string{"select", "with", "table", "values"} {
		if strings.HasPrefix(s, p) {
			return true
		}
	}
	return false
}
