package main

import (
	"encoding/json"
	"strconv"
	"strings"

	"github.com/spf13/cobra"
)

// returns — the filing calendar and the ARN register. This is the group Accounts
// opens first: "is everything filed, and what is the ARN".

func init() { registerSection(newReturnsCmd) }

// returnForms is the vocabulary the portal accepts for rtn_typ / rtntp. Checked
// here so a typo costs nothing: an unknown value comes back as RET11403
// ("Invalid API Request"), which looks like a bug in the CLI rather than a typo.
var returnForms = []string{
	"GSTR1", "GSTR1A", "GSTR2A", "GSTR2B", "GSTR3B", "GSTR4", "GSTR5", "GSTR5A",
	"GSTR6", "GSTR7", "GSTR8", "GSTR9", "GSTR9A", "GSTR9C", "CMP08", "ITC04",
}

// returnFreqs is the `rfp` vocabulary — the literal WORD, not an initial. "M"
// gives RET11403 (API.md §Filed-returns list).
var returnFreqs = []string{"Monthly", "Quarterly", "Annual", "Half Yearly"}

func newReturnsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "returns",
		Short: "Filing calendar, per-period status, and the filed-returns (ARN) register",
	}
	c.AddCommand(
		returnsCalendarCmd(app),
		returnsPeriodsCmd(app),
		returnsStatusCmd(app),
		returnsFiledCmd(app),
	)
	return c
}

func returnsCalendarCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "calendar",
		Short: "Last five periods of GSTR-1/IFF and GSTR-3B, filed or not",
		Long: `The filing snapshot the portal's own dashboard draws.

Note the host: this one endpoint is served by services.gst.gov.in. The identical
path on return.gst.gov.in is refused by the WAF for any non-browser client
(API.md, D3).`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			c := newClient(reg)
			res, err := c.do(epFilingSnapshot, nil, nil, nil)
			if err == nil && !res.Empty {
				if line := filingSnapshotSummary(res.Raw); line != "" {
					app.logf("%s (%s): %s", reg.GSTIN, reg.State, line)
				}
			}
			return app.emit("returns calendar", reg.GSTIN, endpointURL(epFilingSnapshot), res, err)
		},
	}
}

func returnsPeriodsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "periods",
		Short: "Financial years and their MMYYYY period codes",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			return app.read("returns periods", reg, epDropdown, nil, nil, nil)
		},
	}
}

// returnsStatusCmd covers both period-level reads. Without --form it is the tile
// grid (which forms are due, which are filed); with --form it is formdetails,
// which carries the ARN and the filing date — the single most useful field for
// reconciling against SAP.
func returnsStatusCmd(app *App) *cobra.Command {
	var period, form string
	c := &cobra.Command{
		Use:   "status",
		Short: "Per-period return status; with --form, the ARN and filing date for that form",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parsePeriod(period); err != nil {
				return err
			}
			if form == "" {
				return app.read("returns status", reg, epRoleStatus, nil, qs("rtn_prd", period), nil)
			}
			f, err := normaliseForm(form)
			if err != nil {
				return err
			}
			return app.read("returns status", reg, epFormDetails, nil, qs("rtn_prd", period, "rtn_typ", f), nil)
		},
	}
	c.Flags().StringVar(&period, "period", "", "return period, MMYYYY (e.g. 072026)")
	c.Flags().StringVar(&form, "form", "", "one form: "+strings.Join(returnForms, ", "))
	_ = c.MarkFlagRequired("period")
	return c
}

// returnsFiledCmd is the ARN register search. It is a POST because the portal
// offers no GET for it; the body keys are pinned by the allowlist and the values
// validated here, so nothing but a search can be expressed.
func returnsFiledCmd(app *App) *cobra.Command {
	var fy, form, freq string
	c := &cobra.Command{
		Use:   "filed",
		Short: "The filed-returns register for a financial year: ARN, filing date, who filed",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parseFY(fy); err != nil {
				return err
			}
			f, err := normaliseForm(form)
			if err != nil {
				return err
			}
			rfp, err := normaliseFreq(freq)
			if err != nil {
				return err
			}
			// qtr and mth are sent as explicit nulls, exactly as the portal's own
			// page does; leaving them out is untested and RET13510 is what a
			// wrong body looks like.
			body := map[string]any{"fy": fy, "rfp": rfp, "qtr": nil, "mth": nil, "rtntp": f}
			c := newClient(reg)
			res, err := c.do(epEfiledReturns, nil, nil, body)
			if err == nil && !res.Empty {
				app.logf("%s %s %s: %d filed return(s)", reg.GSTIN, f, fy, bestEffortCount(res.Raw))
			}
			return app.emit("returns filed", reg.GSTIN, endpointURL(epEfiledReturns), res, err)
		},
	}
	c.Flags().StringVar(&fy, "fy", "", "financial year, YYYY-YY (e.g. 2026-27)")
	c.Flags().StringVar(&form, "form", "GSTR1", "return type: "+strings.Join(returnForms, ", "))
	c.Flags().StringVar(&freq, "freq", "Monthly", "filing frequency: "+strings.Join(returnFreqs, " | "))
	_ = c.MarkFlagRequired("fy")
	return c
}

// normaliseForm accepts gstr1/GSTR-1/GSTR1 and returns the portal's spelling.
func normaliseForm(s string) (string, error) {
	want := strings.ToUpper(strings.NewReplacer("-", "", " ", "", "_", "").Replace(strings.TrimSpace(s)))
	for _, f := range returnForms {
		if f == want {
			return f, nil
		}
	}
	return "", errUsage("%q is not a return type the portal knows; use one of: %s", s, strings.Join(returnForms, ", "))
}

// normaliseFreq accepts any casing of the four words the portal's rfp field takes.
func normaliseFreq(s string) (string, error) {
	want := strings.Join(strings.Fields(strings.TrimSpace(s)), " ")
	for _, f := range returnFreqs {
		if strings.EqualFold(f, want) {
			return f, nil
		}
	}
	return "", errUsage("%q is not a filing frequency; use one of: %s (the literal word — \"M\" is rejected by the portal)",
		s, strings.Join(returnFreqs, ", "))
}

// filingSnapshotSummary pulls a one-line human summary out of a filingsnapshot
// body, for the stderr line. Best effort: an ISD registration answers with a
// different shape and simply gets no summary.
func filingSnapshotSummary(raw json.RawMessage) string {
	var v struct {
		Data struct {
			FormNames []struct {
				FormName string `json:"formName"`
				RetPrds  []struct {
					MonthYearName string `json:"monthYearName"`
					FilingStatus  string `json:"filingStatus"`
				} `json:"retPrds"`
			} `json:"formNames"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &v); err != nil || len(v.Data.FormNames) == 0 {
		return ""
	}
	var parts []string
	for _, f := range v.Data.FormNames {
		pending := 0
		for _, p := range f.RetPrds {
			if !strings.EqualFold(p.FilingStatus, "Filed") {
				pending++
			}
		}
		if pending > 0 {
			parts = append(parts, f.FormName+": "+strconv.Itoa(pending)+" not filed")
		}
	}
	if len(parts) == 0 {
		return "all shown periods filed"
	}
	return strings.Join(parts, "; ")
}
