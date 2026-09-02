package main

import (
	"encoding/json"
	"time"

	"github.com/spf13/cobra"
)

// ledger — the three electronic ledgers: cash (what has been paid in), credit
// (unutilised ITC) and liability (what was owed and how it was discharged).
//
// Each verb has the same two shapes: no dates = the live balance, --from/--to =
// the statement over that range. The portal wants dd/mm/yyyy on the cash and
// credit statements, ISO on liability Part-II, and MMYYYY on liability Part-I;
// the CLI takes YYYY-MM-DD everywhere and converts.

func init() { registerSection(newLedgerCmd) }

func newLedgerCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "ledger",
		Short: "Electronic cash / credit / liability ledgers and challans",
	}
	c.AddCommand(
		ledgerCashCmd(app),
		ledgerCreditCmd(app),
		ledgerChallansCmd(app),
		ledgerLiabilityCmd(app),
		ledgerLiabilityOtherCmd(app),
	)
	return c
}

// dateRange holds a resolved --from/--to pair.
type dateRange struct {
	from, to time.Time
	set      bool
}

// resolveRange parses the flags. Both or neither; --to defaults to today when
// only --from is given, because "since April" is the question people ask.
func resolveRange(from, to string, required bool) (dateRange, error) {
	if from == "" && to == "" {
		if required {
			return dateRange{}, errUsage("--from and --to are required for this command (YYYY-MM-DD)")
		}
		return dateRange{}, nil
	}
	if from == "" {
		return dateRange{}, errUsage("--to without --from: give both, or neither for the live balance")
	}
	f, err := parseISODate(from)
	if err != nil {
		return dateRange{}, err
	}
	t := nowIST()
	if to != "" {
		if t, err = parseISODate(to); err != nil {
			return dateRange{}, err
		}
	}
	if t.Before(f) {
		return dateRange{}, errUsage("--to (%s) is before --from (%s)", isoDate(t), isoDate(f))
	}
	return dateRange{from: f, to: t, set: true}, nil
}

func rangeFlags(c *cobra.Command, from, to *string) {
	c.Flags().StringVar(from, "from", "", "range start, YYYY-MM-DD")
	// NOTE: --to is INCLUSIVE here, unlike the fleet-wide house rule
	// (docs/conventions.md:49, --to exclusive). These dates are passed straight
	// through to the portal's own tdate/to_dt parameters, and the portal treats
	// them as inclusive; re-basing them would silently disagree with what the
	// same range shows on gst.gov.in. Say so rather than surprise anyone.
	c.Flags().StringVar(to, "to", "", "range end, YYYY-MM-DD, INCLUSIVE (portal semantics; default: today)")
}

func ledgerCashCmd(app *App) *cobra.Command {
	var from, to string
	c := &cobra.Command{
		Use:   "cash",
		Short: "Electronic cash ledger: balance by head, or the statement over --from/--to",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			r, err := resolveRange(from, to, false)
			if err != nil {
				return err
			}
			cl := newClient(reg)
			if r.set {
				res, err := cl.do(epCashDetails, nil, qs("fdate", portalDate(r.from), "tdate", portalDate(r.to)), nil)
				return app.emit("ledger cash", reg.GSTIN, endpointURL(epCashDetails), res, err)
			}
			res, err := cl.do(epCashBalance, nil, nil, nil)
			if err == nil && !res.Empty {
				app.logf("%s cash ledger balance: %s", reg.GSTIN, inr(totalOf(res.Raw, "tot_rng_bal")))
			}
			return app.emit("ledger cash", reg.GSTIN, endpointURL(epCashBalance), res, err)
		},
	}
	rangeFlags(c, &from, &to)
	return c
}

func ledgerCreditCmd(app *App) *cobra.Command {
	var from, to string
	c := &cobra.Command{
		Use:   "credit",
		Short: "Electronic credit (ITC) ledger: balance by head, or the statement over --from/--to",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			r, err := resolveRange(from, to, false)
			if err != nil {
				return err
			}
			cl := newClient(reg)
			if r.set {
				res, err := cl.do(epITCDetails, nil, qs("fdate", portalDate(r.from), "tdate", portalDate(r.to)), nil)
				return app.emit("ledger credit", reg.GSTIN, endpointURL(epITCDetails), res, err)
			}
			res, err := cl.do(epITCBalance, nil, nil, nil)
			if err == nil && !res.Empty {
				// op_tot is the total across heads. The body's `dt` field is
				// garbage ("16/02/0027") and is deliberately not shown.
				app.logf("%s credit ledger balance: %s", reg.GSTIN, inr(totalOf(res.Raw, "op_tot")))
			}
			return app.emit("ledger credit", reg.GSTIN, endpointURL(epITCBalance), res, err)
		},
	}
	rangeFlags(c, &from, &to)
	return c
}

func ledgerChallansCmd(app *App) *cobra.Command {
	var from, to string
	c := &cobra.Command{
		Use:   "challans",
		Short: "Challan ARNs paid in a date range (LG9221 = none, which is an answer)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			r, err := resolveRange(from, to, true)
			if err != nil {
				return err
			}
			return app.read("ledger challans", reg, epChallanSearch, nil,
				qs("fromdate", portalDate(r.from), "todate", portalDate(r.to)), nil)
		},
	}
	rangeFlags(c, &from, &to)
	return c
}

// ledgerLiabilityCmd is the liability register Part-I (return related). Its
// range is in MMYYYY, so the dates are collapsed to their months.
func ledgerLiabilityCmd(app *App) *cobra.Command {
	var from, to string
	c := &cobra.Command{
		Use:   "liability",
		Short: "Liability register Part-I (return related), by month range",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			r, err := resolveRange(from, to, true)
			if err != nil {
				return err
			}
			// gstin=undefined is not a bug here: the portal's own page sends the
			// literal string and the server resolves the GSTIN from the session.
			// Replaying it verbatim is the only shape that has been observed to
			// work (API.md, D5c).
			return app.read("ledger liability", reg, epLiability, nil,
				qs("fdate", formatPeriod(r.from), "to_dt", formatPeriod(r.to), "gstin", "undefined"), nil)
		},
	}
	rangeFlags(c, &from, &to)
	return c
}

// ledgerLiabilityOtherCmd is Part-II (demands, other than return related). Note
// the ISO dates — this endpoint disagrees with every other ledger call.
func ledgerLiabilityOtherCmd(app *App) *cobra.Command {
	var from, to string
	c := &cobra.Command{
		Use:   "liability-other",
		Short: "Liability register Part-II (demands, other than return related)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			r, err := resolveRange(from, to, true)
			if err != nil {
				return err
			}
			return app.read("ledger liability-other", reg, epLiabilityOther, nil,
				qs("fdate", isoDate(r.from), "tdate", isoDate(r.to)), nil)
		},
	}
	rangeFlags(c, &from, &to)
	return c
}

// totalOf reads one top-level number out of a portal body, for the human line.
func totalOf(raw json.RawMessage, key string) float64 {
	var m map[string]any
	if err := json.Unmarshal(raw, &m); err != nil {
		return 0
	}
	if v, ok := m[key].(float64); ok {
		return v
	}
	return 0
}
