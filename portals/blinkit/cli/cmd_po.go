package main

import (
	"encoding/json"
	"fmt"
	"net/url"

	"github.com/spf13/cobra"
)

func newPOCmd(app *App) *cobra.Command {
	po := &cobra.Command{
		Use:   "po",
		Short: "Purchase orders Blinkit raises to JIVO",
	}
	po.AddCommand(
		newPOListCmd(app),
		newPOGetCmd(app),
		newPOItemsCmd(app),
		newPOSimpleGet(app, "grn", "GRN details for a PO", "/v1/get-grn-details/"),
		newPOSimpleGet(app, "invoices", "Invoices tied to a PO", "/v1/partner_po_invoices/"),
		newPOSimpleGet(app, "delivered", "Delivered-item count per PO", "/v1/get-item-delivered-count/"),
		newPOCountCmd(app, "count", "Aggregated PO count for current filters", "/v1/get-po-count/"),
		newPOCountCmd(app, "amount", "Aggregated total PO amount for current filters", "/v1/get-po-amount/"),
		newPOFacetCmd(app, "facets-cities", "City filter dropdown values", "/v1/client-po-details/distinct_values/city_name/"),
		newPOFacetCmd(app, "facets-facilities", "Facility filter dropdown values", "/v1/client-po-details/distinct_values/facility_name/"),
		newPOAmendmentCmd(app, "amendments", "List existing PO amendments (read only)", "/v1/po-amendment/list/"),
		newPOAmendmentCmd(app, "amendment-items", "Items available for amendment (read only)", "/v1/po-amendment/items/"),
		newPOPodCmd(app),
		newPOPdfCmd(app),
	)
	return po
}

// poFilters gathers the shared filter flags used by list/count/amount.
type poFilters struct {
	status   string
	facility string
	city     string
	vendor   string
	poNumber string
	orderBy  string
	limit    int
	offset   int
	body     string
}

func (f *poFilters) attach(c *cobra.Command, withPaging bool) {
	c.Flags().StringVar(&f.status, "status", "", "PO status filter")
	c.Flags().StringVar(&f.facility, "facility", "", "facility_name filter")
	c.Flags().StringVar(&f.city, "city", "", "city_name filter")
	c.Flags().StringVar(&f.vendor, "vendor", "", "vendor filter")
	c.Flags().StringVar(&f.poNumber, "po-number", "", "po_number filter")
	c.Flags().StringVar(&f.body, "body", "", "raw JSON request body (overrides all filter flags)")
	if withPaging {
		c.Flags().StringVar(&f.orderBy, "order-by", "-expiry_date", "order_by field")
		c.Flags().IntVar(&f.limit, "limit", 30, "page size")
		c.Flags().IntVar(&f.offset, "offset", 0, "pagination offset")
	}
}

// bodyJSON builds the {order_by, filters} POST body from the filter flags.
func (f *poFilters) bodyJSON() []byte {
	if f.body != "" {
		return []byte(f.body)
	}
	filters := map[string]any{}
	if f.status != "" {
		filters["status"] = f.status
	}
	if f.facility != "" {
		filters["facility_name"] = f.facility
	}
	if f.city != "" {
		filters["city_name"] = f.city
	}
	if f.vendor != "" {
		filters["vendor"] = f.vendor
	}
	if f.poNumber != "" {
		filters["po_number"] = f.poNumber
	}
	payload := map[string]any{"filters": filters}
	if f.orderBy != "" {
		// PartnersBiz requires order_by as a JSON array, not a scalar string
		// (a string is rejected char-by-char: "Invalid order_by arguments: ['-']").
		payload["order_by"] = []string{f.orderBy}
	}
	b, _ := json.Marshal(payload)
	return b
}

func newPOListCmd(app *App) *cobra.Command {
	f := &poFilters{}
	c := &cobra.Command{
		Use:   "list",
		Short: "PO list grid (fetchPO)",
		RunE: func(cmd *cobra.Command, args []string) error {
			path := fmt.Sprintf("/v1/client-po-details/?offset=%d&limit=%d", f.offset, f.limit)
			return app.postJSON("po list", path, f.bodyJSON())
		},
	}
	f.attach(c, true)
	return c
}

