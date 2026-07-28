package cli

import "github.com/spf13/cobra"

func init() { register(newRolesCmd) }

func newRolesCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "roles",
		Aliases: []string{"users"},
		Short:   "List roles/users with their privilege attributes (cluster-wide)",
		Long: "List database roles and their attributes. Roles are cluster-wide, so this\n" +
			"is independent of --db. member_of shows the roles each one belongs to.",
		Example: "  postsql roles\n" +
			"  postsql roles --json --select role,superuser,login",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			const sql = `
				SELECT r.rolname        AS role,
				       r.rolsuper       AS superuser,
				       r.rolcanlogin    AS login,
				       r.rolcreatedb    AS createdb,
				       r.rolcreaterole  AS createrole,
				       r.rolreplication AS replication,
				       r.rolbypassrls   AS bypass_rls,
				       r.rolconnlimit   AS conn_limit,
				       r.rolvaliduntil  AS valid_until,
				       (SELECT string_agg(g.rolname, ', ' ORDER BY g.rolname)
				        FROM pg_auth_members am
				        JOIN pg_roles g ON g.oid = am.roleid
				        WHERE am.member = r.oid) AS member_of
				FROM pg_roles r
				ORDER BY r.rolname`
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
