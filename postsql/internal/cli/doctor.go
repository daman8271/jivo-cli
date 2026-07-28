package cli

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"postsql/internal/config"
)

func init() { register(newDoctorCmd) }

// doctorReport is the structured self-check result.
type doctorReport struct {
	Reachable     bool     `json:"reachable"`
	ServerVersion string   `json:"server_version,omitempty"`
	Database      string   `json:"database,omitempty"`
	User          string   `json:"user,omitempty"`
	ReadOnly      bool     `json:"read_only"`
	DefaultTxRO   string   `json:"default_transaction_read_only,omitempty"`
	TxRO          string   `json:"transaction_read_only,omitempty"`
	Superuser     bool     `json:"superuser"`
	BypassRLS     bool     `json:"bypass_rls"`
	Databases     int      `json:"non_template_databases,omitempty"`
	Warnings      []string `json:"warnings,omitempty"`
	ConfigPath    string   `json:"config_path"`
	Error         string   `json:"error,omitempty"`
}

func newDoctorCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "doctor",
		Short: "Health/self-check: reachability, version, read-only status, database count",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			rep := doctorReport{ConfigPath: config.Path()}

			ctx, cancel := app.Ctx()
			defer cancel()

			res, err := app.DB.Query(ctx, app.DBName(), `
				SELECT version() AS server_version,
				       current_database() AS db,
				       current_user AS usr,
				       current_setting('default_transaction_read_only') AS default_ro,
				       current_setting('transaction_read_only') AS tx_ro,
				       (SELECT rolsuper FROM pg_roles WHERE rolname = current_user) AS is_super,
				       (SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user) AS bypass_rls,
				       (SELECT count(*) FROM pg_database WHERE NOT datistemplate) AS ndb`)
			if err != nil {
				// Unreachable / connection error: surface it (carries exit code 3).
				return err
			}

			rep.Reachable = true
			if len(res.Rows) > 0 {
				row := res.Rows[0]
				rep.ServerVersion = doctorStr(row, res.Columns, "server_version")
				rep.Database = doctorStr(row, res.Columns, "db")
				rep.User = doctorStr(row, res.Columns, "usr")
				rep.DefaultTxRO = doctorStr(row, res.Columns, "default_ro")
				rep.TxRO = doctorStr(row, res.Columns, "tx_ro")
				rep.ReadOnly = rep.DefaultTxRO == "on" && rep.TxRO == "on"
				rep.Superuser = doctorBool(row, res.Columns, "is_super")
				rep.BypassRLS = doctorBool(row, res.Columns, "bypass_rls")
				rep.Databases = doctorInt(row, res.Columns, "ndb")
			}

			// Loud, honest warnings: the READ ONLY transaction blocks writes but
			// cannot constrain a superuser's reads.
			if rep.Superuser {
				rep.Warnings = append(rep.Warnings,
					"connected as a SUPERUSER: read blast radius is unrestricted (server-side file reads, "+
						"all databases, RLS bypass) — the READ ONLY transaction cannot limit this. "+
						"Use a dedicated NOSUPERUSER, SELECT-only role.")
			}
			if rep.BypassRLS {
				rep.Warnings = append(rep.Warnings,
					"role can BYPASS row-level security: any RLS policy protecting sensitive rows is silently ignored.")
			}

			if app.Flags.JSON || app.Flags.Compact {
				enc := json.NewEncoder(os.Stdout)
				enc.SetEscapeHTML(false)
				if !app.Flags.Compact {
					enc.SetIndent("", "  ")
				}
				return enc.Encode(rep)
			}

			return doctorPrintHuman(os.Stdout, rep)
		},
	}
}

func doctorPrintHuman(w *os.File, r doctorReport) error {
	fmt.Fprintln(w, "postsql doctor")
	fmt.Fprintln(w, "==============")
	fmt.Fprintf(w, "Reachable:     %s\n", doctorYesNo(r.Reachable))
	fmt.Fprintf(w, "Server:        %s\n", doctorDash(r.ServerVersion))
	fmt.Fprintf(w, "Database:      %s\n", doctorDash(r.Database))
	fmt.Fprintf(w, "User:          %s\n", doctorDash(r.User))
	fmt.Fprintf(w, "Read-only:     %s (default_transaction_read_only=%s, transaction_read_only=%s)\n",
		doctorYesNo(r.ReadOnly), doctorDash(r.DefaultTxRO), doctorDash(r.TxRO))
	fmt.Fprintf(w, "Superuser:     %s\n", doctorYesNo(r.Superuser))
	fmt.Fprintf(w, "Bypass RLS:    %s\n", doctorYesNo(r.BypassRLS))
	fmt.Fprintf(w, "Databases:     %d non-template\n", r.Databases)
	fmt.Fprintf(w, "Config:        %s\n", r.ConfigPath)

	for _, wn := range r.Warnings {
		fmt.Fprintf(w, "\nWARNING: %s\n", wn)
	}

	// A superuser / RLS-bypassing connection is not a "safe to point at prod"
	// posture even when read-only, so it degrades the overall verdict.
	healthy := r.Reachable && r.ReadOnly
	switch {
	case !healthy:
		fmt.Fprintln(w, "\nStatus: UNHEALTHY")
	case r.Superuser || r.BypassRLS:
		fmt.Fprintln(w, "\nStatus: healthy, but OVER-PRIVILEGED (see warnings)")
	default:
		fmt.Fprintln(w, "\nStatus: healthy")
	}
	return nil
}

func doctorYesNo(b bool) string {
	if b {
		return "yes"
	}
	return "no"
}

func doctorDash(s string) string {
	if s == "" {
		return "-"
	}
	return s
}

func doctorStr(row []any, cols []string, name string) string {
	i := doctorColIdx(cols, name)
	if i < 0 || i >= len(row) || row[i] == nil {
		return ""
	}
	switch v := row[i].(type) {
	case string:
		return v
	case []byte:
		return string(v)
	default:
		return fmt.Sprintf("%v", v)
	}
}

func doctorBool(row []any, cols []string, name string) bool {
	i := doctorColIdx(cols, name)
	if i < 0 || i >= len(row) || row[i] == nil {
		return false
	}
	switch v := row[i].(type) {
	case bool:
		return v
	case string:
		return v == "true" || v == "t" || v == "TRUE" || v == "T"
	case []byte:
		s := string(v)
		return s == "true" || s == "t" || s == "TRUE" || s == "T"
	default:
		return false
	}
}

func doctorInt(row []any, cols []string, name string) int {
	i := doctorColIdx(cols, name)
	if i < 0 || i >= len(row) || row[i] == nil {
		return 0
	}
	switch v := row[i].(type) {
	case int64:
		return int(v)
	case int:
		return v
	default:
		var n int
		fmt.Sscanf(fmt.Sprintf("%v", v), "%d", &n)
		return n
	}
}

func doctorColIdx(cols []string, name string) int {
	for i, c := range cols {
		if c == name {
			return i
		}
	}
	return -1
}
