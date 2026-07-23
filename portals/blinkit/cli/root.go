package main

import (
	"fmt"
	"net/http"

	"github.com/spf13/cobra"
)

// company maps a friendly name to the entity headers + manufacturer_id.
// Only jivo/1117 is known today; an unknown value is a clear error.
var company = map[string]struct {
	EntityID   string
	EntityType string
	ManufID    string
}{
	"jivo": {EntityID: "1117", EntityType: "manufacturer", ManufID: "176"},
}

func newRootCmd() *cobra.Command {
	app := &App{}

	root := &cobra.Command{
		Use:   "blinkit-partner",
		Short: "Read-only CLI for the Blinkit PartnersBiz (Partner) portal",
		Long: `blinkit-partner — read-only access to the Blinkit PartnersBiz partner portal.

Every command is a READ (GET, POST-to-read, or poll+download of an
already-generated report). No create/update/delete/upload/approve is wired.
Auth is inherited from the existing blinkit-cli config or BLINKIT_* env vars.`,
		SilenceUsage:  true,
		SilenceErrors: true,
		// PersistentPreRunE resolves auth once for every command that needs it.
		// auth import overrides this with its own no-op pre-run.
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			if app.Agent {
				app.JSON = true
			}
			c, ok := company[app.Company]
			if !ok {
				return fmt.Errorf("unknown --company %q (known: jivo)", app.Company)
			}
			cfg, err := resolveConfig()
			if err != nil {
				return err
			}
			// --company selects the entity headers.
			cfg.EntityID = c.EntityID
			cfg.EntityType = c.EntityType
			app.cfg = cfg
			app.ManufID = c.ManufID
			app.Client = newClient(cfg)
			return nil
		},
	}

	root.PersistentFlags().BoolVar(&app.JSON, "json", false, "machine-readable JSON output")
	root.PersistentFlags().BoolVar(&app.Agent, "agent", false, "agent mode: JSON + stable {ok,command,endpoint,count,data|error} envelope, quiet stderr")
	root.PersistentFlags().StringVar(&app.Company, "company", "jivo", "entity selector (known: jivo)")

	root.AddCommand(
		newDoctorCmd(app),
		newAuthCmd(app),
		newReportsCmd(app),
		newSalesCmd(app),
		newSOHCmd(app),
		newPOCmd(app),
		newInvoicesCmd(app),
		newPaymentsCmd(app),
		newOffersCmd(app),
		newAppointmentsCmd(app),
		newScorecardCmd(app),
		newAssortmentCmd(app),
	)
	return root
}

// ---- shared request helpers used by the leaf commands -------------------

// getJSON does an authenticated GET and emits the raw result.
func (a *App) getJSON(command, path string) error {
	raw, err := a.Client.doRaw(http.MethodGet, a.cfg.Base+path, nil)
	return a.emit(command, path, raw, err)
}

// postJSON does an authenticated POST-to-read and emits the raw result.
func (a *App) postJSON(command, path string, body []byte) error {
	raw, err := a.Client.doRaw(http.MethodPost, a.cfg.Base+path, body)
	return a.emit(command, path, raw, err)
}

// deferred prints a uniform "path not yet confirmed" notice for endpoints whose
// exact contract needs one live capture before wiring (kept in the tree so it
// is discoverable, never invented).
func (a *App) deferred(command, note string) error {
	return a.emitError(command, note, fmt.Errorf("endpoint to confirm — capture live first: %s", note))
}
