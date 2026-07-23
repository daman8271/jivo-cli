package main

import (
	"encoding/json"
	"net/url"

	"github.com/spf13/cobra"
)

const apptBase = "/vendor_appointment/api"

func newAppointmentsCmd(app *App) *cobra.Command {
	appt := &cobra.Command{
		Use:   "appointments",
		Short: "PO delivery scheduling — read-only (no booking/cancel)",
	}
	appt.AddCommand(
		newPOFacetCmd(app, "stats", "Pending/Upcoming/Fulfilled stat cards", apptBase+"/v1/appointment-stats/"),
		newApptListCmd(app),
		newApptCancelInfoCmd(app),
		newPOFacetCmd(app, "couriers", "Courier dropdown options", apptBase+"/v1/courier-partner-details/"),
		newApptPostByPO(app, "invoices", "Invoices for PO(s)", apptBase+"/v1/invoice/fetch-invoice/"),
		newApptPostByPO(app, "slots", "Available delivery slots for PO(s) — inspect only", apptBase+"/v2/slots/available/"),
		newApptPostByPO(app, "existing", "Existing appointments for club/merge", apptBase+"/v2/appointment/get-existing-appointments/"),
		newApptClubbingChargesCmd(app),
	)
	return appt
}

func newApptListCmd(app *App) *cobra.Command {
	var tab, facility, po, from, to, body string
	c := &cobra.Command{
		Use:   "list",
		Short: "Appointments list grid",
		RunE: func(cmd *cobra.Command, args []string) error {
			f := map[string]any{}
			if tab != "" {
				f["tab"] = tab
			}
			if facility != "" {
				f["facility"] = facility
			}
			if po != "" {
				f["po_number"] = po
			}
			if from != "" {
				f["issue_date__date__gte"] = from
			}
			if to != "" {
				f["issue_date__date__lte"] = to
			}
			return app.postJSON("appointments list", apptBase+"/v1/appointments/", filtersBody(body, f))
		},
	}
	c.Flags().StringVar(&tab, "tab", "", "all|today|upcoming")
	c.Flags().StringVar(&facility, "facility", "", "facility filter")
	c.Flags().StringVar(&po, "po", "", "po_number filter")
	c.Flags().StringVar(&from, "from", "", "issue_date__date__gte")
	c.Flags().StringVar(&to, "to", "", "issue_date__date__lte")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body")
	return c
}

func newApptCancelInfoCmd(app *App) *cobra.Command {
	var po string
	c := &cobra.Command{
		Use:   "cancel-info",
		Short: "Read cancellability/count for a PO (does NOT cancel)",
		RunE: func(cmd *cobra.Command, args []string) error {
			path := apptBase + "/v1/appointments/fetch-cancel/"
			if po != "" {
				path += "?po_number=" + url.QueryEscape(po)
			}
			return app.getJSON("appointments cancel-info", path)
		},
	}
	c.Flags().StringVar(&po, "po", "", "po_number")
	return c
}

// newApptPostByPO is a POST-to-read keyed by a --po filter body.
func newApptPostByPO(app *App, use, short, path string) *cobra.Command {
	var po, body string
	c := &cobra.Command{
		Use:   use,
		Short: short,
		RunE: func(cmd *cobra.Command, args []string) error {
			var b []byte
			if body != "" {
				b = []byte(body)
			} else if po != "" {
				b, _ = json.Marshal(map[string]any{"po_numbers": []string{po}})
			} else {
				b = []byte(`{}`)
			}
			return app.postJSON("appointments "+use, path, b)
		},
	}
	c.Flags().StringVar(&po, "po", "", "po_number")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body")
	return c
}

func newApptClubbingChargesCmd(app *App) *cobra.Command {
	var po, into string
	c := &cobra.Command{
		Use:   "clubbing-charges",
		Short: "Preview PO-clubbing/merge charges (read only)",
		RunE: func(cmd *cobra.Command, args []string) error {
			q := url.Values{}
			if po != "" {
				q.Set("po_number", po)
			}
			if into != "" {
				q.Set("into", into)
			}
			path := apptBase + "/v2/appointment/clubbing-charges/"
			if len(q) > 0 {
				path += "?" + q.Encode()
			}
			return app.getJSON("appointments clubbing-charges", path)
		},
	}
	c.Flags().StringVar(&po, "po", "", "po_number")
	c.Flags().StringVar(&into, "into", "", "target appointment/PO to merge into")
	return c
}
