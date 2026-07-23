package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
)

func newDoctorCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "doctor",
		Short: "Verify config + token + one live read (report count + granted tabs)",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runDoctor(app)
		},
	}
}

func runDoctor(app *App) error {
	// 1) config source + resolved values.
	tokenSrc := "config-file"
	if os.Getenv("BLINKIT_TOKEN") != "" {
		tokenSrc = "env"
	}
	tokShape := "MISSING"
	if t := app.cfg.Token; t != "" {
		ok := strings.HasPrefix(t, "v2::")
		if ok {
			tokShape = "present (v2::…)"
		} else {
			tokShape = "present (UNEXPECTED SHAPE)"
		}
	}

	// 2) one live read: report queue.
	reports, rErr := app.Client.ListReports()
	// 3) entity tabs.
	tabsRaw, tErr := app.Client.doRaw("GET", app.cfg.Base+"/v1/get-entity-tabs/", nil)

	if app.Agent {
		out := map[string]any{
			"ok":           rErr == nil,
			"command":      "doctor",
			"base":         app.cfg.Base,
			"entity_id":    app.cfg.EntityID,
			"entity_type":  app.cfg.EntityType,
			"token_source": tokenSrc,
			"token_shape":  tokShape,
			"config_path":  configPath(),
		}
		if rErr == nil {
			out["reports_visible"] = len(reports)
			if len(reports) > 0 {
				out["latest_report"] = reports[0]
			}
		} else {
			out["error"] = errWithRelogin(rErr)
		}
		if tErr == nil {
			out["entity_tabs"] = json.RawMessage(tabsRaw)
		} else {
			out["tabs_error"] = errWithRelogin(tErr)
		}
		b, _ := json.MarshalIndent(out, "", "  ")
		fmt.Println(string(b))
		if rErr != nil {
			return errors.New("doctor: live read failed")
		}
		return nil
	}

	fmt.Printf("config      : %s\n", configPath())
	fmt.Printf("base        : %s\n", app.cfg.Base)
	fmt.Printf("entity      : %s (%s)  [company=%s]\n", app.cfg.EntityID, app.cfg.EntityType, app.Company)
	fmt.Printf("api_key     : %s\n", masked(app.cfg.APIKey))
	fmt.Printf("token       : %s  [source=%s]\n", tokShape, tokenSrc)

	if rErr != nil {
		fmt.Printf("live read   : FAILED — %s\n", errWithRelogin(rErr))
		return errors.New("doctor: live read failed")
	}
	fmt.Printf("live read   : OK — %d reports visible\n", len(reports))
	if len(reports) > 0 {
		r := reports[0]
		fmt.Printf("latest      : #%d %q state=%s at %s\n", r.ID, r.Type, r.State, r.CreatedAt)
	}
	if tErr != nil {
		fmt.Printf("entity-tabs : WARN — %s\n", errWithRelogin(tErr))
	} else {
		fmt.Printf("entity-tabs : OK — %s\n", compact(tabsRaw))
	}
	return nil
}

func errWithRelogin(err error) string {
	if errors.Is(err, errUnauthorized) {
		return err.Error() + " | " + reLoginMsg
	}
	return err.Error()
}

func masked(s string) string {
	if s == "" {
		return "MISSING"
	}
	if len(s) <= 8 {
		return "present"
	}
	return s[:4] + "…" + s[len(s)-4:]
}

func compact(raw json.RawMessage) string {
	s := string(raw)
	if len(s) > 400 {
		return s[:400] + "…"
	}
	return s
}
