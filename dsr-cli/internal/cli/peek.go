package cli

import (
	"strconv"

	"github.com/spf13/cobra"

	"dsr/internal/db"
)

func init() { register(newPeekCmd) }

func newPeekCmd(app *App) *cobra.Command {
	var n int
	c := &cobra.Command{
		Use:     "peek <table>",
		Short:   "Show the first N rows of a table (SELECT TOP N *)",
		Example: "  dsr peek tbl_retailers -N 5 --json",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()
			schema, table, err := lookupTable(ctx, app, args[0])
			if err != nil {
				return err
			}
			limit := n
			if limit <= 0 {
				if app.Flags.Limit > 0 {
					limit = app.Flags.Limit
				} else {
					limit = 10
				}
			}
			q := "SELECT TOP " + strconv.Itoa(limit) + " * FROM " + db.Ident(schema, table)
			res, err := app.DB.Query(ctx, app.DBName(), q)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
	c.Flags().IntVarP(&n, "rows", "N", 0, "number of rows (default 10, or --limit)")
	return c
}
