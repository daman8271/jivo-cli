package cli

// Generic read primitives: query / peek / count / schema. These are the escape
// hatch for anything the domain commands do not cover — still SELECT-only.

import (
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/spf13/cobra"

	"ary/internal/db"
)

func init() {
	register(newQueryCmd)
	register(newPeekCmd)
	register(newCountCmd)
	register(newSchemaCmd)
}

func newQueryCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "query [sql]",
		Short: "Run a read-only SQL query (reads stdin when no argument is given)",
		Long: "Runs ONE SELECT (or WITH) statement. Anything else — INSERT/UPDATE/DELETE/EXEC, or a\n" +
			"second statement after a ';' — is refused by the guard before it reaches the server,\n" +
			"and every statement runs inside a transaction that is always rolled back.",
		Example: "  ary query \"SELECT TOP 5 * FROM SaleHeader ORDER BY VoucherDate DESC\"\n" +
			"  echo \"SELECT COUNT(*) FROM ProductMaster\" | ary query\n" +
			"  ary query \"SELECT * FROM WarehouseMaster\" --csv > warehouses.csv",
		Args: cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			var sql string
			if len(args) == 1 {
				sql = args[0]
			} else {
				b, err := io.ReadAll(os.Stdin)
				if err != nil {
					return err
				}
				sql = string(b)
			}
			if strings.TrimSpace(sql) == "" {
				return Usagef("no SQL given: pass it as an argument or on stdin")
			}
			// NOTE: --limit is deliberately NOT injected into raw SQL. Rewriting a
			// user's statement to add TOP would silently change its meaning (and
			// break any query with its own TOP or an ORDER BY that matters). Put
			// TOP in the query, or use --select / a domain command instead.
			return runSelect(app, sql)
		},
	}
}

func newPeekCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "peek <table>",
		Short:   "Show the first N rows of a table (SELECT TOP N *)",
		Example: "  ary peek SaleHeader\n  ary peek Stock -n 20 --json",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d * FROM %s", topN(app, 10), db.Ident(args[0]))
			return runSelect(app, q)
		},
	}
}

func newCountCmd(app *App) *cobra.Command {
	var where string
	c := &cobra.Command{
		Use:     "count <table>",
		Short:   "Count rows in a table, optionally filtered with --where",
		Example: "  ary count SaleHeader\n  ary count SaleHeader --where \"VoucherDate >= '2026-08-01'\"",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT COUNT(*) AS rows_ FROM %s", db.Ident(args[0]))
			if strings.TrimSpace(where) != "" {
				q += " WHERE " + where
			}
			return runSelect(app, q)
		},
	}
	c.Flags().StringVar(&where, "where", "", "raw WHERE clause (no leading WHERE)")
	return c
}

func newSchemaCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "schema",
		Short:   "Explore the catalog: databases, tables, columns",
		Aliases: []string{"catalog"},
	}
	c.AddCommand(schemaTablesCmd(app), schemaColumnsCmd(app), schemaDatabasesCmd(app))
	return c
}

func schemaTablesCmd(app *App) *cobra.Command {
	var search string
	var includeTemp bool
	c := &cobra.Command{
		Use:   "tables",
		Short: "List tables with row counts (FusionERP8 scratch Temp* tables hidden by default)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			w := fWhere(fLike("t.name", search), map[bool]string{true: "", false: "t.name NOT LIKE 'Temp%' AND t.name NOT LIKE 'Header0%'"}[includeTemp])
			q := fmt.Sprintf("SELECT TOP %d t.name AS table_name, SUM(p.rows) AS rows_ "+
				"FROM sys.tables t JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1)%s "+
				"GROUP BY t.name ORDER BY SUM(p.rows) DESC", topN(app, 100), w)
			return runSelect(app, q)
		},
	}
	c.Flags().StringVar(&search, "search", "", "substring match on the table name")
	c.Flags().BoolVar(&includeTemp, "include-temp", false, "include the app's Temp*/Header0* scratch tables")
	return c
}

func schemaColumnsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "columns <table>",
		Short:   "List a table's columns, types and nullability",
		Example: "  ary schema columns SaleHeader",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT ORDINAL_POSITION AS pos, COLUMN_NAME AS column_name, DATA_TYPE AS type, " +
				"COALESCE(CAST(CHARACTER_MAXIMUM_LENGTH AS varchar(16)),'') AS len, IS_NULLABLE AS nullable " +
				"FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = " + db.Lit(args[0]) + " ORDER BY ORDINAL_POSITION"
			return runSelect(app, q)
		},
	}
}

func schemaDatabasesCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "databases",
		Short: "List the user databases on this SQL Server instance (72 of them)",
		Long: "The box hosts far more than ARY: FR8HODBNEW (this default) is the FusionERP8 head-office\n" +
			"DB; ARY_BSU is the SAP B1 SQL company; FR8Ilahi is a separate Ilahi unit; there are also\n" +
			"BusyComp*_db* (Busy accounting books) and the jsap/DSR families. Target one with --db.",
		Aliases: []string{"dbs"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT d.name AS database_name, CAST(SUM(f.size) * 8.0 / 1024 AS decimal(12,0)) AS mb, " +
				"CONVERT(varchar(10), d.create_date, 120) AS created, d.state_desc AS state " +
				"FROM sys.databases d JOIN sys.master_files f ON f.database_id = d.database_id " +
				"WHERE d.database_id > 4 GROUP BY d.name, d.create_date, d.state_desc ORDER BY d.name"
			return runSelect(app, q)
		},
	}
}
