// Package cli wires the postsql command tree.
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

	"postsql/internal/config"
	"postsql/internal/db"
	"postsql/internal/render"
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

// DBName returns the effective target database (--db, else profile default).
func (a *App) DBName() string {
	if a.Flags.Database != "" {
		return a.Flags.Database
	}
	return a.Prof.Database
}

// Ctx returns a context bounded by the --timeout flag.
func (a *App) Ctx() (context.Context, context.CancelFunc) {
	to := a.Flags.Timeout
	if to <= 0 {
		to = 30 * time.Second
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
		Use:           "postsql",
		Short:         "Fast, read-only, AI-native CLI for PostgreSQL",
		Long:          "postsql is a read-only PostgreSQL browser and query tool.\nEvery query runs inside a READ ONLY transaction — it can never write.",
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
			// Mirror Ctx()'s effective timeout so the server-side
			// statement_timeout backstop matches the client deadline.
			stmtTO := flags.Timeout
			if stmtTO <= 0 {
				stmtTO = 30 * time.Second
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
	pf.StringVar(&flags.Profile, "profile", "", "connection profile from ~/.postsql/config.toml")
	pf.StringVarP(&flags.Database, "db", "d", "", "target database (default: profile's database)")
	pf.BoolVar(&flags.JSON, "json", false, "output JSON")
	pf.BoolVar(&flags.CSV, "csv", false, "output CSV")
	pf.BoolVar(&flags.Compact, "compact", false, "compact single-line JSON")
	pf.BoolVarP(&flags.Quiet, "quiet", "q", false, "suppress row-count footer and notices")
	pf.IntVarP(&flags.Limit, "limit", "n", 0, "max rows for query/peek (0 = unlimited)")
	pf.DurationVar(&flags.Timeout, "timeout", 30*time.Second, "per-query timeout")
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
