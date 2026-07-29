package cli

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/spf13/cobra"

	"dsr/internal/config"
)

func init() { register(newDoctorCmd) }

// doctorReport is the structured self-check result for both access paths.
type doctorReport struct {
	// SQL Server (primary path)
	Reachable     bool   `json:"reachable"`
	ServerVersion string `json:"server_version,omitempty"`
	Database      string `json:"database,omitempty"`
	Login         string `json:"login,omitempty"`
	Sysadmin      bool   `json:"sysadmin"`
	DBOwner       bool   `json:"db_owner"`
	Tables        int    `json:"tables,omitempty"`
	Databases     int    `json:"databases,omitempty"`

	// Portal (secondary path)
	PortalURL       string `json:"portal_url,omitempty"`
	PortalReachable bool   `json:"portal_reachable"`
	PortalStatus    string `json:"portal_status,omitempty"`

	Warnings []string `json:"warnings,omitempty"`
	Config   string   `json:"config_path"`
	Error    string   `json:"error,omitempty"`
}

func newDoctorCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "doctor",
		Short: "Health/self-check: DB reachability, version, privileges, table count, and portal reachability",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			rep := doctorReport{Config: config.Path(), PortalURL: app.Prof.PortalURL}

			ctx, cancel := app.Ctx()
			defer cancel()

			res, err := app.DB.Query(ctx, app.DBName(), `
				SELECT @@VERSION AS server_version,
				       DB_NAME() AS db,
				       SUSER_SNAME() AS login,
				       CAST(IS_SRVROLEMEMBER('sysadmin') AS int) AS is_sysadmin,
				       CAST(ISNULL(IS_MEMBER('db_owner'), 0) AS int) AS is_db_owner,
				       (SELECT COUNT(*) FROM sys.tables) AS ntables,
				       (SELECT COUNT(*) FROM sys.databases WHERE database_id > 4) AS ndb`)
			if err != nil {
				rep.Error = err.Error()
				// Still probe the portal so doctor reports both paths even if DB is down.
				checkPortal(&rep, app.Prof)
				printDoctor(app, rep)
				return err
			}

			rep.Reachable = true
			if len(res.Rows) > 0 {
				row := res.Rows[0]
				rep.ServerVersion = firstLine(doctorStr(row, res.Columns, "server_version"))
				rep.Database = doctorStr(row, res.Columns, "db")
				rep.Login = doctorStr(row, res.Columns, "login")
				rep.Sysadmin = doctorInt(row, res.Columns, "is_sysadmin") == 1
				rep.DBOwner = doctorInt(row, res.Columns, "is_db_owner") == 1
				rep.Tables = doctorInt(row, res.Columns, "ntables")
				rep.Databases = doctorInt(row, res.Columns, "ndb")
			}

			// RULE 0 honesty: our SELECT-only guard + rolled-back transaction block
			// writes at the app layer, but the login itself is over-privileged.
			if rep.Sysadmin {
				rep.Warnings = append(rep.Warnings,
					"connected login is a SYSADMIN: it CAN write/DDL server-wide. dsr's read-only guard is the "+
						"only thing preventing writes — prefer a dedicated read-only login for this tool.")
			} else if rep.DBOwner {
				rep.Warnings = append(rep.Warnings,
					"connected login is db_owner on this database: it can write here. dsr's read-only guard is the "+
						"only thing preventing writes.")
			}

			checkPortal(&rep, app.Prof)
			return printDoctor(app, rep)
		},
	}
}

// checkPortal does a best-effort GET of the portal login page.
func checkPortal(rep *doctorReport, prof config.Profile) {
	if prof.PortalURL == "" {
		return
	}
	client := &http.Client{Timeout: 8 * time.Second}
	req, err := http.NewRequest(http.MethodGet, prof.PortalURL+"/Login/Login", nil)
	if err != nil {
		rep.PortalStatus = err.Error()
		return
	}
	resp, err := client.Do(req)
	if err != nil {
		rep.PortalStatus = err.Error()
		return
	}
	defer resp.Body.Close()
	rep.PortalReachable = resp.StatusCode < 500
	rep.PortalStatus = resp.Status
}

func printDoctor(app *App, rep doctorReport) error {
	if app.Flags.JSON || app.Flags.Compact {
		enc := json.NewEncoder(os.Stdout)
		enc.SetEscapeHTML(false)
		if !app.Flags.Compact {
			enc.SetIndent("", "  ")
		}
		return enc.Encode(rep)
	}
	return doctorPrintHuman(os.Stdout, rep)
}

func doctorPrintHuman(w *os.File, r doctorReport) error {
	fmt.Fprintln(w, "dsr doctor")
	fmt.Fprintln(w, "==========")
	fmt.Fprintf(w, "DB reachable:  %s\n", doctorYesNo(r.Reachable))
	fmt.Fprintf(w, "Server:        %s\n", doctorDash(r.ServerVersion))
	fmt.Fprintf(w, "Database:      %s\n", doctorDash(r.Database))
	fmt.Fprintf(w, "Login:         %s\n", doctorDash(r.Login))
	fmt.Fprintf(w, "Sysadmin:      %s\n", doctorYesNo(r.Sysadmin))
	fmt.Fprintf(w, "db_owner:      %s\n", doctorYesNo(r.DBOwner))
	fmt.Fprintf(w, "Tables:        %d\n", r.Tables)
	fmt.Fprintf(w, "Databases:     %d (user)\n", r.Databases)
	fmt.Fprintf(w, "Portal:        %s  (%s %s)\n", doctorYesNo(r.PortalReachable), doctorDash(r.PortalURL), doctorDash(r.PortalStatus))
	fmt.Fprintf(w, "Config:        %s\n", r.Config)
	if r.Error != "" {
		fmt.Fprintf(w, "Error:         %s\n", r.Error)
	}
	for _, wn := range r.Warnings {
		fmt.Fprintf(w, "\nWARNING: %s\n", wn)
	}

	healthy := r.Reachable
	switch {
	case !healthy:
		fmt.Fprintln(w, "\nStatus: UNHEALTHY")
	case r.Sysadmin || r.DBOwner:
		fmt.Fprintln(w, "\nStatus: healthy, but login is OVER-PRIVILEGED (see warnings)")
	default:
		fmt.Fprintln(w, "\nStatus: healthy")
	}
	return nil
}

func firstLine(s string) string {
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' || s[i] == '\r' {
			return s[:i]
		}
	}
	return s
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
