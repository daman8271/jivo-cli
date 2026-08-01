package mcpsrv

// The three domain tools. They exist because a tool description cannot compute
// anything: the olive incident happened despite the server's instructions, and
// benchmark question h17 shows a model that KNOWS the wider basis still
// headlines the narrow number. A tool that returns the external/internal split
// and the all-DocType total in the same payload makes the omission impossible,
// which is a different kind of guarantee from advice.
//
// Nothing here reaches the database directly. Every call goes through
// internal/domain, whose only capability is *hana.DB.QueryReadOnly — the same
// entry point hana_query uses, with the same guard, the same READ ONLY
// transaction and the same caps. There is no privileged path.

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"hana-sql/internal/domain"
)

// missingArg is the refusal for an argument the caller left out. It names what
// the argument is for, so the model can fill it in without a second round trip.
func missingArg(name, what string) error {
	return fmt.Errorf("missing required argument: %s — %s", name, what)
}

// domainEnvelope marshals one domain answer, or one error.
//
// Unlike the generic envelope, as_of here comes from the HANA server clock,
// selected in the SAME statement as the figures — so a month-end close can be
// reproduced against a stated instant instead of whatever this host's clock said.
func (s *Server) domainEnvelope(res *domain.Response, err error) (string, bool) {
	if err != nil {
		return s.scrub(err.Error()), true
	}
	b, merr := json.Marshal(res)
	if merr != nil {
		return "could not encode result: " + merr.Error(), true
	}
	return string(b), false
}

// salesByVariety runs hana_sales_by_variety.
//
// net_credit_notes is a *bool because its default is TRUE: with a plain bool,
// omitting the argument and passing false would be indistinguishable, and the
// tool would silently report sales before returns while claiming to be net.
func (s *Server) salesByVariety(ctx context.Context, raw json.RawMessage) (string, bool) {
	var a struct {
		From           string `json:"from"`
		To             string `json:"to"`
		Company        string `json:"company"`
		Variety        string `json:"variety"`
		IncludeType    bool   `json:"include_type"`
		NetCreditNotes *bool  `json:"net_credit_notes"`
	}
	if err := decodeArgs(raw, &a); err != nil {
		return err.Error(), true
	}
	if err := checkArgs(a.From, a.To, a.Company); err != nil {
		return err.Error(), true
	}
	netCN := true
	if a.NetCreditNotes != nil {
		netCN = *a.NetCreditNotes
	}
	db, err := s.db()
	if err != nil {
		return err.Error(), true
	}
	res, derr := domain.SalesByVariety(ctx, db, domain.SalesRequest{
		From:           a.From,
		To:             a.To,
		Company:        a.Company,
		Variety:        a.Variety,
		IncludeType:    a.IncludeType,
		NetCreditNotes: netCN,
	})
	return s.domainEnvelope(res, derr)
}

// turnover runs hana_turnover.
func (s *Server) turnover(ctx context.Context, raw json.RawMessage) (string, bool) {
	var a struct {
		From    string `json:"from"`
		To      string `json:"to"`
		Company string `json:"company"`
	}
	if err := decodeArgs(raw, &a); err != nil {
		return err.Error(), true
	}
	if err := checkArgs(a.From, a.To, a.Company); err != nil {
		return err.Error(), true
	}
	db, err := s.db()
	if err != nil {
		return err.Error(), true
	}
	res, derr := domain.Turnover(ctx, db, domain.TurnoverRequest{From: a.From, To: a.To, Company: a.Company})
	return s.domainEnvelope(res, derr)
}

// payments runs hana_payments. There is no scoping argument by design: the
// per-DocType breakdown and the all-types total always come back together.
func (s *Server) payments(ctx context.Context, raw json.RawMessage) (string, bool) {
	var a struct {
		Direction string `json:"direction"`
		From      string `json:"from"`
		To        string `json:"to"`
		Company   string `json:"company"`
	}
	if err := decodeArgs(raw, &a); err != nil {
		return err.Error(), true
	}
	dir, derr := domain.ParseDirection(a.Direction)
	if derr != nil {
		return derr.Error(), true
	}
	if err := checkArgs(a.From, a.To, a.Company); err != nil {
		return err.Error(), true
	}
	db, err := s.db()
	if err != nil {
		return err.Error(), true
	}
	res, qerr := domain.Payments(ctx, db, domain.PaymentsRequest{
		Direction: dir, From: a.From, To: a.To, Company: a.Company,
	})
	return s.domainEnvelope(res, qerr)
}

// checkArgs validates the window and the company BEFORE the database is touched.
//
// This is the invariant the rest of this package holds to (see Dispatch): a
// caller's mistake is answered by the argument validator, not by whatever the
// connection layer happens to say. Without it a mis-typed date on a server whose
// tunnel is down comes back as "no HANA connection configured", which sends a
// model debugging the wrong thing — and on a healthy server it would take out a
// connection and run the variety pre-check before anyone had looked at the date.
//
// domain re-validates both when it runs. That duplication is deliberate: the
// domain package must be safe to call directly, and this layer must be able to
// refuse without a database.
func checkArgs(from, to, company string) error {
	if strings.TrimSpace(from) == "" {
		return missingArg("from", `the first day of the range, YYYY-MM-DD, e.g. "2026-06-01" (INCLUSIVE)`)
	}
	if strings.TrimSpace(to) == "" {
		return missingArg("to", `the last day of the range, YYYY-MM-DD, e.g. "2026-06-30" (INCLUSIVE — the server binds to+1 day and echoes the window it applied)`)
	}
	if _, err := domain.ParseWindow(from, to); err != nil {
		return err
	}
	_, err := domain.ResolveCompanies(company)
	return err
}
