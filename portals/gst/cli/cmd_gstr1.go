package main

import (
	"encoding/json"
	"strings"

	"github.com/spf13/cobra"
)

// gstr1 — outward supplies as filed. One list API serves every section; the
// query parameters pick which one (API.md §GSTR-1, captured live 2026-08-21).
//
// Two things to know before using this:
//   - There are NO paging parameters. A big section (Haryana's Jul-26 B2B is 878
//     documents) comes back in one response, and the way to make it smaller is
//     --ctin, not a page number.
//   - The portal's own web view refuses to open a section with more than 500
//     records and points at the offline utility. The API does not care. That is
//     the portal's UI limit, not a rule about the data.
func init() { registerSection(newGSTR1Cmd) }

// gstr1Sections are the sec_name values, with the uploaded_by the portal's own
// page pairs with each. "" means the page sends no uploaded_by at all.
var gstr1Sections = map[string]string{
	"B2B":   "SU",
	"B2BA":  "SU",
	"CDNR":  "SU",
	"CDNRA": "SU",
	"B2CS":  "OE",
	"B2CSA": "OE",
	"B2CL":  "OE",
	"CDNUR": "OE",
	"EXP":   "SU",
	"HSN":   "",
	"DOC":   "",
	"NIL":   "",
	"AT":    "",
	"TXPD":  "",
}

func newGSTR1Cmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "gstr1",
		Short: "GSTR-1 (outward supplies): section counts and the documents in them",
	}
	c.AddCommand(
		gstr1SummaryCmd(app),
		gstr1SectionCmd(app),
		gstr1DocsCmd(app),
	)
	return c
}

// gstr1SummaryCmd answers "what is in this month's GSTR-1, and was it filed" in
// one invocation: the filing status (ARN, date) plus the per-section counts.
func gstr1SummaryCmd(app *App) *cobra.Command {
	var period string
	c := &cobra.Command{
		Use:   "summary",
		Short: "GSTR-1 for one period: filing status (ARN, date) and per-section counts",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parsePeriod(period); err != nil {
				return err
			}
			cl := newClient(reg)
			out := map[string]any{"gstin": reg.GSTIN, "period": period, "fy": fyOfPeriod(period)}

			filing, err := cl.do(epFormDetails, nil, qs("rtn_prd", period, "rtn_typ", "GSTR1"), nil)
			if err != nil {
				return app.emitError("gstr1 summary", reg.GSTIN, endpointURL(epFormDetails), err)
			}
			if !filing.Empty {
				out["filing"] = json.RawMessage(filing.Raw)
			}

			counts, err := cl.do(epGSTR1Count, nil, qs("rtn_prd", period), nil)
			if err != nil {
				return app.emitError("gstr1 summary", reg.GSTIN, endpointURL(epGSTR1Count), err)
			}
			n := 0
			if counts.Empty {
				out["note"] = counts.Note
			} else {
				out["sections"] = json.RawMessage(counts.Raw)
				if line, docs := gstr1CountLine(counts.Raw); line != "" {
					n = docs
					app.logf("%s %s — %s", reg.GSTIN, period, line)
				}
			}
			return app.emitValue("gstr1 summary", reg.GSTIN, endpointURL(epGSTR1Count), out, n)
		},
	}
	periodFlag(c, &period)
	return c
}

// gstr1SectionCmd breaks one section's counts down per counterparty — the cheap
// way to find the ctins to then pull documents for.
func gstr1SectionCmd(app *App) *cobra.Command {
	var period, section string
	c := &cobra.Command{
		Use:   "section",
		Short: "Per-counterparty document counts within one GSTR-1 section",
		Long: `Counts for one section, broken down by counterparty GSTIN.

Known portal defect: --section B2B returns GSTN-EXEC1003, a server-side error,
consistently (three attempts on 2026-08-21). Every other section works. B2B
counterparties can be listed from GSTR-2A instead.`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parsePeriod(period); err != nil {
				return err
			}
			sec, _, err := normaliseSection(section)
			if err != nil {
				return err
			}
			return app.read("gstr1 section", reg, epGSTR1Count, nil, qs("rtn_prd", period, "sec_name", sec), nil)
		},
	}
	periodFlag(c, &period)
	c.Flags().StringVar(&section, "section", "", "section: "+sectionList())
	_ = c.MarkFlagRequired("section")
	return c
}

// gstr1DocsCmd is the document list itself.
func gstr1DocsCmd(app *App) *cobra.Command {
	var period, section, ctin, uploadedBy, inum string
	c := &cobra.Command{
		Use:   "docs",
		Short: "Documents in one GSTR-1 section (scope a big section with --ctin)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parsePeriod(period); err != nil {
				return err
			}
			sec, by, err := normaliseSection(section)
			if err != nil {
				return err
			}
			if uploadedBy != "" {
				by = strings.ToUpper(uploadedBy)
			}
			// Table 13 (documents issued) is addressed by the literal inum=DOC,
			// which is how the portal's own page asks for it.
			if sec == "DOC" && inum == "" {
				inum = "DOC"
			}
			return app.read("gstr1 docs", reg, epGSTR1Invoice, nil,
				qs("rtn_prd", period, "sec_name", sec, "uploaded_by", by, "ctin", strings.ToUpper(ctin), "inum", inum), nil)
		},
	}
	periodFlag(c, &period)
	c.Flags().StringVar(&section, "section", "B2B", "section: "+sectionList())
	c.Flags().StringVar(&ctin, "ctin", "", "counterparty GSTIN — the only way to narrow a large section")
	c.Flags().StringVar(&uploadedBy, "uploaded-by", "", "override the section's default uploaded_by (SU = supplier, OE = own entry)")
	c.Flags().StringVar(&inum, "inum", "", "one document number (the portal wants <inum>_<FY>)")
	return c
}

// normaliseSection validates a section name and returns it with the uploaded_by
// the portal pairs with it.
func normaliseSection(s string) (string, string, error) {
	want := strings.ToUpper(strings.TrimSpace(s))
	if by, ok := gstr1Sections[want]; ok {
		return want, by, nil
	}
	return "", "", errUsage("%q is not a GSTR-1 section; use one of: %s", s, sectionList())
}

func sectionList() string {
	out := make([]string, 0, len(gstr1Sections))
	for k := range gstr1Sections {
		out = append(out, k)
	}
	sortStrings(out)
	return strings.Join(out, ", ")
}

// gstr1CountLine summarises the section counts for the stderr line and returns
// the total processed document count.
func gstr1CountLine(raw json.RawMessage) (string, int) {
	var v struct {
		Data struct {
			SecCount []struct {
				SecName string `json:"sec_name"`
				ProcCnt int    `json:"proc_cnt"`
				PenCnt  int    `json:"pen_cnt"`
				ErrCnt  int    `json:"err_cnt"`
			} `json:"sec_count"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &v); err != nil || len(v.Data.SecCount) == 0 {
		return "", 0
	}
	total, errs := 0, 0
	var parts []string
	for _, s := range v.Data.SecCount {
		n := s.ProcCnt + s.PenCnt
		total += n
		errs += s.ErrCnt
		if n > 0 {
			parts = append(parts, s.SecName+" "+itoa(n))
		}
	}
	line := strings.Join(parts, ", ")
	if errs > 0 {
		line += "; " + itoa(errs) + " in error"
	}
	return line, total
}
