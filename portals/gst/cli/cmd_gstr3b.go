package main

import (
	"encoding/json"

	"github.com/spf13/cobra"
)

// gstr3b — the monthly summary return: what was declared as liability, what ITC
// was claimed, and what was actually paid. This is the form comparison-spec §C3
// diffs against SAP's monthly tax movements.

func init() { registerSection(newGSTR3BCmd) }

func newGSTR3BCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "gstr3b",
		Short: "GSTR-3B: the filed summary return, its auto-population, and its filing status",
	}
	c.AddCommand(
		gstr3bSummaryCmd(app),
		gstr3bAutopopCmd(app),
		gstr3bStatusCmd(app),
	)
	return c
}

func gstr3bSummaryCmd(app *App) *cobra.Command {
	var period string
	c := &cobra.Command{
		Use:   "summary",
		Short: "The filed GSTR-3B for one period (tables 3.1, 3.2, 4, 5.1, 6.1)",
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
			res, err := cl.do(epGSTR3BSummary, nil, qs("rtn_prd", period), nil)
			if err == nil && !res.Empty {
				if line := gstr3bHeadline(res.Raw); line != "" {
					app.logf("%s %s — %s", reg.GSTIN, period, line)
				}
			}
			return app.emit("gstr3b summary", reg.GSTIN, endpointURL(epGSTR3BSummary), res, err)
		},
	}
	periodFlag(c, &period)
	return c
}

func gstr3bAutopopCmd(app *App) *cobra.Command {
	var period string
	c := &cobra.Command{
		Use:   "autopop",
		Short: "GSTR-1 vs 3B auto-population for one period (what the portal pre-filled)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parsePeriod(period); err != nil {
				return err
			}
			// Note the parameter name: retPeriod, camelCase, not rtn_prd. The
			// portal is not consistent about this and the guard would refuse a
			// helpful "correction".
			return app.read("gstr3b autopop", reg, epGSTR3BAutoPop, nil, qs("retPeriod", period), nil)
		},
	}
	periodFlag(c, &period)
	return c
}

func gstr3bStatusCmd(app *App) *cobra.Command {
	var period string
	c := &cobra.Command{
		Use:   "status",
		Short: "GSTR-3B filing status for one period: ARN, filing date, due date",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parsePeriod(period); err != nil {
				return err
			}
			return app.read("gstr3b status", reg, epFormDetails, nil, qs("rtn_prd", period, "rtn_typ", "GSTR3B"), nil)
		},
	}
	periodFlag(c, &period)
	return c
}

// periodFlag adds the --period MMYYYY flag every return-level command takes.
func periodFlag(c *cobra.Command, period *string) {
	c.Flags().StringVar(period, "period", "", "return period, MMYYYY (e.g. 072026)")
	_ = c.MarkFlagRequired("period")
}

// gstr3bHeadline is the human stderr line: outward taxable value and the tax
// paid, the two numbers anyone opening a 3B is looking for.
func gstr3bHeadline(raw json.RawMessage) string {
	var v struct {
		Data struct {
			SupDetails struct {
				OsupDet struct {
					Txval float64 `json:"txval"`
					Iamt  float64 `json:"iamt"`
					Camt  float64 `json:"camt"`
					Samt  float64 `json:"samt"`
					Csamt float64 `json:"csamt"`
				} `json:"osup_det"`
			} `json:"sup_details"`
			TtVal struct {
				TtCshPd float64 `json:"tt_csh_pd"`
				TtItcPd float64 `json:"tt_itc_pd"`
			} `json:"tt_val"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &v); err != nil {
		return ""
	}
	o := v.Data.SupDetails.OsupDet
	if o.Txval == 0 && v.Data.TtVal.TtItcPd == 0 && v.Data.TtVal.TtCshPd == 0 {
		return "nil return (no outward supplies, nothing paid)"
	}
	tax := o.Iamt + o.Camt + o.Samt + o.Csamt
	return "outward taxable " + inr(o.Txval) + ", tax on it " + inr(tax) +
		"; paid via ITC " + inr(v.Data.TtVal.TtItcPd) + ", in cash " + inr(v.Data.TtVal.TtCshPd)
}
