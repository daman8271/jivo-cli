// Package cli wires the saphist command tree.
//
// Command files self-register via init() -> register(newXxxCmd), so no shared
// file needs editing when a new command is added.
package cli

import (
	"context"
	"errors"
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"

	"saphist/internal/config"
	"saphist/internal/db"
	"saphist/internal/render"
)

// Exit codes.
const (
	ExitOK       = 0
	ExitError    = 1
	ExitUsage    = 2
	ExitConn     = 3
	ExitQuery    = 4
	ExitReadOnly = 5
)

// GlobalFlags are the persistent flags shared by every command.
type GlobalFlags struct {
	Profile  string
	Book     string
	Database string
	JSON     bool
	CSV      bool
	Compact  bool
	Quiet    bool
	Limit    int
	Timeout  time.Duration
	Select   string
}

// App is the shared runtime context handed to each command constructor.
type App struct {
	Flags *GlobalFlags
	Cfg   *config.Config
	Prof  config.Profile
	DB    *db.DB
}

// DBName returns a single target database — the raw --db, else the pinned
// --book, else the newest Jivo Wellness book. Commands that answer a dated
// question should use Resolve/runBooks instead, so a range that crosses the
// 2019 cut-over reads both books.
func (a *App) DBName() string {
	if a.Flags.Database != "" {
		return a.Flags.Database
	}
	if b, ok := bookByKey(a.Flags.Book); ok {
		return b.DB
	}
	return a.Prof.Database
}

// Ctx returns a context bounded by the --timeout flag.
func (a *App) Ctx() (context.Context, context.CancelFunc) {
	to := a.Flags.Timeout
	if to <= 0 {
		to = 120 * time.Second
	}
	return context.WithTimeout(context.Background(), to)
}

// RenderOpts maps the global flags to render options.
func (a *App) RenderOpts() render.Options {
	return render.Options{
		JSON:    a.Flags.JSON,
		CSV:     a.Flags.CSV,
		Compact: a.Flags.Compact,
		Quiet:   a.Flags.Quiet,
		Select:  a.Flags.Select,
	}
}

// Render writes a result to stdout using the active output options.
func (a *App) Render(res *db.Result) error {
	return render.Render(os.Stdout, res, a.RenderOpts())
}

// usageError maps to ExitUsage.
type usageError struct{ err error }

func (e *usageError) Error() string { return e.err.Error() }
func (e *usageError) ExitCode() int { return ExitUsage }

// Usagef builds a usage error.
func Usagef(format string, a ...any) error {
	return &usageError{fmt.Errorf(format, a...)}
}

var registry []func(*App) *cobra.Command

func register(f func(*App) *cobra.Command) { registry = append(registry, f) }

// Execute builds the root command, runs it, and returns a process exit code.
func Execute() int {
	flags := &GlobalFlags{}
	app := &App{Flags: flags}

	root := &cobra.Command{
		Use:   "saphist",
		Short: "Read-only CLI for JIVO's OLD SAP B1 books, 2014-2024 (SQL Server)",
		Long: "saphist reads JIVO's closed SAP Business One company databases on the SQL Server at\n" +
			"138.252.101.118 — the books from 2014-11-01 up to the October-2024 move to HANA:\n\n" +
			"  old  Live_Jivo_WellnessN_Aug_2019   Jivo Wellness Pvt. Ltd. (Old)   2014-11 -> 2019-08\n" +
			"  new  Jivo_All_Branches_Live         Jivo Wellness Pvt. Ltd.         2019-08 -> 2024-10\n" +
			"  bsu  ARY_BSU                        Akal Rozgar Yojana (BSU)        2019-04 -> 2023-03\n\n" +
			"Give it a date range and it picks the right book itself; a range that crosses the\n" +
			"August-2019 cut-over reads BOTH and labels every row with the book it came from.\n\n" +
			"ANYTHING AFTER OCTOBER 2024 IS NOT HERE — that is the live SAP HANA system, use `sapb1`.\n\n" +
			"saphist can never write: every statement passes a SELECT-only guard and runs inside a\n" +
			"transaction that is always rolled back.",
		SilenceUsage:  true,
		SilenceErrors: true,
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := config.Load()
			if err != nil {
				return err
			}
			prof, err := cfg.Resolve(flags.Profile)
			if err != nil {
				return err
			}
			app.Cfg = cfg
			app.Prof = prof
			stmtTO := flags.Timeout
			if stmtTO <= 0 {
				stmtTO = 120 * time.Second
			}
			app.DB = db.New(prof, stmtTO)
			return nil
		},
		PersistentPostRun: func(cmd *cobra.Command, args []string) {
			if app.DB != nil {
				app.DB.Close()
			}
		},
	}

	pf := root.PersistentFlags()
	pf.StringVar(&flags.Profile, "profile", "", "connection profile (reserved; env/.env drives config today)")
	pf.StringVarP(&flags.Book, "book", "b", "", "pin a book: old | new | bsu | jivo | all (default: routed by --from/--to)")
	pf.StringVarP(&flags.Database, "db", "d", "", "raw database name — escape hatch, skips book routing")
	pf.BoolVar(&flags.JSON, "json", false, "output JSON")
	pf.BoolVar(&flags.CSV, "csv", false, "output CSV")
	pf.BoolVar(&flags.Compact, "compact", false, "compact single-line JSON")
	pf.BoolVarP(&flags.Quiet, "quiet", "q", false, "suppress row-count footer and notices")
	pf.IntVarP(&flags.Limit, "limit", "n", 0, "max rows per book (0 = command default)")
	pf.DurationVar(&flags.Timeout, "timeout", 120*time.Second, "per-query timeout")
	pf.StringVar(&flags.Select, "select", "", "comma-separated columns to keep in output")

	for _, f := range registry {
		root.AddCommand(f(app))
	}

	if err := root.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		var coder interface{ ExitCode() int }
		if errors.As(err, &coder) {
			return coder.ExitCode()
		}
		return ExitError
	}
	return ExitOK
}