func newPOCountCmd(app *App, use, short, path string) *cobra.Command {
	f := &poFilters{}
	c := &cobra.Command{
		Use:   use,
		Short: short + " [method to confirm: POST-with-filters]",
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.postJSON("po "+use, path, f.bodyJSON())
		},
	}
	f.attach(c, false)
	return c
}

func newPOGetCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "get <po_number>",
		Short: "Single PO detail",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			path := "/v1/get-po-details/?po_number=" + url.QueryEscape(args[0])
			return app.getJSON("po get", path)
		},
	}
}

func newPOItemsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "items <po_id>",
		Short: "Line items in a PO",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			path := fmt.Sprintf("/v1/client-po-items/%s/?paginate=false", url.PathEscape(args[0]))
			return app.postJSON("po items", path, nil)
		},
	}
}

// newPOSimpleGet is a GET keyed by an optional --po-number query param.
func newPOSimpleGet(app *App, use, short, path string) *cobra.Command {
	var poNumber string
	c := &cobra.Command{
		Use:   use,
		Short: short,
		RunE: func(cmd *cobra.Command, args []string) error {
			p := path
			if poNumber != "" {
				p += "?po_number=" + url.QueryEscape(poNumber)
			}
			return app.getJSON("po "+use, p)
		},
	}
	c.Flags().StringVar(&poNumber, "po-number", "", "po_number to look up")
	return c
}

func newPOFacetCmd(app *App, use, short, path string) *cobra.Command {
	return &cobra.Command{
		Use:   use,
		Short: short,
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.getJSON("po "+use, path)
		},
	}
}

func newPOAmendmentCmd(app *App, use, short, path string) *cobra.Command {
	var body string
	c := &cobra.Command{
		Use:   use,
		Short: short,
		RunE: func(cmd *cobra.Command, args []string) error {
			var b []byte
			if body != "" {
				b = []byte(body)
			}
			return app.postJSON("po "+use, path, b)
		},
	}
	c.Flags().StringVar(&body, "body", "", "raw JSON request body")
	return c
}

func newPOPodCmd(app *App) *cobra.Command {
	var poNumbers, out string
	c := &cobra.Command{
		Use:   "pod",
		Short: "Download POD PDF(s) for PO number(s)",
		RunE: func(cmd *cobra.Command, args []string) error {
			if poNumbers == "" {
				return fmt.Errorf("--po-numbers is required (comma-separated)")
			}
			if out == "" {
				out = "blinkit-pod.pdf"
			}
			path := "/v1/download-pod-pdf/?po_numbers=" + url.QueryEscape(poNumbers)
			return runFileDownload(app, "po pod", "GET", path, nil, out)
		},
	}
	c.Flags().StringVar(&poNumbers, "po-numbers", "", "comma-separated PO numbers")
	c.Flags().StringVar(&out, "out", "", "output PDF path")
	return c
}

func newPOPdfCmd(app *App) *cobra.Command {
	var poNumbers, out string
	c := &cobra.Command{
		Use:   "pdf",
		Short: "Download the bulk PO PDF zip",
		RunE: func(cmd *cobra.Command, args []string) error {
			if out == "" {
				out = "blinkit-po-pdfs.zip"
			}
			path := "/v1/get-po-pdf-zip/"
			if poNumbers != "" {
				path += "?po_numbers=" + url.QueryEscape(poNumbers)
			}
			return runFileDownload(app, "po pdf", "GET", path, nil, out)
		},
	}
	c.Flags().StringVar(&poNumbers, "po-numbers", "", "comma-separated PO numbers")
	c.Flags().StringVar(&out, "out", "", "output zip path")
	return c
}

// runFileDownload is the shared authenticated binary-download helper.
func runFileDownload(app *App, command, method, path string, body []byte, out string) error {
	n, err := app.Client.download(method, app.cfg.Base+path, body, out)
	if err != nil {
		return app.emitError(command, path, err)
	}
	if app.JSON || app.Agent {
		return app.emitValue(command, path, map[string]any{"out": out, "bytes": n}, 1)
	}
	fmt.Printf("✓ saved %s (%d bytes)\n", out, n)
	return nil
}
