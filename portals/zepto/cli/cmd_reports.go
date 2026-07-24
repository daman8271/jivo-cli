package main

import (
	"encoding/json"
	"fmt"

	"github.com/spf13/cobra"
)

func init() { registerSection(newReportsCmd) }

// newReportsCmd — the vendor report queue (Sales_F, Vendor Inventory_F, Fill
// Rate, OTIF, OOS Visibility, DEQ Inventory, ODR, Catalogue). `list` and
// `download` are pure reads (poll + fetch an ALREADY-generated report). `request`
// GENERATES a new report (a side-effect: creates a queue row) and is therefore
// gated behind --export. Source: ../vault/vendor/Vendor-Reports-Queue.md.
func newReportsCmd(app *App) *cobra.Command {
	H := hostFCC
	r := &cobra.Command{Use: "reports", Short: "Vendor report queue — list, download (read); request (gated export)"}

	// reports list --offset --limit  (pure read)
	var offset, limit int
	list := &cobra.Command{
		Use:   "list",
		Short: "List the report queue newest-first (reportId, reportType, reportStatus)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			path := fmt.Sprintf("/api/v1/reports?offset=%d&limit=%d", offset, limit)
			return app.get("reports list", H, path)
		},
	}
	list.Flags().IntVar(&offset, "offset", 0, "pagination offset")
	list.Flags().IntVar(&limit, "limit", 20, "page size")

	// reports download <reportId> [--out file]  (pure read: mints presigned URL,
	// and if --out is given, fetches the file from S3 with no auth headers)
	var out string
	dl := &cobra.Command{
		Use:   "download <reportId>",
		Short: "Get the presigned S3 URL for a completed report (and optionally fetch it)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			path := fmt.Sprintf("/api/v1/reports/%s/download", args[0])
			raw, err := app.Client.doRaw("GET", joinURL(H, path), nil)
			if err != nil {
				return app.emitError("reports download", path, err)
			}
			if out == "" {
				return app.emit("reports download", joinURL(H, path), raw, nil)
			}
			url := extractPresigned(raw)
			if url == "" {
				return app.emitError("reports download", path, fmt.Errorf("no presignedS3Url in response: %.200s", raw))
			}
			n, err := app.Client.downloadURL(url, out)
			if err != nil {
				return app.emitError("reports download", path, err)
			}
			return app.emitValue("reports download", joinURL(H, path), map[string]any{"out": out, "bytes": n}, 1)
		},
	}
	dl.Flags().StringVar(&out, "out", "", "fetch the file to this path (else just print the presigned URL)")

	// reports request --type X [--from --to] --export   (SIDE-EFFECT: generates)
	var rType, from, to string
	var export, yesExport bool
	req := &cobra.Command{
		Use:   "request",
		Short: "GENERATE a report (side-effect — creates a queue row; requires --export)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if rType == "" {
				return fmt.Errorf("--type is required (e.g. SALES, INVENTORY, Fill Rate, OTIF, OOS Visibility, DEQ Inventory, ODR, Catalogue)")
			}
			if !export {
				return fmt.Errorf("`reports request` GENERATES a report (a write-side effect). Re-run with --export to confirm; prefer `reports list`/`download` for pure reads")
			}
			if app.Agent && !yesExport {
				return fmt.Errorf("agent mode: also pass --yes-export to confirm the side-effect")
			}
			f, t, err := resolveRange(from, to)
			if err != nil {
				return err
			}
			var payload string
			switch rType {
			case "INVENTORY", "Vendor Inventory_F":
				payload = `{"startDate":null,"endDate":null}`
			default:
				payload = fmt.Sprintf(`{"startDate":%q,"endDate":%q}`, f+"T00:00:00.000Z", t+"T00:00:00.000Z")
			}
			body := []byte(fmt.Sprintf(`{"reportType":%q,"reportPayload":%s}`, rType, payload))
			return app.post("reports request", H, "/api/v1/reports/request", body)
		},
	}
	req.Flags().StringVar(&rType, "type", "", "report type (SALES, INVENTORY, Fill Rate, OTIF, OOS Visibility, DEQ Inventory, ODR, Catalogue)")
	req.Flags().StringVar(&from, "from", "", "window start YYYY-MM-DD (default: 1st of this IST month)")
	req.Flags().StringVar(&to, "to", "", "window end YYYY-MM-DD (default: yesterday)")
	req.Flags().BoolVar(&export, "export", false, "confirm the report-generation side-effect")
	req.Flags().BoolVar(&yesExport, "yes-export", false, "agent-mode confirmation for --export")

	r.AddCommand(list, dl, req)
	return r
}

// extractPresigned pulls the presigned S3 URL out of a reports/download
// response. It decodes the JSON properly (via encoding/json) so escape
// sequences — notably Go's default HTML-escaping of "&" to "&" in query
// strings — are unescaped correctly; a hand-rolled scanner would hand back a
// malformed URL. The shape is unverified, so it probes both the common {data:{…}}
// envelope and a top-level object, and several key spellings.
func extractPresigned(raw []byte) string {
	keys := []string{"presignedS3Url", "presigned_s3_url", "url", "downloadUrl"}
	// try top-level object first, then unwrap a "data" object once.
	for _, obj := range unwrapObjects(raw) {
		for _, k := range keys {
			if v, ok := obj[k]; ok {
				var s string
				if json.Unmarshal(v, &s) == nil && s != "" {
					return s
				}
			}
		}
	}
	return ""
}

// unwrapObjects returns the top-level object and, if it has a "data" object,
// that nested object too — so extractPresigned can look one level down.
func unwrapObjects(raw []byte) []map[string]json.RawMessage {
	var out []map[string]json.RawMessage
	var top map[string]json.RawMessage
	if json.Unmarshal(raw, &top) != nil {
		return out
	}
	out = append(out, top)
	if d, ok := top["data"]; ok {
		var inner map[string]json.RawMessage
		if json.Unmarshal(d, &inner) == nil {
			out = append(out, inner)
		}
	}
	return out
}
